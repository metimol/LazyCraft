from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiogram import Bot
from database.users import get_user_radius, get_user_prompt, get_user_zip
from ai.fast_search_ai import filter_best_items
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

    stripped_items = []
    for i in items:
        stripped_items.append({"id": i.id, "title": i.title, "price": i.price})

    best_ids = await filter_best_items(stripped_items, prompt)
    best_items = [i for i in items if i.id in best_ids]

    if not best_items:
        return

    msg = f"Free Check found {len(best_items)} items:\n\n"
    for item in best_items:
        price_str = f"{item.price} EUR" if item.price else item.price_type
        msg += f"- <a href='{item.url}'>{item.title}</a> | {price_str}\n\n"

    async for chunk in split_message(msg):
        await bot.send_message(
            chat_id=user_id, text=chunk, disable_web_page_preview=True
        )


async def scheduled_parser_check(bot: Bot, user_id: int, parser_name: str):
    parsers = await get_parsers(user_id)
    if parser_name not in parsers:
        return

    config = parsers[parser_name]
    if not config["active"]:
        return

    user_location = await get_user_zip(user_id)
    user_distance = await get_user_radius(user_id)

    async with KleinanzeigenAPI() as api:
        # TODO: Why only first two pages? If user has timer every 12 or 24 hours for example... But limit fo 50 items pro message...
        if config["type"] == "category":
            total, items = await api.search(
                category_id=config["target"],
                pages=2,
                distance_km=user_distance,
                location=user_location,
            )
        else:
            total, items = await api.search_page(
                q=config["target"],
                page=2,
                distance_km=user_distance,
                location=user_location,
            )

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
        # Only process a batch to save tokens/time if there are many new items
        stripped_items = []
        for i in new_items[:50]:
            stripped_items.append({"id": i.id, "title": i.title, "price": i.price})

        best_ids = await filter_best_items(stripped_items, config["ai_prompt"])
        best_items = [i for i in new_items[:50] if i.id in best_ids]
    else:
        best_items = new_items[:50]

    if not best_items:
        return

    msg = f"Parser: {parser_name} found {len(best_items)} new items:\n\n"
    for item in best_items:
        price_str = f"{item.price} EUR" if item.price else item.price_type
        msg += f"- <a href='{item.url}'>{item.title}</a> | {price_str}\n\n"

    async for chunk in split_message(msg):
        await bot.send_message(
            chat_id=user_id, text=chunk, disable_web_page_preview=True
        )


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
