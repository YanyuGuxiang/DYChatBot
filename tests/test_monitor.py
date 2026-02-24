"""Tests for core/monitor module.

These tests verify chat monitoring and processing functionality according to Task 4.1.
"""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from core import exceptions


class TestMonitorInit:
    """Test Monitor initialization."""

    def test_init_creates_components_and_logger(self):
        """Monitor should initialize with required components and logger."""
        from core import monitor as monitor_module

        mock_auth = Mock()
        mock_nav = Mock()
        mock_notifier = Mock()
        mock_config = {"accounts": [], "monitor": {"user_list_size": 5, "poll_interval_seconds": 1}}
        mock_logger = Mock()

        monitor = monitor_module.Monitor(mock_auth, mock_nav, mock_notifier, mock_config, mock_logger)

        assert monitor.auth is mock_auth
        assert monitor.nav is mock_nav
        assert monitor.notifier is mock_notifier
        assert monitor.config is mock_config
        assert monitor.logger is mock_logger


class TestStartMonitoring:
    """Test start_monitoring functionality."""

    @patch("time.sleep", return_value=None)
    def test_start_monitoring_loops_until_stopped(self, mock_sleep):
        """start_monitoring should continuously loop until stopped."""
        from core import monitor as monitor_module

        mock_auth = Mock()
        mock_nav = Mock()
        mock_notifier = Mock()
        mock_config = {"accounts": [{"name": "店铺A", "direct_url": "https://test.com"}], "monitor": {"user_list_size": 5, "poll_interval_seconds": 1}}
        mock_logger = Mock()

        monitor = monitor_module.Monitor(mock_auth, mock_nav, mock_notifier, mock_config, mock_logger)

        # Create a mock that returns True once then False to break the loop
        call_count = 0

        def mock_should_continue():
            nonlocal call_count
            call_count += 1
            return call_count < 2  # Only continue for 1 iteration

        # Mock the internal methods
        monitor._should_continue = mock_should_continue
        monitor.process_account = Mock()

        monitor.start_monitoring()

        # process_account should have been called once
        monitor.process_account.assert_called_once()

    def test_start_monitoring_checks_session_for_each_account(self):
        """start_monitoring should check session for each configured account."""
        from core import monitor as monitor_module

        mock_auth = Mock()
        mock_nav = Mock()
        mock_notifier = Mock()
        mock_config = {
            "accounts": [
                {"name": "店铺A", "direct_url": "https://test1.com"},
                {"name": "店铺B", "direct_url": "https://test2.com"},
                {"name": "店铺C", "direct_url": "https://test3.com"}
            ],
            "monitor": {"user_list_size": 5, "poll_interval_seconds": 1}
        }
        mock_logger = Mock()

        monitor = monitor_module.Monitor(mock_auth, mock_nav, mock_notifier, mock_config, mock_logger)

        # Mock internal methods to control flow
        monitor._should_continue = Mock(side_effect=[True, False])
        monitor.process_account = Mock()

        monitor.start_monitoring()

        # Verify process_account was called for each account
        assert monitor.process_account.call_count == 3
        # Check the arguments for each call
        calls = monitor.process_account.call_args_list
        assert len(calls) == 3
        assert calls[0][0][0] == {"name": "店铺A", "direct_url": "https://test1.com"}
        assert calls[1][0][0] == {"name": "店铺B", "direct_url": "https://test2.com"}
        assert calls[2][0][0] == {"name": "店铺C", "direct_url": "https://test3.com"}


class TestProcessAccount:
    """Test process_account functionality."""

    def test_process_account_with_valid_session_processes_chats(self):
        """process_account should process chats if session is valid."""
        from core import monitor as monitor_module

        mock_auth = Mock()
        mock_nav = Mock()
        mock_notifier = Mock()
        mock_config = {"accounts": [], "monitor": {"user_list_size": 5, "poll_interval_seconds": 1}, "retry": {"element_max_retries": 3}}
        mock_logger = Mock()

        monitor = monitor_module.Monitor(mock_auth, mock_nav, mock_notifier, mock_config, mock_logger)

        # Mock that session is valid (not expired)
        mock_auth.check_session.return_value = False

        # Mock navigation methods
        mock_nav.navigate_to_chat_list = Mock()
        mock_nav.get_unread_chats.return_value = [Mock(), Mock()]  # Two unread chats
        mock_nav.open_chat = Mock()
        mock_nav.send_message = Mock()

        account = {"name": "店铺A", "direct_url": "https://test.com"}

        monitor.process_account(account)

        # Verify session check and navigation
        mock_auth.check_session.assert_called_once_with("https://test.com")
        mock_nav.navigate_to_chat_list.assert_called_once()
        mock_nav.get_unread_chats.assert_called_once()

    def test_process_account_with_expired_session_reauthenticates(self):
        """process_account should re-authenticate if session is expired."""
        from core import monitor as monitor_module

        mock_auth = Mock()
        mock_nav = Mock()
        mock_notifier = Mock()
        mock_config = {
            "accounts": [],
            "monitor": {"user_list_size": 5, "poll_interval_seconds": 1},
            "retry": {"login_max_retries": 3, "element_max_retries": 3}
        }
        mock_logger = Mock()

        monitor = monitor_module.Monitor(mock_auth, mock_nav, mock_notifier, mock_config, mock_logger)

        # Mock that session is expired
        mock_auth.check_session.return_value = True  # Session is expired

        # Mock re-authentication flow
        mock_auth.perform_login = Mock()
        mock_auth.wait_for_login_success = Mock()

        account = {"name": "店铺A", "username": "user1", "password": "pass1", "direct_url": "https://test.com"}

        monitor.process_account(account)

        # Verify re-authentication happened
        mock_auth.check_session.assert_called_once_with("https://test.com")
        mock_auth.perform_login.assert_called_once_with({"username": "user1", "password": "pass1"})
        mock_auth.wait_for_login_success.assert_called_once()

    def test_process_account_sends_reply_to_unread_chats(self):
        """process_account should send replies to unread chats."""
        from core import monitor as monitor_module

        mock_auth = Mock()
        mock_nav = Mock()
        mock_notifier = Mock()
        mock_config = {
            "accounts": [],
            "monitor": {"user_list_size": 5, "poll_interval_seconds": 1},
            "retry": {"element_max_retries": 3}
        }
        mock_logger = Mock()

        monitor = monitor_module.Monitor(mock_auth, mock_nav, mock_notifier, mock_config, mock_logger)

        # Mock valid session
        mock_auth.check_session.return_value = False

        # Mock navigation
        mock_nav.navigate_to_chat_list = Mock()
        mock_unread_chat1 = Mock()
        mock_unread_chat2 = Mock()
        mock_nav.get_unread_chats.return_value = [mock_unread_chat1, mock_unread_chat2]
        mock_nav.open_chat = Mock()
        mock_nav.send_message = Mock()
        mock_nav.get_current_chat_partner.return_value = "Customer"

        account = {"name": "店铺A", "direct_url": "https://test.com"}

        monitor.process_account(account)

        # Verify that each unread chat was processed
        assert mock_nav.open_chat.call_count == 2
        assert mock_nav.send_message.call_count == 2
        # Verify get_current_chat_partner was called to identify customer
        assert mock_nav.get_current_chat_partner.call_count >= 1


