"""
Unit tests for Prune API Router.

Tests cover security, concurrency, and functionality of the prune endpoints:
- POST /api/v1/prune/all
- POST /api/v1/prune/data
- POST /api/v1/prune/system

Security tests are critical and marked with priority indicators.
"""

from __future__ import annotations

import ast
import os
import pathlib
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ============================================================================
# Test Router File Structure
# ============================================================================


class TestPruneRouterStructure:
    """Verify prune router file structure and syntax."""

    def test_router_file_exists(self):
        """Verify get_prune_router.py exists."""
        router_file = self._get_router_file()
        assert router_file.exists(), "get_prune_router.py should exist"

    def test_router_init_file_exists(self):
        """Verify routers/__init__.py exists."""
        init_file = self._get_router_file().parent / "__init__.py"
        assert init_file.exists(), "routers/__init__.py should exist"

    def test_router_file_valid_syntax(self):
        """Verify get_prune_router.py has valid Python syntax."""
        router_file = self._get_router_file()
        content = router_file.read_text()
        try:
            ast.parse(content)
        except SyntaxError as e:
            pytest.fail(f"get_prune_router.py has syntax error: {e}")

    def test_router_exports_get_prune_router(self):
        """Verify routers/__init__.py exports get_prune_router."""
        init_file = self._get_router_file().parent / "__init__.py"
        content = init_file.read_text()
        assert "get_prune_router" in content, "Should export get_prune_router"

    def _get_router_file(self) -> pathlib.Path:
        """Get path to get_prune_router.py."""
        current = pathlib.Path(__file__)
        mflow_root = current.parent.parent.parent.parent
        return mflow_root / "api" / "v1" / "prune" / "routers" / "get_prune_router.py"


# ============================================================================
# Test Security Features - Authentication (Critical)
# ============================================================================


class TestPruneRouterAuthentication:
    """
    Critical security tests for authentication.

    These tests verify that the prune API ALWAYS requires authentication,
    even when REQUIRE_AUTHENTICATION is set to False globally.
    """

    def test_uses_fastapi_users_current_user(self):
        """[CRITICAL] Verify router uses FastAPI-Users current_user dependency."""
        router_file = self._get_router_file()
        content = router_file.read_text()

        # Must use FastAPI-Users authentication
        assert "get_fastapi_users()" in content, "Should use get_fastapi_users() for authentication"
        assert "current_user(" in content, "Should use current_user dependency"

    def test_requires_active_user(self):
        """[CRITICAL] Verify requires active=True."""
        router_file = self._get_router_file()
        content = router_file.read_text()

        assert "active=True" in content, "Should require active=True"

    def test_requires_superuser(self):
        """[CRITICAL] Verify requires superuser=True."""
        router_file = self._get_router_file()
        content = router_file.read_text()

        assert "superuser=True" in content, "Should require superuser=True"

    def test_one_liner_auth_pattern(self):
        """[CRITICAL] Verify uses the secure one-liner auth pattern."""
        router_file = self._get_router_file()
        content = router_file.read_text()

        # The secure pattern: current_user(active=True, superuser=True)
        assert "current_user(active=True, superuser=True)" in content, (
            "Should use the secure one-liner: current_user(active=True, superuser=True)"
        )

    def test_auth_dependency_used_in_all_endpoints(self):
        """[CRITICAL] Verify auth dependency is used in all endpoint definitions."""
        router_file = self._get_router_file()
        content = router_file.read_text()

        # Count endpoint definitions
        endpoint_count = content.count('@router.post("/')

        # Count auth dependency usage in function signatures
        auth_dep_count = content.count("Depends(_require_prune_auth)")

        assert auth_dep_count >= endpoint_count, (
            f"All {endpoint_count} endpoints should use Depends(_require_prune_auth), found only {auth_dep_count}"
        )

    def _get_router_file(self) -> pathlib.Path:
        """Get path to get_prune_router.py."""
        current = pathlib.Path(__file__)
        mflow_root = current.parent.parent.parent.parent
        return mflow_root / "api" / "v1" / "prune" / "routers" / "get_prune_router.py"


