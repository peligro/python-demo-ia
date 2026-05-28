from typing import Optional, List
from datetime import datetime, timezone
from sqlmodel import SQLModel, Field, Column, Index
from sqlalchemy import Text, ARRAY, String, Integer, Boolean, DateTime
from pydantic import ConfigDict  # ✅ Importado para configurar namespaces


class QueryLog(SQLModel, table=True):
    """
    Registro de cada consulta realizada al agente.
    """
    # ✅ CORREGIDO: Silenciamos la advertencia de Pydantic sobre 'model_used'
    model_config = ConfigDict(protected_namespaces=())

    __tablename__ = "query_logs"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    
    example_id: str = Field(
        ..., 
        max_length=50, 
        index=True,
        description="Ejemplo que generó esta consulta"
    )
    
    kb_entry_id: Optional[int] = Field(
        default=None, 
        foreign_key="kb_entries.id",
        description="ID del entry de KB que hizo match"
    )
    
    user_id: Optional[int] = Field(
        default=None,
        index=True,
        description="ID del usuario"
    )
    
    query: str = Field(
        sa_column=Column(Text),
        description="Consulta original del usuario"
    )
    
    response_source: str = Field(
        ..., 
        max_length=20,
        description="Fuente: 'kb', 'ai', 'error'"
    )
    
    response_text: Optional[str] = Field(
        default=None,
        sa_column=Column(Text),
        description="Respuesta final"
    )
    
    prompt_used: Optional[str] = Field(
        default=None,
        sa_column=Column(Text),
        description="Prompt completo enviado a la IA"
    )
    
    # Renombré model_used a ai_model_name para evitar conflictos, 
    # pero con model_config arriba ya no es estrictamente necesario, 
    # aunque es buena práctica. Lo dejo como model_used si prefieres, 
    # pero aquí uso ai_model_name para ser explícito.
    ai_model_name: Optional[str] = Field(
        default=None,
        max_length=100,
        sa_column=Column("model_used", String(100)), # Mapea a columna 'model_used' en BD si quieres mantener nombre
        description="Modelo de IA usado"
    )
    
    input_tokens: Optional[int] = Field(
        default=None,
        sa_column=Column(Integer),
        description="Tokens de entrada"
    )
    
    output_tokens: Optional[int] = Field(
        default=None,
        sa_column=Column(Integer),
        description="Tokens de salida"
    )
    
    total_tokens: Optional[int] = Field(
        default=None,
        sa_column=Column(Integer),
        description="Total de tokens"
    )
    
    latency_ms: Optional[int] = Field(
        default=None,
        sa_column=Column(Integer),
        description="Latencia en ms"
    )
    
    kb_matched: bool = Field(
        default=False,
        description="¿Hubo match en KB?"
    )
    
    kb_priority: Optional[int] = Field(
        default=None,
        sa_column=Column(Integer),
        description="Prioridad del match"
    )
    
    # ✅ CORREGIDO: Quitamos default_factory de sa_column
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False)
    )
    
    # ── Índices para reportes rápidos ───────────────────────────────────────
    __table_args__ = (
        Index('idx_query_logs_example_user', 'example_id', 'user_id'),
        Index('idx_query_logs_created', 'created_at'),
        Index('idx_query_logs_source', 'response_source'),
        Index('idx_query_logs_model', 'model_used'), # Ojo: si cambiaste el nombre del campo, ajusta esto
    )