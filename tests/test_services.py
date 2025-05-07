"""Test the services module."""
import asyncio
import unittest
from unittest.mock import MagicMock, patch

from custom_components.lambda_heat_pumps.services import async_setup_services


class TestServices(unittest.TestCase):
    """Test the services module."""

    def test_async_setup_services(self):
        """Test async_setup_services."""
        with patch("custom_components.lambda_heat_pumps.services._LOGGER") as mock_logger:
            mock_logger.return_value = MagicMock()
            mock_hass = MagicMock()
            mock_hass.bus = MagicMock()
            result = asyncio.run(async_setup_services(mock_hass))
            self.assertIsNone(result)
            mock_logger.debug.assert_called_with("Service setup completed successfully")