from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional, List
from schemas.module import ModulePublic


class ProfileCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100, description="Nombre del perfil")
    description: str = Field(..., min_length=10, max_length=500, description="Descripción del perfil")
    model_config = ConfigDict(
        json_schema_extra={
            "example": {"name": "Administrador", "description": "Perfil con acceso total al sistema"}
        }
    )


class ProfileUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    description: Optional[str] = Field(None, min_length=10, max_length=500)
    model_config = ConfigDict(
        json_schema_extra={"example": {"name": "Super Admin", "description": "Perfil con privilegios elevados"}}
    )


class ProfilePublic(BaseModel):
    id: int
    name: str
    description: str
    model_config = ConfigDict(from_attributes=True)


class ProfileRead(BaseModel):
    id: int
    name: str
    description: str
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


# ✅ Para paginación
class ProfileListResponse(BaseModel):
    total: int
    page: int
    limit: int
    data: List[ProfilePublic]


# Respuesta para módulos del perfil
class ProfileModulesResponse(BaseModel):
    profile_id: int
    profile_name: str
    modules: List["ModulePublic"]
    module_ids: List[int]
    model_config = ConfigDict(from_attributes=True)


class ModuleSyncRequest(BaseModel):
    modules: List[int] = Field(default_factory=list)
    model_config = ConfigDict(from_attributes=True)