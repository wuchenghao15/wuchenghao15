"""
Configuration for text chunking operations.

Provides settings and defaults for how documents are split
into smaller chunks for processing and embedding.
"""

from __future__ import annotations

import os
from functools import lru_cache
from typing import Any

from pydantic_settings import BaseSettings
from m_flow.config.env_compat import MflowSettings, SettingsConfigDict

from m_flow.shared.data_models import ChunkBackend, ChunkMode

# Environment variable names
_SIZE_ENV_VAR = "MFLOW_CHUNK_SIZE"

# Default values
_DEFAULT_CHUNK_SIZE = 3000
_DEFAULT_OVERLAP = 10


def _read_size_from_env() -> int:
    """Parse chunk size from environment or use default."""
    raw = os.getenv(_SIZE_ENV_VAR)
    if raw:
        try:
            return int(raw)
        except ValueError:
            pass
    return _DEFAULT_CHUNK_SIZE


class ChunkConfig(MflowSettings):
    """
    Settings for document chunking behavior.

    Controls how text content is segmented into chunks for
    embedding and retrieval operations.

    Attributes:
        chunk_size: Maximum tokens per chunk.
        chunk_overlap: Overlap tokens between adjacent chunks.
        chunk_strategy: Chunking algorithm to use.
        chunk_engine: Backend engine for chunking.

    Environment Variables:
        MFLOW_CHUNK_SIZE: Override default chunk size.
        CHUNK_OVERLAP: Override default overlap.
    """

    chunk_size: int = _DEFAULT_CHUNK_SIZE
    chunk_overlap: int = _DEFAULT_OVERLAP
    chunk_strategy: ChunkMode = ChunkMode.PARAGRAPH
    chunk_engine: ChunkBackend = ChunkBackend.DEFAULT_ENGINE

    model_config = SettingsConfigDict(
        env_prefix="MFLOW_",
        env_file=".env",
        extra="allow",
    )

    def __init__(self, **kwargs: Any) -> None:
        # Apply environment override for chunk_size if not explicitly set
        if "chunk_size" not in kwargs:
            env_size = _read_size_from_env()
            if env_size != _DEFAULT_CHUNK_SIZE:
                kwargs["chunk_size"] = env_size
        super().__init__(**kwargs)

    def to_dict(self) -> dict[str, Any]:
        """Export configuration as dictionary."""
        return {
            "chunk_size": self.chunk_size,
            "chunk_overlap": self.chunk_overlap,
            "chunk_strategy": self.chunk_strategy,
            "chunk_engine": self.chunk_engine,
        }


@lru_cache(maxsize=1)
def get_chunk_config() -> ChunkConfig:
    """
    Retrieve the global chunking configuration singleton.

    Returns:
        Cached ChunkConfig instance.
    """
    return ChunkConfig()


def reset_chunk_config() -> None:
    """Clear the cached configuration (useful for testing)."""
    get_chunk_config.cache_clear()
