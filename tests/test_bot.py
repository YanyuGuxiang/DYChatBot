"""Tests for core/bot module.

These tests verify AccountBot and BotOrchestrator functionality.
"""

import threading
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import pytest

from core import exceptions


class TestAccountBotInit:
    """Test AccountBot initialization."""

    def test_init_stores_config_and_derives_cookie_path(self):
        """AccountBot should store config and derive per-account cookie path."""
        from core import bot as bot_module

        account = {"name": "店铺A", "direct_url": "https://test.com"}
        config = {"accounts": [account], "monitor": {"poll_interval_seconds": 1}}
        logger = Mock()

        bot = bot_module.AccountBot(account, config, logger)

        assert bot.account_config is account
        assert bot.config is config
        assert bot.logger is logger
        assert bot.cookie_path == Path("cookies") / "店铺A.json"

    def test_init_resources_are_none_before_setup(self):
        """All browser resources should be None before setup()."""
        from core import bot as bot_module

        account = {"name": "店铺A"}
        bot = bot_module.AccountBot(account, {}, Mock())

        assert bot.playwright_instance is None
        assert bot.browser is None
        assert bot.context is None
        assert bot.page is None
        assert bot.auth_instance is None
        assert bot.nav is None
        assert bot.monitor_instance is None

    def test_init_creates_stop_event(self):
        """AccountBot should create a threading.Event for stop signalling."""
        from core import bot as bot_module

        bot = bot_module.AccountBot({"name": "A"}, {}, Mock())
        assert isinstance(bot._stop_event, threading.Event)
        assert not bot._stop_event.is_set()


class TestAccountBotSetup:
    """Test AccountBot.setup() functionality."""

    @patch("core.bot.sync_playwright")
    def test_setup_launches_browser_and_creates_page(self, mock_sync_pw):
        """setup() should launch browser and create context/page."""
        from core import bot as bot_module

        mock_pw = Mock()
        mock_browser = Mock()
        mock_context = Mock()
        mock_page = Mock()

        mock_sync_pw.return_value.__enter__ = Mock(return_value=mock_pw)
        mock_pw.chromium.launch.return_value = mock_browser
        mock_browser.new_context.return_value = mock_context
        mock_context.new_page.return_value = mock_page

        account = {"name": "店铺A", "direct_url": "https://test.com"}
        config = {"monitor": {"poll_interval_seconds": 1},
                  "retry": {"login_max_retries": 3, "element_max_retries": 3},
                  "email": {}}
        bot = bot_module.AccountBot(account, config, Mock())
        bot.setup()

        mock_pw.chromium.launch.assert_called_once()
        mock_browser.new_context.assert_called_once()
        mock_context.new_page.assert_called_once()
        assert bot.page is mock_page

    @patch("core.bot.sync_playwright")
    def test_setup_creates_auth_nav_monitor(self, mock_sync_pw):
        """setup() should wire up auth, nav, and monitor components."""
        from core import bot as bot_module

        mock_pw = Mock()
        mock_sync_pw.return_value.__enter__ = Mock(return_value=mock_pw)
        mock_browser = Mock()
        mock_pw.chromium.launch.return_value = mock_browser
        mock_browser.new_context.return_value = Mock()
        mock_browser.new_context.return_value.new_page.return_value = Mock()

        account = {"name": "店铺A", "direct_url": "https://test.com"}
        config = {"monitor": {"poll_interval_seconds": 1},
                  "retry": {"login_max_retries": 3, "element_max_retries": 3},
                  "email": {}}
        bot = bot_module.AccountBot(account, config, Mock())
        bot.setup()

        assert bot.auth_instance is not None
        assert bot.nav is not None
        assert bot.monitor_instance is not None


