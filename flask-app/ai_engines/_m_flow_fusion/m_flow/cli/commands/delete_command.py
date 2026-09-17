"""
CLI 'delete' command for M-flow data removal.

Handles deletion of datasets, user data, or complete
knowledge base cleanup.
"""

from __future__ import annotations

import argparse
import asyncio
from typing import Optional

import m_flow.cli.echo as output
from m_flow.cli import DEFAULT_DOCS_URL
from m_flow.cli.exceptions import CliCommandException, CliCommandInnerException
from m_flow.cli.reference import SupportsCliCommand
from m_flow.data.methods.get_deletion_counts import get_deletion_counts


_DESCRIPTION = """\
Remove data from M-flow knowledge base.

Targets:
  --dataset-name, -d   Remove a specific dataset
  --user-id, -u        Remove all data for a user
  --all                Purge entire knowledge base

Deletion is permanent. Use --force to skip confirmation.
"""


class DeleteCommand(SupportsCliCommand):
    """Handler for data deletion operations."""

    command_string = "delete"
    help_string = "Remove data from M-flow"
    docs_url = DEFAULT_DOCS_URL
    description = _DESCRIPTION

    def configure_parser(self, parser: argparse.ArgumentParser) -> None:
        """Define deletion arguments."""
        parser.add_argument("--dataset-name", "-d", help="Dataset to remove")
        parser.add_argument("--user-id", "-u", help="User whose data to remove")
        parser.add_argument("--all", action="store_true", help="Remove everything")
        parser.add_argument("--force", "-f", action="store_true", help="Skip prompts")

    def _validate_target(self, args: argparse.Namespace) -> bool:
        """Ensure at least one deletion target is specified."""
        if not any([args.dataset_name, args.user_id, args.all]):
            output.error("Specify a target: --dataset-name, --user-id, or --all")
            return False
        return True

    async def _fetch_preview(
        self,
        dataset: Optional[str],
        user: Optional[str],
        purge_all: bool,
    ):
        """Retrieve counts of items to be deleted."""
        return await get_deletion_counts(
            dataset_name=dataset,
            user_id=user,
            all_data=purge_all,
        )

    def _show_preview(self, preview) -> None:
        """Display deletion preview information."""
        output.echo("Items to be removed:")
        output.echo(f"  Datasets: {preview.datasets}")
        output.echo(f"  Entries: {preview.data_entries}")
        output.echo(f"  Users: {preview.users}")
        output.echo("-" * 30)

    def _build_description(self, args: argparse.Namespace) -> tuple[str, str]:
        """Generate confirmation message and operation label."""
        if args.all:
            return "Purge ALL M-flow data?", "complete knowledge base"
        if args.dataset_name:
            return f"Remove dataset '{args.dataset_name}'?", f"dataset '{args.dataset_name}'"
        if args.user_id:
            return f"Remove data for user '{args.user_id}'?", f"user '{args.user_id}' data"
        return "Remove data?", "selected data"

    async def _execute_removal(
        self,
        dataset: Optional[str],
        user: Optional[str],
        purge_all: bool,
    ) -> None:
        """Perform the async deletion."""
        import m_flow

        target_dataset = None if purge_all else dataset
        await m_flow.remove(dataset_name=target_dataset, user_id=user)

    def execute(self, args: argparse.Namespace) -> None:
        """Execute the delete command."""
        try:
            import m_flow  # noqa: F401

            if not self._validate_target(args):
                return

            # Preview (unless forced)
            if not args.force:
                output.echo("Analyzing deletion scope...")
                try:
                    preview = asyncio.run(self._fetch_preview(args.dataset_name, args.user_id, args.all))
                except Exception as err:
                    output.error(f"Preview failed: {err}")
                    return

                if not preview:
                    output.success("Nothing to remove")
                    return

                self._show_preview(preview)

            confirm_msg, label = self._build_description(args)

            if not args.force:
                output.warning("This operation cannot be undone!")
                if not output.confirm(confirm_msg):
                    output.echo("Cancelled")
                    return

            output.echo(f"Removing {label}...")
            asyncio.run(self._execute_removal(args.dataset_name, args.user_id, args.all))
            output.success(f"Deleted {label}")

        except CliCommandInnerException as err:
            raise CliCommandException(str(err), error_code=1) from err
        except Exception as err:
            raise CliCommandException(f"Deletion failed: {err}", error_code=1) from err
