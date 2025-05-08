"""Utility functions for Lambda Heat Pumps integration."""
import logging

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
    # sensor_id argument is unused, kept for interface compatibility
    DOMAIN = entry.domain if hasattr(entry, 'domain') else 'lambda_heat_pumps'
    entry_id = entry.entry_id
    fw_version = entry.data.get("firmware_version", "unknown")
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
