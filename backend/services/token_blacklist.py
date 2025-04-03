import os
from datetime import datetime, timedelta

import redis

from backend.config import RedisSettings

# Initialize Redis settings
redis_settings = RedisSettings()

# Make Redis client optional
redis_client = None
try:
    redis_client = redis.Redis(
        host=redis_settings.REDIS_HOST,
        port=redis_settings.REDIS_PORT,
        password=redis_settings.REDIS_PASSWORD,
        decode_responses=True,
    )
    # Test the connection
    redis_client.ping()
except (redis.ConnectionError, redis.AuthenticationError, Exception):
    print("Warning: Redis not available. Token blacklisting will be disabled.")
    redis_client = None


def add_to_blacklist(token: str, expires_in: int) -> None:
    if redis_client:
        redis_client.setex(f"blacklist_token:{token}", expires_in, "1")


def is_blacklisted(token: str) -> bool:
    if redis_client:
        return redis_client.exists(f"blacklist_token:{token}") == 1
    return False


def remove_from_blacklist(token: str) -> None:
    if redis_client:
        redis_client.delete(f"blacklist_token:{token}")
