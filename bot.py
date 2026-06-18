import asyncio
import logging
import sys

from aiogram import Dispatcher, Bot, F, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import Message

from const import BOT_TOKEN, locale
from kleinanzeigen_api import KleinanzeigenAPI
from utils.processing import text_processing
from utils.scheduler_jobs import scheduler, add_parser_job
from utils.keyboards import get_main_keyboard
from database.parsers import get_all_users_with_parsers, get_parsers

from handlers.settings_handler import router as settings_router
from handlers.free_search_handler import router as free_router
from handlers.parser_handler import router as parser_router
from handlers.fast_search_handler import router as fast_search_router
from handlers.help_handler import router as help_router

dp = Dispatcher()
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
dp.include_router(free_router)
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
    await update_categories_list()
    scheduler.start()
    await restore_jobs()
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
