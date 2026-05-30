from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session
from database.database import get_session
from schemas.analisis_sentimiento import (
    SentimentAnalysisRequest, 
    SentimentAnalysisResponse,
    SentimentHistoryResponse
)
from services.analisis_sentimiento.analisis_sentimiento_service import AnalisisSentimientoService
from middleware.auth import get_current_user

router = APIRouter(prefix="/portfolio/analisis-de-sentimiento", tags=["Portfolio: Sentiment Analysis"])

@router.post("/analyze", response_model=SentimentAnalysisResponse, status_code=status.HTTP_200_OK)
async def analyze_sentiment(
    body: SentimentAnalysisRequest,
    session: Session = Depends(get_session),
    current_user: dict = Depends(get_current_user)
):
    try:
        service = AnalisisSentimientoService(session)
        return await service.analyze(body)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/history", response_model=SentimentHistoryResponse)
async def get_sentiment_history(
    limit: int = 20,
    session: Session = Depends(get_session),
    current_user: dict = Depends(get_current_user)
):
    """Retorna historial de análisis (placeholder para futura implementación con BD)"""
    return SentimentHistoryResponse(items=[], total=0)