import asyncio
import logging
import sys

from aiogram import Dispatcher, Bot, F, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import Message

from const import BOT_TOKEN, locale, ADMIN_ID
from kleinanzeigen_api import KleinanzeigenAPI
from utils.processing import text_processing
from utils.scheduler_jobs import scheduler, add_parser_job
from utils.keyboards import get_main_keyboard
from database.parsers import get_all_users_with_parsers, get_parsers
from database.client import init_redis, close_redis
from utils.middlewares import LocaleMiddleware

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from typing import Callable, Dict, Any, Awaitable

from handlers.settings_handler import router as settings_router
from handlers.parser_handler import router as parser_router
from handlers.fast_search_handler import router as fast_search_router
from handlers.help_handler import router as help_router


class AdminMiddleware(BaseMiddleware):
    def __init__(self, admin_id: int):
        self.admin_id = admin_id

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        user = data.get("event_from_user")
        if user and user.id != self.admin_id:
            return
        return await handler(event, data)


dp = Dispatcher()
if ADMIN_ID:
    dp.update.outer_middleware(AdminMiddleware(admin_id=ADMIN_ID))
dp.update.outer_middleware(LocaleMiddleware())

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

default_router = Router()


@default_router.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    await message.answer(locale("welcome_message"), reply_markup=get_main_keyboard())


@default_router.message(F.text.startswith("/"))
async def not_supported_command(message: Message) -> None:
    await message.answer(locale("not_supported_command"))


@default_router.message(F.text)
async def text_handler(message: Message) -> None:
    await text_processing(message)


@default_router.message(~F.text)
async def not_supported_format(message: Message) -> None:
    await message.answer(locale("not_supported_format"))


dp.include_router(settings_router)
dp.include_router(parser_router)
dp.include_router(fast_search_router)
dp.include_router(help_router)
dp.include_router(default_router)


async def restore_jobs():
    # Restore parser jobs
    users = await get_all_users_with_parsers()
    for user_id in users:
        parsers = await get_parsers(user_id)
        for name, config in parsers.items():
            if config.get("active"):
                add_parser_job(bot, user_id, name, config["freq"])


async def update_categories_list():
    async with KleinanzeigenAPI() as api:
        await api.update_categories()


async def main() -> None:
    await init_redis()
    try:
        await update_categories_list()
        scheduler.start()
        await restore_jobs()
        await dp.start_polling(bot)
    finally:
        await close_redis()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
