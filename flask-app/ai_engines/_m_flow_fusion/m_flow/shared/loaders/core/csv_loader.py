"""
CSV document loader for M-flow.

Converts CSV files into human-readable text representations
suitable for embedding and retrieval operations.
"""

from __future__ import annotations

import csv
import os
from typing import Any, Sequence

from m_flow.shared.files.storage import get_file_storage, get_storage_config
from m_flow.shared.files.utils.get_file_metadata import get_file_metadata
from m_flow.shared.loaders.LoaderInterface import LoaderInterface

# File type constants
_CSV_EXTENSIONS = frozenset(["csv"])
_CSV_MIME_TYPES = frozenset(["text/csv"])


def _format_row(row_num: int, data: dict[str, Any]) -> str:
    """Format a single CSV row as key-value pairs."""
    pairs = [f"{key}: {value}" for key, value in data.items()]
    return f"Row {row_num}:\n{', '.join(pairs)}\n"


class CsvLoader(LoaderInterface):
    """
    Loader for CSV (Comma-Separated Values) files.

    Parses CSV data and converts each row into a text representation
    with labeled fields for better semantic understanding.
    """

    @property
    def supported_extensions(self) -> Sequence[str]:
        """File extensions handled by this loader."""
        return list(_CSV_EXTENSIONS)

    @property
    def supported_mime_types(self) -> Sequence[str]:
        """MIME types handled by this loader."""
        return list(_CSV_MIME_TYPES)

    @property
    def loader_name(self) -> str:
        """Unique identifier for this loader."""
        return "csv_loader"

    def can_handle(self, extension: str, mime_type: str) -> bool:
        """Check if this loader supports the given file type."""
        ext_ok = extension.lower() in _CSV_EXTENSIONS
        mime_ok = mime_type.lower() in _CSV_MIME_TYPES
        return ext_ok and mime_ok

    async def load(
        self,
        file_path: str,
        encoding: str = "utf-8",
        **kwargs: Any,
    ) -> str:
        """
        Parse CSV and store as text representation.

        Args:
            file_path: Path to the CSV file.
            encoding: Character encoding of the file.
            **kwargs: Additional options (unused).

        Returns:
            Path to the stored text file.

        Raises:
            FileNotFoundError: If the source file doesn't exist.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"CSV file not found: {file_path}")

        # Get file metadata for output naming
        with open(file_path, "rb") as binary_handle:
            metadata = await get_file_metadata(binary_handle)

        output_filename = f"text_{metadata['content_hash']}.txt"

        # Parse CSV and format rows
        formatted_rows: list[str] = []
        with open(file_path, "r", encoding=encoding, newline="") as text_handle:
            reader = csv.DictReader(text_handle)
            for row_index, row_data in enumerate(reader, start=1):
                formatted_rows.append(_format_row(row_index, row_data))

        content = "\n".join(formatted_rows)

        # Store result
        config = get_storage_config()
        storage = get_file_storage(config["data_root_directory"])
        return await storage.store(output_filename, content)
