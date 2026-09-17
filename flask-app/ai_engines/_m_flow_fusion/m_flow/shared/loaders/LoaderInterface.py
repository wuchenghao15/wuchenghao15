"""
M-Flow document loader protocol.

Every file-format adapter that participates in the ingestion pipeline
must satisfy this interface.  The runtime uses :pyattr:`loader_name` for
registry look-ups and :pymeth:`can_handle` for dynamic dispatch when a
document's format needs to be resolved at import time.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Sequence


class LoaderInterface(ABC):
    """
    Specification that all format-specific loaders must fulfil.

    Subclasses declare which file extensions and MIME types they support,
    expose a stable ``loader_name`` for registry / logging, and implement
    the asynchronous ``load`` method that extracts textual content from a
    given file path.

    Lifecycle
    ---------
    1. The loader registry calls :pymeth:`can_handle` with the candidate
       file's extension and MIME type.
    2. If the loader claims the file, :pymeth:`load` is invoked to perform
       the actual extraction.
    3. The extracted content is forwarded to downstream chunking stages.
    """

    __slots__ = ()

    # ------------------------------------------------------------------
    # Capability declarations
    # ------------------------------------------------------------------

    @property
    @abstractmethod
    def supported_extensions(self) -> Sequence[str]:
        """Return lowercase extensions (no leading dot) this loader handles."""
        ...

    @property
    @abstractmethod
    def supported_mime_types(self) -> Sequence[str]:
        """Return MIME type strings this loader recognises."""
        ...

    @property
    @abstractmethod
    def loader_name(self) -> str:
        """Return a stable, unique identifier used for registry key and diagnostics."""
        ...

    # ------------------------------------------------------------------
    # Dispatch
    # ------------------------------------------------------------------

    @abstractmethod
    def can_handle(self, extension: str, mime_type: str) -> bool:
        """
        Decide whether this loader should process a file.

        Parameters
        ----------
        extension:
            File extension without the leading dot, lowercased.
        mime_type:
            IANA media-type string supplied by the upload layer.

        Returns
        -------
        bool
            ``True`` when this loader is the right choice for the file.
        """
        ...

    # ------------------------------------------------------------------
    # Extraction
    # ------------------------------------------------------------------

    @abstractmethod
    async def load(self, file_path: str, **kwargs: Any) -> str:
        """
        Read *file_path*, extract textual content, and persist it.

        Parameters
        ----------
        file_path:
            Absolute or pipeline-relative path to the source document.
        **kwargs:
            Loader-specific tunables (e.g. page range, encoding hints).

        Returns
        -------
        str
            Filesystem path where the extracted content has been stored.
        """
        ...
