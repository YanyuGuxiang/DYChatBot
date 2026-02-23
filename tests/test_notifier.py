"""Tests for utils/notifier module.

These tests verify email notification according to Task 1.3c.
"""

import pytest
from unittest.mock import MagicMock, patch

from core import exceptions


class TestNotifierEnabled:
    """Test notifier behavior when email is disabled."""

    def test_send_alert_returns_when_disabled(self):
        """send_alert should return immediately when email.enabled=false."""
        from utils import notifier as notifier_module

        email_config = {"enabled": False}

        # Should not raise any exception
        notifier_module.send_alert(email_config, "店铺A", "AuthError", "Login failed")


class TestNotifierValidation:
    """Test notifier input validation."""

    def test_empty_receivers_raises_notification_error(self):
        """Empty receivers list should raise NotificationError."""
        from utils import notifier as notifier_module

        email_config = {
            "enabled": True,
            "smtp_host": "smtp.qq.com",
            "smtp_port": 465,
            "sender": "test@qq.com",
            "auth_code": "auth123",
            "receivers": [],
        }

        with pytest.raises(exceptions.NotificationError):
            notifier_module.send_alert(email_config, "店铺A", "AuthError", "Login failed")

    def test_missing_smtp_host_raises_notification_error(self):
        """Missing smtp_host should raise NotificationError."""
        from utils import notifier as notifier_module

        email_config = {
            "enabled": True,
            "smtp_port": 465,
            "sender": "test@qq.com",
            "auth_code": "auth123",
            "receivers": ["receiver@example.com"],
        }

        with pytest.raises(exceptions.NotificationError):
            notifier_module.send_alert(email_config, "店铺A", "AuthError", "Login failed")


class TestNotifierEmailContent:
    """Test email content formatting."""

    def _get_decoded_body(self, message) -> str:
        """Get decoded email body content."""
        body_part = message.get_body()
        return body_part.get_content()

    def test_email_contains_account_name(self):
        """Email should contain the account identifier."""
        from utils import notifier as notifier_module

        email_config = {
            "enabled": True,
            "smtp_host": "smtp.qq.com",
            "smtp_port": 465,
            "sender": "test@qq.com",
            "auth_code": "auth123",
            "receivers": ["receiver@example.com"],
        }

        with patch("utils.notifier.smtplib.SMTP_SSL") as mock_smtp:
            mock_connection = MagicMock()
            mock_smtp.return_value.__enter__ = MagicMock(return_value=mock_connection)
            mock_smtp.return_value.__exit__ = MagicMock(return_value=False)

            notifier_module.send_alert(email_config, "店铺A", "AuthError", "Login failed")

            mock_connection.send_message.assert_called_once()
            call_args = mock_connection.send_message.call_args
            message = call_args[0][0]

            body = self._get_decoded_body(message)
            assert "店铺A" in body

    def test_email_contains_error_type(self):
        """Email should contain the error type."""
        from utils import notifier as notifier_module

        email_config = {
            "enabled": True,
            "smtp_host": "smtp.qq.com",
            "smtp_port": 465,
            "sender": "test@qq.com",
            "auth_code": "auth123",
            "receivers": ["receiver@example.com"],
        }

        with patch("utils.notifier.smtplib.SMTP_SSL") as mock_smtp:
            mock_connection = MagicMock()
            mock_smtp.return_value.__enter__ = MagicMock(return_value=mock_connection)
            mock_smtp.return_value.__exit__ = MagicMock(return_value=False)

            notifier_module.send_alert(email_config, "店铺A", "NavigationError", "Page timeout")

            mock_connection.send_message.assert_called_once()
            call_args = mock_connection.send_message.call_args
            message = call_args[0][0]

            body = self._get_decoded_body(message)
            assert "NavigationError" in body

    def test_email_contains_error_detail(self):
        """Email should contain the error detail."""
        from utils import notifier as notifier_module

        email_config = {
            "enabled": True,
            "smtp_host": "smtp.qq.com",
            "smtp_port": 465,
            "sender": "test@qq.com",
            "auth_code": "auth123",
            "receivers": ["receiver@example.com"],
        }

        with patch("utils.notifier.smtplib.SMTP_SSL") as mock_smtp:
            mock_connection = MagicMock()
            mock_smtp.return_value.__enter__ = MagicMock(return_value=mock_connection)
            mock_smtp.return_value.__exit__ = MagicMock(return_value=False)

            notifier_module.send_alert(email_config, "店铺A", "AuthError", "Element not found after 3 retries")

            mock_connection.send_message.assert_called_once()
            call_args = mock_connection.send_message.call_args
            message = call_args[0][0]

            body = self._get_decoded_body(message)
            assert "Element not found after 3 retries" in body

    def test_email_contains_timestamp(self):
        """Email should contain the timestamp of when the error occurred."""
        from utils import notifier as notifier_module

        email_config = {
            "enabled": True,
            "smtp_host": "smtp.qq.com",
            "smtp_port": 465,
            "sender": "test@qq.com",
            "auth_code": "auth123",
            "receivers": ["receiver@example.com"],
        }

        with patch("utils.notifier.smtplib.SMTP_SSL") as mock_smtp:
            mock_connection = MagicMock()
            mock_smtp.return_value.__enter__ = MagicMock(return_value=mock_connection)
            mock_smtp.return_value.__exit__ = MagicMock(return_value=False)

            notifier_module.send_alert(email_config, "店铺A", "AuthError", "Login failed")

            mock_connection.send_message.assert_called_once()
            call_args = mock_connection.send_message.call_args
            message = call_args[0][0]

            body = self._get_decoded_body(message)
            assert "20" in body  # Year 2026


class TestNotifierSmtpFailure:
    """Test SMTP connection failures."""

    def test_smtp_connection_failure_raises_notification_error(self):
        """SMTP connection failure should raise NotificationError."""
        from utils import notifier as notifier_module

        email_config = {
            "enabled": True,
            "smtp_host": "invalid.smtp.host",
            "smtp_port": 465,
            "sender": "test@qq.com",
            "auth_code": "auth123",
            "receivers": ["receiver@example.com"],
        }

        with pytest.raises(exceptions.NotificationError):
            notifier_module.send_alert(email_config, "店铺A", "AuthError", "Login failed")
