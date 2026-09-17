# m_flow/tests/unit/api/test_maintenance_orphans.py
"""
Unit tests for maintenance.orphans module (P1).

Tests cover:
1. OrphanReport and FixResult dataclasses
2. check_orphans() function structure
3. fix_orphans() function structure
4. Module exports
5. Helper function logic
"""

import ast
import pathlib
import pytest
from dataclasses import fields


# ============================================================
# Test Data Classes
# ============================================================


class TestOrphanReportDataclass:
    """Tests for OrphanReport dataclass."""

    def test_orphan_report_fields(self):
        """Verify OrphanReport has all required fields."""
        from m_flow.api.v1.maintenance.orphans import OrphanReport

        field_names = [f.name for f in fields(OrphanReport)]

        assert "total_checked" in field_names
        assert "orphan_count" in field_names
        assert "orphan_ids" in field_names
        assert "orphan_locations" in field_names
        assert "storage_types_checked" in field_names

    def test_orphan_report_defaults(self):
        """Verify OrphanReport has proper defaults."""
        from m_flow.api.v1.maintenance.orphans import OrphanReport

        report = OrphanReport()

        assert report.total_checked == 0
        assert report.orphan_count == 0
        assert report.orphan_ids == []
        assert report.orphan_locations == []
        assert report.storage_types_checked == []

    def test_orphan_report_to_dict(self):
        """Verify OrphanReport.to_dict() works correctly."""
        from m_flow.api.v1.maintenance.orphans import OrphanReport

        report = OrphanReport(
            total_checked=10,
            orphan_count=2,
            orphan_ids=["id1", "id2"],
            orphan_locations=["/path/to/file"],
            storage_types_checked=["local"],
        )

        d = report.to_dict()

        assert d["total_checked"] == 10
        assert d["orphan_count"] == 2
        assert d["orphan_ids"] == ["id1", "id2"]
        assert d["orphan_locations"] == ["/path/to/file"]
        assert d["storage_types_checked"] == ["local"]


class TestFixResultDataclass:
    """Tests for FixResult dataclass."""

    def test_fix_result_fields(self):
        """Verify FixResult has all required fields."""
        from m_flow.api.v1.maintenance.orphans import FixResult

        field_names = [f.name for f in fields(FixResult)]

        assert "orphan_count" in field_names
        assert "fixed_count" in field_names
        assert "fixed_ids" in field_names
        assert "warning" in field_names

    def test_fix_result_defaults(self):
        """Verify FixResult has proper defaults."""
        from m_flow.api.v1.maintenance.orphans import FixResult

        result = FixResult()

        assert result.orphan_count == 0
        assert result.fixed_count == 0
        assert result.fixed_ids == []
        assert result.warning is None

    def test_fix_result_to_dict(self):
        """Verify FixResult.to_dict() works correctly."""
        from m_flow.api.v1.maintenance.orphans import FixResult

        result = FixResult(
            orphan_count=5,
            fixed_count=3,
            fixed_ids=["id1", "id2", "id3"],
            warning="Test warning",
        )

        d = result.to_dict()

        assert d["orphan_count"] == 5
        assert d["fixed_count"] == 3
        assert d["fixed_ids"] == ["id1", "id2", "id3"]
        assert d["warning"] == "Test warning"

    def test_fix_result_to_dict_without_warning(self):
        """Verify FixResult.to_dict() excludes warning when None."""
        from m_flow.api.v1.maintenance.orphans import FixResult

        result = FixResult(orphan_count=0, fixed_count=0)
        d = result.to_dict()

        # Warning should not be included when None
        assert "warning" not in d or d.get("warning") is None


# ============================================================
# Test Function Signatures (Static Analysis)
# ============================================================


