"""Constants for the Itch.io integration."""
DOMAIN = "itchio"
CONF_SCAN_INTERVAL = "scan_interval"

# Default values
DEFAULT_SCAN_INTERVAL = 5
MIN_SCAN_INTERVAL = 5
API_TIMEOUT = 30

# API endpoints
API_BASE_URL = "https://itch.io/api/1"

SENSOR_TYPES = {
    "views_count": {
        "name": "Views",
        "unit": "views",
        "icon": "mdi:eye",
    },
    "downloads_count": {
        "name": "Downloads",
        "unit": "downloads",
        "icon": "mdi:download",
    },
    "purchases_count": {
        "name": "Purchases",
        "unit": "purchases",
        "icon": "mdi:cash",
    },
    "earnings": {
        "name": "Earnings",
        "unit": "USD",
        "icon": "mdi:currency-usd",
    },
}
