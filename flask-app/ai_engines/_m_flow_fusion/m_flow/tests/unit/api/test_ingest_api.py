# m_flow/tests/unit/api/test_ingest_api.py
"""
Unit tests for ingest API (P2).

Tests cover:
1. ingest() function
2. IngestResult dataclass
3. IngestStatus enum
4. Parameter handling
"""

import ast
import pathlib
import pytest


# ============================================================
# Test IngestStatus Enum
# ============================================================


class TestIngestStatus:
    """Tests for IngestStatus enum."""

    def test_ingest_status_exists(self):
        """Verify IngestStatus enum exists."""
        ingest_file = self._get_ingest_file()
        content = ingest_file.read_text()

        assert "class IngestStatus" in content

    def test_ingest_status_has_completed(self):
        """Verify COMPLETED status exists."""
        ingest_file = self._get_ingest_file()
        content = ingest_file.read_text()

        assert "COMPLETED" in content

    def test_ingest_status_has_background_started(self):
        """Verify BACKGROUND_STARTED status exists."""
        ingest_file = self._get_ingest_file()
        content = ingest_file.read_text()

        assert "BACKGROUND_STARTED" in content

    def test_ingest_status_has_memorize_skipped(self):
        """Verify MEMORIZE_SKIPPED status exists."""
        ingest_file = self._get_ingest_file()
        content = ingest_file.read_text()

        assert "MEMORIZE_SKIPPED" in content

    def test_ingest_status_has_memorize_failed(self):
        """Verify MEMORIZE_FAILED status exists."""
        ingest_file = self._get_ingest_file()
        content = ingest_file.read_text()

        assert "MEMORIZE_FAILED" in content

    def _get_ingest_file(self) -> pathlib.Path:
        """Get path to ingest.py file."""
        current = pathlib.Path(__file__)
        mflow_root = current.parent.parent.parent.parent
        return mflow_root / "api" / "v1" / "ingest" / "ingest.py"


# ============================================================
# Test IngestResult Dataclass
# ============================================================


class TestIngestResult:
    """Tests for IngestResult dataclass."""

    def test_ingest_result_exists(self):
        """Verify IngestResult class exists."""
        ingest_file = self._get_ingest_file()
        content = ingest_file.read_text()

        assert "class IngestResult" in content

    def test_ingest_result_has_add_run_id(self):
        """Verify add_run_id field exists."""
        ingest_file = self._get_ingest_file()
        content = ingest_file.read_text()

        assert "add_run_id:" in content

    def test_ingest_result_has_memorize_run_id(self):
        """Verify memorize_run_id field exists."""
        ingest_file = self._get_ingest_file()
        content = ingest_file.read_text()

        assert "memorize_run_id:" in content

    def test_ingest_result_has_dataset_id(self):
        """Verify dataset_id field exists."""
        ingest_file = self._get_ingest_file()
        content = ingest_file.read_text()

        assert "dataset_id:" in content

    def test_ingest_result_has_status(self):
        """Verify status field exists."""
        ingest_file = self._get_ingest_file()
        content = ingest_file.read_text()

        assert "status: IngestStatus" in content

    def test_ingest_result_has_is_completed(self):
        """Verify is_completed property exists."""
        ingest_file = self._get_ingest_file()
        content = ingest_file.read_text()

        assert "def is_completed(" in content

    def test_ingest_result_has_is_background(self):
        """Verify is_background property exists."""
        ingest_file = self._get_ingest_file()
        content = ingest_file.read_text()

        assert "def is_background(" in content

    def _get_ingest_file(self) -> pathlib.Path:
        """Get path to ingest.py file."""
        current = pathlib.Path(__file__)
        mflow_root = current.parent.parent.parent.parent
        return mflow_root / "api" / "v1" / "ingest" / "ingest.py"


# ============================================================
# Test ingest() Function
# ============================================================


class TestIngestFunction:
    """Tests for ingest() function."""

    def test_ingest_function_exists(self):
        """Verify ingest() function exists."""
        ingest_file = self._get_ingest_file()
        content = ingest_file.read_text()

        assert "async def ingest(" in content

    def test_ingest_has_data_param(self):
        """Verify data parameter exists."""
        ingest_file = self._get_ingest_file()
        content = ingest_file.read_text()

        assert "data:" in content

    def test_ingest_has_dataset_name_param(self):
        """Verify dataset_name parameter exists."""
        ingest_file = self._get_ingest_file()
        content = ingest_file.read_text()

        assert "dataset_name:" in content

    def test_ingest_has_skip_memorize_param(self):
        """Verify skip_memorize parameter exists."""
        ingest_file = self._get_ingest_file()
        content = ingest_file.read_text()

        assert "skip_memorize" in content

    def test_ingest_has_run_in_background_param(self):
        """Verify run_in_background parameter exists."""
        ingest_file = self._get_ingest_file()
        content = ingest_file.read_text()

        assert "run_in_background" in content

    def test_ingest_returns_ingest_result(self):
        """Verify ingest returns IngestResult."""
        ingest_file = self._get_ingest_file()
        content = ingest_file.read_text()

        assert "-> IngestResult" in content

    def _get_ingest_file(self) -> pathlib.Path:
        """Get path to ingest.py file."""
        current = pathlib.Path(__file__)
        mflow_root = current.parent.parent.parent.parent
        return mflow_root / "api" / "v1" / "ingest" / "ingest.py"


# ============================================================
# Test Exports
# ============================================================


class TestIngestExports:
    """Tests for ingest module exports."""

    def test_ingest_exported(self):
        """Verify ingest is exported."""
        init_file = self._get_init_file()
        content = init_file.read_text()

        assert "ingest" in content

    def test_ingest_result_exported(self):
        """Verify IngestResult is exported."""
        init_file = self._get_init_file()
        content = init_file.read_text()

        assert "IngestResult" in content

    def test_ingest_status_exported(self):
        """Verify IngestStatus is exported."""
        init_file = self._get_init_file()
        content = init_file.read_text()

        assert "IngestStatus" in content

    def _get_init_file(self) -> pathlib.Path:
        """Get path to ingest __init__.py file."""
        current = pathlib.Path(__file__)
        mflow_root = current.parent.parent.parent.parent
        return mflow_root / "api" / "v1" / "ingest" / "__init__.py"


# ============================================================
# Test Syntax
# ============================================================


class TestIngestSyntax:
    """Test ingest.py has valid Python syntax."""

    def test_valid_python_syntax(self):
        """Verify ingest.py is valid Python."""
        ingest_file = self._get_ingest_file()
        content = ingest_file.read_text()

        try:
            ast.parse(content)
        except SyntaxError as e:
            pytest.fail(f"ingest.py has syntax error: {e}")

    def _get_ingest_file(self) -> pathlib.Path:
        """Get path to ingest.py file."""
        current = pathlib.Path(__file__)
        mflow_root = current.parent.parent.parent.parent
        return mflow_root / "api" / "v1" / "ingest" / "ingest.py"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
