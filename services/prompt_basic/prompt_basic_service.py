#services/prompt_basic/prompt_basic_service.py
import time
import os
from sqlmodel import Session
from integraciones.agente_integration import AgenteIntegration
from schemas.prompt_basic import PromptBasicRequest, PromptBasicResponse, MetricsSchema

class PromptBasicService:
    def __init__(self, session: Session):
        self.session = session

    async def process_query(self, request: PromptBasicRequest) -> PromptBasicResponse:
        start_time = time.time()
        
        # Determinar proveedor basado en el modelo seleccionado
        model_lower = request.model.lower()
        if 'mistral' in model_lower: provider = 'mistral'
        elif 'gemini' in model_lower: provider = 'gemini'
        elif 'claude' in model_lower: provider = 'claude'
        elif 'gpt' in model_lower or 'openai' in model_lower: provider = 'openai'
        elif 'deepseek' in model_lower: provider = 'deepseek'
        else: provider = 'mistral'

        try:
            # Llamada directa a la IA usando la integración existente
            result = AgenteIntegration.chat_unificado(
                provider=provider,
                prompt=request.input,
                model=request.model
            )
            
            latency_ms = int((time.time() - start_time) * 1000)
            
            return PromptBasicResponse(
                response=result["response"],
                model=request.model or result.get("model", request.model),
                source="ai",
                metrics=MetricsSchema(
                    input_tokens=result["usage"]["input"],
                    output_tokens=result["usage"]["output"],
                    total_tokens=result["usage"]["total"],
                    latency_ms=latency_ms
                )
            )
        except Exception as e:
            latency_ms = int((time.time() - start_time) * 1000)
            return PromptBasicResponse(
                response=f"Error: {str(e)}",
                model=request.model,
                source="error",
                metrics=MetricsSchema(latency_ms=latency_ms)
            )