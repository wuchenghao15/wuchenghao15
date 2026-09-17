"""
Simple PDF text extraction using pypdf.

Provides a lightweight PDF loader that extracts text content
page by page without advanced layout analysis.
"""

from __future__ import annotations

from typing import Any

from m_flow.shared.files.storage import get_file_storage, get_storage_config
from m_flow.shared.files.utils.get_file_metadata import get_file_metadata
from m_flow.shared.loaders.LoaderInterface import LoaderInterface
from m_flow.shared.logging_utils import get_logger

_log = get_logger(__name__)

# Supported file types
_PDF_EXT = frozenset(["pdf"])
_PDF_MIME = frozenset(["application/pdf"])


class PyPdfLoader(LoaderInterface):
    """
    Basic PDF loader using the pypdf library.

    Extracts raw text from each page of a PDF document.
    For layout-aware extraction, use AdvancedPdfLoader instead.
    """

    @property
    def supported_extensions(self) -> list[str]:
        """File extensions this loader handles."""
        return list(_PDF_EXT)

    @property
    def supported_mime_types(self) -> list[str]:
        """MIME types this loader handles."""
        return list(_PDF_MIME)

    @property
    def loader_name(self) -> str:
        """Unique identifier for this loader."""
        return "pypdf_loader"

    def can_handle(self, extension: str, mime_type: str) -> bool:
        """Check if this loader can process the given file."""
        return extension.lower() in _PDF_EXT and mime_type.lower() in _PDF_MIME

    async def load(
        self,
        file_path: str,
        strict: bool = False,
        **kwargs: Any,
    ) -> str:
        """
        Extract text content from a PDF file.

        Args:
            file_path: Path to the PDF document.
            strict: Enable strict PDF parsing mode.
            **kwargs: Additional arguments (unused).

        Returns:
            Path to the stored extracted text file.

        Raises:
            ImportError: If pypdf library is not installed.
            RuntimeError: If PDF processing fails.
        """
        # Verify pypdf is available
        try:
            from pypdf import PdfReader
        except ImportError as err:
            raise ImportError("The pypdf library is required. Install with: pip install pypdf") from err

        _log.info("Processing PDF: %s", file_path)

        try:
            with open(file_path, "rb") as fp:
                # Get content hash for naming
                metadata = await get_file_metadata(fp)
                fp.seek(0)

                output_name = f"text_{metadata['content_hash']}.txt"

                # Parse PDF
                reader = PdfReader(fp, strict=strict)

                # Extract text from each page
                page_outputs: list[str] = []

                for idx, page in enumerate(reader.pages, start=1):
                    try:
                        text = page.extract_text()
                        if text and text.strip():
                            page_outputs.append(f"Page {idx}:\n{text}\n")
                    except Exception as page_err:
                        _log.warning(
                            "Failed to extract page %d: %s",
                            idx,
                            page_err,
                        )

                # Combine pages
                combined = "\n".join(page_outputs)

                # Store result
                storage_cfg = get_storage_config()
                storage = get_file_storage(storage_cfg["data_root_directory"])
                stored_path = await storage.store(output_name, combined)

                return stored_path

        except Exception as err:
            _log.error("PDF processing failed for %s: %s", file_path, err)
            raise RuntimeError(f"Failed to process PDF: {err}") from err
