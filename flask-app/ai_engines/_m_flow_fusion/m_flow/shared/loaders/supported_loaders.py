"""
Loader registry for M-flow document processing.

Maintains a mapping of loader names to their implementation classes,
with automatic registration of optional loaders when available.
"""

from __future__ import annotations

from typing import Dict, Type

from m_flow.shared.loaders.LoaderInterface import LoaderInterface

# Import core loaders (always available)
from m_flow.shared.loaders.core import (
    AudioLoader,
    CsvLoader,
    ImageLoader,
    TextLoader,
)
from m_flow.shared.loaders.external import PyPdfLoader


def _build_core_registry() -> Dict[str, Type[LoaderInterface]]:
    """Initialize registry with core loaders."""
    loaders = [
        PyPdfLoader,
        TextLoader,
        ImageLoader,
        AudioLoader,
        CsvLoader,
    ]
    return {loader.loader_name: loader for loader in loaders}


# Global loader registry
supported_loaders: Dict[str, Type[LoaderInterface]] = _build_core_registry()


def _register_optional(module_path: str, class_name: str) -> None:
    """
    Attempt to register an optional loader.

    Silently skips if the loader's dependencies are not installed.
    """
    try:
        module = __import__(module_path, fromlist=[class_name])
        loader_class = getattr(module, class_name)
        key = loader_class.loader_name
        supported_loaders[key] = loader_class
    except (ImportError, AttributeError):
        # Dependency not available - skip this loader
        pass


# Register optional loaders (may not be installed)
_register_optional("m_flow.shared.loaders.external", "UnstructuredLoader")
_register_optional("m_flow.shared.loaders.external", "AdvancedPdfLoader")
_register_optional("m_flow.shared.loaders.external", "BeautifulSoupLoader")
