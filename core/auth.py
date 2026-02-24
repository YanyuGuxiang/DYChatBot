"""Douyin authentication module.

This module handles login and session management for Douyin accounts.
"""

import time
from pathlib import Path
from typing import Any, Optional

from playwright.sync_api import BrowserContext, Page

from core import exceptions
from utils import logger


class DouyinAuth:
    """Handles Douyin authentication and session management."""

    def __init__(
        self,
        page: Page,
        logger_instance: logger.logging.Logger,
        context: Optional[BrowserContext] = None,
        session_path: Optional[Path] = None,
    ):
        """Initialize the authenticator.

        Args:
            page: Playwright Page instance.
            logger_instance: Logger instance.
            context: Playwright BrowserContext (needed for storage_state).
            session_path: File path to persist session cookies.
        """
        self.page = page
        self.logger = logger_instance
        self.context = context
        self.session_path = session_path

    def perform_login(self, credentials: dict[str, str]) -> None:
        """Perform login with provided credentials.

        The method assumes the page is already showing a login/register page
        on life.douyin.com (抖音来客).  The login flow requires:
        1. Click "立即登录" to switch from register to login view
        2. Click "密码登录" to switch from SMS to password mode
        3. Fill username and password, then submit

        Args:
            credentials: Dictionary containing 'username' and 'password'.

        Raises:
            AuthError: If credentials are invalid or login fails.
        """
        if not credentials.get("username") or not credentials.get("password"):
            raise exceptions.AuthError("Username and password cannot be empty")

        self.logger.info(f"Attempting login for account: {credentials['username']}")

        # Step 1: Click "立即登录" to enter login mode (if visible)
        try:
            login_link = self.page.locator("p:has-text('立即登录')")
            login_link.wait_for(state="visible", timeout=5000)
            login_link.click()
            self.logger.info("Clicked '立即登录'")
        except Exception:
            self.logger.debug("'立即登录' not found or already on login form")

        # Step 2: Click "密码登录" to switch to password mode
        try:
            pwd_tab = self.page.locator("div.switch-tip:has-text('密码登录')")
            pwd_tab.wait_for(state="visible", timeout=5000)
            pwd_tab.click()
            self.logger.info("Clicked '密码登录'")
        except Exception:
            self.logger.debug("'密码登录' tab not found, may already be in password mode")

        # Step 3: Wait for password input to become visible
        self.page.locator("input[placeholder='密码']").first.wait_for(
            state="visible", timeout=10000
        )

        # Step 4: Fill credentials
        username_input = self.page.locator(
            "input[placeholder*='手机号'], input[placeholder*='邮箱'], "
            "input[placeholder*='抖音号']"
        ).first
        password_input = self.page.locator(
            "input[placeholder='密码']"
        ).first

        username_input.fill(credentials["username"])
        password_input.fill(credentials["password"])

        # Step 5: Check the agreement checkbox (已阅读并同意)
        # The actual <input> is visually hidden; click the visible <label> instead.
        try:
            checkbox_label = self.page.locator("label.life-core-checkbox").first
            checkbox_label.click()
            self.logger.info("Checked agreement checkbox")
        except Exception:
            self.logger.debug("Agreement checkbox not found or already checked")

        # Step 6: Click login button
        login_button = self.page.locator("button:has-text('登录')").first
        login_button.click()

        self.logger.info("Login credentials submitted")

    def wait_for_login_success(self, max_attempts: int = 60, sleep_interval: float = 1.0) -> None:
        """Wait for login to complete.

        Detects success by checking that login-form elements have
        disappeared from the page (works for both embedded forms on
        life.douyin.com and SSO redirects).

        Args:
            max_attempts: Maximum number of attempts to check for login success.
            sleep_interval: Time to sleep between attempts in seconds.

        Raises:
            AuthError: If login verification times out.
        """
        self.logger.info("Waiting for login to complete...")

        login_selectors = (
            "input[placeholder*='手机号'],"
            "input[placeholder*='密码'],"
            "input[placeholder*='Password']"
        )

        for attempt in range(max_attempts):
            # If no login-form inputs remain, login succeeded
            try:
                if self.page.locator(login_selectors).count() == 0:
                    self.logger.info("Login successful")
                    return
            except Exception:
                pass

            self.logger.debug(
                f"Login attempt {attempt + 1}: login form still visible"
            )
            time.sleep(sleep_interval)

        raise exceptions.AuthError(
            f"Login verification timed out after "
            f"{max_attempts * sleep_interval:.1f} seconds. "
            f"Current URL: {self.page.url}"
        )

    def check_session(self, direct_url: str) -> bool:
        """Check if current session is still valid on the current page.

        Only inspects the current page state (URL + DOM).
        Does NOT call page.goto() — the caller is responsible for
        navigating to the correct page beforehand.

        Args:
            direct_url: Not used for navigation; kept for API compatibility.

        Returns:
            True if session is expired, False if session is still valid.
        """
        self.logger.debug("Checking session validity on current page")

        current_url = self.page.url

        # --- URL-based check ---
        login_url_markers = ("sso.douyin.com", "passport.douyin.com")
        try:
            if any(marker in current_url for marker in login_url_markers):
                self.logger.warning(
                    f"Session expired: on login page (URL: {current_url})"
                )
                return True
        except TypeError:
            self.logger.info("Session is still valid")
            return False

        # --- Page-content check ---
        # Use the login card container class unique to the login page,
        # not generic input selectors which may match chat page elements.
        login_selectors = [
            "[class*='LoginCard']",
            "p:has-text('立即登录')",
        ]
        for selector in login_selectors:
            try:
                if self.page.locator(selector).count() > 0:
                    self.logger.warning(
                        f"Session expired: login element detected "
                        f"(selector: {selector})"
                    )
                    return True
            except Exception:
                continue

        self.logger.info("Session is still valid")
        return False

    def save_session(self) -> None:
        """Save browser session (cookies/storage) to disk."""
        if not self.context or not self.session_path:
            return
        try:
            self.session_path.parent.mkdir(parents=True, exist_ok=True)
            self.context.storage_state(path=str(self.session_path))
            self.logger.info(f"Session saved to {self.session_path}")
        except Exception as e:
            self.logger.warning(f"Failed to save session: {e}")

    def delete_cookie(self) -> None:
        """Delete the cookie file for this account.

        Called when session validation fails to ensure stale cookies
        are removed before re-authentication.
        """
        if not self.session_path:
            return
        try:
            if self.session_path.exists():
                self.session_path.unlink()
                self.logger.info(f"Deleted cookie file: {self.session_path}")
            else:
                self.logger.debug(f"Cookie file not found, nothing to delete: {self.session_path}")
        except OSError as e:
            self.logger.warning(f"Failed to delete cookie file {self.session_path}: {e}")
