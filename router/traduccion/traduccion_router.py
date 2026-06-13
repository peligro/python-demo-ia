#router/traduccion/traduccion_router.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlmodel import Session
from database.database import get_session
from schemas.traduccion import TranslationRequest, TranslationResponse, TranslationHistoryResponse
from services.traduccion.traduccion_service import TraduccionService
from middleware.auth import get_current_user

router = APIRouter(prefix="/portfolio/traduccion-textos", tags=["Portfolio: Translate"])

@router.post("/translate", response_model=TranslationResponse, status_code=status.HTTP_200_OK)
async def translate_text(
    body: TranslationRequest,
    session: Session = Depends(get_session),
    current_user: dict = Depends(get_current_user)
):
    try:
        service = TraduccionService(session)
        return await service.translate(body)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/languages", response_model=list[dict])
async def list_languages():
    """Retorna lista de idiomas soportados"""
    from schemas.traduccion import LANGUAGES  # Importar desde schemas o definir aquí
    return LANGUAGES

@router.get("/history", response_model=TranslationHistoryResponse)
async def get_translation_history(
    limit: int = Query(20, ge=1, le=100),
    session: Session = Depends(get_session),
    current_user: dict = Depends(get_current_user)
):
    """Retorna historial de traducciones del usuario (implementación futura)"""
    # Por ahora retornamos vacío
    return TranslationHistoryResponse(items=[], total=0)