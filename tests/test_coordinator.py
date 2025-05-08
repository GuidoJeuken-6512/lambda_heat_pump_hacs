import unittest
from unittest.mock import AsyncMock, patch, MagicMock
from custom_components.lambda_heat_pumps.coordinator import LambdaDataUpdateCoordinator
from custom_components.lambda_heat_pumps.const import DOMAIN

class TestCoordinator(unittest.TestCase):
    def setUp(self):
        self.hass = MagicMock()
        self.config = {
            "host": "192.168.1.100",
            "port": 8080,
            "username": "admin",
            "password": "password"
        }

    @patch("custom_components.lambda_heat_pumps.coordinator.LambdaAPI")
    async def test_coordinator_update(self, mock_api):
        mock_api_instance = MagicMock()
        mock_api.return_value = mock_api_instance
        mock_api_instance.get_data.return_value = {"temperature": 20}

        coordinator = LambdaDataUpdateCoordinator(self.hass, self.config)
        await coordinator.async_refresh()

        self.assertEqual(coordinator.data, {"temperature": 20})
        mock_api_instance.get_data.assert_called_once()

    def test_coordinator_initialization(self):
        with patch("custom_components.lambda_heat_pumps.coordinator.DataUpdateCoordinator") as mock_coordinator:
            mock_coordinator.return_value = AsyncMock()
            mock_entry = MagicMock()
            mock_entry.options = {"update_interval": 30}
            coordinator = LambdaDataUpdateCoordinator({}, mock_entry)
            self.assertIsNotNone(coordinator)