import unittest
from unittest.mock import MagicMock, patch
import asyncio
from lambda_heat_pumps.__init__ import setup_debug_logging, async_setup

class TestInit(unittest.TestCase):
    def test_setup_debug_logging(self):
        with patch("lambda_heat_pumps.__init__.logging.getLogger") as mock_logger:
            mock_logger.return_value = MagicMock()
            setup_debug_logging({}, {"debug": True})
            mock_logger.assert_called_with("lambda_wp")

    def test_async_setup(self):
        with patch("lambda_heat_pumps.__init__.setup_debug_logging") as mock_debug:
            mock_debug.return_value = None
            result = asyncio.run(async_setup({}, {}))
            self.assertTrue(result)
            mock_debug.assert_called_once()