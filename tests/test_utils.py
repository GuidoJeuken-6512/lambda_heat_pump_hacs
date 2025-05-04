import unittest
from lambda_heat_pumps.utils import get_compatible_sensors

class TestUtils(unittest.TestCase):
    def test_get_compatible_sensors(self):
        sensors = {
            "sensor_1": {"firmware_version": 1},
            "sensor_2": {"firmware_version": 2},
        }
        result = get_compatible_sensors(sensors, 1)
        self.assertIn("sensor_1", result)
        self.assertNotIn("sensor_2", result)