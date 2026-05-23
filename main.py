from fastapi import FastAPI, status, Request
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from swagger.openapi import custom_openapi
from fastapi.openapi.docs import get_swagger_ui_html
from schemas.schemas import IndexResponse

#dotenv
from dotenv import load_dotenv
load_dotenv()
import os

#rutas
from router.health.health_router import router as health_router

 


#inicializamos FastAPI
app = FastAPI()
 

#configuración de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials = True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Middlewares
from middleware import SetSecurityHeadersMiddleware, DisableOptionsMiddleware

# Excepciones
from exceptions import http_exception_handler, manejar_errores_validacion

#swagger
app.openapi = custom_openapi(app)
@app.get("/docs", include_in_schema=False)
async def swagger_documentation():
    return get_swagger_ui_html(openapi_url="/openapi.json", title=f"{os.getenv('PRODUCT_NAME')}")



# Ruta raíz
@app.get("/", response_model=IndexResponse, tags=["Home"])
def index():
    return {"estado": "ok", "mensaje": f"{os.getenv('PRODUCT_NAME')}"}

# Incluir routers
app.include_router(health_router)

#custom 404
@app.exception_handler(status.HTTP_404_NOT_FOUND)
async def custom_404_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"estado":"error", "mensaje":"Ruta no encontrada"}
    )


#para métodos HTTP no usados {"detail": "Method Not Allowed"}
@app.exception_handler(StarletteHTTPException)
async def custom_405_handler(request: Request, exc: StarletteHTTPException):
    if exc.status_code == status.HTTP_405_METHOD_NOT_ALLOWED:
        return JSONResponse(
            status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
            content={"estado": "error", "mensaje": "Método no permitido"},
        )
    # Para otras excepciones que puedan llegar aquí
    return JSONResponse(
        status_code=exc.status_code,
        content={"estado": "error", "mensaje": str(exc.detail)},
    )


#validaciones dto
@app.exception_handler(RequestValidationError)
async def manejar_errores_validacion(request: Request, exc: RequestValidationError):
    errores_personalizados = []

    for error in exc.errors():
        campo = error["loc"][-1]
        mensaje = error["msg"]

        # Procesar ValueError con ("campo", "mensaje")
        if mensaje.startswith("Value error,"):
            try:
                _, custom_msg = eval(error["input"])
                mensaje = custom_msg
            except:
                pass

        elif mensaje == "Input should be a valid integer":
            mensaje = f"El campo {campo} debe ser un número entero"

        elif mensaje == "Field required":
            mensaje = f"El campo {campo} es obligatorio"

        errores_personalizados.append({
            "campo": campo,
            "mensaje": mensaje
        })

    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "estado": "error",
            "mensaje": "Errores de validación",
            "errores": errores_personalizados
        },
    )


# docker exec -it python_service uvicorn main:app --host 0.0.0.0 --port 8050 --reload


