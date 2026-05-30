from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session
from database.database import get_session
from schemas.generate_sql import GenerateSQLRequest, GenerateSQLResponse
from services.generate_sql.generate_sql_service import GenerateSQLService
from middleware.auth import get_current_user

router = APIRouter(prefix="/portfolio/generate-sql", tags=["Portfolio: Generate SQL"])

@router.post("/generate", response_model=GenerateSQLResponse, status_code=status.HTTP_200_OK)
async def generate_sql(
    body: GenerateSQLRequest,
    session: Session = Depends(get_session),
    current_user: dict = Depends(get_current_user)
):
    try:
        service = GenerateSQLService(session)
        return await service.generate(body)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))