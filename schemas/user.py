from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional


class UserCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: str = Field(..., max_length=255)
    password: str = Field(..., min_length=8, description="Mínimo 8 caracteres")
    model_config = ConfigDict(
        json_schema_extra={
            "example": {"name": "Admin", "email": "admin@demo.com", "password": "SecurePass123!"}
        }
    )


class UserUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    email: Optional[str] = Field(None, max_length=255)
    password: Optional[str] = Field(None, min_length=8)
    model_config = ConfigDict(
        json_schema_extra={"example": {"name": "Nuevo Nombre"}}
    )


class UserPublic(BaseModel):
    id: int
    name: str
    email: str
    model_config = ConfigDict(from_attributes=True)


class UserRead(BaseModel):
    id: int
    name: str
    email: str
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


# ✅ Schemas para metadata resumida (profile + state)
class ProfileSummary(BaseModel):
    id: int
    name: str
    model_config = ConfigDict(from_attributes=True)


class StateSummary(BaseModel):
    id: int
    name: str
    model_config = ConfigDict(from_attributes=True)


class UserMetadataSummary(BaseModel):
    id: int
    phone: Optional[str]
    profile: Optional[ProfileSummary]
    state: Optional[StateSummary]
    model_config = ConfigDict(from_attributes=True)


class UserPublicWithMetadata(BaseModel):
    id: int
    name: str
    email: str
    user_meta: Optional[UserMetadataSummary]
    model_config = ConfigDict(from_attributes=True)


class UserListResponse(BaseModel):
    total: int
    page: int
    limit: int
    data: list[UserPublic]


class UserListResponseWithMetadata(BaseModel):
    total: int
    page: int
    limit: int
    data: list[UserPublicWithMetadata]