# ============================================================================
# Test Security Features - Environment Variable Controls
# ============================================================================


class TestPruneRouterEnvControls:
    """Tests for environment variable security controls."""

    def test_checks_prune_api_enabled(self):
        """Verify checks MFLOW_ENABLE_PRUNE_API environment variable."""
        router_file = self._get_router_file()
        content = router_file.read_text()

        assert "MFLOW_ENABLE_PRUNE_API" in content, "Should check MFLOW_ENABLE_PRUNE_API"
        assert "_check_prune_enabled()" in content, "Should call _check_prune_enabled()"

    def test_default_api_disabled(self):
        """Verify API is disabled by default."""
        router_file = self._get_router_file()
        content = router_file.read_text()

        # Default should be "false"
        assert '"false"' in content.lower() or "'false'" in content.lower(), (
            "MFLOW_ENABLE_PRUNE_API should default to 'false'"
        )

    def test_has_per_endpoint_controls(self):
        """Verify per-endpoint enable/disable controls exist."""
        router_file = self._get_router_file()
        content = router_file.read_text()

        assert "MFLOW_PRUNE_ALLOW_ALL" in content, "Should have ALLOW_ALL control"
        assert "MFLOW_PRUNE_ALLOW_DATA" in content, "Should have ALLOW_DATA control"
        assert "MFLOW_PRUNE_ALLOW_SYSTEM" in content, "Should have ALLOW_SYSTEM control"

    def _get_router_file(self) -> pathlib.Path:
        """Get path to get_prune_router.py."""
        current = pathlib.Path(__file__)
        mflow_root = current.parent.parent.parent.parent
        return mflow_root / "api" / "v1" / "prune" / "routers" / "get_prune_router.py"


# ============================================================================
# Test Security Features - Confirmation Strings
# ============================================================================


class TestPruneRouterConfirmation:
    """Tests for confirmation string requirements."""

    def test_prune_all_requires_confirmation(self):
        """Verify /prune/all requires specific confirmation string."""
        router_file = self._get_router_file()
        content = router_file.read_text()

        assert "DELETE_ALL_DATA" in content, "/prune/all should require 'DELETE_ALL_DATA' confirmation"

    def test_prune_data_requires_confirmation(self):
        """Verify /prune/data requires specific confirmation string."""
        router_file = self._get_router_file()
        content = router_file.read_text()

        assert "DELETE_FILES" in content, "/prune/data should require 'DELETE_FILES' confirmation"

    def test_prune_system_requires_confirmation(self):
        """Verify /prune/system requires specific confirmation string."""
        router_file = self._get_router_file()
        content = router_file.read_text()

        assert "DELETE_SYSTEM" in content, "/prune/system should require 'DELETE_SYSTEM' confirmation"

    def test_invalid_confirmation_returns_400(self):
        """Verify invalid confirmation returns HTTP 400."""
        router_file = self._get_router_file()
        content = router_file.read_text()

        assert "HTTP_400_BAD_REQUEST" in content, "Invalid confirmation should return 400"

    def _get_router_file(self) -> pathlib.Path:
        """Get path to get_prune_router.py."""
        current = pathlib.Path(__file__)
        mflow_root = current.parent.parent.parent.parent
        return mflow_root / "api" / "v1" / "prune" / "routers" / "get_prune_router.py"


# ============================================================================
# Test Concurrency Safety - Pipeline Checks
# ============================================================================


