# services/image_recognition/image_recognition_service.py
import time
from sqlmodel import Session
from integraciones.agente_integration import AgenteIntegration
from schemas.image_recognition import ImageRecognitionRequest, ImageRecognitionResponse

class ImageRecognitionService:
    # Modelos que soportan imágenes
    SUPPORTED_MODELS = {"gpt-4o", "gemini-2.5-flash", "gpt-4o-mini", "gemini-2.0-flash"}
    
    def __init__(self, session: Session):
        self.session = session

    async def analyze(self, request: ImageRecognitionRequest) -> ImageRecognitionResponse:
        if request.model not in self.SUPPORTED_MODELS:
            raise ValueError(f"El modelo '{request.model}' no soporta análisis de imágenes. Usa: {', '.join(self.SUPPORTED_MODELS)}")
        
        start_time = time.time()
        
        try:
            # Determinar proveedor basado en el modelo
            if "gpt" in request.model.lower() or "openai" in request.model.lower():
                result = AgenteIntegration.analyze_image_openai(
                    prompt=request.prompt,
                    image_url=request.image_url,
                    model=request.model
                )
            else:  # Gemini
                result = AgenteIntegration.analyze_image_gemini(
                    prompt=request.prompt,
                    image_url=request.image_url,
                    model=request.model
                )
            
            latency_ms = int((time.time() - start_time) * 1000)
            
            return ImageRecognitionResponse(
                description=result["response"],
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
            return ImageRecognitionResponse(
                description=f"Error: {str(e)}",
                model_used=request.model,
                metrics={"latency_ms": latency_ms}
            )