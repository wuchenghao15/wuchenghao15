import argparse
import asyncio

from m_flow.cli.reference import SupportsCliCommand
from m_flow.cli import DEFAULT_DOCS_URL
from m_flow.cli.config import CHUNKER_CHOICES
import m_flow.cli.echo as fmt
from m_flow.cli.exceptions import CliCommandException, CliCommandInnerException
from m_flow.shared.enums.content_type import ContentType


class MemorizeCommand(SupportsCliCommand):
    command_string = "memorize"
    help_string = "Transform ingested data into a structured knowledge graph"
    docs_url = DEFAULT_DOCS_URL
    description = """
Build structured memory layers from ingested data.

Memorize reads raw documents, segments them into semantic fragments,
and writes layered memory structures (Episodes, Facets, Entities)
into the knowledge graph for later retrieval.

Stages:
1. Classify documents by type
2. Chunk text into coherent fragments
3. Route content (sentence-level classification)
4. Summarise and extract structured knowledge
5. Write episodic memory (Episodes + Facets + Entities)
6. Persist to graph and vector stores

After memorize completes, use `mflow search` to query the knowledge graph.
    """

    def configure_parser(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument(
            "--datasets",
            "-d",
            nargs="*",
            help="Dataset name(s) to process. Processes all available data if not specified. Can be multiple: --datasets dataset1 dataset2",
        )
        parser.add_argument(
            "--chunk-size",
            type=int,
            help="Maximum tokens per chunk. Auto-calculated based on LLM if not specified (~512-8192 tokens)",
        )
        parser.add_argument(
            "--chunker",
            choices=CHUNKER_CHOICES,
            default="TextChunker",
            help="Text chunking strategy (default: TextChunker)",
        )
        parser.add_argument(
            "--background",
            "-b",
            action="store_true",
            help="Run processing in background and return immediately (recommended for large datasets)",
        )
        parser.add_argument("--verbose", "-v", action="store_true", help="Show detailed progress information")
        parser.add_argument(
            "--content-type",
            "-t",
            choices=["text", "dialog"],
            default="text",
            help="Content type: 'text' for articles/documents, 'dialog' for conversations/chat logs (default: text)",
        )

    def execute(self, args: argparse.Namespace) -> None:
        try:
            # Import m_flow here to avoid circular imports
            import m_flow

            # Prepare datasets parameter
            datasets = args.datasets if args.datasets else None
            dataset_msg = f" for datasets {datasets}" if datasets else " for all available data"
            fmt.echo(f"Starting memorization{dataset_msg}...")

            if args.verbose:
                fmt.note("This process will analyze your data and build knowledge graphs.")
                fmt.note("Depending on data size, this may take several minutes.")
                if args.background:
                    fmt.note("Running in background mode - the process will continue after this command exits.")

            # Prepare chunker parameter - will be handled in the async function

            # Run the async memorize function
            async def run_memorize():
                try:
                    # Import chunker classes here
                    from m_flow.ingestion.chunking.TextChunker import TextChunker

                    chunker_class = TextChunker  # Default
                    if args.chunker == "LangchainChunker":
                        try:
                            from m_flow.ingestion.chunking.LangchainChunker import LangchainChunker

                            chunker_class = LangchainChunker
                        except ImportError:
                            fmt.warning("LangchainChunker not available, using TextChunker")
                    elif args.chunker == "CsvChunker":
                        try:
                            from m_flow.ingestion.chunking.CsvChunker import CsvChunker

                            chunker_class = CsvChunker
                        except ImportError:
                            fmt.warning("CsvChunker not available, using TextChunker")

                    content_type = ContentType.DIALOG if args.content_type == "dialog" else ContentType.TEXT
                    result = await m_flow.memorize(
                        datasets=datasets,
                        chunker=chunker_class,
                        chunk_size=args.chunk_size,
                        run_in_background=args.background,
                        content_type=content_type,
                    )
                    return result
                except Exception as e:
                    raise CliCommandInnerException(f"Failed to memorize: {str(e)}") from e

            result = asyncio.run(run_memorize())

            if args.background:
                fmt.success("Memorization started in background!")
                if args.verbose and result:
                    fmt.echo("Background processing initiated. Use pipeline monitoring to track progress.")
            else:
                fmt.success("Memorization completed successfully!")
                if args.verbose and result:
                    fmt.echo(f"Processing results: {result}")

        except Exception as e:
            if isinstance(e, CliCommandInnerException):
                raise CliCommandException(str(e), error_code=1) from e
            raise CliCommandException(f"Error during memorization: {str(e)}", error_code=1) from e
