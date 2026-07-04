import re

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from const import locale, user_lang
from database.users import (
    add_favorite_category,
    get_favorite_categories,
    remove_favorite_category,
    set_user_language,
    set_user_radius,
    set_user_zip,
)
from kleinanzeigen_api.categories import get_category
from utils.filters import TextLoc
from utils.geocoding import get_lat_lon
from utils.keyboards import (
    get_cancel_keyboard,
    get_fav_settings_keyboard,
    get_language_keyboard,
    get_main_keyboard,
    get_radius_keyboard,
    get_settings_keyboard,
)

router = Router()


class SettingsState(StatesGroup):
    waiting_for_prompt = State()
    waiting_for_zip = State()


@router.message(TextLoc("settings_btn"))
@router.message(Command("settings"))
async def settings_cmd(message: Message) -> None:
    await message.answer(locale("settings_menu"), reply_markup=get_settings_keyboard())


@router.callback_query(F.data == "settings_main")
async def process_settings_main(callback: CallbackQuery) -> None:
    await callback.message.edit_text(
        locale("settings_menu"), reply_markup=get_settings_keyboard()
    )


@router.callback_query(F.data == "set_fav_categories")
async def process_set_fav_categories(callback: CallbackQuery) -> None:
    fav_ids = await get_favorite_categories(callback.from_user.id)
    await callback.message.edit_text(
        locale("fav_categories_menu"),
        reply_markup=get_fav_settings_keyboard(fav_ids, page=0),
    )


@router.callback_query(F.data.startswith("favcat_"))
async def process_toggle_fav_cat(callback: CallbackQuery) -> None:
    parts = callback.data.split("_")
    cat_id = parts[1]
    page = int(parts[2]) if len(parts) > 2 else 0

    fav_ids = await get_favorite_categories(callback.from_user.id)
    cat = get_category(cat_id)
    name = cat.name if cat else cat_id

    if cat_id in fav_ids:
        await remove_favorite_category(callback.from_user.id, cat_id)
        fav_ids.discard(cat_id)
        await callback.answer(locale("fav_removed", strip_html=True).format(name=name))
    else:
        await add_favorite_category(callback.from_user.id, cat_id)
        fav_ids.add(cat_id)
        await callback.answer(locale("fav_added", strip_html=True).format(name=name))

    await callback.message.edit_reply_markup(
        reply_markup=get_fav_settings_keyboard(fav_ids, page=page)
    )


@router.callback_query(F.data.startswith("favpage_"))
async def process_favpage(callback: CallbackQuery) -> None:
    page = int(callback.data.split("_")[1])
    fav_ids = await get_favorite_categories(callback.from_user.id)
    await callback.message.edit_reply_markup(
        reply_markup=get_fav_settings_keyboard(fav_ids, page=page)
    )


@router.callback_query(F.data == "set_language")
async def process_set_language(callback: CallbackQuery) -> None:
    await callback.message.edit_text(
        locale("choose_language"),
        reply_markup=get_language_keyboard(),
    )


@router.callback_query(F.data.startswith("lang_"))
async def save_language(callback: CallbackQuery) -> None:
    lang = callback.data.split("_")[1]
    await set_user_language(callback.from_user.id, lang)
    user_lang.set(lang)
    await callback.message.delete()
    await callback.message.answer(
        locale("language_saved"),
        reply_markup=get_main_keyboard(),
    )


@router.callback_query(F.data == "set_location")
async def process_set_location(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.message.edit_text(
        locale("enter_zip"),
        reply_markup=get_cancel_keyboard(),
    )
    await state.set_state(SettingsState.waiting_for_zip)


@router.callback_query(F.data == "cancel_action")
async def cancel_action(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.edit_text(locale("action_cancelled"))


@router.message(SettingsState.waiting_for_zip)
async def process_zip_code(message: Message, state: FSMContext) -> None:
    zip_code = message.text.strip()
    if not re.match(r"^\d{5}$", zip_code):
        await message.answer(locale("invalid_zip"))
        return

    status_msg = await message.answer(locale("validating_zip"))
    coords = await get_lat_lon(zip_code)
    await status_msg.delete()

    if not coords:
        await message.answer(locale("invalid_zip"))
        return

    await set_user_zip(message.from_user.id, zip_code)
    await message.answer(
        locale("zip_saved").format(zip_code=zip_code)
        + "\n\n"
        + locale("choose_radius"),
        reply_markup=get_radius_keyboard(),
    )
    await state.clear()


@router.callback_query(F.data.startswith("radius_"))
async def save_radius(callback: CallbackQuery) -> None:
    radius = int(callback.data.split("_")[1])
    await set_user_radius(callback.from_user.id, radius)
    await callback.message.edit_text(locale("radius_saved").format(radius=radius))
