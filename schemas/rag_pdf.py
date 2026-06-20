#schemas/rag_pdf.py
from pydantic import BaseModel, Field
from typing import Optional, List

class RAGQueryRequest(BaseModel):
    """Payload para consulta RAG PDF"""
    query: str = Field(..., min_length=5, description="Consulta del usuario")
    model: Optional[str] = Field("mistral-small-latest", description="Modelo de IA a usar")
    kb_threshold: Optional[float] = Field(0.75, ge=0.0, le=1.0, description="Threshold para match directo en KB")
    top_k: Optional[int] = Field(3, ge=1, le=10, description="Número de chunks a recuperar")

class RAGQueryResponse(BaseModel):
    """Respuesta del agente RAG PDF"""
    response: str
    source: str  # "knowledge-base", "rag-ai", "none"
    model_used: str
    chunks_used: int = 0
    chunk_ids: List[int] = []
    latency_ms: int = 0
    cache: bool = False
    similarity_score: Optional[float] = None
