from __future__ import annotations

from database.client import get_redis
from kleinanzeigen_api.categories import get_category


async def get_all_users() -> list[int]:
    """Returns a list of all user IDs stored in the database."""
    redis = get_redis()
    # Assume we store timers like 'user:{id}:timer'
    keys = await redis.keys("user:*:timer")
    return [int(k.split(":")[1]) for k in keys]


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
    return lang or "en"


async def set_user_zip(user_id: int, zip_code: str) -> None:
    redis = get_redis()
    await redis.set(f"user:{user_id}:zip", zip_code)


async def get_user_zip(user_id: int) -> str | None:
    redis = get_redis()
    return await redis.get(f"user:{user_id}:zip")


async def add_favorite_category(user_id: int, cat_id: str) -> None:
    redis = get_redis()
    await redis.sadd(f"user:{user_id}:fav_cats", str(cat_id))


async def remove_favorite_category(user_id: int, cat_id: str) -> None:
    redis = get_redis()
    await redis.srem(f"user:{user_id}:fav_cats", str(cat_id))


async def get_favorite_categories(user_id: int) -> set[str]:
    redis = get_redis()
    members = await redis.smembers(f"user:{user_id}:fav_cats")
    if not members:
        return set()
    return {str(m) for m in members if get_category(str(m)) is not None}
