"""
CLI Integration Tests for M-flow.

End-to-end tests verifying command-line interface functionality,
argument parsing, error handling, and subcommand behavior.
"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import patch

if TYPE_CHECKING:
    from subprocess import CompletedProcess

# ============================================================================
# Constants
# ============================================================================

CLI_MODULE = "m_flow.cli.app"
PROJECT_ROOT = Path(__file__).parent.parent.parent


def run_cli(*args: str) -> CompletedProcess:
    """Execute CLI command and return result."""
    cmd = [sys.executable, "-m", CLI_MODULE, *args]
    return subprocess.run(cmd, capture_output=True, text=True, cwd=PROJECT_ROOT)


def stderr_contains(result: CompletedProcess, *terms: str) -> bool:
    """Check if stderr contains any of the given terms."""
    lower_stderr = result.stderr.lower()
    return any(term in lower_stderr for term in terms)


def stdout_contains(result: CompletedProcess, *terms: str) -> bool:
    """Check if stdout contains any of the given terms."""
    lower_stdout = result.stdout.lower()
    return any(term in lower_stdout for term in terms)


# ============================================================================
# Core CLI Tests
# ============================================================================


class TestCoreCliCommands:
    """Tests for fundamental CLI operations."""

    def test_help_displays_correctly(self) -> None:
        """Verify --help shows usage information."""
        result = run_cli("--help")

        assert result.returncode == 0, f"Help command failed: {result.stderr}"
        assert stdout_contains(result, "m_flow"), "Expected 'm_flow' in help output"
        assert stdout_contains(result, "commands"), "Missing commands section"

    def test_version_info_shown(self) -> None:
        """Verify --version displays version string."""
        result = run_cli("--version")

        assert result.returncode == 0, f"Version command failed: {result.stderr}"
        assert stdout_contains(result, "m_flow"), "Expected 'm_flow' in version output"

    def test_unknown_command_rejected(self) -> None:
        """Verify unknown commands return error."""
        result = run_cli("nonexistent_cmd_xyz")
        assert result.returncode != 0, "Unknown command should fail"

    def test_subcommand_help_available(self) -> None:
        """Verify each subcommand has help available."""
        subcommands = ["add", "search", "memorize", "delete", "config"]

        for cmd in subcommands:
            result = run_cli(cmd, "--help")
            assert result.returncode == 0, f"Help for '{cmd}' failed: {result.stderr}"
            assert cmd in result.stdout.lower(), f"'{cmd}' not mentioned in its help"


# ============================================================================
# Add Command Tests
# ============================================================================


class TestAddCommand:
    """Tests for the 'add' subcommand."""

    def test_add_file_argument_parsing(self) -> None:
        """Verify add command accepts file path argument."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as temp_file:
            temp_file.write("Sample content for CLI test")
            temp_path = temp_file.name

        try:
            result = run_cli("add", temp_path)

            lower_out = result.stdout.lower() + result.stderr.lower()
            arg_parse_ok = (
                "unrecognized arguments" not in lower_out and "invalid" not in lower_out and "usage:" not in lower_out
            )
            execution_started = any(x in lower_out for x in ["adding", "processing", "pipeline"])

            assert arg_parse_ok or execution_started
        finally:
            os.unlink(temp_path)

    def test_add_multiple_files_with_dataset(self) -> None:
        """Verify adding multiple files with dataset name."""
        with tempfile.TemporaryDirectory() as temp_dir:
            paths = []
            for i in range(2):
                p = os.path.join(temp_dir, f"doc_{i}.txt")
                with open(p, "w") as f:
                    f.write(f"Document content {i}")
                paths.append(p)

            result = run_cli("add", *paths, "--dataset-name", "multi_file_test")

            # Verify argument parsing succeeded
            assert not stderr_contains(result, "unrecognized", "argument error")


# ============================================================================
# Search Command Tests
# ============================================================================


class TestSearchCommand:
    """Tests for the 'search' subcommand."""

    def test_search_requires_query(self) -> None:
        """Verify search fails without query argument."""
        result = run_cli("search")

        assert result.returncode != 0
        assert stderr_contains(result, "required", "error")

    def test_search_with_options(self) -> None:
        """Verify search accepts all option flags."""
        result = run_cli(
            "search",
            "test query text",
            "--query-type",
            "EPISODIC",
            "--datasets",
            "ds1",
            "ds2",
            "--top-k",
            "10",
            "--output-format",
            "json",
        )

        # Should parse arguments without errors
        assert not stderr_contains(result, "unrecognized arguments", "invalid choice")


# ============================================================================
# Memorize Command Tests
# ============================================================================


class TestMemorizeCommand:
    """Tests for the 'memorize' subcommand."""

    def test_memorize_accepts_options(self) -> None:
        """Verify memorize accepts all available options."""
        result = run_cli(
            "memorize",
            "--datasets",
            "ds1",
            "ds2",
            "--chunk-size",
            "512",
            "--chunker",
            "TextChunker",
            "--background",
            "--verbose",
        )

        assert not stderr_contains(result, "unrecognized arguments", "invalid choice")


# ============================================================================
# Delete Command Tests
# ============================================================================


class TestDeleteCommand:
    """Tests for the 'delete' subcommand."""

    def test_delete_without_target_shows_message(self) -> None:
        """Verify delete with no target shows guidance message."""
        result = run_cli("delete")

        output_combined = result.stdout.lower() + result.stderr.lower()
        assert "specify a target" in output_combined or "error" in output_combined

    def test_delete_with_force_flag(self) -> None:
        """Verify delete accepts force flag."""
        result = run_cli("delete", "--dataset-name", "test_ds", "--force")

        assert not stderr_contains(result, "unrecognized arguments")


# ============================================================================
# Config Subcommand Tests
# ============================================================================


class TestConfigSubcommands:
    """Tests for 'config' subcommand operations."""

    def test_config_subcommand_help_available(self) -> None:
        """Verify each config subcommand has help."""
        subcommands = ["get", "set", "list", "unset", "reset"]

        for subcmd in subcommands:
            result = run_cli("config", subcmd, "--help")
            assert result.returncode == 0, f"config {subcmd} help failed"

    def test_config_set_parsing(self) -> None:
        """Verify config set accepts key-value arguments."""
        result = run_cli("config", "set", "some_key", "some_value")

        # Argument parsing should succeed
        parsing_ok = not stderr_contains(result, "unrecognized arguments", "required")
        exec_fail_ok = stderr_contains(result, "failed to set")

        assert parsing_ok or exec_fail_ok


# ============================================================================
# Error Handling Tests
# ============================================================================


class TestCliErrorHandling:
    """Tests for CLI error handling and validation."""

    def test_debug_flag_accepted(self) -> None:
        """Verify --debug flag is accepted globally."""
        result = run_cli("--debug", "search", "query text")
        assert not stderr_contains(result, "unrecognized arguments")

    def test_invalid_query_type_rejected(self) -> None:
        """Verify invalid query type is rejected."""
        result = run_cli("search", "query", "--query-type", "INVALID_TYPE_XYZ")

        assert result.returncode != 0
        assert stderr_contains(result, "invalid choice")

    def test_invalid_chunker_rejected(self) -> None:
        """Verify invalid chunker name is rejected."""
        result = run_cli("memorize", "--chunker", "InvalidChunkerName")

        assert result.returncode != 0
        assert stderr_contains(result, "invalid choice")

    def test_invalid_output_format_rejected(self) -> None:
        """Verify invalid output format is rejected."""
        result = run_cli("search", "query", "--output-format", "unsupported_format")

        assert result.returncode != 0
        assert stderr_contains(result, "invalid choice")
