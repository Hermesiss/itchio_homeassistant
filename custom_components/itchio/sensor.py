"""Sensors for Itch.io Integration."""
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from .const import DOMAIN, SENSOR_TYPES

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    """Set up Itch.io sensors based on a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    sensors = []

    for game in coordinator.data.get("games", []):
        for sensor_type in SENSOR_TYPES:
            sensors.append(ItchioSensor(coordinator, game, sensor_type))

    async_add_entities(sensors)

class ItchioSensor(CoordinatorEntity):
    """Representation of an Itch.io Sensor."""

    def __init__(self, coordinator, game, sensor_type):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.game = game
        self.type = sensor_type
        self._name = f"Itch.io {game['title']} {SENSOR_TYPES[sensor_type]['name']}"
        self._unique_id = f"itchio_{game['id']}_{sensor_type}"

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def unique_id(self):
        """Return the unique ID."""
        return self._unique_id

    @property
    def state(self):
        """Return the state of the sensor."""
        game_id = self.game["id"]
        for game in self.coordinator.data.get("games", []):
            if game["id"] == game_id:
                self.game = game
                break
        value = self.game.get(self.type)
        if self.type == "earnings":
            amount = self.game.get("earnings", [{}])[0].get("amount", 0)
            return amount / 100
        return value

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return SENSOR_TYPES[self.type]["unit"]

    @property
    def icon(self):
        """Return the icon."""
        return SENSOR_TYPES[self.type]["icon"]

    @property
    def extra_state_attributes(self):
        """Return extra attributes."""
        return {
            "game_id": self.game.get("id"),
            "title": self.game.get("title"),
            "url": self.game.get("url"),
        }
