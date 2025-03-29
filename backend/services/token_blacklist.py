from datetime import datetime, timedelta
import redis
from backend.config import RedisSettings

# Initialize Redis settings
redis_settings = RedisSettings()

# Create Redis client
redis_client = redis.Redis(
    host=redis_settings.REDIS_HOST,
    port=redis_settings.REDIS_PORT,
    password=redis_settings.REDIS_PASSWORD,
    decode_responses=True
)

def add_to_blacklist(token: str, expires_in: int) -> None:
    """
    Add a token to the blacklist with expiration time.
    
    Args:
        token: The JWT token to blacklist
        expires_in: Time in seconds until the token expires
    """
    redis_client.setex(f"blacklist_token:{token}", expires_in, "1")

def is_blacklisted(token: str) -> bool:
    """
    Check if a token is blacklisted.
    
    Args:
        token: The JWT token to check
        
    Returns:
        bool: True if token is blacklisted, False otherwise
    """
    return redis_client.exists(f"blacklist_token:{token}") == 1

def remove_from_blacklist(token: str) -> None:
    """
    Remove a token from the blacklist.
    
    Args:
        token: The JWT token to remove from blacklist
    """
    redis_client.delete(f"blacklist_token:{token}") 