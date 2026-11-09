"""Kroger Public API — free, self-service, store-level prices.

In Maryland this covers Kroger-family stores, mainly Harris Teeter.
Docs: https://developer.kroger.com  (Products API: 10,000 calls/day on the free tier)
"""
from __future__ import annotations

import base64
import time

import httpx

from .. import config
from ..models import Offer
from .base import PriceSource

API = "https://api.kroger.com/v1"

# Kroger "chain" codes -> shopper-facing name and website
CHAINS = {
    "HARRISTEETER": ("Harris Teeter", "https://www.harristeeter.com"),
    "KROGER": ("Kroger", "https://www.kroger.com"),
}


def _describe(p: dict) -> str | None:
    """Kroger's public product data has no marketing copy; describe it from its fields."""
    bits = []
    if p.get("categories"):
        bits.append(" / ".join(p["categories"][:2]))
    if p.get("countryOrigin"):
        bits.append(f"Origin: {p['countryOrigin']}")
    return ". ".join(bits) + "." if bits else None


class KrogerSource(PriceSource):
    name = "Kroger family (Harris Teeter)"

    def __init__(self) -> None:
        self._token: str | None = None
        self._token_expires = 0.0
        self._stores: dict[str, dict | None] = {}  # zip -> nearest store

    @property
    def configured(self) -> bool:
        return bool(config.KROGER_CLIENT_ID and config.KROGER_CLIENT_SECRET)

    async def _get_token(self, client: httpx.AsyncClient) -> str:
        if self._token and time.time() < self._token_expires - 60:
            return self._token
        basic = base64.b64encode(
            f"{config.KROGER_CLIENT_ID}:{config.KROGER_CLIENT_SECRET}".encode()
        ).decode()
        r = await client.post(
            f"{API}/connect/oauth2/token",
            headers={"Authorization": f"Basic {basic}"},
            data={"grant_type": "client_credentials", "scope": "product.compact"},
        )
        r.raise_for_status()
        body = r.json()
        self._token = body["access_token"]
        self._token_expires = time.time() + int(body.get("expires_in", 1800))
        return self._token

    async def _nearest_store(self, client: httpx.AsyncClient, token: str, zip_code: str) -> dict | None:
        if zip_code in self._stores:
            return self._stores[zip_code]
        r = await client.get(
            f"{API}/locations",
            headers={"Authorization": f"Bearer {token}"},
            params={"filter.zipCode.near": zip_code, "filter.radiusInMiles": 15, "filter.limit": 1},
        )
        r.raise_for_status()
        data = r.json().get("data") or []
        store = data[0] if data else None
        self._stores[zip_code] = store
        return store

    async def search(self, query: str, zip_code: str, limit: int = 10) -> list[Offer]:
        async with httpx.AsyncClient(timeout=15) as client:
            token = await self._get_token(client)
            store = await self._nearest_store(client, token, zip_code)
            if not store:
                return []  # no Kroger-family store near this ZIP
            r = await client.get(
                f"{API}/products",
                headers={"Authorization": f"Bearer {token}"},
                params={
                    "filter.term": query,
                    "filter.locationId": store["locationId"],
                    "filter.limit": limit,
                },
            )
            r.raise_for_status()
            products = r.json().get("data") or []

        chain = (store.get("chain") or "KROGER").upper()
        retailer, site = CHAINS.get(chain, (chain.title(), "https://www.kroger.com"))
        addr = store.get("address") or {}
        store_label = f"{store.get('name', retailer)} — {addr.get('addressLine1', '')}, {addr.get('city', '')}".strip(" ,—")

        offers: list[Offer] = []
        for p in products:
            item = (p.get("items") or [{}])[0]
            price = item.get("price") or {}
            regular, promo = price.get("regular"), price.get("promo")
            current = promo if promo else regular
            if not current:
                continue  # seasonal/unpriced items come back without a price
            size = item.get("size")
            sold_by_weight = (item.get("soldBy") or "").upper() == "WEIGHT"
            image = None
            for img in p.get("images") or []:
                if img.get("perspective") == "front":
                    sizes = {s.get("size"): s.get("url") for s in img.get("sizes") or []}
                    image = sizes.get("large") or sizes.get("medium") or sizes.get("small")
            offers.append(
                Offer(
                    retailer=retailer,
                    store=store_label,
                    title=p.get("description", query),
                    brand=p.get("brand"),
                    size="1 lb (sold by weight)" if sold_by_weight else size,
                    price=float(current),
                    regular_price=float(regular) if regular else None,
                    url=site + (p.get("productPageURI") or f"/search?query={query}"),
                    image=image,
                    description=_describe(p),
                    in_stock=(item.get("fulfillment") or {}).get("inStore"),
                    price_scope="store",
                ).with_unit_price()
            )
        return offers
