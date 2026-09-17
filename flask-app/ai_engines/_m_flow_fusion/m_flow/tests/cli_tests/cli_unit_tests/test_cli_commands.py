"""
CLI Command Unit Tests for M-flow.

Unit tests for individual CLI command classes with proper mocking
and async coroutine handling.
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from typing import TYPE_CHECKING, Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from m_flow.cli.commands.add_command import AddCommand
from m_flow.cli.commands.config_command import ConfigCommand
from m_flow.cli.commands.delete_command import DeleteCommand
from m_flow.cli.commands.memorize_command import MemorizeCommand
from m_flow.cli.commands.search_command import SearchCommand
from m_flow.cli.exceptions import CliCommandException
from m_flow.data.methods.get_deletion_counts import DeletionCountsPreview

if TYPE_CHECKING:
    pass


# ============================================================================
# Test Utilities
# ============================================================================


def run_coro_sync(coro: Any) -> Any:
    """Execute a coroutine synchronously for testing."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


def make_namespace(**kwargs: Any) -> argparse.Namespace:
    """Create an argparse.Namespace with given attributes."""
    return argparse.Namespace(**kwargs)


def get_parser_actions(parser: argparse.ArgumentParser) -> dict[str, Any]:
    """Extract parser actions as a dict keyed by dest."""
    return {action.dest: action for action in parser._actions}


# ============================================================================
# AddCommand Tests
# ============================================================================


class TestAddCommandUnit:
    """Unit tests for AddCommand."""

    def test_command_metadata(self) -> None:
        """Verify command string, help, and docs URL."""
        cmd = AddCommand()
        assert cmd.command_string == "add"
        assert "Ingest data into M-flow" in cmd.help_string
        assert cmd.docs_url is not None

    def test_parser_configuration(self) -> None:
        """Verify parser accepts required arguments."""
        cmd = AddCommand()
        parser = argparse.ArgumentParser()
        cmd.configure_parser(parser)

        actions = get_parser_actions(parser)
        assert "data" in actions
        assert "dataset_name" in actions
        assert actions["data"].nargs == "+"

    @patch("m_flow.cli.commands.add_command.asyncio.run", side_effect=run_coro_sync)
    def test_execute_single_file(self, mock_run: MagicMock) -> None:
        """Test adding single data item."""
        mock_mflow = MagicMock()
        mock_mflow.add = AsyncMock()

        with patch.dict(sys.modules, {"m_flow": mock_mflow}):
            cmd = AddCommand()
            args = make_namespace(data=["doc.txt"], dataset_name="ds1")
            cmd.execute(args)

        mock_run.assert_called_once()
        mock_mflow.add.assert_awaited_once_with(data="doc.txt", dataset_name="ds1")

    @patch("m_flow.cli.commands.add_command.asyncio.run", side_effect=run_coro_sync)
    def test_execute_multiple_files(self, mock_run: MagicMock) -> None:
        """Test adding multiple data items."""
        mock_mflow = MagicMock()
        mock_mflow.add = AsyncMock()

        with patch.dict(sys.modules, {"m_flow": mock_mflow}):
            cmd = AddCommand()
            args = make_namespace(data=["a.txt", "b.txt"], dataset_name="ds1")
            cmd.execute(args)

        mock_mflow.add.assert_awaited_once_with(data=["a.txt", "b.txt"], dataset_name="ds1")

    @patch("m_flow.cli.commands.add_command.asyncio.run")
    def test_execute_exception_wrapped(self, mock_run: MagicMock) -> None:
        """Test exception is wrapped in CliCommandException."""
        mock_run.side_effect = Exception("add failed")

        with pytest.raises(CliCommandException):
            AddCommand().execute(make_namespace(data=["x.txt"], dataset_name="ds"))


# ============================================================================
# SearchCommand Tests
# ============================================================================


