from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiogram import Bot
from utils.redis_database import get_user_radius, get_user_prompt
from utils.scrape_kleinanzeigen import scrape_all_pages
from utils.direct_ai_filter import filter_items_with_llm

scheduler = AsyncIOScheduler()

async def scheduled_free_check(bot: Bot, user_id: int):
    radius = await get_user_radius(user_id)
    prompt = await get_user_prompt(user_id)

    items = await scrape_all_pages(radius=radius, query="", max_price=0)
    result = await filter_items_with_llm(items, prompt, radius)

    if result.lower() != "сегодня пусто":
        await bot.send_message(chat_id=user_id, text=result)

def update_user_job(bot: Bot, user_id: int, hours: int):
    job_id = f"free_check_{user_id}"
    if scheduler.get_job(job_id):
        scheduler.remove_job(job_id)

    if hours > 0:
        scheduler.add_job(
            scheduled_free_check,
            'interval',
            hours=hours,
            id=job_id,
            kwargs={"bot": bot, "user_id": user_id}
        )