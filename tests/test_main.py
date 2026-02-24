"""Tests for main module.

These tests verify the main entry point functionality according to Task 6.1.
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from core import exceptions


class TestMainFunction:
    """Test main function functionality."""

    def test_main_with_valid_config_path_runs_bot(self):
        """main should initialize and run bot with provided config path."""
        from core import main as main_module

        # Mock the run_bot function
        with patch('core.main.run_bot') as mock_run_bot:
            # Call main with a dummy config path
            sys.argv = ['main.py', 'config.json']

            main_module.main()

            # Verify run_bot was called with the config path
            mock_run_bot.assert_called_once_with('config.json')

    def test_main_with_no_args_shows_usage_and_exits(self):
        """main should show usage and exit if no config path provided."""
        from core import main as main_module

        # Capture print output and exit call
        with patch('builtins.print') as mock_print, \
             patch('sys.exit') as mock_exit:
            sys.argv = ['main.py']  # No config path

            main_module.main()

            # Verify usage was printed and exit was called
            mock_print.assert_called()
            mock_exit.assert_called_once()

    def test_main_with_help_flag_shows_usage_and_exits(self):
        """main should show usage and exit if help flag is provided."""
        from core import main as main_module

        with patch('builtins.print') as mock_print, \
             patch('sys.exit') as mock_exit:
            sys.argv = ['main.py', '--help']

            main_module.main()

            # Verify usage was printed and exit was called
            mock_print.assert_called()
            mock_exit.assert_called_once()

    def test_main_with_h_flag_shows_usage_and_exits(self):
        """main should show usage and exit if -h flag is provided."""
        from core import main as main_module

        with patch('builtins.print') as mock_print, \
             patch('sys.exit') as mock_exit:
            sys.argv = ['main.py', '-h']

            main_module.main()

            # Verify usage was printed and exit was called
            mock_print.assert_called()
            mock_exit.assert_called_once()

    def test_main_with_invalid_config_path_raises_error(self):
        """main should handle errors from run_bot."""
        from core import main as main_module

        # Mock run_bot to raise an exception
        with patch('core.main.run_bot', side_effect=exceptions.ConfigError("Config not found")):
            with patch('sys.exit') as mock_exit:
                sys.argv = ['main.py', 'nonexistent_config.json']

                main_module.main()

                # Verify sys.exit was called due to the error
                mock_exit.assert_called_once()

    def test_main_prints_error_message_on_exception(self):
        """main should print error message when exception occurs."""
        from core import main as main_module

        # Mock run_bot to raise an exception
        with patch('core.main.run_bot', side_effect=exceptions.ConfigError("Config not found")):
            with patch('builtins.print') as mock_print, \
                 patch('sys.exit') as mock_exit:
                sys.argv = ['main.py', 'nonexistent_config.json']

                main_module.main()

                # Verify error message was printed
                assert any("Config not found" in str(call) for call in mock_print.call_args_list)
                mock_exit.assert_called_once()


class TestRunBotFunction:
    """Test run_bot function functionality."""

    def test_run_bot_loads_config_and_sets_up_logger(self):
        """run_bot should load config and set up logger before creating bot."""
        from core import main as main_module

        mock_config = {
            "accounts": [],
            "monitor": {"user_list_size": 5, "poll_interval_seconds": 1},
            "logging": {"level": "INFO", "log_dir": "logs"},
            "email": {}
        }

        # Mock config loading and logger setup
        with patch('core.main.config_utils.load_config', return_value=mock_config) as mock_load_config, \
             patch('core.main.logger_utils.setup_logger') as mock_setup_logger, \
             patch('core.main.Bot') as mock_bot_class:

            main_module.run_bot("test_config.json")

            # Verify config was loaded
            mock_load_config.assert_called_once_with("test_config.json")

            # Verify logger was set up
            mock_setup_logger.assert_called_once()

    def test_run_bot_creates_bot_with_config_and_logger(self):
        """run_bot should create Bot instance with loaded config and logger."""
        from core import main as main_module

        mock_config = {
            "accounts": [],
            "monitor": {"user_list_size": 5, "poll_interval_seconds": 1},
            "logging": {"level": "INFO", "log_dir": "logs"},
            "email": {}
        }
        mock_logger = Mock()

        # Mock config loading, logger setup, and bot instance
        with patch('core.main.config_utils.load_config', return_value=mock_config), \
             patch('core.main.logger_utils.setup_logger', return_value=mock_logger), \
             patch('core.main.Bot') as mock_bot_class:

            mock_bot_instance = Mock()
            mock_bot_class.return_value = mock_bot_instance

            main_module.run_bot("test_config.json")

            # Verify Bot was created with correct parameters
            mock_bot_class.assert_called_once_with(mock_config, mock_logger)

    def test_run_bot_calls_setup_and_run_methods(self):
        """run_bot should call bot setup and run methods."""
        from core import main as main_module

        mock_config = {
            "accounts": [],
            "monitor": {"user_list_size": 5, "poll_interval_seconds": 1},
            "logging": {"level": "INFO", "log_dir": "logs"},
            "email": {}
        }
        mock_logger = Mock()

        # Mock config loading, logger setup, and bot instance
        with patch('core.main.config_utils.load_config', return_value=mock_config), \
             patch('core.main.logger_utils.setup_logger', return_value=mock_logger), \
             patch('core.main.Bot') as mock_bot_class:

            mock_bot_instance = Mock()
            mock_bot_class.return_value = mock_bot_instance

            main_module.run_bot("test_config.json")

            # Verify bot methods were called
            mock_bot_instance.bot_setup.assert_called_once()
            mock_bot_instance.bot_run.assert_called_once()

    def test_run_bot_calls_cleanup_in_finally_block(self):
        """run_bot should call bot cleanup in finally block."""
        from core import main as main_module

        mock_config = {
            "accounts": [],
            "monitor": {"user_list_size": 5, "poll_interval_seconds": 1},
            "logging": {"level": "INFO", "log_dir": "logs"},
            "email": {}
        }
        mock_logger = Mock()

        # Mock config loading, logger setup, and bot instance
        with patch('core.main.config_utils.load_config', return_value=mock_config), \
             patch('core.main.logger_utils.setup_logger', return_value=mock_logger), \
             patch('core.main.Bot') as mock_bot_class:

            mock_bot_instance = Mock()
            mock_bot_class.return_value = mock_bot_instance

            main_module.run_bot("test_config.json")

            # Verify cleanup was called
            mock_bot_instance.bot_cleanup.assert_called_once()

    def test_run_bot_handles_exception_and_logs_error(self):
        """run_bot should handle exceptions and log errors."""
        from core import main as main_module

        mock_config = {
            "accounts": [],
            "monitor": {"user_list_size": 5, "poll_interval_seconds": 1},
            "logging": {"level": "INFO", "log_dir": "logs"},
            "email": {}
        }
        mock_logger = Mock()

        # Mock config loading, logger setup, and bot instance that raises exception
        with patch('core.main.config_utils.load_config', return_value=mock_config), \
             patch('core.main.logger_utils.setup_logger', return_value=mock_logger), \
             patch('core.main.Bot') as mock_bot_class:

            mock_bot_instance = Mock()
            mock_bot_instance.bot_setup.side_effect = exceptions.AuthError("Login failed")
            mock_bot_class.return_value = mock_bot_instance

            with pytest.raises(exceptions.AuthError):
                main_module.run_bot("test_config.json")

            # Verify logger error was called
            mock_logger.error.assert_called_once()

    def test_run_bot_still_calls_cleanup_after_exception(self):
        """run_bot should call cleanup even after exception."""
        from core import main as main_module

        mock_config = {
            "accounts": [],
            "monitor": {"user_list_size": 5, "poll_interval_seconds": 1},
            "logging": {"level": "INFO", "log_dir": "logs"},
            "email": {}
        }
        mock_logger = Mock()

        # Mock config loading, logger setup, and bot instance that raises exception
        with patch('core.main.config_utils.load_config', return_value=mock_config), \
             patch('core.main.logger_utils.setup_logger', return_value=mock_logger), \
             patch('core.main.Bot') as mock_bot_class:

            mock_bot_instance = Mock()
            mock_bot_instance.bot_setup.side_effect = exceptions.AuthError("Login failed")
            mock_bot_class.return_value = mock_bot_instance

            try:
                main_module.run_bot("test_config.json")
            except exceptions.AuthError:
                pass  # Expected exception

            # Verify cleanup was still called despite exception
            mock_bot_instance.bot_cleanup.assert_called_once()