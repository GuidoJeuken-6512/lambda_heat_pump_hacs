"""Test the sensor module."""
import pytest
from unittest.mock import patch, AsyncMock
from homeassistant.const import UnitOfTemperature
from homeassistant.components.sensor import SensorDeviceClass

from custom_components.lambda_heat_pumps.sensor import async_setup_entry


@pytest.mark.asyncio
async def test_sensor_setup(hass, mock_config_entry, mock_coordinator):
    """Test sensor entity setup."""
    DOMAIN = "lambda_heat_pumps"
    entry_id = getattr(mock_config_entry, 'entry_id', 'test')
    mock_config_entry.options = {}
    hass.data = {DOMAIN: {entry_id: {"coordinator": mock_coordinator}}}

    with patch(
        "custom_components.lambda_heat_pumps.sensor.LambdaSensor"
    ) as mock_sensor:
        mock_sensor._attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS

        await async_setup_entry(hass, mock_config_entry, mock_coordinator)
        assert mock_sensor.called