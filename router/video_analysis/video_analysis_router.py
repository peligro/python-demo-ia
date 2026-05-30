from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session
from database.database import get_session
from schemas.video_analysis import VideoAnalysisRequest, VideoAnalysisResponse
from services.video_analysis.video_analysis_service import VideoAnalysisService
from middleware.auth import get_current_user

router = APIRouter(prefix="/portfolio/video-analysis", tags=["Portfolio: Video Analysis"])

@router.post("/analyze", response_model=VideoAnalysisResponse, status_code=status.HTTP_200_OK)
async def analyze_video(
    body: VideoAnalysisRequest,
    session: Session = Depends(get_session),
    current_user: dict = Depends(get_current_user)
):
    try:
        service = VideoAnalysisService(session)
        return await service.analyze(body)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))