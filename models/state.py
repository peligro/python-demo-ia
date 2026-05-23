from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field

class State(SQLModel, table=True):
    __tablename__ = "state"
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)