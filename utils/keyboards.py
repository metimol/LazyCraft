from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)


def get_main_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="🏴‍☠️ Чекнуть халяву"),
                KeyboardButton(text="⚙️ Настройки"),
            ]
        ],
        resize_keyboard=True,
    )


def get_settings_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="⏱ Настроить таймер", callback_data="set_timer"
                )
            ],
            [
                InlineKeyboardButton(
                    text="📍 Изменить радиус", callback_data="set_radius"
                )
            ],
            [
                InlineKeyboardButton(
                    text="📝 Задать интересы", callback_data="set_prompt"
                )
            ],
        ]
    )


def get_timer_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="1 час", callback_data="timer_1"),
                InlineKeyboardButton(text="3 часа", callback_data="timer_3"),
            ],
            [
                InlineKeyboardButton(text="6 часов", callback_data="timer_6"),
                InlineKeyboardButton(text="12 часов", callback_data="timer_12"),
            ],
            [
                InlineKeyboardButton(text="24 часа", callback_data="timer_24"),
                InlineKeyboardButton(text="Выключить", callback_data="timer_0"),
            ],
        ]
    )


def get_radius_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="5 км", callback_data="radius_5"),
                InlineKeyboardButton(text="10 км", callback_data="radius_10"),
            ],
            [
                InlineKeyboardButton(text="20 км", callback_data="radius_20"),
                InlineKeyboardButton(text="30 км", callback_data="radius_30"),
            ],
            [
                InlineKeyboardButton(text="50 км", callback_data="radius_50"),
                InlineKeyboardButton(text="100 км", callback_data="radius_100"),
            ],
        ]
    )
