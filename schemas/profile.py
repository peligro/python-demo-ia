from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional


class ProfileCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100, description="Nombre del perfil")
    description: str = Field(..., min_length=10, max_length=500, description="Descripción del perfil")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {"name": "Administrador", "description": "Perfil con acceso total al sistema"}
        }
    )


class ProfileUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100, description="Nuevo nombre del perfil")
    description: Optional[str] = Field(None, min_length=10, max_length=500, description="Nueva descripción")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {"name": "Super Admin", "description": "Perfil con privilegios elevados"}
        }
    )


# ✅ Para listados: solo lo esencial
class ProfilePublic(BaseModel):
    id: int
    name: str
    description: str
    model_config = ConfigDict(from_attributes=True)


# ✅ Para detalle: con metadatos completos
class ProfileRead(BaseModel):
    id: int
    name: str
    description: str
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)
