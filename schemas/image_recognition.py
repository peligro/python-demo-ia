from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime, timezone

class ImageRecognitionRequest(BaseModel):
    image_url: str = Field(..., description="URL pública de la imagen a analizar")
    prompt: Optional[str] = Field(default="Describe esta imagen de manera objetiva.", description="Pregunta específica sobre la imagen")
    model: Literal["gpt-4o", "gemini-2.5-flash", "gpt-4o-mini", "gemini-2.0-flash"] = Field(default="gpt-4o", description="Modelo a usar (solo OpenAI o Gemini)")

class ImageRecognitionResponse(BaseModel):
    description: str
    model_used: str
    metrics: dict  # tokens, latency
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
