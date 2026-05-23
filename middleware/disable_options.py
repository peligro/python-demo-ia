# middleware/disable_options.py

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request as StarletteRequest
from starlette.responses import Response
from fastapi import status

class DisableOptionsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: StarletteRequest, call_next):
        if request.method == "OPTIONS":
            path = request.url.path

            # Rutas que deben permitir OPTIONS con respuesta CORS
            cors_paths = [
                "/openapi.json",
                "/docs",
                "/documentacion",
                "/redoc",
            ]

            if any(path.startswith(p) for p in cors_paths):
                # Responder con headers CORS mínimos
                return Response(
                    status_code=status.HTTP_204_NO_CONTENT,
                    headers={
                        "Access-Control-Allow-Origin": "*",
                        "Access-Control-Allow-Methods": "GET, OPTIONS",
                        "Access-Control-Allow-Headers": "*",
                    }
                )

            # Para todas las demás rutas: bloquear OPTIONS
            return Response(status_code=status.HTTP_204_NO_CONTENT)

        return await call_next(request)