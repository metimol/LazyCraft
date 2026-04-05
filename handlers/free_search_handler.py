from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message
from utils.redis_database import get_user_radius, get_user_prompt
from utils.scrape_kleinanzeigen import scrape_all_pages
from utils.direct_ai_filter import filter_items_with_llm
from utils.split_message import split_message
from const import phrases

router = Router()

@router.message(F.text == "🏴‍☠️ Чекнуть халяву")
@router.message(Command("free"))
async def manual_free_check(message: Message):
    status_msg = await message.answer(phrases.get_value("manual_search_started"))

    radius = await get_user_radius(message.from_user.id)
    prompt = await get_user_prompt(message.from_user.id)

    async def update_progress(page: int, found_count: int):
        try:
            await status_msg.edit_text(
                f"{phrases.get_value('SEARCHING_ZU_VERSHENKEN')}\n\n"
                f"{phrases.get_value('CHECKED_PAGES').format(page=page)}\n"
                f"{phrases.get_value('ITEMS_FOUNDED').format(count=found_count)}"
            )
        except Exception:
            pass

    items = await scrape_all_pages(radius=radius, query="", max_price=0, progress_callback=update_progress)
    result = await filter_items_with_llm(items, prompt, radius)

    await status_msg.delete()

    async for chunk in split_message(result):
        await message.answer(chunk)