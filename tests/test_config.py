"""Tests for utils/config module.

These tests verify config loading and validation according to Task 1.3a.
"""

import json
import tempfile
from pathlib import Path

import pytest

from core import exceptions


class TestConfigLoading:
    """Test configuration file loading."""

    @pytest.fixture
    def valid_config(self) -> dict:
        """Return a valid configuration dictionary."""
        return {
            "accounts": [
                {
                    "name": "店铺A",
                    "username": "account1",
                    "password": "password1",
                    "direct_url": "https://life.douyin.com/cs/web/xxx",
                }
            ],
            "monitor": {
                "user_list_size": 10,
                "poll_interval_seconds": 1,
            },
            "retry": {
                "login_max_retries": 3,
                "element_wait_timeout_seconds": 30,
                "element_max_retries": 3,
            },
            "email": {
                "enabled": True,
                "smtp_host": "smtp.qq.com",
                "smtp_port": 465,
                "sender": "test@qq.com",
                "auth_code": "auth123",
                "receivers": ["receiver@example.com"],
            },
            "logging": {
                "level": "INFO",
                "log_dir": "logs",
            },
        }

    @pytest.mark.parametrize(
        "config",
        [
            # Missing accounts
            {
                "monitor": {"user_list_size": 10, "poll_interval_seconds": 1},
                "retry": {"login_max_retries": 3, "element_wait_timeout_seconds": 30, "element_max_retries": 3},
                "email": {"enabled": False},
                "logging": {"level": "INFO", "log_dir": "logs"},
            },
            # Missing monitor
            {
                "accounts": [{"name": "test", "username": "u", "password": "p", "direct_url": ""}],
                "retry": {"login_max_retries": 3, "element_wait_timeout_seconds": 30, "element_max_retries": 3},
                "email": {"enabled": False},
                "logging": {"level": "INFO", "log_dir": "logs"},
            },
            # Missing retry
            {
                "accounts": [{"name": "test", "username": "u", "password": "p", "direct_url": ""}],
                "monitor": {"user_list_size": 10, "poll_interval_seconds": 1},
                "email": {"enabled": False},
                "logging": {"level": "INFO", "log_dir": "logs"},
            },
            # Missing email
            {
                "accounts": [{"name": "test", "username": "u", "password": "p", "direct_url": ""}],
                "monitor": {"user_list_size": 10, "poll_interval_seconds": 1},
                "retry": {"login_max_retries": 3, "element_wait_timeout_seconds": 30, "element_max_retries": 3},
                "logging": {"level": "INFO", "log_dir": "logs"},
            },
            # Missing logging
            {
                "accounts": [{"name": "test", "username": "u", "password": "p", "direct_url": ""}],
                "monitor": {"user_list_size": 10, "poll_interval_seconds": 1},
                "retry": {"login_max_retries": 3, "element_wait_timeout_seconds": 30, "element_max_retries": 3},
                "email": {"enabled": False},
            },
        ],
    )
    def test_missing_required_section_raises_config_error(self, config: dict):
        """Missing required config sections should raise ConfigError."""
        from utils import config as config_module

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(config, f)
            temp_path = Path(f.name)

        try:
            with pytest.raises(exceptions.ConfigError):
                config_module.load_config(temp_path)
        finally:
            temp_path.unlink(missing_ok=True)

    def test_config_file_not_found_raises_config_error(self):
        """Non-existent config file should raise ConfigError."""
        from utils import config as config_module

        with pytest.raises(exceptions.ConfigError):
            config_module.load_config(Path("/nonexistent/config.json"))

    def test_invalid_json_raises_config_error(self):
        """Invalid JSON format should raise ConfigError."""
        from utils import config as config_module

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("{ invalid json }")
            temp_path = Path(f.name)

        try:
            with pytest.raises(exceptions.ConfigError):
                config_module.load_config(temp_path)
        finally:
            temp_path.unlink(missing_ok=True)

    def test_empty_accounts_list_raises_config_error(self, valid_config: dict):
        """Empty accounts list should raise ConfigError."""
        from utils import config as config_module

        valid_config["accounts"] = []

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(valid_config, f)
            temp_path = Path(f.name)

        try:
            with pytest.raises(exceptions.ConfigError):
                config_module.load_config(temp_path)
        finally:
            temp_path.unlink(missing_ok=True)


