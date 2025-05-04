import unittest
from unittest.mock import AsyncMock, patch, MagicMock
from lambda_heat_pumps.coordinator import LambdaDataUpdateCoordinator

class TestCoordinator(unittest.TestCase):
    def test_coordinator_initialization(self):
        with patch("lambda_heat_pumps.coordinator.DataUpdateCoordinator") as mock_coordinator:
            mock_coordinator.return_value = AsyncMock()
            mock_entry = MagicMock()
            mock_entry.options = {"update_interval": 30}
            coordinator = LambdaDataUpdateCoordinator({}, mock_entry)
            self.assertIsNotNone(coordinator)