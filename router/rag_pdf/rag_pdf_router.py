# api/router/rag_pdf/rag_pdf_router.py
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from fastapi.responses import StreamingResponse
from sqlmodel import Session, select, func
from database.database import get_session
from middleware.auth import get_current_user

from models.rag_job import RAGJob, JobStatus
from models.rag_chunk import RAGChunk
from services.rag_pdf.s3_service import S3Service
from services.rag_pdf.rag_engine import RAGEngine
from services.rag_pdf.rag_cache_service import RAGCacheService
from services.queue.queue_service import QueueService
from botocore.exceptions import ClientError

import os
import redis
import boto3

router = APIRouter(prefix="/rag-pdf", tags=["Portfolio: RAG PDF"])


# =============================================================================
# 1. RUTAS ESTÁTICAS
# =============================================================================

@router.post("/upload")
async def upload_pdf(
    file: UploadFile = File(...),
    queue_provider: str = Query(default="redis", pattern="^(redis|sqs)$"),  # ← pattern en vez de regex
    session: Session = Depends(get_session),
    current_user: dict = Depends(get_current_user)
):
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Solo se permiten archivos PDF")

    s3 = S3Service()
    s3_key = s3.upload_file(file)

    job = RAGJob(
        filename=file.filename,
        s3_key=s3_key,
        file_size=file.size,
        status=JobStatus.QUEUED,
        user_id=current_user["user"].id
    )
    session.add(job)
    session.commit()
    session.refresh(job)

    queue = QueueService(provider=queue_provider)
    message_id = queue.enqueue({
        "job_id": job.id,
        "s3_key": s3_key,
        "filename": file.filename,
        "user_id": job.user_id,
        "priority": "normal",
        "created_at": datetime.utcnow().isoformat(),
        "queue_provider": queue_provider
    })

    return {
        "job_id": job.id,
        "status": JobStatus.QUEUED.value,
        "queue_provider": queue_provider,
        "message_id": message_id,
        "message": "Procesamiento iniciado"
    }


@router.get("/jobs")
async def list_jobs(
    status: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    session: Session = Depends(get_session),
    current_user: dict = Depends(get_current_user)
):
    stmt = select(RAGJob).where(RAGJob.user_id == current_user["user"].id)
    count_stmt = select(func.count(RAGJob.id)).where(RAGJob.user_id == current_user["user"].id)
    
    if status:
        try:
            job_status = JobStatus(status.lower())
            stmt = stmt.where(RAGJob.status == job_status)
            count_stmt = count_stmt.where(RAGJob.status == job_status)
        except ValueError:
            raise HTTPException(status_code=400, detail="Status inválido")
    
    if search:
        search_pattern = f"%{search}%"
        stmt = stmt.where(RAGJob.filename.ilike(search_pattern))
        count_stmt = count_stmt.where(RAGJob.filename.ilike(search_pattern))
    
    total = session.exec(count_stmt).one()
    stmt = stmt.order_by(RAGJob.created_at.desc()).offset(offset).limit(limit)
    jobs = session.exec(stmt).all()
    
    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "jobs": [
            {
                "job_id": job.id,
                "status": job.status.value,
                "filename": job.s3_key,
                "file_size": job.file_size,
                "chunks_created": job.chunks_created,
                "processing_time_ms": job.processing_time_ms,
                "error_message": job.error_message,
                "created_at": job.created_at.isoformat() if job.created_at else None,
                "updated_at": job.updated_at.isoformat() if job.updated_at else None,
            }
            for job in jobs
        ]
    }


