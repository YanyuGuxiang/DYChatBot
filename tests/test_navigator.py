"""Tests for core/navigator module.

These tests verify page navigation and UI interaction functionality according to Task 3.1.
"""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from core import exceptions


class TestNavigatorInit:
    """Test Navigator initialization."""

    def test_init_creates_page_and_logger(self):
        """Navigator should initialize with playwright Page and logger."""
        from core import navigator as navigator_module

        mock_page = Mock()
        mock_logger = Mock()

        nav = navigator_module.Navigator(mock_page, mock_logger)

        assert nav.page is mock_page
        assert nav.logger is mock_logger


class TestNavigateToChatList:
    """Test navigate_to_chat_list functionality."""

    def test_navigate_to_chat_list_goes_to_business_center(self):
        """navigate_to_chat_list should navigate to the business center."""
        from core import navigator as navigator_module

        mock_page = Mock()
        mock_logger = Mock()
        mock_page.goto = Mock()

        nav = navigator_module.Navigator(mock_page, mock_logger)
        nav.navigate_to_chat_list()

        # Should navigate to douyin business center
        mock_page.goto.assert_called_once()

    def test_navigate_to_chat_list_clicks_chat_tab(self):
        """navigate_to_chat_list should click the chat tab/button."""
        from core import navigator as navigator_module

        mock_page = Mock()
        mock_logger = Mock()
        mock_page.goto = Mock()
        mock_page.get_by_role = Mock()
        chat_tab_element = Mock()
        mock_page.get_by_role.return_value = chat_tab_element

        nav = navigator_module.Navigator(mock_page, mock_logger)
        nav.navigate_to_chat_list()

        # Should find and click the chat tab
        mock_page.get_by_role.assert_called()
        chat_tab_element.click.assert_called()

    def test_navigate_to_chat_list_waits_for_loading(self):
        """navigate_to_chat_list should wait for chat list to load."""
        from core import navigator as navigator_module

        mock_page = Mock()
        mock_logger = Mock()
        mock_page.goto = Mock()
        mock_page.get_by_role = Mock()
        chat_tab_element = Mock()
        mock_page.get_by_role.return_value = chat_tab_element
        mock_page.wait_for_selector = Mock()

        nav = navigator_module.Navigator(mock_page, mock_logger)
        nav.navigate_to_chat_list()

        # Should wait for the chat list to be loaded
        mock_page.wait_for_selector.assert_called()


