from __future__ import annotations

import json
import logging
import os
import re
from contextvars import ContextVar
from pathlib import Path

from dotenv import load_dotenv

logger = logging.getLogger(__name__)

load_dotenv()

user_lang: ContextVar[str] = ContextVar("user_lang", default="en")


_locales_data = {}


def _load_locales() -> None:
    locales_dir = Path(__file__).parent / "locales"
    if not locales_dir.exists():
        return
    for file_path in locales_dir.glob("*.json"):
        lang = file_path.stem
        with file_path.open(encoding="utf-8") as f:
            try:
                _locales_data[lang] = json.load(f)
            except json.JSONDecodeError:
                logger.warning("Invalid JSON file: %s", file_path)
                # Ignore invalid JSON files


_load_locales()


def locale(key: str, lang: str | None = None, *, strip_html: bool = False) -> str:
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
            msg = f"Cannot access phrase variable: {key} for lang {lang}"
            raise ValueError(msg)
    if strip_html:
        value = re.sub(r"<[^>]+>", "", value)
    return value


BOT_TOKEN = os.getenv("BOT_TOKEN", None)
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", None)

ADMIN_ID_STR = os.getenv("ADMIN_ID", None)
ADMIN_ID = int(ADMIN_ID_STR) if ADMIN_ID_STR else None

if BOT_TOKEN is None or GOOGLE_API_KEY is None:
    msg = "Necessary environment variable not set"
    raise RuntimeError(msg)
