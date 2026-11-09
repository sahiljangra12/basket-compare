"""Links to each store's own search results for an item.

Formats checked in a real browser on 2026-11-09:
  Walmart        /search?q=            works
  Harris Teeter  /search?query=&searchType=default_search   (without searchType it bounces to the homepage)
  Aldi           /store/aldi/s?k=       (the old /results?q= now 404s)
  Instacart      /store/s?k=            works
  Amazon Fresh   /s?k=&i=amazonfresh    Amazon's standard search format (Amazon blocks automated checks)
  Giant          /product-search/       Giant blocks automated browsers, so this one is unverified
Live results from the Kroger and Walmart APIs link to the exact product page instead.
"""
from __future__ import annotations

from urllib.parse import quote, quote_plus

from .. import config
from ..models import LinkOut


def search_url(retailer: str, query: str) -> str:
    q = quote_plus(query)
    if retailer == "Walmart":
        return f"https://www.walmart.com/search?q={q}"
    if retailer == "Harris Teeter":
        return f"https://www.harristeeter.com/search?query={q}&searchType=default_search"
    if retailer == "Aldi":
        return f"https://www.aldi.us/store/aldi/s?k={q}"
    if retailer == "Amazon Fresh":
        tag = f"&tag={config.AMAZON_ASSOCIATE_TAG}" if config.AMAZON_ASSOCIATE_TAG else ""
        return f"https://www.amazon.com/s?k={q}&i=amazonfresh{tag}"
    if retailer == "Giant":
        return f"https://giantfood.com/product-search/{quote(query)}"
    return f"https://www.instacart.com/store/s?k={q}"


def unpriced(query: str, priced_retailers: set[str]) -> list[LinkOut]:
    reasons = {
        "Giant": "No public price API yet. Check Giant's site directly.",
        "Amazon Fresh": "Amazon's price API opens after the affiliate account has qualifying sales.",
        "Aldi": "No public price API yet. Check Aldi's site directly.",
    }
    return [
        LinkOut(retailer=r, url=search_url(r, query), reason=why)
        for r, why in reasons.items()
        if r not in priced_retailers
    ]
