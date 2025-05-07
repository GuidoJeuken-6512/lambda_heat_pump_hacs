import unittest
from custom_components.lambda_heat_pumps.utils import get_compatible_sensors
from custom_components.lambda_heat_pumps.const import DOMAIN

class TestUtils(unittest.TestCase):
    def test_get_compatible_sensors(self):
        data = {
            "temperature": 20,
            "humidity": 50,
            "pressure": 1013
        }
        sensors = get_compatible_sensors(data)
        self.assertIn("temperature", sensors)
        self.assertIn("humidity", sensors)
        self.assertIn("pressure", sensors)