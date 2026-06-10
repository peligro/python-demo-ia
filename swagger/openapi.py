from fastapi.openapi.utils import get_openapi
from dotenv import load_dotenv
import os
# Cargar variables de entorno
load_dotenv()


# Descripción general de la API
DESCRIPTION = f"Documentación oficial de {os.getenv('PRODUCT_NAME')}"

# Información de contacto
CONTACT_INFO = {
    "name": f"{os.getenv('FRONTEND_URL')}",
    "url": f"{os.getenv('FRONTEND_URL')}", 
    "email": "yo@cesarcancino.com"
}

# Licencia
LICENSE_INFO = {
    "name": "Apache 2.0",
    "url": "https://www.apache.org/licenses/LICENSE-2.0.html" 
}

# Términos de servicio
TERMS_OF_SERVICE = f"{os.getenv('FRONTEND_URL')}" 

# Etiquetas de OpenAPI (tags)
OPENAPI_TAGS = [
    {"name": "Home", "description": "Home"},
    {"name": "Health", "description": "Endpoint de salud"},
    {"name": "State", "description": "Listar estados"},
    {"name": "Module", "description": "Listar módulos"},
    {"name": "Profile", "description": "Listar perfiles"},
    {"name": "Item", "description": "Listar ítems"},
    {"name": "User", "description": "Listar usuarios"},
    {"name": "App Menu", "description": "Listar menús de la aplicación"},
    {"name": "Home Menu", "description": "Listar menús del home"},
    {"name": "Authentication", "description": "Endpoints de autenticación"},
    {"name": "Portfolio: Prompt Basic", "description": "Endpoints relacionados con el agente de prompt básico"},
    {"name": "Portfolio: Translate", "description": "Endpoints relacionados con la traducción de textos"},
    {"name": "Portfolio: Sentiment Analysis", "description": "Endpoints relacionados con el análisis de sentimiento"},
    {"name": "Portfolio: Generate SQL", "description": "Endpoints relacionados con la generación de consultas SQL a partir de preguntas en lenguaje natural"},
    {"name": "Portfolio: Chat History", "description": "Endpoints relacionados con el chat con historial de mensajes"},
    {"name": "Portfolio: Image Recognition", "description": "Endpoints relacionados con el análisis de imágenes"},
    {"name": "Portfolio: Audio Transcript", "description": "Endpoints relacionados con la transcripción de audio"},
    {"name": "Portfolio: Video Analysis", "description": "Endpoints relacionados con el análisis de videos"},
    {"name": "Portfolio: Agente KB", "description": "Endpoints relacionados con el agente de conocimiento base"},
    {"name": "Portfolio: Agente KB Logs", "description": "Endpoints relacionados con los logs del agente de conocimiento base"},
    {"name": "Portfolio: RAG PDF", "description": "Endpoints relacionados con el agente RAG para PDFs"},
]

# Función para generar el esquema OpenAPI personalizado
def custom_openapi(app):
    def generate_openapi():
        if app.openapi_schema:
            return app.openapi_schema

        openapi_schema = get_openapi(
            title=f"{os.getenv('PRODUCT_NAME')}",
            version="0.0.1",
            description=DESCRIPTION,
            routes=app.routes,
            tags=OPENAPI_TAGS
        )

        # Añade info adicional
        openapi_schema["info"]["termsOfService"] = TERMS_OF_SERVICE
        openapi_schema["info"]["license"] = LICENSE_INFO
        openapi_schema["info"]["contact"] = CONTACT_INFO

        

        app.openapi_schema = openapi_schema
        return app.openapi_schema

    return generate_openapi

