from aiogram.types import Message
from ai import ask_agent
from ai.context import current_message


async def text_processing(message: Message) -> None:
    current_message.set(message)
    response = await ask_agent(message.text)

    await message.answer(response)