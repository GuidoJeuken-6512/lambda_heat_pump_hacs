import unittest
from unittest.mock import AsyncMock, patch, MagicMock
from lambda_heat_pumps.climate import LambdaClimateEntity

class TestClimate(unittest.TestCase):
    def test_climate_entity_initialization(self):
        with patch("lambda_heat_pumps.climate.CoordinatorEntity") as mock_entity:
            mock_entity.return_value = AsyncMock()
            mock_entry = MagicMock()
            mock_entry.data = {"name": "Test Climate"}
            entity = LambdaClimateEntity(
                coordinator=mock_entity,
                entry=mock_entry,
                climate_type="hot_water_1",
                translation_key="hot_water",
                current_temp_sensor="sensor_1",
                target_temp_sensor="sensor_2",
                min_temp=10,
                max_temp=50,
                temp_step=1,
            )
            self.assertEqual(entity._attr_min_temp, 10)
            self.assertEqual(entity._attr_max_temp, 50)