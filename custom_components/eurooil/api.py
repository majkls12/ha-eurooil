"""Client for the public EuroOil Srdcovka API."""

from __future__ import annotations

import asyncio
from typing import Any

from aiohttp import ClientError, ClientSession, ClientTimeout

from .const import PRICES_URL, REQUEST_TIMEOUT, STATIONS_URL


class EuroOilApiError(Exception):
    """Raised when the EuroOil API cannot be read."""


class EuroOilApi:
    """Read public fuel, price and delivery-quality data."""

    def __init__(self, session: ClientSession) -> None:
        self._session = session

    async def _get(self, url: str) -> dict[str, Any]:
        try:
            async with self._session.get(
                url, timeout=ClientTimeout(total=REQUEST_TIMEOUT.total_seconds())
            ) as response:
                response.raise_for_status()
                return await response.json(content_type=None)
        except (ClientError, TimeoutError, ValueError) as err:
            raise EuroOilApiError(f"Unable to read {url}") from err

    async def async_get_stations(self) -> list[dict[str, Any]]:
        """Return the public station catalogue."""
        return (await self._get(STATIONS_URL)).get("data", [])

    async def async_get_station(self, station_id: int) -> dict[str, Any] | None:
        """Return one station from the catalogue."""
        stations = await self.async_get_stations()
        return next(
            (station for station in stations if station.get("cerpaciStaniceIID") == station_id),
            None,
        )

    async def async_get_station_data(self, station_id: int) -> dict[str, Any]:
        """Return current prices and quality information for a station."""
        prices, quality = await asyncio.gather(
            self._get(PRICES_URL),
            self._get(f"{STATIONS_URL}/{station_id}/kvalita"),
        )
        return {
            "prices": {
                str(item["ean"]): item
                for item in prices.get("data", [])
                if item.get("cerpaciStaniceIID") == station_id
            },
            "quality": {
                str(item["ean"]): item
                for item in quality.get("data", [])
            },
            "quality_token": quality.get("token"),
        }
