import os
import json
from pathlib import Path
import logging
from contextvars import ContextVar

user_lang: ContextVar[str] = ContextVar("user_lang", default="en")


_locales_data = {}


def _load_locales():
    locales_dir = Path(__file__).parent / "locales"
    if not locales_dir.exists():
        return
    for file_path in locales_dir.glob("*.json"):
        lang = file_path.stem
        with open(file_path, mode="r", encoding="utf-8") as f:
            try:
                _locales_data[lang] = json.load(f)
            except json.JSONDecodeError:
                logging.warning(f"Invalid JSON file: {file_path}")
                pass  # Ignore invalid JSON files


_load_locales()


def locale(key: str, lang: str = None) -> str:
    if lang is None:
        lang = user_lang.get()

    lang_data = _locales_data.get(lang)
    if lang_data is None:
        lang_data = _locales_data.get("en", {})

    value = lang_data.get(key)
    if value is None:
        if lang != "en":
            value = _locales_data.get("en", {}).get(key)
        if value is None:
            raise ValueError(f"Cannot access phrase variable: {key} for lang {lang}")
    return value


BOT_TOKEN = os.getenv("BOT_TOKEN", None)
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", None)

ADMIN_ID_STR = os.getenv("ADMIN_ID", None)
ADMIN_ID = int(ADMIN_ID_STR) if ADMIN_ID_STR else None

if BOT_TOKEN is None or GOOGLE_API_KEY is None:
    raise Exception("Necessary environment variable not set")


DEFAULT_SEARCH_PROMPT = "Ищи рабочую электронику, велосипеды, инструменты. Игнорируй откровенный мусор, битые зеркала и пустые банки."
