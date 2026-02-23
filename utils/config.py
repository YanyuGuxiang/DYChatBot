"""Configuration loading and validation for DYChatBot.

This module loads and validates the config.json file.
"""

import json
from pathlib import Path
from typing import Any

from core import exceptions


REQUIRED_SECTIONS = ["accounts", "monitor", "retry", "email", "logging"]

ACCOUNT_REQUIRED_FIELDS = ["name", "username", "password"]

MONITOR_REQUIRED_FIELDS = ["user_list_size", "poll_interval_seconds"]

RETRY_REQUIRED_FIELDS = [
    "login_max_retries",
    "element_wait_timeout_seconds",
    "element_max_retries",
]

LOGGING_REQUIRED_FIELDS = ["level", "log_dir"]

EMAIL_REQUIRED_FIELDS_WHEN_ENABLED = [
    "smtp_host",
    "smtp_port",
    "sender",
    "auth_code",
    "receivers",
]


def _validate_account(account: dict[str, Any], account_idx: int) -> None:
    """Validate a single account configuration."""
    for field in ACCOUNT_REQUIRED_FIELDS:
        if field not in account:
            raise exceptions.ConfigError(
                f"accounts[{account_idx}]: missing required field '{field}'"
            )


def _validate_monitor(monitor: dict[str, Any]) -> None:
    """Validate monitor section."""
    for field in MONITOR_REQUIRED_FIELDS:
        if field not in monitor:
            raise exceptions.ConfigError(f"monitor: missing required field '{field}'")
        if not isinstance(monitor[field], int):
            raise exceptions.ConfigError(
                f"monitor.{field} must be an integer, got {type(monitor[field]).__name__}"
            )


def _validate_retry(retry: dict[str, Any]) -> None:
    """Validate retry section."""
    for field in RETRY_REQUIRED_FIELDS:
        if field not in retry:
            raise exceptions.ConfigError(f"retry: missing required field '{field}'")
        if not isinstance(retry[field], int):
            raise exceptions.ConfigError(
                f"retry.{field} must be an integer, got {type(retry[field]).__name__}"
            )


def _validate_logging(logging_cfg: dict[str, Any]) -> None:
    """Validate logging section."""
    for field in LOGGING_REQUIRED_FIELDS:
        if field not in logging_cfg:
            raise exceptions.ConfigError(f"logging: missing required field '{field}'")


def _validate_email(email: dict[str, Any]) -> None:
    """Validate email section."""
    enabled = email.get("enabled", False)
    if not isinstance(enabled, bool):
        raise exceptions.ConfigError("email.enabled must be a boolean")

    if enabled:
        for field in EMAIL_REQUIRED_FIELDS_WHEN_ENABLED:
            if field not in email:
                raise exceptions.ConfigError(
                    f"email: missing required field '{field}' when enabled=true"
                )
        if not isinstance(email["receivers"], list) or len(email["receivers"]) == 0:
            raise exceptions.ConfigError(
                "email.receivers must be a non-empty list when enabled=true"
            )


def load_config(path: Path) -> dict[str, Any]:
    """Load and validate configuration from JSON file.

    Args:
        path: Path to config.json file.

    Returns:
        Validated configuration dictionary.

    Raises:
        ConfigError: If config file is missing, malformed, or validation fails.
    """
    if not path.exists():
        raise exceptions.ConfigError(f"Config file not found: {path}")

    try:
        with open(path, "r", encoding="utf-8") as f:
            config = json.load(f)
    except json.JSONDecodeError as e:
        raise exceptions.ConfigError(f"Invalid JSON in config file: {e}") from e

    if not isinstance(config, dict):
        raise exceptions.ConfigError("Config file must contain a JSON object")

    # Validate required top-level sections
    for section in REQUIRED_SECTIONS:
        if section not in config:
            raise exceptions.ConfigError(f"Missing required config section: {section}")

    # Validate accounts
    accounts = config["accounts"]
    if not isinstance(accounts, list):
        raise exceptions.ConfigError("accounts must be a list")
    if len(accounts) == 0:
        raise exceptions.ConfigError("accounts list cannot be empty")

    for idx, account in enumerate(accounts):
        _validate_account(account, idx)

    # Validate monitor
    _validate_monitor(config["monitor"])

    # Validate retry
    _validate_retry(config["retry"])

    # Validate email
    _validate_email(config["email"])

    # Validate logging
    _validate_logging(config["logging"])

    return config
