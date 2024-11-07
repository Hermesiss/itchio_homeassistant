"""DataUpdateCoordinator for Itch.io Integration."""

from datetime import timedelta
import logging
import aiohttp
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.core import HomeAssistant
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

class ItchioDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching Itch.io data."""

    def __init__(self, hass: HomeAssistant, api_key: str, scan_interval: int):
        """Initialize."""
        self.api_key = api_key
        self.hass = hass
        self.session = aiohttp.ClientSession()
        update_interval = timedelta(minutes=scan_interval)
        super().__init__(
            hass,
            _LOGGER,
            name="Itch.io Data",
            update_interval=update_interval,
        )

    async def _async_update_data(self):
        """Fetch data from Itch.io."""
        url = f"https://itch.io/api/1/{self.api_key}/my-games"
        try:
            async with self.session.get(url) as response:
                if response.status != 200:
                    raise Exception(f"Error fetching data: {response.status}")
                data = await response.json()
                return data
        except Exception as err:
            raise Exception(f"Error communicating with API: {err}") from err

    async def async_close(self):
        """Close the session."""
        await self.session.close()
