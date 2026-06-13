#router/prompt_basic/prompt_basic_router.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session
from database.database import get_session
from schemas.prompt_basic import PromptBasicRequest, PromptBasicResponse
from services.prompt_basic.prompt_basic_service import PromptBasicService
from middleware.auth import get_current_user

router = APIRouter(prefix="/portfolio/prompt-basic", tags=["Portfolio: Prompt Basic"])

@router.post("/query", response_model=PromptBasicResponse, status_code=status.HTTP_200_OK)
async def query_prompt(
    body: PromptBasicRequest,
    session: Session = Depends(get_session),
    current_user: dict = Depends(get_current_user)
):
    try:
        service = PromptBasicService(session)
        return await service.process_query(body)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))