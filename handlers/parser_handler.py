from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from const import locale
from database.parsers import get_parsers, add_parser, delete_parser, toggle_parser
from database.users import get_user_zip
from utils.keyboards import (
    get_parser_menu_keyboard,
    get_parser_type_keyboard,
    get_parser_frequency_keyboard,
    get_ai_filter_keyboard,
    get_categories_keyboard,
    get_manage_parsers_keyboard,
    get_parser_action_keyboard,
    get_price_limit_keyboard,
)

from utils.scheduler_jobs import add_parser_job, remove_parser_job
from ai.fast_search_ai import generate_optimized_queries

router = Router()


class ParserState(StatesGroup):
    waiting_for_name = State()
    waiting_for_query = State()
    waiting_for_price_limit_choice = State()
    waiting_for_min_price = State()
    waiting_for_max_price = State()
    waiting_for_ai_prompt = State()


@router.message(F.text == locale("auto_parser_btn"))
@router.message(Command("parsers"))
async def parser_menu_cmd(message: Message):
    user_zip = await get_user_zip(message.from_user.id)
    if not user_zip:
        await message.answer(locale("missing_zip_code"))
        return
    await message.answer(locale("parser_menu"), reply_markup=get_parser_menu_keyboard())


@router.callback_query(F.data == "parser_add")
async def process_parser_add(callback: CallbackQuery, state: FSMContext):
    user_zip = await get_user_zip(
        callback.fromuser.id if hasattr(callback, "fromuser") else callback.from_user.id
    )
    if not user_zip:
        await callback.answer(locale("missing_zip_code"), show_alert=True)
        return

    parsers = await get_parsers(callback.from_user.id)
    if len(parsers) >= 5:
        await callback.message.edit_text(locale("parser_limit_reached"))
        return
    await callback.message.edit_text(locale("enter_parser_name"))
    await state.set_state(ParserState.waiting_for_name)


@router.message(ParserState.waiting_for_name)
async def process_parser_name(message: Message, state: FSMContext):
    name = message.text.strip()
    if len(name) > 40:
        await message.answer(locale("parser_name_too_long").format(max_length=40))
        return

    parsers = await get_parsers(message.from_user.id)
    if name in parsers:
        await message.answer(locale("parser_already_exists"))
        return

    await state.update_data(parser_name=name)
    await message.answer(
        locale("choose_search_type"), reply_markup=get_parser_type_keyboard()
    )


@router.callback_query(F.data == "ptype_category", ParserState.waiting_for_name)
async def process_ptype_category(callback: CallbackQuery, state: FSMContext):
    await state.update_data(parser_type="category")
    await callback.message.edit_text(
        locale("choose_category"), reply_markup=get_categories_keyboard(0)
    )


@router.callback_query(F.data.startswith("catpage_"), ParserState.waiting_for_name)
async def process_catpage(callback: CallbackQuery):
    page = int(callback.data.split("_")[1])
    await callback.message.edit_reply_markup(reply_markup=get_categories_keyboard(page))


@router.callback_query(F.data.startswith("cat_"), ParserState.waiting_for_name)
async def process_cat_selection(callback: CallbackQuery, state: FSMContext):
    cat_id = callback.data.split("_")[1]
    await state.update_data(parser_target=cat_id)
    await callback.message.edit_text(
        locale("ask_price_limits"), reply_markup=get_price_limit_keyboard()
    )
    await state.set_state(ParserState.waiting_for_price_limit_choice)


@router.callback_query(F.data == "ptype_query", ParserState.waiting_for_name)
async def process_ptype_query(callback: CallbackQuery, state: FSMContext):
    await state.update_data(parser_type="query")
    await callback.message.edit_text(locale("enter_query"))
    await state.set_state(ParserState.waiting_for_query)


@router.message(ParserState.waiting_for_query)
async def process_parser_query(message: Message, state: FSMContext):
    user_query = message.text.strip()
    await state.update_data(parser_target=user_query)

    status_msg = await message.answer(locale("fs_live_optimizing"))
    optimized_queries = await generate_optimized_queries(user_query, max_queries=3)
    await state.update_data(parser_optimized_queries=optimized_queries)
    await status_msg.delete()

    await message.answer(
        locale("ask_price_limits"), reply_markup=get_price_limit_keyboard()
    )
    await state.set_state(ParserState.waiting_for_price_limit_choice)


@router.callback_query(
    F.data == "pricelimit_no", ParserState.waiting_for_price_limit_choice
)
async def skip_parser_price_limits(callback: CallbackQuery, state: FSMContext):
    await state.update_data(parser_min_price=None, parser_max_price=None)
    await callback.message.edit_text(
        locale("choose_frequency"), reply_markup=get_parser_frequency_keyboard()
    )
    await state.set_state(
        ParserState.waiting_for_max_price
    )  # Setting to max price state so frequency handles it