@router.get("/queue-providers")
async def list_queue_providers():
    providers = []
    
    try:
        r = redis.Redis(
            host=os.getenv("REDIS_HOST", "redis"),
            port=int(os.getenv("REDIS_PORT", 6379)),
            db=int(os.getenv("REDIS_DB", 0)),
            socket_timeout=2
        )
        r.ping()
        providers.append({"name": "redis", "status": "available", "stream": os.getenv("REDIS_STREAM", "rag-jobs")})
    except:
        providers.append({"name": "redis", "status": "unavailable"})
    
    try:
        if os.getenv('ENVIRONMENT') == 'local':
            sqs = boto3.client("sqs", region_name=os.getenv('AWS_REGION'), 
                             aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                             aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
                             endpoint_url=os.getenv('AWS_SECRET_ACCESS_URL'))
        else:
            sqs = boto3.client("sqs", region_name=os.getenv('AWS_REGION'),
                             aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                             aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'))
        
        queue_url = os.getenv("SQS_QUEUE_URL")
        if queue_url:
            sqs.get_queue_attributes(QueueUrl=queue_url, AttributeNames=["QueueArn"])
            providers.append({"name": "sqs", "status": "available", "queue_url": queue_url})
        else:
            providers.append({"name": "sqs", "status": "unconfigured"})
    except:
        providers.append({"name": "sqs", "status": "unavailable"})
    
    return {"providers": providers, "default": "redis"}


# =============================================================================
# 2. RUTAS DINÁMICAS ESPECÍFICAS (van ANTES de /jobs/{job_id})
# =============================================================================

@router.get("/jobs/{job_id}/download")
async def view_pdf(
    job_id: int,
    session: Session = Depends(get_session),
    current_user: dict = Depends(get_current_user)
):
    """Sirve el PDF directamente desde S3 para visualización inline"""
    job = session.get(RAGJob, job_id)
    
    if not job:
        raise HTTPException(status_code=404, detail="Job no encontrado")
    
    if job.user_id != current_user["user"].id:
        raise HTTPException(status_code=403, detail="No autorizado")
    
    if not job.s3_key:
        raise HTTPException(status_code=404, detail="El job no tiene archivo asociado")
    
    s3 = S3Service()
    try:
        response = s3.s3.get_object(Bucket=s3.bucket, Key=job.s3_key)
        body_stream = response["Body"]
        filename = job.filename or job.s3_key.split("/")[-1]
        
        return StreamingResponse(
            body_stream,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'inline; filename="{filename}"',
                "Cache-Control": "private, max-age=300",
                "X-Content-Type-Options": "nosniff",
            }
        )
    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code", "")
        if error_code == "NoSuchKey":
            raise HTTPException(status_code=404, detail="Archivo no encontrado en S3")
        raise HTTPException(status_code=500, detail=f"Error S3: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.get("/jobs/{job_id}/chunks")
async def get_job_chunks(
    job_id: int,
    session: Session = Depends(get_session),
    current_user: dict = Depends(get_current_user)
):
    job = session.get(RAGJob, job_id)
    
    if not job:
        raise HTTPException(status_code=404, detail="Job no encontrado")
    
    if job.user_id != current_user["user"].id:
        raise HTTPException(status_code=403, detail="No autorizado")
    
    if job.status != JobStatus.COMPLETED:
        raise HTTPException(status_code=400, detail=f"Job no completado. Estado: {job.status.value}")
    
    chunks = session.exec(
        select(RAGChunk)
        .where(RAGChunk.source_pdf == job.filename)
        .order_by(RAGChunk.section, RAGChunk.id)
    ).all()
    
    return {
        "job_id": job_id,
        "total_chunks": len(chunks),
        "chunks": [
            {
                "id": chunk.id,
                "section": chunk.section,
                "question": chunk.question,
                "answer": chunk.answer,
                "keywords": chunk.keywords,
                "page_number": chunk.page_number
            }
            for chunk in chunks
        ]
    }


# =============================================================================
# 3. RUTAS DINÁMICAS GENÉRICAS (van AL FINAL)
# =============================================================================

@router.get("/jobs/{job_id}")
async def get_job_status(
    job_id: int,
    session: Session = Depends(get_session),
    current_user: dict = Depends(get_current_user)
):
    job = session.get(RAGJob, job_id)
    
    if not job:
        raise HTTPException(status_code=404, detail="Job no encontrado")
    
    if job.user_id != current_user["user"].id:
        raise HTTPException(status_code=403, detail="No autorizado")
    
    return {
        "job_id": job.id,
        "status": job.status.value,
        "filename": job.filename,
        "chunks_created": job.chunks_created,
        "processing_time_ms": job.processing_time_ms,
        "error_message": job.error_message,
        "created_at": job.created_at,
        "updated_at": job.updated_at
    }


# =============================================================================
# 4. OTRAS RUTAS
# =============================================================================

@router.post("/query")
async def rag_query(
    query: str,
    session: Session = Depends(get_session),
    current_user: dict = Depends(get_current_user)
):
    if not query or len(query.strip()) < 5:
        raise HTTPException(status_code=400, detail="Consulta muy corta (mín 5 caracteres)")
    
    cache = RAGCacheService()
    cached_response = cache.get(query)
    
    if cached_response:
        cached_response["cache"] = True
        return cached_response
    
    engine = RAGEngine()
    result = engine.process_query(query, session)
    cache.set(query, result)
    
    return result


@router.get("/chunks")
async def list_chunks(
    section: str = Query(None),
    search: str = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    session: Session = Depends(get_session),
    current_user: dict = Depends(get_current_user)
):
    stmt = select(RAGChunk).where(RAGChunk.is_active == True)
    
    if section:
        stmt = stmt.where(RAGChunk.section == section.upper())
    
    if search:
        stmt = stmt.where(
            (RAGChunk.question.ilike(f"%{search}%")) |
            (RAGChunk.answer.ilike(f"%{search}%"))
        )
    
    stmt = stmt.order_by(RAGChunk.created_at.desc()).offset(offset).limit(limit)
    chunks = session.exec(stmt).all()
    
    return {
        "total": len(chunks),
        "limit": limit,
        "offset": offset,
        "chunks": [
            {
                "id": chunk.id,
                "section": chunk.section,
                "question": chunk.question,
                "answer": chunk.answer,
                "keywords": chunk.keywords,
                "source_pdf": chunk.source_pdf,
                "created_at": chunk.created_at
            }
            for chunk in chunks
        ]
    }