"""SAMPLE prices from the shared catalog, for running without retailer API keys.

Every offer is tagged source="demo" and the UI says so, so these numbers can't be
mistaken for real prices. The browser computes its own samples the same way.
"""
from __future__ import annotations

from ..catalog import catalog, find
from ..models import Offer
from .base import PriceSource


def _noise(*parts: str) -> float:
    # FNV-1a, same as docs/engine.js, so server and browser agree.
    h = 2166136261
    for ch in "|".join(parts):
        h ^= ord(ch)
        h = (h * 16777619) & 0xFFFFFFFF
    return 0.9 + (h % 2000) / 10000


def sample_offers(item: dict, zip_code: str) -> list[Offer]:
    cat = catalog()
    offers = []
    for store in item["stores"]:
        raw = item["price"] * cat["index"][store] * _noise(item["id"], store, zip_code)
        price = round(round(raw * 100) / 100 - (0.01 if raw > 2 else 0), 2)
        offers.append(Offer(
            retailer=store, title=item["name"], size=item["size"], price=max(0.25, price),
            url=item["links"][store], image=item["icon"], description=item["description"],
            in_stock=True, price_scope="online" if store in ("Walmart", "Amazon Fresh") else "store",
            source="demo",
        ).with_unit_price())
    return offers


class DemoSource(PriceSource):
    name = "Sample data"

    @property
    def configured(self) -> bool:
        return True

    async def search(self, query: str, zip_code: str, limit: int = 10) -> list[Offer]:
        offers: list[Offer] = []
        for item in find(query, limit=3):
            offers.extend(sample_offers(item, zip_code))
        return offers
