from fastapi import FastAPI, status, Request
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html
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


# Swagger custom
from swagger.openapi import custom_openapi

app = FastAPI(
    title=os.getenv("PRODUCT_NAME", "API Demo"),
    description="API modular con FastAPI + SQLModel",
    version="0.0.1",
    docs_url=None,
    redoc_url=None,
    openapi_url="/openapi.json"
)

# =============================================================================
# CORS BÁSICO (sin configuración compleja por ahora)
# =============================================================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 🔒 Cambiar en producción
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =============================================================================
# EXCEPTION HANDLERS (inline, sin imports problemáticos)
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

# =============================================================================
# SWAGGER
# =============================================================================
app.openapi = custom_openapi(app)

@app.get("/docs", include_in_schema=False)
async def swagger_documentation():
    return get_swagger_ui_html(openapi_url="/openapi.json", title=f"{os.getenv('PRODUCT_NAME', 'API')} - Documentación")

@app.get("/redoc", include_in_schema=False)
async def redoc_documentation():
    from fastapi.openapi.redoc import get_redoc_html
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=int(os.getenv("PORT", 8050)), reload=os.getenv("ENVIRONMENT") != "production")