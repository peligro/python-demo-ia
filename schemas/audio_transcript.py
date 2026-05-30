from pydantic import BaseModel, Field, field_validator
from typing import Optional, Literal
from datetime import datetime, timezone
import os

class AudioTranscriptRequest(BaseModel):
    audio_path: str = Field(..., description="Ruta relativa del archivo de audio en el servidor")
    model: Literal["whisper-1", "gemini-2.5-flash", "gemini-2.0-flash"] = Field(default="whisper-1", description="Modelo de transcripción")
    language: Optional[str] = Field(default="es", description="Código ISO del idioma (opcional, auto-detect si no se especifica)")

    @field_validator('audio_path')
    @classmethod
    def validate_audio_path(cls, v: str) -> str:
        """Valida que la ruta sea relativa y apunte a archivos permitidos"""
        if not v.startswith('static/audio/'):
            raise ValueError('La ruta debe estar en static/audio/')
        if not any(v.endswith(ext) for ext in ['.mp3', '.ogg', '.wav', '.m4a', '.flac']):
            raise ValueError('Formato de audio no soportado')
        # Prevenir path traversal
        if '..' in v or v.startswith('/'):
            raise ValueError('Ruta inválida')
        return v

class AudioTranscriptResponse(BaseModel):
    transcription: str
    model_used: str
    audio_duration_seconds: Optional[float] = None
    detected_language: Optional[str] = None
    metrics: dict  # tokens, latency
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
