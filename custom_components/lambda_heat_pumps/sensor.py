"""Platform for Lambda WP sensor integration."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, DEFAULT_NAME, SENSOR_TYPES, FIRMWARE_VERSION, HP_SENSOR_TEMPLATES, HP_BASE_ADDRESS, BOIL_SENSOR_TEMPLATES, BOIL_BASE_ADDRESS, HC_SENSOR_TEMPLATES, HC_BASE_ADDRESS, BUFFER_SENSOR_TEMPLATES, BUFFER_BASE_ADDRESS, SOLAR_SENSOR_TEMPLATES, SOLAR_BASE_ADDRESS, SOLAR_OPERATION_STATE, BUFFER_OPERATION_STATE, BUFFER_REQUEST_TYPE
from .utils import get_compatible_sensors

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Lambda sensor entries."""
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    
    # Hole die konfigurierte Firmware-Version
    configured_fw = entry.options.get("firmware_version", entry.data.get("firmware_version", "V0.0.4-3K"))
    fw_version = int(FIRMWARE_VERSION.get(configured_fw, "1"))
    
    _LOGGER.debug(
        "Firmware-Version Setup - Configured: %s, Numeric Version: %s, Raw Entry Data: %s, Available Versions: %s",
        configured_fw,
        fw_version,
        entry.data,
        FIRMWARE_VERSION
    )
    
    # Erstelle eine Liste von Sensoren basierend auf der Firmware-Version
    entities = []
    name_prefix = entry.data.get("name", "lambda").lower().replace(" ", "")

    # Statische Sensoren mit Prefix und angepasstem Friendly Name versehen
    compatible_static_sensors = get_compatible_sensors(SENSOR_TYPES, fw_version)
    for sensor_id, sensor_config in compatible_static_sensors.items():
        sensor_fw = sensor_config.get("firmware_version", 1)
        is_compatible = sensor_fw <= fw_version
        _LOGGER.debug(
            "Sensor Compatibility Check - Sensor: %s, Required FW: %s, Current FW: %s, Compatible: %s, Raw Sensor Config: %s",
            sensor_id,
            sensor_fw,
            fw_version,
            is_compatible,
            sensor_config
        )
        # sensor_id bleibt unverändert (ohne Prefix)
        sensor_config_with_name = sensor_config.copy()
        if not sensor_config["name"].upper().startswith(name_prefix.upper()):
            sensor_config_with_name["name"] = f"{name_prefix.upper()} {sensor_config['name']}"
        else:
            sensor_config_with_name["name"] = sensor_config["name"]
        entities.append(
            LambdaSensor(
                coordinator=coordinator,
                entry=entry,
                sensor_id=sensor_id,
                sensor_config=sensor_config_with_name,
            )
        )

    # Dynamische Generierung der HP-Sensoren
    compatible_hp_templates = get_compatible_sensors(HP_SENSOR_TEMPLATES, fw_version)
    num_hps = entry.data.get("num_hps", 1)
    _LOGGER.debug("Starting dynamic sensor generation for %d heat pumps", num_hps)
    for hp_idx in range(1, num_hps + 1):
        for template_key, template in compatible_hp_templates.items():
            # Korrekte sensor_id: <name>_hp<idx>_<template_key>
            sensor_id = f"hp{hp_idx}_{template_key}"
            address = HP_BASE_ADDRESS[hp_idx] + template["relative_address"]
            sensor_config = template.copy()
            sensor_config["address"] = address
            sensor_config["name"] = f"{name_prefix.upper()} HP{hp_idx} {template['name']}"
            _LOGGER.debug("Creating sensor: %s at address: %d", sensor_id, address)
            entities.append(
                LambdaSensor(
                    coordinator=coordinator,
                    entry=entry,
                    sensor_id=sensor_id,
                    sensor_config=sensor_config,
                )
            )
    _LOGGER.debug("Total number of dynamic HP sensors created: %d", len(entities) - len(compatible_static_sensors))

    # Dynamische Generierung der Boiler-Sensoren
    compatible_boil_templates = get_compatible_sensors(BOIL_SENSOR_TEMPLATES, fw_version)
    num_boil = entry.data.get("num_boil", 1)
    _LOGGER.debug("Starting dynamic sensor generation for %d boilers", num_boil)
    for boil_idx in range(1, num_boil + 1):
        for template_key, template in compatible_boil_templates.items():
            # Korrekte sensor_id: <name>_boil<idx>_<template_key>
            sensor_id = f"boil{boil_idx}_{template_key}"
            address = BOIL_BASE_ADDRESS[boil_idx] + template["relative_address"]
            sensor_config = template.copy()
            sensor_config["address"] = address
            orig_name = template["name"].replace("Boiler ", "")
            sensor_config["name"] = f"{name_prefix.upper()} Boil{boil_idx} {orig_name}"
            sensor_config["original_name"] = f"{name_prefix.upper()} Boil{boil_idx} {orig_name}"
            _LOGGER.debug("Creating boiler sensor: %s at address: %d", sensor_id, address)
            entities.append(
                LambdaSensor(
                    coordinator=coordinator,
                    entry=entry,
                    sensor_id=sensor_id,
                    sensor_config=sensor_config,
                )
            )
    _LOGGER.debug("Total number of dynamic Boiler sensors created: %d", len(entities) - len(compatible_static_sensors))

    # Dynamische Generierung der HC-Sensoren
    compatible_hc_templates = get_compatible_sensors(HC_SENSOR_TEMPLATES, fw_version)
    num_hc = entry.data.get("num_hc", 1)
    _LOGGER.debug("Starting dynamic sensor generation for %d heating circuits", num_hc)
    for hc_idx in range(1, num_hc + 1):
        for template_key, template in compatible_hc_templates.items():
            sensor_id = f"hc{hc_idx}_{template_key}"
            address = HC_BASE_ADDRESS[hc_idx] + template["relative_address"]
            sensor_config = template.copy()
            sensor_config["address"] = address
            sensor_config["name"] = f"{name_prefix.upper()} HC{hc_idx} {template['name']}"
            _LOGGER.debug("Creating sensor: %s at address: %d", sensor_id, address)
            entities.append(
                LambdaSensor(
                    coordinator=coordinator,
                    entry=entry,
                    sensor_id=sensor_id,
                    sensor_config=sensor_config,
                )
            )
    _LOGGER.debug("Total number of dynamic HC sensors created: %d", len(entities) - len(compatible_static_sensors) - num_hps * len(compatible_hp_templates) - num_boil * len(compatible_boil_templates))

    # Dynamische Generierung der Buffer-Sensoren
    compatible_buffer_templates = get_compatible_sensors(BUFFER_SENSOR_TEMPLATES, fw_version)
    num_buffer = entry.data.get("num_buffer", 1)
    _LOGGER.debug("Starting dynamic sensor generation for %d buffer modules", num_buffer)
    for buffer_idx in range(1, num_buffer + 1):
        for template_key, template in compatible_buffer_templates.items():
            sensor_id = f"buffer{buffer_idx}_{template_key}"
            address = BUFFER_BASE_ADDRESS.get(buffer_idx, 3000) + template["relative_address"]
            sensor_config = template.copy()
            sensor_config["address"] = address
            sensor_config["name"] = f"{name_prefix.upper()} Buffer{buffer_idx} {template['name']}"
            _LOGGER.debug("Creating buffer sensor: %s at address: %d", sensor_id, address)
            entities.append(
                LambdaSensor(
                    coordinator=coordinator,
                    entry=entry,
                    sensor_id=sensor_id,
                    sensor_config=sensor_config,
                )
            )
    _LOGGER.debug("Total number of dynamic Buffer sensors created: %d", len(entities) - len(compatible_static_sensors) - num_hps * len(compatible_hp_templates) - num_boil * len(compatible_boil_templates) - num_hc * len(compatible_hc_templates))

    # Dynamische Generierung der Solar-Sensoren
    compatible_solar_templates = get_compatible_sensors(SOLAR_SENSOR_TEMPLATES, fw_version)
    num_solar = entry.data.get("num_solar", 1)
    _LOGGER.debug("Starting dynamic sensor generation for %d solar modules", num_solar)
    for solar_idx in range(1, num_solar + 1):
        for template_key, template in compatible_solar_templates.items():
            sensor_id = f"solar{solar_idx}_{template_key}"
            address = SOLAR_BASE_ADDRESS.get(solar_idx, 4000) + template["relative_address"]
            sensor_config = template.copy()
            sensor_config["address"] = address
            sensor_config["name"] = f"{name_prefix.upper()} Solar{solar_idx} {template['name']}"
            _LOGGER.debug("Creating solar sensor: %s at address: %d", sensor_id, address)
            entities.append(
                LambdaSensor(
                    coordinator=coordinator,
                    entry=entry,
                    sensor_id=sensor_id,
                    sensor_config=sensor_config,
                )
            )
    _LOGGER.debug("Total number of dynamic Solar sensors created: %d", len(entities) - len(compatible_static_sensors) - num_hps * len(compatible_hp_templates) - num_boil * len(compatible_boil_templates) - num_hc * len(compatible_hc_templates) - num_buffer * len(compatible_buffer_templates))
    
    async_add_entities(entities)

