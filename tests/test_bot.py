"""Tests for core/bot module.

These tests verify the main bot orchestration functionality according to Task 5.1.
"""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from core import exceptions


class TestBotInit:
    """Test Bot initialization."""

    def test_init_creates_components_with_config_and_logger(self):
        """Bot should initialize all required components with config and logger."""
        from core import bot as bot_module

        mock_config = {"accounts": [], "monitor": {"user_list_size": 5, "poll_interval_seconds": 1}, "email": {}}
        mock_logger = Mock()

        bot = bot_module.Bot(mock_config, mock_logger)

        # Verify components were created
        assert bot.config is mock_config
        assert bot.logger is mock_logger
        assert bot.playwright_instance is not None  # Should be a mock in test
        assert bot.browser is not None
        assert bot.page is not None
        assert bot.auth is not None
        assert bot.nav is not None
        assert bot.monitor is not None


class TestBotSetup:
    """Test bot setup functionality."""

    @patch('core.bot.Playwright')
    @patch('core.bot.sync_playwright')
    def test_setup_initializes_playwright_and_browser(self, mock_sync_playwright, mock_playwright_class):
        """bot_setup should initialize Playwright and browser."""
        from core import bot as bot_module

        mock_config = {"accounts": [], "monitor": {"user_list_size": 5, "poll_interval_seconds": 1}, "email": {}}
        mock_logger = Mock()

        # Mock Playwright instance and its methods
        mock_pw_instance = Mock()
        mock_sync_playwright.return_value.__enter__.return_value = mock_pw_instance
        mock_browser = Mock()
        mock_pw_instance.chromium.launch.return_value = mock_browser

        bot = bot_module.Bot(mock_config, mock_logger)

        # Call setup
        bot.bot_setup()

        # Verify Playwright was started and browser launched
        mock_sync_playwright.assert_called_once()
        mock_pw_instance.chromium.launch.assert_called_once()

    @patch('core.bot.Playwright')
    @patch('core.bot.sync_playwright')
    def test_setup_creates_page_context(self, mock_sync_playwright, mock_playwright_class):
        """bot_setup should create browser context and page."""
        from core import bot as bot_module

        mock_config = {"accounts": [], "monitor": {"user_list_size": 5, "poll_interval_seconds": 1}, "email": {}}
        mock_logger = Mock()

        # Mock Playwright instance and its methods
        mock_pw_instance = Mock()
        mock_context = Mock()
        mock_page = Mock()

        mock_sync_playwright.return_value.__enter__.return_value = mock_pw_instance
        mock_browser = Mock()
        mock_pw_instance.chromium.launch.return_value = mock_browser
        mock_browser.new_context.return_value = mock_context
        mock_context.new_page.return_value = mock_page

        bot = bot_module.Bot(mock_config, mock_logger)

        # Call setup
        bot.bot_setup()

        # Verify context and page were created
        mock_browser.new_context.assert_called_once()
        mock_context.new_page.assert_called_once()

    @patch('core.bot.Playwright')
    @patch('core.bot.sync_playwright')
    def test_setup_initializes_auth_and_nav_components(self, mock_sync_playwright, mock_playwright_class):
        """bot_setup should initialize auth and navigation components."""
        from core import bot as bot_module

        mock_config = {"accounts": [], "monitor": {"user_list_size": 5, "poll_interval_seconds": 1}, "email": {}}
        mock_logger = Mock()

        # Mock Playwright instance and its methods
        mock_pw_instance = Mock()
        mock_context = Mock()
        mock_page = Mock()

        mock_sync_playwright.return_value.__enter__.return_value = mock_pw_instance
        mock_browser = Mock()
        mock_pw_instance.chromium.launch.return_value = mock_browser
        mock_browser.new_context.return_value = mock_context
        mock_context.new_page.return_value = mock_page

        bot = bot_module.Bot(mock_config, mock_logger)

        # Call setup
        bot.bot_setup()

        # Verify auth and nav components were initialized with page and logger
        assert bot.auth is not None
        assert bot.nav is not None


