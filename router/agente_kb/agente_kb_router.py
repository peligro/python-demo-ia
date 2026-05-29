from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session
from database.database import get_session
from schemas.agente_kb import QueryRequest, QueryResponse
from services.agente_kb.agente_kb_service import AgenteKBService
from middleware.auth import get_current_user

router = APIRouter(prefix="/portfolio/agente-kb", tags=["Portfolio: Agente KB"])

@router.post("/query", response_model=QueryResponse, status_code=status.HTTP_200_OK)
async def query_agent(
    body: QueryRequest,
    session: Session = Depends(get_session),
    current_user: dict = Depends(get_current_user)
):
    """
    Endpoint principal del agente de conocimiento base.
    
    - Si hay match en KB: respuesta inmediata, costo $0
    - Si no: fallback a IA con contexto, costo controlado
    - Registra métricas en query_logs para auditoría
    """
    try:
        # Extraer datos del usuario del JWT
        user_id = current_user.get("id") or current_user.get("userId") or current_user.get("sub")
        user_name = (
            current_user.get("name") or 
            current_user.get("username") or 
            current_user.get("full_name") or 
            "Usuario"
        )
        
        # Crear servicio con la sesión inyectada 
        service = AgenteKBService(session)
        
        return await service.process_query(
            query=body.input,
            chat_id=body.chatId,
            user_id=user_id,
            user_name=user_name,
            model=body.model or "mistral-small-latest"
        )
        
    except Exception as e:
        # En producción, loguear el error completo
        print(f"[AgenteKB] Error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Error interno: {str(e)}"
        )