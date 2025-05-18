"""Utility functions for Lambda Heat Pumps integration."""
import logging
import os
import yaml
import aiofiles
from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)

def get_compatible_sensors(sensor_templates: dict, fw_version: int) -> dict:
    """Return only sensors compatible with the given firmware version.
     Args:
        sensor_templates: Dictionary of sensor templates
        fw_version: The firmware version to check against
     Returns:
        Filtered dictionary of compatible sensors
    """
    return {
        k: v
        for k, v in sensor_templates.items()
        if v.get("firmware_version", 1) <= fw_version
    }


def setup_debug_logging():
    """Set up debug logging for the integration."""
    logger = logging.getLogger("custom_components.lambda_heat_pumps")
    logger.setLevel(logging.DEBUG)


def build_device_info(entry, device_type, idx=None, sensor_id=None):
    """
    Build device_info dict for Home Assistant device registry.
    device_type: 'main', 'heat_pump', 'boiler', 'heating_circuit', 'buffer', 'solar',
                 oder für Climate-Entities: 'hot_water_climate', 'heating_circuit_climate' (werden intern gemappt)
    idx: Nummer des Subgeräts (z. B. 1, 2, ...)
    """
    DOMAIN = entry.domain if hasattr(entry, 'domain') else 'lambda_heat_pumps'
    entry_id = entry.entry_id
    fw_version = entry.data.get("firmware_version", "unknown")
    # Climate-Entity-Typen auf Subgeräte mappen
    if device_type == "hot_water_climate":
        device_type = "boiler"
    if device_type == "heating_circuit_climate":
        device_type = "heating_circuit"
    if device_type == "main":
        host = entry.data.get("host")
        return {
            "identifiers": {(DOMAIN, entry_id)},
            "name": entry.data.get("name", "Lambda WP"),
            "manufacturer": "Lambda",
            "model": fw_version,
            "configuration_url": f"http://{host}",
            "sw_version": fw_version,
            "entry_type": None,
            "suggested_area": None,
            "via_device": None,
            "hw_version": None,
            "serial_number": None,
        }
    if device_type == "heat_pump":
        device_id = f"{entry_id}_hp{idx}"
        return {
            "identifiers": {(DOMAIN, device_id)},
            "name": f"Heat Pump {idx}",
            "manufacturer": "Lambda",
            "model": fw_version,
            "via_device": (DOMAIN, entry_id),
            "entry_type": "service",
        }
    if device_type == "boiler":
        device_id = f"{entry_id}_boil{idx}"
        return {
            "identifiers": {(DOMAIN, device_id)},
            "name": f"Boiler {idx}",
            "manufacturer": "Lambda",
            "model": fw_version,
            "via_device": (DOMAIN, entry_id),
            "entry_type": "service",
        }
    if device_type == "heating_circuit":
        device_id = f"{entry_id}_hc{idx}"
        return {
            "identifiers": {(DOMAIN, device_id)},
            "name": f"Heating Circuit {idx}",
            "manufacturer": "Lambda",
            "model": fw_version,
            "via_device": (DOMAIN, entry_id),
            "entry_type": "service",
        }
    if device_type == "buffer":
        device_id = f"{entry_id}_buffer{idx}"
        return {
            "identifiers": {(DOMAIN, device_id)},
            "name": f"Buffer {idx}",
            "manufacturer": "Lambda",
            "model": fw_version,
            "via_device": (DOMAIN, entry_id),
            "entry_type": "service",
        }
    if device_type == "solar":
        device_id = f"{entry_id}_solar{idx}"
        return {
            "identifiers": {(DOMAIN, device_id)},
            "name": f"Solar {idx}",
            "manufacturer": "Lambda",
            "model": fw_version,
            "via_device": (DOMAIN, entry_id),
            "entry_type": "service",
        }
    return None


async def load_disabled_registers(hass: HomeAssistant, config_path: str) -> set[int]:
    """Load disabled registers from YAML file.
    
    Args:
        hass: Home Assistant instance
        config_path: Path to the disabled_registers.yaml file
        
    Returns:
        set[int]: Set of disabled register addresses
    """
    try:
        # Wenn die Datei nicht existiert, erstelle sie mit einem leeren Set
        if not os.path.exists(config_path):
            _LOGGER.debug(
                "Creating new disabled_registers.yaml file at %s",
                config_path,
            )
            try:
                async with aiofiles.open(config_path, "w") as file:
                    await file.write(yaml.dump({"disabled_registers": []}))
                _LOGGER.debug("Successfully created new disabled_registers.yaml file")
            except Exception as e:
                _LOGGER.error(
                    "Failed to create disabled_registers.yaml file: %s",
                    str(e),
                )
                raise
            return set()

        # Lade die deaktivierten Register aus der YAML-Datei
        try:
            _LOGGER.debug(
                "Trying to load disabled_registers.yaml from path: %s",
                config_path,
            )
            async with aiofiles.open(config_path, "r") as file:
                content = await file.read()
                _LOGGER.debug(
                    "Content of disabled_registers.yaml: %r",
                    content,
                )
                config = yaml.safe_load(content)
                if config and "disabled_registers" in config:
                    # Typkonvertierung: Alle Adressen zu int
                    disabled_registers = set(int(x) for x in config["disabled_registers"])
                    _LOGGER.debug(
                        "Loaded %d disabled registers from %s: %s (types: %s)",
                        len(disabled_registers),
                        config_path,
                        disabled_registers,
                        {type(x) for x in disabled_registers},
                    )
                    return disabled_registers
                else:
                    _LOGGER.warning(
                        "No disabled registers found in %s or wrong format! Content: %r",
                        config_path,
                        content,
                    )
                    return set()
        except yaml.YAMLError as e:
            _LOGGER.error(
                "YAML parsing error in %s: %s",
                config_path,
                str(e),
            )
            raise
        except Exception as e:
            _LOGGER.error(
                "Error reading disabled_registers.yaml: %s",
                str(e),
            )
            raise
    except Exception as e:
        _LOGGER.error(
            "Error loading disabled registers from %s: %s",
            config_path,
            str(e),
        )
        raise

def is_register_disabled(address: int, disabled_registers: set[int]) -> bool:
    """Check if a register is disabled.
    
    Args:
        address: The register address to check
        disabled_registers: Set of disabled register addresses
        
    Returns:
        bool: True if the register is disabled, False otherwise
    """
    is_disabled = address in disabled_registers
    if is_disabled:
        _LOGGER.debug("Register %d is disabled (in set: %s)", address, disabled_registers)
    return is_disabled