class TestConfigValidation:
    """Test configuration field validation."""

    @pytest.mark.parametrize(
        "config,field",
        [
            # poll_interval as string
            (
                {
                    "accounts": [{"name": "test", "username": "u", "password": "p", "direct_url": ""}],
                    "monitor": {"user_list_size": 10, "poll_interval_seconds": "1"},
                    "retry": {"login_max_retries": 3, "element_wait_timeout_seconds": 30, "element_max_retries": 3},
                    "email": {"enabled": False},
                    "logging": {"level": "INFO", "log_dir": "logs"},
                },
                "poll_interval_seconds",
            ),
            # user_list_size as string
            (
                {
                    "accounts": [{"name": "test", "username": "u", "password": "p", "direct_url": ""}],
                    "monitor": {"user_list_size": "10", "poll_interval_seconds": 1},
                    "retry": {"login_max_retries": 3, "element_wait_timeout_seconds": 30, "element_max_retries": 3},
                    "email": {"enabled": False},
                    "logging": {"level": "INFO", "log_dir": "logs"},
                },
                "user_list_size",
            ),
            # login_max_retries as string
            (
                {
                    "accounts": [{"name": "test", "username": "u", "password": "p", "direct_url": ""}],
                    "monitor": {"user_list_size": 10, "poll_interval_seconds": 1},
                    "retry": {"login_max_retries": "3", "element_wait_timeout_seconds": 30, "element_max_retries": 3},
                    "email": {"enabled": False},
                    "logging": {"level": "INFO", "log_dir": "logs"},
                },
                "login_max_retries",
            ),
        ],
    )
    def test_field_type_error_raises_config_error(self, config: dict, field: str):
        """Wrong field type should raise ConfigError."""
        from utils import config as config_module

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(config, f)
            temp_path = Path(f.name)

        try:
            with pytest.raises(exceptions.ConfigError):
                config_module.load_config(temp_path)
        finally:
            temp_path.unlink(missing_ok=True)

    def test_email_enabled_false_smtp_optional(self):
        """When email.enabled=false, SMTP fields should be optional."""
        from utils import config as config_module

        config = {
            "accounts": [{"name": "test", "username": "u", "password": "p", "direct_url": ""}],
            "monitor": {"user_list_size": 10, "poll_interval_seconds": 1},
            "retry": {"login_max_retries": 3, "element_wait_timeout_seconds": 30, "element_max_retries": 3},
            "email": {"enabled": False},
            "logging": {"level": "INFO", "log_dir": "logs"},
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(config, f)
            temp_path = Path(f.name)

        try:
            result = config_module.load_config(temp_path)
            assert result["email"]["enabled"] is False
        finally:
            temp_path.unlink(missing_ok=True)


class TestConfigLoad:
    """Test successful config loading."""

    def test_valid_config_loads_successfully(self):
        """Valid config should be loaded and returned as dict."""
        from utils import config as config_module

        config = {
            "accounts": [
                {
                    "name": "店铺A",
                    "username": "account1",
                    "password": "password1",
                    "direct_url": "https://life.douyin.com/cs/web/xxx",
                }
            ],
            "monitor": {"user_list_size": 10, "poll_interval_seconds": 1},
            "retry": {"login_max_retries": 3, "element_wait_timeout_seconds": 30, "element_max_retries": 3},
            "email": {"enabled": True, "smtp_host": "smtp.qq.com", "smtp_port": 465, "sender": "test@qq.com", "auth_code": "auth", "receivers": ["a@b.com"]},
            "logging": {"level": "INFO", "log_dir": "logs"},
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(config, f)
            temp_path = Path(f.name)

        try:
            result = config_module.load_config(temp_path)
            assert result["accounts"][0]["name"] == "店铺A"
            assert result["monitor"]["user_list_size"] == 10
            assert result["email"]["enabled"] is True
        finally:
            temp_path.unlink(missing_ok=True)
