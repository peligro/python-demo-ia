from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime, timezone

class SentimentAnalysisRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=2000, description="Texto a analizar")
    model: Optional[str] = Field(default="mistral-small-latest", description="Modelo de IA")
    language: Optional[str] = Field(default="es", description="Código ISO del idioma")

class SentimentAnalysisResponse(BaseModel):
    text: str
    sentiment: Literal["positive", "negative", "neutral"]
    sentiment_label: str  # "Positivo", "Negativo", "Neutral"
    confidence: Optional[float] = None  # 0.0 a 1.0 si la IA lo retorna
    explanation: Optional[str] = None  # Explicación breve del análisis
    model_used: str
    metrics: dict  # tokens, latency, etc.
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class SentimentHistoryItem(BaseModel):
    id: str
    text: str
    sentiment: str
    confidence: Optional[float]
    timestamp: datetime

class SentimentHistoryResponse(BaseModel):
    items: list[SentimentHistoryItem]
    total: int
