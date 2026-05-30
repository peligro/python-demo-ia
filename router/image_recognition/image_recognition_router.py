# router/image_recognition/image_recognition_router.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session
from database.database import get_session
from schemas.image_recognition import ImageRecognitionRequest, ImageRecognitionResponse
from services.image_recognition.image_recognition_service import ImageRecognitionService
from middleware.auth import get_current_user

router = APIRouter(prefix="/portfolio/image-recognition", tags=["Portfolio: Image Recognition"])

@router.post("/analyze", response_model=ImageRecognitionResponse, status_code=status.HTTP_200_OK)
async def analyze_image(
    body: ImageRecognitionRequest,
    session: Session = Depends(get_session),
    current_user: dict = Depends(get_current_user)
):
    try:
        service = ImageRecognitionService(session)
        return await service.analyze(body)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))