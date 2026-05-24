from fastapi import status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

class DisableOptionsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.method.upper() == "OPTIONS":
            # ✅ 204 No Content: no revela métodos permitidos (mitiga API B1)
            return Response(status_code=status.HTTP_204_NO_CONTENT)
        return await call_next(request)