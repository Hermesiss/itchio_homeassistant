"""Device representation for Itch.io Integration."""
from homeassistant.helpers.device_registry import DeviceInfo
from .const import DOMAIN


def get_device_info(game_data: dict) -> DeviceInfo:
    """Get device info for a game."""
    return DeviceInfo(
        identifiers={(DOMAIN, str(game_data["id"]))},
        name=f"Itch.io Game: {game_data['title']}",
        manufacturer="Itch.io",
        model="Game",
        sw_version=game_data.get("version", "Unknown"),
        configuration_url=game_data.get("url"),
    ) 