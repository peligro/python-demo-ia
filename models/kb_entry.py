from typing import Optional, List
from datetime import datetime, timezone
from sqlmodel import SQLModel, Field, Column, Index
from sqlalchemy import Text, ARRAY, String, Integer, Boolean, DateTime


class KBEntry(SQLModel, table=True):
    """
    Entrada de la base de conocimiento para ejemplos de IA.
    """
    __tablename__ = "kb_entries"
    
    # ── Identificación ─────────────────────────────────────────────────────
    id: Optional[int] = Field(default=None, primary_key=True)
    
    example_id: str = Field(
        ..., 
        max_length=50, 
        index=True,
        description="Identificador del ejemplo que usa esta entrada"
    )
    
    # ── Matching (regex patterns para KB) ───────────────────────────────────
    question_patterns: List[str] = Field(
        sa_column=Column(ARRAY(String))
    )
    
    # ── Respuesta ───────────────────────────────────────────────────────────
    answer: str = Field(
        sa_column=Column(Text),
        description="Respuesta predefinida cuando hay match en KB"
    )
    
    # ── Prompt Template (para IA) ───────────────────────────────────────────
    prompt_template: Optional[str] = Field(
        default=None,
        sa_column=Column(Text),
        description="Template base para prompts de IA."
    )
    
    # ── Metadata de clasificación ───────────────────────────────────────────
    category: str = Field(
        ..., 
        max_length=50, 
        index=True,
        description="Categoría temática"
    )
    
    priority: int = Field(
        default=0,
        sa_column=Column(Integer, default=0),
        description="Prioridad de matching"
    )
    
    applies_to: List[str] = Field(
        default_factory=list,
        sa_column=Column(ARRAY(String), default=[])
    )
    
    # ── Flags de comportamiento ─────────────────────────────────────────────
    is_active: bool = Field(
        default=True,
        index=True,
        description="Si está desactivada, no se usa para matching"
    )
    
    requires_human: bool = Field(
        default=False,
        description="Si sugiere derivar a humano"
    )
    
    use_fallback_ai: bool = Field(
        default=True,
        description="Si usar IA como fallback"
    )
    
    last_prompt_used: Optional[str] = Field(
        default=None,
        sa_column=Column(Text),
        description="Último prompt generado (debugging)"
    )
    
    # ── Timestamps ──────────────────────────────────────────────────────────
    # ✅ CORREGIDO: Quitamos default_factory de sa_column. 
    # SQLAlchemy Column no soporta default_factory.
    # Usamos nullable=False para asegurar NOT NULL en la BD.
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False)
    )
    
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        # onupdate es válido en SQLAlchemy, pero default_factory NO.
        sa_column=Column(DateTime(timezone=True), nullable=False, onupdate=lambda: datetime.now(timezone.utc))
    )
    
    # ── Índices compuestos para performance ─────────────────────────────────
    __table_args__ = (
        Index('idx_kb_example_active_priority', 'example_id', 'is_active', 'priority'),
        Index('idx_kb_example_category', 'example_id', 'category'),
        Index('idx_kb_applies_to', 'applies_to', postgresql_using='gin'),
    )