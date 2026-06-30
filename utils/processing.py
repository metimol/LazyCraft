from aiogram.types import Message

from const import locale
from utils.split_message import split_message


async def text_processing(message: Message) -> None:
    response = locale("text_messages_not_supported")

    async for chunk in split_message(response):
        await message.answer(chunk)
