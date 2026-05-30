import time
import os
from typing import Optional
from sqlmodel import Session
from integraciones.agente_integration import AgenteIntegration
from schemas.audio_transcript import AudioTranscriptRequest, AudioTranscriptResponse

class AudioTranscriptService:
    # Modelos soportados para transcripción
    SUPPORTED_MODELS = {"whisper-1", "gemini-2.5-flash", "gemini-2.0-flash"}
    
    # Rutas base para archivos de audio (configurables)
    AUDIO_BASE_PATH = os.getenv('AUDIO_BASE_PATH', 'static/audio')
    
    def __init__(self, session: Session):
        self.session = session

    async def transcribe(self, request: AudioTranscriptRequest) -> AudioTranscriptResponse:
        if request.model not in self.SUPPORTED_MODELS:
            raise ValueError(f"El modelo '{request.model}' no soporta transcripción de audio. Usa: {', '.join(self.SUPPORTED_MODELS)}")
        
        start_time = time.time()
        
        # Construir ruta absoluta segura
        full_path = os.path.join(os.getcwd(), request.audio_path)
        
        # Validar que el archivo existe y es accesible
        if not os.path.exists(full_path):
            raise FileNotFoundError(f"Archivo de audio no encontrado: {request.audio_path}")
        
        try:
            # Determinar proveedor basado en el modelo
            if request.model == "whisper-1":
                result = AgenteIntegration.transcribe_audio_openai(
                    audio_file_path=full_path,
                    language=request.language
                )
            else:  # Gemini
                result = AgenteIntegration.transcribe_audio_gemini(
                    audio_file_path=full_path,
                    model=request.model,
                    language=request.language
                )
            
            latency_ms = int((time.time() - start_time) * 1000)
            
            return AudioTranscriptResponse(
                transcription=result["transcription"],
                model_used=request.model,
                audio_duration_seconds=result.get("duration"),
                detected_language=result.get("detected_language"),
                metrics={
                    "input_tokens": result["usage"]["input"],
                    "output_tokens": result["usage"]["output"],
                    "total_tokens": result["usage"]["total"],
                    "latency_ms": latency_ms
                }
            )
        except Exception as e:
            latency_ms = int((time.time() - start_time) * 1000)
            return AudioTranscriptResponse(
                transcription=f"Error: {str(e)}",
                model_used=request.model,
                metrics={"latency_ms": latency_ms}
            )