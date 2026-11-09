"""SAMPLE prices for building and demoing the interface without API keys.

These numbers are invented. Every offer is tagged source="demo" and the UI shows a
banner, so they can never be mistaken for real prices.
"""
from __future__ import annotations

import hashlib

from ..models import Offer
from ..units import parse_size
from .base import PriceSource
from .linkouts import search_url

# name, keywords, base price, {retailer: size}  (size differs by store on purpose)
CATALOG = [
    ("Red Seedless Grapes", ["grape", "grapes"], 2.49, {"Giant": "per lb", "Walmart": "2 lb bag", "Amazon Fresh": "per lb", "Harris Teeter": "per lb", "Aldi": "2 lb bag"}),
    ("Green Seedless Grapes", ["grape", "grapes"], 2.59, {"Giant": "per lb", "Walmart": "per lb", "Harris Teeter": "per lb"}),
    ("Bananas", ["banana", "bananas"], 0.62, {"Giant": "per lb", "Walmart": "per lb", "Amazon Fresh": "per lb", "Harris Teeter": "per lb", "Aldi": "per lb"}),
    ("Gala Apples", ["apple", "apples", "gala"], 4.49, {"Giant": "3 lb bag", "Walmart": "3 lb bag", "Amazon Fresh": "per lb", "Harris Teeter": "per lb", "Aldi": "3 lb bag"}),
    ("Strawberries", ["strawberry", "strawberries", "berries"], 3.49, {"Giant": "16 oz", "Walmart": "16 oz", "Amazon Fresh": "16 oz", "Harris Teeter": "16 oz", "Aldi": "16 oz"}),
    ("Whole Milk", ["milk", "whole milk"], 3.59, {"Giant": "1 gal", "Walmart": "1 gal", "Amazon Fresh": "1 gal", "Harris Teeter": "1 gal", "Aldi": "1 gal"}),
    ("2% Reduced Fat Milk", ["milk", "2%"], 3.49, {"Giant": "1 gal", "Walmart": "1 gal", "Amazon Fresh": "0.5 gal", "Harris Teeter": "1 gal", "Aldi": "1 gal"}),
    ("Large Grade A Eggs", ["egg", "eggs"], 3.29, {"Giant": "12 ct", "Walmart": "18 ct", "Amazon Fresh": "12 ct", "Harris Teeter": "12 ct", "Aldi": "12 ct"}),
    ("White Sandwich Bread", ["bread", "white bread"], 2.19, {"Giant": "20 oz", "Walmart": "20 oz", "Amazon Fresh": "20 oz", "Harris Teeter": "20 oz", "Aldi": "20 oz"}),
    ("Boneless Skinless Chicken Breast", ["chicken", "chicken breast"], 3.99, {"Giant": "per lb", "Walmart": "2.5 lb", "Amazon Fresh": "per lb", "Harris Teeter": "per lb", "Aldi": "per lb"}),
    ("80% Lean Ground Beef", ["beef", "ground beef"], 5.49, {"Giant": "1 lb", "Walmart": "1 lb", "Amazon Fresh": "1 lb", "Harris Teeter": "1 lb", "Aldi": "1 lb"}),
    ("Long Grain White Rice", ["rice"], 3.29, {"Giant": "5 lb", "Walmart": "5 lb", "Amazon Fresh": "2 lb", "Harris Teeter": "5 lb", "Aldi": "3 lb"}),
    ("Spaghetti Pasta", ["pasta", "spaghetti"], 1.39, {"Giant": "16 oz", "Walmart": "16 oz", "Amazon Fresh": "16 oz", "Harris Teeter": "16 oz", "Aldi": "16 oz"}),
    ("Sharp Cheddar Cheese", ["cheese", "cheddar"], 2.99, {"Giant": "8 oz", "Walmart": "8 oz", "Amazon Fresh": "8 oz", "Harris Teeter": "8 oz", "Aldi": "16 oz"}),
    ("Salted Butter", ["butter"], 4.29, {"Giant": "16 oz", "Walmart": "16 oz", "Amazon Fresh": "16 oz", "Harris Teeter": "16 oz", "Aldi": "16 oz"}),
    ("Orange Juice, No Pulp", ["orange juice", "juice", "oj"], 3.99, {"Giant": "52 fl oz", "Walmart": "52 fl oz", "Amazon Fresh": "89 fl oz", "Harris Teeter": "52 fl oz", "Aldi": "52 fl oz"}),
    ("Greek Yogurt, Plain", ["yogurt", "greek yogurt"], 4.99, {"Giant": "32 oz", "Walmart": "32 oz", "Amazon Fresh": "32 oz", "Harris Teeter": "32 oz", "Aldi": "32 oz"}),
    ("Roma Tomatoes", ["tomato", "tomatoes"], 1.49, {"Giant": "per lb", "Walmart": "per lb", "Amazon Fresh": "per lb", "Harris Teeter": "per lb", "Aldi": "2 lb"}),
    ("Yellow Onions", ["onion", "onions"], 2.99, {"Giant": "3 lb bag", "Walmart": "3 lb bag", "Amazon Fresh": "3 lb bag", "Harris Teeter": "3 lb bag", "Aldi": "3 lb bag"}),
    ("Russet Potatoes", ["potato", "potatoes"], 4.49, {"Giant": "5 lb bag", "Walmart": "5 lb bag", "Amazon Fresh": "5 lb bag", "Harris Teeter": "5 lb bag", "Aldi": "5 lb bag"}),
    ("Ground Coffee, Medium Roast", ["coffee"], 8.99, {"Giant": "11.3 oz", "Walmart": "12 oz", "Amazon Fresh": "12 oz", "Harris Teeter": "11.3 oz", "Aldi": "12 oz"}),
]

# Rough store-level price index used only to make sample data look plausible
INDEX = {"Aldi": 0.86, "Walmart": 0.92, "Amazon Fresh": 1.0, "Giant": 1.06, "Harris Teeter": 1.12}
DEMO_STORES = {
    "Giant": "Giant — sample store",
    "Harris Teeter": "Harris Teeter — sample store",
    "Aldi": "Aldi — sample store",
}


def _noise(*parts: str) -> float:
    h = int(hashlib.sha256("|".join(parts).encode()).hexdigest()[:8], 16)
    return 0.9 + (h % 2000) / 10000  # 0.90 – 1.10, stable across runs


class DemoSource(PriceSource):
    name = "Sample data"

    @property
    def configured(self) -> bool:
        return True

    async def search(self, query: str, zip_code: str, limit: int = 10) -> list[Offer]:
        q = query.lower().strip()
        offers: list[Offer] = []
        for title, keywords, base, sizes in CATALOG:
            if not any(k in q or q in k for k in keywords) and q not in title.lower():
                continue
            ref = parse_size(next(iter(sizes.values())))
            per_base_unit = base / ref.quantity
            for retailer, size in sizes.items():
                qty = parse_size(size).quantity
                price = per_base_unit * qty * INDEX[retailer] * _noise(title, retailer, zip_code)
                if qty > 1.5 * ref.quantity:
                    price *= 0.93  # bigger packs a bit cheaper per unit
                price = round(price, 2)
                offers.append(
                    Offer(
                        retailer=retailer,
                        store=DEMO_STORES.get(retailer),
                        title=title,
                        size=size,
                        price=max(price, 0.25),
                        url=search_url(retailer, title),
                        in_stock=True,
                        price_scope="online" if retailer in ("Walmart", "Amazon Fresh") else "store",
                        source="demo",
                    ).with_unit_price()
                )
        return offers[: limit * 5]
