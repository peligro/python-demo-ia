# models/profile_module.py
from typing import Optional
from datetime import datetime, timezone
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import UniqueConstraint

class ProfileModule(SQLModel, table=True):
    __tablename__ = "profile_module"
    __table_args__ = (UniqueConstraint("profile_id", "module_id"),)
    
    id: Optional[int] = Field(default=None, primary_key=True)
    profile_id: int = Field(foreign_key="profile.id")
    module_id: int = Field(foreign_key="module.id")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Relationships
    profile: "Profile" = Relationship(back_populates="profile_modules")
    module: "Module" = Relationship(back_populates="profile_modules")

    items: list["ProfileModuleItem"] = Relationship(back_populates="profile_module")