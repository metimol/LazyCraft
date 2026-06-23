from typing import Optional
from database.client import get_redis


async def get_all_users() -> list[int]:
    """
    Returns a list of all user IDs stored in the database.
    """
    redis = get_redis()
    # Assume we store timers like 'user:{id}:timer'
    keys = await redis.keys("user:*:timer")
    return [int(k.split(":")[1]) for k in keys]


async def get_user_timer(user_id: int) -> int:
    """
    Retrieves the user timer from Redis.
    """
    redis = get_redis()
    hours = await redis.get(f"user:{user_id}:timer")
    return int(hours) if hours else 0


async def get_user_prompt(user_id: int) -> Optional[str]:
    redis = get_redis()
    return await redis.get(f"user:{user_id}:prompt")


async def set_user_radius(user_id: int, radius: int) -> None:
    redis = get_redis()
    await redis.set(f"user:{user_id}:radius", str(radius))


async def get_user_radius(user_id: int) -> int:
    redis = get_redis()
    radius = await redis.get(f"user:{user_id}:radius")
    return int(radius) if radius else 50


async def set_user_language(user_id: int, lang: str) -> None:
    redis = get_redis()
    await redis.set(f"user:{user_id}:lang", lang)


async def get_user_language(user_id: int) -> str:
    redis = get_redis()
    lang = await redis.get(f"user:{user_id}:lang")
    return lang if lang else "en"


async def set_user_zip(user_id: int, zip_code: str) -> None:
    redis = get_redis()
    await redis.set(f"user:{user_id}:zip", zip_code)


async def get_user_zip(user_id: int) -> Optional[str]:
    redis = get_redis()
    return await redis.get(f"user:{user_id}:zip")
