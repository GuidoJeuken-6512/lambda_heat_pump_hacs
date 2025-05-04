"""Data update coordinator for Lambda."""
from __future__ import annotations
from datetime import timedelta
import logging
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
    FIRMWARE_VERSION
)
from .utils import get_compatible_sensors

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
        _LOGGER.debug("Room thermostat control: %s", entry.options.get("room_thermostat_control", "nicht gefunden"))

        super().__init__(
            hass,
            _LOGGER,
            name="Lambda Coordinator",
            update_interval=timedelta(seconds=update_interval)
        )
        self.host = entry.data["host"]
        self.port = entry.data["port"]
        self.slave_id = entry.data.get("slave_id", 1)
        self.debug_mode = entry.data.get("debug_mode", False)
        if self.debug_mode:
            _LOGGER.setLevel(logging.DEBUG)
        self.client = None
        self.config_entry_id = entry.entry_id

    async def _async_update_data(self):
        """Fetch data from Lambda device."""
        from pymodbus.client import ModbusTcpClient
        from pymodbus.exceptions import ModbusException
        
        entry = self.hass.config_entries.async_get_entry(self.config_entry_id)
        configured_fw = entry.options.get("firmware_version", entry.data.get("firmware_version", "V0.0.4-3K"))
        fw_version = int(FIRMWARE_VERSION.get(configured_fw, "1"))
        
        if not self.client:
            self.client = ModbusTcpClient(self.host, port=self.port)
            if not await self.hass.async_add_executor_job(self.client.connect):
                raise ConnectionError("Could not connect to Modbus TCP")
            _LOGGER.debug("Modbus client initialized for host %s on port %s", self.host, self.port)

        try:
            data = {}
            # 1. Statische Sensoren abfragen
            _LOGGER.debug("Starting static sensor block...")
            static_sensor_count = len(SENSOR_TYPES)
            _LOGGER.debug("Reading %d static sensors", static_sensor_count)
            try:
                for sensor_id, sensor_config in SENSOR_TYPES.items():
                    _LOGGER.debug("Reading static sensor: %s with address: %d", sensor_id, sensor_config["address"])
                    count = 2 if sensor_config["data_type"] == "int32" else 1
                    result = await self.hass.async_add_executor_job(
                        self.client.read_holding_registers,
                        sensor_config["address"],
                        count,
                        self.slave_id
                    )
                    if result.isError():
                        _LOGGER.warning(f"Modbus error for {sensor_id}")
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
            compatible_hp_templates = get_compatible_sensors(HP_SENSOR_TEMPLATES, fw_version)
            for hp_idx in range(1, num_hps + 1):
                _LOGGER.debug("Reading sensors for HP %s", hp_idx)
                for template_key, template in compatible_hp_templates.items():
                    _LOGGER.debug("HP %s, template_key: %s", hp_idx, template_key)
                    sensor_id = f"hp{hp_idx}_{template_key}"
                    address = HP_BASE_ADDRESS.get(hp_idx)
                    if address is None:
                        _LOGGER.warning("No base address for HP %s", hp_idx)
                        continue
                    address += HP_SENSOR_TEMPLATES[template_key]["relative_address"]
                    count = 2 if HP_SENSOR_TEMPLATES[template_key]["data_type"] == "int32" else 1
                    try:
                        _LOGGER.debug("Attempting to read Modbus register for sensor %s at address %d with count %d", sensor_id, address, count)
                        result = await self.hass.async_add_executor_job(
                            self.client.read_holding_registers,
                            address,
                            count,
                            self.slave_id
                        )
                        if result.isError():
                            _LOGGER.warning(f"Modbus error for {sensor_id}")
                            continue
                        if HP_SENSOR_TEMPLATES[template_key]["data_type"] == "int32":
                            raw_value = (result.registers[0] << 16) | result.registers[1]
                        else:
                            raw_value = result.registers[0]
                        scaled_value = raw_value * HP_SENSOR_TEMPLATES[template_key]["scale"]
                        _LOGGER.debug(
                            "Successfully read %s: %s (raw: %s)",
                            sensor_id, scaled_value, raw_value
                        )
                        data[sensor_id] = scaled_value
                    except Exception as ex:
                        _LOGGER.error("Exception reading HP sensor %s at address %s: %s", sensor_id, address, ex)
            _LOGGER.debug("HP sensor block finished, entering Boiler sensor block...")
            # 3. Dynamische Boiler-Sensoren abfragen
            num_boil = entry.data.get("num_boil", 1)
            compatible_boil_templates = get_compatible_sensors(BOIL_SENSOR_TEMPLATES, fw_version)
            for boil_idx in range(1, num_boil + 1):
                _LOGGER.debug("Reading sensors for Boiler %s", boil_idx)
                for template_key, template in compatible_boil_templates.items():
                    sensor_id = f"boil{boil_idx}_{template_key}"
                    address = BOIL_BASE_ADDRESS.get(boil_idx)
                    if address is None:
                        _LOGGER.warning("No base address for Boiler %s", boil_idx)
                        continue
                    address += template["relative_address"]
                    count = 2 if template["data_type"] == "int32" else 1
                    try:
                        _LOGGER.debug("Attempting to read Modbus register for boiler sensor %s at address %d with count %d", sensor_id, address, count)
                        result = await self.hass.async_add_executor_job(
                            self.client.read_holding_registers,
                            address,
                            count,
                            self.slave_id
                        )
                        if result.isError():
                            _LOGGER.warning(f"Modbus error for {sensor_id}")
                            continue
                        if template["data_type"] == "int32":
                            raw_value = (result.registers[0] << 16) | result.registers[1]
                        else:
                            raw_value = result.registers[0]
                        scaled_value = raw_value * template["scale"]
                        _LOGGER.debug(
                            "Successfully read %s: %s (raw: %s)",
                            sensor_id, scaled_value, raw_value
                        )
                        data[sensor_id] = scaled_value
                    except Exception as ex:
                        _LOGGER.error("Exception reading Boiler sensor %s at address %s: %s", sensor_id, address, ex)
            _LOGGER.debug("Boiler sensor block finished, entering HC sensor block...")
            # 4. Dynamische HC-Sensoren abfragen
            num_hc = entry.data.get("num_hc", 1)
            from .const import HC_SENSOR_TEMPLATES, HC_BASE_ADDRESS
            compatible_hc_templates = get_compatible_sensors(HC_SENSOR_TEMPLATES, fw_version)
            for hc_idx in range(1, num_hc + 1):
                _LOGGER.debug("Reading sensors for HC %s", hc_idx)
                for template_key, template in compatible_hc_templates.items():
                    sensor_id = f"hc{hc_idx}_{template_key}"
                    address = HC_BASE_ADDRESS.get(hc_idx)
                    if address is None:
                        _LOGGER.warning("No base address for HC %s", hc_idx)
                        continue
                    address += template["relative_address"]
                    count = 2 if template["data_type"] == "int32" else 1
                    try:
                        _LOGGER.debug("Attempting to read Modbus register for HC sensor %s at address %d with count %d", sensor_id, address, count)
                        result = await self.hass.async_add_executor_job(
                            self.client.read_holding_registers,
                            address,
                            count,
                            self.slave_id
                        )
                        if result.isError():
                            _LOGGER.warning(f"Modbus error for {sensor_id}")
                            continue
                        if template["data_type"] == "int32":
                            raw_value = (result.registers[0] << 16) | result.registers[1]
                        else:
                            raw_value = result.registers[0]
                        scaled_value = raw_value * template["scale"]
                        _LOGGER.debug(
                            "Successfully read %s: %s (raw: %s)",
                            sensor_id, scaled_value, raw_value
                        )
                        data[sensor_id] = scaled_value
                    except Exception as ex:
                        _LOGGER.error("Exception reading HC sensor %s at address %s: %s", sensor_id, address, ex)

            _LOGGER.debug("HC sensor block finished, entering Buffer sensor block...")
            # 5. Dynamische Buffer-Sensoren abfragen
            num_buffer = entry.data.get("num_buffer", 1)
            compatible_buffer_templates = get_compatible_sensors(BUFFER_SENSOR_TEMPLATES, fw_version)
            for buffer_idx in range(1, num_buffer + 1):
                _LOGGER.debug("Reading sensors for Buffer %s", buffer_idx)
                for template_key, template in compatible_buffer_templates.items():
                    sensor_id = f"buffer{buffer_idx}_{template_key}"
                    address = BUFFER_BASE_ADDRESS.get(buffer_idx)
                    if address is None:
                        _LOGGER.warning("No base address for Buffer %s", buffer_idx)
                        continue
                    address += template["relative_address"]
                    count = 2 if template["data_type"] == "int32" else 1
                    try:
                        _LOGGER.debug("Attempting to read Modbus register for Buffer sensor %s at address %d with count %d", sensor_id, address, count)
                        result = await self.hass.async_add_executor_job(
                            self.client.read_holding_registers,
                            address,
                            count,
                            self.slave_id
                        )
                        if result.isError():
                            _LOGGER.warning(f"Modbus error for {sensor_id}")
                            continue
                        if template["data_type"] == "int32":
                            raw_value = (result.registers[0] << 16) | result.registers[1]
                        else:
                            raw_value = result.registers[0]
                        scaled_value = raw_value * template["scale"]
                        _LOGGER.debug(
                            "Successfully read %s: %s (raw: %s)",
                            sensor_id, scaled_value, raw_value
                        )
                        data[sensor_id] = scaled_value
                    except Exception as ex:
                        _LOGGER.error("Exception reading Buffer sensor %s at address %s: %s", sensor_id, address, ex)

            _LOGGER.debug("Buffer sensor block finished, entering Solar sensor block...")
            # 6. Dynamische Solar-Sensoren abfragen
            num_solar = entry.data.get("num_solar", 1)
            compatible_solar_templates = get_compatible_sensors(SOLAR_SENSOR_TEMPLATES, fw_version)
            for solar_idx in range(1, num_solar + 1):
                _LOGGER.debug("Reading sensors for Solar %s", solar_idx)
                for template_key, template in compatible_solar_templates.items():
                    sensor_id = f"solar{solar_idx}_{template_key}"
                    address = SOLAR_BASE_ADDRESS.get(solar_idx)
                    if address is None:
                        _LOGGER.warning("No base address for Solar %s", solar_idx)
                        continue
                    address += template["relative_address"]
                    count = 2 if template["data_type"] == "int32" else 1
                    try:
                        _LOGGER.debug("Attempting to read Modbus register for Solar sensor %s at address %d with count %d", sensor_id, address, count)
                        result = await self.hass.async_add_executor_job(
                            self.client.read_holding_registers,
                            address,
                            count,
                            self.slave_id
                        )
                        if result.isError():
                            _LOGGER.warning(f"Modbus error for {sensor_id}")
                            continue
                        if template["data_type"] == "int32":
                            raw_value = (result.registers[0] << 16) | result.registers[1]
                        else:
                            raw_value = result.registers[0]
                        scaled_value = raw_value * template["scale"]
                        _LOGGER.debug(
                            "Successfully read %s: %s (raw: %s)",
                            sensor_id, scaled_value, raw_value
                        )
                        data[sensor_id] = scaled_value
                    except Exception as ex:
                        _LOGGER.error("Exception reading Solar sensor %s at address %s: %s", sensor_id, address, ex)

            _LOGGER.debug("Solar sensor block finished")
            return data
        except ModbusException as ex:
            _LOGGER.error("Modbus error: %s", ex)
            if self.client:
                await self.hass.async_add_executor_job(self.client.close)
                self.client = None
            raise
        except Exception as ex:
            _LOGGER.error("Exception in _async_update_data: %s", ex)
            raise
        finally:
            _LOGGER.debug("End of _async_update_data reached (after Boiler sensor block)")