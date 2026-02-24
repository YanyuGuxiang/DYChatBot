"""Tests for core/monitor module.

These tests verify single-account chat monitoring and processing functionality.
"""

import threading
from unittest.mock import Mock, patch

import pytest

from core import exceptions


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_monitor(**overrides):
    """Create a Monitor with sensible defaults, allowing per-test overrides."""
    from core import monitor as monitor_module

    defaults = dict(
        auth_instance=Mock(),
        navigator_instance=Mock(),
        notifier_instance=Mock(),
        account_config={"name": "店铺A", "direct_url": "https://test.com"},
        global_config={
            "monitor": {"poll_interval_seconds": 1},
            "retry": {"login_max_retries": 3, "element_max_retries": 3},
            "email": {"enabled": True},
        },
        logger_instance=Mock(),
        stop_event=threading.Event(),
    )
    defaults.update(overrides)
    return monitor_module.Monitor(**defaults)


class TestMonitorInit:
    """Test Monitor initialization."""

    def test_init_stores_all_dependencies(self):
        """Monitor should store all injected dependencies."""
        from core import monitor as monitor_module

        mock_auth = Mock()
        mock_nav = Mock()
        mock_notifier = Mock()
        account_config = {"name": "店铺A", "direct_url": "https://test.com"}
        global_config = {
            "monitor": {"poll_interval_seconds": 1},
            "retry": {"login_max_retries": 3, "element_max_retries": 3},
            "email": {},
        }
        mock_logger = Mock()
        stop_event = threading.Event()

        mon = monitor_module.Monitor(
            mock_auth, mock_nav, mock_notifier,
            account_config, global_config, mock_logger, stop_event,
        )

        assert mon.auth is mock_auth
        assert mon.nav is mock_nav
        assert mon.notifier is mock_notifier
        assert mon.account is account_config
        assert mon.config is global_config
        assert mon.logger is mock_logger
        assert mon._stop_event is stop_event
        assert mon._initialized is False


class TestStartMonitoring:
    """Test start_monitoring functionality."""

    @patch("time.sleep", return_value=None)
    def test_start_monitoring_loops_until_stopped(self, mock_sleep):
        """start_monitoring should loop until stop_event is set."""
        mon = _make_monitor()

        # Let it run one iteration then stop
        call_count = 0
        original_should_continue = mon._should_continue

        def counting_should_continue():
            nonlocal call_count
            call_count += 1
            if call_count >= 2:
                return False
            return True

        mon._should_continue = counting_should_continue
        mon.process_account = Mock()

        mon.start_monitoring()

        mon.process_account.assert_called_once()

    @patch("time.sleep", return_value=None)
    def test_start_monitoring_processes_single_account(self, mock_sleep):
        """start_monitoring should call process_account (no multi-account loop)."""
        mon = _make_monitor()

        mon._should_continue = Mock(side_effect=[True, False])
        mon.process_account = Mock()

        mon.start_monitoring()

        # Only one call — single account, single iteration
        mon.process_account.assert_called_once()

    @patch("time.sleep", return_value=None)
    def test_start_monitoring_handles_process_error(self, mock_sleep):
        """start_monitoring should catch and handle errors from process_account."""
        mon = _make_monitor()

        mon._should_continue = Mock(side_effect=[True, False])
        mon.process_account = Mock(side_effect=Exception("boom"))
        mon._handle_error = Mock()

        mon.start_monitoring()

        mon._handle_error.assert_called_once()


