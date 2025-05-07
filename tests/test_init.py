import unittest
from unittest.mock import patch, MagicMock
import logging
from custom_components.lambda_heat_pumps.__init__ import setup_debug_logging, async_setup
from custom_components.lambda_heat_pumps.const import DOMAIN

class TestInit(unittest.TestCase):
    def setUp(self):
        self.hass = MagicMock()
        self.config = {
            DOMAIN: {
                "host": "192.168.1.100",
                "port": 8080,
                "username": "admin",
                "password": "password"
            }
        }

    def test_setup_debug_logging(self):
        with self.assertLogs(level=logging.DEBUG) as log:
            setup_debug_logging()
            self.assertTrue(any("Debug logging enabled" in message for message in log.output))

    @patch("custom_components.lambda_heat_pumps.coordinator.LambdaDataUpdateCoordinator")
    async def test_async_setup(self, mock_coordinator):
        mock_coordinator_instance = MagicMock()
        mock_coordinator.return_value = mock_coordinator_instance

        result = await async_setup(self.hass, self.config)

        self.assertTrue(result)
        mock_coordinator.assert_called_once_with(self.hass, self.config[DOMAIN])
        mock_coordinator_instance.async_refresh.assert_called_once()