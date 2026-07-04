from __future__ import annotations

from typing import TYPE_CHECKING

from aiogram import Bot, F, Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from ai.fast_search_ai import generate_optimized_queries
from const import locale
from database.parsers import (
    add_parser,
    delete_parser,
    get_parsers,
    rename_parser,
    toggle_parser,
)
from database.users import get_favorite_categories, get_user_zip
from kleinanzeigen_api.categories import get_category
from utils.filters import TextLoc
from utils.keyboards import (
    get_ai_filter_keyboard,
    get_cancel_keyboard,
    get_categories_keyboard,
    get_category_source_keyboard,
    get_manage_parsers_keyboard,
    get_parser_action_keyboard,
    get_parser_edit_cancel_keyboard,
    get_parser_edit_keyboard,
    get_parser_frequency_keyboard,
    get_parser_menu_keyboard,
    get_parser_type_keyboard,
    get_price_limit_keyboard,
)
from utils.scheduler_jobs import add_parser_job, remove_parser_job

if TYPE_CHECKING:
    from aiogram.fsm.context import FSMContext

router = Router()


class ParserState(StatesGroup):
    waiting_for_name = State()
    waiting_for_category = State()
    waiting_for_query = State()
    waiting_for_price_limit_choice = State()
    waiting_for_min_price = State()
    waiting_for_max_price = State()
    waiting_for_ai_prompt = State()


class ParserEditState(StatesGroup):
    waiting_for_name = State()
    waiting_for_query = State()
    waiting_for_category = State()
    waiting_for_ai_prompt = State()


@router.message(TextLoc("auto_parser_btn"))
@router.message(Command("parsers"))
async def parser_menu_cmd(message: Message) -> None:
    user_zip = await get_user_zip(message.from_user.id)
    if not user_zip:
        await message.answer(locale("missing_zip_code"))
        return
    await message.answer(locale("parser_menu"), reply_markup=get_parser_menu_keyboard())


@router.callback_query(F.data == "parser_add")
async def process_parser_add(callback: CallbackQuery, state: FSMContext) -> None:
    user_zip = await get_user_zip(callback.from_user.id)
    if not user_zip:
        await callback.answer(
            locale("missing_zip_code", strip_html=True), show_alert=True
        )
        return

    parsers = await get_parsers(callback.from_user.id)
    if len(parsers) >= 5:
        await callback.message.edit_text(locale("parser_limit_reached"))
        return
    await callback.message.edit_text(
        locale("enter_parser_name"), reply_markup=get_cancel_keyboard()
    )
    await state.set_state(ParserState.waiting_for_name)


@router.message(ParserState.waiting_for_name)
async def process_parser_name(message: Message, state: FSMContext) -> None:
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
        locale("choose_search_type"),
        reply_markup=get_parser_type_keyboard(),
    )


@router.callback_query(F.data == "ptype_category", ParserState.waiting_for_name)
async def process_ptype_category(callback: CallbackQuery, state: FSMContext) -> None:
    await state.update_data(parser_type="category")
    await callback.message.edit_text(
        locale("choose_category_source"),
        reply_markup=get_category_source_keyboard(),
    )
    await state.set_state(ParserState.waiting_for_category)


@router.callback_query(
    F.data.startswith("catsrc_"),
    StateFilter(ParserState.waiting_for_category, ParserEditState.waiting_for_category),
)
async def process_parser_catsrc(callback: CallbackQuery) -> None:
    mode = callback.data.split("_")[1]
    fav_ids = None
    if mode == "fav":
        fav_ids = await get_favorite_categories(callback.from_user.id)
        if not fav_ids:
            await callback.answer(
                locale("no_fav_categories", strip_html=True), show_alert=True
            )
            return

    await callback.message.edit_text(
        locale("choose_category"),
        reply_markup=get_categories_keyboard(0, mode=mode, fav_ids=fav_ids),
    )


@router.callback_query(
    F.data.startswith("catpage_"),
    StateFilter(ParserState.waiting_for_category, ParserEditState.waiting_for_category),
)
async def process_catpage(callback: CallbackQuery) -> None:
    parts = callback.data.split("_")
    mode = parts[1] if len(parts) > 2 else "all"
    page = int(parts[2]) if len(parts) > 2 else int(parts[1])
    fav_ids = None
    if mode == "fav":
        fav_ids = await get_favorite_categories(callback.from_user.id)
    await callback.message.edit_reply_markup(
        reply_markup=get_categories_keyboard(page, mode=mode, fav_ids=fav_ids)
    )


