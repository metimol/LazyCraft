from __future__ import annotations

import asyncio
import contextlib
import logging
import os
import sys
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from aiogram.fsm.context import FSMContext
    from aiogram.types import CallbackQuery, ErrorEvent, Message, TelegramObject

from aiogram import BaseMiddleware, Bot, Dispatcher, F, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.fsm.state import any_state
from aiogram.fsm.storage.redis import RedisStorage

from const import ADMIN_ID, BOT_TOKEN, locale
from database.client import close_redis, init_redis
from database.parsers import get_all_users_with_parsers, get_parsers
from handlers.fast_search_handler import router as fast_search_router
from handlers.help_handler import router as help_router
from handlers.parser_handler import router as parser_router
from handlers.settings_handler import router as settings_router
from kleinanzeigen_api import KleinanzeigenAPI
from utils.keyboards import get_main_keyboard
from utils.middlewares import CleanPreviousPromptMiddleware, LocaleMiddleware
from utils.processing import text_processing
from utils.scheduler_jobs import add_parser_job, scheduler


class AdminMiddleware(BaseMiddleware):
    def __init__(self, admin_id: int) -> None:
        self.admin_id = admin_id

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        user = data.get("event_from_user")
        if user and user.id != self.admin_id:
            return None
        return await handler(event, data)


redis_host = os.getenv("REDIS_HOST", "localhost")
redis_port = os.getenv("REDIS_PORT", "6379")
redis_url = f"redis://{redis_host}:{redis_port}/0"
dp = Dispatcher(storage=RedisStorage.from_url(redis_url))
if ADMIN_ID:
    dp.update.outer_middleware(AdminMiddleware(admin_id=ADMIN_ID))
dp.update.outer_middleware(LocaleMiddleware())
dp.message.outer_middleware(CleanPreviousPromptMiddleware())

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
logger = logging.getLogger(__name__)


@dp.errors()
async def global_error_handler(event: ErrorEvent) -> None:
    logger.exception(
        "Unhandled exception caused by update %s:",
        event.update.update_id,
        exc_info=event.exception,
    )
    error_text = locale("ai_error")
    with contextlib.suppress(Exception):
        if event.update.message:
            await event.update.message.answer(error_text)
        elif event.update.callback_query and event.update.callback_query.message:
            await event.update.callback_query.answer(error_text, show_alert=True)


default_router = Router()


@default_router.message(CommandStart(), any_state)
async def command_start_handler(message: Message, state: FSMContext) -> None:
    await state.clear()
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


@default_router.callback_query()
async def unhandled_callback_query(callback: CallbackQuery) -> None:
    with contextlib.suppress(Exception):
        await callback.answer(
            locale("action_cancelled", strip_html=True), show_alert=True
        )
        await callback.message.edit_reply_markup(reply_markup=None)


dp.include_router(settings_router)
dp.include_router(parser_router)
dp.include_router(fast_search_router)
dp.include_router(help_router)
dp.include_router(default_router)


async def restore_jobs() -> None:
    # Restore parser jobs
    users = await get_all_users_with_parsers()
    for user_id in users:
        parsers = await get_parsers(user_id)
        for name, config in parsers.items():
            if config.get("active"):
                await add_parser_job(bot, user_id, name, config["freq"], config=config)


async def update_categories_list() -> None:
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
