import time
import re
from typing import Optional
from sqlmodel import Session
from integraciones.agente_integration import AgenteIntegration
from schemas.analisis_sentimiento import (
    SentimentAnalysisRequest, 
    SentimentAnalysisResponse
)

class AnalisisSentimientoService:
    def __init__(self, session: Session):
        self.session = session

    async def analyze(self, request: SentimentAnalysisRequest) -> SentimentAnalysisResponse:
        start_time = time.time()
        
        # Construir prompt optimizado para análisis de sentimiento
        prompt = self._build_sentiment_prompt(
            text=request.text,
            language=request.language
        )
        
        # Determinar proveedor
        provider = self._get_provider_from_model(request.model)
        
        try:
            # Llamar a la IA
            result = AgenteIntegration.chat_unificado(
                provider=provider,
                prompt=prompt,
                model=request.model
            )
            
            latency_ms = int((time.time() - start_time) * 1000)
            
            # Parsear respuesta de la IA
            sentiment_data = self._parse_sentiment_response(result["response"])
            
            return SentimentAnalysisResponse(
                text=request.text,
                sentiment=sentiment_data["sentiment"],
                sentiment_label=sentiment_data["label"],
                confidence=sentiment_data.get("confidence"),
                explanation=sentiment_data.get("explanation"),
                model_used=request.model,
                metrics={
                    "input_tokens": result["usage"]["input"],
                    "output_tokens": result["usage"]["output"],
                    "total_tokens": result["usage"]["total"],
                    "latency_ms": latency_ms
                }
            )
        except Exception as e:
            latency_ms = int((time.time() - start_time) * 1000)
            return SentimentAnalysisResponse(
                text=request.text,
                sentiment="neutral",
                sentiment_label="Neutral",
                confidence=None,
                explanation=f"Error: {str(e)}",
                model_used=request.model,
                metrics={"latency_ms": latency_ms}
            )

    def _build_sentiment_prompt(self, text: str, language: str) -> str:
        """Construye el prompt optimizado para análisis de sentimiento"""
        lang_name = {"es": "español", "en": "inglés", "pt": "portugués"}.get(language, "español")
        
        return f"""Eres un experto en análisis de sentimientos y procesamiento de lenguaje natural en {lang_name}.

Analiza el siguiente texto y determina su sentimiento emocional:

Texto: "{text}"

Instrucciones:
1. Clasifica el sentimiento como: POSITIVO, NEGATIVO o NEUTRAL
2. Proporciona un score de confianza entre 0.0 y 1.0 (opcional)
3. Explica brevemente tu razonamiento en una frase
4. Responde SOLO en el siguiente formato JSON, sin explicaciones adicionales:

{{
  "sentiment": "positive|negative|neutral",
  "label": "Positivo|Negativo|Neutral",
  "confidence": 0.85,
  "explanation": "Breve explicación del análisis"
}}

Respuesta:"""

    def _parse_sentiment_response(self, response: str) -> dict:
        """Parsea la respuesta de la IA para extraer datos estructurados"""
        # Intentar extraer JSON de la respuesta
        import json
        import re
        
        # Buscar patrón JSON en la respuesta
        json_match = re.search(r'\{[^{}]*"sentiment"[^{}]*\}', response, re.DOTALL)
        
        if json_match:
            try:
                data = json.loads(json_match.group())
                return {
                    "sentiment": data.get("sentiment", "neutral"),
                    "label": data.get("label", "Neutral"),
                    "confidence": data.get("confidence"),
                    "explanation": data.get("explanation")
                }
            except:
                pass
        
        # Fallback: análisis básico por palabras clave
        text_lower = response.lower()
        if any(word in text_lower for word in ["positiv", "buen", "excelent", "feliz", "amor"]):
            return {"sentiment": "positive", "label": "Positivo", "confidence": None, "explanation": "Análisis por palabras clave"}
        elif any(word in text_lower for word in ["negativ", "mal", "terribl", "trist", "odio"]):
            return {"sentiment": "negative", "label": "Negativo", "confidence": None, "explanation": "Análisis por palabras clave"}
        
        return {"sentiment": "neutral", "label": "Neutral", "confidence": None, "explanation": "Análisis por palabras clave"}

    def _get_provider_from_model(self, model: str) -> str:
        model_lower = model.lower()
        if 'mistral' in model_lower: return 'mistral'
        elif 'gemini' in model_lower: return 'gemini'
        elif 'claude' in model_lower: return 'claude'
        elif 'gpt' in model_lower or 'openai' in model_lower: return 'openai'
        elif 'deepseek' in model_lower: return 'deepseek'
        return 'mistral'