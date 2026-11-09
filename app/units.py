"""Turn package sizes like "2 lb", "16 fl oz" or "12 ct" into comparable unit prices.

Every size is reduced to one of three dimensions:
  weight -> ounces (shown to shoppers per lb)
  volume -> fluid ounces (shown per fl oz)
  count  -> items (shown per item)
"""
from __future__ import annotations

import re
from dataclasses import dataclass

# unit text -> (dimension, multiplier into the base unit)
_UNITS: dict[str, tuple[str, float]] = {
    # volume (checked before weight so "fl oz" is not read as "oz")
    "fl oz": ("volume", 1.0), "fl. oz": ("volume", 1.0), "floz": ("volume", 1.0),
    "fluid ounce": ("volume", 1.0), "fluid ounces": ("volume", 1.0),
    "gal": ("volume", 128.0), "gallon": ("volume", 128.0), "gallons": ("volume", 128.0),
    "qt": ("volume", 32.0), "quart": ("volume", 32.0), "quarts": ("volume", 32.0),
    "pt": ("volume", 16.0), "pint": ("volume", 16.0), "pints": ("volume", 16.0),
    "l": ("volume", 33.814), "liter": ("volume", 33.814), "liters": ("volume", 33.814),
    "litre": ("volume", 33.814), "ml": ("volume", 0.033814),
    # weight
    "lb": ("weight", 16.0), "lbs": ("weight", 16.0), "pound": ("weight", 16.0), "pounds": ("weight", 16.0),
    "oz": ("weight", 1.0), "ounce": ("weight", 1.0), "ounces": ("weight", 1.0),
    "kg": ("weight", 35.274), "g": ("weight", 0.035274), "gram": ("weight", 0.035274), "grams": ("weight", 0.035274),
    # count
    "ct": ("count", 1.0), "count": ("count", 1.0), "each": ("count", 1.0), "ea": ("count", 1.0),
    "pk": ("count", 1.0), "pack": ("count", 1.0), "pc": ("count", 1.0), "pcs": ("count", 1.0),
    "dozen": ("count", 12.0), "doz": ("count", 12.0),
}

# Longest unit names first so "fl oz" wins over "oz" and "lbs" over "lb".
_UNIT_PATTERN = "|".join(re.escape(u) for u in sorted(_UNITS, key=len, reverse=True))
_NUM = r"(\d+(?:\.\d+)?|\d+/\d+)"
_MULTI_RE = re.compile(rf"{_NUM}\s*(?:x|×)\s*{_NUM}\s*({_UNIT_PATTERN})\b", re.I)
_SINGLE_RE = re.compile(rf"{_NUM}\s*-?\s*({_UNIT_PATTERN})\b\.?", re.I)
_PER_RE = re.compile(rf"(?:/|per\s+)({_UNIT_PATTERN})\b", re.I)

DISPLAY = {"weight": ("lb", 16.0), "volume": ("fl oz", 1.0), "count": ("item", 1.0)}


@dataclass(frozen=True)
class Size:
    quantity: float   # amount in the base unit (oz, fl oz or items)
    dimension: str    # "weight" | "volume" | "count"


def _num(text: str) -> float:
    if "/" in text:
        a, b = text.split("/", 1)
        return float(a) / float(b)
    return float(text)


def parse_size(text: str | None) -> Size | None:
    """Parse a size string. Returns None when no size can be found."""
    if not text:
        return None
    t = text.lower().replace("fl. oz", "fl oz")
    m = _MULTI_RE.search(t)
    if m:
        dim, mult = _UNITS[m.group(3).lower()]
        return Size(_num(m.group(1)) * _num(m.group(2)) * mult, dim)
    m = _SINGLE_RE.search(t)
    if m:
        dim, mult = _UNITS[m.group(2).lower()]
        qty = _num(m.group(1)) * mult
        return Size(qty, dim) if qty > 0 else None
    m = _PER_RE.search(t)  # "$2.99/lb" style: priced per one unit
    if m:
        dim, mult = _UNITS[m.group(1).lower()]
        return Size(mult, dim)
    return None


def unit_price(price: float | None, size: Size | None) -> tuple[float | None, str | None]:
    """Price per display unit (per lb, per fl oz, per item)."""
    if price is None or size is None or size.quantity <= 0:
        return None, None
    label, per = DISPLAY[size.dimension]
    return round(price / (size.quantity / per), 4), label
