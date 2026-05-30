from pydantic import BaseModel, Field, ConfigDict  # ✅ Agregar ConfigDict aquí
from typing import Optional, List
from datetime import datetime, timezone

class Message(BaseModel):
    role: str
    content: str

class ChatHistoryRequest(BaseModel):
    messages: List[Message] = Field(..., min_length=1)
    model: Optional[str] = Field(default="mistral-small-latest")
    max_history: Optional[int] = Field(default=10, ge=1, le=50)

class ChatHistoryResponse(BaseModel):
    response: str
    model_name: str  # ✅ Cambiado de model_used a model_name
    messages_count: int
    metrics: dict
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # ✅ Config para evitar warnings de Pydantic
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "response": "Hola, mucho gusto César...",
                "model_name": "mistral-small-latest",
                "messages_count": 5,
                "metrics": {"input_tokens": 100, "output_tokens": 50, "total_tokens": 150, "latency_ms": 1234}
            }
        }
    )