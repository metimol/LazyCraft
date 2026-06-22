from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import (
    Message,
)

from const import locale

router = Router()


@router.message(F.text == locale("help_btn"))
@router.message(Command("help"))
async def help_cmd(message: Message):
    await message.answer(locale("help_message"))
