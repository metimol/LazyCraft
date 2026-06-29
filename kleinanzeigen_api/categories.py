"""Category catalog: look up categories, search by name, and convert names to ids.

All ~159 categories are stored in data/categories.json, so lookups work without
a network request.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass

_CAT_NS = "{http://www.ebayclassifiedsgroup.com/schema/category/v1}categories"


@dataclass(frozen=True)
class Category:
    id: str
    name: str
    path: str  # e.g. "Auto, Rad & Boot > Fahrräder & Zubehör"
    real_estate: bool = False

    def to_dict(self) -> dict:
        return asdict(self)


_CATEGORIES_CACHE: list[Category] = []
_BY_ID_CACHE: dict = {}


def set_categories(categories: list[Category]) -> None:
    global _CATEGORIES_CACHE, _BY_ID_CACHE
    _CATEGORIES_CACHE = categories
    _BY_ID_CACHE = {c.id: c for c in categories}


def all_categories() -> list[Category]:
    """Return the catalog as a list of Category objects."""
    if not _CATEGORIES_CACHE:
        msg = "Categories not loaded. Call api.update_categories() first."
        raise RuntimeError(msg)
    return _CATEGORIES_CACHE


def _by_id() -> dict:
    if not _BY_ID_CACHE:
        msg = "Categories not loaded. Call api.update_categories() first."
        raise RuntimeError(msg)
    return _BY_ID_CACHE


def get_category(category_id) -> Category | None:
    """Return the Category with this id, or None if the id is not found."""
    if category_id is None:
        return None
    return _by_id().get(str(category_id))


def find_categories(query: str, limit: int = 8) -> list[Category]:
    """Return up to `limit` categories that match `query`, best matches first.

    Matches are ranked in this order: exact name, name starts with the query,
    name contains the query, then path contains the query.
    """
    q = (query or "").lower().strip()
    if not q:
        return []
    scored = []
    for c in all_categories():
        name, path = c.name.lower(), c.path.lower()
        if name == q:
            s = 0
        elif name.startswith(q):
            s = 1
        elif q in name:
            s = 2
        elif q in path:
            s = 3
        else:
            continue
        scored.append((s, len(c.name), c))
    scored.sort(key=lambda x: (x[0], x[1]))
    return [c for _, _, c in scored[:limit]]


def resolve_category(value) -> str | None:
    """Convert a category name or id into an id string.

    Rules:
    - None or "" returns None, which means "search all categories".
    - A number or numeric string is returned unchanged.
    - A name is looked up. A case-insensitive exact match is used first,
      otherwise the single best match from find_categories().

    Raises ValueError if the name is unknown or matches more than one category.
    The error message lists the possible matches.
    """
    if value is None:
        return None
    s = str(value).strip()
    if not s:
        return None
    if s.isdigit():
        return s

    exact = [c for c in all_categories() if c.name.lower() == s.lower()]
    if len(exact) == 1:
        return exact[0].id
    if len(exact) > 1:
        opts = ", ".join(f"{c.id} ({c.path})" for c in exact)
        msg = f"Category name {value!r} is ambiguous: {opts}. Pass the numeric id instead."
        raise ValueError(
            msg,
        )

    cands = find_categories(s, limit=6)
    if len(cands) == 1:
        return cands[0].id
    if not cands:
        msg = (
            f"Unknown category {value!r}. Browse with find_categories({value!r}) "
            f"or KleinanzeigenAPI().find_categories({value!r})."
        )
        raise ValueError(
            msg,
        )
    opts = "; ".join(f"{c.name} (id {c.id})" for c in cands)
    msg = (
        f"Ambiguous category {value!r}. Did you mean: {opts}? "
        f"Pass an exact name or the numeric id."
    )
    raise ValueError(
        msg,
    )


def flatten_api_categories(payload: dict) -> list[dict]:
    """Convert a raw /api/categories.json response into the flat format used by
    data/categories.json: [{"id", "name", "path", "real_estate"}, ...].

    fetch_categories() uses this to rebuild the bundled file when categories are
    added or renamed on the site.
    """
    root = payload[_CAT_NS]
    node = root.get("value", root) if isinstance(root, dict) else root

    def name_of(cat: dict) -> str:
        return (
            (cat.get("localized-name") or {}).get("value")
            or (cat.get("id-name") or {}).get("value")
            or ""
        )

    out: list[dict] = []

    def walk(cat: dict, parts: list, real_estate: bool) -> None:
        nm = name_of(cat)
        path_parts = [*parts, nm] if nm else parts
        cid = cat.get("id")
        if cid:  # skip the synthetic "Alle Kategorien" root (no id)
            out.append(
                {
                    "id": str(cid),
                    "name": nm,
                    "path": " > ".join(path_parts),
                    "real_estate": real_estate,
                },
            )
        for child in cat.get("category", []) or []:
            walk(child, path_parts, real_estate)

    for alle in node.get("category", []) or []:  # "Alle Kategorien"
        for branch in alle.get("category", []) or []:  # top-level branches
            is_re = (branch.get("id-name") or {}).get("value") == "Immobilien"
            walk(branch, [], is_re)
    return out
