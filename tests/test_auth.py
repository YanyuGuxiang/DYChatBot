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

    @staticmethod
    def _make_page_with_login_form():
        """Create a mock page that simulates the 抖音来客 login flow.

        The new perform_login calls page.locator() multiple times:
        - "立即登录" link, "密码登录" tab (navigation clicks)
        - password visibility wait
        - username input, password input, login button (credential filling)

        We use selector-based dispatch so each locator call gets the right mock.
        """
        mock_page = Mock()
        username_input = Mock()
        password_input = Mock()
        login_button = Mock()

        def locator_side_effect(selector: str):
            m = Mock()
            if "手机号" in selector or "邮箱" in selector:
                m.first = username_input
            elif "密码" in selector:
                m.first = password_input
                m.first.wait_for = Mock()  # wait_for visibility
            elif "登录" in selector and "button" in selector.lower():
                m.first = login_button
            # For "立即登录" / "密码登录" navigation clicks, return generic mock
            return m

        mock_page.locator = Mock(side_effect=locator_side_effect)
        return mock_page, username_input, password_input, login_button

    def test_perform_login_fills_and_submits(self):
        """perform_login should fill credentials and click login on current page."""
        from core import auth as auth_module

        mock_page, username_input, password_input, login_button = (
            self._make_page_with_login_form()
        )
        mock_logger = Mock()

        auth = auth_module.DouyinAuth(mock_page, mock_logger)
        auth.perform_login({"username": "test_user", "password": "test_pass"})

        # Should NOT navigate away
        mock_page.goto.assert_not_called()
        username_input.fill.assert_called_once_with("test_user")
        password_input.fill.assert_called_once_with("test_pass")
        login_button.click.assert_called_once()

    def test_perform_login_username_filled(self):
        """perform_login should fill username field."""
        from core import auth as auth_module

        mock_page, username_input, _, _ = self._make_page_with_login_form()
        auth = auth_module.DouyinAuth(mock_page, Mock())
        auth.perform_login({"username": "test_user", "password": "test_pass"})

        username_input.fill.assert_called_once_with("test_user")

    def test_perform_login_password_filled(self):
        """perform_login should fill password field."""
        from core import auth as auth_module

        mock_page, _, password_input, _ = self._make_page_with_login_form()
        auth = auth_module.DouyinAuth(mock_page, Mock())
        auth.perform_login({"username": "test_user", "password": "test_pass"})

        password_input.fill.assert_called_once_with("test_pass")

    def test_perform_login_clicks_login_button(self):
        """perform_login should click login button."""
        from core import auth as auth_module

        mock_page, _, _, login_button = self._make_page_with_login_form()
        auth = auth_module.DouyinAuth(mock_page, Mock())
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

    def test_wait_for_login_success_detects_form_disappearance(self):
        """wait_for_login_success should succeed when login form elements disappear."""
        from core import auth as auth_module

        mock_page = Mock()
        mock_logger = Mock()

        # Simulate: login form elements are gone (count == 0)
        locator_mock = Mock()
        locator_mock.count.return_value = 0
        mock_page.locator.return_value = locator_mock

        auth = auth_module.DouyinAuth(mock_page, mock_logger)

        # Should not raise
        auth.wait_for_login_success()

    @patch("time.sleep", return_value=None)
    def test_wait_for_login_success_timeout_raises_auth_error(self, mock_sleep):
        """wait_for_login_success should raise AuthError if login form never disappears."""
        from core import auth as auth_module

        mock_page = Mock()
        mock_logger = Mock()

        # Simulate: login form elements always present
        locator_mock = Mock()
        locator_mock.count.return_value = 1
        mock_page.locator.return_value = locator_mock
        mock_page.url = "https://life.douyin.com/"

        auth = auth_module.DouyinAuth(mock_page, mock_logger)

        with pytest.raises(exceptions.AuthError):
            auth.wait_for_login_success(max_attempts=3, sleep_interval=0.1)

    def test_wait_for_login_success_logs_waiting_message(self):
        """wait_for_login_success should log waiting message."""
        from core import auth as auth_module

        mock_page = Mock()
        mock_logger = Mock()

        locator_mock = Mock()
        locator_mock.count.return_value = 0
        mock_page.locator.return_value = locator_mock

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

    def test_check_session_does_not_navigate(self):
        """check_session should NOT call page.goto (navigation is caller's job)."""
        from core import auth as auth_module

        mock_page = Mock()
        mock_logger = Mock()
        mock_page.goto = Mock()

        auth = auth_module.DouyinAuth(mock_page, mock_logger)

        auth.check_session(direct_url="https://life.douyin.com/cs/web/xxx")

        mock_page.goto.assert_not_called()