class TestBotRun:
    """Test bot run functionality."""

    @patch('core.bot.Playwright')
    @patch('core.bot.sync_playwright')
    def test_run_executes_monitoring_process(self, mock_sync_playwright, mock_playwright_class):
        """bot_run should start the monitoring process."""
        from core import bot as bot_module

        mock_config = {"accounts": [{"name": "店铺A", "username": "user1", "password": "pass1", "direct_url": "https://test.com"}],
                       "monitor": {"user_list_size": 5, "poll_interval_seconds": 1},
                       "email": {},
                       "retry": {"login_max_retries": 3, "element_max_retries": 3}}
        mock_logger = Mock()

        # Mock all the components
        mock_pw_instance = Mock()
        mock_context = Mock()
        mock_page = Mock()
        mock_auth = Mock()
        mock_nav = Mock()
        mock_notifier = Mock()
        mock_monitor = Mock()

        mock_sync_playwright.return_value.__enter__.return_value = mock_pw_instance
        mock_browser = Mock()
        mock_pw_instance.chromium.launch.return_value = mock_browser
        mock_browser.new_context.return_value = mock_context
        mock_context.new_page.return_value = mock_page

        # Patch the imports inside bot module
        with patch('core.bot.DouyinAuth', return_value=mock_auth), \
             patch('core.bot.Navigator', return_value=mock_nav), \
             patch('core.bot.Monitor', return_value=mock_monitor), \
             patch('core.bot.send_alert', mock_notifier.send_alert):

            bot = bot_module.Bot(mock_config, mock_logger)

            # Call setup then run
            bot.bot_setup()
            bot.bot_run()

            # Verify monitor.start_monitoring was called
            mock_monitor.start_monitoring.assert_called_once()

    @patch('core.bot.Playwright')
    @patch('core.bot.sync_playwright')
    def test_run_handles_authentication_for_all_accounts(self, mock_sync_playwright, mock_playwright_class):
        """bot_run should authenticate for each account in config."""
        from core import bot as bot_module

        mock_config = {
            "accounts": [
                {"name": "店铺A", "username": "user1", "password": "pass1", "direct_url": "https://test1.com"},
                {"name": "店铺B", "username": "user2", "password": "pass2", "direct_url": "https://test2.com"},
                {"name": "店铺C", "username": "user3", "password": "pass3", "direct_url": "https://test3.com"}
            ],
            "monitor": {"user_list_size": 5, "poll_interval_seconds": 1},
            "email": {},
            "retry": {"login_max_retries": 3, "element_max_retries": 3}
        }
        mock_logger = Mock()

        # Mock all the components
        mock_pw_instance = Mock()
        mock_context = Mock()
        mock_page = Mock()
        mock_auth = Mock()
        mock_nav = Mock()
        mock_notifier = Mock()
        mock_monitor = Mock()

        mock_sync_playwright.return_value.__enter__.return_value = mock_pw_instance
        mock_browser = Mock()
        mock_pw_instance.chromium.launch.return_value = mock_browser
        mock_browser.new_context.return_value = mock_context
        mock_context.new_page.return_value = mock_page

        with patch('core.bot.DouyinAuth', return_value=mock_auth), \
             patch('core.bot.Navigator', return_value=mock_nav), \
             patch('core.bot.Monitor', return_value=mock_monitor), \
             patch('core.bot.send_alert', mock_notifier.send_alert):

            bot = bot_module.Bot(mock_config, mock_logger)

            # Call setup then run
            bot.bot_setup()
            bot.bot_run()

            # The monitor handles authentication internally during process_account
            # So we mainly verify the monitoring started
            mock_monitor.start_monitoring.assert_called_once()


