from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional


# ✅ NUEVO: Schema específico para el padre (evita recursión infinita)
class AppMenuParent(BaseModel):
    id: int
    label: str
    model_config = ConfigDict(from_attributes=True)


class AppMenuCreate(BaseModel):
    label: str = Field(..., min_length=2, max_length=200)
    title: str = Field(..., min_length=2, max_length=200)
    icon: str = Field(default="", max_length=200)
    order: int = Field(default=0, ge=0)
    parent_id: Optional[int] = Field(default=None, ge=1)
    module_id: Optional[int] = Field(default=None, ge=1)
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "label": "Usuarios",
                "title": "Gestión de Usuarios",
                "icon": "fa-users",
                "order": 1,
                "parent_id": None,
                "module_id": 1
            }
        }
    )


class AppMenuUpdate(BaseModel):
    label: Optional[str] = Field(None, min_length=2, max_length=200)
    title: Optional[str] = Field(None, min_length=2, max_length=200)
    icon: Optional[str] = Field(None, max_length=200)
    order: Optional[int] = Field(None, ge=0)
    parent_id: Optional[int] = Field(None, ge=1)
    module_id: Optional[int] = Field(None, ge=1)
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "label": "Usuarios Admin",
                "order": 2
            }
        }
    )


class ModuleSummary(BaseModel):
    id: int
    name: str
    slug: str
    model_config = ConfigDict(from_attributes=True)


class AppMenuPublic(BaseModel):
    id: int
    label: str
    title: str
    icon: str
    order: int
    parent_id: Optional[int]
    module_id: Optional[int]
    module_slug: Optional[str] = None
    parent: Optional[AppMenuParent] = None  # ✅ CAMBIO: Usar AppMenuParent en lugar de dict
    model_config = ConfigDict(from_attributes=True)


class AppMenuRead(AppMenuPublic):
    created_at: datetime
    updated_at: datetime


class AppMenuListResponse(BaseModel):
    total: int
    page: int
    limit: int
    data: list[AppMenuPublic]