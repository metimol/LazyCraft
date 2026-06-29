from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from ai.fast_search_ai import filter_best_items
from database.parsers import get_parsers, has_seen_items, is_item_seen, mark_item_seen
from database.users import get_user_radius, get_user_zip
from kleinanzeigen_api import KleinanzeigenAPI
from utils.split_message import split_message

scheduler = AsyncIOScheduler()


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
        location_id = None
        if user_location:
            locations = await api.resolve_location(str(user_location))
            if locations:
                location_id = locations[0][0]
            else:
                location_id = str(user_location)

        new_items = []
        seen_old_items_count = 0

        is_first_run = not await has_seen_items(user_id, parser_name)

        if config["type"] == "category":
            for page in range(40):  # hard limit to 40 pages to prevent infinite loops
                if is_first_run and page >= 3:
                    break

                total, page_items = await api.search_page(
                    category_id=config["target"],
                    page=page,
                    size=40,
                    distance_km=user_distance,
                    location_id=location_id,
                    min_price=config.get("min_price"),
                    max_price=config.get("max_price"),
                )

                if not page_items:
                    break

                for item in page_items:
                    if not await is_item_seen(user_id, parser_name, item.id):
                        await mark_item_seen(user_id, parser_name, item.id)
                        new_items.append(item)
                    else:
                        seen_old_items_count += 1

                # If we've seen multiple old items on this page, assume we've caught up with previously seen ads
                if seen_old_items_count >= 10:
                    break
        else:
            optimized_queries = config.get("optimized_queries", [config["target"]])
            for q in optimized_queries:
                seen_old_items_count = 0
                for page in range(40):
                    if is_first_run and page >= 5:
                        break

                    total, page_items = await api.search_page(
                        q=q,
                        page=page,
                        size=40,
                        distance_km=user_distance,
                        location_id=location_id,
                        min_price=config.get("min_price"),
                        max_price=config.get("max_price"),
                    )

                    if not page_items:
                        break

                    for item in page_items:
                        if not await is_item_seen(user_id, parser_name, item.id):
                            await mark_item_seen(user_id, parser_name, item.id)
                            new_items.append(item)
                        else:
                            seen_old_items_count += 1

                    if seen_old_items_count >= 10:
                        break

    if not new_items:
        return

    # Combine or filter
    if config["ai_filter"] and config["ai_prompt"]:
        # Only process a batch to save tokens/time if there are many new items
        stripped_items = []
        for i in new_items:
            stripped_items.append({"id": i.id, "title": i.title, "price": i.price})

        best_ids = await filter_best_items(stripped_items, config["ai_prompt"])
        best_items = [i for i in new_items if i.id in best_ids]
    else:
        best_items = new_items

    if not best_items:
        return

    msg = f"Parser: {parser_name} found {len(best_items)} new items:\n\n"
    for item in best_items:
        price_str = f"{item.price} EUR" if item.price else item.price_type
        msg += f"- <a href='{item.url}'>{item.title}</a> | {price_str}\n\n"

    async for chunk in split_message(msg):
        await bot.send_message(
            chat_id=user_id,
            text=chunk,
            disable_web_page_preview=True,
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
