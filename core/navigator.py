"""Douyin navigation module.

This module handles page navigation and UI interactions within Douyin business center.
"""

import time
from typing import List, Optional

from playwright.sync_api import Page

from core import exceptions
from utils import logger


class Navigator:
    """Handles navigation and UI interactions in Douyin business center."""

    def __init__(self, page: Page, logger_instance: logger.logging.Logger):
        """Initialize the navigator.

        Args:
            page: Playwright Page instance.
            logger_instance: Logger instance.
        """
        self.page = page
        self.logger = logger_instance

    def navigate_to_chat_list(self) -> None:
        """Navigate to the chat list page."""
        self.logger.info("Navigating to chat list page")

        # Navigate to Douyin business center
        self.page.goto("https://life.douyin.com/")

        # Wait for page to load
        self.page.wait_for_load_state("domcontentloaded")

        # Find and click the chat tab/button
        # Using role-based selectors for accessibility
        chat_tab = self.page.get_by_role("tab", name="消息", exact=True)
        if not chat_tab.count():  # If not found with role="tab", try other selectors
            chat_tab = self.page.get_by_role("button", name="消息", exact=True)

        chat_tab.click()

        # Wait for chat list to load
        self.page.wait_for_selector("[data-testid='chat-list'], .chat-list-item", timeout=10000)

        self.logger.info("Successfully navigated to chat list")

    def get_unread_chats(self, max_retries: int = 3, retry_delay: float = 1.0) -> List:
        """Get list of unread chat elements.

        Args:
            max_retries: Maximum number of retries to find unread chats.
            retry_delay: Delay between retries in seconds.

        Returns:
            List of unread chat elements.
        """
        self.logger.info("Getting unread chats")

        for attempt in range(max_retries):
            # Find unread chat elements (elements with unread indicators)
            unread_chats = self.page.locator("[data-unread='true'], .unread-chat, .unread-indicator")
            count = unread_chats.count()

            if count > 0:
                self.logger.info(f"Found {count} unread chats")
                # Return list of chat elements
                chat_elements = []
                for i in range(count):
                    chat_elements.append(unread_chats.nth(i))
                return chat_elements

            self.logger.debug(f"No unread chats found, attempt {attempt + 1}/{max_retries}")
            if attempt < max_retries - 1:  # Don't sleep on the last attempt
                time.sleep(retry_delay)

        self.logger.info("No unread chats found after all retries")
        return []

    def open_chat(self, chat_element) -> None:
        """Open a specific chat by clicking on its element.

        Args:
            chat_element: Element representing the chat to open.
        """
        self.logger.info("Opening chat")

        try:
            # Click on the chat element to open the conversation
            chat_element.click()

            # Wait for messages to load
            self.page.wait_for_selector("[data-testid='message-bubble'], .message-item", timeout=10000)

            self.logger.info("Successfully opened chat and messages loaded")
        except Exception as e:
            self.logger.error(f"Failed to open chat: {str(e)}")
            raise exceptions.NavigationError(f"Failed to open chat: {str(e)}") from e

    def send_message(self, message: str) -> None:
        """Send a message in the current chat.

        Args:
            message: Message text to send.

        Raises:
            ValueError: If message is empty.
            NavigationError: If UI elements are not found.
        """
        if not message:
            raise ValueError("Message cannot be empty")

        self.logger.info(f"Sending message: {message}")

        try:
            # Find message input field
            message_input = self.page.get_by_role("textbox", name="输入消息")
            if not message_input.count():
                # Alternative selector for message input
                message_input = self.page.locator("textarea[placeholder*='输入'], textarea[data-testid='message-input']")

            # Fill the message input
            message_input.fill(message)

            # Find and click send button
            send_button = self.page.get_by_role("button", name="发送", exact=True)
            if not send_button.count():
                # Alternative selector for send button
                send_button = self.page.locator("button[data-testid='send-button'], button.send-btn")

            send_button.click()

            # Wait for message to be sent and appear in the chat
            self.page.wait_for_selector(f"text={message}", timeout=5000)

            self.logger.info("Message sent successfully")
        except Exception as e:
            self.logger.error(f"Failed to send message: {str(e)}")
            raise exceptions.NavigationError(f"Failed to send message: {str(e)}") from e

    def get_current_chat_partner(self) -> Optional[str]:
        """Get the name of the current chat partner.

        Returns:
            Name of the current chat partner, or None if not found.
        """
        self.logger.info("Getting current chat partner")

        try:
            # Find the chat partner name in the header/title area
            # Using various possible selectors for the chat partner name
            partner_name_element = (
                self.page.locator("[data-testid='chat-partner-name']").first or
                self.page.locator(".chat-header-title").first or
                self.page.locator("h2.chat-title").first
            )

            partner_name = partner_name_element.text_content()

            if partner_name:
                self.logger.info(f"Current chat partner: {partner_name}")
                return partner_name.strip()
            else:
                self.logger.info("No chat partner name found")
                return None
        except Exception as e:
            self.logger.error(f"Failed to get current chat partner: {str(e)}")
            raise exceptions.NavigationError(f"Failed to get current chat partner: {str(e)}") from e
