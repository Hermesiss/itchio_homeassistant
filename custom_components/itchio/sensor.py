"""Sensors for Itch.io Integration."""
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from .const import DOMAIN, SENSOR_TYPES
import datetime
import logging

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    """Set up Itch.io sensors based on a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    sensors = []

    for game in coordinator.data.get("games", []):
        for sensor_type in SENSOR_TYPES:
            sensors.append(ItchioSensor(coordinator, game, sensor_type))
            sensors.append(ItchioDailyChangeSensor(coordinator, game, sensor_type))

    async_add_entities(sensors)


class ItchioSensor(CoordinatorEntity, RestoreEntity):
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
        _LOGGER.debug(f"Itchio: sensor {self._name} state: {self.game.get(self.type)}")
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
        _LOGGER.debug(f"Itchio: daily change sensor {self._name} trying to restore state {state}")
        if state:
            self._previous_value = state.attributes.get('previous_value')
            self._last_update_date = state.attributes.get('last_update_date')
            _LOGGER.debug(
                f"Itchio: daily change sensor {self._name} has been restored with previous value {self._previous_value} and last update date {self._last_update_date}")
        else:
            _LOGGER.debug(f"Itchio: daily change sensor {self._name} has no previous state")

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def unique_id(self):
        """Return the unique ID."""
        return self._unique_id

    def _update_game_data(self, game_id):
        """Update game data from coordinator."""
        for game in self.coordinator.data.get("games", []):
            if game["id"] == game_id:
                self.game = game
                break

    def _get_sensor_value(self, value):
        """Get the numeric value from sensor data, handling earnings structure."""
        if self.type == "earnings" and isinstance(value, list) and len(value) > 0:
            amount = value[0].get("amount", 0)
            return amount / 100
        return value

    @property
    def state(self):
        """Return the state of the sensor."""
        self._update_game_data(self.game["id"])
        raw_current_value = self.game.get(self.type)
        current_value = self._get_sensor_value(raw_current_value)
        current_date = datetime.date.today()

        _LOGGER.debug(
            f"Itchio: daily change sensor {self._name} current value: {current_value}, previous value: {self._previous_value}, "
            f"last update date: {self._last_update_date}, current date: {current_date}")
        
        if str(self._last_update_date) != str(current_date):
            _LOGGER.debug(
                f"Itchio: daily change sensor {self._name} has been reset from {self._previous_value} to {current_value}")
            self._previous_value = current_value
            self._last_update_date = current_date
            return 0

        if current_value is None or self._previous_value is None:
            _LOGGER.warning(
                f"Itchio: daily change sensor {self._name} has None value(s) - current_value: {current_value}, previous_value: {self._previous_value}")
            return 0

        # Handle case where previous_value might be stored as dict/list from before the fix
        if isinstance(self._previous_value, (dict, list)) and self.type == "earnings":
            _LOGGER.debug(f"Itchio: daily change sensor {self._name} converting legacy previous_value format")
            self._previous_value = self._get_sensor_value(self._previous_value)

        if isinstance(current_value, list) and isinstance(self._previous_value, list):
            if len(current_value) == len(self._previous_value):
                daily_change = [curr - prev for curr, prev in zip(current_value, self._previous_value)]
                _LOGGER.debug(f"Itchio: daily change sensor {self._name} calculated daily change as list: {daily_change}")
                return daily_change
            else:
                _LOGGER.warning(
                    f"Itchio: daily change sensor {self._name} has mismatched list lengths - current_value: {current_value}, previous_value: {self._previous_value}")
                return 0

        if isinstance(current_value, (int, float)) and isinstance(self._previous_value, (int, float)):
            _LOGGER.debug(f"Itchio: daily change sensor {self._name} calculating daily change from {self._previous_value} to {current_value}")
            daily_change = current_value - self._previous_value
            return daily_change

        _LOGGER.warning(
            f"Itchio: daily change sensor {self._name} has unsupported types - current_value: {current_value} ({type(current_value)}), previous_value: {self._previous_value} ({type(self._previous_value)})")
        return 0

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
            "previous_value": self._previous_value,
            "last_update_date": self._last_update_date,
        }

    async def async_update(self):
        """Update the sensor state."""
        await self.coordinator.async_request_refresh()
        self.async_write_ha_state()
