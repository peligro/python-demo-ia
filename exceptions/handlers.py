# exceptions/handlers.py

from fastapi import status
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.exceptions import RequestValidationError


async def http_exception_handler(request, exc: StarletteHTTPException):
    # Manejo especial para 404
    if exc.status_code == status.HTTP_404_NOT_FOUND:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"estado": "error", "mensaje": "Ruta no encontrada"}
        )

    # Manejo especial para 405
    if exc.status_code == status.HTTP_405_METHOD_NOT_ALLOWED:
        return JSONResponse(
            status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
            content={"estado": "error", "mensaje": "Método no permitido"},
        )

    # Para cualquier otro error HTTP (400, 401, 403, 500, etc.)
    return JSONResponse(
        status_code=exc.status_code,
        content={"estado": "error", "mensaje": str(exc.detail)},
    )


# El handler de validación sigue siendo separado (es otra excepción)
async def manejar_errores_validacion(request, exc: RequestValidationError):
    errores_personalizados = []
    for error in exc.errors():
        campo = error["loc"][-1]
        mensaje = error["msg"]

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

        errores_personalizados.append({"campo": campo, "mensaje": mensaje})

    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "estado": "error",
            "mensaje": "Errores de validación",
            "errores": errores_personalizados
        },
    )