@router.callback_query(F.data.startswith("cat_"), ParserState.waiting_for_category)
async def process_cat_selection(callback: CallbackQuery, state: FSMContext) -> None:
    cat_id = callback.data.split("_")[1]
    await state.update_data(parser_target=cat_id)
    await callback.message.edit_text(
        locale("ask_price_limits"),
        reply_markup=get_price_limit_keyboard(),
    )
    await state.set_state(ParserState.waiting_for_price_limit_choice)


@router.callback_query(F.data == "ptype_query", ParserState.waiting_for_name)
async def process_ptype_query(callback: CallbackQuery, state: FSMContext) -> None:
    await state.update_data(parser_type="query")
    await callback.message.edit_text(
        locale("enter_query"), reply_markup=get_cancel_keyboard()
    )
    await state.set_state(ParserState.waiting_for_query)


@router.message(ParserState.waiting_for_query)
async def process_parser_query(message: Message, state: FSMContext) -> None:
    user_query = message.text.strip()
    await state.update_data(parser_target=user_query)

    status_msg = await message.answer(locale("fs_live_optimizing"))
    optimized_queries = await generate_optimized_queries(user_query, max_queries=3)
    await state.update_data(parser_optimized_queries=optimized_queries)
    await status_msg.delete()

    await message.answer(
        locale("ask_price_limits"),
        reply_markup=get_price_limit_keyboard(),
    )
    await state.set_state(ParserState.waiting_for_price_limit_choice)


@router.callback_query(
    F.data == "pricelimit_no",
    ParserState.waiting_for_price_limit_choice,
)
async def skip_parser_price_limits(callback: CallbackQuery, state: FSMContext) -> None:
    await state.update_data(parser_min_price=None, parser_max_price=None)
    await callback.message.edit_text(
        locale("choose_frequency"),
        reply_markup=get_parser_frequency_keyboard(),
    )
    await state.set_state(
        ParserState.waiting_for_max_price,
    )  # Setting to max price state so frequency handles it


@router.callback_query(
    F.data == "pricelimit_yes",
    ParserState.waiting_for_price_limit_choice,
)
async def ask_parser_min_price(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.message.edit_text(
        locale("enter_min_price"), reply_markup=get_cancel_keyboard()
    )
    await state.set_state(ParserState.waiting_for_min_price)


@router.message(ParserState.waiting_for_min_price, ~F.text.startswith("/"))
async def process_parser_min_price(message: Message, state: FSMContext) -> None:
    try:
        min_price = int(message.text.strip())
        await state.update_data(parser_min_price=min_price if min_price > 0 else None)
    except ValueError:
        await message.answer(
            locale("invalid_price"), reply_markup=get_cancel_keyboard()
        )
        return

    await message.answer(locale("enter_max_price"), reply_markup=get_cancel_keyboard())
    await state.set_state(ParserState.waiting_for_max_price)


@router.message(ParserState.waiting_for_max_price, ~F.text.startswith("/"))
async def process_parser_max_price(message: Message, state: FSMContext) -> None:
    try:
        max_price = int(message.text.strip())
        await state.update_data(parser_max_price=max_price if max_price > 0 else None)
    except ValueError:
        await message.answer(
            locale("invalid_price"), reply_markup=get_cancel_keyboard()
        )
        return

    await message.answer(
        locale("choose_frequency"),
        reply_markup=get_parser_frequency_keyboard(),
    )


@router.callback_query(F.data.startswith("freq_"), ParserState.waiting_for_max_price)
async def process_frequency(callback: CallbackQuery, state: FSMContext) -> None:
    freq = int(callback.data.split("_")[1])
    await state.update_data(parser_freq=freq)
    await callback.message.edit_text(
        locale("enable_ai_filter"),
        reply_markup=get_ai_filter_keyboard(),
    )


@router.callback_query(
    F.data.startswith("aifilter_"),
    ParserState.waiting_for_max_price,
)
async def process_ai_filter(
    callback: CallbackQuery,
    state: FSMContext,
    bot: Bot,
) -> None:
    enable_ai = callback.data == "aifilter_yes"
    await state.update_data(parser_ai=enable_ai)

    if enable_ai:
        await callback.message.edit_text(
            locale("enter_ai_prompt"), reply_markup=get_cancel_keyboard()
        )
        await state.set_state(ParserState.waiting_for_ai_prompt)
    else:
        await state.update_data(parser_ai_prompt="")
        await finish_parser_creation(
            callback.message,
            state,
            callback.from_user.id,
            bot,
        )


@router.message(ParserState.waiting_for_ai_prompt)
async def process_ai_prompt(message: Message, state: FSMContext, bot: Bot) -> None:
    await state.update_data(parser_ai_prompt=message.text.strip())
    await finish_parser_creation(message, state, message.from_user.id, bot)


async def finish_parser_creation(
    message: Message,
    state: FSMContext,
    user_id: int,
    bot: Bot,
) -> None:
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
            "parser_optimized_queries",
            [data["parser_target"]],
        ),
        "freq": data["parser_freq"],
        "ai_filter": data["parser_ai"],
        "ai_prompt": data["parser_ai_prompt"],
        "min_price": data.get("parser_min_price"),
        "max_price": data.get("parser_max_price"),
        "active": True,
    }

    await add_parser(user_id, name, config)
    await add_parser_job(bot, user_id, name, config["freq"], config=config)

    await message.answer(locale("parser_created").format(name=name))
    await state.clear()


