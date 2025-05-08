# File: tests/test_climate.py
"""Tests for the Lambda Heat Pumps climate platform."""
import pytest
from unittest.mock import patch, MagicMock
from homeassistant.components.climate import HVACMode
from homeassistant.const import UnitOfTemperature
from custom_components.lambda_heat_pumps.climate import async_setup_entry
from custom_components.lambda_heat_pumps.const import DOMAIN
from pytest_homeassistant_custom_component.common import MockConfigEntry

pytestmark = pytest.mark.asyncio

@pytest.fixture
def mock_config_entry():
    """Create a mock config entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        data={
            "host": "192.168.1.100",
            "port": 502,
            "unit_id": 1,
        },
        entry_id="test_entry_id",
    )

@pytest.fixture
def mock_coordinator():
    """Create a mock coordinator."""
    coordinator = MagicMock()
    coordinator.data = {
        "temperature": 20.0,
        "target_temperature": 22.0,
        "hvac_mode": HVACMode.HEAT,
    }
    return coordinator

@pytest.mark.asyncio
async def test_climate_setup(hass, mock_config_entry, mock_coordinator):
    """Test climate entity setup."""
    hass.data = {DOMAIN: {mock_config_entry.entry_id: {"coordinator": mock_coordinator}}}
    
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

@pytest.mark.asyncio
async def test_lambda_climate_entity_properties():
    """Test properties of LambdaClimateEntity."""
    coordinator_mock = MagicMock()
    coordinator_mock.data = {
        "boil1_actual_high_temperature": 60,
        "boil1_target_high_temperature": 65,
    }
    
    entry_mock = MagicMock(spec=MockConfigEntry)
    entry_mock.entry_id = "test_entry"
    entry_mock.data = {"name": "test"}
    entry_mock.options = {}
    
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
    assert entity is not None
    assert entity._attr_name == "test_hot_water"
    assert entity._attr_unique_id == "test_hot_water_climate"
    assert entity._attr_min_temp == min_temp
    assert entity._attr_max_temp == max_temp
    assert entity._attr_target_temperature_step == temp_step
    assert entity.current_temperature == 60
    assert entity.target_temperature == 65

@pytest.mark.asyncio
async def test_lambda_climate_entity_set_temperature():
    """Test set temperature method of LambdaClimateEntity."""
    coordinator_mock = MagicMock()
    coordinator_mock.data = {}
    coordinator_mock.client = MagicMock()
    coordinator_mock.client.write_register = MagicMock(return_value=MagicMock(isError=lambda: False))
    coordinator_mock.async_refresh = MagicMock()
    
    entry_mock = MagicMock(spec=MockConfigEntry)
    entry_mock.entry_id = "test_entry"
    entry_mock.data = {"name": "test", "slave_id": 1}
    entry_mock.options = {}
    
    hass_mock = MagicMock()
    hass_mock.async_add_executor_job = MagicMock(return_value=MagicMock(isError=lambda: False))
    
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
    entity.hass = hass_mock
    
    await entity.async_set_temperature(temperature=60)
    
    # Überprüfe, ob async_add_executor_job mit den korrekten Parametern aufgerufen wurde
    hass_mock.async_add_executor_job.assert_called_once()
    call_args = hass_mock.async_add_executor_job.call_args[0]
    assert call_args[0] == coordinator_mock.client.write_register
    assert call_args[1] == 2050  # BOIL_BASE_ADDRESS[1] + relative_address von target_high_temperature
    assert call_args[2] == 600  # Temperatur * scale (10.0)
    assert call_args[3] == 1  # slave_id
    
    # Überprüfe, ob der Coordinator-Cache aktualisiert wurde
    assert coordinator_mock.data[target_temp_sensor] == 60
    
    # Überprüfe, ob async_refresh aufgerufen wurde
    coordinator_mock.async_refresh.assert_called_once()

@pytest.mark.asyncio
async def test_lambda_climate_entity_device_info():
    """Test device info method of LambdaClimateEntity."""
    coordinator_mock = MagicMock()
    coordinator_mock.data = {}
    
    entry_mock = MagicMock(spec=MockConfigEntry)
    entry_mock.entry_id = "test_entry"
    entry_mock.data = {"name": "test"}
    entry_mock.options = {}
    
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
    assert device_info is not None
    assert device_info["identifiers"] == {("lambda_heat_pumps", "test_hot_water_1")}