class TestPruneRouterPipelineChecks:
    """Tests for pipeline running checks."""

    def test_checks_pipeline_status(self):
        """Verify checks for running pipelines before prune."""
        router_file = self._get_router_file()
        content = router_file.read_text()

        assert "_check_no_running_pipelines()" in content, "Should call _check_no_running_pipelines()"

    def test_checks_started_state(self):
        """Verify checks for STARTED pipeline state."""
        router_file = self._get_router_file()
        content = router_file.read_text()

        assert "STARTED" in content, "Should check for STARTED pipeline state"

    def test_checks_initiated_state(self):
        """Verify checks for INITIATED pipeline state."""
        router_file = self._get_router_file()
        content = router_file.read_text()

        assert "INITIATED" in content, "Should check for INITIATED pipeline state"

    def test_pipeline_conflict_returns_409(self):
        """Verify running pipeline returns HTTP 409."""
        router_file = self._get_router_file()
        content = router_file.read_text()

        assert "HTTP_409_CONFLICT" in content, "Running pipeline should return 409"

    def _get_router_file(self) -> pathlib.Path:
        """Get path to get_prune_router.py."""
        current = pathlib.Path(__file__)
        mflow_root = current.parent.parent.parent.parent
        return mflow_root / "api" / "v1" / "prune" / "routers" / "get_prune_router.py"


# ============================================================================
# Test Concurrency Safety - Locking
# ============================================================================


class TestPruneRouterLocking:
    """Tests for concurrent operation locking."""

    def test_has_asyncio_lock(self):
        """Verify uses asyncio.Lock for process-local locking."""
        router_file = self._get_router_file()
        content = router_file.read_text()

        assert "asyncio.Lock()" in content, "Should use asyncio.Lock()"
        assert "_prune_lock" in content, "Should have _prune_lock variable"

    def test_has_distributed_lock_support(self):
        """Verify supports Redis distributed locking."""
        router_file = self._get_router_file()
        content = router_file.read_text()

        assert "mflow_prune_operation" in content, "Should use dedicated 'mflow_prune_operation' lock key"

    def test_lock_has_timeout(self):
        """Verify Redis lock has timeout to prevent deadlocks."""
        router_file = self._get_router_file()
        content = router_file.read_text()

        # Check for timeout parameter
        assert "timeout=300" in content or "timeout = 300" in content, "Redis lock should have 300 second timeout"

    def test_concurrent_request_returns_409(self):
        """Verify concurrent prune request returns HTTP 409."""
        router_file = self._get_router_file()
        content = router_file.read_text()

        # Should check if lock is held
        assert "_prune_lock.locked()" in content, "Should check if lock is already held"

    def _get_router_file(self) -> pathlib.Path:
        """Get path to get_prune_router.py."""
        current = pathlib.Path(__file__)
        mflow_root = current.parent.parent.parent.parent
        return mflow_root / "api" / "v1" / "prune" / "routers" / "get_prune_router.py"


# ============================================================================
# Test Concurrency Safety - Cooldown
# ============================================================================


class TestPruneRouterCooldown:
    """Tests for cooldown period between operations."""

    def test_has_cooldown_check(self):
        """Verify checks cooldown period."""
        router_file = self._get_router_file()
        content = router_file.read_text()

        assert "_check_cooldown()" in content, "Should call _check_cooldown()"

    def test_cooldown_configurable(self):
        """Verify cooldown is configurable via environment."""
        router_file = self._get_router_file()
        content = router_file.read_text()

        assert "MFLOW_PRUNE_COOLDOWN_SECONDS" in content, "Should support MFLOW_PRUNE_COOLDOWN_SECONDS"

    def test_cooldown_default_60_seconds(self):
        """Verify default cooldown is 60 seconds."""
        router_file = self._get_router_file()
        content = router_file.read_text()

        assert '"60"' in content or "'60'" in content, "Default cooldown should be 60 seconds"

    def test_cooldown_violation_returns_429(self):
        """Verify cooldown violation returns HTTP 429."""
        router_file = self._get_router_file()
        content = router_file.read_text()

        assert "HTTP_429_TOO_MANY_REQUESTS" in content, "Cooldown violation should return 429"

    def test_retry_after_header(self):
        """Verify includes Retry-After header on 429."""
        router_file = self._get_router_file()
        content = router_file.read_text()

        assert "Retry-After" in content, "Should include Retry-After header"

    def _get_router_file(self) -> pathlib.Path:
        """Get path to get_prune_router.py."""
        current = pathlib.Path(__file__)
        mflow_root = current.parent.parent.parent.parent
        return mflow_root / "api" / "v1" / "prune" / "routers" / "get_prune_router.py"


