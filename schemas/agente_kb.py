from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, timezone

class MetricsSchema(BaseModel):
    """Métricas de consumo de la consulta"""
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    latency_ms: int = 0

class QueryRequest(BaseModel):
    """Payload que recibe el endpoint (Alineado con PlaiChatRequest del frontend)"""
    input: str = Field(..., min_length=1, description="Consulta del usuario")
    chatId: Optional[str] = Field(None, description="ID de sesión para contexto")
    model: Optional[str] = Field("mistral-small-latest", description="Modelo de IA a usar")

class QueryResponse(BaseModel):
    """Respuesta del agente (Alineado con PlaiChatResponse del frontend)"""
    response: str
    chatId: str
    messageId: str
    model: str
    source: str  # "knowledge-base", "plai-ai", "error"
    contextWasUsed: Optional[bool] = None
    userName: Optional[str] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    requiresHuman: bool = False
    # ✅ Agregamos metrics para que tu widget pueda mostrar el consumo
    metrics: Optional[MetricsSchema] = None
