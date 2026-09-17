"""
Abstract interface for vector database adapters.
"""

from __future__ import annotations

from abc import abstractmethod
from typing import Any, Dict, List, Optional, Protocol, TYPE_CHECKING
from uuid import UUID

if TYPE_CHECKING:
    from m_flow.core import MemoryNode
    from m_flow.auth.models import User


class VectorProvider(Protocol):
    """
    Contract for vector store backends (Qdrant, LanceDB, Weaviate, etc.).

    Implementations must provide collection management, CRUD for memory
    nodes, and semantic search capabilities.
    """

    # -------------------------------------------------------------------------
    # Collection management
    # -------------------------------------------------------------------------

    @abstractmethod
    async def has_collection(self, collection_name: str) -> bool:
        """Return True if collection *collection_name* exists."""
        ...

    @abstractmethod
    async def create_collection(
        self,
        collection_name: str,
        payload_schema: Optional[Any] = None,
    ) -> None:
        """Create a new collection, optionally with a payload schema."""
        ...

    # -------------------------------------------------------------------------
    # Memory node CRUD
    # -------------------------------------------------------------------------

    @abstractmethod
    async def create_memory_nodes(
        self,
        collection_name: str,
        memory_nodes: List["MemoryNode"],
    ) -> None:
        """Insert memory nodes into the specified collection."""
        ...

    @abstractmethod
    async def retrieve(
        self,
        collection_name: str,
        memory_node_ids: List[str],
    ) -> List[Dict[str, Any]]:
        """Fetch memory nodes by ID."""
        ...

    @abstractmethod
    async def delete_memory_nodes(
        self,
        collection_name: str,
        memory_node_ids: List[str],
    ) -> None:
        """Remove memory nodes by ID."""
        ...

    # -------------------------------------------------------------------------
    # Search
    # -------------------------------------------------------------------------

    @abstractmethod
    async def search(
        self,
        collection_name: str,
        query_text: Optional[str] = None,
        query_vector: Optional[List[float]] = None,
        limit: Optional[int] = None,
        with_vector: bool = False,
        where_filter: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Semantic search by text or vector.

        *where_filter* is an optional SQL-like expression for post-filtering.
        """
        ...

    @abstractmethod
    async def batch_search(
        self,
        collection_name: str,
        query_texts: List[str],
        limit: Optional[int] = None,
        with_vectors: bool = False,
    ) -> List[List[Dict[str, Any]]]:
        """Batch semantic search for multiple queries."""
        ...

    # -------------------------------------------------------------------------
    # Embedding
    # -------------------------------------------------------------------------

    @abstractmethod
    async def embed_data(self, texts: List[str]) -> List[List[float]]:
        """Generate vector embeddings for the given texts."""
        ...

    # -------------------------------------------------------------------------
    # Maintenance
    # -------------------------------------------------------------------------

    @abstractmethod
    async def prune(self) -> None:
        """Remove stale or orphaned data."""
        ...

    # -------------------------------------------------------------------------
    # Optional extension points (default implementations provided)
    # -------------------------------------------------------------------------

    async def get_connection(self) -> Any:
        """Return underlying connection object if applicable."""
        return None

    async def get_collection(self, collection_name: str) -> Any:
        """Return collection handle if applicable."""
        return None

    async def create_vector_index(
        self,
        index_name: str,
        index_property_name: str,
    ) -> None:
        """Create a vector index (no-op by default)."""
        pass

    async def index_memory_nodes(
        self,
        index_name: str,
        index_property_name: str,
        memory_nodes: List["MemoryNode"],
    ) -> None:
        """Index nodes for faster retrieval (no-op by default)."""
        pass

    def get_memory_node_schema(self, model_type: Any) -> Any:
        """Transform model to backend-specific schema (identity by default)."""
        return model_type

    # -------------------------------------------------------------------------
    # Multi-tenancy hooks
    # -------------------------------------------------------------------------

    @classmethod
    async def create_dataset(
        cls,
        dataset_id: Optional[UUID],
        user: Optional["User"],
    ) -> Dict[str, Any]:
        """
        Provision a vector store for a new dataset.

        Returns connection info to be persisted in the relational DB.
        """
        return {}

    async def delete_dataset(
        self,
        dataset_id: UUID,
        user: "User",
    ) -> None:
        """Deprovision the vector store for a dataset."""
        pass
