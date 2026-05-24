from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship

class Module(SQLModel, table=True):
    __tablename__ = "module"
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    slug: str
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    profile_modules: list["ProfileModule"] = Relationship(back_populates="module")