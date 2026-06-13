#router/agente_kb_logs/agente_kb_logs_router.py
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlmodel import Session, select, func
from database.database import get_session
from models.query_log import QueryLog
from schemas.agente_kb_logs import QueryLogsResponse, QueryLogResponse, QueryLogsFilter
from middleware.auth import get_current_user
from datetime import datetime
from typing import Optional

router = APIRouter(prefix="/portfolio/agente-kb", tags=["Portfolio: Agente KB Logs"])

@router.get("/logs", response_model=QueryLogsResponse)
async def get_query_logs(
    session: Session = Depends(get_session),
    current_user: dict = Depends(get_current_user),
    # Filtros query params
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    source: Optional[str] = None,
    model: Optional[str] = None,
    search: Optional[str] = None,
    user_id: Optional[int] = None,
):
    """
    Obtener logs de consultas del Agente KB con filtros y paginación.
    Solo usuarios autenticados pueden acceder.
    """
    try:
        # Construir query base
        stmt = select(QueryLog).where(QueryLog.example_id == "agente-kb")
        
        # Aplicar filtros
        filters_applied = {}
        
        if start_date:
            stmt = stmt.where(QueryLog.created_at >= datetime.fromisoformat(start_date))
            filters_applied["start_date"] = start_date
        if end_date:
            stmt = stmt.where(QueryLog.created_at <= datetime.fromisoformat(end_date))
            filters_applied["end_date"] = end_date
        if source:
            stmt = stmt.where(QueryLog.response_source == source)
            filters_applied["source"] = source
        if model:
            stmt = stmt.where(QueryLog.ai_model_name == model)
            filters_applied["model"] = model
        if user_id:
            stmt = stmt.where(QueryLog.user_id == user_id)
            filters_applied["user_id"] = user_id
        if search:
            stmt = stmt.where(
                (QueryLog.query.ilike(f"%{search}%")) | 
                (QueryLog.response_text.ilike(f"%{search}%"))
            )
            filters_applied["search"] = search
        
        # Contar total para paginación
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_records = session.exec(count_stmt).one()
        
        # Aplicar paginación
        offset = (page - 1) * per_page
        stmt = stmt.order_by(QueryLog.created_at.desc()).offset(offset).limit(per_page)
        
        logs = session.exec(stmt).all()
        
        # Serializar respuesta
        data = [
            QueryLogResponse(
                id=log.id,
                example_id=log.example_id,
                user_id=log.user_id,
                query=log.query,
                response_source=log.response_source,
                response_text=log.response_text,
                ai_model_name=log.ai_model_name,
                input_tokens=log.input_tokens,
                output_tokens=log.output_tokens,
                total_tokens=log.total_tokens,
                latency_ms=log.latency_ms,
                kb_matched=log.kb_matched,
                kb_priority=log.kb_priority,
                created_at=log.created_at,
            )
            for log in logs
        ]
        
        return QueryLogsResponse(
            data=data,
            pagination={
                "page": page,
                "per_page": per_page,
                "total_records": total_records,
                "total_pages": (total_records + per_page - 1) // per_page,
            },
            filters_applied=filters_applied,
        )
        
    except Exception as e:
        print(f"[AgenteKBLogs] Error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener logs: {str(e)}"
        )