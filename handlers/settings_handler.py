from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import re

from utils.keyboards import (
    get_settings_keyboard,
    get_timer_keyboard,
    get_radius_keyboard,
    get_language_keyboard,
)
from database.users import (
    set_user_prompt,
    set_user_radius,
    set_user_timer,
    set_user_language,
    set_user_zip,
)
from utils.scheduler_jobs import update_user_job
from utils.geocoding import get_lat_lon
from const import locale, user_lang

router = Router()


class SettingsState(StatesGroup):
    waiting_for_prompt = State()
    waiting_for_zip = State()


@router.message(F.text == locale("settings_btn"))
@router.message(Command("settings"))
async def settings_cmd(message: Message):
    await message.answer(locale("settings_menu"), reply_markup=get_settings_keyboard())


@router.callback_query(F.data == "set_language")
async def process_set_language(callback: CallbackQuery):
    await callback.message.edit_text(
        locale("choose_language"), reply_markup=get_language_keyboard()
    )


@router.callback_query(F.data.startswith("lang_"))
async def save_language(callback: CallbackQuery):
    lang = callback.data.split("_")[1]
    await set_user_language(callback.from_user.id, lang)
    user_lang.set(lang)
    await callback.message.edit_text(locale("language_saved"))


@router.callback_query(F.data == "set_prompt")
async def process_set_prompt(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(locale("enter_prompt"))
    await state.set_state(SettingsState.waiting_for_prompt)


@router.message(SettingsState.waiting_for_prompt)
async def save_prompt(message: Message, state: FSMContext):
    await set_user_prompt(message.from_user.id, message.text)
    await message.answer(locale("prompt_saved"))
    await state.clear()


@router.callback_query(F.data == "set_timer")
async def process_set_timer(callback: CallbackQuery):
    await callback.message.edit_text(
        locale("choose_timer"), reply_markup=get_timer_keyboard()
    )


@router.callback_query(F.data.startswith("timer_"))
async def save_timer(callback: CallbackQuery, bot: Bot):
    hours = int(callback.data.split("_")[1])
    await set_user_timer(callback.from_user.id, hours)
    update_user_job(bot, callback.from_user.id, hours)
    await callback.message.edit_text(locale("timer_saved").format(hours=hours))


@router.callback_query(F.data == "set_location")
async def process_set_location(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(locale("enter_zip"))
    await state.set_state(SettingsState.waiting_for_zip)


@router.message(SettingsState.waiting_for_zip)
async def process_zip_code(message: Message, state: FSMContext):
    zip_code = message.text.strip()
    if not re.match(r"^\d{5}$", zip_code):
        await message.answer(locale("invalid_zip"))
        return

    status_msg = await message.answer("Validating zip code...")
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
async def save_radius(callback: CallbackQuery):
    radius = int(callback.data.split("_")[1])
    await set_user_radius(callback.from_user.id, radius)
    await callback.message.edit_text(locale("radius_saved").format(radius=radius))
