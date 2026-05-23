from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional


class StateCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    model_config = ConfigDict(json_schema_extra={"example": {"name": "Activo"}})


class StateUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    model_config = ConfigDict(json_schema_extra={"example": {"name": "Inactivo"}})


# ✅ Para listados: solo lo esencial
class StatePublic(BaseModel):
    id: int
    name: str
    model_config = ConfigDict(from_attributes=True)


# ✅ Para detalle: con metadatos completos
class StateRead(BaseModel):
    id: int
    name: str
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)