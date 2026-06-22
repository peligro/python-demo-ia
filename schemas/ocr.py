#schemas/ocr.py
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Literal
from datetime import datetime, timezone


class OCRBasicRequest(BaseModel):
    """Request para OCR básico"""
    image_path: str = Field(
        ...,
        description="Ruta relativa de la imagen en static/images/"
    )
    language: Literal["spa", "eng", "spa+eng"] = Field(
        default="spa",
        description="Idioma del texto: spa (español), eng (inglés), spa+eng (ambos)"
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


class OCRBasicResponse(BaseModel):
    """Respuesta de OCR básico"""
    image_path: str
    extracted_text: str
    language_used: str
    confidence: float
    word_count: int
    processing_time_ms: int
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class OCRPreprocessRequest(BaseModel):
    """Request para OCR con preprocesamiento"""
    image_path: str = Field(..., description="Ruta relativa de la imagen")
    language: Literal["spa", "eng", "spa+eng"] = Field(default="spa")
    preprocessing: Literal["auto", "grayscale", "binarize", "denoise", "deskew", "enhance"] = Field(
        default="auto",
        description="Tipo de preprocesamiento"
    )

    @field_validator('image_path')
    @classmethod
    def validate_image_path(cls, v: str) -> str:
        if not v.startswith('static/images/'):
            raise ValueError('La ruta debe estar en static/images/')
        
        valid_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.webp', '.tiff']
        if not any(v.lower().endswith(ext) for ext in valid_extensions):
            raise ValueError(f'Formato no soportado')
        
        if '..' in v or v.startswith('/'):
            raise ValueError('Ruta inválida')
        
        return v


class OCRPreprocessResponse(BaseModel):
    """Respuesta de OCR con preprocesamiento"""
    image_path: str
    preprocessing_applied: str
    extracted_text: str
    language_used: str
    confidence: float
    word_count: int
    processing_time_ms: int
    preprocessed_image_url: Optional[str] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ExtractDataRequest(BaseModel):
    """Request para extracción de datos estructurados"""
    image_path: str = Field(..., description="Ruta relativa de la imagen")
    language: Literal["spa", "eng", "spa+eng"] = Field(default="spa")
    extract_patterns: List[Literal["email", "phone", "rut", "date", "url"]] = Field(
        default=["email", "phone", "rut"],
        description="Patrones a extraer"
    )

    @field_validator('image_path')
    @classmethod
    def validate_image_path(cls, v: str) -> str:
        if not v.startswith('static/images/'):
            raise ValueError('La ruta debe estar en static/images/')
        
        valid_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.webp', '.tiff']
        if not any(v.lower().endswith(ext) for ext in valid_extensions):
            raise ValueError(f'Formato no soportado')
        
        if '..' in v or v.startswith('/'):
            raise ValueError('Ruta inválida')
        
        return v


class ExtractedData(BaseModel):
    """Datos extraídos de la imagen"""
    emails: List[str] = []
    phones: List[str] = []
    ruts: List[str] = []
    dates: List[str] = []
    urls: List[str] = []


class ExtractDataResponse(BaseModel):
    """Respuesta de extracción de datos"""
    image_path: str
    extracted_data: ExtractedData
    raw_text: str
    language_used: str
    processing_time_ms: int
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class CompareDocumentsRequest(BaseModel):
    """Request para comparación de documentos"""
    image_path_1: str = Field(..., description="Ruta de la primera imagen")
    image_path_2: str = Field(..., description="Ruta de la segunda imagen")
    language: Literal["spa", "eng", "spa+eng"] = Field(default="spa")

    @field_validator('image_path_1', 'image_path_2')
    @classmethod
    def validate_image_path(cls, v: str) -> str:
        if not v.startswith('static/images/'):
            raise ValueError('La ruta debe estar en static/images/')
        
        valid_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.webp', '.tiff']
        if not any(v.lower().endswith(ext) for ext in valid_extensions):
            raise ValueError(f'Formato no soportado')
        
        if '..' in v or v.startswith('/'):
            raise ValueError('Ruta inválida')
        
        return v


class CompareDocumentsResponse(BaseModel):
    """Respuesta de comparación de documentos"""
    image_path_1: str
    image_path_2: str
    text_1: str
    text_2: str
    similarity_score: float
    differences: List[str]
    are_identical: bool
    processing_time_ms: int
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class InvoiceItem(BaseModel):
    """Item de factura"""
    description: str
    quantity: float
    unit_price: float
    total: float


class InvoiceData(BaseModel):
    """Datos estructurados de factura"""
    invoice_number: Optional[str] = None
    invoice_date: Optional[str] = None
    due_date: Optional[str] = None
    ruc_emitter: Optional[str] = None
    emitter_name: Optional[str] = None
    emitter_address: Optional[str] = None
    ruc_client: Optional[str] = None
    client_name: Optional[str] = None
    client_address: Optional[str] = None
    subtotal: Optional[float] = None
    tax: Optional[float] = None
    total: Optional[float] = None
    items: List[InvoiceItem] = []
    raw_text: str = ""


class ExtractInvoiceRequest(BaseModel):
    """Request para extracción de factura PDF"""
    file_path: str = Field(..., description="Ruta relativa del PDF (ej: static/pdfs/factura.pdf)")
    language: Literal["spa", "eng", "spa+eng"] = Field(default="spa")

    @field_validator('file_path')
    @classmethod
    def validate_file_path(cls, v: str) -> str:
        if not v.startswith('static/pdfs/'):
            raise ValueError('La ruta debe estar en static/pdfs/')
        
        if not v.lower().endswith('.pdf'):
            raise ValueError('El archivo debe ser PDF')
        
        if '..' in v or v.startswith('/'):
            raise ValueError('Ruta inválida')
        
        return v


class ExtractInvoiceResponse(BaseModel):
    """Respuesta de extracción de factura"""
    file_path: str
    invoice_data: InvoiceData
    processing_time_ms: int
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))