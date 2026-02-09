"""Redis client for sessions, cache and pub/sub WebSocket"""

import json
import logging
from typing import Optional

import redis

from app.core.config import settings

logger = logging.getLogger(__name__)

# Synchronous Redis client (matching the sync SQLAlchemy pattern)
redis_client = redis.Redis.from_url(
    settings.REDIS_URL,
    decode_responses=True,
    max_connections=20,
)


def publish_ws_event(run_id: str, event: dict):
    """Publish a WS event via Redis pub/sub"""
    try:
        redis_client.publish(f"ws:run:{run_id}", json.dumps(event))
    except Exception as e:
        logger.error(f"Failed to publish WS event: {e}")


def get_cached_embedding(text_hash: str) -> Optional[list]:
    """Cache d'embeddings pour eviter les appels Ollama redondants"""
    try:
        cached = redis_client.get(f"emb:{text_hash}")
        return json.loads(cached) if cached else None
    except Exception:
        return None


def cache_embedding(text_hash: str, embedding: list, ttl: int = 86400):
    """Stocker un embedding en cache (TTL 24h par defaut)"""
    try:
        redis_client.setex(f"emb:{text_hash}", ttl, json.dumps(embedding))
    except Exception as e:
        logger.error(f"Failed to cache embedding: {e}")


def store_session(session_id: str, user_data: dict, ttl: int = 3600):
    """Session JWT dans Redis (TTL 1h par defaut)"""
    try:
        redis_client.setex(f"session:{session_id}", ttl, json.dumps(user_data))
    except Exception as e:
        logger.error(f"Failed to store session: {e}")


def get_session(session_id: str) -> Optional[dict]:
    """Recuperer une session"""
    try:
        data = redis_client.get(f"session:{session_id}")
        return json.loads(data) if data else None
    except Exception:
        return None


def invalidate_session(session_id: str):
    """Invalider une session (logout)"""
    try:
        redis_client.delete(f"session:{session_id}")
    except Exception as e:
        logger.error(f"Failed to invalidate session: {e}")
