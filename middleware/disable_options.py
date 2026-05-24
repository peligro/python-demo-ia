from fastapi import status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
import os

class DisableOptionsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.method.upper() == "OPTIONS":
            # ✅ Permitir OPTIONS solo para preflight CORS (orígenes permitidos)
            origin = request.headers.get("origin", "")
            allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(",")
            
            if origin in allowed_origins:
                # Deja que CORS maneje el preflight
                return await call_next(request)
            else:
                # Bloquear OPTIONS para otros orígenes (mitiga API B1)
                return Response(status_code=status.HTTP_204_NO_CONTENT)
        
        return await call_next(request)