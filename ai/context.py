from contextvars import ContextVar
from aiogram.types import Message

current_message: ContextVar[Message] = ContextVar('current_message')