"""Douyin chat monitoring module.

This module monitors a single account for unread messages and responds automatically.
Each account gets its own Monitor instance running in a dedicated thread.
"""

import threading
import time
from typing import Any, Dict

from core import auth, exceptions, navigator
from utils import notifier
from utils import logger as logger_utils


class Monitor:
    """Monitors a single Douyin account for unread messages and responds automatically.

    Thread-safety: each Monitor instance owns its own browser page, auth, and
    navigator — no shared mutable state between instances.  The only cross-thread
    communication is the ``stop_event`` (a :class:`threading.Event`), which is
    inherently thread-safe.
    """

    def __init__(
        self,
        auth_instance: auth.DouyinAuth,
        navigator_instance: navigator.Navigator,
        notifier_instance: notifier,
        account_config: Dict[str, Any],
        global_config: Dict[str, Any],
        logger_instance: logger_utils.logging.Logger,
        stop_event: threading.Event,
    ):
        """Initialize the monitor for a single account.

        Args:
            auth_instance: DouyinAuth instance for authentication.
            navigator_instance: Navigator instance for UI interactions.
            notifier_instance: Notifier instance for error notifications.
            account_config: Configuration dict for the single account this
                monitor is responsible for.
            global_config: Global configuration dictionary (email, retry, etc.).
            logger_instance: Logger instance.
            stop_event: Threading event used to signal graceful shutdown.
        """
        self.auth = auth_instance
        self.nav = navigator_instance
        self.notifier = notifier_instance
        self.account = account_config
        self.config = global_config
        self.logger = logger_instance
        self._stop_event = stop_event
        self._initialized: bool = False

    def start_monitoring(self) -> None:
        """Start the monitoring loop for this account."""
        account_name = self.account["name"]
        self.logger.info(f"Starting monitoring for account: {account_name}")

        while self._should_continue():
            try:
                self.process_account()
            except Exception as e:
                self.logger.error(f"Error processing account {account_name}: {e}")
                self._handle_error(type(e).__name__, str(e))

            # Wait before next poll cycle
            time.sleep(self.config["monitor"]["poll_interval_seconds"])

        self.logger.info(f"Monitoring stopped for account: {account_name}")

    def process_account(self) -> None:
        """Process the account for unread messages."""
        account_name = self.account["name"]
        self.logger.info(f"Processing account: {account_name}")

        direct_url = self.account.get("direct_url", "")

        # First time: navigate to the chat page
        if not self._initialized:
            self.nav.navigate_to_chat_list(direct_url=direct_url or None)
            is_expired = self.auth.check_session(direct_url)
            if is_expired:
                self.logger.info(
                    f"Session expired for account {account_name}, re-authenticating..."
                )
                self._reauthenticate_account()
                self.nav.navigate_to_chat_list(direct_url=direct_url or None)
            self._initialized = True
        else:
            # Subsequent cycles: check current page state
            is_expired = self.auth.check_session(direct_url)
            if is_expired:
                self.logger.info(
                    f"Session expired for account {account_name}, re-authenticating..."
                )
                self._initialized = False
                self._reauthenticate_account()
                self.nav.navigate_to_chat_list(direct_url=direct_url or None)
                self._initialized = True

        # Get unread chats
        unread_chats = self.nav.get_unread_chats(
            max_retries=self.config["retry"]["element_max_retries"],
            retry_delay=1.0,
        )

        # Handle case where unread_chats might be a Mock object during tests
        if hasattr(unread_chats, "__len__"):
            unread_chats_count = len(unread_chats)
        else:
            unread_chats_count = 0

        self.logger.info(
            f"Found {unread_chats_count} unread chats for account {account_name}"
        )

        # Process each unread chat
        try:
            chats_list = list(unread_chats)
            chats_to_process = chats_list
        except TypeError:
            chats_to_process = []

        for chat in chats_to_process:
            try:
                self.nav.open_chat(chat)
                partner = self.nav.get_current_chat_partner()
                if partner:
                    self.logger.info(f"Opened chat with: {partner}")

                self.nav.click_quick_reply()

                self.logger.info(
                    f"Sent quick reply to {partner or 'unknown user'} "
                    f"in account {account_name}"
                )
            except Exception as e:
                self.logger.error(
                    f"Error processing chat for account {account_name}: {e}"
                )
                self._handle_error(type(e).__name__, str(e))

    def _reauthenticate_account(self) -> None:
        """Re-authenticate the account with expired session."""
        credentials = {
            "username": self.account["username"],
            "password": self.account["password"],
        }

        max_retries = self.config["retry"]["login_max_retries"]

        for attempt in range(max_retries):
            try:
                self.logger.info(
                    f"Attempt {attempt + 1} to re-authenticate "
                    f"account {self.account['name']}"
                )
                self.auth.perform_login(credentials)
                self.auth.wait_for_login_success()
                self.auth.save_session()

                self.logger.info(
                    f"Successfully re-authenticated account {self.account['name']}"
                )
                return
            except Exception as e:
                self.logger.error(
                    f"Failed to re-authenticate account {self.account['name']}, "
                    f"attempt {attempt + 1}: {e}"
                )

                if attempt == max_retries - 1:
                    self.auth.delete_cookie()
                    raise exceptions.AuthError(
                        f"Failed to re-authenticate account "
                        f"{self.account['name']} after {max_retries} "
                        f"attempts: {e}"
                    )

                time.sleep(2)

    def _handle_error(
        self, error_type: str, error_detail: str, reraise: bool = False
    ) -> None:
        """Handle an error by logging and sending notification.

        Args:
            error_type: Type of error that occurred.
            error_detail: Detailed error message.
            reraise: Whether to re-raise the error after handling.
        """
        account_name = self.account["name"]
        self.logger.error(
            f"Error in account {account_name}: {error_type} - {error_detail}"
        )

        self.notifier.send_alert(
            self.config["email"],
            account_name,
            error_type,
            error_detail,
        )

        if reraise:
            if error_type == "SessionExpiredError":
                raise exceptions.SessionExpiredError(error_detail)
            elif error_type == "AuthError":
                raise exceptions.AuthError(error_detail)
            elif error_type == "NavigationError":
                raise exceptions.NavigationError(error_detail)
            else:
                raise exceptions.DYChatBotError(error_detail)

    def stop(self) -> None:
        """Stop the monitoring process via the shared event."""
        self.logger.info(f"Stopping monitoring for account: {self.account['name']}")
        self._stop_event.set()

    def _should_continue(self) -> bool:
        """Check if monitoring should continue.

        Returns:
            True if monitoring should continue, False if stop was signalled.
        """
        return not self._stop_event.is_set()
