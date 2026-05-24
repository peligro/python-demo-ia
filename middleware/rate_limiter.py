# middleware/rate_limiter.py
from slowapi import Limiter
from slowapi.util import get_remote_address
import os

def get_rate_limit_key(request):
    token = request.cookies.get("remember_token")
    if token:
        return f"user:{token[:32]}"
    return get_remote_address(request)

redis_host = os.getenv("REDIS_HOST", "redis")
redis_port = int(os.getenv("REDIS_PORT", 6379))
redis_db = int(os.getenv("REDIS_DB", 0))
redis_url = f"redis://{redis_host}:{redis_port}/{redis_db}"

limiter = Limiter(
    key_func=get_rate_limit_key,
    storage_uri=redis_url,
    default_limits=[os.getenv("RATE_LIMIT_DEFAULT", "120/minute")],
    strategy="fixed-window",
    headers_enabled=True
)