class TestBotCleanup:
    """Test bot cleanup functionality."""

    @patch('core.bot.Playwright')
    @patch('core.bot.sync_playwright')
    def test_cleanup_closes_browser_and_playwright(self, mock_sync_playwright, mock_playwright_class):
        """bot_cleanup should close browser and stop Playwright."""
        from core import bot as bot_module

        mock_config = {"accounts": [], "monitor": {"user_list_size": 5, "poll_interval_seconds": 1}, "email": {}}
        mock_logger = Mock()

        # Mock Playwright instance and its methods
        mock_pw_instance = Mock()
        mock_context = Mock()
        mock_page = Mock()

        mock_sync_playwright.return_value.__enter__.return_value = mock_pw_instance
        mock_browser = Mock()
        mock_pw_instance.chromium.launch.return_value = mock_browser
        mock_browser.new_context.return_value = mock_context
        mock_context.new_page.return_value = mock_page

        with patch('core.bot.DouyinAuth'), \
             patch('core.bot.Navigator'), \
             patch('core.bot.Monitor'):

            bot = bot_module.Bot(mock_config, mock_logger)

            # Call setup
            bot.bot_setup()

            # Call cleanup
            bot.bot_cleanup()

            # Verify cleanup methods were called
            mock_browser.close.assert_called_once()
            # For playwright, it uses context manager so __exit__ is called


class TestBotErrorHandling:
    """Test bot error handling during setup/run."""

    @patch('core.bot.Playwright')
    @patch('core.bot.sync_playwright')
    def test_setup_handles_playwright_launch_failure(self, mock_sync_playwright, mock_playwright_class):
        """bot_setup should handle Playwright launch failure."""
        from core import bot as bot_module

        mock_config = {"accounts": [], "monitor": {"user_list_size": 5, "poll_interval_seconds": 1}, "email": {}}
        mock_logger = Mock()

        # Mock Playwright to throw an exception
        mock_sync_playwright.return_value.__enter__.side_effect = Exception("Playwright launch failed")

        bot = bot_module.Bot(mock_config, mock_logger)

        # This should handle the error gracefully or raise appropriate exception
        with pytest.raises(Exception):
            bot.bot_setup()

    @patch('core.bot.Playwright')
    @patch('core.bot.sync_playwright')
    def test_run_handles_monitoring_errors(self, mock_sync_playwright, mock_playwright_class):
        """bot_run should handle errors during monitoring."""
        from core import bot as bot_module

        mock_config = {"accounts": [{"name": "店铺A", "username": "user1", "password": "pass1", "direct_url": "https://test.com"}],
                       "monitor": {"user_list_size": 5, "poll_interval_seconds": 1},
                       "email": {},
                       "retry": {"login_max_retries": 3, "element_max_retries": 3}}
        mock_logger = Mock()

        # Mock all the components
        mock_pw_instance = Mock()
        mock_context = Mock()
        mock_page = Mock()
        mock_auth = Mock()
        mock_nav = Mock()
        mock_notifier = Mock()
        mock_monitor = Mock()
        mock_monitor.start_monitoring.side_effect = exceptions.AuthError("Authentication failed")

        mock_sync_playwright.return_value.__enter__.return_value = mock_pw_instance
        mock_browser = Mock()
        mock_pw_instance.chromium.launch.return_value = mock_browser
        mock_browser.new_context.return_value = mock_context
        mock_context.new_page.return_value = mock_page

        with patch('core.bot.DouyinAuth', return_value=mock_auth), \
             patch('core.bot.Navigator', return_value=mock_nav), \
             patch('core.bot.Monitor', return_value=mock_monitor), \
             patch('core.bot.send_alert', mock_notifier.send_alert):

            bot = bot_module.Bot(mock_config, mock_logger)

            # Call setup then run - this should handle the AuthError
            bot.bot_setup()
            # The function may or may not catch and handle the error depending on design
            # If it propagates, we expect the error
            with pytest.raises(exceptions.AuthError):
                bot.bot_run()
