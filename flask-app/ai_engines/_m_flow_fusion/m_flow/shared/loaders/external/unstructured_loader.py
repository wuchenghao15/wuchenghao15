"""
Generic document loader using the unstructured library.

Provides extraction capabilities for various document formats including
Office documents, presentations, spreadsheets, and email messages.
"""

from __future__ import annotations

from typing import Any

from m_flow.shared.files.storage import get_file_storage, get_storage_config
from m_flow.shared.files.utils.get_file_metadata import get_file_metadata
from m_flow.shared.loaders.LoaderInterface import LoaderInterface
from m_flow.shared.logging_utils import get_logger

_log = get_logger(__name__)

# Document format support mappings
_SUPPORTED_EXTENSIONS: frozenset[str] = frozenset(
    [
        # Word processing
        "docx",
        "doc",
        "odt",
        "rtf",
        # Spreadsheets
        "xlsx",
        "xls",
        "ods",
        # Presentations
        "pptx",
        "ppt",
        "odp",
        # Web and email
        "html",
        "htm",
        "eml",
        "msg",
        # eBooks
        "epub",
    ]
)

_SUPPORTED_MIMES: frozenset[str] = frozenset(
    [
        # Word processing
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/msword",
        "application/vnd.oasis.opendocument.text",
        "application/rtf",
        # Spreadsheets
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/vnd.ms-excel",
        "application/vnd.oasis.opendocument.spreadsheet",
        # Presentations
        "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        "application/vnd.ms-powerpoint",
        "application/vnd.oasis.opendocument.presentation",
        # Web and email
        "text/html",
        "message/rfc822",
        # eBooks
        "application/epub+zip",
    ]
)


class UnstructuredLoader(LoaderInterface):
    """
    Multi-format document loader powered by unstructured.

    Automatically detects document type and extracts text content
    using the unstructured library's auto-partition functionality.
    """

    @property
    def supported_extensions(self) -> list[str]:
        """File extensions this loader can process."""
        return list(_SUPPORTED_EXTENSIONS)

    @property
    def supported_mime_types(self) -> list[str]:
        """MIME types this loader can process."""
        return list(_SUPPORTED_MIMES)

    @property
    def loader_name(self) -> str:
        """Unique identifier for this loader."""
        return "unstructured_loader"

    def can_handle(self, extension: str, mime_type: str) -> bool:
        """
        Check if this loader supports the given file type.

        Args:
            extension: File extension (without dot).
            mime_type: MIME type string.

        Returns:
            True if both extension and mime_type are supported.
        """
        ext_ok = extension.lower() in _SUPPORTED_EXTENSIONS
        mime_ok = mime_type.lower() in _SUPPORTED_MIMES
        return ext_ok and mime_ok

    async def load(
        self,
        file_path: str,
        strategy: str = "auto",
        **kwargs: Any,
    ) -> str:
        """
        Extract text content from a document.

        Args:
            file_path: Path to the document file.
            strategy: Extraction strategy ("auto", "fast", "hi_res", "ocr_only").
            **kwargs: Additional parameters for unstructured.

        Returns:
            Path to the stored extracted text file.

        Raises:
            ImportError: If unstructured library is not installed.
            RuntimeError: If document processing fails.
        """
        # Verify unstructured is available
        try:
            from unstructured.partition.auto import partition
        except ImportError as err:
            raise ImportError("The unstructured library is required. Install with: pip install unstructured") from err

        _log.info("Processing document: %s", file_path)

        try:
            # Compute content hash for output naming
            with open(file_path, "rb") as fp:
                metadata = await get_file_metadata(fp)

            output_name = f"text_{metadata['content_hash']}.txt"

            # Extract document elements
            partition_opts = {
                "filename": file_path,
                "strategy": strategy,
                **kwargs,
            }
            elements = partition(**partition_opts)

            # Convert elements to text
            text_segments: list[str] = []
            for element in elements:
                segment = str(element).strip()
                if segment:
                    text_segments.append(segment)

            combined = "\n\n".join(text_segments)

            # Persist extracted content
            storage_cfg = get_storage_config()
            storage = get_file_storage(storage_cfg["data_root_directory"])
            stored_path = await storage.store(output_name, combined)

            return stored_path

        except Exception as err:
            _log.error("Document processing failed for %s: %s", file_path, err)
            raise RuntimeError(f"Failed to process document: {err}") from err
