"""Small SQLite cache so each retailer is queried at most once per TTL per search."""
from __future__ import annotations

import json
import sqlite3
import threading
import time
from pathlib import Path


class PriceCache:
    def __init__(self, path: Path, ttl_minutes: int):
        self.ttl = ttl_minutes * 60
        self._lock = threading.Lock()
        self._db = sqlite3.connect(str(path), check_same_thread=False)
        self._db.execute(
            "CREATE TABLE IF NOT EXISTS cache (key TEXT PRIMARY KEY, stored REAL, payload TEXT)"
        )
        self._db.commit()

    def get(self, key: str):
        with self._lock:
            row = self._db.execute("SELECT stored, payload FROM cache WHERE key=?", (key,)).fetchone()
        if not row or time.time() - row[0] > self.ttl:
            return None
        return json.loads(row[1])

    def set(self, key: str, value) -> None:
        with self._lock:
            self._db.execute(
                "INSERT OR REPLACE INTO cache (key, stored, payload) VALUES (?, ?, ?)",
                (key, time.time(), json.dumps(value)),
            )
            self._db.commit()
