import unittest
from unittest.mock import AsyncMock, patch
from lambda_heat_pumps.config_flow import LambdaConfigFlow
import asyncio

class TestConfigFlow(unittest.TestCase):
    def test_validate_input(self):
        with patch("lambda_heat_pumps.config_flow.validate_input", new_callable=AsyncMock) as mock_validate:
            mock_validate.return_value = None
            result = asyncio.run(mock_validate({}, {"host": "127.0.0.1"}))
            self.assertIsNone(result)