"""Test the init module."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.const import CONF_HOST, CONF_PORT

from custom_components.lambda_heat_pumps import (
    DOMAIN,
    async_setup_entry,
    async_unload_entry,
)
from custom_components.lambda_heat_pumps.const import CONF_SLAVE_ID
from custom_components.lambda_heat_pumps.coordinator import LambdaDataUpdateCoordinator

@pytest.fixture
def mock_config_entry():
    """Create a mock config entry."""
    entry = MagicMock(spec=ConfigEntry)
    entry.entry_id = "test"
    entry.data = {
        CONF_HOST: "192.168.1.100",
        CONF_PORT: 502,
        CONF_SLAVE_ID: 1,
    }
    entry.options = {}
    return entry

@pytest.fixture
def mock_hass():
    """Create a mock hass."""
    hass = MagicMock(spec=HomeAssistant)
    hass.data = {}
    hass.config_entries = MagicMock()
    hass.config_entries.async_forward_entry_setups = AsyncMock(return_value=True)
    hass.config_entries.async_unload_platforms = AsyncMock(return_value=True)
    hass.async_add_executor_job = AsyncMock()
    hass.bus = MagicMock()
    hass.bus.async_listen = MagicMock()
    return hass

@pytest.mark.asyncio
async def test_async_setup_entry(mock_hass: HomeAssistant, mock_config_entry):
    """Test async_setup_entry."""
    with patch(
        "custom_components.lambda_heat_pumps.coordinator.LambdaDataUpdateCoordinator"
    ) as mock_coordinator:
        coordinator = AsyncMock()
        coordinator.async_refresh = AsyncMock()
        mock_coordinator.return_value = coordinator
        
        mock_hass.services = MagicMock()
        
        result = await async_setup_entry(mock_hass, mock_config_entry)
        assert result is True
        
        mock_hass.config_entries.async_forward_entry_setups.assert_called_once_with(
            mock_config_entry, ["sensor", "climate"]
        )

@pytest.mark.asyncio
async def test_async_unload_entry(mock_hass: HomeAssistant, mock_config_entry):
    """Test async_unload_entry."""
    coordinator_mock = AsyncMock()
    coordinator_mock.client = MagicMock()
    coordinator_mock.client.close = MagicMock()
    
    # Patch für Home Assistant Services-Mock
    mock_hass.services = MagicMock()
    
    mock_hass.data = {
        DOMAIN: {
            mock_config_entry.entry_id: {
                "coordinator": coordinator_mock,
            }
        }
    }
    
    result = await async_unload_entry(mock_hass, mock_config_entry)
    assert result is True
    
    mock_hass.config_entries.async_unload_platforms.assert_called_once_with(
        mock_config_entry, ["sensor", "climate"]
    )
    mock_hass.async_add_executor_job.assert_called_once_with(coordinator_mock.client.close)

def test_setup_debug_logging():
    """Test setup_debug_logging."""
    with patch("logging.getLogger") as mock_get_logger:
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        
        from custom_components.lambda_heat_pumps.utils import setup_debug_logging
        setup_debug_logging()
        
        mock_get_logger.assert_called_once_with("custom_components.lambda_heat_pumps")
        mock_logger.setLevel.assert_called_once()