from __future__ import annotations

import math

import aiohttp


async def get_lat_lon(zip_code: str) -> tuple[float, float] | None:
    url = f"https://nominatim.openstreetmap.org/search?postalcode={zip_code}&country=Germany&format=json"
    headers = {"User-Agent": "KeigenBot/1.0"}
    async with (
        aiohttp.ClientSession() as session,
        session.get(
            url,
            headers=headers,
        ) as response,
    ):
        if response.status == 200:
            data = await response.json()
            if data and len(data) > 0:
                return float(data[0]["lat"]), float(data[0]["lon"])
    return None


def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r_earth = 6371  # Earth radius in kilometers
    d_lat = math.radians(lat2 - lat1)
    d_lon = math.radians(lon2 - lon1)
    a = math.sin(d_lat / 2) * math.sin(d_lat / 2) + math.cos(
        math.radians(lat1),
    ) * math.cos(math.radians(lat2)) * math.sin(d_lon / 2) * math.sin(d_lon / 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return r_earth * c
