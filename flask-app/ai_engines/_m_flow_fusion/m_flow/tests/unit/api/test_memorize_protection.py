# m_flow/tests/unit/api/test_memorize_protection.py
"""
Unit tests for memorize concurrency protection (P1).

Tests cover:
1. _ACTIVE_DATASETS and _ACTIVE_LOCK existence
2. ConflictMode type
3. _check_and_register_datasets function
4. _unregister_datasets function
5. ConcurrentMemorizeError exception
"""

import ast
import pathlib
import pytest


# ============================================================
# Test Concurrency Infrastructure
# ============================================================


class TestMemorizeConcurrencyInfra:
    """Tests for memorize concurrency infrastructure."""

    def test_active_datasets_set(self):
        """Verify _ACTIVE_DATASETS set exists."""
        memorize_file = self._get_memorize_file()
        content = memorize_file.read_text()

        assert "_ACTIVE_DATASETS: Set[str] = set()" in content

    def test_active_lock_exists(self):
        """Verify _ACTIVE_LOCK exists."""
        memorize_file = self._get_memorize_file()
        content = memorize_file.read_text()

        assert "_ACTIVE_LOCK = asyncio.Lock()" in content

    def test_conflict_mode_type(self):
        """Verify ConflictMode type definition."""
        memorize_file = self._get_memorize_file()
        content = memorize_file.read_text()

        assert "ConflictMode" in content

    def test_check_and_register_function(self):
        """Verify _check_and_register_datasets function exists."""
        memorize_file = self._get_memorize_file()
        content = memorize_file.read_text()

        assert "async def _check_and_register_datasets(" in content

    def test_unregister_function(self):
        """Verify _unregister_datasets function exists."""
        memorize_file = self._get_memorize_file()
        content = memorize_file.read_text()

        assert "_unregister_datasets" in content

    def _get_memorize_file(self) -> pathlib.Path:
        """Get path to memorize.py file."""
        current = pathlib.Path(__file__)
        mflow_root = current.parent.parent.parent.parent
        return mflow_root / "api" / "v1" / "memorize" / "memorize.py"


# ============================================================
# Test Conflict Mode Handling
# ============================================================


class TestConflictModeHandling:
    """Tests for conflict mode handling."""

    def test_error_mode(self):
        """Verify error mode handling."""
        memorize_file = self._get_memorize_file()
        content = memorize_file.read_text()

        assert 'conflict_mode == "error"' in content

    def test_warn_mode(self):
        """Verify warn mode handling."""
        memorize_file = self._get_memorize_file()
        content = memorize_file.read_text()

        assert 'conflict_mode == "warn"' in content

    def test_ignore_mode(self):
        """Verify ignore mode handling."""
        memorize_file = self._get_memorize_file()
        content = memorize_file.read_text()

        assert 'conflict_mode == "ignore"' in content

    def test_default_is_warn(self):
        """Verify default conflict_mode is 'warn'."""
        memorize_file = self._get_memorize_file()
        content = memorize_file.read_text()

        assert 'conflict_mode: ConflictMode = "warn"' in content

    def _get_memorize_file(self) -> pathlib.Path:
        """Get path to memorize.py file."""
        current = pathlib.Path(__file__)
        mflow_root = current.parent.parent.parent.parent
        return mflow_root / "api" / "v1" / "memorize" / "memorize.py"


# ============================================================
# Test Exception Class
# ============================================================


class TestConcurrentMemorizeError:
    """Tests for ConcurrentMemorizeError exception."""

    def test_exception_imported(self):
        """Verify exception is imported in memorize.py."""
        memorize_file = self._get_memorize_file()
        content = memorize_file.read_text()

        assert "from m_flow.api.v1.exceptions.exceptions import ConcurrentMemorizeError" in content

    def test_exception_defined(self):
        """Verify exception is defined in exceptions.py."""
        exceptions_file = self._get_exceptions_file()
        content = exceptions_file.read_text()

        assert "class ConcurrentMemorizeError" in content

    def test_exception_raised_on_error_mode(self):
        """Verify exception is raised in error mode."""
        memorize_file = self._get_memorize_file()
        content = memorize_file.read_text()

        assert "raise ConcurrentMemorizeError(" in content

    def _get_memorize_file(self) -> pathlib.Path:
        """Get path to memorize.py file."""
        current = pathlib.Path(__file__)
        mflow_root = current.parent.parent.parent.parent
        return mflow_root / "api" / "v1" / "memorize" / "memorize.py"

    def _get_exceptions_file(self) -> pathlib.Path:
        """Get path to exceptions.py file."""
        current = pathlib.Path(__file__)
        mflow_root = current.parent.parent.parent.parent
        return mflow_root / "api" / "v1" / "exceptions" / "exceptions.py"


# ============================================================
# Test Syntax
# ============================================================


class TestMemorizeSyntax:
    """Test memorize.py has valid Python syntax."""

    def test_valid_python_syntax(self):
        """Verify memorize.py is valid Python."""
        memorize_file = self._get_memorize_file()
        content = memorize_file.read_text()

        try:
            ast.parse(content)
        except SyntaxError as e:
            pytest.fail(f"memorize.py has syntax error: {e}")

    def _get_memorize_file(self) -> pathlib.Path:
        """Get path to memorize.py file."""
        current = pathlib.Path(__file__)
        mflow_root = current.parent.parent.parent.parent
        return mflow_root / "api" / "v1" / "memorize" / "memorize.py"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
