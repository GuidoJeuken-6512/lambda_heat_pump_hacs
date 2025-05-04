import unittest
from lambda_heat_pumps.const import DOMAIN, DEFAULT_NAME

class TestConst(unittest.TestCase):
    def test_constants(self):
        self.assertEqual(DOMAIN, "lambda")
        self.assertEqual(DEFAULT_NAME, "EU08L")