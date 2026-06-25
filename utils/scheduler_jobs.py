import random
import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiogram import Bot
from database.users import get_user_radius, get_user_prompt, get_user_zip
from utils.direct_ai_filter import filter_items_with_llm
from utils.split_message import split_message
from database.parsers import get_parsers, is_item_seen, mark_item_seen
from kleinanzeigen_api import KleinanzeigenAPI

scheduler = AsyncIOScheduler()


async def scheduled_free_check(bot: Bot, user_id: int):
    radius = await get_user_radius(user_id)
    prompt = await get_user_prompt(user_id)
    zip_code = await get_user_zip(user_id)

    if not zip_code:
        return

    async with KleinanzeigenAPI() as api:
        location_id = zip_code
        locations = await api.resolve_location(str(zip_code))
        if locations:
            location_id = locations[0][0]

        total, items = await api.search_page(
            q="", location_id=location_id, max_price=0, distance_km=radius, size=20
        )

    if not items:
        return

    result = await filter_items_with_llm(items, prompt)

    if result.lower() != "none":
        async for chunk in split_message(result):
            await bot.send_message(chat_id=user_id, text=chunk)


async def scheduled_parser_check(bot: Bot, user_id: int, parser_name: str):
    # Stagger execution to avoid limits and flooding
    await asyncio.sleep(random.uniform(6, 300))

    parsers = await get_parsers(user_id)
    if parser_name not in parsers:
        return

    config = parsers[parser_name]
    if not config["active"]:
        return

    async with KleinanzeigenAPI() as api:
        if config["type"] == "category":
            total, items = await api.search_page(category_id=config["target"], page=0)
        else:
            total, items = await api.search_page(q=config["target"], page=0)

    if not items:
        return

    new_items = []
    for item in items:
        if not await is_item_seen(user_id, parser_name, item.id):
            await mark_item_seen(user_id, parser_name, item.id)
            new_items.append(item)

    if not new_items:
        return

    # Combine or filter
    if config["ai_filter"] and config["ai_prompt"]:
        # Only process a batch to save tokens/time if there are many new itemsms
        result = await filter_items_with_llm(new_items[:50], config["ai_prompt"])
        if result and result.lower() != "none":
            async for chunk in split_message(f"Parser: {parser_name}\n\n{result}"):
                await bot.send_message(chat_id=user_id, text=chunk)
    else:
        # Without AI, just send raw messages for up to top 50 new items to prevent flooding
        msg = f"Parser: {parser_name} found {len(new_items)} new items:\n\n"
        for i in new_items[:50]:
            msg += f"- {i.title}\n{i.url}\n\n"

        async for chunk in split_message(msg):
            await bot.send_message(chat_id=user_id, text=chunk)


def add_parser_job(bot: Bot, user_id: int, parser_name: str, minutes: int):
    job_id = f"parser_{user_id}_{parser_name}"
    if scheduler.get_job(job_id):
        scheduler.remove_job(job_id)

    if minutes > 0:
        scheduler.add_job(
            scheduled_parser_check,
            "interval",
            minutes=minutes,
            id=job_id,
            kwargs={"bot": bot, "user_id": user_id, "parser_name": parser_name},
        )


def remove_parser_job(user_id: int, parser_name: str):
    job_id = f"parser_{user_id}_{parser_name}"
    if scheduler.get_job(job_id):
        scheduler.remove_job(job_id)
