from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)

from const import locale
from kleinanzeigen_api.categories import all_categories


def get_main_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=locale("fast_search_btn")),
                KeyboardButton(text=locale("auto_parser_btn")),
            ],
            [
                KeyboardButton(text=locale("help_btn")),
                KeyboardButton(text=locale("settings_btn")),
            ],
        ],
        resize_keyboard=True,
    )


def get_settings_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=locale("set_location_btn"),
                    callback_data="set_location",
                ),
            ],
            [
                InlineKeyboardButton(
                    text=locale("set_language_btn"),
                    callback_data="set_language",
                ),
            ],
        ],
    )


def get_language_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="English", callback_data="lang_en"),
                InlineKeyboardButton(text="Deutsch", callback_data="lang_de"),
            ],
            [
                InlineKeyboardButton(text="Русский", callback_data="lang_ru"),
                InlineKeyboardButton(text="Türkçe", callback_data="lang_tur"),
            ],
            [
                InlineKeyboardButton(text="Українська", callback_data="lang_ukr"),
            ],
        ],
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
        ],
    )


def get_cancel_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=locale("cancel_btn"), callback_data="cancel_action"
                ),
            ],
        ],
    )


def get_parser_menu_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=locale("add_new_btn"),
                    callback_data="parser_add",
                ),
            ],
            [
                InlineKeyboardButton(
                    text=locale("manage_existing_btn"),
                    callback_data="parser_manage",
                ),
            ],
        ],
    )


def get_parser_type_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=locale("search_by_category_btn"),
                    callback_data="ptype_category",
                ),
            ],
            [
                InlineKeyboardButton(
                    text=locale("search_by_query_btn"),
                    callback_data="ptype_query",
                ),
            ],
            [
                InlineKeyboardButton(
                    text=locale("cancel_btn"), callback_data="cancel_action"
                ),
            ],
        ],
    )


def get_parser_frequency_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                # TODO: Change to 5 min after testing
                InlineKeyboardButton(text="1m", callback_data="freq_1"),
                InlineKeyboardButton(text="10m", callback_data="freq_10"),
                InlineKeyboardButton(text="15m", callback_data="freq_15"),
            ],
            [
                InlineKeyboardButton(text="30m", callback_data="freq_30"),
                InlineKeyboardButton(text="1h", callback_data="freq_60"),
                InlineKeyboardButton(text="1h 30m", callback_data="freq_90"),
            ],
            [
                InlineKeyboardButton(text="2h", callback_data="freq_120"),
                InlineKeyboardButton(text="4h", callback_data="freq_240"),
                InlineKeyboardButton(text="6h", callback_data="freq_360"),
            ],
            [
                InlineKeyboardButton(text="12h", callback_data="freq_720"),
                InlineKeyboardButton(text="24h", callback_data="freq_1440"),
            ],
            [
                InlineKeyboardButton(
                    text=locale("cancel_btn"), callback_data="cancel_action"
                ),
            ],
        ],
    )


def get_ai_filter_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=locale("yes_btn"),
                    callback_data="aifilter_yes",
                ),
            ],
            [InlineKeyboardButton(text=locale("no_btn"), callback_data="aifilter_no")],
            [
                InlineKeyboardButton(
                    text=locale("cancel_btn"), callback_data="cancel_action"
                )
            ],
        ],
    )


def get_categories_keyboard(page: int = 0):
    cats = all_categories()

    items_per_page = 10
    total_pages = (len(cats) + items_per_page - 1) // items_per_page
    page = max(0, min(page, total_pages - 1))

    start = page * items_per_page
    end = start + items_per_page
    page_cats = cats[start:end]

    kb = [
        [InlineKeyboardButton(text=c.name, callback_data=f"cat_{c.id}")]
        for c in page_cats
    ]

    nav_buttons = []
    if page > 0:
        nav_buttons.append(
            InlineKeyboardButton(
                text=locale("prev_page_btn"),
                callback_data=f"catpage_{page - 1}",
            ),
        )
    if page < total_pages - 1:
        nav_buttons.append(
            InlineKeyboardButton(
                text=locale("next_page_btn"),
                callback_data=f"catpage_{page + 1}",
            ),
        )

    if nav_buttons:
        kb.append(nav_buttons)

    kb.append(
        [InlineKeyboardButton(text=locale("cancel_btn"), callback_data="cancel_action")]
    )

    return InlineKeyboardMarkup(inline_keyboard=kb)


def get_manage_parsers_keyboard(parsers: dict):
    kb = [
        [InlineKeyboardButton(text=name, callback_data=f"managep_{name}")]
        for name in parsers
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)


def get_parser_action_keyboard(name: str, is_active: bool):  # noqa: FBT001
    toggle_text = locale("pause_btn") if is_active else locale("resume_btn")
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=toggle_text,
                    callback_data=f"pact_toggle_{name}",
                ),
            ],
            [
                InlineKeyboardButton(
                    text=locale("delete_btn"),
                    callback_data=f"pact_delete_{name}",
                ),
            ],
        ],
    )


def get_fs_category_prompt_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=locale("yes_btn"), callback_data="fs_cat_yes")],
            [InlineKeyboardButton(text=locale("no_btn"), callback_data="fs_cat_no")],
            [
                InlineKeyboardButton(
                    text=locale("cancel_btn"), callback_data="cancel_action"
                )
            ],
        ],
    )


def get_price_limit_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=locale("yes_btn"),
                    callback_data="pricelimit_yes",
                ),
            ],
            [
                InlineKeyboardButton(
                    text=locale("no_btn"),
                    callback_data="pricelimit_no",
                ),
            ],
            [
                InlineKeyboardButton(
                    text=locale("cancel_btn"), callback_data="cancel_action"
                ),
            ],
        ],
    )
