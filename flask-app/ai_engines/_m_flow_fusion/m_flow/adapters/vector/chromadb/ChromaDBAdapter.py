"""
ChromaDB vector database adapter.

Provides async interface for vector storage and similarity search
using ChromaDB as the backend.
"""

from __future__ import annotations

import asyncio
import json
import re
from typing import TYPE_CHECKING, List, Optional
from uuid import UUID

from chromadb import AsyncHttpClient, Settings

from m_flow.adapters.exceptions import MissingQueryParameterError
from m_flow.adapters.vector.exceptions import CollectionNotFoundError
from m_flow.adapters.vector.models.VectorSearchHit import VectorSearchHit
from m_flow.core import MemoryNode
from m_flow.core.utils import parse_id
from m_flow.shared.logging_utils import get_logger
from m_flow.storage.utils_mod.utils import get_own_properties

from ..embeddings.EmbeddingEngine import EmbeddingEngine
from ..utils import normalize_distances
from ..vector_db_interface import VectorProvider

if TYPE_CHECKING:
    pass

_log = get_logger("ChromaDB")

# Whitelist of filterable fields and their allowed values
# None value means any value is allowed (for dynamic fields like dataset_id)
_FILTER_WHITELIST: dict[str, list[str] | None] = {
    "memory_type": ["atomic", "episodic"],
    "dataset_id": None,  # Allow any UUID value
}


def _serialize_for_chroma(data: dict) -> dict:
    """
    Transform data dictionary for ChromaDB storage.

    ChromaDB only supports primitive types in metadata. Complex types
    are serialized to JSON strings with type-indicating suffixes.
    """
    result = {}

    for key, val in data.items():
        if val is None:
            continue
        if isinstance(val, UUID):
            result[key] = str(val)
        elif isinstance(val, dict):
            result[f"{key}__dict"] = json.dumps(val, default=str)
        elif isinstance(val, list):
            result[f"{key}__list"] = json.dumps(val, default=str)
        elif isinstance(val, (str, int, float, bool)):
            result[key] = val
        else:
            result[key] = str(val)

    return result


def _deserialize_from_chroma(data: dict) -> dict:
    """
    Restore data dictionary from ChromaDB storage format.

    Reverses the serialization performed by _serialize_for_chroma,
    converting JSON strings back to Python objects.
    """
    result = {}
    deferred_dict = []
    deferred_list = []

    for key in data.keys():
        if key.endswith("__dict"):
            deferred_dict.append(key)
        elif key.endswith("__list"):
            deferred_list.append(key)
        else:
            result[key] = data[key]

    # Restore dicts
    for key in deferred_dict:
        base_key = key[:-6]  # Remove __dict
        try:
            result[base_key] = json.loads(data[key])
        except (json.JSONDecodeError, TypeError) as err:
            _log.debug(f"Dict restoration failed for {key}: {err}")
            result[key] = data[key]

    # Restore lists
    for key in deferred_list:
        base_key = key[:-6]  # Remove __list
        try:
            result[base_key] = json.loads(data[key])
        except (json.JSONDecodeError, TypeError) as err:
            _log.debug(f"List restoration failed for {key}: {err}")
            result[key] = data[key]

    return result


def _parse_filter_clause(filter_str: str) -> Optional[dict]:
    """
    Parse SQL-style filter to ChromaDB where clause.

    Only accepts whitelisted fields and values for security.
    Format: payload.field = 'value'
    """
    if not filter_str:
        return None

    # Value part uses [\w-]+ to support UUIDs (containing hyphens)
    pattern = r"^payload\.(\w+)\s*=\s*'([\w-]+)'$"
    match = re.match(pattern, filter_str.strip())

    if not match:
        raise ValueError(f"Invalid filter format: '{filter_str}'. Expected: payload.field = 'value'")

    field, value = match.groups()

    if field not in _FILTER_WHITELIST:
        raise ValueError(f"Field '{field}' not filterable. Allowed: {list(_FILTER_WHITELIST.keys())}")

    allowed_values = _FILTER_WHITELIST[field]
    # None means any value is allowed (for dynamic fields like dataset_id)
    if allowed_values is not None and value not in allowed_values:
        raise ValueError(f"Value '{value}' invalid for '{field}'. Allowed: {allowed_values}")

    return {field: value}


class IndexSchema(MemoryNode):
    """Schema for text indexing with metadata."""

    text: str
    # Dataset isolation: for Episode Routing dataset filtering
    dataset_id: Optional[str] = None
    # Memory type: for atomic/episodic filtering
    memory_type: Optional[str] = None
    metadata: dict = {"index_fields": ["text"]}

    def model_dump(self):
        """Serialize for ChromaDB storage."""
        raw = super().model_dump()
        return _serialize_for_chroma(raw)


