#models/app_menu.py
from typing import Optional
from datetime import datetime, timezone
from sqlmodel import SQLModel, Field, Relationship

class AppMenu(SQLModel, table=True):
    __tablename__ = "app_menu"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    label: str = Field(max_length=200)
    title: str = Field(max_length=200)
    icon: str = Field(max_length=200)
    order: int = Field(default=0)
    
    # Relaciones opcionales (nullable)
    parent_id: Optional[int] = Field(default=None, foreign_key="app_menu.id", ondelete="CASCADE")
    module_id: Optional[int] = Field(default=None, foreign_key="module.id", ondelete="SET NULL")
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Relaciones bidireccionales
    parent: Optional["AppMenu"] = Relationship(back_populates="children", sa_relationship_kwargs={"remote_side": "AppMenu.id"})
    children: list["AppMenu"] = Relationship(back_populates="parent", sa_relationship_kwargs={"lazy": "select"})
    module: Optional["Module"] = Relationship(back_populates="app_menus")
