from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from fastapi import status

class DisableOptionsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.method == "OPTIONS":
            # Permitir solo en rutas esenciales y de documentación
            allowed_paths = ["/docs", "/openapi.json", "/redoc", "/health", "/favicon.ico"]
            if any(request.url.path.startswith(p) for p in allowed_paths):
                return await call_next(request)

            # API B1: Bloquear OPTIONS para evitar divulgación de métodos HTTP
            return Response(status_code=status.HTTP_405_METHOD_NOT_ALLOWED)

        return await call_next(request)