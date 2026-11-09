from __future__ import annotations

from datetime import datetime, timezone

from pydantic import BaseModel, Field

from .units import parse_size, unit_price


class Offer(BaseModel):
    """One product at one retailer, with its current price."""

    retailer: str                      # "Walmart", "Harris Teeter", ...
    store: str | None = None           # store name/address when the price is store-specific
    title: str
    brand: str | None = None
    size: str | None = None            # as the retailer writes it, e.g. "2 lb bag"
    price: float                       # what the shopper pays now (promo if active)
    regular_price: float | None = None
    unit_price: float | None = None
    unit: str | None = None            # "lb", "fl oz", "item"
    url: str                           # where the shopper buys it (affiliate-tagged when configured)
    image: str | None = None
    image_credit: dict | None = None   # {"author", "license", "page"} for licensed stock photos
    description: str | None = None
    in_stock: bool | None = None
    price_scope: str = "store"         # "store" (local shelf price) or "online" (national web price)
    source: str = "live"               # "live" or "demo" — demo prices must never be shown as real
    fetched_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat(timespec="seconds"))

    def with_unit_price(self) -> "Offer":
        if self.unit_price is None:
            up, unit = unit_price(self.price, parse_size(self.size) or parse_size(self.title))
            self.unit_price, self.unit = up, unit
        return self


class LinkOut(BaseModel):
    """A retailer we can't price yet: we send the shopper to search there."""

    retailer: str
    url: str
    reason: str


class BasketItem(BaseModel):
    query: str
    quantity: int = 1


class BasketRequest(BaseModel):
    zip: str
    items: list[BasketItem]
