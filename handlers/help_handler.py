from aiogram import Router
from aiogram.filters import Command
from aiogram.types import (
    Message,
)

from const import locale
from utils.filters import TextLoc

router = Router()


@router.message(TextLoc("help_btn"))
@router.message(Command("help"))
async def help_cmd(message: Message):
    await message.answer(locale("help_message"))
