"""Data coordinator for EuroOil."""

from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import EuroOilApi, EuroOilApiError
from .const import CONF_STATION_ADDRESS, CONF_STATION_ID, CONF_STATION_NAME, DOMAIN

_LOGGER = logging.getLogger(__name__)


class EuroOilCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Fetch one station's data only when requested by the configured schedule."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        api: EuroOilApi,
        update_interval: timedelta,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{entry.data[CONF_STATION_ID]}",
            update_interval=update_interval,
        )
        self.entry = entry
        self.api = api

    @property
    def station_id(self) -> int:
        return self.entry.data[CONF_STATION_ID]

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            return await self.api.async_get_station_data(self.station_id)
        except EuroOilApiError as err:
            raise UpdateFailed(str(err)) from err

    @property
    def device_info(self) -> dr.DeviceInfo:
        """Return the station device representation."""
        return dr.DeviceInfo(
            identifiers={(DOMAIN, str(self.station_id))},
            name=f"EuroOil / RoBiN OIL – {self.entry.data[CONF_STATION_NAME]}",
            manufacturer="ČEPRO, a.s.",
            model="Čerpací stanice",
            configuration_url="https://srdcovka.eurooil.cz/",
        )
