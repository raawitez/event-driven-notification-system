import os
import json
import redis
from loguru import logger


def create_redis_client():
    redis_url = os.getenv("REDIS_URL")

    if redis_url:
        return redis.from_url(
            redis_url,
            decode_responses=True
        )
    else:
        return redis.Redis(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", "6379")),
            db=0,
            decode_responses=True
        )


redis_client = create_redis_client()

CACHE_NOTIFICATION = "notification:{id}"
TTL_NOTIFICATION   = 300


def check_redis() -> bool:
    try:
        redis_client.ping()
        logger.info("Redis connected")
        return True
    except Exception as e:
        logger.warning(f"Redis unavailable: {e}")
        return False


def get_cache(key: str):
    try:
        value = redis_client.get(key)
        return json.loads(value) if value else None
    except Exception as e:
        logger.warning(f"Redis GET error: {e}")
        return None


def set_cache(key: str, value, ttl: int = TTL_NOTIFICATION):
    try:
        redis_client.setex(key, ttl, json.dumps(value))
    except Exception as e:
        logger.warning(f"Redis SET error: {e}")


def delete_cache(key: str):
    try:
        redis_client.delete(key)
    except Exception as e:
        logger.warning(f"Redis DELETE error: {e}")