import time
from typing import Optional, List
from sqlmodel import Session
from integraciones.agente_integration import AgenteIntegration
from schemas.chat_history import ChatHistoryRequest, ChatHistoryResponse, Message

class ChatHistoryService:
    def __init__(self, session: Session):
        self.session = session

    async def chat(self, request: ChatHistoryRequest) -> ChatHistoryResponse:
        start_time = time.time()
        
        # Limitar historial si es necesario (para ahorrar tokens)
        messages_limited = request.messages[-request.max_history:] if len(request.messages) > request.max_history else request.messages
        
        # Convertir a formato que entienden las APIs
        api_messages = [{"role": msg.role, "content": msg.content} for msg in messages_limited]
        
        # Determinar proveedor
        provider = self._get_provider_from_model(request.model)
        
        try:
            # Llamar a la IA con historial completo
            result = AgenteIntegration.chat_unificado(
                provider=provider,
                prompt="",  # No usamos prompt base, el historial ya lo contiene
                model=request.model,
                messages=api_messages  # Pasamos el historial como kwarg adicional
            )
            
            latency_ms = int((time.time() - start_time) * 1000)
            
            return ChatHistoryResponse(
                response=result["response"],
                model_name=request.model,
                messages_count=len(messages_limited),
                metrics={
                    "input_tokens": result["usage"]["input"],
                    "output_tokens": result["usage"]["output"],
                    "total_tokens": result["usage"]["total"],
                    "latency_ms": latency_ms
                }
            )
        except Exception as e:
            latency_ms = int((time.time() - start_time) * 1000)
            return ChatHistoryResponse(
                response=f"Error: {str(e)}",
                model_name=request.model,
                messages_count=len(messages_limited),
                metrics={"latency_ms": latency_ms}
            )

    def _get_provider_from_model(self, model: str) -> str:
        model_lower = model.lower()
        if 'mistral' in model_lower: return 'mistral'
        elif 'gemini' in model_lower: return 'gemini'
        elif 'claude' in model_lower: return 'claude'
        elif 'gpt' in model_lower or 'openai' in model_lower: return 'openai'
        elif 'deepseek' in model_lower: return 'deepseek'
        return 'mistral'