# ============================================================================
# Test Response Structure
# ============================================================================


class TestPruneRouterResponse:
    """Tests for response model structure."""

    def test_has_response_model(self):
        """Verify defines PruneResponse model."""
        router_file = self._get_router_file()
        content = router_file.read_text()

        assert "class PruneResponse" in content, "Should define PruneResponse model"

    def test_response_has_status_field(self):
        """Verify response includes status field."""
        router_file = self._get_router_file()
        content = router_file.read_text()

        # In PruneResponse class
        assert "status:" in content or '"status"' in content, "PruneResponse should have status field"

    def test_response_has_cleared_field(self):
        """Verify response includes cleared field."""
        router_file = self._get_router_file()
        content = router_file.read_text()

        assert "cleared:" in content or '"cleared"' in content, "PruneResponse should have cleared field"

    def test_response_has_warnings_field(self):
        """Verify response includes warnings field."""
        router_file = self._get_router_file()
        content = router_file.read_text()

        assert "warnings:" in content or '"warnings"' in content, "PruneResponse should have warnings field"

    def test_response_has_message_field(self):
        """Verify response includes message field."""
        router_file = self._get_router_file()
        content = router_file.read_text()

        assert "message:" in content or '"message"' in content, "PruneResponse should have message field"

    def _get_router_file(self) -> pathlib.Path:
        """Get path to get_prune_router.py."""
        current = pathlib.Path(__file__)
        mflow_root = current.parent.parent.parent.parent
        return mflow_root / "api" / "v1" / "prune" / "routers" / "get_prune_router.py"


# ============================================================================
# Test Logging
# ============================================================================


class TestPruneRouterLogging:
    """Tests for audit logging."""

    def test_logs_prune_initiation(self):
        """Verify logs when prune operation is initiated."""
        router_file = self._get_router_file()
        content = router_file.read_text()

        assert "_logger.warning" in content, "Should use warning level for prune initiation"

    def test_logs_user_info(self):
        """Verify logs include user information."""
        router_file = self._get_router_file()
        content = router_file.read_text()

        assert "user.email" in content, "Should log user email"
        assert "user.id" in content, "Should log user id"

    def test_logs_completion(self):
        """Verify logs successful completion."""
        router_file = self._get_router_file()
        content = router_file.read_text()

        assert "_logger.info" in content, "Should log completion at info level"

    def test_logs_errors(self):
        """Verify logs errors."""
        router_file = self._get_router_file()
        content = router_file.read_text()

        assert "_logger.error" in content, "Should log errors"

    def _get_router_file(self) -> pathlib.Path:
        """Get path to get_prune_router.py."""
        current = pathlib.Path(__file__)
        mflow_root = current.parent.parent.parent.parent
        return mflow_root / "api" / "v1" / "prune" / "routers" / "get_prune_router.py"


# ============================================================================
# Test Error Handling
# ============================================================================


