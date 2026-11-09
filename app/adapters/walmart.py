"""Walmart Affiliate API — free developer account, signed requests.

Prices here are Walmart.com online prices (national), not a specific store's shelf
price, so offers are marked price_scope="online".
Sign up: https://walmart.io  (Affiliate Marketing API)
"""
from __future__ import annotations

import base64
import time
from urllib.parse import quote_plus

import httpx

from .. import config
from ..models import Offer
from .base import PriceSource

SEARCH_URL = "https://developer.api.walmart.com/api-proxy/service/affil/product/v2/search"


def _plain(html: str | None) -> str | None:
    """Walmart descriptions come HTML-escaped; reduce to one or two plain sentences."""
    if not html:
        return None
    import html as _html
    import re

    text = re.sub(r"<[^>]+>", " ", _html.unescape(_html.unescape(html)))
    text = re.sub(r"\s+", " ", text).strip()
    return (text[:220].rsplit(" ", 1)[0] + "…") if len(text) > 220 else text


class WalmartSource(PriceSource):
    name = "Walmart"

    def __init__(self) -> None:
        self._key = None

    @property
    def configured(self) -> bool:
        return bool(config.WALMART_CONSUMER_ID and config.WALMART_PRIVATE_KEY_PATH)

    def _signed_headers(self) -> dict[str, str]:
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import padding

        if self._key is None:
            with open(config.WALMART_PRIVATE_KEY_PATH, "rb") as fh:
                self._key = serialization.load_pem_private_key(fh.read(), password=None)
        ts = str(int(time.time() * 1000))
        to_sign = f"{config.WALMART_CONSUMER_ID}\n{ts}\n{config.WALMART_KEY_VERSION}\n".encode()
        signature = self._key.sign(to_sign, padding.PKCS1v15(), hashes.SHA256())
        return {
            "WM_CONSUMER.ID": config.WALMART_CONSUMER_ID,
            "WM_CONSUMER.INTIMESTAMP": ts,
            "WM_SEC.KEY_VERSION": config.WALMART_KEY_VERSION,
            "WM_SEC.AUTH_SIGNATURE": base64.b64encode(signature).decode(),
        }

    async def search(self, query: str, zip_code: str, limit: int = 10) -> list[Offer]:
        params = {"query": query, "numItems": limit, "categoryId": "976759"}  # 976759 = Food
        if config.WALMART_PUBLISHER_ID:
            params["publisherId"] = config.WALMART_PUBLISHER_ID
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(SEARCH_URL, params=params, headers=self._signed_headers())
            r.raise_for_status()
            items = r.json().get("items") or []

        offers: list[Offer] = []
        for it in items:
            price = it.get("salePrice")
            if price is None:
                continue
            url = (
                it.get("productTrackingUrl")
                or it.get("productUrl")
                or f"https://www.walmart.com/search?q={quote_plus(query)}"
            )
            offers.append(
                Offer(
                    retailer="Walmart",
                    title=it.get("name", query),
                    brand=it.get("brandName"),
                    size=it.get("size"),
                    price=float(price),
                    regular_price=float(it["msrp"]) if it.get("msrp") else None,
                    url=url,
                    image=it.get("largeImage") or it.get("mediumImage") or it.get("thumbnailImage"),
                    description=_plain(it.get("shortDescription")),
                    in_stock=(it.get("stock") or "").lower() == "available" if it.get("stock") else None,
                    price_scope="online",
                ).with_unit_price()
            )
        return offers
