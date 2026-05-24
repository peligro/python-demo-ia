from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship

class Profile(SQLModel, table=True):
    __tablename__ = "profile"
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    description: str
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    profile_modules: list["ProfileModule"] = Relationship(back_populates="profile")
    user_metadata: list["UserMetadata"] = Relationship(back_populates="profile")