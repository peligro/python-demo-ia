from pydantic import BaseModel, Field, ConfigDict, field_validator
from datetime import datetime
from typing import Optional
import re

class ItemCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100, description="Nombre del ítem")
    code: str = Field(..., min_length=2, max_length=50, description="Código único del ítem")

    @field_validator("code")
    @classmethod
    def validate_code(cls, v: str) -> str:
        # ✅ CORREGIDO: Solo validar, NO convertir a mayúsculas
        v = v.strip()  # Solo quitar espacios
        if not re.match(r"^[A-Za-z0-9\-_]+$", v):  # ✅ Aceptar mayúsculas y minúsculas
            raise ValueError("El código solo puede contener letras, números, guiones y guiones bajos")
        return v

    model_config = ConfigDict(
        json_schema_extra={"example": {"name": "Ver todos los registros", "code": "view_all_register"}}
    )

class ItemUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100, description="Nuevo nombre del ítem")
    code: Optional[str] = Field(None, min_length=2, max_length=50, description="Nuevo código del ítem")

    @field_validator("code")
    @classmethod
    def validate_code(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        # ✅ CORREGIDO: Solo validar, NO convertir a mayúsculas
        v = v.strip()
        if not re.match(r"^[A-Za-z0-9\-_]+$", v):
            raise ValueError("El código solo puede contener letras, números, guiones y guiones bajos")
        return v

    model_config = ConfigDict(
        json_schema_extra={"example": {"name": "Monitor Samsung 27\"", "code": "IT-MON-042"}}
    )

class ItemPublic(BaseModel):
    id: int
    name: str
    code: str
    model_config = ConfigDict(from_attributes=True)

class ItemRead(BaseModel):
    id: int
    name: str
    code: str
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

class ItemListResponse(BaseModel):
    total: int
    page: int
    limit: int
    data: list[ItemPublic]
    model_config = ConfigDict(from_attributes=True)