# Manage Existing
@router.callback_query(F.data == "parser_manage")
async def process_parser_manage(callback: CallbackQuery) -> None:
    parsers = await get_parsers(callback.from_user.id)
    if not parsers:
        await callback.message.edit_text(locale("no_parsers_found"))
        return
    await callback.message.edit_text(
        locale("manage_parsers_menu"),
        reply_markup=get_manage_parsers_keyboard(parsers),
    )


@router.callback_query(F.data.startswith("managep_"))
async def process_manage_specific_parser(callback: CallbackQuery) -> None:
    name = callback.data.split("_", 1)[1]
    parsers = await get_parsers(callback.from_user.id)
    if name not in parsers:
        await callback.answer("Parser not found")
        return

    config = parsers[name]
    status = "Active" if config["active"] else "Paused"
    text = locale("parser_info").format(
        name=name,
        status=status,
        type=config["type"],
        freq=config["freq"],
    )
    await callback.message.edit_text(
        text,
        reply_markup=get_parser_action_keyboard(name, config["active"]),
    )


@router.callback_query(F.data.startswith("pact_toggle_"))
async def process_parser_toggle(callback: CallbackQuery, bot: Bot) -> None:
    name = callback.data.split("_", 2)[2]
    parsers = await get_parsers(callback.from_user.id)
    if name not in parsers:
        return

    is_active = not parsers[name]["active"]
    await toggle_parser(callback.from_user.id, name, is_active)

    if is_active:
        await add_parser_job(
            bot,
            callback.from_user.id,
            name,
            parsers[name]["freq"],
            config=parsers[name],
        )
        await callback.answer(
            locale("parser_resumed", strip_html=True).format(name=name)
        )
    else:
        remove_parser_job(callback.from_user.id, name)
        await callback.answer(
            locale("parser_paused", strip_html=True).format(name=name)
        )

    config = parsers[name]
    config["active"] = is_active
    status = "Active" if is_active else "Paused"
    text = locale("parser_info").format(
        name=name,
        status=status,
        type=config["type"],
        freq=config["freq"],
    )
    await callback.message.edit_text(
        text,
        reply_markup=get_parser_action_keyboard(name, is_active),
    )


@router.callback_query(F.data.startswith("pact_delete_"))
async def process_parser_delete(callback: CallbackQuery) -> None:
    name = callback.data.split("_", 2)[2]
    await delete_parser(callback.from_user.id, name)
    remove_parser_job(callback.from_user.id, name)

    await callback.message.edit_text(locale("parser_deleted").format(name=name))


async def display_parser_edit_menu(
    event: Message | CallbackQuery,
    name: str,
    user_id: int,
) -> None:
    parsers = await get_parsers(user_id)
    if name not in parsers:
        return
    config = parsers[name]

    if config["type"] == "category":
        cat = get_category(config["target"])
        target_str = f"📂 {cat.name if cat else config['target']}"
    else:
        target_str = f"🔍 {config['target']}"

    ai_status = locale("yes_btn") if config["ai_filter"] else locale("no_btn")
    prompt_val = config.get("ai_prompt", "")
    prompt_str = prompt_val if len(prompt_val) <= 150 else prompt_val[:150] + "..."
    ai_info = (
        locale("ai_prompt_info").format(prompt=prompt_str)
        if config["ai_filter"] and prompt_val
        else ""
    )

    text = locale("edit_parser_menu").format(
        name=name,
        target=target_str,
        ai_status=ai_status,
        ai_info=ai_info,
    )
    keyboard = get_parser_edit_keyboard(name, config)

    if isinstance(event, CallbackQuery):
        await event.message.edit_text(text, reply_markup=keyboard)
    else:
        await event.answer(text, reply_markup=keyboard)


