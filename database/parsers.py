import json
from database.client import get_redis


async def add_parser(user_id: int, name: str, data: dict) -> None:
    redis = get_redis()
    await redis.hset(f"user:{user_id}:parsers", name, json.dumps(data))


async def get_parsers(user_id: int) -> dict[str, dict]:
    redis = get_redis()
    raw = await redis.hgetall(f"user:{user_id}:parsers")
    return {k: json.loads(v) for k, v in raw.items()}


async def get_all_users_with_parsers() -> list[int]:
    redis = get_redis()
    keys = await redis.keys("user:*:parsers")
    return [int(k.split(":")[1]) for k in keys]


async def delete_parser(user_id: int, name: str) -> None:
    redis = get_redis()
    await redis.hdel(f"user:{user_id}:parsers", name)
    # Also clean up seen cache for this parser
    await redis.delete(f"user:{user_id}:parser:{name}:seen")


async def toggle_parser(user_id: int, name: str, is_active: bool) -> None:
    parsers = await get_parsers(user_id)
    if name in parsers:
        parsers[name]["active"] = is_active
        await add_parser(user_id, name, parsers[name])


async def is_item_seen(user_id: int, parser_name: str, item_id: str) -> bool:
    redis = get_redis()
    return await redis.sismember(f"user:{user_id}:parser:{parser_name}:seen", item_id)


async def mark_item_seen(user_id: int, parser_name: str, item_id: str) -> None:
    redis = get_redis()
    key = f"user:{user_id}:parser:{parser_name}:seen"
    await redis.sadd(key, item_id)
    # Set a 30 day TTL so it doesn't grow forever
    await redis.expire(key, 60 * 60 * 24 * 30)


async def has_seen_items(user_id: int, parser_name: str) -> bool:
    redis = get_redis()
    return await redis.scard(f"user:{user_id}:parser:{parser_name}:seen") > 0
