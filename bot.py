import asyncio
import logging
import sys

from aiogram import Dispatcher, Bot, F, BaseMiddleware, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command
from aiogram.types import Message

from const import BOT_TOKEN, phrases, ALLOWED_USERS
from utils.processing import text_processing
from utils.scheduler_jobs import scheduler, update_user_job
from utils.redis_database import get_user_timer
from utils.keyboards import get_main_keyboard

from handlers.settings_handler import router as settings_router
from handlers.free_search_handler import router as free_router

dp = Dispatcher()
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))


class AuthMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        if event.from_user.id not in ALLOWED_USERS:
            if isinstance(event, Message):
                await event.answer(phrases.get_value("UNAUTHORIZED_USER"))
            return
        return await handler(event, data)


dp.message.middleware(AuthMiddleware())
dp.callback_query.middleware(AuthMiddleware())

default_router = Router()


@default_router.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    await message.answer(
        phrases.get_value("welcome_message"), reply_markup=get_main_keyboard()
    )


@default_router.message(Command("help"))
async def command_help_handler(message: Message) -> None:
    await message.answer(phrases.get_value("help_message"))


@default_router.message(F.text.startswith("/"))
async def not_supported_command(message: Message) -> None:
    await message.answer(phrases.get_value("not_supported_command"))


@default_router.message(F.text)
async def text_handler(message: Message) -> None:
    await text_processing(message)


@default_router.message(~F.text)
async def not_supported_format(message: Message) -> None:
    await message.answer(phrases.get_value("not_supported_format"))


dp.include_router(settings_router)
dp.include_router(free_router)
dp.include_router(default_router)


async def restore_jobs():
    for user_id in ALLOWED_USERS:
        hours = await get_user_timer(user_id)
        if hours > 0:
            update_user_job(bot, user_id, hours)


async def main() -> None:
    scheduler.start()
    await restore_jobs()
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
