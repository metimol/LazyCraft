from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)


from const import locale


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


def get_parser_menu_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=locale("add_new_btn"), callback_data="parser_add"
                )
            ],
            [
                InlineKeyboardButton(
                    text=locale("manage_existing_btn"), callback_data="parser_manage"
                )
            ],
        ]
    )


def get_parser_type_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=locale("search_by_category_btn"),
                    callback_data="ptype_category",
                )
            ],
            [
                InlineKeyboardButton(
                    text=locale("search_by_query_btn"), callback_data="ptype_query"
                )
            ],
        ]
    )


def get_parser_frequency_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="5m", callback_data="freq_5"),
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
        ]
    )


def get_ai_filter_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=locale("yes_btn"), callback_data="aifilter_yes"
                )
            ],
            [InlineKeyboardButton(text=locale("no_btn"), callback_data="aifilter_no")],
        ]
    )


def get_categories_keyboard(page: int = 0):
    from kleinanzeigen_api.categories import all_categories

    cats = all_categories()

    ITEMS_PER_PAGE = 10
    total_pages = (len(cats) + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE
    page = max(0, min(page, total_pages - 1))

    start = page * ITEMS_PER_PAGE
    end = start + ITEMS_PER_PAGE
    page_cats = cats[start:end]

    kb = []
    for c in page_cats:
        kb.append([InlineKeyboardButton(text=c.name, callback_data=f"cat_{c.id}")])

    nav_buttons = []
    if page > 0:
        nav_buttons.append(
            InlineKeyboardButton(
                text=locale("prev_page_btn"), callback_data=f"catpage_{page - 1}"
            )
        )
    if page < total_pages - 1:
        nav_buttons.append(
            InlineKeyboardButton(
                text=locale("next_page_btn"), callback_data=f"catpage_{page + 1}"
            )
        )

    if nav_buttons:
        kb.append(nav_buttons)

    return InlineKeyboardMarkup(inline_keyboard=kb)


def get_manage_parsers_keyboard(parsers: dict):
    kb = []
    for name in parsers.keys():
        kb.append([InlineKeyboardButton(text=name, callback_data=f"managep_{name}")])
    return InlineKeyboardMarkup(inline_keyboard=kb)


def get_parser_action_keyboard(name: str, is_active: bool):
    toggle_text = locale("pause_btn") if is_active else locale("resume_btn")
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=toggle_text, callback_data=f"pact_toggle_{name}"
                )
            ],
            [
                InlineKeyboardButton(
                    text=locale("delete_btn"), callback_data=f"pact_delete_{name}"
                )
            ],
        ]
    )


def get_fs_category_prompt_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=locale("yes_btn"), callback_data="fs_cat_yes")],
            [InlineKeyboardButton(text=locale("no_btn"), callback_data="fs_cat_no")],
        ]
    )
