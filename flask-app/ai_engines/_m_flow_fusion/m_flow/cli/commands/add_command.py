"""
CLI 'add' command for M-flow data ingestion.

Handles adding various data types to M-flow datasets
for subsequent knowledge graph processing.
"""

from __future__ import annotations

import argparse
import asyncio
from typing import List, Union

import m_flow.cli.echo as output
from m_flow.cli import DEFAULT_DOCS_URL
from m_flow.cli.exceptions import CliCommandException, CliCommandInnerException
from m_flow.cli.reference import SupportsCliCommand


_DESCRIPTION = """\
Ingest data into M-flow for knowledge graph construction.

This command is the entry point for the M-flow pipeline. It accepts
multiple input formats and stores them for processing.

Input Formats:
  - Plain text strings
  - Local file paths (absolute: /path/to/file)
  - File URLs (file:///absolute/path or file://relative/path)
  - S3 URIs (s3://bucket-name/key/path)
  - Multiple items as a list

File Types:
  - Documents: .txt, .md, .csv, .pdf, .docx, .pptx
  - Images: .png, .jpg, .jpeg (OCR extraction)
  - Audio: .mp3, .wav (transcription)
  - Code: .py, .js, .ts (structure parsing)

After adding data, run `mflow memorize` to build the knowledge graph.
"""


class AddCommand(SupportsCliCommand):
    """Command handler for data ingestion."""

    command_string = "add"
    help_string = "Ingest data into M-flow for processing"
    docs_url = DEFAULT_DOCS_URL
    description = _DESCRIPTION

    def configure_parser(self, parser: argparse.ArgumentParser) -> None:
        """Register command arguments."""
        parser.add_argument(
            "data",
            nargs="+",
            help="Data items: text, file paths, URLs, or S3 URIs",
        )
        parser.add_argument(
            "--dataset-name",
            "-d",
            default="main_dataset",
            help="Target dataset name (default: main_dataset)",
        )

    def _prepare_input(self, items: List[str]) -> Union[str, List[str]]:
        """Normalize input data for the add API."""
        return items[0] if len(items) == 1 else items

    async def _execute_add(self, data: Union[str, List[str]], dataset: str) -> None:
        """Async wrapper for the add operation."""
        import m_flow

        output.echo("Processing input data...")
        await m_flow.add(data=data, dataset_name=dataset)
        output.success(f"Data added to dataset '{dataset}'")

    def execute(self, args: argparse.Namespace) -> None:
        """Execute the add command."""
        try:
            item_count = len(args.data)
            dataset = args.dataset_name

            output.echo(f"Adding {item_count} item(s) to '{dataset}'...")

            data = self._prepare_input(args.data)
            asyncio.run(self._execute_add(data, dataset))

        except CliCommandInnerException as err:
            raise CliCommandException(str(err), error_code=1) from err
        except Exception as err:
            msg = f"Add operation failed: {err}"
            raise CliCommandException(msg, error_code=1) from err
