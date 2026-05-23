from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request as StarletteRequest
import os

class SetSecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: StarletteRequest, call_next):
        response = await call_next(request)

        # Rutas donde NO aplicar CSP restrictivo (Swagger UI)
        doc_paths = ["/docs", "/documentacion", "/redoc"]
        path = request.url.path

        # 👇 Encabezados anti-caché (siempre)
        response.headers["Cache-Control"] = "no-store"
        response.headers["Pragma"] = "no-cache"

        # 👇 Eliminar headers sensibles
        if "server" in response.headers:
            del response.headers["server"]
        if "x-powered-by" in response.headers:
            del response.headers["x-powered-by"]

        # 👇 Encabezados de seguridad OWASP (siempre)
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # 👇 HSTS (solo producción)
        if os.getenv("ENVIRONMENT") == "production":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"

        # 👇 CSP: solo en rutas NO de documentación
        if not any(path.startswith(p) for p in doc_paths):
            csp_policy = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data:; "
                "font-src 'self'; "
                "connect-src 'self'; "
                "frame-ancestors 'none';"
            )
            response.headers["Content-Security-Policy"] = csp_policy

        return response