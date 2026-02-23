"""Tests for core/exceptions module.

These tests verify the exception hierarchy and behavior according to Task 1.1.
"""

import pytest

from core import exceptions


class TestExceptionHierarchy:
    """Test that all custom exceptions inherit from DYChatBotError."""

    @pytest.mark.parametrize(
        "exception_class",
        [
            exceptions.ConfigError,
            exceptions.AuthError,
            exceptions.NavigationError,
            exceptions.NotificationError,
        ],
    )
    def test_exception_inherits_from_base(self, exception_class):
        """All custom exceptions should inherit from DYChatBotError."""
        assert issubclass(exception_class, exceptions.DYChatBotError)

    def test_session_expired_inherits_from_auth(self):
        """SessionExpiredError should inherit from AuthError."""
        assert issubclass(exceptions.SessionExpiredError, exceptions.AuthError)


class TestExceptionMessage:
    """Test that exceptions can carry message strings."""

    @pytest.mark.parametrize(
        "exception_class,message",
        [
            (exceptions.DYChatBotError, "Base error message"),
            (exceptions.ConfigError, "Config file not found"),
            (exceptions.AuthError, "Login failed"),
            (exceptions.SessionExpiredError, "Session expired for account X"),
            (exceptions.NavigationError, "Failed to navigate to page"),
            (exceptions.NotificationError, "Failed to send email"),
        ],
    )
    def test_exception_carries_message(self, exception_class, message):
        """Exceptions should be instantiable with a message string."""
        exc = exception_class(message)
        assert str(exc) == message


class TestExceptionChaining:
    """Test that exception chaining is preserved with 'raise ... from err'."""

    def test_exception_chain_preserved(self):
        """Exception chain should be preserved when using 'raise ... from err'."""
        original = ValueError("Original error")
        try:
            raise exceptions.ConfigError("Config error") from original
        except exceptions.ConfigError as exc:
            # __cause__ is set when using 'raise ... from'
            assert exc.__cause__ is original
            assert str(exc) == "Config error"

    def test_exception_chain_with_another_exception(self):
        """Test chaining between custom exceptions."""
        auth_error = exceptions.AuthError("Auth failed")
        try:
            raise exceptions.SessionExpiredError("Session expired") from auth_error
        except exceptions.SessionExpiredError as exc:
            assert exc.__cause__ is auth_error
            assert isinstance(exc.__cause__, exceptions.AuthError)
