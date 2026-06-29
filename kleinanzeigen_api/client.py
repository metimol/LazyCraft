from __future__ import annotations

import asyncio
import base64
import html
import logging
import os
import random
import time
import uuid
from dataclasses import asdict, dataclass, field

from curl_cffi.requests import AsyncSession

from . import categories as _catalog

API_HOST = "https://api.kleinanzeigen.de"
WEB_HOST = "https://www.kleinanzeigen.de"
ADS_NS = "{http://www.ebayclassifiedsgroup.com/schema/ad/v1}ads"
LOCATIONS_NS = "{http://www.ebayclassifiedsgroup.com/schema/location/v1}locations"
SEARCH_META_NS = "{http://www.ebayclassifiedsgroup.com/schema/ad/v1}ads-search-options"

# Get android app secrets from environment variables
APP_VERSION = os.environ.get("APP_VERSION", None)
DEFAULT_BASIC_USER = os.environ.get("APP_USER", None)
DEFAULT_BASIC_PW = os.environ.get("APP_PASSWORD", None)

if None in [APP_VERSION, DEFAULT_BASIC_USER, DEFAULT_BASIC_PW]:
    raise RuntimeError(
        "Set APP_VERSION, APP_USER and APP_PASSWORD environment variables.",
    )


# --------------------------------------------------------------------------- #
# capi (eBay-Classifieds) JSON helpers — values are wrapped in {"value": ...}
# --------------------------------------------------------------------------- #
def _val(node):
    """Pull the scalar value out of a capi node. Handles nesting like {'value': {'value': x}}."""
    if isinstance(node, dict):
        if "value" in node:
            return _val(node["value"])
        return node
    return node


def _num(x) -> float | None:
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def _as_terms(exclude) -> list:
    """Turn the exclude argument (str, list, or None) into a list of lowercase terms."""
    if not exclude:
        return []
    if isinstance(exclude, str):
        exclude = [exclude]
    return [str(t).strip().lower() for t in exclude if t and str(t).strip()]


def _excluded(listing, terms) -> bool:
    """Return True if the title or description contains any of the excluded terms."""
    if not terms:
        return False
    hay = f"{listing.title}\n{listing.description}".lower()
    return any(t in hay for t in terms)


@dataclass
class Listing:
    """One ad returned by the API."""

    id: str
    title: str
    description: str
    price: float | None
    price_type: str
    url: str
    city: str
    zip_code: str
    latitude: float | None
    longitude: float | None
    size_m2: float | None
    rooms: float | None
    posted: str
    poster_type: str
    images: list = field(default_factory=list)
    attributes: dict = field(default_factory=dict)  # localized-label -> value

    def to_dict(self) -> dict:
        return asdict(self)


_global_last_request = 0.0
_global_lock = None


def _get_api_lock():
    global _global_lock
    if _global_lock is None:
        _global_lock = asyncio.Lock()
    return _global_lock


