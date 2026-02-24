"""Main bot orchestration module.

This module provides:
- ``AccountBot``: manages a single account's full lifecycle
  (browser, auth, navigation, monitoring) in its own thread.
- ``BotOrchestrator``: spins up one ``AccountBot`` per configured account,
  each in a dedicated thread, and coordinates graceful shutdown.

Thread-safety: each AccountBot owns independent browser/context/page instances.
The only shared primitive is ``threading.Event`` for stop signalling, which is
inherently thread-safe.  No additional locking is required.
"""

import os
import threading
from pathlib import Path
from typing import Any, Dict, List, Optional

from playwright.sync_api import sync_playwright as real_sync_playwright

from core import auth, exceptions, monitor, navigator
from utils import config as config_utils
from utils import logger as logger_utils
from utils import notifier as notifier_utils

# Project root: one level up from core/
_PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _set_playwright_browsers_path() -> None:
    """Set PLAYWRIGHT_BROWSERS_PATH to the project-local .ms-playwright if present."""
    if os.environ.get("PLAYWRIGHT_BROWSERS_PATH"):
        return
    local_browsers = _PROJECT_ROOT / ".ms-playwright"
    if local_browsers.is_dir():
        os.environ["PLAYWRIGHT_BROWSERS_PATH"] = str(local_browsers)


class AccountBot:
    """Manages a single account's full lifecycle in its own thread.

    Each instance owns an independent Playwright browser, context, and page.
    Designed to be the ``target`` of a :class:`threading.Thread`.
    """

    def __init__(
        self,
        account_config: Dict[str, Any],
        global_config: Dict[str, Any],
        logger_instance: logger_utils.logging.Logger,
        playwright_launcher: Optional[Any] = None,
    ):
        """Initialize the bot for a single account.

        Args:
            account_config: Single account configuration dict.
            global_config: Global configuration dictionary.
            logger_instance: Logger instance.
            playwright_launcher: Optional callable for dependency injection
                during testing.  When *None*, uses the real
                ``sync_playwright``.
        """
        self.account_config = account_config
        self.config = global_config
        self.logger = logger_instance
        self.playwright_launcher = playwright_launcher
        self._stop_event = threading.Event()

        # Derive per-account cookie path
        self.cookie_path = Path("cookies") / f"{account_config['name']}.json"

        # Will be set during setup()
        self.playwright_instance: Optional[Any] = None
        self.browser: Optional[Any] = None
        self.context: Optional[Any] = None
        self.page: Optional[Any] = None
        self.auth_instance: Optional[auth.DouyinAuth] = None
        self.nav: Optional[navigator.Navigator] = None
        self.monitor_instance: Optional[monitor.Monitor] = None

    def setup(self) -> None:
        """Launch browser, restore cookies, and wire up all components."""
        account_name = self.account_config["name"]
        self.logger.info(f"Setting up bot for account: {account_name}")

        try:
            # Ensure Playwright finds locally installed browsers
            _set_playwright_browsers_path()

            sync_playwright_fn = self.playwright_launcher or sync_playwright
            pw_context = sync_playwright_fn()
            self.playwright_instance = pw_context.__enter__()

            self.browser = self.playwright_instance.chromium.launch(
                headless=False,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--disable-dev-shm-usage",
                    "--no-sandbox",
                ],
            )

            # Build context options, restoring cookies if available
            context_opts: Dict[str, Any] = {
                "viewport": {"width": 1920, "height": 1080},
                "user_agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/91.0.4472.124 Safari/537.36"
                ),
            }
            if self.cookie_path.exists():
                context_opts["storage_state"] = str(self.cookie_path)
                self.logger.info(
                    f"Restoring session from {self.cookie_path}"
                )

            self.context = self.browser.new_context(**context_opts)
            self.page = self.context.new_page()

            self.auth_instance = auth.DouyinAuth(
                self.page, self.logger,
                context=self.context,
                session_path=self.cookie_path,
            )
            self.nav = navigator.Navigator(self.page, self.logger)

            self.monitor_instance = monitor.Monitor(
                auth_instance=self.auth_instance,
                navigator_instance=self.nav,
                notifier_instance=notifier_utils,
                account_config=self.account_config,
                global_config=self.config,
                logger_instance=self.logger,
                stop_event=self._stop_event,
            )

            self.logger.info(
                f"Bot setup completed for account: {account_name}"
            )
        except Exception as e:
            self.logger.error(
                f"Error during bot setup for {account_name}: {e}"
            )
            self.cleanup()
            raise

    def run(self) -> None:
        """Thread entry point: setup → monitor → cleanup.

        This method is designed to be passed as ``target`` to
        :class:`threading.Thread`.
        """
        account_name = self.account_config["name"]
        try:
            self.setup()
            self.monitor_instance.start_monitoring()
        except Exception as e:
            self.logger.error(
                f"Account {account_name} terminated with error: {e}"
            )
        finally:
            self.cleanup()

    def cleanup(self) -> None:
        """Release all browser resources."""
        account_name = self.account_config["name"]
        self.logger.info(f"Cleaning up bot for account: {account_name}")

        for resource_name in ("page", "context", "browser"):
            resource = getattr(self, resource_name, None)
            if resource is not None:
                try:
                    resource.close()
                except Exception:
                    self.logger.warning(
                        f"Error closing {resource_name} for {account_name}"
                    )
                setattr(self, resource_name, None)

        self.playwright_instance = None
        self.auth_instance = None
        self.nav = None
        self.monitor_instance = None
        self.logger.info(f"Bot cleanup completed for account: {account_name}")

    def stop(self) -> None:
        """Signal this bot to stop gracefully."""
        self._stop_event.set()


class BotOrchestrator:
    """Spins up one AccountBot per configured account in dedicated threads.

    Thread-safety: each AccountBot owns fully independent resources.
    The orchestrator only coordinates start/stop via threading primitives.
    """

    # Timeout (seconds) when joining threads during shutdown
    JOIN_TIMEOUT = 10

    def __init__(
        self,
        config: Dict[str, Any],
        logger_instance: logger_utils.logging.Logger,
    ):
        self.config = config
        self.logger = logger_instance
        self._bots: List[AccountBot] = []
        self._threads: List[threading.Thread] = []

    def start(self) -> None:
        """Create and start a thread for each account."""
        accounts = self.config["accounts"]
        self.logger.info(f"Starting orchestrator for {len(accounts)} account(s)")

        for account_cfg in accounts:
            bot = AccountBot(
                account_config=account_cfg,
                global_config=self.config,
                logger_instance=self.logger,
            )
            thread = threading.Thread(
                target=bot.run,
                name=f"bot-{account_cfg['name']}",
                daemon=True,
            )
            self._bots.append(bot)
            self._threads.append(thread)

        for thread in self._threads:
            thread.start()

        # Block until all threads finish.
        # Use a timeout loop so the main thread can receive KeyboardInterrupt
        # on Windows (join() without timeout swallows the signal).
        while any(t.is_alive() for t in self._threads):
            for thread in self._threads:
                thread.join(timeout=0.5)

    def stop(self) -> None:
        """Signal all bots to stop and wait for threads to finish."""
        self.logger.info("Stopping all account bots...")
        for bot in self._bots:
            bot.stop()

        for thread in self._threads:
            thread.join(timeout=self.JOIN_TIMEOUT)


# Module-level aliases for test mocking compatibility
sync_playwright = real_sync_playwright
