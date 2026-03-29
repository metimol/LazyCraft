import asyncio
import logging
import sys

from aiogram import Dispatcher, Bot, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command
from aiogram.types import Message

from const import BOT_TOKEN, phrases, ALLOWED_USERS
from utils.processing import text_processing

dp = Dispatcher()

@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    await message.answer(phrases.get_value("welcome_message"))

@dp.message(Command("help"))
async def command_help_handler(message: Message) -> None:
    await message.answer(phrases.get_value("help_message"))

@dp.message(F.text.startswith('/'))
async def not_supported_command(message: Message) -> None:
    await message.answer(phrases.get_value("not_supported_command"))

@dp.message(F.text)
async def text_handler(message: Message) -> None:
    if message.from_user.id in ALLOWED_USERS:
        await text_processing(message)
    else:
        await message.answer(phrases.get_value("UNAUTHORIZED_USER"))

@dp.message(~F.text)
async def not_supported_format(message: Message) -> None:
    await message.answer(phrases.get_value("not_supported_format"))

async def main() -> None:
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())