class ChromaDBAdapter(VectorProvider):
    """
    Async ChromaDB vector database adapter.

    Implements VectorProvider for ChromaDB, providing embedding,
    storage, and similarity search operations.
    """

    name = "ChromaDB"
    url: str
    api_key: str
    connection: AsyncHttpClient = None

    def __init__(
        self,
        url: Optional[str],
        api_key: Optional[str],
        embedding_engine: EmbeddingEngine,
    ):
        """
        Initialize ChromaDB adapter.

        Args:
            url: ChromaDB server URL
            api_key: Authentication token
            embedding_engine: Engine for text embedding
        """
        self._url = url
        self._api_key = api_key
        self._embed_engine = embedding_engine
        self._client: Optional[AsyncHttpClient] = None
        self._lock = asyncio.Lock()

    @property
    def url(self) -> str:
        return self._url

    @property
    def api_key(self) -> str:
        return self._api_key

    @property
    def embedding_engine(self) -> EmbeddingEngine:
        return self._embed_engine

    @property
    def VECTOR_DB_LOCK(self):
        return self._lock

    @property
    def connection(self) -> Optional[AsyncHttpClient]:  # noqa: F811 - overrides class attribute
        return self._client

    @connection.setter
    def connection(self, value):
        self._client = value

    async def get_connection(self) -> AsyncHttpClient:
        """Establish or return existing connection."""
        if self._client is None:
            auth_settings = Settings(
                chroma_client_auth_provider="token",
                chroma_client_auth_credentials=self._api_key,
            )
            self._client = await AsyncHttpClient(
                host=self._url,
                settings=auth_settings,
            )
        return self._client

    async def embed_data(self, data: list[str]) -> list[list[float]]:
        """Generate embeddings for text data."""
        return await self._embed_engine.embed_text(data)

    # =========================================================================
    # Collection Management
    # =========================================================================

    async def get_collection_names(self) -> list:
        """List all collection names."""
        client = await self.get_connection()
        return await client.list_collections()

    async def has_collection(self, collection_name: str) -> bool:
        """Check if collection exists."""
        names = await self.get_collection_names()
        return collection_name in names

    async def create_collection(self, collection_name: str, payload_schema=None):
        """Create collection if not exists."""
        async with self._lock:
            client = await self.get_connection()

            if not await self.has_collection(collection_name):
                await client.create_collection(
                    name=collection_name,
                    metadata={"hnsw:space": "cosine"},
                )

    async def get_collection(self, collection_name: str):
        """Get collection by name."""
        if not await self.has_collection(collection_name):
            raise CollectionNotFoundError(f"Collection '{collection_name}' not found")

        client = await self.get_connection()
        return await client.get_collection(collection_name)

    async def create_vector_index(self, index_name: str, index_property_name: str):
        """Create vector index (collection)."""
        combined_name = f"{index_name}_{index_property_name}"
        await self.create_collection(combined_name)

    # =========================================================================
    # Memory Node Operations
    # =========================================================================

    async def create_memory_nodes(self, collection_name: str, memory_nodes: list[MemoryNode]):
        """Upsert memory nodes into collection."""
        await self.create_collection(collection_name)
        coll = await self.get_collection(collection_name)

        # Extract embeddable data
        texts = [MemoryNode.extract_index_text(n) for n in memory_nodes]
        vec_size = self._embed_engine.get_vector_size()

        # Identify valid (non-None) entries
        valid_idx = [i for i, t in enumerate(texts) if t is not None]
        valid_texts = [texts[i] for i in valid_idx]

        # Embed valid texts
        if valid_texts:
            valid_vecs = await self.embed_data(valid_texts)
        else:
            valid_vecs = []

        # Build full vectors list
        zero_vec = [0.0] * vec_size
        embeddings = []
        v_idx = 0

        for i, t in enumerate(texts):
            if t is not None:
                embeddings.append(valid_vecs[v_idx])
                v_idx += 1
            else:
                embeddings.append(zero_vec)
                texts[i] = ""

        # Prepare IDs and metadata
        ids = [str(n.id) for n in memory_nodes]
        metadatas = [_serialize_for_chroma(get_own_properties(n)) for n in memory_nodes]

        await coll.upsert(
            ids=ids,
            embeddings=embeddings,
            metadatas=metadatas,
            documents=texts,
        )

    async def index_memory_nodes(
        self,
        index_name: str,
        index_property_name: str,
        memory_nodes: list[MemoryNode],
    ):
        """Index memory nodes by specific property.

        Preserves dataset_id and memory_type fields for:
        - Episode Routing dataset isolation filtering
        - Retrieval memory_type filtering
        """
        combined_name = f"{index_name}_{index_property_name}"

        schema_nodes = [
            IndexSchema(
                id=n.id,
                text=getattr(n, n.metadata["index_fields"][0]),
                dataset_id=getattr(n, "dataset_id", None),
                memory_type=getattr(n, "memory_type", None),
            )
            for n in memory_nodes
        ]

        await self.create_memory_nodes(combined_name, schema_nodes)

    async def retrieve(self, collection_name: str, memory_node_ids: list[str]) -> list[VectorSearchHit]:
        """Retrieve nodes by IDs."""
        coll = await self.get_collection(collection_name)
        results = await coll.get(ids=memory_node_ids, include=["metadatas"])

        return [
            VectorSearchHit(
                id=parse_id(nid),
                payload=_deserialize_from_chroma(meta),
                score=0,
            )
            for nid, meta in zip(results["ids"], results["metadatas"])
        ]

    async def delete_memory_nodes(self, collection_name: str, memory_node_ids: list[str]) -> bool:
        """Delete nodes by IDs."""
        coll = await self.get_collection(collection_name)
        await coll.delete(ids=memory_node_ids)
        return True

    # =========================================================================
    # Search Operations
    # =========================================================================

    async def search(
        self,
        collection_name: str,
        query_text: str = None,
        query_vector: List[float] = None,
        limit: Optional[int] = 15,
        with_vector: bool = False,
        normalized: bool = True,
        where_filter: Optional[str] = None,
    ) -> list[VectorSearchHit]:
        """
        Search collection by text or vector query.

        Args:
            collection_name: Target collection
            query_text: Text to search (will be embedded)
            query_vector: Pre-computed query vector
            limit: Maximum results
            with_vector: Include vectors in results
            normalized: Normalize distance scores
            where_filter: SQL-style filter clause
        """
        if query_text is None and query_vector is None:
            raise MissingQueryParameterError()

        if query_text and not query_vector:
            embedded = await self._embed_engine.embed_text([query_text])
            query_vector = embedded[0]

        try:
            coll = await self.get_collection(collection_name)

            if limit is None:
                limit = await coll.count()

            if limit <= 0:
                return []

            # Parse filter if provided
            chroma_where = None
            if where_filter:
                chroma_where = _parse_filter_clause(where_filter)

            include_fields = ["metadatas", "distances"]
            if with_vector:
                include_fields.append("embeddings")

            results = await coll.query(
                query_embeddings=[query_vector],
                include=include_fields,
                n_results=limit,
                where=chroma_where,
            )

            items = []
            for i, (nid, meta, dist) in enumerate(
                zip(
                    results["ids"][0],
                    results["metadatas"][0],
                    results["distances"][0],
                )
            ):
                item = {
                    "id": parse_id(nid),
                    "payload": _deserialize_from_chroma(meta),
                    "_distance": dist,
                }

                if with_vector and "embeddings" in results:
                    item["vector"] = results["embeddings"][0][i]

                items.append(item)

            # Normalize scores
            scores = normalize_distances(items)
            for i, score in enumerate(scores):
                items[i]["score"] = score

            return [
                VectorSearchHit(
                    id=item["id"],
                    payload=item["payload"],
                    score=item["score"],
                    vector=item.get("vector") if with_vector else None,
                )
                for item in items
            ]

        except Exception as err:
            _log.warning(f"Search failed: {err}")
            return []

    async def batch_search(
        self,
        collection_name: str,
        query_texts: List[str],
        limit: int = 5,
        with_vectors: bool = False,
    ) -> list[list[VectorSearchHit]]:
        """Batch search with multiple queries."""
        query_vecs = await self.embed_data(query_texts)
        coll = await self.get_collection(collection_name)

        include_fields = ["metadatas", "distances"]
        if with_vectors:
            include_fields.append("embeddings")

        results = await coll.query(
            query_embeddings=query_vecs,
            include=include_fields,
            n_results=limit,
        )

        batch_results = []

        for q_idx in range(len(query_texts)):
            items = []

            for r_idx, (nid, meta, dist) in enumerate(
                zip(
                    results["ids"][q_idx],
                    results["metadatas"][q_idx],
                    results["distances"][q_idx],
                )
            ):
                item = {
                    "id": parse_id(nid),
                    "payload": _deserialize_from_chroma(meta),
                    "_distance": dist,
                }

                if with_vectors and "embeddings" in results:
                    item["vector"] = results["embeddings"][q_idx][r_idx]

                items.append(item)

            scores = normalize_distances(items)

            query_results = []
            for i, item in enumerate(items):
                scored = VectorSearchHit(
                    id=item["id"],
                    payload=item["payload"],
                    score=scores[i],
                )

                if with_vectors:
                    scored.vector = item.get("vector")

                query_results.append(scored)

            batch_results.append(query_results)

        return batch_results

    # =========================================================================
    # Maintenance
    # =========================================================================

    async def prune(self) -> bool:
        """Delete all collections."""
        client = await self.get_connection()
        collections = await client.list_collections()

        for coll_name in collections:
            await client.delete_collection(coll_name)

        return True

    # Compatibility aliases
    _ALLOWED_FILTER_FIELDS = _FILTER_WHITELIST

    def _parse_where_filter_to_chroma(self, where_filter: str) -> Optional[dict]:
        """Alias for _parse_filter_clause."""
        return _parse_filter_clause(where_filter)


# Module-level compatibility aliases
def process_data_for_chroma(data: dict) -> dict:
    """Alias for _serialize_for_chroma."""
    return _serialize_for_chroma(data)


def restore_data_from_chroma(data: dict) -> dict:
    """Alias for _deserialize_from_chroma."""
    return _deserialize_from_chroma(data)
