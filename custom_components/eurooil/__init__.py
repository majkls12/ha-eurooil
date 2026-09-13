"""EuroOil / RoBiN OIL integration."""

from __future__ import annotations

from datetime import timedelta
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import EuroOilApi
from .const import (
    CONF_UPDATE_INTERVAL,
    DEFAULT_UPDATE_INTERVAL,
    DOMAIN,
    MAX_UPDATE_INTERVAL,
    MIN_UPDATE_INTERVAL,
)
from .coordinator import EuroOilCoordinator

_LOGGER = logging.getLogger(__name__)
PLATFORMS = [Platform.SENSOR]


def _get_update_interval(value: int | str | None) -> timedelta | None:
    """Return a validated update interval in hours, or None for manual updates."""
    try:
        hours = int(value)
    except (TypeError, ValueError):
        hours = DEFAULT_UPDATE_INTERVAL
    if hours <= 0:
        return None
    return timedelta(hours=min(MAX_UPDATE_INTERVAL, hours))


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the EuroOil integration."""
    hass.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up a configured EuroOil station."""
    coordinator = EuroOilCoordinator(
        hass,
        entry,
        EuroOilApi(async_get_clientsession(hass)),
        _get_update_interval(entry.options.get(CONF_UPDATE_INTERVAL)),
    )
    await coordinator.async_config_entry_first_refresh()
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
