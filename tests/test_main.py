"""Tests for main module.

These tests verify the main entry point functionality.
"""

import sys
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from core import exceptions


class TestMainFunction:
    """Test main function functionality."""

    def test_main_with_valid_config_path_runs_bot(self):
        """main should call run_bot with provided config path."""
        from core import main as main_module

        with patch("core.main.run_bot") as mock_run_bot:
            main_module.main(["main.py", "config.json"])
            mock_run_bot.assert_called_once_with("config.json")

    def test_main_with_no_args_shows_usage_and_exits(self):
        """main should show usage and exit if no config path provided."""
        from core import main as main_module

        with patch("builtins.print") as mock_print, \
             patch("sys.exit") as mock_exit:
            main_module.main(["main.py"])
            mock_print.assert_called()
            mock_exit.assert_called_once()

    def test_main_with_help_flag_shows_usage_and_exits(self):
        """main should show help and exit for --help flag."""
        from core import main as main_module

        with patch("builtins.print") as mock_print, \
             patch("sys.exit") as mock_exit:
            main_module.main(["main.py", "--help"])
            mock_print.assert_called()
            mock_exit.assert_called_once()

    def test_main_with_h_flag_shows_usage_and_exits(self):
        """main should show help and exit for -h flag."""
        from core import main as main_module

        with patch("builtins.print") as mock_print, \
             patch("sys.exit") as mock_exit:
            main_module.main(["main.py", "-h"])
            mock_print.assert_called()
            mock_exit.assert_called_once()

    def test_main_with_invalid_config_path_raises_error(self):
        """main should handle errors from run_bot."""
        from core import main as main_module

        with patch("core.main.run_bot", side_effect=exceptions.ConfigError("Config not found")):
            with patch("sys.exit") as mock_exit:
                main_module.main(["main.py", "nonexistent.json"])
                mock_exit.assert_called_once()

    def test_main_prints_error_message_on_exception(self):
        """main should print error message when exception occurs."""
        from core import main as main_module

        with patch("core.main.run_bot", side_effect=exceptions.ConfigError("Config not found")):
            with patch("builtins.print") as mock_print, \
                 patch("sys.exit") as mock_exit:
                main_module.main(["main.py", "nonexistent.json"])
                assert any("Config not found" in str(call) for call in mock_print.call_args_list)
                mock_exit.assert_called_once()


class TestRunBotFunction:
    """Test run_bot function functionality."""

    def test_run_bot_loads_config_and_sets_up_logger(self):
        """run_bot should load config and set up logger."""
        from core import main as main_module

        mock_config = {
            "accounts": [],
            "monitor": {"poll_interval_seconds": 1},
            "logging": {"level": "INFO", "log_dir": "logs"},
            "email": {},
        }

        with patch("core.main.config_utils.load_config", return_value=mock_config) as mock_load, \
             patch("core.main.logger_utils.setup_logger") as mock_setup_logger, \
             patch("core.main.BotOrchestrator"):
            main_module.run_bot("test_config.json")

            mock_load.assert_called_once_with(Path("test_config.json"))
            mock_setup_logger.assert_called_once()

    def test_run_bot_creates_orchestrator_with_config_and_logger(self):
        """run_bot should create BotOrchestrator with config and logger."""
        from core import main as main_module

        mock_config = {
            "accounts": [],
            "monitor": {"poll_interval_seconds": 1},
            "logging": {"level": "INFO", "log_dir": "logs"},
            "email": {},
        }
        mock_logger = Mock()

        with patch("core.main.config_utils.load_config", return_value=mock_config), \
             patch("core.main.logger_utils.setup_logger", return_value=mock_logger), \
             patch("core.main.BotOrchestrator") as mock_orch_cls:
            mock_orch = Mock()
            mock_orch_cls.return_value = mock_orch

            main_module.run_bot("test_config.json")

            mock_orch_cls.assert_called_once_with(mock_config, mock_logger)

    def test_run_bot_calls_start(self):
        """run_bot should call orchestrator.start()."""
        from core import main as main_module

        mock_config = {
            "accounts": [],
            "monitor": {"poll_interval_seconds": 1},
            "logging": {"level": "INFO", "log_dir": "logs"},
            "email": {},
        }

        with patch("core.main.config_utils.load_config", return_value=mock_config), \
             patch("core.main.logger_utils.setup_logger", return_value=Mock()), \
             patch("core.main.BotOrchestrator") as mock_orch_cls:
            mock_orch = Mock()
            mock_orch_cls.return_value = mock_orch

            main_module.run_bot("test_config.json")

            mock_orch.start.assert_called_once()

    def test_run_bot_calls_stop_in_finally(self):
        """run_bot should call orchestrator.stop() in finally block."""
        from core import main as main_module

        mock_config = {
            "accounts": [],
            "monitor": {"poll_interval_seconds": 1},
            "logging": {"level": "INFO", "log_dir": "logs"},
            "email": {},
        }

        with patch("core.main.config_utils.load_config", return_value=mock_config), \
             patch("core.main.logger_utils.setup_logger", return_value=Mock()), \
             patch("core.main.BotOrchestrator") as mock_orch_cls:
            mock_orch = Mock()
            mock_orch_cls.return_value = mock_orch

            main_module.run_bot("test_config.json")

            mock_orch.stop.assert_called_once()

    def test_run_bot_handles_exception_and_logs_error(self):
        """run_bot should log errors and re-raise."""
        from core import main as main_module

        mock_config = {
            "accounts": [],
            "monitor": {"poll_interval_seconds": 1},
            "logging": {"level": "INFO", "log_dir": "logs"},
            "email": {},
        }
        mock_logger = Mock()

        with patch("core.main.config_utils.load_config", return_value=mock_config), \
             patch("core.main.logger_utils.setup_logger", return_value=mock_logger), \
             patch("core.main.BotOrchestrator") as mock_orch_cls:
            mock_orch = Mock()
            mock_orch.start.side_effect = exceptions.AuthError("Login failed")
            mock_orch_cls.return_value = mock_orch

            with pytest.raises(exceptions.AuthError):
                main_module.run_bot("test_config.json")

            mock_logger.error.assert_called_once()