class TestSaveSession:
    """Test save_session functionality."""

    def test_save_session_calls_storage_state(self):
        """save_session should call context.storage_state with session_path."""
        from core import auth as auth_module

        mock_page = Mock()
        mock_logger = Mock()
        mock_context = Mock()
        session_path = Path(tempfile.mkdtemp()) / "cookies" / "test.json"

        auth = auth_module.DouyinAuth(
            mock_page, mock_logger, context=mock_context, session_path=session_path
        )
        auth.save_session()

        mock_context.storage_state.assert_called_once_with(path=str(session_path))

    def test_save_session_creates_parent_directory(self):
        """save_session should auto-create parent directories."""
        from core import auth as auth_module

        mock_page = Mock()
        mock_logger = Mock()
        mock_context = Mock()
        base = Path(tempfile.mkdtemp()) / "nested" / "cookies"
        session_path = base / "account.json"

        auth = auth_module.DouyinAuth(
            mock_page, mock_logger, context=mock_context, session_path=session_path
        )
        auth.save_session()

        assert base.exists()

    def test_save_session_noop_without_context(self):
        """save_session should do nothing if context is None."""
        from core import auth as auth_module

        mock_page = Mock()
        mock_logger = Mock()
        session_path = Path("dummy.json")

        auth = auth_module.DouyinAuth(
            mock_page, mock_logger, context=None, session_path=session_path
        )
        auth.save_session()

        mock_logger.info.assert_not_called()

    def test_save_session_noop_without_session_path(self):
        """save_session should do nothing if session_path is None."""
        from core import auth as auth_module

        mock_page = Mock()
        mock_logger = Mock()
        mock_context = Mock()

        auth = auth_module.DouyinAuth(
            mock_page, mock_logger, context=mock_context, session_path=None
        )
        auth.save_session()

        mock_context.storage_state.assert_not_called()


class TestDeleteCookie:
    """Test delete_cookie functionality."""

    def test_delete_cookie_removes_existing_file(self):
        """delete_cookie should remove the cookie file when it exists."""
        from core import auth as auth_module

        mock_page = Mock()
        mock_logger = Mock()

        tmp_dir = Path(tempfile.mkdtemp())
        cookie_file = tmp_dir / "test_account.json"
        cookie_file.write_text("{}")

        auth = auth_module.DouyinAuth(
            mock_page, mock_logger, session_path=cookie_file
        )
        auth.delete_cookie()

        assert not cookie_file.exists()
        mock_logger.info.assert_called()

    def test_delete_cookie_no_error_when_file_missing(self):
        """delete_cookie should not raise when cookie file does not exist."""
        from core import auth as auth_module

        mock_page = Mock()
        mock_logger = Mock()
        session_path = Path(tempfile.mkdtemp()) / "nonexistent.json"

        auth = auth_module.DouyinAuth(
            mock_page, mock_logger, session_path=session_path
        )

        auth.delete_cookie()
        mock_logger.debug.assert_called()

    def test_delete_cookie_noop_without_session_path(self):
        """delete_cookie should do nothing if session_path is None."""
        from core import auth as auth_module

        mock_page = Mock()
        mock_logger = Mock()

        auth = auth_module.DouyinAuth(mock_page, mock_logger, session_path=None)
        auth.delete_cookie()

        mock_logger.info.assert_not_called()