class KleinanzeigenAPI:
    """Client for the Kleinanzeigen mobile JSON API.

    Arguments:
        rate_limit: minimum seconds to wait between requests (plus a little
            random jitter).
        app_version: version string sent in the app headers.
        timeout: per-request timeout in seconds.
        max_retries: how many times to retry on temporary errors (429, 5xx, or
            network problems).
        basic_user / basic_pw: override the built-in Basic-auth login. If these
            are not set, the APP_USER / APP_PASSWORD
            environment variables are used, then the built-in defaults.

    """

    def __init__(
        self,
        rate_limit: float = 1.0,
        app_version: str = APP_VERSION,
        timeout: int = 25,
        max_retries: int = 3,
        basic_user: str | None = None,
        basic_pw: str | None = None,
    ):
        self.rate_limit = rate_limit
        self.app_version = app_version
        self.timeout = timeout
        self.max_retries = max_retries
        self._last = 0.0
        # build one install id per client, the same way the app makes one per install
        self._xapp = f"{uuid.uuid4()}{int(time.time() * 1000)}"
        user = basic_user or DEFAULT_BASIC_USER
        pw = basic_pw or DEFAULT_BASIC_PW
        self._auth = "Basic " + base64.b64encode(f"{user}:{pw}".encode()).decode()
        self._s = AsyncSession(impersonate="chrome")

    async def close(self):
        if self._s:
            await self._s.close()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.close()

    # -- transport ---------------------------------------------------------- #
    def _headers(self) -> dict:
        return {
            "X-EBAYK-APP": self._xapp,
            "X-ECG-USER-AGENT": f"ebayk-android-app-{self.app_version}",
            "X-ECG-USER-VERSION": self.app_version,
            "User-Agent": f"Kleinanzeigen/{self.app_version} (Android 13; Pixel 7)",
            "Accept": "application/json",
            "Accept-Language": "de-DE",
            "Authorization": self._auth,
        }

    async def _get(self, url: str, params: dict | None = None):
        global _global_last_request
        last = None
        for attempt in range(1, self.max_retries + 1):
            async with _get_api_lock():
                wait = self.rate_limit - (time.time() - _global_last_request)
                if wait > 0:
                    await asyncio.sleep(wait)
                # Jitter
                await asyncio.sleep(random.uniform(0.3, 0.7))

                try:
                    r = await self._s.get(
                        url,
                        params=params,
                        headers=self._headers(),
                        timeout=self.timeout,
                    )
                    _global_last_request = time.time()
                    if r.status_code == 200:
                        return r
                    if r.status_code in (401, 403):
                        raise RuntimeError(
                            f"{r.status_code} from API — Basic-auth credentials likely "
                            f"rotated. Supply fresh ones via basic_user/basic_pw or the "
                            f"APP_USER/APP_PASSWORD env vars. "
                            f"Body: {r.text[:160]}",
                        )
                    if r.status_code in (429, 500, 503):
                        await asyncio.sleep(1.5 * attempt + random.uniform(0, 1.5))
                        continue
                    r.raise_for_status()
                except RuntimeError:
                    raise
                except Exception as e:  # noqa: BLE001 - retry on any network error
                    last = e
                    _global_last_request = time.time()
                    await asyncio.sleep(1.2 * attempt)
        raise RuntimeError(f"GET failed after {self.max_retries} tries: {url} ({last})")

    # -- location resolution ------------------------------------------------ #
    async def resolve_location(self, query: str) -> list:
        """Look up a place name and return a list of (location_id, label) matches.

        Asks the app's location endpoint first. If that call fails for any reason
        (e.g. the credentials stopped working), it quietly tries the website
        instead, so this keeps working either way.
        """
        try:
            cands = await self._resolve_location_api(query)
            if cands:
                return cands
        except Exception:  # API down or response unreadable -> try the website
            pass
        return await self._resolve_location_web(query)

    async def _resolve_location_api(self, query: str) -> list:
        """Look up a place name using the app's /api/locations.json endpoint."""
        r = await self._get(f"{API_HOST}/api/locations.json", params={"q": query})
        data = r.json()
        root = _val(data.get(LOCATIONS_NS, {}))
        nodes = root.get("location") if isinstance(root, dict) else None
        if isinstance(nodes, dict):  # one match comes back as a single item, not a list
            nodes = [nodes]
        out: list = []
        self._flatten_locations(nodes, out)
        return out

    def _flatten_locations(self, nodes, out: list) -> None:
        """Turn the nested location tree into a flat list of (id, label) pairs.

        A place can contain sub-places (Berlin -> Charlottenburg -> a postcode).
        We add each place before its sub-places, so bigger areas like "Berlin"
        end up first and best_location() picks them over smaller ones.
        """
        for n in nodes or []:
            lid = _val(n.get("id"))
            label = _val(n.get("localized-name")) or _val(n.get("id-name"))
            if lid is not None and label:
                out.append((str(lid), label))
            kids = n.get("location")
            if kids:
                self._flatten_locations(kids if isinstance(kids, list) else [kids], out)

    async def _resolve_location_web(self, query: str) -> list:
        """Look up a place name on the website (used only as a backup)."""
        r = await self._s.get(
            f"{WEB_HOST}/s-ort-empfehlungen.json",
            params={"query": query},
            headers={"X-Requested-With": "XMLHttpRequest", "Accept-Language": "de-DE"},
            timeout=self.timeout,
        )
        out = []
        for k, label in r.json().items():
            lid = k.lstrip("_")
            if lid != "0":
                out.append((lid, label))
        return out

    # -- parsing ------------------------------------------------------------ #
    @staticmethod
    def _parse_ad(ad: dict) -> Listing:
        """Build a Listing from one ad dict in the API response."""
        addr = ad.get("ad-address", {})
        price = ad.get("price", {})
        # attributes
        attrs, size, rooms = {}, None, None
        for at in (ad.get("attributes", {}) or {}).get("attribute", []) or []:
            label = at.get("localized-label") or at.get("name")
            vlist = at.get("value") or []
            v = vlist[0].get("value") if vlist else None
            attrs[label] = v
            name = at.get("name", "")
            if name.endswith(".qm"):  # wohnung_mieten.qm / haus_mieten.qm
                size = _num(v)
            elif name.endswith(".zimmer"):  # *_mieten.zimmer
                rooms = _num(v)
        # public website link
        url = ""
        for ln in ad.get("link", []) or []:
            if ln.get("rel") == "self-public-website":
                url = ln.get("href", "")
        # images: collect the image urls, preferring the larger sizes
        images = []
        for pic in (ad.get("pictures", {}) or {}).get("picture", []) or []:
            best = None
            for ln in pic.get("link", []) or []:
                href = ln.get("href", "")
                if ln.get("rel") in ("XXL", "large", "teaser") or best is None:
                    best = href
            if best:
                images.append(best)
        return Listing(
            id=str(ad.get("id", "")),
            title=html.unescape(_val(ad.get("title")) or ""),
            description=html.unescape(_val(ad.get("description")) or ""),
            price=_num(_val(price.get("amount"))) if price.get("amount") else None,
            price_type=_val(price.get("price-type")) or "",
            url=url,
            city=_val(addr.get("state")) or "",
            zip_code=_val(addr.get("zip-code")) or "",
            latitude=_num(_val(addr.get("latitude"))),
            longitude=_num(_val(addr.get("longitude"))),
            size_m2=size,
            rooms=rooms,
            posted=_val(ad.get("start-date-time")) or "",
            poster_type=_val(ad.get("poster-type")) or "",
            images=images,
            attributes=attrs,
        )

    # -- search ------------------------------------------------------------- #
    async def search_page(
        self,
        *,
        category_id=None,
        location_id=None,
        distance_km=None,
        min_price=None,
        max_price=None,
        ad_type="OFFERED",
        q=None,
        picture_required=False,
        sort_type=None,
        page=0,
        size=25,
    ):
        """Fetch one page of results. Returns (total_found, list_of_Listing)."""
        params = {"page": page, "size": size}
        if category_id:
            params["categoryId"] = category_id
        if location_id:
            params["locationId"] = location_id
        if distance_km is not None:
            params["distance"] = distance_km
        if min_price is not None:
            params["minPrice"] = min_price
        if max_price is not None:
            params["maxPrice"] = max_price
        if ad_type:
            params["adType"] = ad_type
        if q:
            params["q"] = q
        if picture_required:
            params["pictureRequired"] = "true"
        if (
            sort_type
        ):  # PRICE_ASCENDING | PRICE_DESCENDING | DATE_DESCENDING | DISTANCE_ASCENDING
            params["sortType"] = sort_type

        r = await self._get(f"{API_HOST}/api/ads.json", params=params)
        data = r.json()
        block = data.get(ADS_NS, {}).get("value", {})
        total = int(_num(block.get("paging", {}).get("numFound")) or 0)
        raw = block.get("ad", [])
        if isinstance(raw, dict):  # capi returns a single object when 1 result
            raw = [raw]
        return total, [self._parse_ad(a) for a in raw]

    async def search(
        self,
        location: int = None,
        *,
        q: str = None,
        exclude=None,
        category: str = None,
        category_id: int = None,
        distance_km: int = None,
        min_price: int = None,
        max_price: int = None,
        ad_type: str = "OFFERED",
        sort_type=None,
        pages: int = 1,
        size: int = 25,
        sort_by_price: bool = False,
    ):
        """Search kleinanzeigen.de. By default this searches every category.

        Picking a category:
          - category takes a name or an id, for example "Fahrräder & Zubehör" or
            217. Names are looked up in the bundled catalog and raise a
            ValueError if they are unknown or match more than one category (use
            find_categories() to browse).
          - category_id is the same thing but only accepts an id. Pass either
            category or category_id, not both.

        location should be a numeric zip code

        q is the keyword sent to the server. exclude (a string or list of
        strings) removes any result whose title or description contains one of
        the terms (case-insensitive, done on our side).

        Returns a list of Listing, in the order the server sorted them
        (sort_type).
        """
        if category is not None and category_id is not None:
            raise ValueError("pass either `category` or `category_id`, not both")
        category_id = _catalog.resolve_category(
            category if category is not None else category_id,
        )
        if sort_by_price and not sort_type:  # default to cheapest-first
            sort_type = "PRICE_ASCENDING"
        exclude_terms = _as_terms(exclude)
        location_id = None
        if location:
            if str(location).isdigit():
                locations = await self.resolve_location(str(location))
                if locations:
                    location_id = locations[0][0]
                    logging.info(
                        f"Resolved location {location} to location_id in Kleinanzeigen API: {location_id} ({locations[0][1]})",
                    )
                else:
                    logging.warning(f"Could not resolve location zip code {location}")
                    location_id = str(location)  # fallback
            else:
                raise ValueError("Invalid location zip code")

        # TODO: Remove logging after release
        logging.info(f"Search radius in Kleinanzeigen API: {distance_km}")

        results, seen = [], set()
        for page in range(pages):
            total, listings = await self.search_page(
                category_id=category_id,
                location_id=location_id,
                distance_km=distance_km,
                min_price=min_price,
                max_price=max_price,
                ad_type=ad_type,
                q=q,
                sort_type=sort_type,
                page=page,
                size=size,
            )
            if not listings:
                break
            for listing in listings:
                if listing.id in seen:
                    continue
                if _excluded(listing, exclude_terms):
                    continue
                seen.add(listing.id)
                results.append(listing)
            if (page + 1) * size >= total:
                break
        return results  # already ordered by the server (sort_type)

    async def search_rentals(self, location=None, **kwargs):
        """Shortcut for search() limited to apartment rentals (category id 203,
        "Mietwohnungen"). Takes the same keyword arguments as search(); pass
        category_id yourself to use a different category.
        """
        return await self.search(location=location, category_id=203, **kwargs)

    async def search_metadata(self, category=None, *, category_id=None):
        """List the filters you can search a category with.

        Returns a dict like ``param_name -> {label, type, search_param, values}``.
        ``values`` only appears for filters with a fixed set of choices (e.g.
        priceType, adType) and holds the allowed ``(value, label)`` pairs. This
        is the same filter info the app uses to draw its filter screen.

        Give a category as a name or id via ``category``, or an id via
        ``category_id``; one of them is required.
        """
        if category is not None and category_id is not None:
            raise ValueError("pass either `category` or `category_id`, not both")
        cat = _catalog.resolve_category(
            category if category is not None else category_id,
        )
        if cat is None:
            raise ValueError("search_metadata needs a category (name or id)")
        r = await self._get(f"{API_HOST}/api/ads/search-metadata/{cat}.json")
        data = r.json()
        opts = _val(data.get(SEARCH_META_NS, {}))
        out: dict = {}
        for name, spec in opts.items() if isinstance(opts, dict) else []:
            if not isinstance(spec, dict):
                continue
            entry = {
                "label": spec.get("localized-label"),
                "type": spec.get("type"),
                "search_param": spec.get("search-param"),
            }
            sv = spec.get("supported-value")
            if sv:
                if isinstance(sv, dict):  # one choice comes back alone, not in a list
                    sv = [sv]
                entry["values"] = [
                    (v.get("value"), v.get("localized-label"))
                    for v in sv
                    if isinstance(v, dict)
                ]
            out[name] = entry
        return out

    async def get_ad(self, ad_id: str) -> Listing:
        """Fetch a single ad by id."""
        r = await self._get(f"{API_HOST}/api/ads/{ad_id}.json")
        data = r.json()
        # single-ad payload wraps under an "ad" key
        ad = data.get("{http://www.ebayclassifiedsgroup.com/schema/ad/v1}ad", data)
        ad = ad.get("value", ad) if isinstance(ad, dict) else ad
        return self._parse_ad(ad)

    # -- categories (offline, bundled catalog) ------------------------------ #
    @staticmethod
    def categories() -> list:
        """Return the bundled category catalog as a list of Category objects."""
        return _catalog.all_categories()

    @staticmethod
    def find_categories(query: str, limit: int = 8) -> list:
        """Search the bundled catalog by name/path, best match first."""
        return _catalog.find_categories(query, limit=limit)

    @staticmethod
    def get_category(category_id):
        """Return the Category for this id, or None if it's not found."""
        return _catalog.get_category(category_id)

    @staticmethod
    def resolve_category(value):
        """Convert a category name or id to an id string (None means all categories)."""
        return _catalog.resolve_category(value)

    async def update_categories(self) -> None:
        """Download the live category list and update the in-memory cache."""
        r = await self._get(f"{API_HOST}/api/categories.json")
        data = r.json()
        flat = _catalog.flatten_api_categories(data)

        categories = [_catalog.Category(**c) for c in flat]
        _catalog.set_categories(categories)

    async def fetch_categories(self) -> list:
        """Download the live category list and return it as Category objects.

        Use this to rebuild the bundled data/categories.json when the site
        changes its categories.
        """
        r = await self._get(f"{API_HOST}/api/categories.json")
        data = r.json()
        return [_catalog.Category(**c) for c in _catalog.flatten_api_categories(data)]
