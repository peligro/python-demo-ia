from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime, timezone
import os

class VideoAnalysisRequest(BaseModel):
    video_path: str = Field(..., description="Ruta relativa del archivo de video en el servidor")
    prompt: Optional[str] = Field(default=None, description="Prompt personalizado para el análisis")
    model: str = Field(default="gemini-2.5-flash", description="Modelo de Gemini a usar")

    @field_validator('video_path')
    @classmethod
    def validate_video_path(cls, v: str) -> str:
        """Valida que la ruta sea relativa y apunte a videos permitidos"""
        if not v.startswith('static/videos/'):
            raise ValueError('La ruta debe estar en static/videos/')
        if not v.endswith('.mp4'):
            raise ValueError('Solo se soportan archivos MP4')
        # Prevenir path traversal
        if '..' in v or v.startswith('/'):
            raise ValueError('Ruta inválida')
        return v

class VideoAnalysisResponse(BaseModel):
    analysis: str
    model_used: str
    video_duration_seconds: Optional[float] = None
    metrics: dict  # tokens, latency
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