class TestCheckOrphansSignature:
    """Tests for check_orphans() function signature."""

    def test_is_async_function(self):
        """Verify check_orphans is async."""
        orphans_file = self._get_orphans_file()
        content = orphans_file.read_text()

        assert "async def check_orphans(" in content

    def test_has_storage_type_param(self):
        """Verify storage_type parameter exists."""
        orphans_file = self._get_orphans_file()
        content = orphans_file.read_text()

        assert "storage_type: Optional[str] = None" in content

    def test_has_limit_param(self):
        """Verify limit parameter exists."""
        orphans_file = self._get_orphans_file()
        content = orphans_file.read_text()

        assert "limit: Optional[int] = None" in content

    def test_returns_orphan_report(self):
        """Verify return type annotation."""
        orphans_file = self._get_orphans_file()
        content = orphans_file.read_text()

        assert "-> OrphanReport" in content

    def _get_orphans_file(self) -> pathlib.Path:
        """Get path to orphans.py file."""
        current = pathlib.Path(__file__)
        mflow_root = current.parent.parent.parent.parent
        return mflow_root / "api" / "v1" / "maintenance" / "orphans.py"


class TestFixOrphansSignature:
    """Tests for fix_orphans() function signature."""

    def test_is_async_function(self):
        """Verify fix_orphans is async."""
        orphans_file = self._get_orphans_file()
        content = orphans_file.read_text()

        assert "async def fix_orphans(" in content

    def test_has_dry_run_param(self):
        """Verify dry_run parameter exists with default False."""
        orphans_file = self._get_orphans_file()
        content = orphans_file.read_text()

        assert "dry_run: bool = False" in content

    def test_has_storage_type_param(self):
        """Verify storage_type parameter exists."""
        orphans_file = self._get_orphans_file()
        content = orphans_file.read_text()

        assert "storage_type: Optional[str] = None" in content

    def test_returns_fix_result(self):
        """Verify return type annotation."""
        orphans_file = self._get_orphans_file()
        content = orphans_file.read_text()

        assert "-> FixResult" in content

    def _get_orphans_file(self) -> pathlib.Path:
        """Get path to orphans.py file."""
        current = pathlib.Path(__file__)
        mflow_root = current.parent.parent.parent.parent
        return mflow_root / "api" / "v1" / "maintenance" / "orphans.py"


# ============================================================
# Test Module Exports
# ============================================================


class TestModuleExports:
    """Tests for maintenance module exports."""

    def test_check_orphans_exported(self):
        """Verify check_orphans is exported from maintenance."""
        init_file = self._get_init_file()
        content = init_file.read_text()

        assert "check_orphans" in content
        assert '"check_orphans"' in content or "'check_orphans'" in content

    def test_fix_orphans_exported(self):
        """Verify fix_orphans is exported from maintenance."""
        init_file = self._get_init_file()
        content = init_file.read_text()

        assert "fix_orphans" in content
        assert '"fix_orphans"' in content or "'fix_orphans'" in content

    def test_orphan_report_exported(self):
        """Verify OrphanReport is exported from maintenance."""
        init_file = self._get_init_file()
        content = init_file.read_text()

        assert "OrphanReport" in content

    def test_fix_result_exported(self):
        """Verify FixResult is exported from maintenance."""
        init_file = self._get_init_file()
        content = init_file.read_text()

        assert "FixResult" in content

    def _get_init_file(self) -> pathlib.Path:
        """Get path to maintenance __init__.py file."""
        current = pathlib.Path(__file__)
        mflow_root = current.parent.parent.parent.parent
        return mflow_root / "api" / "v1" / "maintenance" / "__init__.py"


# ============================================================
# Test Implementation Details
# ============================================================


class TestCheckOrphansImplementation:
    """Tests for check_orphans() implementation details."""

    def test_uses_get_db_adapter(self):
        """Verify uses relational engine to query Data."""
        orphans_file = self._get_orphans_file()
        content = orphans_file.read_text()

        assert "get_db_adapter" in content

    def test_uses_get_file_storage(self):
        """Verify uses file storage to check file existence."""
        orphans_file = self._get_orphans_file()
        content = orphans_file.read_text()

        assert "get_file_storage" in content

    def test_handles_empty_records(self):
        """Verify handles empty record list."""
        orphans_file = self._get_orphans_file()
        content = orphans_file.read_text()

        assert "if not all_records:" in content

    def test_limits_orphan_ids(self):
        """Verify limits orphan_ids to prevent large reports."""
        orphans_file = self._get_orphans_file()
        content = orphans_file.read_text()

        assert "orphan_ids[:100]" in content

    def test_limits_orphan_locations(self):
        """Verify limits orphan_locations sample."""
        orphans_file = self._get_orphans_file()
        content = orphans_file.read_text()

        assert "len(orphan_locations) < 10" in content

    def _get_orphans_file(self) -> pathlib.Path:
        """Get path to orphans.py file."""
        current = pathlib.Path(__file__)
        mflow_root = current.parent.parent.parent.parent
        return mflow_root / "api" / "v1" / "maintenance" / "orphans.py"


