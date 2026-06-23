#schemas/object_detection.py
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Literal
from datetime import datetime, timezone


class BoundingBox(BaseModel):
    """Bounding box en formato x, y, width, height"""
    x: int
    y: int
    width: int
    height: int


class ObjectDetection(BaseModel):
    """Una detección de objeto"""
    class_id: int
    class_name: str
    confidence: float
    bounding_box: BoundingBox


class ObjectDetectionRequest(BaseModel):
    """Request para detección de objetos"""
    image_path: str = Field(
        ...,
        description="Ruta relativa de la imagen en static/images/"
    )
    model: Literal["yolov8n.pt", "yolov8s.pt", "yolov8m.pt", "yolov8l.pt", "yolov8x.pt"] = Field(
        default="yolov8n.pt",
        description="Modelo YOLOv8 a usar (n=nano, s=small, m=medium, l=large, x=xlarge)"
    )
    confidence_threshold: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Umbral mínimo de confianza (0.0 a 1.0)"
    )

    @field_validator('image_path')
    @classmethod
    def validate_image_path(cls, v: str) -> str:
        if not v.startswith('static/images/'):
            raise ValueError('La ruta debe estar en static/images/')
        
        valid_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.webp', '.tiff']
        if not any(v.lower().endswith(ext) for ext in valid_extensions):
            raise ValueError(f'Formato no soportado. Usa: {", ".join(valid_extensions)}')
        
        if '..' in v or v.startswith('/'):
            raise ValueError('Ruta inválida')
        
        return v


class ObjectDetectionResponse(BaseModel):
    """Respuesta de detección de objetos"""
    image_path: str
    model_used: str
    confidence_threshold: float
    total_objects: int
    detections: List[ObjectDetection]
    image_width: int
    image_height: int
    processing_time_ms: int
    processed_image_url: Optional[str] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))