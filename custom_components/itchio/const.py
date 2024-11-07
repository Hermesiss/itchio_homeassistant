"""Constants for the Itch.io integration."""
DOMAIN = "itchio"
CONF_SCAN_INTERVAL = "scan_interval"

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