@router.callback_query(
    F.data == "pricelimit_yes", ParserState.waiting_for_price_limit_choice
)
async def ask_parser_min_price(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(locale("enter_min_price"))
    await state.set_state(ParserState.waiting_for_min_price)


@router.message(ParserState.waiting_for_min_price, ~F.text.startswith("/"))
async def process_parser_min_price(message: Message, state: FSMContext):
    try:
        min_price = int(message.text.strip())
        await state.update_data(parser_min_price=min_price if min_price > 0 else None)
    except ValueError:
        await message.answer(locale("invalid_price"))
        return

    await message.answer(locale("enter_max_price"))
    await state.set_state(ParserState.waiting_for_max_price)


@router.message(ParserState.waiting_for_max_price, ~F.text.startswith("/"))
async def process_parser_max_price(message: Message, state: FSMContext):
    try:
        max_price = int(message.text.strip())
        await state.update_data(parser_max_price=max_price if max_price > 0 else None)
    except ValueError:
        await message.answer(locale("invalid_price"))
        return

    await message.answer(
        locale("choose_frequency"), reply_markup=get_parser_frequency_keyboard()
    )


@router.callback_query(F.data.startswith("freq_"), ParserState.waiting_for_max_price)
async def process_frequency(callback: CallbackQuery, state: FSMContext):
    freq = int(callback.data.split("_")[1])
    await state.update_data(parser_freq=freq)
    await callback.message.edit_text(
        locale("enable_ai_filter"), reply_markup=get_ai_filter_keyboard()
    )


@router.callback_query(
    F.data.startswith("aifilter_"), ParserState.waiting_for_max_price
)
async def process_ai_filter(callback: CallbackQuery, state: FSMContext, bot: Bot):
    enable_ai = callback.data == "aifilter_yes"
    await state.update_data(parser_ai=enable_ai)

    if enable_ai:
        await callback.message.edit_text(locale("enter_ai_prompt"))
        await state.set_state(ParserState.waiting_for_ai_prompt)
    else:
        await state.update_data(parser_ai_prompt="")
        await finish_parser_creation(
            callback.message, state, callback.from_user.id, bot
        )


@router.message(ParserState.waiting_for_ai_prompt)
async def process_ai_prompt(message: Message, state: FSMContext, bot: Bot):
    await state.update_data(parser_ai_prompt=message.text.strip())
    await finish_parser_creation(message, state, message.from_user.id, bot)


async def finish_parser_creation(
    message: Message, state: FSMContext, user_id: int, bot: Bot
):
    data = await state.get_data()
    name = data.get("parser_name")
    if not name:
        await message.answer(locale("session_expired"))
        await state.clear()
        return

    config = {
        "type": data["parser_type"],
        "target": data["parser_target"],
        "optimized_queries": data.get(
            "parser_optimized_queries", [data["parser_target"]]
        ),
        "freq": data["parser_freq"],
        "ai_filter": data["parser_ai"],
        "ai_prompt": data["parser_ai_prompt"],
        "min_price": data.get("parser_min_price"),
        "max_price": data.get("parser_max_price"),
        "active": True,
    }

    await add_parser(user_id, name, config)
    add_parser_job(bot, user_id, name, config["freq"])

    await message.answer(locale("parser_created").format(name=name))
    await state.clear()


# Manage Existing
@router.callback_query(F.data == "parser_manage")
async def process_parser_manage(callback: CallbackQuery):
    parsers = await get_parsers(callback.from_user.id)
    if not parsers:
        await callback.message.edit_text(locale("no_parsers_found"))
        return
    await callback.message.edit_text(
        locale("manage_parsers_menu"), reply_markup=get_manage_parsers_keyboard(parsers)
    )


@router.callback_query(F.data.startswith("managep_"))
async def process_manage_specific_parser(callback: CallbackQuery):
    name = callback.data.split("_", 1)[1]
    parsers = await get_parsers(callback.from_user.id)
    if name not in parsers:
        await callback.answer("Parser not found")
        return

    config = parsers[name]
    status = "Active" if config["active"] else "Paused"
    text = locale("parser_info").format(
        name=name, status=status, type=config["type"], freq=config["freq"]
    )
    await callback.message.edit_text(
        text, reply_markup=get_parser_action_keyboard(name, config["active"])
    )


@router.callback_query(F.data.startswith("pact_toggle_"))
async def process_parser_toggle(callback: CallbackQuery, bot: Bot):
    name = callback.data.split("_", 2)[2]
    parsers = await get_parsers(callback.from_user.id)
    if name not in parsers:
        return

    is_active = not parsers[name]["active"]
    await toggle_parser(callback.fromuser.id, name, is_active)

    if is_active:
        add_parser_job(bot, callback.from_user.id, name, parsers[name]["freq"])
        await callback.answer(locale("parser_resumed"))
    else:
        remove_parser_job(callback.from_user.id, name)
        await callback.answer(locale("parser_paused"))

    config = parsers[name]
    config["active"] = is_active
    status = "Active" if is_active else "Paused"
    text = locale("parser_info").format(
        name=name, status=status, type=config["type"], freq=config["freq"]
    )
    await callback.message.edit_text(
        text, reply_markup=get_parser_action_keyboard(name, is_active)
    )


@router.callback_query(F.data.startswith("pact_delete_"))
async def process_parser_delete(callback: CallbackQuery):
    name = callback.data.split("_", 2)[2]
    await delete_parser(callback.from_user.id, name)
    remove_parser_job(callback.from_user.id, name)

    await callback.message.edit_text(locale("parser_deleted").format(name=name))
