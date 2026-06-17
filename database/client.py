import os
from redis.asyncio import Redis, ConnectionPool

# Get Redis host from environment (set by docker-compose)
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))

# Create a connection pool to manage connections safely
_pool = ConnectionPool.from_url(
    f"redis://{REDIS_HOST}:{REDIS_PORT}/0",
    decode_responses=True,  # Automatically decodes bytes to string
)


def get_redis() -> Redis:
    """
    Returns an async Redis client instance.
    You can use this client to execute commands across the app.
    """
    return Redis(connection_pool=_pool)