class LambdaSensor(CoordinatorEntity, SensorEntity):
    """Representation of a Lambda sensor."""

    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(
        self,
        coordinator,
        entry: ConfigEntry,
        sensor_id: str,
        sensor_config: dict[str, Any],
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._entry = entry
        self._sensor_id = sensor_id
        self._config = sensor_config
        self._attr_name = sensor_config["name"]
        self._attr_unique_id = sensor_id
        self.entity_id = f"sensor.{sensor_id}"

        # Verbesserte Erkennung von Zustandssensoren
        # Prüfe zuerst, ob es ein Temperatursensor ist
        if sensor_config.get("unit") == "°C":
            self._is_state_sensor = False
        else:
            # Nur wenn es kein Temperatursensor ist, prüfe auf Zustandssensor
            state_patterns = [
                "_operating_state",
                "_error_state",
                "_operating_mode",
                "ambient_state",
                "hp_state",
                "request_type"
            ]
            self._is_state_sensor = any(pattern in sensor_id for pattern in state_patterns)

        # Setze Attribute basierend auf Sensortyp
        if self._is_state_sensor:
            self._attr_native_unit_of_measurement = None
            self._attr_device_class = None
            self._attr_state_class = None
            # Für Zustandssensoren keine Genauigkeit setzen
        else:
            self._attr_native_unit_of_measurement = sensor_config["unit"]
            # Setze die Genauigkeit für numerische Sensoren
            if "precision" in sensor_config:
                self._attr_suggested_display_precision = sensor_config["precision"]

            # Bestimme die Device-Klasse basierend auf der Einheit
            if sensor_config["unit"] == "°C":
                self._attr_device_class = SensorDeviceClass.TEMPERATURE
            elif sensor_config["unit"] == "W":
                self._attr_device_class = SensorDeviceClass.POWER
            elif sensor_config["unit"] == "Wh":
                self._attr_device_class = SensorDeviceClass.ENERGY
                self._attr_state_class = SensorStateClass.TOTAL_INCREASING

    @property
    def native_value(self) -> float | str | None:
        """Return the state of the sensor."""
        if not self.coordinator.data:
            return None

        value = self.coordinator.data.get(self._sensor_id)
        if value is None:
            return None

        # Check if the sensor is a state sensor and map the value to text using the dictionaries in const.py
        if self._is_state_sensor:
            from .const import (
                AMBIENT_OPERATING_STATE,
                EMGR_OPERATING_STATE,
                HP_ERROR_STATE,
                HP_STATE,
                HP_OPERATING_STATE,
                HP_REQUEST_TYPE,
                BOIL_OPERATING_STATE,
                HC_OPERATING_STATE,
                HC_OPERATING_MODE,
                CIRCULATION_PUMP_STATE,
                SOLAR_OPERATION_STATE,
                BUFFER_OPERATION_STATE,
                BUFFER_REQUEST_TYPE,
            )

            # Ensure value is an integer for state mapping
            try:
                numeric_value = int(value)
            except (ValueError, TypeError):
                return f"Unknown state ({value})"

            # Verbesserte Zuordnung der State-Mappings
            state_mapping = None
            if "ambient_operating_state" in self._sensor_id:
                state_mapping = AMBIENT_OPERATING_STATE
            elif "emgr_operating_state" in self._sensor_id:
                state_mapping = EMGR_OPERATING_STATE
            elif "actual_circulation_pump_state" in self._sensor_id:
                state_mapping = CIRCULATION_PUMP_STATE
            elif "operating_state" in self._sensor_id and "solar" in self._sensor_id:
                state_mapping = SOLAR_OPERATION_STATE
            elif "operating_state" in self._sensor_id and "buffer" in self._sensor_id:
                state_mapping = BUFFER_OPERATION_STATE
            elif "request_type" in self._sensor_id and "buffer" in self._sensor_id:
                state_mapping = BUFFER_REQUEST_TYPE
            elif "error_state" in self._sensor_id:
                state_mapping = HP_ERROR_STATE
            elif "_state" in self._sensor_id:
                if "hp" in self._sensor_id and not "operating" in self._sensor_id:
                    state_mapping = HP_STATE
                elif "hp" in self._sensor_id and "operating" in self._sensor_id:
                    state_mapping = HP_OPERATING_STATE
                elif "boil" in self._sensor_id:
                    state_mapping = BOIL_OPERATING_STATE
                elif "hc" in self._sensor_id:
                    state_mapping = HC_OPERATING_STATE
            elif "operating_mode" in self._sensor_id:
                state_mapping = HC_OPERATING_MODE

            if state_mapping is not None:
                return state_mapping.get(numeric_value, f"Unknown state ({numeric_value})")
            return f"Unknown mapping for state ({numeric_value})"

        # Return the raw value for non-state sensors
        return value

    @property
    def device_class(self) -> str | None:
        """Return the device class of the sensor."""
        if "state" in self._sensor_id or "mode" in self._sensor_id:
            return None  # State/mode sensors do not have a numeric device class
        return super().device_class

    @property
    def state_class(self) -> str | None:
        """Return the state class of the sensor."""
        if "state" in self._sensor_id or "mode" in self._sensor_id:
            return None  # State/mode sensors do not have a numeric state class
        return super().state_class

    @property
    def device_info(self):
        device_type = self._config.get("device_type")
        if device_type == "main":
            return {
                "identifiers": {(DOMAIN, self._entry.entry_id)},
                "name": self._entry.data.get("name", "Lambda WP"),
                "manufacturer": "Lambda",
                "model": self._entry.data.get("firmware_version", "unknown"),
                "configuration_url": f"http://{self._entry.data.get('host')}",
                "sw_version": self._entry.data.get("firmware_version", "unknown"),
                "entry_type": None,
                "suggested_area": None,
                "via_device": None,
                "hw_version": None,
                "serial_number": None
            }
        if device_type == "heat_pump":
            idx = self._sensor_id[2]
            return {
                "identifiers": {(DOMAIN, f"{self._entry.entry_id}_hp{idx}")},
                "name": f"Heat Pump {idx}",
                "manufacturer": "Lambda",
                "model": self._entry.data.get("firmware_version", "unknown"),
                "via_device": (DOMAIN, self._entry.entry_id),
                "entry_type": "service"
            }
        if device_type == "boiler":
            idx = self._sensor_id[4]
            return {
                "identifiers": {(DOMAIN, f"{self._entry.entry_id}_boil{idx}")},
                "name": f"Boiler {idx}",
                "manufacturer": "Lambda",
                "model": self._entry.data.get("firmware_version", "unknown"),
                "via_device": (DOMAIN, self._entry.entry_id),
                "entry_type": "service"
            }
        if device_type == "heating_circuit":
            idx = self._sensor_id[2]
            return {
                "identifiers": {(DOMAIN, f"{self._entry.entry_id}_hc{idx}")},
                "name": f"Heating Circuit {idx}",
                "manufacturer": "Lambda",
                "model": self._entry.data.get("firmware_version", "unknown"),
                "via_device": (DOMAIN, self._entry.entry_id),
                "entry_type": "service"
            }
        if device_type == "buffer":
            idx = self._sensor_id[6]
            return {
                "identifiers": {(DOMAIN, f"{self._entry.entry_id}_buffer{idx}")},
                "name": f"Buffer {idx}",
                "manufacturer": "Lambda",
                "model": self._entry.data.get("firmware_version", "unknown"),
                "via_device": (DOMAIN, self._entry.entry_id),
                "entry_type": "service"
            }
        if device_type == "solar":
            idx = self._sensor_id[5]
            return {
                "identifiers": {(DOMAIN, f"{self._entry.entry_id}_solar{idx}")},
                "name": f"Solar {idx}",
                "manufacturer": "Lambda",
                "model": self._entry.data.get("firmware_version", "unknown"),
                "via_device": (DOMAIN, self._entry.entry_id),
                "entry_type": "service"
            }
        return None