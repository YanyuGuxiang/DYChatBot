"""Email notification for DYChatBot.

This module provides SMTP email notification for error alerts.
"""

import smtplib
from datetime import datetime
from email.message import EmailMessage
from typing import Any

from core import exceptions


def send_alert(
    email_config: dict[str, Any],
    account_name: str,
    error_type: str,
    error_detail: str,
) -> None:
    """Send an error alert email via SMTP.

    Args:
        email_config: Email configuration dictionary.
        account_name: Account identifier.
        error_type: Type of error (e.g., "AuthError", "NavigationError").
        error_detail: Detailed error message.

    Raises:
        NotificationError: If email sending fails.
    """
    enabled = email_config.get("enabled", False)

    if not enabled:
        return

    # Validate required fields
    smtp_host = email_config.get("smtp_host")
    smtp_port = email_config.get("smtp_port")
    sender = email_config.get("sender")
    auth_code = email_config.get("auth_code")
    receivers = email_config.get("receivers", [])

    if not smtp_host:
        raise exceptions.NotificationError("email.smtp_host is required when enabled=true")

    if not receivers or len(receivers) == 0:
        raise exceptions.NotificationError(
            "email.receivers must be a non-empty list when enabled=true"
        )

    # Build email content
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    subject = f"[DYChatBot] 账号异常告警 - {account_name}"
    body = f"""账号: {account_name}
错误类型: {error_type}
错误详情: {error_detail}
发生时间: {timestamp}

请及时检查系统状态。"""

    # Create email message
    message = EmailMessage()
    message["From"] = sender
    message["To"] = ", ".join(receivers)
    message["Subject"] = subject
    message.set_content(body)

    # Send email via SMTP_SSL
    try:
        with smtplib.SMTP_SSL(smtp_host, smtp_port) as server:
            server.login(sender, auth_code)
            server.send_message(message)
    except Exception as e:
        raise exceptions.NotificationError(f"Failed to send email: {e}") from e
