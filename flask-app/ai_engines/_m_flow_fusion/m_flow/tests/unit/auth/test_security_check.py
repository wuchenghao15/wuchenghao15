"""
Unit tests for auth/security_check module.

Tests the production security check functionality for authentication secrets.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest

# Import from conftest which has the mocked dependencies
from . import conftest

security_check = conftest.security_check


@pytest.fixture(autouse=True)
def reset_warned_secrets():
    """Reset _warned_secrets set before and after each test."""
    security_check._warned_secrets.clear()
    yield
    security_check._warned_secrets.clear()


class TestGetSecretWithProductionCheck:
    """Tests for get_secret_with_production_check function."""

    def test_returns_env_value_when_set(self):
        """Should return environment variable value when it's set."""
        with patch.dict("os.environ", {"TEST_SECRET": "my_secure_value"}):
            result = security_check.get_secret_with_production_check("TEST_SECRET", "default_value", "test secret")
            assert result == "my_secure_value"

    def test_returns_default_in_development(self):
        """Should return default value in development environment."""
        # Test with no MFLOW_ENV set (defaults to development)
        with patch.dict("os.environ", {}, clear=True):
            result = security_check.get_secret_with_production_check("MISSING_SECRET", "dev_default", "test secret")
            assert result == "dev_default"

        # Test with explicit development values
        for env_value in ["development", "dev", "local", ""]:
            security_check._warned_secrets.clear()
            with patch.dict("os.environ", {"MFLOW_ENV": env_value}, clear=True):
                result = security_check.get_secret_with_production_check("MISSING_SECRET", "dev_default", "test secret")
                assert result == "dev_default", f"Failed for MFLOW_ENV={env_value!r}"

    def test_raises_in_production(self):
        """Should raise RuntimeError in production when secret is not set."""
        # Test various non-development environment values
        for env_value in ["production", "staging", "test", "prod"]:
            with patch.dict("os.environ", {"MFLOW_ENV": env_value}, clear=True):
                with pytest.raises(RuntimeError) as exc_info:
                    security_check.get_secret_with_production_check("MISSING_SECRET", "default_value", "test secret")

                assert "MISSING_SECRET" in str(exc_info.value)
                assert env_value in str(exc_info.value)
                assert "CRITICAL" in str(exc_info.value)

    def test_warns_only_once(self):
        """Should only warn once per secret in development."""
        with patch.dict("os.environ", {"MFLOW_ENV": "development"}, clear=True):
            with patch.object(security_check, "_log") as mock_log:
                # First call should warn
                security_check.get_secret_with_production_check("WARN_TEST_SECRET", "default", "test secret")
                assert mock_log.warning.call_count == 1

                # Second call with same secret should not warn
                security_check.get_secret_with_production_check("WARN_TEST_SECRET", "default", "test secret")
                assert mock_log.warning.call_count == 1

                # Different secret should warn
                security_check.get_secret_with_production_check("DIFFERENT_SECRET", "default", "other secret")
                assert mock_log.warning.call_count == 2

    def test_production_with_secret_set(self):
        """Should return value in production when secret IS set."""
        with patch.dict(
            "os.environ",
            {"MFLOW_ENV": "production", "PROD_SECRET": "secure_value"},
        ):
            result = security_check.get_secret_with_production_check(
                "PROD_SECRET", "default_value", "production secret"
            )
            assert result == "secure_value"


class TestEnvironmentWhitelist:
    """Tests verifying the whitelist-based security approach."""

    def test_unknown_env_requires_secrets(self):
        """Unknown environment values should require explicit secrets."""
        # Any value not in whitelist should be treated as production
        for env_value in ["PRODUCTION", "Production", "qa", "uat", "demo"]:
            with patch.dict("os.environ", {"MFLOW_ENV": env_value}, clear=True):
                with pytest.raises(RuntimeError):
                    security_check.get_secret_with_production_check("TEST_SECRET", "default", "test")

    def test_whitelist_is_case_insensitive(self):
        """Development environment check should be case-insensitive."""
        for env_value in ["DEVELOPMENT", "Development", "DEV", "Dev", "LOCAL", "Local"]:
            security_check._warned_secrets.clear()
            with patch.dict("os.environ", {"MFLOW_ENV": env_value}, clear=True):
                # Should not raise - these are all valid development values
                result = security_check.get_secret_with_production_check("TEST_SECRET", "default", "test")
                assert result == "default", f"Failed for MFLOW_ENV={env_value!r}"
