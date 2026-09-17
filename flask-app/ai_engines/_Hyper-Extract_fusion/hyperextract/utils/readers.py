"""Document readers: UTF-8 text files plus markitdown-backed format conversion.

Two input classes are supported:

- Plain text (``.txt``/``.md``): read directly, with a best-effort encoding
  fallback for non-UTF-8 files (GBK etc.).
- Binary/structured documents (PDF, DOCX, PPTX, XLSX, HTML, ...): converted
  to Markdown via the optional ``markitdown`` backend
  (``pip install "hyperextract[ingest]"``).

Conversion output feeds the normal text pipeline unchanged: chunking,
extraction, indexing, and provenance all operate on plain strings.
"""

import importlib.util
from pathlib import Path

from hyperextract.utils.logging import get_logger

logger = get_logger(__name__)

#: Suffixes read directly as text (with encoding fallback).
TEXT_SUFFIXES = {".txt", ".md"}

#: Suffixes convertible through the optional ``markitdown`` backend,
#: mapped to a human-readable format label for error messages.
INGESTABLE_SUFFIXES = {
    ".pdf": "PDF",
    ".docx": "Word",
    ".doc": "Word (legacy)",
    ".pptx": "PowerPoint",
    ".xlsx": "Excel",
    ".xls": "Excel (legacy)",
    ".html": "HTML",
    ".htm": "HTML",
    ".csv": "CSV",
    ".json": "JSON",
    ".xml": "XML",
    ".epub": "EPUB",
    ".zip": "ZIP archive",
    ".eml": "Email",
    ".msg": "Outlook message",
}

_INGEST_HINT = (
    "Document conversion requires the optional ingest extra: "
    'pip install "hyperextract[ingest]"'
)


class ReaderError(Exception):
    """Raised when an input document cannot be read or converted."""


def markitdown_available() -> bool:
    """Return True when the optional ``markitdown`` backend is importable."""
    return importlib.util.find_spec("markitdown") is not None


def supported_suffixes() -> set[str]:
    """Input suffixes readable in the current environment.

    Text suffixes are always supported; ingestable suffixes only when
    ``markitdown`` is installed.
    """
    if markitdown_available():
        return set(TEXT_SUFFIXES) | set(INGESTABLE_SUFFIXES)
    return set(TEXT_SUFFIXES)


def read_text_with_fallback(path: str | Path) -> str:
    """Read a text file, tolerating non-UTF-8 encodings.

    UTF-8 is tried first; on failure ``charset-normalizer`` detects the
    encoding when available, otherwise the file is decoded lossily
    (``errors="replace"``) so ingestion never hard-fails on legacy encodings.
    """
    path = Path(path)
    raw = path.read_bytes()
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        pass
    try:
        from charset_normalizer import from_bytes

        best = from_bytes(raw).best()
        if best is not None:
            logger.info(
                "stage=text_decoded_fallback path=%s encoding=%s",
                path.name,
                best.encoding,
            )
            return str(best)
    except ImportError:
        pass
    logger.warning("stage=text_lossy_decode path=%s", path.name)
    return raw.decode("utf-8", errors="replace")


def convert_document(path: str | Path) -> str:
    """Convert a binary/structured document to Markdown via markitdown.

    Raises:
        ReaderError: If the backend is not installed or conversion fails
            (including text-less/damaged PDFs such as scanned documents).
    """
    path = Path(path)
    suffix = path.suffix.lower()
    if not markitdown_available():
        raise ReaderError(_INGEST_HINT)
    try:
        from markitdown import MarkItDown
    except Exception as e:  # pragma: no cover - broken install
        raise ReaderError(f"{_INGEST_HINT} (import failed: {e})") from e

    try:
        result = MarkItDown().convert(str(path))
    except Exception as e:
        raise ReaderError(f"Failed to convert {path.name}: {e}") from e

    text = (result.text_content or "") if result is not None else ""
    if not text.strip():
        raise ReaderError(
            f"No text could be extracted from {path.name}. The file may be "
            "scanned (image-only) — run OCR first, or feed a text-based copy."
        )
    if suffix == ".pdf" and "%PDF-" in text:
        # pdfminer's fallback dumps raw file bytes (including the header)
        # for damaged PDFs — treat that as a failed conversion rather than
        # silently feeding garbage downstream.
        raise ReaderError(
            f"{path.name} appears to be damaged or non-text (no readable "
            "text layer). The file may be scanned — run OCR first."
        )
    return text


def read_document(path: str | Path) -> str:
    """Read any supported input file as plain text.

    Dispatches by suffix: text suffixes go through the encoding-tolerant
    reader, everything else through markitdown conversion.

    Raises:
        ReaderError: If the suffix is unsupported or conversion fails.
    """
    path = Path(path)
    suffix = path.suffix.lower()
    if suffix in TEXT_SUFFIXES:
        return read_text_with_fallback(path)
    if suffix in INGESTABLE_SUFFIXES:
        return convert_document(path)
    raise ReaderError(
        f"Unsupported input type: {path.name or path} "
        f"({suffix or 'no suffix'}). Supported: "
        f"{', '.join(sorted(supported_suffixes()))}"
    )
