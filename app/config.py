"""Settings, read from environment variables (or a .env file next to the app)."""
from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _load_dotenv() -> None:
    env = ROOT / ".env"
    if not env.exists():
        return
    for line in env.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


_load_dotenv()


def get(name: str, default: str | None = None) -> str | None:
    value = os.environ.get(name, default)
    return value or default


# Kroger Public API (covers Kroger-family stores such as Harris Teeter)
KROGER_CLIENT_ID = get("KROGER_CLIENT_ID")
KROGER_CLIENT_SECRET = get("KROGER_CLIENT_SECRET")

# Walmart Affiliate API
WALMART_CONSUMER_ID = get("WALMART_CONSUMER_ID")
WALMART_KEY_VERSION = get("WALMART_KEY_VERSION", "1")
WALMART_PRIVATE_KEY_PATH = get("WALMART_PRIVATE_KEY_PATH")
WALMART_PUBLISHER_ID = get("WALMART_PUBLISHER_ID")  # affiliate ID for commissions

# Instacart Developer Platform (ordering hand-off for Giant, Aldi, Safeway, ...)
INSTACART_API_KEY = get("INSTACART_API_KEY")
INSTACART_ENV = get("INSTACART_ENV", "development")  # "development" or "production"

# Amazon Associates tag (Creators API needs 10 referred sales/30 days before it opens)
AMAZON_ASSOCIATE_TAG = get("AMAZON_ASSOCIATE_TAG")

# How long a fetched price stays fresh before we fetch it again
PRICE_TTL_MINUTES = int(get("PRICE_TTL_MINUTES", "180"))
CACHE_PATH = Path(get("CACHE_PATH", str(ROOT / "price_cache.sqlite3")))

# "auto": use demo data only when no live source is configured. "on"/"off" force it.
DEMO_MODE = get("DEMO_MODE", "auto")
