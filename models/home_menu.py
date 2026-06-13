#model/home_menu.py
from typing import Optional
from datetime import datetime, timezone
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Column, Text  # ← Agregar este import

class HomeMenu(SQLModel, table=True):
    __tablename__ = "home_menu"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str = Field(max_length=200)
    icon: str = Field(max_length=100)
    color: str = Field(max_length=100)
    
    description: str = Field(sa_column=Column(Text))
    
    slug: str = Field(default="vacío", max_length=200, unique=True, index=True)
    order: int = Field(default=1, ge=0)
    
    # Relación opcional con Module
    module_id: Optional[int] = Field(default=None, foreign_key="module.id", ondelete="SET NULL")
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Relaciones bidireccionales
    module: Optional["Module"] = Relationship(back_populates="home_menus")