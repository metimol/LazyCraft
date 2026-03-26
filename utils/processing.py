from aiogram.types import Message
from ai import ask_agent


async def text_processing(message: Message) -> None:
    response = await ask_agent(message.text)

    await message.answer(response)