from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, timezone

class MetricsSchema(BaseModel):
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    latency_ms: int = 0

class PromptBasicRequest(BaseModel):
    input: str = Field(..., min_length=1, description="Consulta del usuario")
    model: Optional[str] = Field("mistral-small-latest", description="Modelo de IA")

class PromptBasicResponse(BaseModel):
    response: str
    model: str
    source: str = "ai" # Siempre será IA directa
    metrics: MetricsSchema
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
