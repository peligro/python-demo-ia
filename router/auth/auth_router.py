# router/auth/auth_router.py
from fastapi import APIRouter, Depends, Response, Request, status
from fastapi.responses import JSONResponse
from sqlmodel import Session
from database.database import get_session
from services.auth.auth_service import AuthService
from schemas.auth import LoginRequest, MeResponse
from middleware.auth import get_current_user
from utilidades.redis_client import redis_client
import os

router = APIRouter(prefix="/auth", tags=["Authentication"])


def get_auth_service(session: Session = Depends(get_session)) -> AuthService:
    return AuthService(session)


@router.post("/login")
async def login(
    request: Request,
    login_data: LoginRequest,
    response: Response,
    service: AuthService = Depends(get_auth_service)
):
    """
    Login con cookie HttpOnly + Redis session
    - API C2: Token con TTL configurable + blacklist en logout
    - API C3: Cookie con SameSite + Secure dinámico según ENVIRONMENT
    """
    # 1. Verificar si ya hay sesión activa
    existing_token = request.cookies.get("remember_token")
    if existing_token:
        session_data = redis_client.get_session(existing_token)
        if session_data and not redis_client.is_blacklisted(existing_token):
            return JSONResponse(
                status_code=status.HTTP_409_CONFLICT,
                content={"estado": "error", "mensaje": "Ya existe una sesión activa. Cierra sesión primero."}
            )
    
    # 2. Intentar login
    try:
        token, user = service.login(
            login_data.email,
            login_data.password,
            login_data.remember
        )
    except ValueError as e:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"estado": "error", "mensaje": str(e)}
        )
    
    # 3. Configurar cookie segura (dinámico según ENVIRONMENT)
    is_production = os.getenv("ENVIRONMENT", "local") == "production"
    cookie_secure = is_production  # ✅ True solo en prod (HTTPS obligatorio)
    
    response.set_cookie(
        key="remember_token",
        value=token,
        max_age=86400 * 7 if login_data.remember else 86400,  # 7 días o 1 día
        httponly=True,           # ✅ No accesible desde JS (previene XSS)
        secure=cookie_secure,    # ✅ Solo HTTPS en producción
        samesite="lax",          # ✅ CSRF protection
        domain=os.getenv("COOKIE_DOMAIN", "") or None,  # Subdominios en prod
        path="/"
    )
    
    return {
        "status": "success",
        "message": "Login exitoso",
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email
        }
    }


@router.post("/logout")
async def logout(
    request: Request,
    response: Response,
    service: AuthService = Depends(get_auth_service)
):
    """
    Logout: invalida sesión en Redis + limpia cookie
    - API C2: Blacklist para prevenir reuso de token
    """
    # 1. Verificar si hay cookie
    token = request.cookies.get("remember_token")
    
    if not token:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"estado": "error", "mensaje": "No autenticado"}
        )
    
    # 2. Verificar si la sesión existe en Redis
    session_data = redis_client.get_session(token)
    if not session_data:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"estado": "error", "mensaje": "No autenticado"}
        )
    
    # 3. Invalidar sesión (blacklist + delete)
    service.logout(token)
    
    # 4. Limpiar cookie
    response.delete_cookie(
        key="remember_token",
        path="/",
        domain=os.getenv("COOKIE_DOMAIN", "") or None
    )
    
    return {
        "status": "success",
        "message": "Logout exitoso"
    }


@router.get("/me", response_model=MeResponse)
async def me(
    current_user: dict = Depends(get_current_user)
):
    """
    Obtener datos del usuario autenticado + módulos + items
    - API C1: Solo retorna módulos asignados al perfil del usuario (BOLA prevention)
    """
    user = current_user["user"]
    metadata = current_user["metadata"]
    modules_with_items = current_user["modules_with_items"]
    
    # Construir respuesta con módulos e items
    modules_response = []
    for mwi in modules_with_items:
        module = mwi["module"]
        items = mwi["items"]
        modules_response.append({
            "id": module.id,
            "name": module.name,
            "slug": module.slug,
            "items": [
                {"id": item.id, "name": item.name, "code": item.code}
                for item in items
            ]
        })
    
    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "metadata": metadata,
        "profile": metadata.profile if metadata else None,
        "state": metadata.state if metadata else None,
        "modules": modules_response
    }


@router.get("/check")
async def check_auth(
    current_user: dict = Depends(get_current_user)
):
    """
    Verificación ligera de sesión (para SPA: cargar app, heartbeat, detectar logout externo)
    """
    return {
        "authenticated": True,
        "user": {
            "id": current_user["user"].id,
            "name": current_user["user"].name,
            "email": current_user["user"].email
        }
    }