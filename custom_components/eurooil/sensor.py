"""Sensors for EuroOil / RoBiN OIL stations."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Literal

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfVolume
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from .const import DOMAIN
from .coordinator import EuroOilCoordinator


@dataclass(frozen=True, kw_only=True)
class EuroOilSensorDescription(SensorEntityDescription):
    """Describe a EuroOil value."""

    ean: str
    value_kind: Literal["price", "bio", "delivery", "last_update"]


SENSORS: tuple[EuroOilSensorDescription, ...] = (
    EuroOilSensorDescription(key="last_update", name="Poslední aktualizace dat", icon="mdi:update", ean="", value_kind="last_update", device_class=SensorDeviceClass.TIMESTAMP),
    EuroOilSensorDescription(key="natural_95_price", name="Natural 95 cena", icon="mdi:gas-station", ean="4", value_kind="price", native_unit_of_measurement="Kč/l"),
    EuroOilSensorDescription(key="super_98_price", name="Super 98 cena", icon="mdi:gas-station", ean="5", value_kind="price", native_unit_of_measurement="Kč/l"),
    EuroOilSensorDescription(key="diesel_price", name="Diesel bez biosložky cena", icon="mdi:gas-station", ean="1", value_kind="price", native_unit_of_measurement="Kč/l"),
    EuroOilSensorDescription(key="diesel_plus_price", name="Diesel bez biosložky Plus cena", icon="mdi:gas-station", ean="9", value_kind="price", native_unit_of_measurement="Kč/l"),
    EuroOilSensorDescription(key="lpg_price", name="LPG cena", icon="mdi:gas-station", ean="8", value_kind="price", native_unit_of_measurement="Kč/l"),
    EuroOilSensorDescription(key="natural_95_bioethanol", name="Natural 95 obsah biolihu", icon="mdi:leaf", ean="4", value_kind="bio", native_unit_of_measurement="%"),
    EuroOilSensorDescription(key="super_98_bioethanol", name="Super 98 obsah biolihu", icon="mdi:leaf", ean="5", value_kind="bio", native_unit_of_measurement="%"),
    EuroOilSensorDescription(key="natural_95_delivery", name="Natural 95 poslední závoz", icon="mdi:truck-delivery", ean="4", value_kind="delivery", device_class=SensorDeviceClass.TIMESTAMP),
    EuroOilSensorDescription(key="super_98_delivery", name="Super 98 poslední závoz", icon="mdi:truck-delivery", ean="5", value_kind="delivery", device_class=SensorDeviceClass.TIMESTAMP),
    EuroOilSensorDescription(key="diesel_delivery", name="Diesel bez biosložky poslední závoz", icon="mdi:truck-delivery", ean="1", value_kind="delivery", device_class=SensorDeviceClass.TIMESTAMP),
    EuroOilSensorDescription(key="diesel_plus_delivery", name="Diesel bez biosložky Plus poslední závoz", icon="mdi:truck-delivery", ean="9", value_kind="delivery", device_class=SensorDeviceClass.TIMESTAMP),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up station sensors."""
    coordinator: EuroOilCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(EuroOilSensor(coordinator, description) for description in SENSORS)


class EuroOilSensor(CoordinatorEntity[EuroOilCoordinator], SensorEntity):
    """Expose one public EuroOil station value."""

    entity_description: EuroOilSensorDescription
    _attr_has_entity_name = True

    def __init__(
        self, coordinator: EuroOilCoordinator, description: EuroOilSensorDescription
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{coordinator.station_id}_{description.key}"
        self._attr_device_info = coordinator.device_info
        if description.value_kind == "price":
            self._attr_suggested_display_precision = 2

    @property
    def available(self) -> bool:
        """Only expose values for products sold by the selected station."""
        if not super().available or self.coordinator.data is None:
            return False
        if self.entity_description.value_kind == "last_update":
            return self.coordinator.last_update_success_time is not None
        source = "prices" if self.entity_description.value_kind == "price" else "quality"
        return self.entity_description.ean in self.coordinator.data[source]

    @property
    def native_value(self) -> float | datetime | None:
        """Return the normalized API value."""
        if not self.available:
            return None
        ean = self.entity_description.ean
        kind = self.entity_description.value_kind
        if kind == "last_update":
            return self.coordinator.last_update_success_time
        if kind == "price":
            return self.coordinator.data["prices"][ean].get("prodejniCena")
        if kind == "delivery":
            return dt_util.parse_datetime(self.coordinator.data["quality"][ean].get("datumZavozu"))

        quality = self.coordinator.data["quality"][ean]
        # The quality API groups every gasoline grade under code 4, including EAN 5.
        code = "4-2" if ean in {"4", "5"} else "1-2"
        value = next(
            (item.get("hodnota") for item in quality.get("hodnoty", []) if item.get("kod") == code),
            None,
        )
        return value

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Expose the source timestamp for price and quality data."""
        if self.coordinator.data is None:
            return None
        if self.entity_description.value_kind == "last_update":
            return None
        if self.entity_description.value_kind == "price":
            item = self.coordinator.data["prices"].get(self.entity_description.ean)
            return {"aktualizovano": item.get("aktualizovano")} if item else None
        if self.entity_description.value_kind == "bio":
            item = self.coordinator.data["quality"].get(self.entity_description.ean)
            return {"datum_zavozu": item.get("datumZavozu")} if item else None
        return None