class TestProcessAccount:
    """Test process_account functionality."""

    def test_process_account_with_valid_session_processes_chats(self):
        """process_account should process chats if session is valid."""
        mock_auth = Mock()
        mock_nav = Mock()
        mock_auth.check_session.return_value = False
        mock_nav.get_unread_chats.return_value = [Mock(), Mock()]

        mon = _make_monitor(auth_instance=mock_auth, navigator_instance=mock_nav)
        mon.process_account()

        mock_auth.check_session.assert_called_once_with("https://test.com")
        mock_nav.navigate_to_chat_list.assert_called_once_with(direct_url="https://test.com")
        mock_nav.get_unread_chats.assert_called_once()

    def test_process_account_with_expired_session_reauthenticates(self):
        """process_account should re-authenticate if session is expired."""
        mock_auth = Mock()
        mock_nav = Mock()
        mock_auth.check_session.return_value = True

        account = {
            "name": "店铺A", "username": "user1",
            "password": "pass1", "direct_url": "https://test.com",
        }
        mon = _make_monitor(auth_instance=mock_auth, navigator_instance=mock_nav,
                            account_config=account)
        mon.process_account()

        mock_auth.check_session.assert_called_once_with("https://test.com")
        mock_auth.perform_login.assert_called_once_with(
            {"username": "user1", "password": "pass1"}
        )
        mock_auth.wait_for_login_success.assert_called_once()

    def test_process_account_sends_reply_to_unread_chats(self):
        """process_account should send replies to unread chats."""
        mock_auth = Mock()
        mock_nav = Mock()
        mock_auth.check_session.return_value = False
        mock_nav.get_unread_chats.return_value = [Mock(), Mock()]
        mock_nav.get_current_chat_partner.return_value = "Customer"

        mon = _make_monitor(auth_instance=mock_auth, navigator_instance=mock_nav)
        mon.process_account()

        assert mock_nav.open_chat.call_count == 2
        assert mock_nav.click_quick_reply.call_count == 2
        assert mock_nav.get_current_chat_partner.call_count >= 1


class TestHandleError:
    """Test _handle_error functionality."""

    def test_handle_error_sends_notification(self):
        """_handle_error should send notification via notifier."""
        mock_notifier = Mock()
        mon = _make_monitor(notifier_instance=mock_notifier)

        mon._handle_error("AuthError", "Login failed")

        mock_notifier.send_alert.assert_called_once_with(
            {"enabled": True},
            "店铺A",
            "AuthError",
            "Login failed",
        )

    def test_handle_error_logs_error(self):
        """_handle_error should log the error."""
        mock_logger = Mock()
        mon = _make_monitor(logger_instance=mock_logger)

        mon._handle_error("NavigationError", "Element not found")

        mock_logger.error.assert_called_once()

    def test_handle_error_propagates_specific_errors(self):
        """_handle_error should propagate certain error types when reraise=True."""
        mon = _make_monitor()

        with pytest.raises(exceptions.SessionExpiredError):
            mon._handle_error("SessionExpiredError", "Session expired", reraise=True)


class TestShouldContinue:
    """Test _should_continue functionality."""

    def test_should_continue_returns_true_by_default(self):
        """_should_continue should return True when stop_event is not set."""
        mon = _make_monitor()
        assert mon._should_continue() is True

    def test_should_continue_returns_false_after_stop(self):
        """_should_continue should return False after stop() is called."""
        mon = _make_monitor()
        mon.stop()
        assert mon._should_continue() is False

    def test_stop_sets_event(self):
        """stop() should set the threading.Event."""
        stop_event = threading.Event()
        mon = _make_monitor(stop_event=stop_event)
        mon.stop()
        assert stop_event.is_set()


class TestReauthenticate:
    """Test _reauthenticate_account functionality."""

    def test_reauthenticate_calls_login_flow(self):
        """_reauthenticate_account should perform login and save session."""
        mock_auth = Mock()
        account = {
            "name": "店铺A", "username": "user1",
            "password": "pass1", "direct_url": "https://test.com",
        }
        mon = _make_monitor(auth_instance=mock_auth, account_config=account)

        mon._reauthenticate_account()

        mock_auth.perform_login.assert_called_once_with(
            {"username": "user1", "password": "pass1"}
        )
        mock_auth.wait_for_login_success.assert_called_once()
        mock_auth.save_session.assert_called_once()

    @patch("time.sleep", return_value=None)
    def test_reauthenticate_deletes_cookie_on_final_failure(self, mock_sleep):
        """_reauthenticate_account should delete cookie after all retries fail."""
        mock_auth = Mock()
        mock_auth.perform_login.side_effect = Exception("login failed")
        account = {
            "name": "店铺A", "username": "user1",
            "password": "pass1", "direct_url": "https://test.com",
        }
        mon = _make_monitor(auth_instance=mock_auth, account_config=account)

        with pytest.raises(exceptions.AuthError):
            mon._reauthenticate_account()

        mock_auth.delete_cookie.assert_called_once()

