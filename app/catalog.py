"""The shared product catalog (docs/catalog.json) and typo-tolerant matching for the server.

The browser does the same matching in docs/engine.js; this keeps the server's answers in line.
"""
from __future__ import annotations

import difflib
import json
import re
from functools import lru_cache

from . import config


@lru_cache(maxsize=1)
def catalog() -> dict:
    return json.loads((config.ROOT / "docs" / "catalog.json").read_text())


def norm(text: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9% ]+", " ", text.lower())).strip()


@lru_cache(maxsize=1)
def _vocab() -> list[str]:
    words = set()
    for item in catalog()["items"]:
        for phrase in [item["name"], *item["aliases"]]:
            words.update(w for w in norm(phrase).split() if len(w) > 1)
    return sorted(words)


def correct(query: str) -> str:
    """Fix obvious typos word by word against the catalog's vocabulary ("graps" -> "grapes")."""
    vocab = _vocab()
    fixed = []
    for w in norm(query).split():
        if w in vocab or len(w) <= 3:
            fixed.append(w)
            continue
        close = difflib.get_close_matches(w, vocab, n=1, cutoff=0.75)
        fixed.append(close[0] if close else w)
    return " ".join(fixed)


def find(query: str, limit: int = 8) -> list[dict]:
    """Catalog items matching a query, best first."""
    q = correct(query)
    q_words = q.split()
    scored = []
    for order, item in enumerate(catalog()["items"]):
        phrases = [norm(p) for p in [item["name"], *item["aliases"]]]
        words = {w for p in phrases for w in p.split()}
        hits = sum(any(w == qw or w.rstrip("s") == qw.rstrip("s") or w.startswith(qw) for w in words) for qw in q_words)
        if hits < len(q_words):
            continue
        score = hits * 10 + (12 if q in phrases else 0) + (4 if q in norm(item["name"]) else 0) - len(item["name"].split()) * 0.3
        scored.append((score, -order, item))
    scored.sort(key=lambda s: (s[0], s[1]), reverse=True)
    return [s[2] for s in scored[:limit]]
