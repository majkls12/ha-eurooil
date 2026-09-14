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
from homeassistant.util import dt as dt_util

from .const import DOMAIN
from .coordinator import EuroOilCoordinator


@dataclass(frozen=True, kw_only=True)
class Product:
    """Known product labels used by the Srdcovka application."""

    key: str
    name: str


# The API identifies fuels by EAN. Keep established keys for existing entities.
KNOWN_PRODUCTS: dict[str, Product] = {
    "1": Product(key="diesel", name="Diesel"),
    "4": Product(key="natural_95", name="Natural 95"),
    "5": Product(key="super_98", name="BA 98 Super+"),
    "8": Product(key="lpg", name="LPG PB"),
    "9": Product(key="diesel_plus", name="Diesel Plus"),
    "6": Product(key="adblue", name="AdBlue"),
}

QUALITY_VALUES: dict[str, tuple[str, str, str, str]] = {
    # code: (key suffix, entity name, icon, unit)
    "1-1": ("density", "Hustota", "mdi:weight-kilogram", "kg/m³"),
    "1-2": ("bio", "Obsah biosložky", "mdi:leaf", "%"),
    "1-4": ("flash_point", "Bod vzplanutí", "mdi:thermometer-alert", "°C"),
    "4-1": ("density", "Hustota", "mdi:weight-kilogram", "kg/m³"),
    "4-2": ("bioethanol", "Obsah biolihu", "mdi:leaf", "%"),
    "4-3": ("distillation_end", "Konec destilace", "mdi:thermometer-lines", "°C"),
}


@dataclass(frozen=True, kw_only=True)
class EuroOilSensorDescription(SensorEntityDescription):
    """Describe a EuroOil value."""

    ean: str = ""
    value_kind: Literal["price", "quality", "delivery", "last_update"]
    quality_code: str | None = None


def _product_for(ean: str, price: dict[str, Any]) -> Product:
    """Return an application label, with a useful fallback for new products."""
    if ean in KNOWN_PRODUCTS:
        return KNOWN_PRODUCTS[ean]
    name = next(
        (
            price.get(field)
            for field in ("nazev", "nazevPaliva", "produkt", "productName")
            if price.get(field)
        ),
        None,
    )
    return Product(key=f"product_ean_{ean}", name=str(name or f"Palivo EAN {ean}"))


def _sensor_descriptions(data: dict[str, Any]) -> list[EuroOilSensorDescription]:
    """Build sensors from fuels actually sold by the selected station."""
    descriptions = [
        EuroOilSensorDescription(
            key="last_update",
            name="Poslední aktualizace dat",
            icon="mdi:update",
            value_kind="last_update",
            device_class=SensorDeviceClass.TIMESTAMP,
        )
    ]

    for ean, price in sorted(data.get("prices", {}).items()):
        product = _product_for(ean, price)
        descriptions.append(
            EuroOilSensorDescription(
                key=f"{product.key}_price",
                name=f"{product.name} cena",
                icon="mdi:gas-station",
                ean=ean,
                value_kind="price",
                native_unit_of_measurement="Kč/l",
            )
        )
        quality = data.get("quality", {}).get(ean)
        if not quality:
            continue
        descriptions.append(
            EuroOilSensorDescription(
                key=f"{product.key}_delivery",
                name=f"{product.name} poslední závoz",
                icon="mdi:truck-delivery",
                ean=ean,
                value_kind="delivery",
                device_class=SensorDeviceClass.TIMESTAMP,
            )
        )
        for value in quality.get("hodnoty", []):
            code = value.get("kod")
            if code not in QUALITY_VALUES:
                continue
            suffix, label, icon, unit = QUALITY_VALUES[code]
            descriptions.append(
                EuroOilSensorDescription(
                    key=f"{product.key}_{suffix}",
                    name=f"{product.name} {label}",
                    icon=icon,
                    ean=ean,
                    value_kind="quality",
                    quality_code=code,
                    native_unit_of_measurement=unit,
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
    """Expose one public EuroOil station value."""

    entity_description: EuroOilSensorDescription
    _attr_has_entity_name = True

    def __init__(self, coordinator: EuroOilCoordinator, description: EuroOilSensorDescription) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{coordinator.station_id}_{description.key}"
        self._attr_device_info = coordinator.device_info
        if description.value_kind == "price":
            self._attr_suggested_display_precision = 2
        elif description.value_kind == "quality":
            self._attr_suggested_display_precision = 1

    @property
    def available(self) -> bool:
        """Expose only values supplied by the selected station."""
        if not super().available or self.coordinator.data is None:
            return False
        description = self.entity_description
        if description.value_kind == "last_update":
            return self.coordinator.data.get("last_update") is not None
        if description.value_kind == "price":
            return description.ean in self.coordinator.data["prices"]
        if description.value_kind == "delivery":
            return description.ean in self.coordinator.data["quality"]
        return any(
            item.get("kod") == description.quality_code
            for item in self.coordinator.data["quality"].get(description.ean, {}).get("hodnoty", [])
        )

    @property
    def native_value(self) -> float | datetime | None:
        """Return the normalized API value."""
        if not self.available:
            return None
        description = self.entity_description
        if description.value_kind == "last_update":
            return self.coordinator.data.get("last_update")
        if description.value_kind == "price":
            return self.coordinator.data["prices"][description.ean].get("prodejniCena")
        if description.value_kind == "delivery":
            return dt_util.parse_datetime(
                self.coordinator.data["quality"][description.ean].get("datumZavozu")
            )
        return next(
            (
                item.get("hodnota")
                for item in self.coordinator.data["quality"][description.ean].get("hodnoty", [])
                if item.get("kod") == description.quality_code
            ),
            None,
        )

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Expose the source timestamp for price and quality data."""
        if self.coordinator.data is None:
            return None
        description = self.entity_description
        if description.value_kind == "last_update":
            return None
        if description.value_kind == "price":
            item = self.coordinator.data["prices"].get(description.ean)
            return {"aktualizovano": item.get("aktualizovano")} if item else None
        if description.value_kind == "quality":
            item = self.coordinator.data["quality"].get(description.ean)
            return {"datum_zavozu": item.get("datumZavozu")} if item else None
        return None
