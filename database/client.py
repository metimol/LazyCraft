import os

from redis.asyncio import ConnectionPool, Redis

# Get Redis host from environment (set by docker-compose)
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))

_pool: ConnectionPool | None = None


async def init_redis() -> None:
    global _pool  # noqa: PLW0603
    _pool = ConnectionPool.from_url(
        f"redis://{REDIS_HOST}:{REDIS_PORT}/0",
        decode_responses=True,  # Automatically decodes bytes to string
    )
    # Test connection on startup
    client = Redis(connection_pool=_pool)
    await client.ping()


async def close_redis() -> None:
    global _pool  # noqa: PLW0603
    if _pool:
        await _pool.disconnect()
        _pool = None


def get_redis() -> Redis:
    """Returns an async Redis client instance.
    You can use this client to execute commands across the app.
    """
    if _pool is None:
        msg = "Redis pool is not initialized"
        raise RuntimeError(msg)
    return Redis(connection_pool=_pool)
