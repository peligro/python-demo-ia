#services/rag_pdf/rag_cache_service.py
import os
import json
import hashlib
import logging
from typing import Optional, Dict, Any
from common.redis_client import redis_client

logger = logging.getLogger(__name__)

class RAGCacheService:
    """Cache Redis para respuestas RAG (patrón Cache-Aside)"""
    
    def __init__(self):
        self.prefix = "rag:chat:"
        self.ttl = int(os.getenv("RAG_CACHE_TTL", 3600))

    def _get_cache_key(self, query: str) -> str:
        normalized = query.lower().strip()
        hash_val = hashlib.md5(normalized.encode()).hexdigest()
        return f"{self.prefix}{hash_val}"

    def get(self, query: str) -> Optional[Dict[str, Any]]:
        key = self._get_cache_key(query)
        try:
            data = redis_client.client.get(key)
            if data:
                logger.debug(f"🔥 Cache HIT: {query[:40]}...")
                return json.loads(data)
            logger.debug(f"❄️ Cache MISS: {query[:40]}...")
            return None
        except Exception as e:
            logger.error(f"❌ Error cache Redis: {e}")
            return None

    def set(self, query: str, response_data: Dict[str, Any]) -> bool:
        key = self._get_cache_key(query)
        try:
            redis_client.client.setex(key, self.ttl, json.dumps(response_data))
            logger.debug(f"💾 Cache guardada: {key}")
            return True
        except Exception as e:
            logger.error(f" Error guardando cache: {e}")
            return False
