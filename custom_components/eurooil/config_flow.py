"""Config flow for EuroOil / RoBiN OIL."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
)

from .api import EuroOilApi, EuroOilApiError
from .const import (
    CONF_ROBIN_OIL,
    CONF_STATION_ADDRESS,
    CONF_STATION_ID,
    CONF_STATION_NAME,
    CONF_UPDATE_INTERVAL,
    DEFAULT_UPDATE_INTERVAL,
    DOMAIN,
    MAX_UPDATE_INTERVAL,
    MIN_UPDATE_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)


def _station_label(station: dict[str, Any]) -> str:
    """Create a useful and unambiguous station label."""
    brand = "RoBiN OIL" if station.get("robinOil") else "EuroOil"
    address = " ".join(
        part for part in (station.get("ulice"), station.get("cislo")) if part
    )
    suffix = f" – {address}" if address else ""
    return f"{brand}: {station.get('nazev')}{suffix}"


class EuroOilConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a EuroOil station setup."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        errors: dict[str, str] = {}
        api = EuroOilApi(async_get_clientsession(self.hass))

        try:
            stations = await api.async_get_stations()
        except EuroOilApiError:
            return self.async_abort(reason="cannot_connect")

        station_map = {str(item["cerpaciStaniceIID"]): item for item in stations}
        if user_input is not None:
            station = station_map.get(user_input[CONF_STATION_ID])
            if station is None:
                errors["base"] = "invalid_station"
            else:
                await self.async_set_unique_id(user_input[CONF_STATION_ID])
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=_station_label(station),
                    data={
                        CONF_STATION_ID: station["cerpaciStaniceIID"],
                        CONF_STATION_NAME: station["nazev"],
                        CONF_STATION_ADDRESS: " ".join(
                            part
                            for part in (station.get("ulice"), station.get("cislo"))
                            if part
                        ),
                        CONF_ROBIN_OIL: station.get("robinOil", False),
                    },
                    options={CONF_UPDATE_INTERVAL: DEFAULT_UPDATE_INTERVAL},
                )

        options = [
            SelectOptionDict(value=station_id, label=_station_label(station))
            for station_id, station in sorted(
                station_map.items(), key=lambda item: _station_label(item[1]).casefold()
            )
        ]
        schema = vol.Schema(
            {
                vol.Required(CONF_STATION_ID): SelectSelector(
                    SelectSelectorConfig(options=options, multiple=False)
                )
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    @staticmethod
    def async_get_options_flow(config_entry: config_entries.ConfigEntry) -> EuroOilOptionsFlow:
        """Return the options flow handler."""
        return EuroOilOptionsFlow()


class EuroOilOptionsFlow(config_entries.OptionsFlow):
    """Handle EuroOil options."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        schema = vol.Schema(
            {
                vol.Required(
                    CONF_UPDATE_INTERVAL,
                    default=self.config_entry.options.get(
                        CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL
                    ),
                ): NumberSelector(
                    NumberSelectorConfig(
                        min=MIN_UPDATE_INTERVAL,
                        max=MAX_UPDATE_INTERVAL,
                        step=1,
                        mode=NumberSelectorMode.BOX,
                    )
                )
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema, errors=errors)
