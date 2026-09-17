"""Centralised registry that dispatches files to the correct loader."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

from .LoaderInterface import LoaderInterface
from m_flow.shared.files.utils.guess_file_type import guess_file_type
from m_flow.shared.logging_utils import get_logger

_log = get_logger(__name__)

# Fallback ordering when no explicit preference is given.
_DEFAULT_PRIORITY = [
    "text_loader",
    "pypdf_loader",
    "image_loader",
    "audio_loader",
    "csv_loader",
    "unstructured_loader",
    "advanced_pdf_loader",
]


class LoaderEngine:
    """Registry that maps file types to :class:`LoaderInterface` implementations."""

    def __init__(self) -> None:
        self._registry: Dict[str, LoaderInterface] = {}
        self._ext_index: Dict[str, List[LoaderInterface]] = {}
        self._mime_index: Dict[str, List[LoaderInterface]] = {}
        self.priority_order = list(_DEFAULT_PRIORITY)

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------

    def register_loader(self, loader: LoaderInterface) -> bool:
        """Add *loader* to the internal registry and update lookup indices."""
        name = loader.loader_name
        self._registry[name] = loader

        for ext in loader.supported_extensions:
            normalised = ext.lower()
            self._ext_index.setdefault(normalised, []).append(loader)

        for mt in loader.supported_mime_types:
            self._mime_index.setdefault(mt, []).append(loader)

        _log.info("Registered loader: %s", name)
        return True

    # ------------------------------------------------------------------
    # Lookup
    # ------------------------------------------------------------------

    def _try_loader(
        self,
        loader: LoaderInterface,
        ext_from_path: str,
        detected_ext: str,
        detected_mime: str,
    ) -> bool:
        """Return ``True`` when *loader* accepts the file."""
        if loader.can_handle(extension=ext_from_path, mime_type=detected_mime):
            return True
        return loader.can_handle(extension=detected_ext, mime_type=detected_mime)

    def get_loader(
        self,
        file_path: str,
        preferred_loaders: Optional[Dict[str, Dict[str, Any]]] = None,
    ) -> Optional[LoaderInterface]:
        """Resolve the best loader for *file_path*."""
        detected = guess_file_type(file_path)
        path_ext = Path(file_path).suffix.lstrip(".")

        # 1. honour explicit preferences
        if preferred_loaders:
            for name in preferred_loaders:
                if name not in self._registry:
                    _log.info("Skipping %s: preferred loader not registered", name)
                    continue
                candidate = self._registry[name]
                if self._try_loader(candidate, path_ext, detected.extension, detected.mime):
                    return candidate

        # 2. fallback to default priority
        for name in self.priority_order:
            if name not in self._registry:
                _log.info("Skipping %s: not registered (default priority)", name)
                continue
            candidate = self._registry[name]
            if self._try_loader(candidate, path_ext, detected.extension, detected.mime):
                return candidate

        return None

    # ------------------------------------------------------------------
    # High-level API
    # ------------------------------------------------------------------

    async def load_file(
        self,
        file_path: str,
        preferred_loaders: Optional[Dict[str, Dict[str, Any]]] = None,
        **extra,
    ):
        """Locate the right loader for *file_path* and delegate ingestion."""
        loader = self.get_loader(file_path, preferred_loaders)
        if loader is None:
            raise ValueError(f"No registered loader can handle: {file_path}")

        _log.debug("Loading %s with %s", file_path, loader.loader_name)

        per_loader_cfg: dict = {}
        if preferred_loaders and loader.loader_name in preferred_loaders:
            per_loader_cfg = preferred_loaders[loader.loader_name]

        combined = {**per_loader_cfg, **extra}
        return await loader.load(file_path, **combined)

    # ------------------------------------------------------------------
    # Introspection helpers
    # ------------------------------------------------------------------

    def get_available_loaders(self) -> List[str]:
        """Return names of all registered loaders."""
        return list(self._registry)

    def get_loader_info(self, loader_name: str) -> Dict[str, Any]:
        """Return metadata dict for a registered loader, or empty dict."""
        if loader_name not in self._registry:
            return {}
        inst = self._registry[loader_name]
        return {
            "name": inst.loader_name,
            "extensions": inst.supported_extensions,
            "mime_types": inst.supported_mime_types,
        }
