"""Config flow for Itch.io integration."""
from homeassistant import config_entries
from homeassistant.core import callback
import voluptuous as vol
from .const import DOMAIN
import aiohttp

class ItchioConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Itch.io."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            api_key = user_input.get("api_key")
            scan_interval = user_input.get("scan_interval", 5)

            await self.async_set_unique_id(api_key)
            self._abort_if_unique_id_configured()

            valid = await self._test_api_key(api_key)
            if valid:
                return self.async_create_entry(title="Itch.io", data=user_input)
            else:
                errors["base"] = "invalid_api_key"

        data_schema = vol.Schema({
            vol.Required("api_key"): str,
            vol.Optional("scan_interval", default=5): vol.All(int, vol.Range(min=5)),
        })

        return self.async_show_form(
            step_id="user", data_schema=data_schema, errors=errors
        )

    async def _test_api_key(self, api_key):
        """Test if the API key is valid."""
        try:
            url = f"https://itch.io/api/1/{api_key}/my-games"
            session = aiohttp.ClientSession()
            async with session.get(url) as response:
                await session.close()
                return response.status == 200
        except Exception:
            return False

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return ItchioOptionsFlowHandler(config_entry)

class ItchioOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle Itch.io options."""

    def __init__(self, config_entry):
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        data_schema = vol.Schema({
            vol.Optional("scan_interval", default=self.config_entry.options.get("scan_interval", 5)): vol.All(int, vol.Range(min=5)),
        })

        return self.async_show_form(step_id="init", data_schema=data_schema)
