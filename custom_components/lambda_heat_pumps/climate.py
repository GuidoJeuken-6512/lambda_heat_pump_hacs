"""Climate platform for Lambda integration."""
from __future__ import annotations
from typing import Any
import logging

from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    HVACMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_TEMPERATURE, CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN, 
    DEFAULT_NAME, 
    SENSOR_TYPES, 
    FIRMWARE_VERSION, 
    BOIL_SENSOR_TEMPLATES, 
    HC_SENSOR_TEMPLATES,
    BOIL_OPERATING_STATE,
    HC_OPERATING_STATE,
    DEFAULT_HOT_WATER_MIN_TEMP,
    DEFAULT_HOT_WATER_MAX_TEMP,
    DEFAULT_HEATING_CIRCUIT_MIN_TEMP,
    DEFAULT_HEATING_CIRCUIT_MAX_TEMP,
    DEFAULT_HEATING_CIRCUIT_TEMP_STEP,
    DEFAULT_FIRMWARE,
)

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Lambda climate entities."""
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    
    # Hole die Konfigurationsoptionen
    options = entry.options
    
    # Hole die konfigurierte Firmware-Version
    configured_fw = entry.options.get("firmware_version", entry.data.get("firmware_version", DEFAULT_FIRMWARE))
    fw_version = int(FIRMWARE_VERSION.get(configured_fw, "1"))
    
    _LOGGER.debug(
        "Climate Firmware-Version Setup - Configured: %s, Numeric Version: %s, Raw Entry Data: %s",
        configured_fw,
        fw_version,
        entry.data
    )
    
    # Funktion zur Überprüfung der Sensor-Firmware-Kompatibilität
    def is_sensor_compatible(sensor_id: str) -> bool:
        # Prüfe dynamische Boiler-Sensoren
        if sensor_id.startswith("boil"):
            parts = sensor_id.split("_", 1)
            if len(parts) == 2 and parts[1] in BOIL_SENSOR_TEMPLATES:
                template = BOIL_SENSOR_TEMPLATES[parts[1]]
                sensor_fw = template.get("firmware_version", 1)
                is_compatible = sensor_fw <= fw_version
                _LOGGER.debug(
                    "Climate Boiler Sensor Compatibility Check - Sensor: %s, Required FW: %s, Current FW: %s, Compatible: %s",
                    sensor_id,
                    sensor_fw,
                    fw_version,
                    is_compatible
                )
                return is_compatible
            _LOGGER.warning("Boiler sensor template for '%s' not found.", sensor_id)
            return False
        # Prüfe dynamische HC-Sensoren
        if sensor_id.startswith("hc"):
            parts = sensor_id.split("_", 1)
            if len(parts) == 2 and parts[1] in HC_SENSOR_TEMPLATES:
                template = HC_SENSOR_TEMPLATES[parts[1]]
                sensor_fw = template.get("firmware_version", 1)
                is_compatible = sensor_fw <= fw_version
                _LOGGER.debug(
                    "Climate HC Sensor Compatibility Check - Sensor: %s, Required FW: %s, Current FW: %s, Compatible: %s",
                    sensor_id,
                    sensor_fw,
                    fw_version,
                    is_compatible
                )
                return is_compatible
            _LOGGER.warning("HC sensor template for '%s' not found.", sensor_id)
            return False
        # Prüfe statische Sensoren
        sensor_config = SENSOR_TYPES.get(sensor_id)
        if not sensor_config:
            _LOGGER.warning("Sensor '%s' not found in SENSOR_TYPES.", sensor_id)
            return False
        sensor_fw = sensor_config.get("firmware_version", 1)
        is_compatible = sensor_fw <= fw_version
        _LOGGER.debug(
            "Climate Sensor Compatibility Check - Sensor: %s, Required FW: %s, Current FW: %s, Compatible: %s",
            sensor_id,
            sensor_fw,
            fw_version,
            is_compatible
        )
        return is_compatible
        
    entities = []

    # Dynamische Hot Water Entities für alle Boiler
    num_boil = entry.data.get("num_boil", 1)
    for boil_idx in range(1, num_boil + 1):
        hw_current_temp_sensor = f"boil{boil_idx}_actual_high_temperature"
        hw_target_temp_sensor = f"boil{boil_idx}_target_high_temperature"
        if is_sensor_compatible(hw_current_temp_sensor) and is_sensor_compatible(hw_target_temp_sensor):
            entities.append(
                LambdaClimateEntity(
                    coordinator=coordinator,
                    entry=entry,
                    climate_type=f"hot_water_{boil_idx}",
                    translation_key="hot_water",
                    current_temp_sensor=hw_current_temp_sensor,
                    target_temp_sensor=hw_target_temp_sensor,
                    min_temp=options.get("hot_water_min_temp", DEFAULT_HOT_WATER_MIN_TEMP),
                    max_temp=options.get("hot_water_max_temp", DEFAULT_HOT_WATER_MAX_TEMP),
                    temp_step=1
                )
            )

    # Dynamische Heating Circuit Entities für alle Heizkreise
    num_hc = entry.data.get("num_hc", 1)
    for hc_idx in range(1, num_hc + 1):
        hc_current_temp_sensor = f"hc{hc_idx}_room_device_temperature"
        hc_target_temp_sensor = f"hc{hc_idx}_target_room_temperature"
        if is_sensor_compatible(hc_current_temp_sensor) and is_sensor_compatible(hc_target_temp_sensor):
            entities.append(
                LambdaClimateEntity(
                    coordinator=coordinator,
                    entry=entry,
                    climate_type=f"heating_circuit_{hc_idx}",
                    translation_key="heating_circuit",
                    current_temp_sensor=hc_current_temp_sensor,
                    target_temp_sensor=hc_target_temp_sensor,
                    min_temp=options.get("heating_circuit_min_temp", DEFAULT_HEATING_CIRCUIT_MIN_TEMP),
                    max_temp=options.get("heating_circuit_max_temp", DEFAULT_HEATING_CIRCUIT_MAX_TEMP),
                    temp_step=options.get("heating_circuit_temp_step", DEFAULT_HEATING_CIRCUIT_TEMP_STEP)
                )
            )
    
    async_add_entities(entities)

class LambdaClimateEntity(CoordinatorEntity, ClimateEntity):
    """Representation of a Lambda climate entity."""

    _attr_has_entity_name = True
    _attr_should_poll = False
    _attr_temperature_unit = "°C"
    _attr_supported_features = ClimateEntityFeature.TARGET_TEMPERATURE
    _attr_hvac_modes = [HVACMode.HEAT]  # Nur HEAT-Modus
    _attr_hvac_mode = HVACMode.HEAT     # Immer im HEAT-Modus
    _attr_firmware_version = 1

    def __init__(
        self,
        coordinator,
        entry: ConfigEntry,
        climate_type: str,
        translation_key: str,
        current_temp_sensor: str,
        target_temp_sensor: str,
        min_temp: float,
        max_temp: float,
        temp_step: float
    ) -> None:
        """Initialize the climate entity."""
        super().__init__(coordinator)
        self._entry = entry
        self._climate_type = climate_type
        self._current_temp_sensor = current_temp_sensor
        self._target_temp_sensor = target_temp_sensor
        name_prefix = entry.data.get("name", "lambda").lower().replace(" ", "")
        # Name und unique_id nach Schema
        if climate_type.startswith("hot_water"):
            idx = climate_type.split("_")[-1]
            self._attr_name = f"{name_prefix.upper()} Boil{idx}"
            self._attr_unique_id = f"{name_prefix}_boil{idx}_climate"
            self.entity_id = f"climate.{name_prefix}_boil{idx}_climate"
            # Get operating state sensor ID for boiler
            self._operating_state_sensor = f"boil{idx}_operating_state"
        elif climate_type.startswith("heating_circuit"):
            idx = climate_type.split("_")[-1]
            self._attr_name = f"{name_prefix.upper()} HC {idx}"
            self._attr_unique_id = f"{name_prefix}_hc{idx}_climate"
            self.entity_id = f"climate.{name_prefix}_hc{idx}_climate"
            # Get operating state sensor ID for heating circuit
            self._operating_state_sensor = f"hc{idx}_operating_state"
        else:
            self._attr_name = climate_type.capitalize()
            self._attr_unique_id = f"{name_prefix}_{climate_type}_climate"
            self.entity_id = f"climate.{name_prefix}_{climate_type}_climate"
            self._operating_state_sensor = None
        self._attr_min_temp = min_temp
        self._attr_max_temp = max_temp
        self._attr_target_temperature_step = temp_step

    @property
    def current_temperature(self) -> float | None:
        """Return the current temperature."""
        if not self.coordinator.data:
            return None
        return self.coordinator.data.get(self._current_temp_sensor)

    @property
    def target_temperature(self) -> float | None:
        """Return the temperature we try to reach."""
        if not self.coordinator.data:
            return None
        return self.coordinator.data.get(self._target_temp_sensor)

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return entity specific state attributes."""
        if not self.coordinator.data or not self._operating_state_sensor:
            return None

        attributes = {}
        
        # Get the raw operating state value
        operating_state = self.coordinator.data.get(self._operating_state_sensor)
        if operating_state is not None:
            try:
                # Convert to integer for mapping
                state_value = int(operating_state)
                # Map the state value to text based on the climate type
                if self._climate_type.startswith("hot_water"):
                    state_text = BOIL_OPERATING_STATE.get(state_value, f"Unknown state ({state_value})")
                    attributes["operating_state"] = state_text
                elif self._climate_type.startswith("heating_circuit"):
                    state_text = HC_OPERATING_STATE.get(state_value, f"Unknown state ({state_value})")
                    attributes["operating_state"] = state_text
            except (ValueError, TypeError):
                attributes["operating_state"] = f"Invalid state value: {operating_state}"

        return attributes

    @property
    def device_info(self):
        from .const import SENSOR_TYPES, HP_SENSOR_TEMPLATES, BOIL_SENSOR_TEMPLATES, HC_SENSOR_TEMPLATES
        # Hauptgerät für Boiler/HC: climate_type hot_water_X oder heating_circuit_X
        if self._climate_type.startswith("hot_water"):
            idx = self._climate_type.split("_")[-1]
            return {
                "identifiers": {(DOMAIN, f"{self._entry.entry_id}_boil{idx}")},
                "name": f"Boiler {idx}",
                "manufacturer": "Lambda",
                "model": self._entry.data.get("firmware_version", "unknown"),
                "via_device": (DOMAIN, self._entry.entry_id),
                "entry_type": "service"
            }
        if self._climate_type.startswith("heating_circuit"):
            idx = self._climate_type.split("_")[-1]
            return {
                "identifiers": {(DOMAIN, f"{self._entry.entry_id}_hc{idx}")},
                "name": f"Heating Circuit {idx}",
                "manufacturer": "Lambda",
                "model": self._entry.data.get("firmware_version", "unknown"),
                "via_device": (DOMAIN, self._entry.entry_id),
                "entry_type": "service"
            }
        # Fallback: Hauptgerät
        return {
            "identifiers": {(DOMAIN, self._entry.entry_id)},
            "name": self._entry.data.get("name", "Lambda WP"),
            "manufacturer": "Lambda",
            "model": self._entry.data.get("firmware_version", "unknown"),
            "configuration_url": f"http://{self._entry.data.get('host')}",
            "sw_version": self._entry.data.get("firmware_version", "unknown")
        }

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set new target temperature."""
        if (temperature := kwargs.get(ATTR_TEMPERATURE)) is None:
            return

        try:
            # Dynamische Boiler-Sensoren unterstützen
            sensor_info = None
            if self._target_temp_sensor.startswith("boil"):
                parts = self._target_temp_sensor.split("_", 1)
                if len(parts) == 2 and parts[1] in BOIL_SENSOR_TEMPLATES:
                    sensor_info = BOIL_SENSOR_TEMPLATES[parts[1]].copy()
                    idx = int(self._target_temp_sensor[4])
                    from .const import BOIL_BASE_ADDRESS
                    sensor_info["address"] = BOIL_BASE_ADDRESS[idx] + sensor_info["relative_address"]
            elif self._target_temp_sensor.startswith("hc"):
                parts = self._target_temp_sensor.split("_", 1)
                if len(parts) == 2 and parts[1] in HC_SENSOR_TEMPLATES:
                    sensor_info = HC_SENSOR_TEMPLATES[parts[1]].copy()
                    idx = int(self._target_temp_sensor[2])
                    from .const import HC_BASE_ADDRESS
                    sensor_info["address"] = HC_BASE_ADDRESS[idx] + sensor_info["relative_address"]
            else:
                sensor_info = SENSOR_TYPES.get(self._target_temp_sensor)
            if not sensor_info:
                _LOGGER.error("No sensor definition found for %s", self._target_temp_sensor)
                return
            # Berechne den Rohwert für das Register mit der korrekten Skalierung
            raw_value = int(temperature / sensor_info["scale"])
            # Schreibe den Wert in das Modbus-Register
            result = await self.hass.async_add_executor_job(
                self.coordinator.client.write_registers,
                sensor_info["address"],
                [raw_value],
                self._entry.data.get("slave_id", 1)
            )
            if result.isError():
                _LOGGER.error("Failed to write target temperature: %s", result)
                return
            # Aktualisiere den Coordinator-Cache
            self.coordinator.data[self._target_temp_sensor] = temperature
            self.async_write_ha_state()
            _LOGGER.debug("Successfully set target temperature to %s°C", temperature)
        except Exception as ex:
            _LOGGER.error("Error setting target temperature: %s", ex)