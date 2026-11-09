"""Basket Compare — grocery price comparison for Maryland.

Run:  uvicorn app.main:app --reload     then open http://127.0.0.1:8000
On GitHub Pages the page in docs/ runs on its own with sample prices.
"""
from __future__ import annotations

import asyncio
import logging
import re

from fastapi import FastAPI, HTTPException, Query
from fastapi.staticfiles import StaticFiles

from . import config
from .adapters import instacart, linkouts
from .adapters.demo import DemoSource
from .catalog import correct, find
from .adapters.kroger import KrogerSource
from .adapters.walmart import WalmartSource
from .cache import PriceCache
from .compare import price_basket, rank, relevant
from .models import BasketRequest, Offer

log = logging.getLogger("basket")
app = FastAPI(title="Basket Compare", version="0.1.0")

LIVE_SOURCES = [KrogerSource(), WalmartSource()]
DEMO = DemoSource()
cache = PriceCache(config.CACHE_PATH, config.PRICE_TTL_MINUTES)

# Maryland ZIP codes run 206xx–219xx
MD_ZIP = re.compile(r"^2(0[6-9]|1[0-9])\d{2}$")


def demo_mode() -> bool:
    setting = (config.DEMO_MODE or "auto").lower()
    if setting in ("on", "true", "1"):
        return True
    if setting in ("off", "false", "0"):
        return False
    return not any(s.configured for s in LIVE_SOURCES)


def active_sources():
    return [DEMO] if demo_mode() else [s for s in LIVE_SOURCES if s.configured]


def _check_zip(zip_code: str) -> str:
    zip_code = zip_code.strip()[:5]
    if not MD_ZIP.match(zip_code):
        raise HTTPException(400, "Enter a 5-digit Maryland ZIP code (206xx–219xx).")
    return zip_code


async def _search_source(source, query: str, zip_code: str) -> tuple[list[Offer], str | None]:
    key = f"{source.name}|{query.lower().strip()}|{zip_code}"
    cached = cache.get(key)
    if cached is not None:
        return [Offer(**o) for o in cached], None
    try:
        offers = await source.search(query, zip_code)
    except Exception as exc:  # one retailer failing shouldn't break the page
        log.warning("%s failed: %s", source.name, exc)
        return [], f"{source.name} is unavailable right now."
    cache.set(key, [o.model_dump() for o in offers])
    return offers, None


async def find_offers(query: str, zip_code: str) -> tuple[list[Offer], list[str]]:
    query = correct(query) or query  # "graps" -> "grapes" before asking any store
    results = await asyncio.gather(*(_search_source(s, query, zip_code) for s in active_sources()))
    offers = [o for found, _ in results for o in found]
    errors = [err for _, err in results if err]
    return rank(relevant(offers, query) or offers), errors


def product_guide(query: str, offers: list[Offer]) -> dict | None:
    """Icon and description for what was searched, from the shared catalog."""
    match = find(query, limit=1)
    if match:
        m = match[0]
        return {"id": m["id"], "title": m["name"], "icon": m["icon"], "description": m["description"], "size": m["size"]}
    if offers:
        return {"id": None, "title": offers[0].title, "icon": None, "description": offers[0].description, "size": offers[0].size}
    return None


@app.get("/api/status")
async def status():
    return {
        "demo_mode": demo_mode(),
        "sources": {s.name: s.configured for s in LIVE_SOURCES},
        "instacart_ordering": instacart.configured(),
        "refresh_minutes": config.PRICE_TTL_MINUTES,
    }


@app.get("/api/search")
async def search(q: str = Query(..., min_length=2, max_length=80), zip: str = Query(...)):
    zip_code = _check_zip(zip)
    offers, errors = await find_offers(q, zip_code)
    priced = {o.retailer for o in offers}
    return {
        "guide": product_guide(q, offers),
        "query": q,
        "zip": zip_code,
        "demo_mode": demo_mode(),
        "offers": [o.model_dump() for o in offers],
        "best": offers[0].model_dump() if offers else None,
        "unpriced": [l.model_dump() for l in linkouts.unpriced(q, priced)],
        "errors": errors,
    }


@app.post("/api/basket")
async def basket(req: BasketRequest):
    zip_code = _check_zip(req.zip)
    if not req.items:
        raise HTTPException(400, "Add at least one item.")
    found = await asyncio.gather(*(find_offers(i.query, zip_code) for i in req.items))
    lines = [(i.query, max(i.quantity, 1), offers) for i, (offers, _) in zip(req.items, found)]
    result = price_basket(lines)
    result["demo_mode"] = demo_mode()
    return result


@app.post("/api/order/instacart")
async def order_instacart(req: BasketRequest):
    """Turn the basket into an Instacart shopping-list page (Giant, Aldi, Safeway, ...)."""
    if not req.items:
        raise HTTPException(400, "Add at least one item.")
    try:
        url = await instacart.shopping_list_link(
            "My Basket Compare list",
            [{"name": i.query, "quantity": max(i.quantity, 1)} for i in req.items],
        )
    except Exception as exc:
        log.warning("Instacart failed: %s", exc)
        raise HTTPException(502, "Instacart is unavailable right now.")
    return {"url": url, "configured": instacart.configured()}


# The web page lives in docs/ so GitHub Pages can serve the same files (in browser-only mode).
app.mount("/", StaticFiles(directory=config.ROOT / "docs", html=True), name="web")
