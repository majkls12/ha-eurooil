"""Sensors for EuroOil / RoBiN OIL stations."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Literal

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import EuroOilCoordinator


@dataclass(frozen=True, kw_only=True)
class Product:
    """A supported fuel product."""

    key: str
    name: str


# Friendly labels are based on the Srdcovka station catalogue. The catalogue is
# also read at setup, so unknown non-fuel services (PPL, Wi-Fi, car wash …)
# never become price sensors.
FUEL_PRODUCTS: dict[str, Product] = {
    "1": Product(key="diesel", name="Diesel"),
    "3": Product(key="diesel_plus_3", name="Diesel Plus"),
    "4": Product(key="natural_95", name="Natural 95"),
    "5": Product(key="super_98", name="BA 98 Super+"),
    "6": Product(key="ba_91_special", name="BA 91 Special"),
    "8": Product(key="lpg", name="LPG PB"),
    "9": Product(key="diesel_plus", name="Diesel Plus"),
    "11": Product(key="optimal_ba95", name="Optimal BA95"),
    "15": Product(key="cng", name="CNG"),
    "16": Product(key="adblue", name="AdBlue"),
    "204": Product(key="hvo_xtl", name="HVO (XTL)"),
}

QUALITY_ATTRIBUTES = {
    "1-1": "Hustota (kg/m³)",
    "1-2": "Obsah biosložky (%)",
    "1-4": "Bod vzplanutí (°C)",
    "4-1": "Hustota (kg/m³)",
    "4-2": "Obsah biolihu (%)",
    "4-3": "Konec destilace (°C)",
}


@dataclass(frozen=True, kw_only=True)
class EuroOilSensorDescription(SensorEntityDescription):
    """Describe a EuroOil value."""

    ean: str = ""
    value_kind: Literal["price", "last_update"]


def _sensor_descriptions(data: dict[str, Any]) -> list[EuroOilSensorDescription]:
    """Create only one price sensor for every fuel sold by this station."""
    descriptions = [
        EuroOilSensorDescription(
            key="last_update",
            name="Poslední aktualizace dat",
            icon="mdi:update",
            value_kind="last_update",
            device_class=SensorDeviceClass.TIMESTAMP,
        )
    ]
    for ean in sorted(
        data.get("prices", {}),
        key=lambda item: (not item.isdigit(), int(item) if item.isdigit() else item),
    ):
        product = FUEL_PRODUCTS.get(ean)
        if product is None or ean not in data.get("product_names", {}):
            continue
        descriptions.append(
            EuroOilSensorDescription(
                key=product.key,
                name=product.name,
                icon=(
                    "mdi:gas-station-outline"
                    if ean in {"1", "3", "9"}
                    else "mdi:gas-station"
                ),
                ean=ean,
                value_kind="price",
                native_unit_of_measurement="Kč/l",
            )
        )
    return descriptions


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up station sensors."""
    coordinator: EuroOilCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        EuroOilSensor(coordinator, description)
        for description in _sensor_descriptions(coordinator.data or {})
    )


class EuroOilSensor(CoordinatorEntity[EuroOilCoordinator], SensorEntity):
    """Expose a public EuroOil station price."""

    entity_description: EuroOilSensorDescription
    _attr_has_entity_name = True

    def __init__(self, coordinator: EuroOilCoordinator, description: EuroOilSensorDescription) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{coordinator.station_id}_{description.key}"
        self._attr_device_info = coordinator.device_info
        if description.value_kind == "price":
            self._attr_suggested_display_precision = 2

    @property
    def available(self) -> bool:
        """Return whether the source has this value."""
        if not super().available or self.coordinator.data is None:
            return False
        if self.entity_description.value_kind == "last_update":
            return self.coordinator.data.get("last_update") is not None
        return self.entity_description.ean in self.coordinator.data["prices"]

    @property
    def native_value(self) -> float | datetime | None:
        """Return the sensor value."""
        if not self.available:
            return None
        if self.entity_description.value_kind == "last_update":
            return self.coordinator.data.get("last_update")
        return self.coordinator.data["prices"][self.entity_description.ean].get("prodejniCena")

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Expose price validity and fuel-quality details as attributes."""
        if self.coordinator.data is None or self.entity_description.value_kind != "price":
            return None
        ean = self.entity_description.ean
        price = self.coordinator.data["prices"].get(ean)
        if price is None:
            return None
        attributes: dict[str, Any] = {
            "Platnost od": price.get("platnostOd"),
            "Platnost do": price.get("platnostDo"),
            "Aktualizováno": price.get("aktualizovano"),
        }
        quality = self.coordinator.data["quality"].get(ean)
        if not quality:
            return attributes
        attributes["Poslední závoz"] = quality.get("datumZavozu")
        for value in quality.get("hodnoty", []):
            attribute = QUALITY_ATTRIBUTES.get(value.get("kod"))
            if attribute:
                attributes[attribute] = value.get("hodnota")
        return attributes
