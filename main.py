# main.py
from fastapi import FastAPI, status, Request
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html
from slowapi.middleware import SlowAPIMiddleware
from slowapi.errors import RateLimitExceeded
from dotenv import load_dotenv
import os

load_dotenv()

# Routers
from router.health.health_router import router as health_router
from router.state.state_router import router as state_router
from router.profile.profile_router import router as profile_router
from router.module.module_router import router as module_router
from router.item.item_router import router as item_router
from router.user.user_router import router as user_router
from router.auth.auth_router import router as auth_router
from router.app_menu.app_menu_router import router as app_menu_router
from router.home_menu.home_menu_router import router as home_menu_router
from router.agente_kb.agente_kb_router import router as agente_kb_router



# Middlewares (sin API Key - usamos cookies HttpOnly)
from middleware.security_headers import SecurityHeadersMiddleware
from middleware.rate_limiter import limiter
from middleware.disable_options import DisableOptionsMiddleware

# Swagger
from swagger.openapi import custom_openapi

app = FastAPI(
    title=os.getenv("PRODUCT_NAME", "API Demo"),
    description="API modular con FastAPI + SQLModel",
    version="0.0.1",
    docs_url=None,  # Deshabilitamos /docs default
    redoc_url=None,
    openapi_url="/openapi.json"
)

# =============================================================================
# MIDDLEWARES
# =============================================================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,  # ✅ Necesario para cookies
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(DisableOptionsMiddleware)
app.add_middleware(SecurityHeadersMiddleware)

# Rate limiting con slowapi (automático con default_limits)
app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)

# =============================================================================
# EXCEPTION HANDLERS
# =============================================================================
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    if exc.status_code == status.HTTP_404_NOT_FOUND:
        return JSONResponse(status_code=404, content={"estado": "error", "mensaje": "Ruta no encontrada"})
    if exc.status_code == status.HTTP_405_METHOD_NOT_ALLOWED:
        return JSONResponse(status_code=405, content={"estado": "error", "mensaje": "Método no permitido"})
    return JSONResponse(status_code=exc.status_code, content={"estado": "error", "mensaje": str(exc.detail)})

@app.exception_handler(RequestValidationError)
async def manejar_errores_validacion(request: Request, exc: RequestValidationError):
    errores = []
    for error in exc.errors():
        campo = ".".join(str(x) for x in error["loc"][1:]) if len(error["loc"]) > 1 else "desconocido"
        mensaje = error.get("msg", "Error de validación")
        if mensaje.startswith("Value error, "):
            mensaje = mensaje[len("Value error, "):]
        elif "Input should be a valid" in mensaje or "string type expected" in mensaje:
            mensaje = f"El campo {campo} tiene un formato inválido"
        elif mensaje == "Field required":
            mensaje = f"El campo {campo} es obligatorio"
        errores.append({"campo": campo, "mensaje": mensaje})
    return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"estado": "error", "mensaje": "Errores de validación", "errores": errores})

@app.exception_handler(RateLimitExceeded)
async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={"estado": "error", "mensaje": "Demasiadas solicitudes. Intenta más tarde."}
    )

# =============================================================================
# SWAGGER (solo en local/development)
# =============================================================================
app.openapi = custom_openapi(app)

# ✅ Solo mostrar documentación si NO es producción
if os.getenv("ENVIRONMENT") != "production":
    @app.get("/docs", include_in_schema=False)
    async def swagger_documentation():
        return get_swagger_ui_html(openapi_url="/openapi.json", title=f"{os.getenv('PRODUCT_NAME', 'API')} - Documentación")

    @app.get("/redoc", include_in_schema=False)
    async def redoc_documentation():
        from fastapi.openapi.docs import get_redoc_html
        return get_redoc_html(openapi_url="/openapi.json", title="ReDoc")

# =============================================================================
# RUTAS
# =============================================================================
from schemas.schemas import IndexResponse

@app.get("/", response_model=IndexResponse, tags=["Home"])
def index():
    return {"estado": "ok", "mensaje": f"{os.getenv('PRODUCT_NAME', 'API Demo')}"}

@app.get("/health", tags=["Health"], include_in_schema=False)
def health_check():
    return {"status": "UP"}

app.include_router(health_router)
app.include_router(state_router)
app.include_router(profile_router)
app.include_router(module_router)
app.include_router(item_router)
app.include_router(user_router)
app.include_router(app_menu_router)
app.include_router(auth_router)
app.include_router(home_menu_router)
app.include_router(agente_kb_router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=int(os.getenv("PORT", 8050)), reload=os.getenv("ENVIRONMENT") != "production")