class TestSearchCommandUnit:
    """Unit tests for SearchCommand."""

    def test_command_metadata(self) -> None:
        """Verify command string, help, and docs URL."""
        cmd = SearchCommand()
        assert cmd.command_string == "search"
        assert "Query the knowledge graph" in cmd.help_string
        assert cmd.docs_url is not None

    def test_parser_configuration(self) -> None:
        """Verify parser accepts all search arguments."""
        cmd = SearchCommand()
        parser = argparse.ArgumentParser()
        cmd.configure_parser(parser)

        actions = get_parser_actions(parser)
        assert "query_text" in actions
        assert "query_type" in actions
        assert "datasets" in actions
        assert "top_k" in actions
        assert actions["query_type"].default == "TRIPLET_COMPLETION"
        assert actions["top_k"].default == 10

    @patch("m_flow.cli.commands.search_command.asyncio.run", side_effect=run_coro_sync)
    def test_execute_basic_search(self, mock_run: MagicMock) -> None:
        """Test basic search execution."""
        mock_mflow = MagicMock()
        mock_mflow.search = AsyncMock(return_value=["r1", "r2"])

        with patch.dict(sys.modules, {"m_flow": mock_mflow}):
            cmd = SearchCommand()
            args = make_namespace(
                query_text="test",
                query_type="TRIPLET_COMPLETION",
                datasets=None,
                top_k=5,
                system_prompt=None,
                output_format="pretty",
            )
            cmd.execute(args)

        mock_run.assert_called_once()
        mock_mflow.search.assert_awaited_once()

        call_kwargs = mock_mflow.search.await_args.kwargs
        assert call_kwargs["query_text"] == "test"
        assert call_kwargs["top_k"] == 5

    @patch("m_flow.cli.commands.search_command.asyncio.run")
    def test_execute_exception_wrapped(self, mock_run: MagicMock) -> None:
        """Test search exception is wrapped."""
        mock_run.side_effect = Exception("search failed")

        args = make_namespace(
            query_text="q",
            query_type="TRIPLET_COMPLETION",
            datasets=None,
            top_k=10,
            system_prompt=None,
            output_format="pretty",
        )

        with pytest.raises(CliCommandException):
            SearchCommand().execute(args)


# ============================================================================
# MemorizeCommand Tests
# ============================================================================


class TestMemorizeCommandUnit:
    """Unit tests for MemorizeCommand."""

    def test_command_metadata(self) -> None:
        """Verify command string, help, and docs URL."""
        cmd = MemorizeCommand()
        assert cmd.command_string == "memorize"
        assert "Transform ingested data" in cmd.help_string

    def test_parser_configuration(self) -> None:
        """Verify parser accepts memorize arguments."""
        cmd = MemorizeCommand()
        parser = argparse.ArgumentParser()
        cmd.configure_parser(parser)

        actions = get_parser_actions(parser)
        assert "datasets" in actions
        assert "chunk_size" in actions
        assert "chunker" in actions
        assert actions["chunker"].default == "TextChunker"

    @patch("m_flow.cli.commands.memorize_command.asyncio.run", side_effect=run_coro_sync)
    def test_execute_basic_memorize(self, mock_run: MagicMock) -> None:
        """Test basic memorize execution."""
        mock_mflow = MagicMock()
        mock_mflow.memorize = AsyncMock(return_value="ok")

        with patch.dict(sys.modules, {"m_flow": mock_mflow}):
            cmd = MemorizeCommand()
            args = make_namespace(
                datasets=None,
                chunk_size=None,
                chunker="TextChunker",
                background=False,
                verbose=False,
                content_type="text",
            )
            cmd.execute(args)

        mock_run.assert_called_once()
        mock_mflow.memorize.assert_awaited_once()

    @patch("m_flow.cli.commands.memorize_command.asyncio.run")
    def test_execute_exception_wrapped(self, mock_run: MagicMock) -> None:
        """Test memorize exception is wrapped."""
        mock_run.side_effect = Exception("memorize failed")

        args = make_namespace(
            datasets=None,
            chunk_size=None,
            chunker="TextChunker",
            background=False,
            verbose=False,
            content_type="text",
        )

        with pytest.raises(CliCommandException):
            MemorizeCommand().execute(args)


