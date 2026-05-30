from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime, timezone

class GenerateSQLRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=500, description="Pregunta en lenguaje natural")
    model: Optional[str] = Field(default="mistral-small-latest", description="Modelo de IA")
    dialect: Optional[Literal["postgresql", "mysql", "sqlite", "mssql"]] = Field(
        default="postgresql", description="Dialecto SQL"
    )

class GenerateSQLResponse(BaseModel):
    question: str
    sql_query: str
    explanation: Optional[str] = None
    dialect: str
    model_used: str
    metrics: dict  # tokens, latency
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    # Campos de la tabla para referencia
    table_schema: dict = {
        "table": "usuarios",
        "columns": [
            {"name": "id", "type": "int", "description": "ID único"},
            {"name": "name", "type": "string", "description": "Nombre del usuario"},
            {"name": "correo", "type": "string", "description": "Email del usuario"},
            {"name": "password", "type": "string", "description": "Password (hash)"},
            {"name": "state", "type": "int", "description": "Estado: 1=activo, 0=inactivo"},
            {"name": "created_ut", "type": "datetime", "description": "Fecha de creación"},
            {"name": "updated_at", "type": "datetime", "description": "Fecha de actualización"},
            {"name": "phone", "type": "string", "description": "Teléfono"},
        ]
    }
