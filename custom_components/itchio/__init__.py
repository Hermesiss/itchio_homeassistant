"""Itch.io Integration for Home Assistant."""

from homeassistant.helpers import config_validation as cv
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.const import CONF_API_KEY
from .const import DOMAIN, DEFAULT_SCAN_INTERVAL
from .coordinator import ItchioDataUpdateCoordinator
import logging

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["sensor"]

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

async def async_setup(hass: HomeAssistant, config: dict):
    """Set up the Itch.io component."""
    hass.data.setdefault(DOMAIN, {})
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up Itch.io from a config entry."""
    api_key = entry.data[CONF_API_KEY]
    scan_interval = entry.options.get("scan_interval", DEFAULT_SCAN_INTERVAL)

    coord = ItchioDataUpdateCoordinator(hass, api_key, scan_interval)
    
    try:
        await coord.async_config_entry_first_refresh()
    except Exception as err:
        _LOGGER.error("Failed to setup Itch.io integration: %s", err)
        return False

    hass.data[DOMAIN][entry.entry_id] = coord

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