@router.callback_query(F.data.startswith("pact_edit_"))
async def process_parser_edit(callback: CallbackQuery) -> None:
    name = callback.data.split("_", 2)[2]
    await display_parser_edit_menu(callback, name, callback.from_user.id)


@router.callback_query(F.data.startswith("pedit_cancel_"))
async def process_pedit_cancel(callback: CallbackQuery, state: FSMContext) -> None:
    name = callback.data.split("_", 2)[2]
    await state.clear()
    await display_parser_edit_menu(callback, name, callback.from_user.id)


@router.callback_query(F.data.startswith("pedit_name_"))
async def process_pedit_name(callback: CallbackQuery, state: FSMContext) -> None:
    name = callback.data.split("_", 2)[2]
    await state.update_data(editing_parser_name=name)
    await callback.message.edit_text(
        locale("enter_new_name").format(name=name),
        reply_markup=get_parser_edit_cancel_keyboard(name),
    )
    await state.set_state(ParserEditState.waiting_for_name)


@router.message(ParserEditState.waiting_for_name, ~F.text.startswith("/"))
async def process_edit_name_input(
    message: Message, state: FSMContext, bot: Bot
) -> None:
    new_name = message.text.strip()
    data = await state.get_data()
    old_name = data.get("editing_parser_name")
    if not old_name:
        await state.clear()
        await message.answer(locale("session_expired"))
        return

    if len(new_name) > 40:
        await message.answer(
            locale("parser_name_too_long").format(max_length=40),
            reply_markup=get_parser_edit_cancel_keyboard(old_name),
        )
        return

    parsers = await get_parsers(message.from_user.id)
    if old_name not in parsers:
        await state.clear()
        return

    if new_name != old_name and new_name in parsers:
        await message.answer(
            locale("parser_already_exists"),
            reply_markup=get_parser_edit_cancel_keyboard(old_name),
        )
        return

    if new_name != old_name:
        config = parsers[old_name]
        await rename_parser(message.from_user.id, old_name, new_name)
        remove_parser_job(message.from_user.id, old_name)
        if config.get("active", True):
            await add_parser_job(
                bot, message.from_user.id, new_name, config["freq"], config=config
            )

    await state.clear()
    await message.answer(locale("parser_updated").format(name=new_name))
    await display_parser_edit_menu(message, new_name, message.from_user.id)


@router.callback_query(F.data.startswith("pedit_target_"))
async def process_pedit_target(callback: CallbackQuery, state: FSMContext) -> None:
    name = callback.data.split("_", 2)[2]
    parsers = await get_parsers(callback.from_user.id)
    if name not in parsers:
        await callback.answer("Parser not found")
        return

    config = parsers[name]
    await state.update_data(editing_parser_name=name)

    if config["type"] == "category":
        await callback.message.edit_text(
            locale("choose_category_source"),
            reply_markup=get_category_source_keyboard(),
        )
        await state.set_state(ParserEditState.waiting_for_category)
    else:
        await callback.message.edit_text(
            locale("enter_new_prompt").format(query=config["target"]),
            reply_markup=get_parser_edit_cancel_keyboard(name),
        )
        await state.set_state(ParserEditState.waiting_for_query)


@router.message(ParserEditState.waiting_for_query, ~F.text.startswith("/"))
async def process_edit_query_input(
    message: Message, state: FSMContext, bot: Bot
) -> None:
    new_query = message.text.strip()
    data = await state.get_data()
    name = data.get("editing_parser_name")
    if not name:
        await state.clear()
        await message.answer(locale("session_expired"))
        return

    parsers = await get_parsers(message.from_user.id)
    if name not in parsers:
        await state.clear()
        return

    status_msg = await message.answer(locale("fs_live_optimizing"))
    optimized_queries = await generate_optimized_queries(new_query, max_queries=3)
    await status_msg.delete()

    config = parsers[name]
    config["target"] = new_query
    config["optimized_queries"] = optimized_queries
    await add_parser(message.from_user.id, name, config)
    if config.get("active", True):
        await add_parser_job(
            bot, message.from_user.id, name, config["freq"], config=config
        )

    await state.clear()
    await message.answer(locale("parser_updated").format(name=name))
    await display_parser_edit_menu(message, name, message.from_user.id)


