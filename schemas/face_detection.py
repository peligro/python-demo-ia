#schemas/face_detection.py
from pydantic import BaseModel, Field, field_validator
from typing import Optional, Literal, List
from datetime import datetime, timezone

class BoundingBox(BaseModel):
    x: int
    y: int
    width: int
    height: int
    confidence: Optional[float] = None

class EyeDetection(BaseModel):
    left_eye: Optional[BoundingBox] = None
    right_eye: Optional[BoundingBox] = None
    total_eyes_detected: int = 0

class FaceDetection(BaseModel):
    face_id: int
    bounding_box: BoundingBox
    eyes: EyeDetection

class FaceDetectionRequest(BaseModel):
    image_path: str = Field(..., description="Ruta relativa de la imagen en static/images/")
    method: Literal["haarcascade"] = Field(default="haarcascade", description="Método de detección")
    min_face_size: Optional[int] = Field(default=30, ge=10, description="Tamaño mínimo del rostro en píxeles")
    scale_factor: Optional[float] = Field(default=1.05, ge=1.01, le=2.0, description="Factor de escala")
    min_neighbors: Optional[int] = Field(default=3, ge=1, le=10, description="Mínimo de vecinos")

    @field_validator('image_path')
    @classmethod
    def validate_image_path(cls, v: str) -> str:
        if not v.startswith('static/images/'):
            raise ValueError('La ruta debe estar en static/images/')
        
        valid_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.webp']
        if not any(v.lower().endswith(ext) for ext in valid_extensions):
            raise ValueError(f'Formato no soportado. Usa: {", ".join(valid_extensions)}')
        
        if '..' in v or v.startswith('/'):
            raise ValueError('Ruta inválida')
        
        return v

class FaceDetectionResponse(BaseModel):
    image_path: str
    method_used: str
    total_faces_detected: int
    faces: List[FaceDetection]
    image_width: int
    image_height: int
    processing_time_ms: int
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    processed_image_url: Optional[str] = None