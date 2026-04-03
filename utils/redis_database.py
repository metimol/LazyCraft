import os
import redis.asyncio as redis
from const import DEFAULT_SEARCH_PROMPT

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
r = redis.Redis(host=REDIS_HOST, port=6379, decode_responses=True)

async def get_user_prompt(user_id: int) -> str:
    val = await r.get(f"lazy:prompt:{user_id}")
    return val if val else DEFAULT_SEARCH_PROMPT

async def set_user_prompt(user_id: int, prompt: str):
    await r.set(f"lazy:prompt:{user_id}", prompt)

async def get_user_radius(user_id: int) -> int:
    val = await r.get(f"lazy:radius:{user_id}")
    return int(val) if val else 10

async def set_user_radius(user_id: int, radius: int):
    await r.set(f"lazy:radius:{user_id}", radius)

async def get_user_timer(user_id: int) -> int:
    val = await r.get(f"lazy:timer:{user_id}")
    return int(val) if val else 0

async def set_user_timer(user_id: int, hours: int):
    await r.set(f"lazy:timer:{user_id}", hours)