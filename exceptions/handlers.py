from fastapi import status
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.exceptions import RequestValidationError

async def http_exception_handler(request, exc: StarletteHTTPException):
    if exc.status_code == status.HTTP_404_NOT_FOUND:
        return JSONResponse(status_code=404, content={"estado": "error", "mensaje": "Ruta no encontrada"})
    if exc.status_code == status.HTTP_405_METHOD_NOT_ALLOWED:
        return JSONResponse(status_code=405, content={"estado": "error", "mensaje": "Método no permitido"})
    return JSONResponse(status_code=exc.status_code, content={"estado": "error", "mensaje": str(exc.detail)})

async def manejar_errores_validacion(request, exc: RequestValidationError):
    errores = []
    for error in exc.errors():
        # Pydantic V2: loc es ('body', 'campo', ...) o ('query', 'campo')
        campo = ".".join(str(x) for x in error["loc"][1:]) if len(error["loc"]) > 1 else "desconocido"
        mensaje = error.get("msg", "Error de validación")

        # ✅ Limpieza segura sin eval() (Vulnerabilidad RCE eliminada)
        if mensaje.startswith("Value error, "):
            mensaje = mensaje[len("Value error, "):]
        elif "Input should be a valid" in mensaje or "string type expected" in mensaje:
            mensaje = f"El campo {campo} tiene un formato inválido"
        elif mensaje == "Field required":
            mensaje = f"El campo {campo} es obligatorio"

        errores.append({"campo": campo, "mensaje": mensaje})

    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"estado": "error", "mensaje": "Errores de validación", "errores": errores}
    )