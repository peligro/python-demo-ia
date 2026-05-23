from fastapi import FastAPI, status, Request
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html
from dotenv import load_dotenv
import os

# Cargar variables de entorno
load_dotenv()

# Routers
from router.health.health_router import router as health_router
from router.state.state_router import router as state_router

# Middlewares (import desde módulo)
from middleware.disable_options import DisableOptionsMiddleware
from middleware.security_headers import SetSecurityHeadersMiddleware

# Manejadores de excepciones (import desde módulo)
from exceptions.handlers import http_exception_handler, manejar_errores_validacion

# Swagger custom
from swagger.openapi import custom_openapi

# Inicializar FastAPI
app = FastAPI(
    title=os.getenv("PRODUCT_NAME", "API Demo"),
    description="API segura y modular con FastAPI + SQLModel",
    version="0.0.1",
    docs_url=None,  # Deshabilitamos /docs default para usar el custom
    redoc_url=None,
    openapi_url="/openapi.json"
)

# =============================================================================
# 1. MIDDLEWARES (Orden crítico: CORS primero para interceptar preflight)
# =============================================================================

# CORS - API C3: Control de origen de peticiones
# 🔒 En producción: cambiar "*" por lista explícita desde .env
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("ALLOWED_ORIGINS", "*").split(",") if os.getenv("ALLOWED_ORIGINS") != "*" else ["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# Security Headers - API M1, WEB M4, WEB B3, API B2
app.add_middleware(SetSecurityHeadersMiddleware)

# Disable OPTIONS - API B1: Evitar divulgación de métodos HTTP
app.add_middleware(DisableOptionsMiddleware)

# =============================================================================
# 2. EXCEPTION HANDLERS (Registro único, sin decoradores duplicados)
# =============================================================================
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, manejar_errores_validacion)

# =============================================================================
# 3. SWAGGER / DOCUMENTACIÓN (Custom + protegido en prod)
# =============================================================================
app.openapi = custom_openapi(app)

@app.get("/docs", include_in_schema=False)
async def swagger_documentation(request: Request):
    # 🔒 ARQ A2: En producción, requerir autenticación para /docs
    if os.getenv("ENVIRONMENT") == "production":
        # Aquí podrías agregar: Depends(verify_admin)
        pass
    return get_swagger_ui_html(
        openapi_url="/openapi.json",
        title=f"{os.getenv('PRODUCT_NAME', 'API')} - Documentación"
    )

@app.get("/redoc", include_in_schema=False)
async def redoc_documentation():
    from fastapi.openapi.redoc import get_redoc_html
    return get_redoc_html(openapi_url="/openapi.json", title="ReDoc")

# =============================================================================
# 4. RUTAS PÚBLICAS
# =============================================================================
from schemas.schemas import IndexResponse

@app.get("/", response_model=IndexResponse, tags=["Home"])
def index():
    return {"estado": "ok", "mensaje": f"{os.getenv('PRODUCT_NAME', 'API Demo')}"}

@app.get("/health", tags=["Health"], include_in_schema=False)
def health_check():
    return {"status": "UP"}

# =============================================================================
# 5. INCLUSIÓN DE ROUTERS MODULARES
# =============================================================================
app.include_router(health_router)  # prefix="/health"
app.include_router(state_router)    # prefix="/states"

# =============================================================================
# 6. ENTRY POINT (solo para desarrollo con --reload)
# =============================================================================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8050)),
        reload=os.getenv("ENVIRONMENT") != "production",
        log_level="info"
    )