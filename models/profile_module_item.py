from typing import Optional
from datetime import datetime, timezone
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import UniqueConstraint, Index

class ProfileModuleItem(SQLModel, table=True):
    __tablename__ = "profile_module_item"
    __table_args__ = (
        UniqueConstraint("profile_module_id", "item_id", name="uq_pm_item"),
        Index("idx_pm_item", "profile_module_id", "item_id"),
    )
    
    id: Optional[int] = Field(default=None, primary_key=True)
    
    # Foreign keys
    profile_module_id: int = Field(foreign_key="profile_module.id", nullable=False)
    item_id: int = Field(foreign_key="item.id", nullable=False)
    
    # Timestamps (siempre UTC)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Relationships bidireccionales
    profile_module: "ProfileModule" = Relationship(back_populates="items")
    item: "Item" = Relationship(back_populates="profile_module_items")
