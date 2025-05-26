"""Sensors for Itch.io Integration."""
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.components.sensor import SensorEntity, SensorDeviceClass
from homeassistant.const import EntityCategory
from .const import DOMAIN, SENSOR_TYPES
from .device import get_device_info
import datetime
import logging

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    """Set up Itch.io sensors based on a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    sensors = []

    if not coordinator.data or not coordinator.data.get("games"):
        _LOGGER.warning("No games data available from Itch.io API")
        return

    for game in coordinator.data.get("games", []):
        for sensor_type in SENSOR_TYPES:
            sensors.append(ItchioSensor(coordinator, game, sensor_type))
            sensors.append(ItchioDailyChangeSensor(coordinator, game, sensor_type))

    async_add_entities(sensors)


class ItchioSensor(CoordinatorEntity, SensorEntity):
    """Representation of an Itch.io Sensor."""

    def __init__(self, coordinator, game, sensor_type):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.game = game
        self.type = sensor_type
        self._attr_name = f"Itch.io {game['title']} {SENSOR_TYPES[sensor_type]['name']}"
        self._attr_unique_id = f"itchio_{game['id']}_{sensor_type}"
        self._attr_icon = SENSOR_TYPES[sensor_type]["icon"]
        self._attr_native_unit_of_measurement = SENSOR_TYPES[sensor_type]["unit"]
        self._attr_device_info = get_device_info(game)
        
        # Set device class for monetary sensors
        if sensor_type == "earnings":
            self._attr_device_class = SensorDeviceClass.MONETARY

    @property
    def native_value(self):
        """Return the state of the sensor."""
        try:
            game_id = self.game["id"]
            self._update_game_data(game_id)
            return self._get_sensor_value()
        except Exception as err:
            _LOGGER.error("Error getting sensor value for %s: %s", self._attr_name, err)
            return None

    def _update_game_data(self, game_id):
        """Update game data from coordinator."""
        if not self.coordinator.data or not self.coordinator.data.get("games"):
            return
            
        for game in self.coordinator.data.get("games", []):
            if game["id"] == game_id:
                self.game = game
                break

    def _get_sensor_value(self):
        """Get the value of the sensor."""
        value = self.game.get(self.type)
        if self.type == "earnings" and isinstance(value, list) and len(value) > 0:
            amount = value[0].get("amount", 0)
            return amount / 100
        return value

    @property
    def extra_state_attributes(self):
        """Return extra attributes."""
        return {
            "game_id": self.game.get("id"),
            "title": self.game.get("title"),
            "url": self.game.get("url"),
        }


class ItchioDailyChangeSensor(CoordinatorEntity, RestoreEntity, SensorEntity):
    """Representation of an Itch.io Daily Change Sensor."""

    def __init__(self, coordinator, game, sensor_type):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.game = game
        self.type = sensor_type
        self._attr_name = f"Itch.io {game['title']} Daily Change in {SENSOR_TYPES[sensor_type]['name']}"
        self._attr_unique_id = f"itchio_{game['id']}_{sensor_type}_daily_change"
        self._attr_icon = SENSOR_TYPES[sensor_type]["icon"]
        self._attr_native_unit_of_measurement = SENSOR_TYPES[sensor_type]["unit"]
        self._attr_entity_category = EntityCategory.DIAGNOSTIC
        self._attr_device_info = get_device_info(game)
        self._previous_value = None
        self._last_update_date = None
        
        # Set device class for monetary sensors
        if sensor_type == "earnings":
            self._attr_device_class = SensorDeviceClass.MONETARY

    async def async_added_to_hass(self):
        """Handle entity which will be added."""
        await super().async_added_to_hass()
        state = await self.async_get_last_state()
        _LOGGER.debug("Daily change sensor %s trying to restore state %s", self._attr_name, state)
        if state and state.attributes:
            self._previous_value = state.attributes.get('previous_value')
            self._last_update_date = state.attributes.get('last_update_date')
            _LOGGER.debug(
                "Daily change sensor %s restored with previous value %s and last update date %s",
                self._attr_name, self._previous_value, self._last_update_date)
        else:
            _LOGGER.debug("Daily change sensor %s has no previous state", self._attr_name)

    def _update_game_data(self, game_id):
        """Update game data from coordinator."""
        if not self.coordinator.data or not self.coordinator.data.get("games"):
            return
            
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
    def native_value(self):
        """Return the state of the sensor."""
        try:
            self._update_game_data(self.game["id"])
            raw_current_value = self.game.get(self.type)
            current_value = self._get_sensor_value(raw_current_value)
            current_date = datetime.date.today()

            _LOGGER.debug(
                "Daily change sensor %s current value: %s, previous value: %s, "
                "last update date: %s, current date: %s",
                self._attr_name, current_value, self._previous_value, 
                self._last_update_date, current_date)
            
            if str(self._last_update_date) != str(current_date):
                _LOGGER.debug(
                    "Daily change sensor %s has been reset from %s to %s",
                    self._attr_name, self._previous_value, current_value)
                self._previous_value = current_value
                self._last_update_date = current_date
                return 0

            if current_value is None or self._previous_value is None:
                _LOGGER.warning(
                    "Daily change sensor %s has None value(s) - current_value: %s, previous_value: %s",
                    self._attr_name, current_value, self._previous_value)
                return 0

            # Handle case where previous_value might be stored as dict/list from before the fix
            if isinstance(self._previous_value, (dict, list)) and self.type == "earnings":
                _LOGGER.debug("Daily change sensor %s converting legacy previous_value format", self._attr_name)
                self._previous_value = self._get_sensor_value(self._previous_value)

            if isinstance(current_value, (int, float)) and isinstance(self._previous_value, (int, float)):
                daily_change = current_value - self._previous_value
                _LOGGER.debug("Daily change sensor %s calculated daily change from %s to %s = %s",
                            self._attr_name, self._previous_value, current_value, daily_change)
                return daily_change

            _LOGGER.warning(
                "Daily change sensor %s has unsupported types - current_value: %s (%s), previous_value: %s (%s)",
                self._attr_name, current_value, type(current_value), 
                self._previous_value, type(self._previous_value))
            return 0
        except Exception as err:
            _LOGGER.error("Error calculating daily change for %s: %s", self._attr_name, err)
            return 0

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
