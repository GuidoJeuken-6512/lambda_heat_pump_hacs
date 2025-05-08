"""Test constants."""
import unittest
from custom_components.lambda_heat_pumps.const import DOMAIN, DEFAULT_NAME

class TestConst(unittest.TestCase):
    """Test constants."""

    def test_constants(self):
        """Test constants."""
        self.assertEqual(DOMAIN, "lambda_heat_pumps")
        self.assertEqual(DEFAULT_NAME, "EU08L")