"""EuroOil / RoBiN OIL integration."""

from __future__ import annotations

from datetime import datetime
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.event import async_track_time_change

from .api import EuroOilApi
from .const import CONF_UPDATE_TIME, DEFAULT_UPDATE_TIME, DOMAIN
from .coordinator import EuroOilCoordinator

_LOGGER = logging.getLogger(__name__)
PLATFORMS = [Platform.SENSOR]


def _parse_update_time(value: str) -> tuple[int, int]:
    """Parse a HH:MM option, falling back to the default."""
    try:
        time_value = datetime.strptime(value, "%H:%M")
        return time_value.hour, time_value.minute
    except (TypeError, ValueError):
        _LOGGER.warning("Invalid EuroOil update time %s; using %s", value, DEFAULT_UPDATE_TIME)
        return 6, 0


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the EuroOil integration."""
    hass.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up a configured EuroOil station."""
    coordinator = EuroOilCoordinator(hass, entry, EuroOilApi(async_get_clientsession(hass)))
    await coordinator.async_config_entry_first_refresh()

    hour, minute = _parse_update_time(entry.options.get(CONF_UPDATE_TIME, DEFAULT_UPDATE_TIME))

    @callback
    def _scheduled_refresh(now: datetime) -> None:
        """Ask the coordinator to refresh at the configured local time."""
        hass.async_create_task(coordinator.async_request_refresh())

    unsub_schedule = async_track_time_change(
        hass, _scheduled_refresh, hour=hour, minute=minute, second=0
    )
    entry.async_on_unload(unsub_schedule)
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload the entry when its update time changes."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a EuroOil station."""
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unloaded
