#services/video_analysis/video_analysis_service.py
import time
import os
from typing import Optional
from sqlmodel import Session
from integraciones.agente_integration import AgenteIntegration
from schemas.video_analysis import VideoAnalysisRequest, VideoAnalysisResponse

class VideoAnalysisService:
    # Tamaño máximo: 20MB (límite de Gemini)
    MAX_VIDEO_SIZE_MB = 20
    
    def __init__(self, session: Session):
        self.session = session

    async def analyze(self, request: VideoAnalysisRequest) -> VideoAnalysisResponse:
        start_time = time.time()
        
        # Construir ruta absoluta segura
        full_path = os.path.join(os.getcwd(), request.video_path)
        
        # Validar que el archivo existe
        if not os.path.exists(full_path):
            raise FileNotFoundError(f"Archivo de video no encontrado: {request.video_path}")
        
        # Validar tamaño del archivo
        file_size_mb = os.path.getsize(full_path) / (1024 * 1024)
        if file_size_mb > self.MAX_VIDEO_SIZE_MB:
            raise ValueError(f"El video es demasiado grande ({file_size_mb:.1f}MB). Máximo {self.MAX_VIDEO_SIZE_MB}MB")
        
        try:
            # Llamar a Gemini para análisis de video
            result = AgenteIntegration.analyze_video_gemini(
                video_file_path=full_path,
                model=request.model,
                prompt=request.prompt
            )
            
            latency_ms = int((time.time() - start_time) * 1000)
            
            return VideoAnalysisResponse(
                analysis=result["analysis"],
                model_used=request.model,
                video_duration_seconds=result.get("duration"),
                metrics={
                    "input_tokens": result["usage"]["input"],
                    "output_tokens": result["usage"]["output"],
                    "total_tokens": result["usage"]["total"],
                    "latency_ms": latency_ms
                }
            )
        except Exception as e:
            latency_ms = int((time.time() - start_time) * 1000)
            return VideoAnalysisResponse(
                analysis=f"Error: {str(e)}",
                model_used=request.model,
                metrics={"latency_ms": latency_ms}
            )