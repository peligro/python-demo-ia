#schemas/agente_kb_logs.py
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class QueryLogResponse(BaseModel):
    """Respuesta para un log individual"""
    id: int
    example_id: str
    user_id: Optional[int]
    query: str
    response_source: str  # "knowledge-base", "plai-ai", "error"
    response_text: Optional[str]
    ai_model_name: Optional[str]
    input_tokens: Optional[int]
    output_tokens: Optional[int]
    total_tokens: Optional[int]
    latency_ms: Optional[int]
    kb_matched: bool
    kb_priority: Optional[int]
    created_at: datetime

class QueryLogsFilter(BaseModel):
    """Filtros para consultar logs"""
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    source: Optional[str] = None  # "knowledge-base", "plai-ai", "error"
    model: Optional[str] = None
    search: Optional[str] = None  # Búsqueda en query/response_text
    user_id: Optional[int] = None

class QueryLogsResponse(BaseModel):
    """Respuesta paginada de logs"""
    data: List[QueryLogResponse]
    pagination: dict
    filters_applied: dict
