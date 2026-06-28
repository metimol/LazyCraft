from aiogram.filters import BaseFilter
from aiogram.types import Message
from const import locale


class TextLoc(BaseFilter):
    def __init__(self, key: str):
        self.key = key

    async def __call__(self, message: Message) -> bool:
        if not message.text:
            return False
        return message.text == locale(self.key)
