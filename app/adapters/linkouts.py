"""Search links for retailers we can't price through an official API yet.

Giant has no public API, and Amazon's Creators API only opens after an Associates
account has 10 referred sales in 30 days. Until then we send shoppers to search there.
"""
from __future__ import annotations

from urllib.parse import quote_plus

from .. import config
from ..models import LinkOut


def search_url(retailer: str, query: str) -> str:
    q = quote_plus(query)
    if retailer == "Giant":
        return f"https://giantfood.com/product-search/{q}"
    if retailer == "Amazon Fresh":
        tag = f"&tag={config.AMAZON_ASSOCIATE_TAG}" if config.AMAZON_ASSOCIATE_TAG else ""
        return f"https://www.amazon.com/s?k={q}&i=amazonfresh{tag}"
    if retailer == "Aldi":
        return f"https://www.aldi.us/results?q={q}"
    if retailer == "Walmart":
        return f"https://www.walmart.com/search?q={q}"
    if retailer == "Harris Teeter":
        return f"https://www.harristeeter.com/search?query={q}"
    return f"https://www.instacart.com/store/s?k={q}"


def unpriced(query: str, priced_retailers: set[str]) -> list[LinkOut]:
    reasons = {
        "Giant": "No public price API — check price on Giant's site or order through Instacart.",
        "Amazon Fresh": "Amazon's product API opens after the affiliate account has qualifying sales.",
        "Aldi": "No public price API — order through Instacart.",
    }
    return [
        LinkOut(retailer=r, url=search_url(r, query), reason=why)
        for r, why in reasons.items()
        if r not in priced_retailers
    ]