class TestHandleError:
    """Test _handle_error functionality."""

    def test_handle_error_sends_notification(self):
        """_handle_error should send notification via notifier."""
        from core import monitor as monitor_module

        mock_auth = Mock()
        mock_nav = Mock()
        mock_notifier = Mock()
        mock_config = {
            "accounts": [],
            "monitor": {"user_list_size": 5, "poll_interval_seconds": 1},
            "email": {"enabled": True}
        }
        mock_logger = Mock()

        monitor = monitor_module.Monitor(mock_auth, mock_nav, mock_notifier, mock_config, mock_logger)

        account = {"name": "店铺A"}
        error_type = "AuthError"
        error_detail = "Login failed"

        monitor._handle_error(account, error_type, error_detail)

        # Verify notifier was called with correct parameters
        mock_notifier.send_alert.assert_called_once_with(
            {"enabled": True},
            "店铺A",
            "AuthError",
            "Login failed"
        )

    def test_handle_error_logs_error(self):
        """_handle_error should log the error."""
        from core import monitor as monitor_module

        mock_auth = Mock()
        mock_nav = Mock()
        mock_notifier = Mock()
        mock_config = {"accounts": [], "monitor": {"user_list_size": 5, "poll_interval_seconds": 1}, "email": {}}
        mock_logger = Mock()

        monitor = monitor_module.Monitor(mock_auth, mock_nav, mock_notifier, mock_config, mock_logger)

        account = {"name": "店铺A"}
        error_type = "NavigationError"
        error_detail = "Element not found"

        monitor._handle_error(account, error_type, error_detail)

        # Verify logger was called
        mock_logger.error.assert_called_once()

    def test_handle_error_propagates_specific_errors(self):
        """_handle_error should propagate certain error types."""
        from core import monitor as monitor_module

        mock_auth = Mock()
        mock_nav = Mock()
        mock_notifier = Mock()
        mock_config = {"accounts": [], "monitor": {"user_list_size": 5, "poll_interval_seconds": 1}, "email": {}}
        mock_logger = Mock()

        monitor = monitor_module.Monitor(mock_auth, mock_nav, mock_notifier, mock_config, mock_logger)

        account = {"name": "店铺A"}

        # Test with an error that should propagate
        error = exceptions.SessionExpiredError("Session expired")
        with pytest.raises(exceptions.SessionExpiredError):
            monitor._handle_error(account, "SessionExpiredError", "Session expired", reraise=True)


class TestShouldContinue:
    """Test _should_continue functionality."""

    def test_should_continue_returns_true_by_default(self):
        """_should_continue should return True by default."""
        from core import monitor as monitor_module

        mock_auth = Mock()
        mock_nav = Mock()
        mock_notifier = Mock()
        mock_config = {"accounts": [], "monitor": {"user_list_size": 5, "poll_interval_seconds": 1}, "email": {}}
        mock_logger = Mock()

        monitor = monitor_module.Monitor(mock_auth, mock_nav, mock_notifier, mock_config, mock_logger)

        assert monitor._should_continue() is True

    def test_should_continue_can_be_set_to_false(self):
        """_should_continue should return False when stop is called."""
        from core import monitor as monitor_module

        mock_auth = Mock()
        mock_nav = Mock()
        mock_notifier = Mock()
        mock_config = {"accounts": [], "monitor": {"user_list_size": 5, "poll_interval_seconds": 1}, "email": {}}
        mock_logger = Mock()

        monitor = monitor_module.Monitor(mock_auth, mock_nav, mock_notifier, mock_config, mock_logger)

        monitor.stop()
        assert monitor._should_continue() is False