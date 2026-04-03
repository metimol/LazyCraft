from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from utils.keyboards import get_settings_keyboard, get_timer_keyboard, get_radius_keyboard
from utils.redis_database import set_user_prompt, set_user_radius, set_user_timer
from utils.scheduler_jobs import update_user_job
from const import phrases

router = Router()

class PromptState(StatesGroup):
    waiting_for_prompt = State()

@router.message(F.text == "⚙️ Настройки")
@router.message(Command("settings"))
async def settings_cmd(message: Message):
    await message.answer(phrases.get_value("settings_menu"), reply_markup=get_settings_keyboard())

@router.callback_query(F.data == "set_prompt")
async def process_set_prompt(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(phrases.get_value("enter_prompt"))
    await state.set_state(PromptState.waiting_for_prompt)

@router.message(PromptState.waiting_for_prompt)
async def save_prompt(message: Message, state: FSMContext):
    await set_user_prompt(message.from_user.id, message.text)
    await message.answer(phrases.get_value("prompt_saved"))
    await state.clear()

@router.callback_query(F.data == "set_timer")
async def process_set_timer(callback: CallbackQuery):
    await callback.message.edit_text(phrases.get_value("choose_timer"), reply_markup=get_timer_keyboard())

@router.callback_query(F.data.startswith("timer_"))
async def save_timer(callback: CallbackQuery, bot: Bot):
    hours = int(callback.data.split("_")[1])
    await set_user_timer(callback.from_user.id, hours)
    update_user_job(bot, callback.from_user.id, hours)
    await callback.message.edit_text(phrases.get_value("timer_saved").format(hours=hours))

@router.callback_query(F.data == "set_radius")
async def process_set_radius(callback: CallbackQuery):
    await callback.message.edit_text(phrases.get_value("choose_radius"), reply_markup=get_radius_keyboard())

@router.callback_query(F.data.startswith("radius_"))
async def save_radius(callback: CallbackQuery):
    radius = int(callback.data.split("_")[1])
    await set_user_radius(callback.from_user.id, radius)
    await callback.message.edit_text(phrases.get_value("radius_saved").format(radius=radius))