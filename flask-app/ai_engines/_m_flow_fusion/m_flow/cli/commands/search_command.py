"""
CLI 'search' command for M-flow knowledge retrieval.

Provides various search modes for querying the knowledge graph
including natural language Q&A and graph traversal.
"""

from __future__ import annotations

import argparse
import asyncio
import json
from typing import Any, List, Optional

import m_flow.cli.echo as output
from m_flow.cli import DEFAULT_DOCS_URL
from m_flow.cli.config import OUTPUT_FORMAT_CHOICES, RECALL_MODE_CHOICES
from m_flow.cli.exceptions import CliCommandException, CliCommandInnerException
from m_flow.cli.reference import SupportsCliCommand


_DESCRIPTION = """\
Query the M-flow knowledge graph for insights and information.

Available search modes:

TRIPLET_COMPLETION (default):
    Natural language Q&A with LLM reasoning over graph context.
    Ideal for complex questions, summaries, and analysis.

EPISODIC:
    Event-based memory retrieval using episode/facet/concept structure.
    Best for contextual recall and temporal queries.

PROCEDURAL:
    Step-by-step instruction retrieval.
    Suited for how-to questions and process documentation.

CYPHER:
    Direct graph database queries using Cypher syntax.
    For advanced users and specific graph traversals.

CHUNKS_LEXICAL:
    Token-based lexical matching with stopword awareness.
    Good for exact term lookups.
"""


def _format_pretty_output(results: List[Any], mode: str) -> None:
    """Display results in human-readable format."""
    if not results:
        output.warning("No matching results found.")
        return

    output.echo(f"\nRetrieved {len(results)} result(s) via {mode}:")
    output.echo("=" * 60)

    for idx, item in enumerate(results, start=1):
        if mode == "TRIPLET_COMPLETION":
            output.echo(f"{output.bold('Response:')} {item}")
        else:
            output.echo(f"{output.bold(f'[{idx}]')} {item}")

        if idx < len(results):
            output.echo("-" * 40)

    output.echo()


class SearchCommand(SupportsCliCommand):
    """Handler for knowledge graph search operations."""

    command_string = "search"
    help_string = "Query the knowledge graph for information"
    docs_url = DEFAULT_DOCS_URL
    description = _DESCRIPTION

    def configure_parser(self, parser: argparse.ArgumentParser) -> None:
        """Define search command arguments."""
        parser.add_argument(
            "query_text",
            help="Natural language query or search terms",
        )
        parser.add_argument(
            "--query-type",
            "-t",
            choices=RECALL_MODE_CHOICES,
            default="TRIPLET_COMPLETION",
            help="Retrieval mode (default: TRIPLET_COMPLETION)",
        )
        parser.add_argument(
            "--datasets",
            "-d",
            nargs="*",
            help="Filter to specific dataset(s)",
        )
        parser.add_argument(
            "--top-k",
            "-k",
            type=int,
            default=10,
            help="Maximum results (default: 10)",
        )
        parser.add_argument(
            "--system-prompt",
            help="Custom prompt file for LLM modes",
        )
        parser.add_argument(
            "--output-format",
            "-f",
            choices=OUTPUT_FORMAT_CHOICES,
            default="pretty",
            help="Output style (default: pretty)",
        )

    async def _run_search(
        self,
        query: str,
        mode: str,
        datasets: Optional[List[str]],
        prompt_path: str,
        limit: int,
    ) -> List[Any]:
        """Execute the async search operation."""
        import m_flow
        from m_flow.search.types import RecallMode

        recall_mode = RecallMode[mode]

        return await m_flow.search(
            query_text=query,
            query_type=recall_mode,
            datasets=datasets,
            system_prompt_path=prompt_path,
            top_k=limit,
        )

    def _display_results(
        self,
        results: List[Any],
        fmt: str,
        mode: str,
    ) -> None:
        """Output results in the requested format."""
        if fmt == "json":
            output.echo(json.dumps(results, indent=2, default=str))
        elif fmt == "simple":
            for idx, item in enumerate(results, 1):
                output.echo(f"{idx}. {item}")
        else:
            _format_pretty_output(results, mode)

    def execute(self, args: argparse.Namespace) -> None:
        """Run the search command."""
        try:
            scope = f" in {args.datasets}" if args.datasets else ""
            output.echo(f"Searching: '{args.query_text}' [{args.query_type}]{scope}")

            prompt = args.system_prompt or "direct_answer.txt"

            results = asyncio.run(
                self._run_search(
                    args.query_text,
                    args.query_type,
                    args.datasets,
                    prompt,
                    args.top_k,
                )
            )

            self._display_results(results, args.output_format, args.query_type)

        except CliCommandInnerException as err:
            raise CliCommandException(str(err), error_code=1) from err
        except Exception as err:
            raise CliCommandException(f"Search failed: {err}", error_code=1) from err
