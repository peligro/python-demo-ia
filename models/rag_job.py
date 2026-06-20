# models/rag_job.py
from typing import Optional
from datetime import datetime, timezone
from sqlmodel import SQLModel, Field, Column
from sqlalchemy import Text, String, Integer, DateTime, Index, Enum as SQLEnum
import enum


# ✅ Enum para el status del job (reemplaza Literal)
class JobStatus(str, enum.Enum):
    """Estados posibles de un job de procesamiento RAG"""
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class RAGJob(SQLModel, table=True):
    """
    Job de procesamiento de PDF para RAG.
    Permite tracking asíncrono del estado de procesamiento.
    """
    __tablename__ = "rag_jobs"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    
    # Metadata del archivo
    filename: str = Field(..., max_length=255, description="Nombre original del archivo")
    s3_key: Optional[str] = Field(default=None, max_length=500, description="Ruta en S3")
    file_size: Optional[int] = Field(default=None, description="Tamaño en bytes")
    
    # Estado del job - ✅ Usar Enum con SQLEnum para PostgreSQL
    status: JobStatus = Field(
        default=JobStatus.QUEUED,
        sa_column=Column(SQLEnum(JobStatus, name="jobstatus", create_type=True)),
        description="Estado actual del procesamiento"
    )
    error_message: Optional[str] = Field(default=None, sa_column=Column(Text))
    
    # Resultados
    chunks_created: Optional[int] = Field(default=None, description="Número de chunks generados")
    processing_time_ms: Optional[int] = Field(default=None, description="Tiempo total en ms")
    
    # Auditoría
    user_id: Optional[int] = Field(default=None, index=True, description="Usuario que subió el archivo")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False)
    )
    updated_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), onupdate=lambda: datetime.now(timezone.utc))
    )
    
    # Índices para consultas eficientes
    __table_args__ = (
        Index('idx_rag_jobs_status', 'status'),
        Index('idx_rag_jobs_created', 'created_at'),
        Index('idx_rag_jobs_user', 'user_id'),
        {"extend_existing": True} 
    )