"""
Layout-aware PDF extraction using unstructured library.

Provides advanced PDF parsing that preserves document structure,
extracts tables, and handles images with fallback to simple extraction.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from m_flow.shared.files.storage import get_file_storage, get_storage_config
from m_flow.shared.files.utils.get_file_metadata import get_file_metadata
from m_flow.shared.loaders.LoaderInterface import LoaderInterface
from m_flow.shared.logging_utils import get_logger

_log = get_logger(__name__)

# Supported file types
_PDF_EXTENSIONS = frozenset(["pdf"])
_PDF_MIME_TYPES = frozenset(["application/pdf"])


@dataclass
class _PageContent:
    """Accumulator for content within a single PDF page."""

    page_number: Optional[int] = None
    parts: list[str] = field(default_factory=list)

    def render(self) -> str:
        """Render page content as formatted string."""
        header = f"Page {self.page_number}:" if self.page_number else "Page:"
        body = "\n\n".join(self.parts)
        return f"{header}\n{body}\n"


def _normalize_text(value: Any) -> str:
    """Clean and normalize text content."""
    if value is None:
        return ""
    text = str(value)
    # Replace non-breaking spaces
    text = text.replace("\xa0", " ")
    return text.strip()


def _element_to_dict(element: Any) -> dict[str, Any]:
    """
    Convert an unstructured element to a dictionary.

    Falls back to extracting attributes directly if to_dict() fails.
    """
    if hasattr(element, "to_dict"):
        try:
            return element.to_dict()
        except Exception:
            pass

    # Fallback extraction
    elem_type = getattr(element, "category", None)
    if not elem_type:
        elem_type = type(element).__name__

    return {
        "type": elem_type,
        "text": getattr(element, "text", ""),
        "metadata": getattr(element, "metadata", {}),
    }


def _render_table(elem_dict: dict[str, Any]) -> str:
    """Extract table content, preferring HTML representation."""
    metadata = elem_dict.get("metadata", {})
    html_content = metadata.get("text_as_html")

    if html_content:
        return html_content.strip()

    return _normalize_text(elem_dict.get("text", ""))


def _render_image(metadata: dict[str, Any]) -> str:
    """Generate image placeholder with coordinate info."""
    base = "[Image omitted]"

    coords = metadata.get("coordinates")
    if not isinstance(coords, dict):
        return base

    points = coords.get("points")
    if not (isinstance(points, (list, tuple)) and len(points) >= 4):
        return base

    try:
        tl, _, _, br = points[:4]
        if len(tl) >= 2 and len(br) >= 2:
            bbox = f"bbox=({tl[0]}, {tl[1]}, {br[0]}, {br[1]})"
            result = f"{base} ({bbox}"

            # Add layout info if available
            width = coords.get("layout_width")
            height = coords.get("layout_height")
            system = coords.get("system")

            if width and height and system:
                result += f", system={system}, layout={width}x{height}"

            result += ")"
            return result
    except (TypeError, IndexError):
        pass

    return base


def _format_element(elem_dict: dict[str, Any]) -> str:
    """
    Format a single element for output.

    Handles tables, images, and text elements differently.
    Ignores headers and footers.
    """
    elem_type = str(elem_dict.get("type", "")).lower()
    text = _normalize_text(elem_dict.get("text", ""))
    metadata = elem_dict.get("metadata", {})

    # Special handling by type
    if elem_type == "table":
        return _render_table(elem_dict) or text

    if elem_type == "image":
        return text or _render_image(metadata)

    # Skip document structure elements
    if elem_type in ("header", "footer"):
        return ""

    return text


def _group_elements_by_page(elements: list[Any]) -> list[_PageContent]:
    """
    Group extracted elements by their page number.

    Returns a list of _PageContent objects, one per page.
    """
    pages: list[_PageContent] = []
    current = _PageContent()

    for element in elements:
        elem_dict = _element_to_dict(element)
        page_num = elem_dict.get("metadata", {}).get("page_number")

        # Start new page if number changes
        if current.page_number != page_num:
            if current.parts:
                pages.append(current)
            current = _PageContent(page_number=page_num)

        formatted = _format_element(elem_dict)
        if formatted:
            current.parts.append(formatted)

    # Don't forget the last page
    if current.parts:
        pages.append(current)

    return pages


class AdvancedPdfLoader(LoaderInterface):
    """
    PDF loader with layout-aware extraction using unstructured.

    Falls back to PyPdfLoader if unstructured extraction fails
    or returns no content.
    """

    @property
    def supported_extensions(self) -> list[str]:
        """File extensions this loader handles."""
        return list(_PDF_EXTENSIONS)

    @property
    def supported_mime_types(self) -> list[str]:
        """MIME types this loader handles."""
        return list(_PDF_MIME_TYPES)

    @property
    def loader_name(self) -> str:
        """Unique identifier for this loader."""
        return "advanced_pdf_loader"

    def can_handle(self, extension: str, mime_type: str) -> bool:
        """Check if this loader can process the given file."""
        return extension.lower() in _PDF_EXTENSIONS and mime_type.lower() in _PDF_MIME_TYPES

    async def _use_fallback(self, file_path: str, **kwargs: Any) -> str:
        """Delegate to simple PDF loader."""
        from m_flow.shared.loaders.external.pypdf_loader import PyPdfLoader

        _log.info("Using fallback PyPDF loader for: %s", file_path)
        simple_loader = PyPdfLoader()
        return await simple_loader.load(file_path, **kwargs)

    async def load(
        self,
        file_path: str,
        strategy: str = "auto",
        **kwargs: Any,
    ) -> str:
        """
        Extract text content from a PDF file.

        Args:
            file_path: Path to the PDF document.
            strategy: Extraction strategy ("auto", "fast", "hi_res", "ocr_only").
            **kwargs: Additional parameters for unstructured.

        Returns:
            Path to the stored extracted text file.
        """
        try:
            _log.info("Processing PDF: %s", file_path)

            # Get file metadata for naming
            with open(file_path, "rb") as fp:
                metadata = await get_file_metadata(fp)

            output_name = f"text_{metadata['content_hash']}.txt"

            # Import and run unstructured partition
            from unstructured.partition.pdf import partition_pdf

            partition_params = {
                "filename": file_path,
                "strategy": strategy,
                "infer_table_structure": True,
                "include_page_breaks": False,
                "include_metadata": True,
                **kwargs,
            }

            elements = partition_pdf(**partition_params)

            # Group by page and format
            pages = _group_elements_by_page(elements)

            if not pages:
                _log.warning(
                    "No content extracted from PDF, using fallback: %s",
                    file_path,
                )
                return await self._use_fallback(file_path, **kwargs)

            # Combine all pages
            combined = "\n".join(page.render() for page in pages)

            # Store result
            storage_cfg = get_storage_config()
            storage = get_file_storage(storage_cfg["data_root_directory"])
            stored_path = await storage.store(output_name, combined)

            return stored_path

        except Exception as err:
            _log.warning("PDF extraction failed, using fallback: %s", err)
            return await self._use_fallback(file_path, **kwargs)
