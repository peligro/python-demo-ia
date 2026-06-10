# api/services/rag_pdf/rag_engine.py
import os
import time
import logging
from typing import List, Optional, Dict, Any
from sqlmodel import Session, select
from sentence_transformers import SentenceTransformer

from api.models.rag_chunk import RAGChunk

logger = logging.getLogger(__name__)

class RAGEngine:
    """Motor RAG: búsqueda vectorial + prompt minimalista + IA"""
    
    def __init__(self):
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        self.top_k = int(os.getenv("RAG_TOP_K", 3))
        self.default_model = os.getenv("RAG_DEFAULT_MODEL", "mistral-small-latest")

    def _search_chunks(self, query: str, session: Session) -> List[RAGChunk]:
        """Búsqueda vectorial en pgvector (distancia L2)"""
        query_embedding = self.embedding_model.encode(query).tolist()
        stmt = (
            select(RAGChunk)
            .where(RAGChunk.is_active == True)
            .order_by(RAGChunk.embedding.l2_distance(query_embedding))
            .limit(self.top_k)
        )
        chunks = session.exec(stmt).all()
        logger.debug(f"🔍 Encontrados {len(chunks)} chunks relevantes")
        return chunks

    def _build_prompt(self, query: str, chunks: List[RAGChunk]) -> str:
        """Prompt minimalista optimizado para tokens"""
        context = "\n\n".join([f"P: {c.question}\nR: {c.answer}" for c in chunks])
        return f"""Eres un asistente de atención al cliente.
Responde SOLO con la información del manual:

{context}

Pregunta del usuario: {query}
Responde en español, máximo 100 palabras. Si no está en el manual, di "No encontré información en el manual".
"""

    def _call_ia(self, prompt: str, model: str) -> str:
        """
        Llamada a IA. 
         Aquí conectas con tu integración existente (headers_ia.py / agente_integration.py)
        Por ahora uso requests directo compatible con tu .env
        """
        import requests
        # Ejemplo con Mistral (ajusta según tu headers_ia.py)
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {os.getenv('MISTRAL_API_KEY')}"
        }
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.3,
            "max_tokens": 150
        }
        resp = requests.post(
            f"{os.getenv('MISTRAL_BASE_URL')}chat/completions",
            headers=headers, json=payload, timeout=30
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]

    def process_query(self, query: str, session: Session, model: Optional[str] = None) -> Dict[str, Any]:
        """Flujo completo RAG"""
        start_time = time.time()
        model = model or self.default_model

        # 1. Búsqueda vectorial
        chunks = self._search_chunks(query, session)
        if not chunks:
            return {
                "response": "No encontré información específica sobre esto en el manual.",
                "source": "none",
                "chunks_used": 0,
                "latency_ms": int((time.time() - start_time) * 1000),
                "cache": False
            }

        # 2. Prompt + IA
        prompt = self._build_prompt(query, chunks)
        ia_response = self._call_ia(prompt, model)
        latency_ms = int((time.time() - start_time) * 1000)

        return {
            "response": ia_response,
            "source": "rag-kb",
            "chunks_used": len(chunks),
            "chunk_ids": [c.id for c in chunks],
            "latency_ms": latency_ms,
            "cache": False,
            "model_used": model
        }
