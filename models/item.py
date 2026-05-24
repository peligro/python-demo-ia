from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship

class Item(SQLModel, table=True):
    __tablename__ = "item"
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    code: str
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    profile_module_items: list["ProfileModuleItem"] = Relationship(back_populates="item")