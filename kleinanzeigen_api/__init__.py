"""Unofficial API for Kleinanzeigen via Mobile API
Got this idea from https://github.com/monkrel/kleinanzeigen-api.
"""

from __future__ import annotations

from .categories import Category, all_categories, find_categories, get_category
from .client import KleinanzeigenAPI, Listing

__version__ = "0.2.0"
__all__ = [
    "Category",
    "KleinanzeigenAPI",
    "Listing",
    "__version__",
    "all_categories",
    "find_categories",
    "get_category",
]
