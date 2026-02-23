"""Tests for utils/logger module.

These tests verify logger setup according to Task 1.3b.
"""

import logging
import os
import tempfile
from pathlib import Path

import pytest


class TestLoggerSetup:
    """Test logger initialization."""

    def test_setup_logger_returns_logger_instance(self):
        """setup_logger should return a logging.Logger instance."""
        from utils import logger as logger_module

        with tempfile.TemporaryDirectory() as tmpdir:
            log = logger_module.setup_logger("test_logger", "INFO", tmpdir)
            assert isinstance(log, logging.Logger)

    def test_logger_has_correct_name(self):
        """Logger should have the specified name."""
        from utils import logger as logger_module

        with tempfile.TemporaryDirectory() as tmpdir:
            log = logger_module.setup_logger("my_custom_logger", "INFO", tmpdir)
            assert log.name == "my_custom_logger"

    def test_logger_creates_log_file(self):
        """Logger should create log file in specified directory."""
        import logging.handlers
        from utils import logger as logger_module

        with tempfile.TemporaryDirectory() as tmpdir:
            log = logger_module.setup_logger("test_logger", "INFO", tmpdir)
            # Get the file handler
            file_handlers = [h for h in log.handlers if isinstance(h, logging.handlers.TimedRotatingFileHandler)]
            assert len(file_handlers) > 0
            # Verify the log file name is correct
            handler = file_handlers[0]
            log_path = Path(handler.baseFilename)
            assert log_path.name == "test_logger.log"

    def test_logger_creates_directory_if_not_exists(self):
        """Logger should create log directory if it doesn't exist."""
        from utils import logger as logger_module

        with tempfile.TemporaryDirectory() as tmpdir:
            new_log_dir = Path(tmpdir) / "nonexistent" / "logs"
            assert not new_log_dir.exists()
            logger_module.setup_logger("test_logger", "INFO", str(new_log_dir))
            assert new_log_dir.exists()

    @pytest.mark.parametrize(
        "level,expected_level",
        [
            ("DEBUG", logging.DEBUG),
            ("INFO", logging.INFO),
            ("WARNING", logging.WARNING),
            ("ERROR", logging.ERROR),
        ],
    )
    def test_logger_level_configurable(self, level: str, expected_level: int):
        """Logger level should be configurable."""
        from utils import logger as logger_module

        with tempfile.TemporaryDirectory() as tmpdir:
            log = logger_module.setup_logger("test_logger", level, tmpdir)
            assert log.level == expected_level

    def test_logger_has_console_handler(self):
        """Logger should have StreamHandler for console output."""
        from utils import logger as logger_module

        with tempfile.TemporaryDirectory() as tmpdir:
            log = logger_module.setup_logger("test_logger", "INFO", tmpdir)
            # Check for console handler (StreamHandler)
            handler_types = [type(h).__name__ for h in log.handlers]
            assert "StreamHandler" in handler_types

    def test_logger_has_file_handler(self):
        """Logger should have FileHandler for file output."""
        from utils import logger as logger_module

        with tempfile.TemporaryDirectory() as tmpdir:
            log = logger_module.setup_logger("test_logger", "INFO", tmpdir)
            # Check for file handler (FileHandler or TimedRotatingFileHandler)
            handler_types = [type(h).__name__ for h in log.handlers]
            assert "FileHandler" in handler_types or "TimedRotatingFileHandler" in handler_types