@router.callback_query(F.data.startswith("cat_"), ParserEditState.waiting_for_category)
async def process_edit_cat_selection(
    callback: CallbackQuery, state: FSMContext, bot: Bot
) -> None:
    cat_id = callback.data.split("_")[1]
    data = await state.get_data()
    name = data.get("editing_parser_name")
    if not name:
        await state.clear()
        await callback.message.edit_text(locale("session_expired"))
        return

    parsers = await get_parsers(callback.from_user.id)
    if name not in parsers:
        await state.clear()
        return

    config = parsers[name]
    config["target"] = cat_id
    await add_parser(callback.from_user.id, name, config)
    if config.get("active", True):
        await add_parser_job(
            bot, callback.from_user.id, name, config["freq"], config=config
        )

    await state.clear()
    await callback.answer(
        locale("parser_updated", strip_html=True).format(name=name), show_alert=True
    )
    await display_parser_edit_menu(callback, name, callback.from_user.id)


@router.callback_query(F.data.startswith("pedit_toggleai_"))
async def process_pedit_toggleai(
    callback: CallbackQuery, state: FSMContext, bot: Bot
) -> None:
    name = callback.data.split("_", 2)[2]
    parsers = await get_parsers(callback.from_user.id)
    if name not in parsers:
        await callback.answer("Parser not found")
        return

    config = parsers[name]
    current_ai = config.get("ai_filter", False)
    new_ai = not current_ai

    if new_ai:
        ai_prompt = config.get("ai_prompt", "").strip()
        if not ai_prompt:
            await state.update_data(editing_parser_name=name, enabling_ai=True)
            await callback.message.edit_text(
                locale("enter_ai_prompt"),
                reply_markup=get_parser_edit_cancel_keyboard(name),
            )
            await state.set_state(ParserEditState.waiting_for_ai_prompt)
            return

    config["ai_filter"] = new_ai
    await add_parser(callback.from_user.id, name, config)
    if config.get("active", True):
        await add_parser_job(
            bot, callback.from_user.id, name, config["freq"], config=config
        )

    status_str = locale("yes_btn") if new_ai else locale("no_btn")
    await callback.answer(f"AI Filter: {status_str}")
    await display_parser_edit_menu(callback, name, callback.from_user.id)


@router.callback_query(F.data.startswith("pedit_aiprompt_"))
async def process_pedit_aiprompt(callback: CallbackQuery, state: FSMContext) -> None:
    name = callback.data.split("_", 2)[2]
    parsers = await get_parsers(callback.from_user.id)
    if name not in parsers:
        await callback.answer("Parser not found")
        return

    config = parsers[name]
    await state.update_data(editing_parser_name=name, enabling_ai=False)
    prompt_val = config.get("ai_prompt", "")
    prompt_str = prompt_val if len(prompt_val) <= 3000 else prompt_val[:3000] + "..."
    await callback.message.edit_text(
        locale("enter_new_ai_prompt").format(prompt=prompt_str),
        reply_markup=get_parser_edit_cancel_keyboard(name),
    )
    await state.set_state(ParserEditState.waiting_for_ai_prompt)


@router.message(ParserEditState.waiting_for_ai_prompt, ~F.text.startswith("/"))
async def process_edit_aiprompt_input(
    message: Message, state: FSMContext, bot: Bot
) -> None:
    new_ai_prompt = message.text.strip()
    data = await state.get_data()
    name = data.get("editing_parser_name")
    enabling_ai = data.get("enabling_ai", False)
    if not name:
        await state.clear()
        await message.answer(locale("session_expired"))
        return

    parsers = await get_parsers(message.from_user.id)
    if name not in parsers:
        await state.clear()
        return

    config = parsers[name]
    config["ai_prompt"] = new_ai_prompt
    if enabling_ai:
        config["ai_filter"] = True

    await add_parser(message.from_user.id, name, config)
    if config.get("active", True):
        await add_parser_job(
            bot, message.from_user.id, name, config["freq"], config=config
        )

    await state.clear()
    await message.answer(locale("parser_updated").format(name=name))
    await display_parser_edit_menu(message, name, message.from_user.id)
