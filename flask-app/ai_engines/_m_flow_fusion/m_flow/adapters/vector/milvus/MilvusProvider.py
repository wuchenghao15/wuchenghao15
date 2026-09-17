"""
Milvus / Zilliz Cloud vector store adapter.

Requires: ``pip install m_flow[milvus]``

Configuration via environment variables::

    VECTOR_DB_PROVIDER=milvus
    MILVUS_URI=http://localhost:19530
    MILVUS_TOKEN=
"""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from m_flow.shared.logging_utils import get_logger

if TYPE_CHECKING:
    from m_flow.core import MemoryNode

_log = get_logger(__name__)

_DEFAULT_DIM = 3072


class MilvusProvider:
    """
    Vector store backed by Milvus or Zilliz Cloud.

    Implements the M-flow VectorProvider protocol.
    """

    def __init__(
        self,
        uri: str = "",
        token: str = "",
        collection_prefix: str = "mflow",
        dimension: int = _DEFAULT_DIM,
        embedding_engine: Any = None,
        **kwargs,
    ):
        try:
            from pymilvus import MilvusClient
        except ImportError as exc:
            raise ImportError("pymilvus is required. Install with: pip install m_flow[milvus]") from exc

        self._uri = uri or os.getenv("MILVUS_URI", "http://localhost:19530")
        self._token = token or os.getenv("MILVUS_TOKEN", "")
        self._prefix = collection_prefix
        self._dim = dimension
        self.embedding_engine = embedding_engine

        self._client = MilvusClient(uri=self._uri, token=self._token)
        _log.info("Milvus connected: uri=%s prefix=%s", self._uri, self._prefix)

    def _col(self, name: str) -> str:
        return f"{self._prefix}_{name}"

    # ------------------------------------------------------------------
    # Collection management
    # ------------------------------------------------------------------

    async def create_collection(self, collection_name: str, payload_schema=None):
        from pymilvus import DataType

        col = self._col(collection_name)
        if self._client.has_collection(col):
            return

        schema = self._client.create_schema(auto_id=False)
        schema.add_field("id", DataType.VARCHAR, max_length=128, is_primary=True)
        schema.add_field("vector", DataType.FLOAT_VECTOR, dim=self._dim)
        schema.add_field("text", DataType.VARCHAR, max_length=65535)
        schema.add_field("node_type", DataType.VARCHAR, max_length=256)

        index_params = self._client.prepare_index_params()
        index_params.add_index(field_name="vector", metric_type="COSINE", index_type="HNSW")

        self._client.create_collection(
            collection_name=col,
            schema=schema,
            index_params=index_params,
        )
        _log.info("Milvus collection created: %s (dim=%d)", col, self._dim)

    async def has_collection(self, collection_name: str) -> bool:
        return self._client.has_collection(self._col(collection_name))

    async def delete_collection(self, collection_name: str):
        col = self._col(collection_name)
        if self._client.has_collection(col):
            self._client.drop_collection(col)

    # ------------------------------------------------------------------
    # Memory node CRUD
    # ------------------------------------------------------------------

    async def create_memory_nodes(
        self,
        collection_name: str,
        memory_nodes: List["MemoryNode"],
    ) -> None:
        await self.create_collection(collection_name)
        col = self._col(collection_name)

        rows = []
        for node in memory_nodes:
            text = node.extract_index_text() if hasattr(node, "extract_index_text") else str(node)
            embedding = await self.embedding_engine.embed_data([text])
            rows.append(
                {
                    "id": str(node.id),
                    "vector": embedding[0] if embedding else [0.0] * self._dim,
                    "text": text[:65535],
                    "node_type": getattr(node, "type", ""),
                }
            )

        if rows:
            self._client.upsert(collection_name=col, data=rows)
            _log.info("Milvus upserted %d rows to %s", len(rows), col)

    async def retrieve(self, collection_name: str, memory_node_ids: List[str]) -> List[Dict]:
        col = self._col(collection_name)
        results = self._client.get(collection_name=col, ids=memory_node_ids)
        return [{"id": r["id"], "text": r.get("text", "")} for r in results]

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

        col = self._col(collection_name)
        results = self._client.search(
            collection_name=col,
            data=[embedding[0]],
            limit=limit,
            output_fields=["id", "text", "node_type"],
        )
        return [
            {"id": hit["id"], "score": hit.get("distance", 0), "text": hit["entity"].get("text", "")}
            for hit in (results[0] if results else [])
        ]

    async def batch_search(self, collection_name, queries, limit=10, **kwargs):
        results = []
        for q in queries:
            results.append(await self.search(collection_name, q, limit, **kwargs))
        return results

    async def delete_memory_nodes(self, collection_name: str, memory_node_ids: List[str]):
        col = self._col(collection_name)
        self._client.delete(collection_name=col, ids=memory_node_ids)

    async def prune(self):
        collections = self._client.list_collections()
        for col in collections:
            if col.startswith(self._prefix):
                self._client.drop_collection(col)
        _log.info("Milvus pruned all %s_* collections", self._prefix)

    # ------------------------------------------------------------------
    # Embedding
    # ------------------------------------------------------------------

    async def embed_data(self, data: List[str]) -> List[List[float]]:
        if self.embedding_engine:
            return await self.embedding_engine.embed_data(data)
        return []
