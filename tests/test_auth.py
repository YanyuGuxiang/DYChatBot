"""Tests for core/auth module.

These tests verify Douyin login and authentication functionality according to Task 2.1.
"""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from core import exceptions


class TestDouyinAuthInit:
    """Test DouyinAuth initialization."""

    def test_init_creates_page_and_logger(self):
        """DouyinAuth should initialize with playwright Page and logger."""
        from core import auth as auth_module

        mock_page = Mock()
        mock_logger = Mock()

        auth = auth_module.DouyinAuth(mock_page, mock_logger)

        assert auth.page is mock_page
        assert auth.logger is mock_logger


class TestPerformLogin:
    """Test perform_login functionality."""

    def test_perform_login_calls_page_functions(self):
        """perform_login should navigate to login page and submit credentials."""
        from core import auth as auth_module

        mock_page = Mock()
        mock_logger = Mock()

        # Setup page behavior expectations
        mock_page.goto = Mock()
        mock_page.get_by_role = Mock()
        username_input = Mock()
        password_input = Mock()
        login_button = Mock()
        mock_page.get_by_role.side_effect = [username_input, password_input, login_button]

        auth = auth_module.DouyinAuth(mock_page, mock_logger)

        # Perform login
        auth.perform_login({"username": "test_user", "password": "test_pass"})

        # Verify calls
        mock_page.goto.assert_called_once()
        assert username_input.fill.called
        assert password_input.fill.called
        assert login_button.click.called

    def test_perform_login_username_filled(self):
        """perform_login should fill username field."""
        from core import auth as auth_module

        mock_page = Mock()
        mock_logger = Mock()
        mock_page.goto = Mock()
        mock_page.get_by_role = Mock()
        username_input = Mock()
        password_input = Mock()
        login_button = Mock()
        mock_page.get_by_role.side_effect = [username_input, password_input, login_button]

        auth = auth_module.DouyinAuth(mock_page, mock_logger)

        auth.perform_login({"username": "test_user", "password": "test_pass"})

        username_input.fill.assert_called_once_with("test_user")

    def test_perform_login_password_filled(self):
        """perform_login should fill password field."""
        from core import auth as auth_module

        mock_page = Mock()
        mock_logger = Mock()
        mock_page.goto = Mock()
        mock_page.get_by_role = Mock()
        username_input = Mock()
        password_input = Mock()
        login_button = Mock()
        mock_page.get_by_role.side_effect = [username_input, password_input, login_button]

        auth = auth_module.DouyinAuth(mock_page, mock_logger)

        auth.perform_login({"username": "test_user", "password": "test_pass"})

        password_input.fill.assert_called_once_with("test_pass")

    def test_perform_login_clicks_login_button(self):
        """perform_login should click login button."""
        from core import auth as auth_module

        mock_page = Mock()
        mock_logger = Mock()
        mock_page.goto = Mock()
        mock_page.get_by_role = Mock()
        username_input = Mock()
        password_input = Mock()
        login_button = Mock()
        mock_page.get_by_role.side_effect = [username_input, password_input, login_button]

        auth = auth_module.DouyinAuth(mock_page, mock_logger)

        auth.perform_login({"username": "test_user", "password": "test_pass"})

        login_button.click.assert_called_once()

    @pytest.mark.parametrize(
        "credentials",
        [
            {"username": "", "password": "test_pass"},  # Empty username
            {"username": "test_user", "password": ""},  # Empty password
        ],
    )
    def test_perform_login_with_empty_credentials_raises_auth_error(self, credentials):
        """perform_login should raise AuthError with empty credentials."""
        from core import auth as auth_module

        mock_page = Mock()
        mock_logger = Mock()

        auth = auth_module.DouyinAuth(mock_page, mock_logger)

        with pytest.raises(exceptions.AuthError):
            auth.perform_login(credentials)


class TestWaitForLoginSuccess:
    """Test wait_for_login_success functionality."""

    def test_wait_for_login_success_waits_for_url_change(self):
        """wait_for_login_success should wait for expected post-login URL."""
        from core import auth as auth_module

        mock_page = Mock()
        mock_logger = Mock()

        # Simulate successful login - URL eventually matches
        mock_page.url = "https://life.douyin.com/"
        auth = auth_module.DouyinAuth(mock_page, mock_logger)

        # This should not raise
        auth.wait_for_login_success()

    @patch("time.sleep", return_value=None)
    def test_wait_for_login_success_timeout_raises_auth_error(self, mock_sleep):
        """wait_for_login_success should raise AuthError if timeout exceeded."""
        from core import auth as auth_module

        mock_page = Mock()
        mock_logger = Mock()
        # Simulate URL never changing - always the login page
        mock_page.url = "https://sso.douyin.com/login"

        auth = auth_module.DouyinAuth(mock_page, mock_logger)

        with pytest.raises(exceptions.AuthError):
            auth.wait_for_login_success(max_attempts=3, sleep_interval=0.1)

    def test_wait_for_login_success_logs_waiting_message(self):
        """wait_for_login_success should log waiting message."""
        from core import auth as auth_module

        mock_page = Mock()
        mock_logger = Mock()
        mock_page.url = "https://life.douyin.com/"

        auth = auth_module.DouyinAuth(mock_page, mock_logger)

        auth.wait_for_login_success()

        mock_logger.info.assert_called()


class TestCheckSession:
    """Test check_session functionality."""

    def test_check_session_detects_expired_session(self):
        """check_session should detect session expiration."""
        from core import auth as auth_module

        mock_page = Mock()
        mock_logger = Mock()

        # Simulate expired session by returning login URL
        mock_page.url = "https://sso.douyin.com/login"

        auth = auth_module.DouyinAuth(mock_page, mock_logger)

        # This should return True indicating session expired
        is_expired = auth.check_session(direct_url="https://life.douyin.com/")

        assert is_expired is True

    def test_check_session_detects_active_session(self):
        """check_session should confirm active session."""
        from core import auth as auth_module

        mock_page = Mock()
        mock_logger = Mock()

        # Simulate active session by returning direct URL
        mock_page.url = "https://life.douyin.com/"

        auth = auth_module.DouyinAuth(mock_page, mock_logger)

        # This should return False indicating session is not expired
        is_expired = auth.check_session(direct_url="https://life.douyin.com/")

        assert is_expired is False

    def test_check_session_navigates_to_direct_url(self):
        """check_session should navigate to the direct URL."""
        from core import auth as auth_module

        mock_page = Mock()
        mock_logger = Mock()
        mock_page.goto = Mock()

        auth = auth_module.DouyinAuth(mock_page, mock_logger)

        auth.check_session(direct_url="https://life.douyin.com/cs/web/xxx")

        mock_page.goto.assert_called_once_with("https://life.douyin.com/cs/web/xxx")