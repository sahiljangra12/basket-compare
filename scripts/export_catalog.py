"""Write the sample catalog to docs/sample-catalog.json for the browser-only (GitHub Pages) mode.

Run after editing app/adapters/demo.py:  python scripts/export_catalog.py
"""
import json
from pathlib import Path

from app.adapters.demo import CATALOG, INDEX
from app.adapters.linkouts import search_url

root = Path(__file__).resolve().parent.parent
data = {
    "index": INDEX,
    "items": [
        {"title": t, "keywords": k, "base": b, "sizes": s,
         "urls": {r: search_url(r, t) for r in s}}
        for t, k, b, s in CATALOG
    ],
}
(root / "docs" / "sample-catalog.json").write_text(json.dumps(data, indent=1))
print("wrote", len(CATALOG), "items")
