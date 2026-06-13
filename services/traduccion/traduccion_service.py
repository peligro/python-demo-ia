#services/traduccion/traduccion_service.py
import time
import uuid
from typing import Optional
from sqlmodel import Session
from integraciones.agente_integration import AgenteIntegration
from schemas.traduccion import TranslationRequest, TranslationResponse, TranslationHistoryItem

class TraduccionService:
    def __init__(self, session: Session):
        self.session = session

    async def translate(self, request: TranslationRequest) -> TranslationResponse:
        start_time = time.time()
        
        # Construir prompt de traducción
        prompt = self._build_translation_prompt(
            text=request.text,
            source_lang=request.source_lang,
            target_lang=request.target_lang,
            tone=request.tone
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
            
            # Extraer solo la traducción (la IA puede agregar comentarios)
            translated_text = self._extract_translation(result["response"])
            
            return TranslationResponse(
                original_text=request.text,
                translated_text=translated_text,
                source_lang_detected=request.source_lang if request.source_lang != "auto" else "detectado",
                target_lang=request.target_lang,
                model_used=request.model,
                confidence=None,  # Las APIs no retornan confianza fácilmente
                metrics={
                    "input_tokens": result["usage"]["input"],
                    "output_tokens": result["usage"]["output"],
                    "total_tokens": result["usage"]["total"],
                    "latency_ms": latency_ms
                }
            )
        except Exception as e:
            latency_ms = int((time.time() - start_time) * 1000)
            return TranslationResponse(
                original_text=request.text,
                translated_text=f"Error: {str(e)}",
                source_lang_detected="unknown",
                target_lang=request.target_lang,
                model_used=request.model,
                metrics={"latency_ms": latency_ms}
            )

    def _build_translation_prompt(self, text: str, source_lang: str, target_lang: str, tone: str) -> str:
        """Construye el prompt optimizado para traducción"""
        source_note = f" (desde {source_lang})" if source_lang != "auto" else ""
        tone_note = {
            "formal": "Usa un tono formal y profesional.",
            "casual": "Usa un tono casual y cercano.",
            "neutral": "Mantén un tono neutral y claro."
        }.get(tone, "Mantén un tono neutral y claro.")
        
        return f"""Eres un traductor profesional experto en {target_lang}{source_note}.

Instrucciones:
1. Traduce el siguiente texto al {target_lang}
2. {tone_note}
3. Mantén el significado original, formato y puntuación
4. NO agregues explicaciones, notas ni comentarios adicionales
5. Devuelve SOLO la traducción, nada más

Texto a traducir:
{text}

Traducción:"""

    def _extract_translation(self, response: str) -> str:
        """Limpia la respuesta de la IA para obtener solo la traducción"""
        # Remover posibles prefijos como "Traducción:", "Aquí está:", etc.
        prefixes = ["Traducción:", "Translation:", "Here is:", "Aquí está:", "```", "```text"]
        cleaned = response.strip()
        for prefix in prefixes:
            if cleaned.startswith(prefix):
                cleaned = cleaned[len(prefix):].strip()
        return cleaned.strip()

    def _get_provider_from_model(self, model: str) -> str:
        model_lower = model.lower()
        if 'mistral' in model_lower: return 'mistral'
        elif 'gemini' in model_lower: return 'gemini'
        elif 'claude' in model_lower: return 'claude'
        elif 'gpt' in model_lower or 'openai' in model_lower: return 'openai'
        elif 'deepseek' in model_lower: return 'deepseek'
        return 'mistral'

    def save_to_history(self, item: TranslationHistoryItem) -> None:
        """Guarda en historial (implementación futura con tabla dedicated)"""
        # Por ahora, solo logueamos
        print(f"[Traducción] Guardado: {item.id} - {item.source_lang} → {item.target_lang}")