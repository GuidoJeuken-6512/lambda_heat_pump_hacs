"""Test the climate module."""
import pytest
from unittest.mock import patch, AsyncMock
from homeassistant.const import UnitOfTemperature
from homeassistant.components.climate import HVACMode

from custom_components.lambda_heat_pumps.climate import async_setup_entry


@pytest.mark.asyncio
async def test_climate_setup(hass, mock_config_entry, mock_coordinator):
    """Test climate entity setup."""
    with patch(
        "custom_components.lambda_heat_pumps.climate.LambdaClimateEntity"
    ) as mock_climate:
        mock_climate.return_value = mock_climate
        mock_climate._attr_name = "Test Climate"
        mock_climate._attr_unique_id = "test_climate"
        mock_climate._attr_hvac_mode = HVACMode.HEAT
        mock_climate._attr_hvac_modes = [HVACMode.HEAT]
        mock_climate._attr_min_temp = 5
        mock_climate._attr_max_temp = 35
        mock_climate._attr_target_temperature_step = 0.5
        mock_climate._attr_temperature_unit = UnitOfTemperature.CELSIUS

        await async_setup_entry(hass, mock_config_entry, mock_coordinator)
        assert mock_climate.called 