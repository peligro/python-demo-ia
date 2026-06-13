#router/chat_history/chat_history_router.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session
from database.database import get_session
from schemas.chat_history import ChatHistoryRequest, ChatHistoryResponse
from services.chat_history.chat_history_service import ChatHistoryService
from middleware.auth import get_current_user

router = APIRouter(prefix="/portfolio/chat-history", tags=["Portfolio: Chat History"])

@router.post("/chat", response_model=ChatHistoryResponse, status_code=status.HTTP_200_OK)
async def chat_with_history(
    body: ChatHistoryRequest,
    session: Session = Depends(get_session),
    current_user: dict = Depends(get_current_user)
):
    try:
        service = ChatHistoryService(session)
        return await service.chat(body)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))