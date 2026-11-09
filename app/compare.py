"""Ranking offers fairly and pricing a whole shopping basket."""
from __future__ import annotations

import re
from collections import Counter

from .models import Offer
from .units import DISPLAY, parse_size

DISPLAY_PER = {label: per for label, per in DISPLAY.values()}

_STOP = {"the", "a", "an", "of", "and", "fresh", "organic"}


def _tokens(text: str) -> set[str]:
    words = re.findall(r"[a-z0-9%]+", text.lower())
    return {w.rstrip("s") if len(w) > 3 else w for w in words if w not in _STOP}


def relevant(offers: list[Offer], query: str) -> list[Offer]:
    """Drop results that don't contain every word of the query. (A broader product like
    'grape jelly' still passes; unit-price ranking keeps it from looking like a deal on grapes
    only when its unit differs, so better matching is a known next step.)"""
    need = _tokens(query)
    if not need:
        return offers
    return [o for o in offers if need <= _tokens(o.title)]


def main_unit(offers: list[Offer]) -> str | None:
    units = Counter(o.unit for o in offers if o.unit)
    return units.most_common(1)[0][0] if units else None


def rank(offers: list[Offer]) -> list[Offer]:
    """Cheapest first by unit price within the most common unit; others after, by price."""
    unit = main_unit(offers)
    comparable = sorted((o for o in offers if o.unit == unit and o.unit_price is not None),
                        key=lambda o: (o.unit_price, o.price))
    rest = sorted((o for o in offers if o not in comparable), key=lambda o: o.price)
    return comparable + rest


def best_per_retailer(offers: list[Offer]) -> dict[str, Offer]:
    best: dict[str, Offer] = {}
    for o in rank(offers):
        best.setdefault(o.retailer, o)
    return best


def _pack_qty(o: Offer) -> float | None:
    size = parse_size(o.size) or parse_size(o.title)
    return size.quantity if size else None


def _line_cost(o: Offer, unit: str | None, ref_qty: float | None, n: int) -> float:
    """Cost of n reference-sized amounts at this offer's unit price, so a half-gallon
    can't beat a gallon just by being smaller."""
    qty = _pack_qty(o)
    if unit and o.unit == unit and ref_qty and qty:
        return o.price * (ref_qty / qty) * n
    return o.price * n


def price_basket(lines: list[tuple[str, int, list[Offer]]]) -> dict:
    """lines: (query, quantity, offers). Returns per-store totals and the cheapest split.
    Every store is priced for the same amount of each item (the most common pack size)."""
    per_line = []
    for q, n, offers in lines:
        best = best_per_retailer(offers)
        unit = main_unit(list(best.values()))
        sizes = sorted(x for x in (_pack_qty(o) for o in best.values() if o.unit == unit) if x)
        ref_qty = Counter(sizes).most_common(1)[0][0] if sizes else None
        per_line.append((q, n, best, unit, ref_qty))
    retailers = sorted({r for _q, _n, best, _u, _ref in per_line for r in best})

    stores = []
    for r in retailers:
        picks, missing, total = [], [], 0.0
        for q, n, best, unit, ref_qty in per_line:
            if r in best:
                o = best[r]
                cost = _line_cost(o, unit, ref_qty, n)
                total += cost
                picks.append({"query": q, "quantity": n, "cost": round(cost, 2),
                              "amount": _amount_label(unit, ref_qty), "offer": o.model_dump()})
            else:
                missing.append(q)
        stores.append({"retailer": r, "total": round(total, 2), "complete": not missing,
                       "missing": missing, "items": picks})
    stores.sort(key=lambda s: (not s["complete"], s["total"]))

    split_items, split_total, uncovered = [], 0.0, []
    for q, n, best, unit, ref_qty in per_line:
        if not best:
            uncovered.append(q)
            continue
        cheapest = min(best.values(), key=lambda o: _line_cost(o, unit, ref_qty, n))
        cost = _line_cost(cheapest, unit, ref_qty, n)
        split_total += cost
        split_items.append({"query": q, "quantity": n, "cost": round(cost, 2),
                            "amount": _amount_label(unit, ref_qty), "offer": cheapest.model_dump()})

    best_single = next((s for s in stores if s["complete"]), None)
    return {
        "stores": stores,
        "split": {"total": round(split_total, 2), "items": split_items,
                  "retailers": sorted({i["offer"]["retailer"] for i in split_items})},
        "best_single_store": best_single["retailer"] if best_single else None,
        "savings_vs_best_single": round(best_single["total"] - split_total, 2) if best_single else None,
        "not_found": uncovered,
    }


def _amount_label(unit: str | None, ref_qty: float | None) -> str | None:
    if not unit or not ref_qty:
        return None
    amount = ref_qty / DISPLAY_PER[unit]
    if unit == "fl oz" and ref_qty % 128 == 0:
        return f"{ref_qty / 128:g} gal"
    if unit == "item":
        return f"{amount:g} ct"
    return f"{amount:g} {unit}"
