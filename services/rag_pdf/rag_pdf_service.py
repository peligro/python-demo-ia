#services/rag_pdf/rag_pdf_service.py
import os
import time
import logging
from typing import List, Optional, Dict, Any
from sqlmodel import Session, select
from sentence_transformers import SentenceTransformer
from models.rag_chunk import RAGChunk
from integraciones.agente_integration import AgenteIntegration

logger = logging.getLogger(__name__)

class RAGPDFService:
    """
    Servicio RAG PDF: búsqueda vectorial + match KB + fallback IA.
    Flujo:
    1. Búsqueda vectorial en rag_chunks (pgvector)
    2. Si similitud > threshold → respuesta directa de KB (costo $0)
    3. Si no → IA con contexto de los chunks (fallback)
    """
    
    def __init__(self, session: Session):
        self.session = session
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        self.default_model = os.getenv("RAG_DEFAULT_MODEL", "mistral-small-latest")
    
    async def process_query(
        self,
        query: str,
        model: Optional[str] = None,
        kb_threshold: float = 0.75,
        top_k: int = 3
    ) -> Dict[str, Any]:
        """Flujo completo RAG"""
        start_time = time.time()
        model = model or self.default_model
        
        # 1. Búsqueda vectorial
        chunks, similarity_score = self._search_chunks(query, top_k)
        
        if not chunks:
            return {
                "response": "No encontré información específica sobre esto en el manual.",
                "source": "none",
                "model_used": model,
                "chunks_used": 0,
                "chunk_ids": [],
                "latency_ms": int((time.time() - start_time) * 1000),
                "cache": False,
                "similarity_score": 0.0
            }
        
        # 2. ¿Match directo en KB?
        if similarity_score >= kb_threshold:
            logger.info(f"🎯 KB MATCH directo (score: {similarity_score:.3f})")
            return {
                "response": chunks[0].answer,
                "source": "knowledge-base",
                "model_used": "kb-direct",
                "chunks_used": 1,
                "chunk_ids": [chunks[0].id],
                "latency_ms": int((time.time() - start_time) * 1000),
                "cache": False,
                "similarity_score": similarity_score
            }
        
        # 3. Fallback a IA con contexto
        logger.info(f"🤖 Fallback a IA (score: {similarity_score:.3f} < {kb_threshold})")
        prompt = self._build_prompt(query, chunks)
        ia_response = self._call_ia(prompt, model)
        
        return {
            "response": ia_response,
            "source": "rag-ai",
            "model_used": model,
            "chunks_used": len(chunks),
            "chunk_ids": [c.id for c in chunks],
            "latency_ms": int((time.time() - start_time) * 1000),
            "cache": False,
            "similarity_score": similarity_score
        }
    
    def _search_chunks(self, query: str, top_k: int) -> tuple[List[RAGChunk], float]:
        """Búsqueda vectorial en pgvector + cálculo de similitud"""
        query_embedding = self.embedding_model.encode(query).tolist()
        
        stmt = (
            select(RAGChunk)
            .where(RAGChunk.is_active == True)
            .order_by(RAGChunk.embedding.l2_distance(query_embedding))
            .limit(top_k)
        )
        chunks = list(self.session.exec(stmt).all())
        
        # Calcular similitud coseno con el mejor chunk
        similarity_score = 0.0
        if chunks:
            similarity_score = self._cosine_similarity(query_embedding, chunks[0].embedding)
        
        return chunks, similarity_score
    
    def _cosine_similarity(self, vec_a: List[float], vec_b: List[float]) -> float:
        """Calcula similitud coseno entre dos vectores"""
        import numpy as np
        a = np.array(vec_a)
        b = np.array(vec_b)
        dot_product = np.dot(a, b)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return float(dot_product / (norm_a * norm_b))
    
    def _build_prompt(self, query: str, chunks: List[RAGChunk]) -> str:
        """Prompt optimizado para RAG con contexto de chunks"""
        context = "\n\n".join([
            f"P: {c.question}\nR: {c.answer}" 
            for c in chunks
        ])
        
        return f"""Eres un asistente experto en atención al cliente. Responde SOLO con la información del manual proporcionado.

CONTEXTO DEL MANUAL:
{context}

Pregunta del usuario: {query}

Instrucciones:
- Responde en español
- Sé claro y conciso (máximo 150 palabras)
- Si la información no está en el contexto, di "No encontré información específica sobre esto en el manual"
- No inventes información
- Cita la sección del manual si es relevante

Respuesta:"""
    
    def _call_ia(self, prompt: str, model: str) -> str:
        """Llama a la IA usando AgenteIntegration (reutiliza tu infraestructura)"""
        try:
            provider = self._get_provider_from_model(model)
            result = AgenteIntegration.chat_unificado(
                provider=provider,
                prompt=prompt,
                model=model,
                messages=None
            )
            return result["response"]
        except Exception as e:
            logger.error(f"❌ Error en llamada a IA: {e}")
            return f"Error al conectar con el servicio de IA: {str(e)}"
    
    def _get_provider_from_model(self, model: str) -> str:
        """Mapea modelo a proveedor (igual que AgenteKBService)"""
        model_lower = model.lower()
        if 'mistral' in model_lower: return 'mistral'
        elif 'gemini' in model_lower: return 'gemini'
        elif 'claude' in model_lower: return 'claude'
        elif 'gpt' in model_lower or 'openai' in model_lower: return 'openai'
        elif 'deepseek' in model_lower: return 'deepseek'
        return 'mistral'