class TestAccountBotRun:
    """Test AccountBot.run() functionality."""

    def test_run_calls_setup_monitor_cleanup(self):
        """run() should call setup, start_monitoring, then cleanup."""
        from core import bot as bot_module

        account = {"name": "店铺A"}
        bot = bot_module.AccountBot(account, {}, Mock())

        mock_monitor = Mock()
        bot.setup = Mock()
        bot.cleanup = Mock()
        bot.monitor_instance = mock_monitor

        bot.run()

        bot.setup.assert_called_once()
        mock_monitor.start_monitoring.assert_called_once()
        bot.cleanup.assert_called_once()

    def test_run_calls_cleanup_on_error(self):
        """run() should call cleanup even if setup raises."""
        from core import bot as bot_module

        account = {"name": "店铺A"}
        bot = bot_module.AccountBot(account, {}, Mock())
        bot.setup = Mock(side_effect=Exception("setup failed"))
        bot.cleanup = Mock()

        bot.run()

        bot.cleanup.assert_called_once()


class TestAccountBotCleanup:
    """Test AccountBot.cleanup() functionality."""

    def test_cleanup_closes_page_context_browser(self):
        """cleanup() should close page, context, and browser."""
        from core import bot as bot_module

        account = {"name": "店铺A"}
        bot = bot_module.AccountBot(account, {}, Mock())

        mock_page = Mock()
        mock_context = Mock()
        mock_browser = Mock()
        bot.page = mock_page
        bot.context = mock_context
        bot.browser = mock_browser

        bot.cleanup()

        mock_page.close.assert_called_once()
        mock_context.close.assert_called_once()
        mock_browser.close.assert_called_once()
        assert bot.page is None
        assert bot.context is None
        assert bot.browser is None

    def test_cleanup_handles_close_errors_gracefully(self):
        """cleanup() should not raise if close() fails."""
        from core import bot as bot_module

        account = {"name": "店铺A"}
        bot = bot_module.AccountBot(account, {}, Mock())

        mock_page = Mock()
        mock_page.close.side_effect = Exception("close failed")
        bot.page = mock_page
        bot.context = None
        bot.browser = None

        # Should not raise
        bot.cleanup()
        assert bot.page is None


class TestAccountBotStop:
    """Test AccountBot.stop() functionality."""

    def test_stop_sets_event(self):
        """stop() should set the internal threading.Event."""
        from core import bot as bot_module

        bot = bot_module.AccountBot({"name": "A"}, {}, Mock())
        assert not bot._stop_event.is_set()

        bot.stop()
        assert bot._stop_event.is_set()


class TestBotOrchestrator:
    """Test BotOrchestrator functionality."""

    @patch("core.bot.AccountBot")
    def test_start_creates_thread_per_account(self, mock_bot_cls):
        """start() should create one AccountBot and thread per account."""
        from core import bot as bot_module

        accounts = [
            {"name": "店铺A", "direct_url": "https://a.com"},
            {"name": "店铺B", "direct_url": "https://b.com"},
        ]
        config = {
            "accounts": accounts,
            "monitor": {"poll_interval_seconds": 1},
            "retry": {"login_max_retries": 3, "element_max_retries": 3},
            "email": {},
        }

        # Make AccountBot.run() a no-op so threads finish immediately
        mock_instance = Mock()
        mock_instance.run = Mock()
        mock_bot_cls.return_value = mock_instance

        orch = bot_module.BotOrchestrator(config, Mock())
        orch.start()

        assert mock_bot_cls.call_count == 2

    @patch("core.bot.AccountBot")
    def test_stop_signals_all_bots(self, mock_bot_cls):
        """stop() should call stop() on every AccountBot."""
        from core import bot as bot_module

        config = {
            "accounts": [
                {"name": "店铺A"},
                {"name": "店铺B"},
            ],
            "monitor": {"poll_interval_seconds": 1},
            "retry": {"login_max_retries": 3, "element_max_retries": 3},
            "email": {},
        }

        mock_instance = Mock()
        mock_bot_cls.return_value = mock_instance

        orch = bot_module.BotOrchestrator(config, Mock())
        orch.start()
        orch.stop()

        # stop() called on each bot instance
        assert mock_instance.stop.call_count == 2
