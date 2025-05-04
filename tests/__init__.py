import sys
from os.path import dirname, abspath

# Add the custom_components directory to the Python path
sys.path.insert(0, abspath(dirname(__file__) + '/../custom_components'))

import asyncio
from unittest.mock import patch, MagicMock
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from custom_components.lambda_heat_pumps.__init__ import (
    async_setup,
    async_setup_entry,
    async_unload_entry,
    async_reload_entry,
)

async def test_async_setup(hass: HomeAssistant):
    config = {}
    result = await async_setup(hass, config)
    assert result is True

async def test_async_setup_entry_success(hass: HomeAssistant):
    entry = MagicMock(spec=ConfigEntry)
    entry.data = {"some_key": "some_value"}

    with patch("custom_components.lambda_heat_pumps.coordinator.LambdaDataUpdateCoordinator") as mock_coordinator:
        mock_instance = mock_coordinator.return_value
        mock_instance.async_refresh.return_value = asyncio.Future()
        mock_instance.async_refresh.set_result(None)

        result = await async_setup_entry(hass, entry)
        assert result is True

async def test_async_setup_entry_failure(hass: HomeAssistant):
    entry = MagicMock(spec=ConfigEntry)
    entry.data = {"some_key": "some_value"}

    with patch("custom_components.lambda_heat_pumps.coordinator.LambdaDataUpdateCoordinator") as mock_coordinator:
        mock_instance = mock_coordinator.return_value
        mock_instance.async_refresh.side_effect = Exception("Failed to refresh")

        result = await async_setup_entry(hass, entry)
        assert result is False

async def test_async_unload_entry_success(hass: HomeAssistant):
    entry = MagicMock(spec=ConfigEntry)
    entry.entry_id = "test_entry_id"
    hass.data["lambda_heat_pumps"] = {
        "test_entry_id": {"coordinator": MagicMock()}
    }

    with patch(
        "custom_components.lambda_heat_pumps.__init__.async_unload_services",
        return_value=True
    ) as mock_async_unload_services:
        result = await async_unload_entry(hass, entry)
        assert result is True
        mock_async_unload_services.assert_called_once()

async def test_async_unload_entry_failure(hass: HomeAssistant):
    entry = MagicMock(spec=ConfigEntry)
    entry.entry_id = "test_entry_id"
    hass.data["lambda_heat_pumps"] = {
        "test_entry_id": {"coordinator": MagicMock()}
    }

    with patch(
        "homeassistant.config_entries.ConfigEntries.async_unload_platforms",
        side_effect=ValueError("Platform not loaded")
    ):
        result = await async_unload_entry(hass, entry)
        assert result is True

async def test_async_reload_entry(hass: HomeAssistant):
    entry = MagicMock(spec=ConfigEntry)

    with patch(
        "custom_components.lambda_heat_pumps.__init__.async_unload_entry",
        return_value=True
    ) as mock_async_unload_entry, patch(
        "custom_components.lambda_heat_pumps.__init__.async_setup_entry",
        return_value=True
    ) as mock_async_setup_entry:
        await async_reload_entry(hass, entry)
        mock_async_unload_entry.assert_called_once_with(hass, entry)
        mock_async_setup_entry.assert_called_once_with(hass, entry)
