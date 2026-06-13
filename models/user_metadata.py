#models/user_metadata.py
from typing import Optional
from datetime import datetime, timezone
from sqlmodel import SQLModel, Field, Relationship

class UserMetadata(SQLModel, table=True):
    __tablename__ = "user_metadata"
    id: Optional[int] = Field(default=None, primary_key=True)
    
    phone: Optional[str] = Field(default=None, max_length=50)

    # Foreign Keys
    user_id: int = Field(foreign_key="user.id", unique=True)
    state_id: Optional[int] = Field(default=None, foreign_key="state.id")
    profile_id: Optional[int] = Field(default=None, foreign_key="profile.id")

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Relaciones bidireccionales
    user: Optional["User"] = Relationship(back_populates="user_meta")
    state: Optional["State"] = Relationship(back_populates="user_metadata")
    profile: Optional["Profile"] = Relationship(back_populates="user_metadata")