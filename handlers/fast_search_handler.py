import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from ai.fast_search_ai import filter_best_items, generate_optimized_queries
from const import locale
from database.limits import check_fast_search_limit
from database.users import get_user_radius, get_user_zip
from kleinanzeigen_api import KleinanzeigenAPI
from utils.filters import TextLoc
from utils.keyboards import (
    get_cancel_keyboard,
    get_categories_keyboard,
    get_fs_category_prompt_keyboard,
    get_price_limit_keyboard,
)
from utils.split_message import split_message

logger = logging.getLogger(__name__)

router = Router()


class FSState(StatesGroup):
    waiting_for_category_choice = State()
    waiting_for_category = State()
    waiting_for_query = State()
    waiting_for_price_limit_choice = State()
    waiting_for_min_price = State()
    waiting_for_max_price = State()


@router.message(TextLoc("fast_search_btn"))
async def fast_search_entry(message: Message, state: FSMContext) -> None:
    user_zip = await get_user_zip(message.from_user.id)
    if not user_zip:
        await message.answer(locale("missing_zip_code"))
        return

    allowed, time_left = await check_fast_search_limit(message.from_user.id)
    if not allowed:
        await message.answer(locale("fs_limit_reached").format(time_left=time_left))
        return

    await message.answer(
        locale("fs_ask_category"),
        reply_markup=get_fs_category_prompt_keyboard(),
    )
    await state.set_state(FSState.waiting_for_category_choice)


@router.callback_query(F.data == "fs_cat_yes", FSState.waiting_for_category_choice)
async def process_fs_cat_yes(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.message.edit_text(
        locale("choose_category"),
        reply_markup=get_categories_keyboard(0),
    )
    await state.set_state(FSState.waiting_for_category)


@router.callback_query(F.data == "fs_cat_no", FSState.waiting_for_category_choice)
async def process_fs_cat_no(callback: CallbackQuery, state: FSMContext) -> None:
    await state.update_data(fs_category=None)
    await callback.message.edit_text(
        locale("fs_enter_query"), reply_markup=get_cancel_keyboard()
    )
    await state.set_state(FSState.waiting_for_query)


@router.callback_query(F.data.startswith("catpage_"), FSState.waiting_for_category)
async def process_fs_catpage(callback: CallbackQuery) -> None:
    page = int(callback.data.split("_")[1])
    await callback.message.edit_reply_markup(reply_markup=get_categories_keyboard(page))


@router.callback_query(F.data.startswith("cat_"), FSState.waiting_for_category)
async def process_fs_cat_selection(callback: CallbackQuery, state: FSMContext) -> None:
    cat_id = callback.data.split("_")[1]
    await state.update_data(fs_category=cat_id)
    await callback.message.edit_text(
        locale("fs_enter_query"), reply_markup=get_cancel_keyboard()
    )
    await state.set_state(FSState.waiting_for_query)


@router.message(FSState.waiting_for_query, ~F.text.startswith("/"))
async def process_fs_query(message: Message, state: FSMContext) -> None:
    user_query = message.text.strip()
    await state.update_data(fs_query=user_query)

    await message.answer(
        locale("ask_price_limits"),
        reply_markup=get_price_limit_keyboard(),
    )
    await state.set_state(FSState.waiting_for_price_limit_choice)


@router.callback_query(
    F.data == "pricelimit_no",
    FSState.waiting_for_price_limit_choice,
)
async def skip_fs_price_limits(callback: CallbackQuery, state: FSMContext) -> None:
    await state.update_data(fs_min_price=None, fs_max_price=None)
    await callback.message.delete()
    await execute_fast_search(callback.message, state, callback.from_user.id)


@router.callback_query(
    F.data == "pricelimit_yes",
    FSState.waiting_for_price_limit_choice,
)
async def ask_fs_min_price(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.message.edit_text(
        locale("enter_min_price"), reply_markup=get_cancel_keyboard()
    )
    await state.set_state(FSState.waiting_for_min_price)


@router.message(FSState.waiting_for_min_price, ~F.text.startswith("/"))
async def process_fs_min_price(message: Message, state: FSMContext) -> None:
    try:
        min_price = int(message.text.strip())
        await state.update_data(fs_min_price=min_price if min_price > 0 else None)
    except ValueError:
        await message.answer(
            locale("invalid_price"), reply_markup=get_cancel_keyboard()
        )
        return

    await message.answer(locale("enter_max_price"), reply_markup=get_cancel_keyboard())
    await state.set_state(FSState.waiting_for_max_price)


@router.message(FSState.waiting_for_max_price, ~F.text.startswith("/"))
async def process_fs_max_price(message: Message, state: FSMContext) -> None:
    try:
        max_price = int(message.text.strip())
        await state.update_data(fs_max_price=max_price if max_price > 0 else None)
    except ValueError:
        await message.answer(
            locale("invalid_price"), reply_markup=get_cancel_keyboard()
        )
        return

    await execute_fast_search(message, state, message.from_user.id)


def format_item(item) -> str:
    price_str = f"{item.price} EUR" if item.price else item.price_type
    if item.price and item.price_type in ("NEGOTIABLE", "PLEASE_CONTACT"):
        price_str += " VB"
    dist_str = f" ({item.distance})" if item.distance else ""
    return f"- <a href='{item.url}'>{item.title}</a> | {price_str}{dist_str}\n\n"


async def execute_fast_search(message, state: FSMContext, user_id: int) -> None:  # noqa: C901
    data = await state.get_data()
    user_query = data.get("fs_query")
    category_id = data.get("fs_category")
    min_price = data.get("fs_min_price")
    max_price = data.get("fs_max_price")

    user_location = await get_user_zip(user_id)
    user_distance = await get_user_radius(user_id)

    if isinstance(message, CallbackQuery):
        status_msg = await message.message.answer(locale("fs_live_optimizing"))
    else:
        status_msg = await message.answer(locale("fs_live_optimizing"))

    # 1. AI Optimization
    optimized_queries = await generate_optimized_queries(user_query)
    if not optimized_queries:
        optimized_queries = [user_query]

    await status_msg.edit_text(locale("fs_live_scraping"))

    # 2. Sequential Scrape with Jitter
    all_items = []
    seen_ids = set()

    async with KleinanzeigenAPI() as api:
        for _i, q in enumerate(optimized_queries):
            try:
                items = await api.search(
                    location=user_location,
                    q=q,
                    category_id=category_id,
                    distance_km=user_distance,
                    min_price=min_price,
                    max_price=max_price,
                    pages=40,
                )
                for item in items:
                    if item.id not in seen_ids:
                        seen_ids.add(item.id)
                        all_items.append(item)
            except Exception as e:  # noqa: PERF203, BLE001
                logger.warning("Error searching for %s: %s", q, e)

    if not all_items:
        await status_msg.edit_text(locale("fs_no_results"))
        await state.clear()
        return

    # 3. AI Filtering
    await status_msg.edit_text(locale("fs_live_filtering").format(count=len(all_items)))

    # Strip data down to minimal JSON to save tokens
    stripped_items = [
        {"id": i.id, "title": i.title, "price": i.price} for i in all_items
    ]

    best_ids = await filter_best_items(stripped_items, user_query)

    best_items = [i for i in all_items if i.id in best_ids]
    if not best_items:
        # Fallback up to 30 items if AI fails
        best_items = all_items[:30]

    # 4. Final Output
    await status_msg.delete()

    markdown_table = locale("fs_results_title")
    for item in best_items:
        markdown_table += format_item(item)

    async for chunk in split_message(markdown_table):
        await message.answer(chunk, disable_web_page_preview=True)

    await state.clear()
