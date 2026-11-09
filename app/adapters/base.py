from __future__ import annotations

from abc import ABC, abstractmethod

from ..models import Offer


class PriceSource(ABC):
    """A retailer (or group of retailers) we can pull real prices from."""

    name: str = "source"

    @property
    @abstractmethod
    def configured(self) -> bool:
        """True when the API credentials this source needs are present."""

    @abstractmethod
    async def search(self, query: str, zip_code: str, limit: int = 10) -> list[Offer]:
        """Return offers for a search term near a ZIP code."""
