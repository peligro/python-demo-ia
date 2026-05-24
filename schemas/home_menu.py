from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional

class HomeMenuCreate(BaseModel):
    title: str = Field(..., min_length=2, max_length=200)
    icon: str = Field(..., min_length=2, max_length=100)
    color: str = Field(..., min_length=3, max_length=100, pattern=r"^#?[0-9a-fA-F]{3,8}$")
    description: str = Field(..., min_length=10, max_length=500)
    slug: str = Field(default="vacío", min_length=2, max_length=200, pattern=r"^[a-z0-9\-_]+$")
    order: int = Field(default=1, ge=0)
    module_id: Optional[int] = Field(default=None, ge=1)
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "title": "Gestión de Usuarios",
                "icon": "user-group",
                "color": "#3B82F6",
                "description": "Administra usuarios, roles y permisos del sistema",
                "slug": "user-management",
                "order": 1,
                "module_id": 1
            }
        }
    )

class HomeMenuUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=2, max_length=200)
    icon: Optional[str] = Field(None, min_length=2, max_length=100)
    color: Optional[str] = Field(None, min_length=3, max_length=100, pattern=r"^#?[0-9a-fA-F]{3,8}$")
    description: Optional[str] = Field(None, min_length=10, max_length=500)
    slug: Optional[str] = Field(None, min_length=2, max_length=200, pattern=r"^[a-z0-9\-_]+$")
    order: Optional[int] = Field(None, ge=0)
    module_id: Optional[int] = Field(None, ge=1)
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "title": "Usuarios Admin",
                "order": 2,
                "color": "#10B981"
            }
        }
    )

class HomeMenuPublic(BaseModel):
    id: int
    title: str
    icon: str
    color: str
    description: str
    slug: str
    order: int
    module_id: Optional[int]
    model_config = ConfigDict(from_attributes=True)

class HomeMenuRead(BaseModel):
    id: int
    title: str
    icon: str
    color: str
    description: str
    slug: str
    order: int
    module_id: Optional[int]
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

class HomeMenuListResponse(BaseModel):
    total: int
    page: int
    limit: int
    data: list[HomeMenuPublic]
