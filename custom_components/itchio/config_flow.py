"""Config flow for Itch.io integration."""
from homeassistant import config_entries
from homeassistant.core import callback
import voluptuous as vol
from .const import DOMAIN, API_BASE_URL, DEFAULT_SCAN_INTERVAL, MIN_SCAN_INTERVAL
import aiohttp
import logging

_LOGGER = logging.getLogger(__name__)

class ItchioConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Itch.io."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            api_key = user_input.get("api_key")
            scan_interval = user_input.get("scan_interval", DEFAULT_SCAN_INTERVAL)

            await self.async_set_unique_id(api_key)
            self._abort_if_unique_id_configured()

            valid = await self._test_api_key(api_key)
            if valid:
                return self.async_create_entry(title="Itch.io", data=user_input)
            else:
                errors["base"] = "invalid_api_key"

        data_schema = vol.Schema({
            vol.Required("api_key"): str,
            vol.Optional("scan_interval", default=DEFAULT_SCAN_INTERVAL): vol.All(int, vol.Range(min=MIN_SCAN_INTERVAL)),
        })

        return self.async_show_form(
            step_id="user", data_schema=data_schema, errors=errors
        )

    async def _test_api_key(self, api_key):
        """Test if the API key is valid."""
        try:
            url = f"{API_BASE_URL}/{api_key}/my-games"
            timeout = aiohttp.ClientTimeout(total=10)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url) as response:
                    return response.status == 200
        except aiohttp.ClientError as err:
            _LOGGER.error("API key validation failed: %s", err)
            return False
        except Exception as err:
            _LOGGER.error("Unexpected error during API key validation: %s", err)
            return False

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return ItchioOptionsFlowHandler()

class ItchioOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle Itch.io options."""

    def __init__(self):
        """Initialize options flow."""

    async def async_step_init(self, user_input=None):
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        data_schema = vol.Schema({
            vol.Optional("scan_interval", default=self.config_entry.options.get("scan_interval", DEFAULT_SCAN_INTERVAL)): vol.All(int, vol.Range(min=MIN_SCAN_INTERVAL)),
        })

        return self.async_show_form(step_id="init", data_schema=data_schema)
