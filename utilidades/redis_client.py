import redis
import os
from dotenv import load_dotenv
import json

load_dotenv()

class RedisClient:
    def __init__(self):
        self.client = redis.Redis(
            host=os.getenv("REDIS_HOST", "redis"),
            port=int(os.getenv("REDIS_PORT", 6379)),
            db=int(os.getenv("REDIS_DB", 0)),
            decode_responses=True
        )
    
    def set_session(self, token: str, user_id: int, ttl: int = 86400):
        """Guarda sesión en Redis: session:{token} -> {user_id, metadata}"""
        session_data = json.dumps({"user_id": user_id})
        self.client.setex(f"session:{token}", ttl, session_data)
    
    def get_session(self, token: str) -> dict | None:
        """Obtiene sesión de Redis"""
        data = self.client.get(f"session:{token}")
        return json.loads(data) if data else None
    
    def delete_session(self, token: str):
        """Invalida sesión (logout)"""
        self.client.delete(f"session:{token}")
    
    def blacklist_token(self, token: str, ttl: int):
        """Agrega token a blacklist (logout forzado)"""
        self.client.setex(f"blacklist:{token}", ttl, "1")
    
    def is_blacklisted(self, token: str) -> bool:
        """Verifica si token está en blacklist"""
        return self.client.exists(f"blacklist:{token}") > 0

# Singleton
redis_client = RedisClient()