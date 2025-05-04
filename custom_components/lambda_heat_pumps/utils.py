def get_compatible_sensors(sensor_templates: dict, fw_version: int) -> dict:
    """Filtert und gibt nur die Sensoren zurück, die mit der angegebenen Firmware-Version kompatibel sind."""
    return {k: v for k, v in sensor_templates.items() if v.get("firmware_version", 1) <= fw_version} 