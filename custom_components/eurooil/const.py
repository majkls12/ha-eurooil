"""Constants for the EuroOil integration."""

from datetime import timedelta

DOMAIN = "eurooil"
PLATFORMS = ["sensor"]

CONF_STATION_ID = "station_id"
CONF_STATION_NAME = "station_name"
CONF_STATION_ADDRESS = "station_address"
CONF_ROBIN_OIL = "robin_oil"
CONF_UPDATE_TIME = "update_time"

DEFAULT_UPDATE_TIME = "06:00"

BASE_URL = "https://srdcovka.eurooil.cz/api/verejne"
STATIONS_URL = f"{BASE_URL}/cerpaci-stanice"
PRICES_URL = f"{BASE_URL}/ceniky"

REQUEST_TIMEOUT = timedelta(seconds=20)
