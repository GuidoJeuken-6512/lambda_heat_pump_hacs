# File: tests/test_climate.py
"""Test the climate module."""
import pytest
from unittest.mock import patch, AsyncMock
from homeassistant.const import (
    ATTR_TEMPERATURE,
    UnitOfTemperature,
)
from homeassistant.components.climate import HVACMode

from custom_components.lambda_heat_pumps.climate import async_setup_entry


@pytest.mark.asyncio
async def test_climate_setup(hass, mock_config_entry, mock_coordinator):
    """Test climate entity setup."""
    with patch(
        "custom_components.lambda_heat_pumps.climate.LambdaClimateEntity"
    ) as mock_climate:
        instance = mock_climate.return_value
        instance._attr_name = "Test Climate"
        instance._attr_unique_id = "test_climate"
        instance._attr_hvac_mode = HVACMode.HEAT
        instance._attr_hvac_modes = [HVACMode.HEAT]
        instance._attr_min_temp = 5
        instance._attr_max_temp = 35
        instance._attr_target_temperature_step = 0.5
        instance._attr_temperature_unit = UnitOfTemperature.CELSIUS

        await async_setup_entry(hass, mock_config_entry, mock_coordinator)
        assert mock_climate.called


@pytest.mark.asyncio
async def test_lambda_climate_entity_init():
    """Test initialization of LambdaClimateEntity."""
    coordinator_mock = AsyncMock()
    entry_mock = {
        "data": {"name": "test", "slave_id": 1},
        "options": {},
    }
    climate_type = "hot_water_1"
    translation_key = "hot_water"
    current_temp_sensor = "boil1_actual_high_temperature"
    target_temp_sensor = "boil1_target_high_temperature"
    min_temp = 50
    max_temp = 75
    temp_step = 1

    entity = LambdaClimateEntity(
        coordinator=coordinator_mock,
        entry=entry_mock,
        climate_type=climate_type,
        translation_key=translation_key,
        current_temp_sensor=current_temp_sensor,
        target_temp_sensor=target_temp_sensor,
        min_temp=min_temp,
        max_temp=max_temp,
        temp_step=temp_step,
    )

    assert entity._attr_name == "TEST Boil1"
    assert entity._attr_unique_id == "test_boil1_climate"
    assert entity.entity_id == "climate.test_boil1_climate"
    assert entity._attr_min_temp == min_temp
    assert entity._attr_max_temp == max_temp
    assert entity._attr_target_temperature_step == temp_step


@pytest.mark.asyncio
async def test_lambda_climate_entity_properties():
    """Test properties of LambdaClimateEntity."""
    coordinator_mock = AsyncMock()
    entry_mock = {
        "data": {"name": "test"},
        "options": {},
    }
    climate_type = "hot_water_1"
    translation_key = "hot_water"
    current_temp_sensor = "boil1_actual_high_temperature"
    target_temp_sensor = "boil1_target_high_temperature"
    min_temp = 50
    max_temp = 75
    temp_step = 1

    entity = LambdaClimateEntity(
        coordinator=coordinator_mock,
        entry=entry_mock,
        climate_type=climate_type,
        translation_key=translation_key,
        current_temp_sensor=current_temp_sensor,
        target_temp_sensor=target_temp_sensor,
        min_temp=min_temp,
        max_temp=max_temp,
        temp_step=temp_step,
    )

    # Mock coordinator data
    coordinator_mock.data = {
        "boil1_actual_high_temperature": 60,
        "boil1_target_high_temperature": 65,
        "boil1_operating_state": 2,  # Example operating state value
    }

    assert entity.current_temperature == 60
    assert entity.target_temperature == 65

    extra_attributes = entity.extra_state_attributes
    assert extra_attributes["operating_state"] == BOIL_OPERATING_STATE[2]


@pytest.mark.asyncio
async def test_lambda_climate_entity_set_temperature():
    """Test set temperature method of LambdaClimateEntity."""
    coordinator_mock = AsyncMock()
    entry_mock = {
        "data": {"name": "test", "slave_id": 1},
        "options": {},
    }
    climate_type = "hot_water_1"
    translation_key = "hot_water"
    current_temp_sensor = "boil1_actual_high_temperature"
    target_temp_sensor = "boil1_target_high_temperature"
    min_temp = 50
    max_temp = 75
    temp_step = 1

    entity = LambdaClimateEntity(
        coordinator=coordinator_mock,
        entry=entry_mock,
        climate_type=climate_type,
        translation_key=translation_key,
        current_temp_sensor=current_temp_sensor,
        target_temp_sensor=target_temp_sensor,
        min_temp=min_temp,
        max_temp=max_temp,
        temp_step=temp_step,
    )

    # Mock sensor_info for boil1_target_high_temperature
    BOIL_SENSOR_TEMPLATES["boil1_target_high_temperature"] = {
        "scale": 0.5,
        "relative_address": 0x1234,
    }

    with patch(
        "custom_components.lambda_heat_pumps.climate.LambdaClimateEntity.coordinator.client.write_registers"
    ) as mock_write_registers:
        await entity.async_set_temperature(**{ATTR_TEMPERATURE: 70})

        assert mock_write_registers.called_once_with(
            BOIL_BASE_ADDRESS[1] + 0x1234, [140], 1
        )
        assert coordinator_mock.data[target_temp_sensor] == 70


@pytest.mark.asyncio
async def test_lambda_climate_entity_device_info():
    """Test device info method of LambdaClimateEntity."""
    coordinator_mock = AsyncMock()
    entry_mock = {
        "data": {"name": "test"},
        "options": {},
    }
    climate_type = "hot_water_1"
    translation_key = "hot_water"
    current_temp_sensor = "boil1_actual_high_temperature"
    target_temp_sensor = "boil1_target_high_temperature"
    min_temp = 50
    max_temp = 75
    temp_step = 1

    entity = LambdaClimateEntity(
        coordinator=coordinator_mock,
        entry=entry_mock,
        climate_type=climate_type,
        translation_key=translation_key,
        current_temp_sensor=current_temp_sensor,
        target_temp_sensor=target_temp_sensor,
        min_temp=min_temp,
        max_temp=max_temp,
        temp_step=temp_step,
    )

    device_info = entity.device_info
    assert device_info["identifiers"] == {("lambda_heat_pumps", "boiler_1")}
    assert device_info["manufacturer"] == "Lambda"
    assert device_info["model"] == "Boiler 1"
    assert device_info["name"] == "TEST Boil1"
