#models/state.py
from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship

class State(SQLModel, table=True):
    __tablename__ = "state"
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    user_metadata: list["UserMetadata"] = Relationship(back_populates="state")