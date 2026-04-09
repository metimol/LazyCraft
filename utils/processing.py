from aiogram.types import Message
from ai import ask_agent
from ai.context import current_message
from utils.split_message import split_message


async def text_processing(message: Message) -> None:
    current_message.set(message)
    response = await ask_agent(message.text)

    async for chunk in split_message(response):
        await message.answer(chunk)
