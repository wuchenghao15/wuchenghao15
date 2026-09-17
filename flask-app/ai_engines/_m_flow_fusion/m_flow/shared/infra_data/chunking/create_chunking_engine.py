"""Factory that instantiates the correct chunking back-end.

The *engine key* (``ChunkBackend`` enum member stored under
``config["chunk_engine"]``) selects one of three concrete
implementations.  Each is imported lazily so that optional dependencies
(Langchain, Haystack) are only loaded when actually requested.
"""

from __future__ import annotations

from typing import Any, Dict, Union

from m_flow.shared.data_models import ChunkBackend

# Type alias for the configuration dictionary.
EngineConfig = Dict[str, Any]


class ChunkingConfig(Dict):
    """Lightweight typed dict carrying chunking parameters.

    Kept as a ``dict`` subclass for backward-compat with code that
    accesses fields via ``config["chunk_engine"]``.
    """

    vector_db_url: str
    vector_db_key: str
    vector_db_provider: str


# Map enum values to (module_path, class_name) for lazy loading.
_ENGINE_REGISTRY: Dict[ChunkBackend, tuple] = {
    ChunkBackend.LANGCHAIN_ENGINE: (
        "m_flow.shared.infra_data.chunking.LangchainChunkingEngine",
        "LangchainChunkEngine",
    ),
    ChunkBackend.DEFAULT_ENGINE: (
        "m_flow.shared.infra_data.chunking.DefaultChunkEngine",
        "DefaultChunkEngine",
    ),
    ChunkBackend.HAYSTACK_ENGINE: (
        "m_flow.shared.infra_data.chunking.HaystackChunkEngine",
        "HaystackChunkEngine",
    ),
}


def create_chunking_engine(config: Union[ChunkingConfig, EngineConfig]):
    """Return a ready-to-use chunking engine described by *config*.

    Raises ``KeyError`` if the engine identifier is missing or unknown.
    """
    import importlib

    key = config["chunk_engine"]
    module_path, cls_name = _ENGINE_REGISTRY[key]
    module = importlib.import_module(module_path)
    engine_cls = getattr(module, cls_name)

    return engine_cls(
        chunk_size=config["chunk_size"],
        chunk_overlap=config["chunk_overlap"],
        chunk_strategy=config["chunk_strategy"],
    )
