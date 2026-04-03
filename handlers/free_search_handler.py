from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message
from utils.redis_database import get_user_radius, get_user_prompt
from utils.scrape_kleinanzeigen import scrape_all_pages
from ai.direct_ai_filter import filter_items_with_llm
from const import phrases

router = Router()

@router.message(F.text == "🏴‍☠️ Чекнуть халяву")
@router.message(Command("free"))
async def manual_free_check(message: Message):
    status_msg = await message.answer(phrases.get_value("manual_search_started"))

    radius = await get_user_radius(message.from_user.id)
    prompt = await get_user_prompt(message.from_user.id)

    items = await scrape_all_pages(radius=radius, query="", max_price=0)
    result = await filter_items_with_llm(items, prompt)

    await status_msg.delete()

    if result.lower() == "сегодня пусто":
        await message.answer(phrases.get_value("nothing_found"))
    else:
        await message.answer(result)