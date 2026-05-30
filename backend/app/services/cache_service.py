"""Redis caching helpers with JSON serialization."""
import json
from app.extensions import redis_client


def get_cached(key: str):
    """Retrieve a cached value by key. Returns None if cache miss or Redis unavailable."""
    if not redis_client:
        return None
    try:
        value = redis_client.get(key)
        if value:
            return json.loads(value)
    except Exception:
        pass
    return None


def set_cached(key: str, value, ttl: int = 300):
    """Store a value in cache with a TTL (default 5 minutes)."""
    if not redis_client:
        return
    try:
        redis_client.setex(key, ttl, json.dumps(value, default=str))
    except Exception:
        pass


def invalidate_cache(pattern: str = 'analytics:*'):
    """Invalidate all cache keys matching the given pattern."""
    if not redis_client:
        return
    try:
        keys = redis_client.keys(pattern)
        if keys:
            redis_client.delete(*keys)
    except Exception:
        pass
