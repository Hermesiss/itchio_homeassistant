"""Sensors for Itch.io Integration."""
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from .const import DOMAIN, SENSOR_TYPES
import datetime


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    """Set up Itch.io sensors based on a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    sensors = []

    for game in coordinator.data.get("games", []):
        for sensor_type in SENSOR_TYPES:
            sensors.append(ItchioSensor(coordinator, game, sensor_type))
            sensors.append(ItchioDailyChangeSensor(coordinator, game, sensor_type))

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
        self._update_game_data(game_id)
        return self._get_sensor_value()

    def _update_game_data(self, game_id):
        """Update game data from coordinator."""
        for game in self.coordinator.data.get("games", []):
            if game["id"] == game_id:
                self.game = game
                break

    def _get_sensor_value(self):
        """Get the value of the sensor."""
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

    async def async_update(self):
        """Update the sensor state."""
        await self.coordinator.async_request_refresh()
        self.async_write_ha_state()


class ItchioDailyChangeSensor(CoordinatorEntity, RestoreEntity):
    """Representation of an Itch.io Daily Change Sensor."""

    def __init__(self, coordinator, game, sensor_type):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.game = game
        self.type = sensor_type
        self._name = f"Itch.io {game['title']} Daily Change in {SENSOR_TYPES[sensor_type]['name']}"
        self._unique_id = f"itchio_{game['id']}_{sensor_type}_daily_change"
        self._previous_value = None
        self._last_update_date = None

    async def async_added_to_hass(self):
        """Handle entity which will be added."""
        await super().async_added_to_hass()
        state = await self.async_get_last_state()
        if state:
            self._previous_value = state.attributes.get('previous_value')
            self._last_update_date = state.attributes.get('last_update_date')

    @property
    def state(self):
        """Return the state of the sensor."""
        current_value = self.game.get(self.type)
        current_date = datetime.date.today()

        if self._last_update_date != current_date:
            self._previous_value = current_value
            self._last_update_date = current_date
            return 0

        daily_change = current_value - self._previous_value
        self._previous_value = current_value
        return daily_change

    @property
    def extra_state_attributes(self):
        """Return extra attributes."""
        return {
            "game_id": self.game.get("id"),
            "title": self.game.get("title"),
            "url": self.game.get("url"),
            "previous_value": self._previous_value,
            "last_update_date": self._last_update_date,
        }

    async def async_update(self):
        """Update the sensor state."""
        await self.coordinator.async_request_refresh()
        self.async_write_ha_state()
