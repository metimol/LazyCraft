from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

from const import locale

router = Router()


def get_help_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🤝 Get Referral Link", callback_data="get_referral_link"
                )
            ]
        ]
    )


@router.message(F.text == locale("help_btn"))
@router.message(Command("help"))
async def help_cmd(message: Message):
    await message.answer(locale("help_message"), reply_markup=get_help_keyboard())


@router.callback_query(F.data == "get_referral_link")
async def process_get_referral_link(callback: CallbackQuery):
    bot_info = await callback.bot.me()
    ref_link = f"https://t.me/{bot_info.username}?start=ref_{callback.from_user.id}"
    await callback.message.answer(
        locale("referral_explanation").format(ref_link=ref_link),
        disable_web_page_preview=True,
    )
    await callback.answer()
