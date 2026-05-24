from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from datetime import datetime

class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    remember: bool = False  # Para TTL extendido

class UserMetadataResponse(BaseModel):
    id: int
    phone: Optional[str]
    state_id: Optional[int]
    profile_id: Optional[int]

class ModuleItemResponse(BaseModel):
    id: int
    name: str
    code: str

class ModuleWithItemsResponse(BaseModel):
    id: int
    name: str
    slug: str
    items: List[ModuleItemResponse]

class ProfileResponse(BaseModel):
    id: int
    name: str
    description: str

class StateResponse(BaseModel):
    id: int
    name: str

class MeResponse(BaseModel):
    id: int
    name: str
    email: str
    metadata: UserMetadataResponse
    profile: Optional[ProfileResponse]
    state: Optional[StateResponse]
    modules: List[ModuleWithItemsResponse]
    
    model_config = {"from_attributes": True}
