"""Custom exception definitions for DYChatBot.

Exception hierarchy:
    DYChatBotError (base)
    ├── ConfigError
    ├── AuthError
    │   └── SessionExpiredError
    ├── NavigationError
    └── NotificationError
"""

from typing import Any


class DYChatBotError(Exception):
    """Base exception for all DYChatBot errors."""

    pass


class ConfigError(DYChatBotError):
    """Raised when configuration file is missing, malformed, or validation fails."""

    pass


class AuthError(DYChatBotError):
    """Raised when authentication or login fails."""

    pass


class SessionExpiredError(AuthError):
    """Raised when session is detected as expired during operation."""

    pass


class NavigationError(DYChatBotError):
    """Raised when page navigation fails or target elements cannot be found."""

    pass


class NotificationError(DYChatBotError):
    """Raised when email notification fails to send."""

    pass
