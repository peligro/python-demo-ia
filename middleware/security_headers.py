from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
import os

class SetSecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # API B2: Anti-cache para respuestas sensibles
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"

        # WEB B3: Eliminar divulgación de tecnología
        response.headers.pop("server", None)
        response.headers.pop("x-powered-by", None)

        # OWASP Secure Headers (API M1 / WEB M4)
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"

        # HSTS solo en producción
        if os.getenv("ENVIRONMENT") == "production":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"

        # CSP restrictivo para APIs, mínimo necesario para Docs
        doc_paths = ["/docs", "/openapi.json", "/redoc"]
        if not any(request.url.path.startswith(p) for p in doc_paths):
            response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none';"
        else:
            # Swagger/Redoc necesitan cargar assets externos
            response.headers["Content-Security-Policy"] = (
                "default-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
                "img-src 'self' data:; "
                "font-src 'self' https://fonts.gstatic.com;"
            )

        return response