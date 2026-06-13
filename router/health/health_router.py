#router/health/health_router.py
from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from schemas.schemas import HealthResponse

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("", response_model=HealthResponse)
async def index():
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"status": "UP!!",}
    )

