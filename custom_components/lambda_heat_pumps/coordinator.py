"""Data update coordinator for Lambda."""
from __future__ import annotations
from datetime import timedelta
import logging
import os
import yaml
import aiofiles
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from .const import (
    SENSOR_TYPES,
    HP_SENSOR_TEMPLATES,
    HP_BASE_ADDRESS,
    BOIL_SENSOR_TEMPLATES,
    BOIL_BASE_ADDRESS,
    BUFFER_SENSOR_TEMPLATES,
    BUFFER_BASE_ADDRESS,
    SOLAR_SENSOR_TEMPLATES,
    SOLAR_BASE_ADDRESS,
    FIRMWARE_VERSION,
)
from .utils import get_compatible_sensors, load_disabled_registers, is_register_disabled

_LOGGER = logging.getLogger(__name__)
SCAN_INTERVAL = timedelta(seconds=30)


class LambdaDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching Lambda data."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry):
        """Initialize."""
        # Lese update_interval aus den Optionen, falls vorhanden
        update_interval = entry.options.get("update_interval", 30)
        _LOGGER.debug("Update interval from options: %s seconds", update_interval)
        _LOGGER.debug("Entry options: %s", entry.options)
        _LOGGER.debug(
            "Room thermostat control: %s",
            entry.options.get("room_thermostat_control", "nicht gefunden"),
        )

        super().__init__(
            hass,
            _LOGGER,
            name="Lambda Coordinator",
            update_interval=timedelta(seconds=update_interval),
        )
        self.host = entry.data["host"]
        self.port = entry.data["port"]
        self.slave_id = entry.data.get("slave_id", 1)
        self.debug_mode = entry.data.get("debug_mode", False)
        if self.debug_mode:
            _LOGGER.setLevel(logging.DEBUG)
        self.client = None
        self.config_entry_id = entry.entry_id
        self.disabled_registers = set()
        self._config_dir = hass.config.config_dir
        self._config_path = os.path.join(self._config_dir, "lambda_heat_pumps")
        # Nutze die lokale Datei im Custom Component-Ordner
        self._disabled_registers_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "disabled_registers.yaml"
        )
        self.hass = hass

    async def async_init(self):
        """Async initialization."""
        _LOGGER.debug("Initializing Lambda coordinator")
        _LOGGER.debug("Config directory: %s", self._config_dir)
        _LOGGER.debug("Config path: %s", self._config_path)
        _LOGGER.debug("Disabled registers path: %s", self._disabled_registers_path)

        try:
            await self._ensure_config_dir()
            _LOGGER.debug("Config directory ensured")

            self.disabled_registers = await load_disabled_registers(self.hass, self._disabled_registers_path)
            _LOGGER.debug("Loaded disabled registers: %s", self.disabled_registers)

            if not self.disabled_registers:
                _LOGGER.debug("No disabled registers configured - this is normal if you haven't disabled any registers")
        except Exception as e:
            _LOGGER.error("Failed to initialize coordinator: %s", str(e))
            self.disabled_registers = set()
            raise

    async def _ensure_config_dir(self):
        """Ensure config directory exists."""
        try:
            def _create_dirs():
                os.makedirs(self._config_dir, exist_ok=True)
                os.makedirs(self._config_path, exist_ok=True)
                _LOGGER.debug("Created directories: %s and %s", self._config_dir, self._config_path)

            await self.hass.async_add_executor_job(_create_dirs)
        except Exception as e:
            _LOGGER.error("Failed to create config directories: %s", str(e))
            raise

    def is_register_disabled(self, address: int) -> bool:
        """Check if a register is disabled."""
        if not hasattr(self, 'disabled_registers'):
            _LOGGER.error("disabled_registers not initialized")
            return False

        # Debug: Ausgabe der Typen und Inhalte
        _LOGGER.debug(
            "Check if address %r (type: %s) is in disabled_registers: %r (types: %r)",
            address, type(address), self.disabled_registers, {type(x) for x in self.disabled_registers}
        )

        is_disabled = is_register_disabled(address, self.disabled_registers)
        if is_disabled:
            _LOGGER.debug("Register %d is disabled (in set: %s)", address, self.disabled_registers)
        else:
            _LOGGER.debug("Register %d is not disabled (checked against set: %s)", address, self.disabled_registers)
        return is_disabled

    async def _async_update_data(self):
        """Fetch data from Lambda device."""
        from pymodbus.client import ModbusTcpClient
        from pymodbus.exceptions import ModbusException

        entry = self.hass.config_entries.async_get_entry(self.config_entry_id)
        configured_fw = entry.options.get(
            "firmware_version", entry.data.get("firmware_version", "V0.0.4-3K")
        )
        fw_version = int(FIRMWARE_VERSION.get(configured_fw, "1"))

        if not self.client:
            self.client = ModbusTcpClient(self.host, port=self.port)
            if not await self.hass.async_add_executor_job(self.client.connect):
                raise ConnectionError("Could not connect to Modbus TCP")
            _LOGGER.debug(
                "Modbus client initialized for host %s on port %s",
                self.host,
                self.port,
            )

        try:
            data = {}
            # 1. Statische Sensoren abfragen
            _LOGGER.debug("Starting static sensor block...")
            compatible_static_sensors = get_compatible_sensors(SENSOR_TYPES, fw_version)
            _LOGGER.debug("Reading %d compatible static sensors", len(compatible_static_sensors))
            try:
                for sensor_id, sensor_config in compatible_static_sensors.items():
                    # Prüfe ob das Register deaktiviert ist
                    if self.is_register_disabled(sensor_config["address"]):
                        _LOGGER.debug(
                            "Skipping disabled register %d for sensor %s",
                            sensor_config["address"],
                            sensor_id
                        )
                        continue

                    _LOGGER.debug(
                        "Reading static sensor: %s with address: %d",
                        sensor_id,
                        sensor_config["address"],
                    )
                    count = 2 if sensor_config["data_type"] == "int32" else 1
                    result = await self.hass.async_add_executor_job(
                        self.client.read_holding_registers,
                        sensor_config["address"],
                        count,
                        self.slave_id,
                    )
                    if result.isError():
                        _LOGGER.warning(
                            "Modbus error for %s (address: %d)",
                            sensor_id,
                            sensor_config["address"]
                        )
                        continue
                    if sensor_config["data_type"] == "int32":
                        raw_value = (result.registers[0] << 16) | result.registers[1]
                    else:
                        raw_value = result.registers[0]
                    scaled_value = raw_value * sensor_config["scale"]
                    data[sensor_id] = scaled_value
            except Exception as ex:
                _LOGGER.error("Exception in static sensor block: %s", ex)
            _LOGGER.debug("Static sensor block finished, entering HP sensor block...")
            # 2. Dynamische HP-Sensoren abfragen
            num_hps = entry.data.get("num_hps", 1)
            compatible_hp_templates = get_compatible_sensors(
                HP_SENSOR_TEMPLATES, fw_version
            )
            for hp_idx in range(1, num_hps + 1):
                _LOGGER.debug("Reading sensors for Heat Pump %s", hp_idx)
                for template_key, template in compatible_hp_templates.items():
                    sensor_id = f"hp{hp_idx}_{template_key}"
                    base_address = HP_BASE_ADDRESS.get(hp_idx)
                    if base_address is None:
                        _LOGGER.warning("No base address for Heat Pump %s", hp_idx)
                        continue
                    address = base_address + template["relative_address"]

                    # Prüfe ob das Register deaktiviert ist
                    if self.is_register_disabled(address):
                        _LOGGER.debug(
                            "Skipping disabled register %d for sensor %s",
                            address,
                            sensor_id
                        )
                        continue

                    count = 2 if template["data_type"] == "int32" else 1
                    try:
                        _LOGGER.debug(
                            "Attempting to read Modbus register for HP sensor %s "
                            "at address %d with count %d",
                            sensor_id,
                            address,
                            count,
                        )
                        result = await self.hass.async_add_executor_job(
                            self.client.read_holding_registers,
                            address,
                            count,
                            self.slave_id,
                        )
                        if result.isError():
                            _LOGGER.warning(
                                "Modbus error for %s (address: %d)",
                                sensor_id,
                                address
                            )
                            continue
                        if template["data_type"] == "int32":
                            raw_value = (result.registers[0] << 16) | result.registers[1]
                        else:
                            raw_value = result.registers[0]
                        scaled_value = raw_value * template["scale"]
                        data[sensor_id] = scaled_value
                    except Exception as ex:
                        _LOGGER.error(
                            "Exception reading HP sensor %s at address %s: %s",
                            sensor_id,
                            address,
                            ex,
                        )
            _LOGGER.debug("HP sensor block finished, entering Boiler sensor block...")
            # 3. Dynamische Boiler-Sensoren abfragen
            num_boil = entry.data.get("num_boil", 1)
            compatible_boil_templates = get_compatible_sensors(
                BOIL_SENSOR_TEMPLATES, fw_version
            )
            for boil_idx in range(1, num_boil + 1):
                _LOGGER.debug("Reading sensors for Boiler %s", boil_idx)
                for template_key, template in compatible_boil_templates.items():
                    sensor_id = f"boil{boil_idx}_{template_key}"
                    base_address = BOIL_BASE_ADDRESS.get(boil_idx)
                    if base_address is None:
                        _LOGGER.warning("No base address for Boiler %s", boil_idx)
                        continue
                    address = base_address + template["relative_address"]

                    # Prüfe ob das Register deaktiviert ist
                    if self.is_register_disabled(address):
                        _LOGGER.debug(
                            "Skipping disabled register %d for sensor %s",
                            address,
                            sensor_id
                        )
                        continue

                    count = 2 if template["data_type"] == "int32" else 1
                    try:
                        _LOGGER.debug(
                            "Attempting to read Modbus register for boiler sensor %s "
                            "at address %d with count %d",
                            sensor_id,
                            address,
                            count,
                        )
                        result = await self.hass.async_add_executor_job(
                            self.client.read_holding_registers,
                            address,
                            count,
                            self.slave_id,
                        )
                        if result.isError():
                            _LOGGER.warning(
                                "Modbus error for %s (address: %d)",
                                sensor_id,
                                address
                            )
                            continue
                        if template["data_type"] == "int32":
                            raw_value = (result.registers[0] << 16) | result.registers[1]
                        else:
                            raw_value = result.registers[0]
                        scaled_value = raw_value * template["scale"]
                        data[sensor_id] = scaled_value
                    except Exception as ex:
                        _LOGGER.error(
                            "Exception reading Boiler sensor %s at address %s: %s",
                            sensor_id,
                            address,
                            ex,
                        )
            _LOGGER.debug("Boiler sensor block finished, entering HC sensor block...")
            # 4. Dynamische HC-Sensoren abfragen
            num_hc = entry.data.get("num_hc", 1)
            from .const import HC_SENSOR_TEMPLATES, HC_BASE_ADDRESS

            compatible_hc_templates = get_compatible_sensors(
                HC_SENSOR_TEMPLATES, fw_version
            )
            for hc_idx in range(1, num_hc + 1):
                _LOGGER.debug("Reading sensors for Heating Circuit %s", hc_idx)
                for template_key, template in compatible_hc_templates.items():
                    sensor_id = f"hc{hc_idx}_{template_key}"
                    address = HC_BASE_ADDRESS.get(hc_idx)
                    if address is None:
                        _LOGGER.warning("No base address for Heating Circuit %s", hc_idx)
                        continue
                    address += template["relative_address"]

                    # Prüfe ob das Register deaktiviert ist
                    if self.is_register_disabled(address):
                        _LOGGER.debug(
                            "Skipping disabled register %d for sensor %s",
                            address,
                            sensor_id
                        )
                        continue

                    count = 2 if template["data_type"] == "int32" else 1
                    try:
                        _LOGGER.debug(
                            "Attempting to read Modbus register for HC sensor %s "
                            "at address %d with count %d",
                            sensor_id,
                            address,
                            count,
                        )
                        result = await self.hass.async_add_executor_job(
                            self.client.read_holding_registers,
                            address,
                            count,
                            self.slave_id,
                        )
                        if result.isError():
                            _LOGGER.warning(
                                "Modbus error for %s (address: %d)",
                                sensor_id,
                                address
                            )
                            continue
                        if template["data_type"] == "int32":
                            raw_value = (result.registers[0] << 16) | result.registers[1]
                        else:
                            raw_value = result.registers[0]
                        scaled_value = raw_value * template["scale"]
                        data[sensor_id] = scaled_value
                    except Exception as ex:
                        _LOGGER.error(
                            "Exception reading HC sensor %s at address %s: %s",
                            sensor_id,
                            address,
                            ex,
                        )

            _LOGGER.debug("HC sensor block finished, entering Buffer sensor block...")
            # 5. Dynamische Buffer-Sensoren abfragen
            num_buffer = entry.data.get("num_buffer", 1)
            compatible_buffer_templates = get_compatible_sensors(
                BUFFER_SENSOR_TEMPLATES, fw_version
            )
            for buffer_idx in range(1, num_buffer + 1):
                _LOGGER.debug("Reading sensors for Buffer %s", buffer_idx)
                for template_key, template in compatible_buffer_templates.items():
                    sensor_id = f"buffer{buffer_idx}_{template_key}"
                    address = BUFFER_BASE_ADDRESS.get(buffer_idx)
                    if address is None:
                        _LOGGER.warning("No base address for Buffer %s", buffer_idx)
                        continue
                    address += template["relative_address"]

                    # Prüfe ob das Register deaktiviert ist
                    if self.is_register_disabled(address):
                        _LOGGER.debug(
                            "Skipping disabled register %d for sensor %s",
                            address,
                            sensor_id
                        )
                        continue

                    count = 2 if template["data_type"] == "int32" else 1
                    try:
                        _LOGGER.debug(
                            "Attempting to read Modbus register for Buffer sensor %s "
                            "at address %d with count %d",
                            sensor_id,
                            address,
                            count,
                        )
                        result = await self.hass.async_add_executor_job(
                            self.client.read_holding_registers,
                            address,
                            count,
                            self.slave_id,
                        )
                        if result.isError():
                            _LOGGER.warning(
                                "Modbus error for %s (address: %d)",
                                sensor_id,
                                address
                            )
                            continue
                        if template["data_type"] == "int32":
                            raw_value = (result.registers[0] << 16) | result.registers[1]
                        else:
                            raw_value = result.registers[0]
                        scaled_value = raw_value * template["scale"]
                        data[sensor_id] = scaled_value
                    except Exception as ex:
                        _LOGGER.error(
                            "Exception reading Buffer sensor %s at address %s: %s",
                            sensor_id,
                            address,
                            ex,
                        )

            _LOGGER.debug(
                "Buffer sensor block finished, entering Solar sensor block..."
            )
            # 6. Dynamische Solar-Sensoren abfragen
            num_solar = entry.data.get("num_solar", 1)
            compatible_solar_templates = get_compatible_sensors(
                SOLAR_SENSOR_TEMPLATES, fw_version
            )
            for solar_idx in range(1, num_solar + 1):
                _LOGGER.debug("Reading sensors for Solar %s", solar_idx)
                for template_key, template in compatible_solar_templates.items():
                    sensor_id = f"solar{solar_idx}_{template_key}"
                    address = SOLAR_BASE_ADDRESS.get(solar_idx)
                    if address is None:
                        _LOGGER.warning("No base address for Solar %s", solar_idx)
                        continue
                    address += template["relative_address"]

                    # Prüfe ob das Register deaktiviert ist
                    if self.is_register_disabled(address):
                        _LOGGER.debug(
                            "Skipping disabled register %d for sensor %s",
                            address,
                            sensor_id
                        )
                        continue

                    count = 2 if template["data_type"] == "int32" else 1
                    try:
                        _LOGGER.debug(
                            "Attempting to read Modbus register for Solar sensor %s "
                            "at address %d with count %d",
                            sensor_id,
                            address,
                            count,
                        )
                        result = await self.hass.async_add_executor_job(
                            self.client.read_holding_registers,
                            address,
                            count,
                            self.slave_id,
                        )
                        if result.isError():
                            _LOGGER.warning(
                                "Modbus error for %s (address: %d)",
                                sensor_id,
                                address
                            )
                            continue
                        if template["data_type"] == "int32":
                            raw_value = (result.registers[0] << 16) | result.registers[1]
                        else:
                            raw_value = result.registers[0]
                        scaled_value = raw_value * template["scale"]
                        data[sensor_id] = scaled_value
                    except Exception as ex:
                        _LOGGER.error(
                            "Exception reading Solar sensor %s at address %s: %s",
                            sensor_id,
                            address,
                            ex,
                        )

            _LOGGER.debug("Solar sensor block finished")
            return data
        except Exception as ex:
            _LOGGER.error("Error updating data: %s", ex)
            raise
