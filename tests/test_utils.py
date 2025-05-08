"""Test the utils module."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from homeassistant.const import CONF_HOST, CONF_PORT

from custom_components.lambda_heat_pumps.utils import (
    get_compatible_sensors,
    setup_debug_logging,
)
from custom_components.lambda_heat_pumps.const import CONF_SLAVE_ID, SENSOR_TYPES

@pytest.fixture
def mock_config_entry():
    """Create a mock config entry."""
    entry = MagicMock()
    entry.data = {
        CONF_HOST: "192.168.1.100",
        CONF_PORT: 502,
        CONF_SLAVE_ID: 1,
    }
    entry.options = {}
    return entry

def test_get_compatible_sensors():
    """Test get_compatible_sensors."""
    fw_version = "1.0.0"
    sensors = get_compatible_sensors(fw_version)
    assert isinstance(sensors, list)
    assert len(sensors) > 0
    for sensor_id in sensors:
        assert sensor_id in SENSOR_TYPES
        assert SENSOR_TYPES[sensor_id]["firmware_version"] <= fw_version

def test_setup_debug_logging():
    """Test setup_debug_logging."""
    mock_logger = MagicMock()
    
    with patch("logging.getLogger", return_value=mock_logger) as mock_get_logger:
        setup_debug_logging()
        
        mock_get_logger.assert_called_once_with("custom_components.lambda_heat_pumps")
        mock_logger.setLevel.assert_called_once()