# ============================================================================
# DeleteCommand Tests
# ============================================================================


class TestDeleteCommandUnit:
    """Unit tests for DeleteCommand."""

    def test_command_metadata(self) -> None:
        """Verify command string, help, and docs URL."""
        cmd = DeleteCommand()
        assert cmd.command_string == "delete"
        assert "Remove data from M-flow" in cmd.help_string

    def test_parser_configuration(self) -> None:
        """Verify parser accepts delete arguments."""
        cmd = DeleteCommand()
        parser = argparse.ArgumentParser()
        cmd.configure_parser(parser)

        actions = get_parser_actions(parser)
        assert "dataset_name" in actions
        assert "user_id" in actions
        assert "force" in actions

    @patch("m_flow.cli.commands.delete_command.get_deletion_counts")
    @patch("m_flow.cli.commands.delete_command.output.confirm")
    @patch("m_flow.cli.commands.delete_command.asyncio.run", side_effect=run_coro_sync)
    def test_execute_with_confirmation(
        self,
        mock_run: MagicMock,
        mock_confirm: MagicMock,
        mock_counts: MagicMock,
    ) -> None:
        """Test delete with user confirmation."""
        mock_mflow = MagicMock()
        mock_mflow.remove = AsyncMock()
        mock_counts.return_value = DeletionCountsPreview()
        mock_confirm.return_value = True

        with patch.dict(sys.modules, {"m_flow": mock_mflow}):
            cmd = DeleteCommand()
            args = make_namespace(
                dataset_name="ds1",
                user_id=None,
                all=False,
                force=False,
            )
            cmd.execute(args)

        mock_confirm.assert_called_once()

    @patch("m_flow.cli.commands.delete_command.asyncio.run", side_effect=run_coro_sync)
    def test_execute_forced_delete(self, mock_run: MagicMock) -> None:
        """Test delete with force flag bypasses confirmation."""
        mock_mflow = MagicMock()
        mock_mflow.remove = AsyncMock()

        with patch.dict(sys.modules, {"m_flow": mock_mflow}):
            cmd = DeleteCommand()
            args = make_namespace(
                dataset_name="ds1",
                user_id=None,
                all=False,
                force=True,
            )
            cmd.execute(args)

        mock_mflow.remove.assert_awaited_once()

    def test_execute_no_target(self) -> None:
        """Test delete with no target shows error."""
        cmd = DeleteCommand()
        args = make_namespace(dataset_name=None, user_id=None, all=False, force=False)
        # Should not raise, just show error
        cmd.execute(args)


# ============================================================================
# ConfigCommand Tests
# ============================================================================


class TestConfigCommandUnit:
    """Unit tests for ConfigCommand."""

    def test_command_metadata(self) -> None:
        """Verify command string, help, and docs URL."""
        cmd = ConfigCommand()
        assert cmd.command_string == "config"
        assert "Manage M-flow configuration" in cmd.help_string

    def test_parser_has_subcommands(self) -> None:
        """Verify config has get/set/list/unset/reset subcommands."""
        cmd = ConfigCommand()
        parser = argparse.ArgumentParser()
        cmd.configure_parser(parser)

        subparsers = [a for a in parser._actions if isinstance(a, argparse._SubParsersAction)]
        assert len(subparsers) == 1

        choices = subparsers[0].choices
        for sub in ["get", "set", "list", "unset", "reset"]:
            assert sub in choices

    def test_execute_no_action(self) -> None:
        """Test config with no action shows help."""
        cmd = ConfigCommand()
        # Should not raise
        cmd.execute(argparse.Namespace())

    def test_execute_list_action(self) -> None:
        """Test config list action."""
        cmd = ConfigCommand()
        cmd.execute(make_namespace(config_action="list"))

    def test_execute_invalid_action(self) -> None:
        """Test config with invalid action handled gracefully."""
        cmd = ConfigCommand()
        cmd.execute(make_namespace(config_action="invalid_xyz"))
