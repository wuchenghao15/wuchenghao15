# m_flow/tests/unit/api/test_prune.py
"""
Unit tests for prune module (P0).

Tests cover:
1. prune.all() method existence and structure
2. prune_system(metadata=False) warning behavior
3. dispatch_function.py integration
4. __main__ block correctness
"""

import ast
import pathlib
import pytest


# ============================================================
# Test prune.all() Method
# ============================================================


class TestPruneAllMethod:
    """Tests for prune.all() static method."""

    def test_prune_all_exists(self):
        """Verify prune.all() method exists in source code."""
        prune_file = self._get_prune_file()
        content = prune_file.read_text()

        assert "async def all(" in content, "prune.all() method not found"

    def test_prune_all_calls_prune_data(self):
        """Verify prune.all() calls _do_prune_data."""
        prune_file = self._get_prune_file()
        content = prune_file.read_text()

        # Find all() method body
        assert "_do_prune_data()" in content, "prune.all() should call _do_prune_data()"

    def test_prune_all_calls_prune_system_with_metadata_true(self):
        """Verify prune.all() calls _do_prune_system with metadata=True."""
        prune_file = self._get_prune_file()
        content = prune_file.read_text()

        # Find the call with metadata=True
        assert "metadata=True" in content, "prune.all() should use metadata=True"

    def test_prune_all_has_exception_handling(self):
        """Verify prune.all() has proper exception handling."""
        prune_file = self._get_prune_file()
        content = prune_file.read_text()

        # Check for try/except
        assert "try:" in content and "except Exception" in content, "prune.all() should have exception handling"

    def test_prune_all_has_logging(self):
        """Verify prune.all() has logging."""
        prune_file = self._get_prune_file()
        content = prune_file.read_text()

        assert "_logger.info" in content, "prune.all() should have info logging"
        assert "_logger.error" in content, "prune.all() should have error logging"

    def _get_prune_file(self) -> pathlib.Path:
        """Get path to prune.py file."""
        current = pathlib.Path(__file__)
        # tests/unit/api/ -> m_flow/api/v1/prune/
        mflow_root = current.parent.parent.parent.parent
        return mflow_root / "api" / "v1" / "prune" / "prune.py"


# ============================================================
# Test prune_system Warning Behavior
# ============================================================


class TestPruneSystemWarning:
    """Tests for prune_system(metadata=False) warning."""

    def test_warning_when_metadata_false(self):
        """Verify warning is issued when metadata=False."""
        prune_file = self._get_prune_file()
        content = prune_file.read_text()

        # Check warning logic exists
        assert "if not metadata:" in content, "Should check for metadata=False"
        assert "warnings.warn(" in content, "Should use warnings.warn()"
        assert "UserWarning" in content, "Should use UserWarning type"

    def test_warning_stacklevel(self):
        """Verify warning uses stacklevel=2."""
        prune_file = self._get_prune_file()
        content = prune_file.read_text()

        assert "stacklevel=2" in content, "Warning should use stacklevel=2"

    def test_logger_warning_also_called(self):
        """Verify _logger.warning is also called for visibility."""
        prune_file = self._get_prune_file()
        content = prune_file.read_text()

        assert "_logger.warning" in content, "Should also log warning"

    def _get_prune_file(self) -> pathlib.Path:
        """Get path to prune.py file."""
        current = pathlib.Path(__file__)
        mflow_root = current.parent.parent.parent.parent
        return mflow_root / "api" / "v1" / "prune" / "prune.py"


# ============================================================
# Test dispatch_function.py Bug Fix
# ============================================================


class TestDispatchFunctionFix:
    """Tests for dispatch_function.py bug fix."""

    def test_uses_prune_all(self):
        """Verify dispatch_function uses prune.all() not prune()."""
        dispatch_file = self._get_dispatch_file()
        content = dispatch_file.read_text()

        assert "await prune.all()" in content, "Should use prune.all()"

    def test_no_wrong_prune_call(self):
        """Verify no incorrect await prune() calls."""
        dispatch_file = self._get_dispatch_file()
        content = dispatch_file.read_text()

        # Replace prune.all() to check for remaining prune() calls
        test_content = content.replace("prune.all()", "")

        # Should not have standalone await prune()
        assert "await prune()" not in test_content, "Should not have incorrect await prune() call"

    def _get_dispatch_file(self) -> pathlib.Path:
        """Get path to dispatch_function.py file."""
        current = pathlib.Path(__file__)
        mflow_root = current.parent.parent.parent.parent
        return mflow_root / "api" / "v1" / "responses" / "dispatch_function.py"


# ============================================================
# Test __main__ Block
# ============================================================


class TestPruneMainBlock:
    """Tests for prune.py __main__ block."""

    def test_main_uses_prune_all(self):
        """Verify __main__ block uses prune.all()."""
        prune_file = self._get_prune_file()
        content = prune_file.read_text()

        # Find __main__ block
        assert 'if __name__ == "__main__":' in content, "Should have __main__ block"

        # The __main__ block should use prune.all()
        main_idx = content.find('if __name__ == "__main__":')
        main_block = content[main_idx:]

        assert "await prune.all()" in main_block, "__main__ should use prune.all()"

    def _get_prune_file(self) -> pathlib.Path:
        """Get path to prune.py file."""
        current = pathlib.Path(__file__)
        mflow_root = current.parent.parent.parent.parent
        return mflow_root / "api" / "v1" / "prune" / "prune.py"


# ============================================================
# Test Backward Compatibility
# ============================================================


class TestBackwardCompatibility:
    """Tests for backward compatibility of prune API."""

    def test_prune_data_still_exists(self):
        """Verify prune_data() method still exists."""
        prune_file = self._get_prune_file()
        content = prune_file.read_text()

        assert "async def prune_data(" in content, "prune_data() should still exist"

    def test_prune_system_still_exists(self):
        """Verify prune_system() method still exists."""
        prune_file = self._get_prune_file()
        content = prune_file.read_text()

        assert "async def prune_system(" in content, "prune_system() should still exist"

    def test_prune_system_signature_unchanged(self):
        """Verify prune_system() signature is unchanged."""
        prune_file = self._get_prune_file()
        content = prune_file.read_text()

        # Check signature components
        assert "graph: bool = True" in content, "graph parameter should have default True"
        assert "vector: bool = True" in content, "vector parameter should have default True"
        assert "metadata: bool = False" in content, "metadata parameter should have default False"
        assert "cache: bool = True" in content, "cache parameter should have default True"

    def _get_prune_file(self) -> pathlib.Path:
        """Get path to prune.py file."""
        current = pathlib.Path(__file__)
        mflow_root = current.parent.parent.parent.parent
        return mflow_root / "api" / "v1" / "prune" / "prune.py"


# ============================================================
# Test Syntax
# ============================================================


class TestPruneSyntax:
    """Test prune.py has valid Python syntax."""

    def test_valid_python_syntax(self):
        """Verify prune.py is valid Python."""
        prune_file = self._get_prune_file()
        content = prune_file.read_text()

        try:
            ast.parse(content)
        except SyntaxError as e:
            pytest.fail(f"prune.py has syntax error: {e}")

    def _get_prune_file(self) -> pathlib.Path:
        """Get path to prune.py file."""
        current = pathlib.Path(__file__)
        mflow_root = current.parent.parent.parent.parent
        return mflow_root / "api" / "v1" / "prune" / "prune.py"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
