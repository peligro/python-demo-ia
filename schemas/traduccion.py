#schemas/traduccion.py
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, timezone

class TranslationRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=5000, description="Texto a traducir")
    source_lang: Optional[str] = Field(default="auto", description="Código ISO del idioma origen (auto para detectar)")
    target_lang: str = Field(..., description="Código ISO del idioma destino")
    model: Optional[str] = Field(default="mistral-small-latest", description="Modelo de IA a usar")
    tone: Optional[str] = Field(default="neutral", description="Tono: neutral, formal, casual")

class TranslationResponse(BaseModel):
    original_text: str
    translated_text: str
    source_lang_detected: str
    target_lang: str
    model_used: str
    confidence: Optional[float] = None  # Si la IA lo retorna
    metrics: dict  # tokens, latency, etc.
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class TranslationHistoryItem(BaseModel):
    id: str
    original_text: str
    translated_text: str
    source_lang: str
    target_lang: str
    model: str
    timestamp: datetime
    tokens_used: int

class TranslationHistoryResponse(BaseModel):
    items: List[TranslationHistoryItem]
    total: int