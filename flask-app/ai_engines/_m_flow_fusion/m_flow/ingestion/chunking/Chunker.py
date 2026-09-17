"""Base chunker interface."""

from __future__ import annotations

from typing import Any, Callable


class Chunker:
    """
    Base class for document chunking implementations.
    """

    def __init__(
        self,
        document: Any,
        get_text: Callable[[Any], str],
        max_chunk_size: int,
    ) -> None:
        self.document = document
        self.get_text = get_text
        self.max_chunk_size = max_chunk_size
        self.chunk_index = 0
        self.chunk_size = 0
        self.token_count = 0

    def read(self) -> Any:
        """Read and yield chunks. Must be implemented by subclasses."""
        raise NotImplementedError