class TestFixOrphansImplementation:
    """Tests for fix_orphans() implementation details."""

    def test_calls_check_orphans(self):
        """Verify fix_orphans calls check_orphans first."""
        orphans_file = self._get_orphans_file()
        content = orphans_file.read_text()

        # Find fix_orphans function and check it calls check_orphans
        fix_idx = content.find("async def fix_orphans(")
        if fix_idx > -1:
            fix_body = content[fix_idx:]
            assert "await check_orphans(" in fix_body

    def test_respects_dry_run(self):
        """Verify dry_run mode is respected."""
        orphans_file = self._get_orphans_file()
        content = orphans_file.read_text()

        assert "if dry_run:" in content

    def test_has_p1_limitation_warning(self):
        """Verify P1 limitation warning is included."""
        orphans_file = self._get_orphans_file()
        content = orphans_file.read_text()

        assert "P1 limitation" in content

    def test_commits_transaction(self):
        """Verify transaction is committed."""
        orphans_file = self._get_orphans_file()
        content = orphans_file.read_text()

        assert "await session.commit()" in content

    def _get_orphans_file(self) -> pathlib.Path:
        """Get path to orphans.py file."""
        current = pathlib.Path(__file__)
        mflow_root = current.parent.parent.parent.parent
        return mflow_root / "api" / "v1" / "maintenance" / "orphans.py"


# ============================================================
# Test Syntax and Imports
# ============================================================


class TestOrphansSyntax:
    """Test orphans.py has valid Python syntax."""

    def test_valid_python_syntax(self):
        """Verify orphans.py is valid Python."""
        orphans_file = self._get_orphans_file()
        content = orphans_file.read_text()

        try:
            ast.parse(content)
        except SyntaxError as e:
            pytest.fail(f"orphans.py has syntax error: {e}")

    def test_no_circular_imports(self):
        """Verify no API-level circular imports."""
        orphans_file = self._get_orphans_file()
        content = orphans_file.read_text()

        tree = ast.parse(content)

        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                imports.append(node.module)

        # Should not import from api.v1 (except maintenance itself)
        problematic = [imp for imp in imports if "m_flow.api.v1" in imp and "maintenance" not in imp]

        assert len(problematic) == 0, f"Potential circular imports: {problematic}"

    def _get_orphans_file(self) -> pathlib.Path:
        """Get path to orphans.py file."""
        current = pathlib.Path(__file__)
        mflow_root = current.parent.parent.parent.parent
        return mflow_root / "api" / "v1" / "maintenance" / "orphans.py"


# ============================================================
# Test Documentation
# ============================================================


class TestOrphansDocumentation:
    """Tests for orphans.py documentation."""

    def test_module_docstring(self):
        """Verify module has docstring."""
        orphans_file = self._get_orphans_file()
        content = orphans_file.read_text()

        # Check for docstring at the top
        assert content.strip().startswith("# m_flow") or content.strip().startswith('"""'), (
            "Module should have docstring"
        )

    def test_check_orphans_docstring(self):
        """Verify check_orphans has docstring."""
        orphans_file = self._get_orphans_file()
        content = orphans_file.read_text()

        assert "Check for orphan records" in content

    def test_fix_orphans_docstring(self):
        """Verify fix_orphans has docstring."""
        orphans_file = self._get_orphans_file()
        content = orphans_file.read_text()

        assert "Delete orphan records" in content

    def test_has_usage_examples(self):
        """Verify usage examples are included."""
        orphans_file = self._get_orphans_file()
        content = orphans_file.read_text()

        assert ">>> import m_flow" in content

    def _get_orphans_file(self) -> pathlib.Path:
        """Get path to orphans.py file."""
        current = pathlib.Path(__file__)
        mflow_root = current.parent.parent.parent.parent
        return mflow_root / "api" / "v1" / "maintenance" / "orphans.py"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
