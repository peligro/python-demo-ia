#router/audio_transcript/audio_transcript_router.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session
from database.database import get_session
from schemas.audio_transcript import AudioTranscriptRequest, AudioTranscriptResponse
from services.audio_transcript.audio_transcript_service import AudioTranscriptService
from middleware.auth import get_current_user

router = APIRouter(prefix="/portfolio/audio-transcript", tags=["Portfolio: Audio Transcript"])

@router.post("/transcribe", response_model=AudioTranscriptResponse, status_code=status.HTTP_200_OK)
async def transcribe_audio(
    body: AudioTranscriptRequest,
    session: Session = Depends(get_session),
    current_user: dict = Depends(get_current_user)
):
    try:
        service = AudioTranscriptService(session)
        return await service.transcribe(body)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))