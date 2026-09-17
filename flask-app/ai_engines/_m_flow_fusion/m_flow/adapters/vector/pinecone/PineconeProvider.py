"""
Pinecone cloud vector store adapter.

Requires: ``pip install m_flow[pinecone]``

Configuration via environment variables::

    VECTOR_DB_PROVIDER=pinecone
    PINECONE_API_KEY=your-key
    PINECONE_INDEX_NAME=m_flow
"""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional, TYPE_CHECKING
from uuid import UUID

from m_flow.shared.logging_utils import get_logger

if TYPE_CHECKING:
    from m_flow.auth.models import User
    from m_flow.core import MemoryNode

_log = get_logger(__name__)


class PineconeProvider:
    """
    Vector store backed by Pinecone (cloud-hosted).

    Implements the M-flow VectorProvider protocol for seamless integration
    with the memory pipeline.
    """

    def __init__(
        self,
        api_key: str = "",
        index_name: str = "m_flow",
        namespace: str = "default",
        embedding_engine: Any = None,
        **kwargs,
    ):
        try:
            from pinecone import Pinecone
        except ImportError as exc:
            raise ImportError("pinecone is required. Install with: pip install m_flow[pinecone]") from exc

        self._api_key = api_key or os.getenv("PINECONE_API_KEY", "")
        self._index_name = index_name or os.getenv("PINECONE_INDEX_NAME", "m_flow")
        self._namespace = namespace
        self.embedding_engine = embedding_engine

        self._pc = Pinecone(api_key=self._api_key)
        self._index = self._pc.Index(self._index_name)
        _log.info("Pinecone connected: index=%s namespace=%s", self._index_name, self._namespace)

    # ------------------------------------------------------------------
    # Collection management
    # ------------------------------------------------------------------

    async def create_collection(self, collection_name: str, payload_schema=None):
        _log.debug("Pinecone: create_collection %s (namespace-based, no-op)", collection_name)

    async def has_collection(self, collection_name: str) -> bool:
        stats = self._index.describe_index_stats()
        return collection_name in (stats.get("namespaces") or {})

    async def delete_collection(self, collection_name: str):
        self._index.delete(delete_all=True, namespace=collection_name)

    # ------------------------------------------------------------------
    # Memory node CRUD
    # ------------------------------------------------------------------

    async def create_memory_nodes(
        self,
        collection_name: str,
        memory_nodes: List["MemoryNode"],
    ) -> None:
        vectors = []
        for node in memory_nodes:
            text = node.extract_index_text() if hasattr(node, "extract_index_text") else str(node)
            embedding = await self.embedding_engine.embed_data([text])
            vectors.append(
                {
                    "id": str(node.id),
                    "values": embedding[0] if embedding else [],
                    "metadata": {"text": text, "type": getattr(node, "type", "")},
                }
            )

        if vectors:
            self._index.upsert(vectors=vectors, namespace=collection_name)
            _log.info("Pinecone upserted %d vectors to %s", len(vectors), collection_name)

    async def retrieve(self, collection_name: str, memory_node_ids: List[str]) -> List[Dict]:
        results = self._index.fetch(ids=memory_node_ids, namespace=collection_name)
        return [{"id": vid, **vec.get("metadata", {})} for vid, vec in (results.get("vectors") or {}).items()]

    async def search(
        self,
        collection_name: str,
        query_text: str,
        limit: int = 10,
        **kwargs,
    ) -> List[Dict]:
        embedding = await self.embedding_engine.embed_data([query_text])
        if not embedding:
            return []

        results = self._index.query(
            vector=embedding[0],
            top_k=limit,
            include_metadata=True,
            namespace=collection_name,
        )
        return [
            {
                "id": match["id"],
                "score": match.get("score", 0),
                **(match.get("metadata") or {}),
            }
            for match in results.get("matches", [])
        ]

    async def batch_search(self, collection_name, queries, limit=10, **kwargs):
        results = []
        for q in queries:
            results.append(await self.search(collection_name, q, limit, **kwargs))
        return results

    async def delete_memory_nodes(self, collection_name: str, memory_node_ids: List[str]):
        self._index.delete(ids=memory_node_ids, namespace=collection_name)

    async def prune(self):
        _log.info("Pinecone prune: deleting all vectors in index %s", self._index_name)
        self._index.delete(delete_all=True, namespace=self._namespace)

    # ------------------------------------------------------------------
    # Embedding
    # ------------------------------------------------------------------

    async def embed_data(self, data: List[str]) -> List[List[float]]:
        if self.embedding_engine:
            return await self.embedding_engine.embed_data(data)
        return []
