#schemas/module.py
from pydantic import BaseModel, Field, ConfigDict, field_validator
from datetime import datetime
from typing import Optional
import re


class ModuleCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100, description="Nombre del módulo")
    slug: str = Field(..., min_length=2, max_length=100, description="Slug tipo ruta (ej: /settings/users)")

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, v: str) -> str:
        v = v.lower().strip()
        if not v.startswith("/"):
            raise ValueError("El slug debe comenzar con '/'")
        if not re.match(r"^\/[a-z0-9\-_\/]+$", v):
            raise ValueError("El slug solo puede contener letras minúsculas, números, guiones, guiones bajos y '/'")
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "example": {"name": "Usuarios", "slug": "/settings/users"}
        }
    )


class ModuleUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100, description="Nuevo nombre del módulo")
    slug: Optional[str] = Field(None, min_length=2, max_length=100, description="Nuevo slug del módulo")

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v = v.lower().strip()
        if not v.startswith("/"):
            raise ValueError("El slug debe comenzar con '/'")
        if not re.match(r"^\/[a-z0-9\-_\/]+$", v):
            raise ValueError("El slug solo puede contener letras minúsculas, números, guiones, guiones bajos y '/'")
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "example": {"name": "Administración de Usuarios", "slug": "/admin/users"}
        }
    )


# ✅ Para listados: solo lo esencial
class ModulePublic(BaseModel):
    id: int
    name: str
    slug: str
    model_config = ConfigDict(from_attributes=True)


# ✅ Para detalle: con metadatos completos
class ModuleRead(BaseModel):
    id: int
    name: str
    slug: str
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class ModuleListResponse(BaseModel):
    total: int
    page: int
    limit: int
    data: list[ModulePublic]
    model_config = ConfigDict(from_attributes=True)