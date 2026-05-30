import time
import re
import uuid
import os
from typing import Optional, List
from datetime import datetime, timezone

from sqlmodel import Session, select
from models.kb_entry import KBEntry
from models.query_log import QueryLog
from schemas.agente_kb import QueryResponse, MetricsSchema
from integraciones.agente_integration import AgenteIntegration


class AgenteKBService:
    """
    Servicio principal del agente de conocimiento base.
    Orquesta el flujo: KB Matching → Fallback IA → Registro de Métricas
    """
    
    def __init__(self, session: Session):
        # Recibir sesión inyectada desde el router
        self.session = session
        self.example_id = "agente-kb"
        
        # Cache simple en memoria para la KB
        self._kb_cache: Optional[List[KBEntry]] = None
        self._cache_timestamp: float = 0
        self._cache_ttl: float = 300  # 5 minutos

    async def process_query(
        self, 
        query: str, 
        chat_id: Optional[str], 
        user_id: Optional[int], 
        user_name: str,
        model: str = "mistral-small-latest"
    ) -> QueryResponse:
        """
        Procesa una consulta completa con métricas y logging.
        """
        start_time = time.time()
        
        try:
            # 1. Intentar KB Matching primero
            kb_match = self._match_kb(query)
            
            if kb_match:
                return await self._handle_kb_match(
                    kb_match=kb_match,
                    query=query,
                    chat_id=chat_id,
                    user_id=user_id,
                    user_name=user_name,
                    start_time=start_time
                )
            
            # 2. Fallback a IA (si no hay match en KB)
            return await self._handle_ai_fallback(
                query=query,
                chat_id=chat_id,
                user_id=user_id,
                user_name=user_name,
                model=model,
                start_time=start_time
            )
            
        except Exception as e:
            return await self._handle_error(
                query=query,
                chat_id=chat_id,
                user_id=user_id,
                user_name=user_name,
                error=e,
                start_time=start_time
            )

    # =========================================================================
    # MÉTODOS PRIVADOS - Handlers
    # =========================================================================
    
    async def _handle_kb_match(
        self,
        kb_match: KBEntry,
        query: str,
        chat_id: Optional[str],
        user_id: Optional[int],
        user_name: str,
        start_time: float
    ) -> QueryResponse:
        """Maneja una respuesta desde la KB"""
        latency_ms = int((time.time() - start_time) * 1000)
        
        self._log_query(
            query=query,
            kb_entry_id=kb_match.id,
            kb_matched=True,
            kb_priority=kb_match.priority,
            response_source="knowledge-base",
            response_text=kb_match.answer,
            latency_ms=latency_ms,
            user_id=user_id
        )
        
        return QueryResponse(
            response=kb_match.answer,
            chatId=chat_id or str(uuid.uuid4()),
            messageId=str(uuid.uuid4()),
            model="kb-direct",
            source="knowledge-base",
            userName=user_name,
            requiresHuman=kb_match.requires_human,
            metrics=MetricsSchema(
                input_tokens=0,
                output_tokens=0,
                total_tokens=0,
                latency_ms=latency_ms
            )
        )
    
    async def _handle_ai_fallback(
        self,
        query: str,
        chat_id: Optional[str],
        user_id: Optional[int],
        user_name: str,
        model: str,
        start_time: float
    ) -> QueryResponse:
        """Maneja fallback a IA cuando no hay match en KB"""
        kb_entry_for_template = self._get_active_kb_entry()
        prompt = self._build_prompt(query, user_name, kb_entry_for_template)
        
        # Llamada real a la API de IA usando integración
        ai_response, tokens = await self._call_ai_api(query, prompt, model)
        
        latency_ms = int((time.time() - start_time) * 1000)
        
        self._log_query(
            query=query,
            kb_entry_id=None,
            kb_matched=False,
            response_source="plai-ai",
            response_text=ai_response,
            prompt_used=prompt,
            model_used=model,
            input_tokens=tokens.get("input", 0),
            output_tokens=tokens.get("output", 0),
            total_tokens=tokens.get("total", 0),
            latency_ms=latency_ms,
            user_id=user_id
        )
        
        return QueryResponse(
            response=ai_response,
            chatId=chat_id or str(uuid.uuid4()),
            messageId=str(uuid.uuid4()),
            model=model,
            source="plai-ai",
            userName=user_name,
            requiresHuman=False,
            metrics=MetricsSchema(
                input_tokens=tokens.get("input", 0),
                output_tokens=tokens.get("output", 0),
                total_tokens=tokens.get("total", 0),
                latency_ms=latency_ms
            )
        )
    
    async def _handle_error(
        self,
        query: str,
        chat_id: Optional[str],
        user_id: Optional[int],
        user_name: str,
        error: Exception,
        start_time: float
    ) -> QueryResponse:
        """Maneja errores generales"""
        latency_ms = int((time.time() - start_time) * 1000)
        
        self._log_query(
            query=query,
            response_source="error",
            response_text="Error procesando tu consulta.",
            latency_ms=latency_ms,
            user_id=user_id
        )
        
        return QueryResponse(
            response="Hubo un problema al procesar tu consulta. Por favor intenta de nuevo.",
            chatId=chat_id or str(uuid.uuid4()),
            messageId=str(uuid.uuid4()),
            model="error",
            source="error",
            userName=user_name,
            requiresHuman=True,
            metrics=MetricsSchema(latency_ms=latency_ms)
        )

    # =========================================================================
    # MÉTODOS PRIVADOS - Lógica de Negocio
    # =========================================================================
    
    def _match_kb(self, query: str) -> Optional[KBEntry]:
        """Busca un match en la KB usando regex patterns."""
        if self._kb_cache is None or (time.time() - self._cache_timestamp) > self._cache_ttl:
            self._kb_cache = self._load_kb_from_db()
            self._cache_timestamp = time.time()
            
        query_lower = query.lower().strip()
        
        for entry in self._kb_cache:
            for pattern in entry.question_patterns:
                try:
                    if re.search(pattern, query_lower, re.IGNORECASE):
                        return entry
                except re.error:
                    continue
        return None
    
    def _load_kb_from_db(self) -> List[KBEntry]:
        """Carga KB desde BD filtrando por example_id y is_active"""
        stmt = (
            select(KBEntry)
            .where(KBEntry.example_id == self.example_id, KBEntry.is_active == True)
            .order_by(KBEntry.priority.desc())
        )
        return list(self.session.exec(stmt).all())
    
    def _get_active_kb_entry(self) -> Optional[KBEntry]:
        """Obtiene un entry activo para extraer prompt_template (fallback)"""
        stmt = (
            select(KBEntry)
            .where(KBEntry.example_id == self.example_id, KBEntry.is_active == True)
            .limit(1)
        )
        return self.session.exec(stmt).first()
    
    def _build_prompt(self, query: str, user_name: str, kb_entry: Optional[KBEntry]) -> str:
        """Construye el prompt final para la IA"""
        template = kb_entry.prompt_template if kb_entry and kb_entry.prompt_template else (
            "Eres un asistente experto en logística. "
            "Responde la pregunta del usuario de forma clara, práctica y en español.\n\n"
            "Usuario: {user_name}\n"
            "Pregunta: {query}\n\n"
            "Respuesta:"
        )
        return template.format(query=query, user_name=user_name, context="")
    
    async def _call_ai_api(self, query: str, prompt: str, model: str) -> tuple[str, dict]:
        """
        Llama a la API de IA usando el servicio de integración
        """
        try:
            provider = self._get_provider_from_model(model)
            result = AgenteIntegration.chat_unificado(
                provider=provider,
                prompt=prompt,
                model=model
            )
            return result["response"], result["usage"]
        except Exception as e:
            print(f"[AgenteKB] Error en llamada a IA: {e}")
            return (
                "Error al conectar con el servicio de IA. Intenta nuevamente.",
                {"input": 0, "output": 0, "total": 0}
            )
    
    def _get_provider_from_model(self, model: str) -> str:
        """Determina el proveedor basado en el nombre del modelo"""
        model_lower = model.lower()
        if 'mistral' in model_lower:
            return 'mistral'
        elif 'gemini' in model_lower:
            return 'gemini'
        elif 'claude' in model_lower:
            return 'claude'
        elif 'gpt' in model_lower or 'openai' in model_lower:
            return 'openai'
        elif 'deepseek' in model_lower:
            return 'deepseek'
        return 'mistral'  # Default
    
    def _log_query(
        self,
        query: str,
        response_source: str,
        response_text: str,
        latency_ms: int,
        user_id: Optional[int],
        kb_entry_id: Optional[int] = None,
        kb_matched: bool = False,
        kb_priority: Optional[int] = None,
        prompt_used: Optional[str] = None,
        model_used: Optional[str] = None,
        input_tokens: Optional[int] = None,
        output_tokens: Optional[int] = None,
        total_tokens: Optional[int] = None
    ):
        """Registra la consulta en query_logs para auditoría y métricas"""
        log = QueryLog(
            example_id=self.example_id,
            user_id=user_id,
            query=query,
            response_source=response_source,
            response_text=response_text,
            kb_entry_id=kb_entry_id,
            kb_matched=kb_matched,
            kb_priority=kb_priority,
            prompt_used=prompt_used,
            model_used=model_used,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
            latency_ms=latency_ms
        )
        self.session.add(log)
        self.session.commit()
        self.session.refresh(log)