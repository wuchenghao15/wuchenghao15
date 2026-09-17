"""
External loader backends with optional dependencies.

This package provides document loaders that depend on third-party
libraries which may not be installed. Each loader is imported
with graceful fallback if its dependencies are unavailable.

Available Loaders
-----------------
PyPdfLoader
    Basic PDF text extraction using pypdf.

UnstructuredLoader
    Multi-format document parsing via the unstructured library.

AdvancedPdfLoader
    Layout-aware PDF extraction with table and image support.

BeautifulSoupLoader
    HTML/XML content extraction using BeautifulSoup4.

Installation
------------
Install optional dependencies as needed::

    pip install pypdf          # For PyPdfLoader
    pip install unstructured   # For UnstructuredLoader
    pip install beautifulsoup4 # For BeautifulSoupLoader
"""

from __future__ import annotations

# Always-available loader (pypdf is a core dependency)
from .pypdf_loader import PyPdfLoader as PyPdfLoader

# Build dynamic export list
_available_loaders: list[str] = ["PyPdfLoader"]


def _try_import(module: str, class_name: str) -> bool:
    """Attempt to import a loader class, returning success status."""
    try:
        loader_module = __import__(
            f".{module}",
            globals(),
            locals(),
            [class_name],
            level=1,
        )
        globals()[class_name] = getattr(loader_module, class_name)
        return True
    except (ImportError, AttributeError):
        return False


# Conditionally import optional loaders
if _try_import("unstructured_loader", "UnstructuredLoader"):
    _available_loaders.append("UnstructuredLoader")

if _try_import("advanced_pdf_loader", "AdvancedPdfLoader"):
    _available_loaders.append("AdvancedPdfLoader")

if _try_import("beautiful_soup_loader", "BeautifulSoupLoader"):
    _available_loaders.append("BeautifulSoupLoader")


__all__ = _available_loaders