class TestGetUnreadChats:
    """Test get_unread_chats functionality."""

    def test_get_unread_chats_finds_unread_elements(self):
        """get_unread_chats should locate unread chat elements."""
        from core import navigator as navigator_module

        mock_page = Mock()
        mock_logger = Mock()
        mock_page.locator = Mock()
        mock_locator = Mock()
        mock_locator.count.return_value = 2
        mock_locator.nth.side_effect = [Mock(), Mock()]
        mock_page.locator.return_value = mock_locator

        nav = navigator_module.Navigator(mock_page, mock_logger)
        chats = nav.get_unread_chats()

        # Should use locator to find unread chats
        mock_page.locator.assert_called()
        assert len(chats) == 2

    def test_get_unread_chats_returns_list_of_chat_elements(self):
        """get_unread_chats should return a list of chat elements."""
        from core import navigator as navigator_module

        mock_page = Mock()
        mock_logger = Mock()
        mock_page.locator = Mock()
        mock_locator = Mock()
        mock_locator.count.return_value = 2
        mock_locator_element1 = Mock()
        mock_locator_element2 = Mock()
        mock_locator.nth.side_effect = [mock_locator_element1, mock_locator_element2]
        mock_page.locator.return_value = mock_locator

        nav = navigator_module.Navigator(mock_page, mock_logger)
        chats = nav.get_unread_chats()

        # Should return a list of chat elements
        assert isinstance(chats, list)
        assert len(chats) == 2
        assert chats[0] is mock_locator_element1
        assert chats[1] is mock_locator_element2

    @patch("time.sleep", return_value=None)
    def test_get_unread_chats_with_retry_mechanism(self, mock_sleep):
        """get_unread_chats should retry if no chats found initially."""
        from core import navigator as navigator_module

        mock_page = Mock()
        mock_logger = Mock()
        mock_page.locator = Mock()
        mock_locator_first = Mock()
        mock_locator_first.count.return_value = 0  # No chats on first try
        mock_locator_second = Mock()
        mock_locator_second.count.return_value = 1  # One chat on second try
        mock_locator_element = Mock()
        mock_locator_second.nth.return_value = mock_locator_element
        # Return different locators on subsequent calls
        call_count = 0

        def mock_locator_return(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return mock_locator_first
            else:
                return mock_locator_second

        mock_page.locator.side_effect = mock_locator_return

        nav = navigator_module.Navigator(mock_page, mock_logger)
        chats = nav.get_unread_chats(max_retries=3, retry_delay=0.1)

        # Should retry since first attempt had 0 chats
        assert mock_page.locator.call_count > 1
        assert len(chats) == 1


class TestOpenChat:
    """Test open_chat functionality."""

    def test_open_chat_clicks_on_chat_element(self):
        """open_chat should click on the provided chat element."""
        from core import navigator as navigator_module

        mock_page = Mock()
        mock_logger = Mock()
        mock_chat_element = Mock()

        nav = navigator_module.Navigator(mock_page, mock_logger)
        nav.open_chat(mock_chat_element)

        # Should click on the chat element
        mock_chat_element.click.assert_called_once()

    def test_open_chat_waits_for_messages_to_load(self):
        """open_chat should wait for messages to load after clicking."""
        from core import navigator as navigator_module

        mock_page = Mock()
        mock_logger = Mock()
        mock_chat_element = Mock()
        mock_page.wait_for_selector = Mock()

        nav = navigator_module.Navigator(mock_page, mock_logger)
        nav.open_chat(mock_chat_element)

        # Should wait for messages to load
        mock_page.wait_for_selector.assert_called_once()

    def test_open_chat_handles_navigation_error(self):
        """open_chat should raise NavigationError if element is not clickable."""
        from core import navigator as navigator_module

        mock_page = Mock()
        mock_logger = Mock()
        mock_chat_element = Mock()
        mock_chat_element.click.side_effect = Exception("Timeout")

        nav = navigator_module.Navigator(mock_page, mock_logger)

        with pytest.raises(exceptions.NavigationError):
            nav.open_chat(mock_chat_element)


class TestSendMessage:
    """Test send_message functionality."""

    def test_send_message_fills_message_input(self):
        """send_message should fill the message input field."""
        from core import navigator as navigator_module

        mock_page = Mock()
        mock_logger = Mock()
        mock_page.get_by_role = Mock()
        message_input = Mock()
        send_button = Mock()
        mock_page.get_by_role.side_effect = [message_input, send_button]

        nav = navigator_module.Navigator(mock_page, mock_logger)
        nav.send_message("Hello, World!")

        # Should fill the message input
        message_input.fill.assert_called_once_with("Hello, World!")

    def test_send_message_clicks_send_button(self):
        """send_message should click the send button."""
        from core import navigator as navigator_module

        mock_page = Mock()
        mock_logger = Mock()
        mock_page.get_by_role = Mock()
        message_input = Mock()
        send_button = Mock()
        mock_page.get_by_role.side_effect = [message_input, send_button]

        nav = navigator_module.Navigator(mock_page, mock_logger)
        nav.send_message("Hello, World!")

        # Should click the send button
        send_button.click.assert_called_once()

    def test_send_message_waits_for_sent_confirmation(self):
        """send_message should wait for sent message to appear."""
        from core import navigator as navigator_module

        mock_page = Mock()
        mock_logger = Mock()
        mock_page.get_by_role = Mock()
        message_input = Mock()
        send_button = Mock()
        mock_page.get_by_role.side_effect = [message_input, send_button]
        mock_page.wait_for_selector = Mock()

        nav = navigator_module.Navigator(mock_page, mock_logger)
        nav.send_message("Hello, World!")

        # Should wait for sent message to appear
        mock_page.wait_for_selector.assert_called_once()

    def test_send_message_with_empty_message_raises_error(self):
        """send_message should raise an error with empty message."""
        from core import navigator as navigator_module

        mock_page = Mock()
        mock_logger = Mock()

        nav = navigator_module.Navigator(mock_page, mock_logger)

        with pytest.raises(ValueError):
            nav.send_message("")

    def test_send_message_handles_element_not_found_error(self):
        """send_message should raise NavigationError if input not found."""
        from core import navigator as navigator_module

        mock_page = Mock()
        mock_logger = Mock()
        mock_page.get_by_role = Mock()
        mock_page.get_by_role.side_effect = Exception("Element not found")

        nav = navigator_module.Navigator(mock_page, mock_logger)

        with pytest.raises(exceptions.NavigationError):
            nav.send_message("Hello, World!")


class TestGetCurrentChatPartner:
    """Test get_current_chat_partner functionality."""

    def test_get_current_chat_partner_reads_header_text(self):
        """get_current_chat_partner should extract the name from chat header."""
        from core import navigator as navigator_module

        mock_page = Mock()
        mock_logger = Mock()
        mock_page.locator = Mock()
        mock_element_handle = Mock()
        mock_element_handle.text_content.return_value = "张三"
        mock_page.locator.return_value.first = mock_element_handle

        nav = navigator_module.Navigator(mock_page, mock_logger)
        partner = nav.get_current_chat_partner()

        # Should return the extracted text content
        assert partner == "张三"

    def test_get_current_chat_partner_returns_none_if_not_found(self):
        """get_current_chat_partner should return None if element not found."""
        from core import navigator as navigator_module

        mock_page = Mock()
        mock_logger = Mock()
        mock_page.locator = Mock()
        mock_element_handle = Mock()
        mock_element_handle.text_content.return_value = None
        mock_page.locator.return_value.first = mock_element_handle

        nav = navigator_module.Navigator(mock_page, mock_logger)
        partner = nav.get_current_chat_partner()

        # Should return None if no text content
        assert partner is None

    def test_get_current_chat_partner_handles_element_error(self):
        """get_current_chat_partner should handle element access errors."""
        from core import navigator as navigator_module

        mock_page = Mock()
        mock_logger = Mock()
        mock_page.locator = Mock()
        mock_page.locator.side_effect = Exception("Element not found")

        nav = navigator_module.Navigator(mock_page, mock_logger)

        with pytest.raises(exceptions.NavigationError):
            nav.get_current_chat_partner()