import unittest
from unittest.mock import AsyncMock, patch
from lambda_heat_pumps.sensor import LambdaSensor

class TestSensor(unittest.TestCase):
    def test_sensor_initialization(self):
        with patch("lambda_heat_pumps.sensor.CoordinatorEntity") as mock_entity:
            mock_entity.return_value = AsyncMock()
            sensor = LambdaSensor(
                coordinator=mock_entity,
                entry={},
                sensor_id="sensor_1",
                sensor_config={"name": "Test Sensor", "unit": "°C"},
            )
            self.assertEqual(sensor._attr_name, "Test Sensor")
            self.assertEqual(sensor._attr_native_unit_of_measurement, "°C")