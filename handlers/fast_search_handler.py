import asyncio
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from const import locale
from database.limits import check_fast_search_limit
from utils.keyboards import get_fs_category_prompt_keyboard, get_categories_keyboard
from utils.split_message import split_message
from kleinanzeigen_api import KleinanzeigenAPI
from ai.fast_search_ai import generate_optimized_queries, filter_best_items
from database.users import get_user_zip

router = Router()


class FSState(StatesGroup):
    waiting_for_category_choice = State()
    waiting_for_category = State()
    waiting_for_query = State()


@router.message(F.text == locale("fast_search_btn"))
async def fast_search_entry(message: Message, state: FSMContext):
    user_zip = await get_user_zip(message.from_user.id)
    if not user_zip:
        await message.answer(locale("missing_zip_code"))
        return

    allowed, time_left = await check_fast_search_limit(message.from_user.id)
    if not allowed:
        await message.answer(locale("fs_limit_reached").format(time_left=time_left))
        return

    await message.answer(
        locale("fs_ask_category"), reply_markup=get_fs_category_prompt_keyboard()
    )
    await state.set_state(FSState.waiting_for_category_choice)


@router.callback_query(F.data == "fs_cat_yes", FSState.waiting_for_category_choice)
async def process_fs_cat_yes(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        locale("choose_category"), reply_markup=get_categories_keyboard(0)
    )
    await state.set_state(FSState.waiting_for_category)


@router.callback_query(F.data == "fs_cat_no", FSState.waiting_for_category_choice)
async def process_fs_cat_no(callback: CallbackQuery, state: FSMContext):
    await state.update_data(fs_category=None)
    await callback.message.edit_text(locale("fs_enter_query"))
    await state.set_state(FSState.waiting_for_query)


@router.callback_query(F.data.startswith("catpage_"), FSState.waiting_for_category)
async def process_fs_catpage(callback: CallbackQuery):
    page = int(callback.data.split("_")[1])
    await callback.message.edit_reply_markup(reply_markup=get_categories_keyboard(page))


@router.callback_query(F.data.startswith("cat_"), FSState.waiting_for_category)
async def process_fs_cat_selection(callback: CallbackQuery, state: FSMContext):
    cat_id = callback.data.split("_")[1]
    await state.update_data(fs_category=cat_id)
    await callback.message.edit_text(locale("fs_enter_query"))
    await state.set_state(FSState.waiting_for_query)


@router.message(FSState.waiting_for_query, ~F.text.startswith("/"))
async def process_fs_query(message: Message, state: FSMContext):
    user_query = message.text.strip()
    data = await state.get_data()
    category_id = data.get("fs_category")

    status_msg = await message.answer(locale("fs_live_optimizing"))

    # 1. AI Optimization
    optimized_queries = await generate_optimized_queries(user_query)
    if not optimized_queries:
        optimized_queries = [user_query]

    await status_msg.edit_text(locale("fs_live_scraping"))

    # 2. Asynchronous Multithreaded Scrape
    all_items = []
    seen_ids = set()

    async def fetch_query(api, q):
        try:
            return await api.search(q=q, category_id=category_id, pages=2)
        except Exception:
            return []

    async with KleinanzeigenAPI() as api:
        tasks = [fetch_query(api, q) for q in optimized_queries]
        results = await asyncio.gather(*tasks)

        for items in results:
            for item in items:
                if item.id not in seen_ids:
                    seen_ids.add(item.id)
                    all_items.append(item)

    if not all_items:
        await status_msg.edit_text(locale("fs_no_results"))
        await state.clear()
        return

    # 3. AI Filtering
    await status_msg.edit_text(locale("fs_live_filtering").format(count=len(all_items)))

    # Strip data down to minimal JSON to save tokens
    stripped_items = []
    for i in all_items:
        stripped_items.append(
            {
                "id": i.id,
                "title": i.title,
                "price": i.price,
                "distance": 0,  # Not using location yet
            }
        )

    best_ids = await filter_best_items(stripped_items, user_query)

    best_items = [i for i in all_items if i.id in best_ids]
    if not best_items:
        # Fallback to top 10 if AI fails
        best_items = all_items[:10]

    # 4. Final Output
    await status_msg.delete()

    markdown_table = locale("fs_results_title")
    for item in best_items:
        price_str = f"{item.price} EUR" if item.price else item.price_type
        markdown_table += f"- <a href='{item.url}'>{item.title}</a> | {price_str}\n\n"

    async for chunk in split_message(markdown_table):
        await message.answer(chunk, disable_web_page_preview=True)

    await state.clear()
