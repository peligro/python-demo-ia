from pydantic import BaseModel
from typing import List

class HealthResponse(BaseModel):
    status: str


class IndexResponse(BaseModel):
    estado: str
    mensaje: str