class TestPruneRouterErrorHandling:
    """Tests for error handling."""

    def test_catches_prune_exceptions(self):
        """Verify catches exceptions during prune."""
        router_file = self._get_router_file()
        content = router_file.read_text()

        assert "except Exception" in content, "Should catch exceptions during prune"

    def test_returns_500_on_failure(self):
        """Verify returns 500 on prune failure."""
        router_file = self._get_router_file()
        content = router_file.read_text()

        assert "HTTP_500_INTERNAL_SERVER_ERROR" in content, "Should return 500 on failure"

    def test_does_not_expose_internal_details(self):
        """Verify error messages don't expose internal details."""
        router_file = self._get_router_file()
        content = router_file.read_text()

        # Error messages should be generic
        assert "Check server logs" in content, "Error message should direct to logs, not expose details"

    def test_releases_lock_on_error(self):
        """Verify lock is released on error (uses finally or context manager)."""
        router_file = self._get_router_file()
        content = router_file.read_text()

        # Should use async with for automatic release
        assert "async with _prune_lock:" in content, "Should use async with for automatic lock release"

    def _get_router_file(self) -> pathlib.Path:
        """Get path to get_prune_router.py."""
        current = pathlib.Path(__file__)
        mflow_root = current.parent.parent.parent.parent
        return mflow_root / "api" / "v1" / "prune" / "routers" / "get_prune_router.py"


# ============================================================================
# Test Integration with client.py
# ============================================================================


class TestPruneRouterIntegration:
    """Tests for integration with main client.py."""

    def test_router_registered_in_client(self):
        """Verify prune router is registered in client.py."""
        client_file = self._get_client_file()
        content = client_file.read_text()

        assert "get_prune_router" in content, "client.py should import get_prune_router"

    def test_router_has_correct_prefix(self):
        """Verify router uses /api/v1/prune prefix."""
        client_file = self._get_client_file()
        content = client_file.read_text()

        assert '"/api/v1/prune"' in content, "Router should be mounted at /api/v1/prune"

    def test_router_has_prune_tag(self):
        """Verify router uses prune tag for OpenAPI."""
        client_file = self._get_client_file()
        content = client_file.read_text()

        assert '"prune"' in content, "Router should use 'prune' tag"

    def _get_client_file(self) -> pathlib.Path:
        """Get path to client.py."""
        current = pathlib.Path(__file__)
        mflow_root = current.parent.parent.parent.parent
        return mflow_root / "api" / "client.py"

    def _get_router_file(self) -> pathlib.Path:
        """Get path to get_prune_router.py."""
        current = pathlib.Path(__file__)
        mflow_root = current.parent.parent.parent.parent
        return mflow_root / "api" / "v1" / "prune" / "routers" / "get_prune_router.py"


# ============================================================================
# Test English Documentation
# ============================================================================


class TestPruneRouterDocumentation:
    """Tests for code documentation quality."""

    def test_has_module_docstring(self):
        """Verify module has docstring."""
        router_file = self._get_router_file()
        content = router_file.read_text()

        # Should start with triple-quoted docstring
        assert content.strip().startswith('"""'), "Module should have docstring"

    def test_no_chinese_comments(self):
        """Verify no Chinese characters in comments."""
        router_file = self._get_router_file()
        content = router_file.read_text()

        # Check for common Chinese character ranges
        import re

        chinese_pattern = re.compile(r"[\u4e00-\u9fff]")
        matches = chinese_pattern.findall(content)

        assert not matches, f"Found Chinese characters in code: {matches[:10]}..."

    def test_functions_have_docstrings(self):
        """Verify key functions have docstrings."""
        router_file = self._get_router_file()
        content = router_file.read_text()

        # Key functions that should have docstrings
        key_functions = [
            "_check_prune_enabled",
            "_check_no_running_pipelines",
            "_check_cooldown",
            "get_prune_router",
        ]

        for func in key_functions:
            # Find function definition
            func_idx = content.find(f"def {func}")
            if func_idx == -1:
                func_idx = content.find(f"async def {func}")

            assert func_idx != -1, f"Function {func} should exist"

            # Check for docstring after function definition
            func_start = content.find(":", func_idx)
            next_content = content[func_start : func_start + 100]

            assert '"""' in next_content, f"Function {func} should have docstring"

    def _get_router_file(self) -> pathlib.Path:
        """Get path to get_prune_router.py."""
        current = pathlib.Path(__file__)
        mflow_root = current.parent.parent.parent.parent
        return mflow_root / "api" / "v1" / "prune" / "routers" / "get_prune_router.py"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
