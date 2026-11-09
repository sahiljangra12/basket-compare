"""Instacart Developer Platform — ordering hand-off.

The public API doesn't return prices. It turns a shopping list into an Instacart page
where the shopper picks a nearby store (Giant, Aldi, Safeway, ...) and checks out.
That covers ordering for stores we can't price yet. Self-service keys:
https://docs.instacart.com/developer_platform_api/
"""
from __future__ import annotations

from urllib.parse import quote_plus

import httpx

from .. import config

BASES = {
    "development": "https://connect.dev.instacart.tools",
    "production": "https://connect.instacart.com",
}


def _base() -> str:
    return BASES.get((config.INSTACART_ENV or "development").lower(), BASES["development"])


def configured() -> bool:
    return bool(config.INSTACART_API_KEY)


async def shopping_list_link(title: str, items: list[dict]) -> str:
    """items: [{"name": "grapes", "quantity": 1}] -> URL of an Instacart shopping-list page."""
    if not configured():
        # Without a key, fall back to a plain Instacart search for the first item.
        first = items[0]["name"] if items else ""
        return f"https://www.instacart.com/store/s?k={quote_plus(first)}"
    payload = {
        "title": title,
        "link_type": "shopping_list",
        "line_items": [
            {"name": i["name"], "quantity": i.get("quantity", 1), "unit": "each"} for i in items
        ],
    }
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.post(
            f"{_base()}/idp/v1/products/products_link",
            headers={
                "Authorization": f"Bearer {config.INSTACART_API_KEY}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            json=payload,
        )
        r.raise_for_status()
        return r.json()["products_link_url"]


async def nearby_retailers(zip_code: str) -> list[dict]:
    """Retailers Instacart serves near a ZIP code: [{"name": ..., "retailer_key": ...}]."""
    if not configured():
        return []
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.get(
            f"{_base()}/idp/v1/retailers",
            headers={"Authorization": f"Bearer {config.INSTACART_API_KEY}", "Accept": "application/json"},
            params={"postal_code": zip_code, "country_code": "US"},
        )
        r.raise_for_status()
        return r.json().get("retailers") or []
