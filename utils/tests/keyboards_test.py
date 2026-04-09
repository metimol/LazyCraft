from aiogram.types import ReplyKeyboardMarkup, InlineKeyboardMarkup

from utils.keyboards import (
    get_main_keyboard,
    get_settings_keyboard,
    get_timer_keyboard,
    get_radius_keyboard
)

def test_get_main_keyboard():
    keyboard = get_main_keyboard()

    assert isinstance(keyboard, ReplyKeyboardMarkup)
    assert keyboard.resize_keyboard is True
    assert len(keyboard.keyboard) == 1
    assert len(keyboard.keyboard[0]) == 2
    assert keyboard.keyboard[0][0].text == "🏴‍☠️ Чекнуть халяву"
    assert keyboard.keyboard[0][1].text == "⚙️ Настройки"

def test_get_settings_keyboard():
    keyboard = get_settings_keyboard()

    assert isinstance(keyboard, InlineKeyboardMarkup)
    assert len(keyboard.inline_keyboard) == 3
    assert keyboard.inline_keyboard[0][0].text == "⏱ Настроить таймер"
    assert keyboard.inline_keyboard[0][0].callback_data == "set_timer"
    assert keyboard.inline_keyboard[2][0].text == "📝 Задать интересы"
    assert keyboard.inline_keyboard[2][0].callback_data == "set_prompt"

def test_get_timer_keyboard():
    keyboard = get_timer_keyboard()

    assert isinstance(keyboard, InlineKeyboardMarkup)
    assert len(keyboard.inline_keyboard) == 3
    assert len(keyboard.inline_keyboard[0]) == 2
    assert len(keyboard.inline_keyboard[2]) == 2
    assert keyboard.inline_keyboard[0][0].text == "1 час"
    assert keyboard.inline_keyboard[0][0].callback_data == "timer_1"
    assert keyboard.inline_keyboard[2][1].text == "Выключить"
    assert keyboard.inline_keyboard[2][1].callback_data == "timer_0"

def test_get_radius_keyboard():
    keyboard = get_radius_keyboard()

    assert isinstance(keyboard, InlineKeyboardMarkup)
    assert len(keyboard.inline_keyboard) == 3
    assert len(keyboard.inline_keyboard[0]) == 2
    assert keyboard.inline_keyboard[0][1].text == "10 км"
    assert keyboard.inline_keyboard[0][1].callback_data == "radius_10"
    assert keyboard.inline_keyboard[2][1].text == "100 км"
    assert keyboard.inline_keyboard[2][1].callback_data == "radius_100"