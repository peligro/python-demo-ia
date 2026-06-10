# api/router/rag_pdf/rag_pdf_router.py
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from sqlmodel import Session, select
from database.database import get_session
from middleware.auth import get_current_user

from models.rag_job import RAGJob, JobStatus
from models.rag_chunk import RAGChunk
from services.rag_pdf.s3_service import S3Service
from services.rag_pdf.rag_engine import RAGEngine
from services.rag_pdf.rag_cache_service import RAGCacheService
from services.queue.queue_service import QueueService
from botocore.exceptions import ClientError


router = APIRouter(prefix="/rag-pdf", tags=["Portfolio: RAG PDF"])


@router.post("/upload")
async def upload_pdf(
    file: UploadFile = File(...),
    queue_provider: str = Query(default="redis", regex="^(redis|sqs)$"),  # ← Nuevo parámetro
    session: Session = Depends(get_session),
    current_user: dict = Depends(get_current_user)
):
    """Sube PDF, crea job y encola para procesamiento asíncrono
    
    Args:
        queue_provider: "redis" (default) o "sqs" para definir dónde encolar el job
    """
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Solo se permiten archivos PDF")

    # 1. Subir a S3
    s3 = S3Service()
    s3_key = s3.upload_file(file)

    # 2. Crear registro de job
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

    # 3. Encolar mensaje con el proveedor seleccionado
    queue = QueueService(provider=queue_provider)  # ← Usa el factory
    message_id = queue.enqueue({
        "job_id": job.id,
        "s3_key": s3_key,
        "filename": file.filename,
        "user_id": job.user_id,
        "priority": "normal",
        "created_at": datetime.utcnow().isoformat(),
        "queue_provider": queue_provider  # ← Útil para debugging/logs
    })

    return {
        "job_id": job.id,
        "status": JobStatus.QUEUED.value,
        "queue_provider": queue_provider,  # ← Confirmar qué cola se usó
        "message_id": message_id,
        "message": "Procesamiento iniciado"
    }


@router.get("/jobs/{job_id}")
async def get_job_status(
    job_id: int,
    session: Session = Depends(get_session),
    current_user: dict = Depends(get_current_user)
):
    """
    Polling: Obtiene el estado del job de procesamiento.
    El frontend debe consultar cada 2-3 segundos hasta que status = 'completed'
    """
    job = session.get(RAGJob, job_id)
    
    if not job:
        raise HTTPException(status_code=404, detail="Job no encontrado")
    
    # Verificar que el job pertenezca al usuario
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


@router.get("/jobs/{job_id}/chunks")
async def get_job_chunks(
    job_id: int,
    session: Session = Depends(get_session),
    current_user: dict = Depends(get_current_user)
):
    """
    Obtiene todos los chunks generados por un job.
    Útil para revisar/editar chunks antes de usar el chat.
    """
    job = session.get(RAGJob, job_id)
    
    if not job:
        raise HTTPException(status_code=404, detail="Job no encontrado")
    
    if job.user_id != current_user["user"].id:
        raise HTTPException(status_code=403, detail="No autorizado")
    
    if job.status != JobStatus.COMPLETED:
        raise HTTPException(
            status_code=400,
            detail=f"El job no está completado. Estado actual: {job.status.value}"
        )
    
    # Obtener chunks del PDF
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


@router.post("/query")
async def rag_query(
    query: str,
    session: Session = Depends(get_session),
    current_user: dict = Depends(get_current_user)
):
    """
    Consulta al chatbot RAG.
    Busca en los chunks del manual y genera respuesta con IA.
    """
    if not query or len(query.strip()) < 5:
        raise HTTPException(
            status_code=400,
            detail="La consulta debe tener al menos 5 caracteres"
        )
    
    # Usar cache
    cache = RAGCacheService()
    cached_response = cache.get(query)
    
    if cached_response:
        cached_response["cache"] = True
        return cached_response
    
    # Procesar con RAG
    engine = RAGEngine()
    result = engine.process_query(query, session)
    
    # Guardar en cache
    cache.set(query, result)
    
    # Registrar query en query_logs (opcional, para analytics)
    # from models.query_log import QueryLog
    # log = QueryLog(
    #     user_id=current_user["user"].id,
    #     query=query,
    #     response=result["response"],
    #     chunks_used=result["chunks_used"]
    # )
    # session.add(log)
    # session.commit()
    
    return result


@router.get("/chunks")
async def list_chunks(
    section: str = Query(None, description="Filtrar por sección"),
    search: str = Query(None, description="Buscar en question/answer"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    session: Session = Depends(get_session),
    current_user: dict = Depends(get_current_user)
):
    """
    Lista todos los chunks (con filtros opcionales).
    Útil para admin/revisión.
    """
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
    

@router.get("/queue-providers")
async def list_queue_providers():
    """Lista los proveedores de cola disponibles y su estado"""
    providers = []
    
    # Verificar Redis
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
    
    # Verificar SQS
    try:
        from api.aws.aws import get_conection
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