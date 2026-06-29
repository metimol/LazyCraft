from datetime import datetime, timedelta

import pytz

from database.client import get_redis


# TODO: Free users will have 3 searches per day
async def check_fast_search_limit(
    user_id: int,
    max_searches: int = 30,
) -> tuple[bool, str]:
    """Checks if a user has exceeded their daily limit.
    Returns (True, "") if allowed.
    Returns (False, "Xh Ym") with remaining time until midnight Berlin if exceeded.
    """
    redis = get_redis()
    berlin_tz = pytz.timezone("Europe/Berlin")
    now = datetime.now(berlin_tz)
    date_str = now.strftime("%Y-%m-%d")
    key = f"user:{user_id}:fs_limit:{date_str}"

    count = await redis.get(key)
    if count and int(count) >= max_searches:
        tomorrow = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(
            days=1,
        )
        diff = tomorrow - now
        hours, remainder = divmod(diff.seconds, 3600)
        minutes, _ = divmod(remainder, 60)
        return False, f"{hours}h {minutes}m"

    await redis.incr(key)
    await redis.expire(key, 86400 * 2)
    return True, ""
