from __future__ import annotations

import contextlib
from typing import TYPE_CHECKING, Any

from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from aiogram.fsm.context import FSMContext

from const import user_lang
from database.users import get_user_language


class LocaleMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        user = data.get("event_from_user")
        if user:
            lang = await get_user_language(user.id)
            user_lang.set(lang)
        return await handler(event, data)


class CleanPreviousPromptMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        state: FSMContext | None = data.get("state")
        if state and isinstance(event, Message):
            current_state = await state.get_state()
            if current_state is not None:
                bot = data.get("bot") or getattr(event, "bot", None)
                chat = data.get("event_chat")
                if bot and chat and hasattr(event, "message_id"):
                    with contextlib.suppress(Exception):
                        for i in range(1, 4):
                            await bot.edit_message_reply_markup(
                                chat_id=chat.id,
                                message_id=event.message_id - i,
                                reply_markup=None,
                            )
        return await handler(event, data)
