"""DataUpdateCoordinator for Itch.io Integration."""

from datetime import timedelta
import logging
import aiohttp
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.core import HomeAssistant
from .const import API_BASE_URL, API_TIMEOUT

_LOGGER = logging.getLogger(__name__)

class ItchioDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching Itch.io data."""

    def __init__(self, hass: HomeAssistant, api_key: str, scan_interval: int):
        """Initialize."""
        self.api_key = api_key
        self.hass = hass
        self._last_data = None
        update_interval = timedelta(minutes=scan_interval)
        super().__init__(
            hass,
            _LOGGER,
            name="Itch.io Data",
            update_interval=update_interval,
        )

    async def _async_update_data(self):
        """Fetch data from Itch.io."""
        url = f"{API_BASE_URL}/{self.api_key}/my-games"
        try:
            timeout = aiohttp.ClientTimeout(total=API_TIMEOUT)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url) as response:
                    response.raise_for_status()
                    data = await response.json()
                    self._last_data = data
                    return data
        except aiohttp.ClientError as err:
            _LOGGER.error("Error communicating with API: %s", err)
            if self._last_data is not None:
                _LOGGER.info("Using last known data due to error")
                return self._last_data
            raise UpdateFailed(f"Error communicating with API: {err}") from err
        except Exception as err:
            _LOGGER.error("Unexpected error: %s", err)
            if self._last_data is not None:
                _LOGGER.info("Using last known data due to unexpected error")
                return self._last_data
            raise UpdateFailed(f"Unexpected error: {err}") from err

