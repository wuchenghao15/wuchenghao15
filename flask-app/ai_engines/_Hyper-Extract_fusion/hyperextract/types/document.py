"""Corpus Knowledge Pattern - retrievable raw text chunks (no LLM extraction).

Unlike the other AutoTypes, ``AutoDocument`` performs **no LLM extraction**:
``feed_text`` splits the text into chunks, stores them in an OMem-backed
chunk memory, and search returns the raw chunks. This is the baseline chunk
retrieval unit and is also useful as a fallback when extraction quality or
cost is a concern.

All provenance machinery (source ledger, per-document rollback, tags,
scoped search, content-hash change detection) is inherited from the
underlying OMem memory with ``track_sources=True``.
"""

import hashlib
from datetime import datetime
from pathlib import Path
from typing import Any

from langchain_core.embeddings import Embeddings
from langchain_core.language_models.chat_models import BaseChatModel
from ontomem import OMem
from ontomem.merger import MergeStrategy
from pydantic import BaseModel

from hyperextract.utils.logging import get_logger

from .base import BaseAutoType

logger = get_logger(__name__)


DEFAULT_DOCUMENT_PROMPT = (
    "You are a helpful assistant answering questions about a corpus of "
    "document chunks.\n\n### Context:\n{context}\n\n### Question:\n{question}"
)


class TextChunk(BaseModel):
    """A single retrievable chunk of source text."""

    content: str


class DocumentData(BaseModel):
    """Serialization wrapper for chunk-based knowledge abstracts (data.json)."""

    chunks: list[TextChunk] = []


def chunk_key_extractor(chunk: TextChunk) -> str:
    """Stable content-hash key: identical chunks dedup across documents."""
    return hashlib.sha1(chunk.content.encode("utf-8")).hexdigest()[:16]


class AutoDocument(BaseAutoType[DocumentData]):
    """AutoDocument - a searchable corpus of raw text chunks.

    Key characteristics:
        - Extraction target: none (chunking only, zero LLM extraction cost)
        - Storage: OMem memory of ``TextChunk`` items keyed by content hash
        - Indexing: embeddings of the chunk content
        - Provenance: full source ledger (``track_sources=True``) supporting
          per-document rollback, tags, and scoped search
    """

    def __init__(
        self,
        llm_client: BaseChatModel,
        embedder: Embeddings,
        *,
        chunk_size: int = 2048,
        chunk_overlap: int = 256,
        verbose: bool = False,
        **kwargs,
    ):
        """Initialize the document corpus.

        Args:
            llm_client: Language model client (used by ``chat`` only; the
                ingestion path makes no LLM calls).
            embedder: Embedding model for chunk indexing and search.
            chunk_size: Maximum characters per chunk.
            chunk_overlap: Overlapping characters between adjacent chunks.
            verbose: Whether to enable debug logging.
            **kwargs: Accepted for template-option compatibility; unused.
        """
        if kwargs:
            logger.debug("auto_document_ignored_options", options=sorted(kwargs))
        super().__init__(
            DocumentData,
            llm_client,
            embedder,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            verbose=verbose,
        )

    def _create_empty_instance(self) -> "AutoDocument":
        """Creates a new empty instance with the same configuration."""
        return self.__class__(
            llm_client=self.llm_client,
            embedder=self.embedder,
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            verbose=self.verbose,
        )

    def _default_prompt(self) -> str:
        """Returns the QA prompt (chunks are answered over, not extracted)."""
        return DEFAULT_DOCUMENT_PROMPT

    # ==================== Data Access Interface ====================

    @property
    def data(self) -> DocumentData:
        """Returns all stored chunks (read-only access)."""
        return DocumentData(chunks=list(self._memory.items))

    def empty(self) -> bool:
        """Checks if the corpus currently holds no chunks."""
        return self._memory.size == 0

    # ==================== State Management Lifecycle Hooks ====================

    def _init_data_state(self) -> None:
        """INIT/RESET: fresh chunk memory (ledger cleared with it)."""
        self._memory = OMem(
            memory_schema=TextChunk,
            key_extractor=chunk_key_extractor,
            llm_client=self.llm_client,
            embedder=self.embedder,
            strategy_or_merger=MergeStrategy.MERGE_FIELD,
            fields_for_index=["content"],
            track_sources=True,
            verbose=self.verbose,
        )

    def _init_index_state(self) -> None:
        """Index state lives inside the chunk memory."""
        self._memory.clear_index()

    def _set_data_state(self, data: DocumentData) -> None:
        """SET: full reset from serialized data (e.g. load from disk)."""
        self._init_data_state()
        self._memory.add(data.chunks)
        self.clear_index()

    def _update_data_state(self, incoming_data: DocumentData) -> None:
        """UPDATE: append chunks (dedup by content hash inside OMem)."""
        self._memory.add(incoming_data.chunks)

    # ==================== Extraction & Merge ====================

    def _chunk_text(self, text: str) -> list[TextChunk]:
        """Split text into chunk models (the only ingestion "extraction")."""
        if len(text) <= self.chunk_size:
            return [TextChunk(content=text)]
        return [
            TextChunk(content=chunk) for chunk in self.text_splitter.split_text(text)
        ]

    def _extract_data(self, text: str) -> DocumentData:
        """Chunk the text without any LLM call."""
        chunks = self._chunk_text(text)
        logger.debug("stage=document_chunking num_chunks=%d", len(chunks))
        return DocumentData(chunks=chunks)

    def merge_batch_data(self, data_list: list[DocumentData]) -> DocumentData:
        """Concatenate chunk batches; dedup happens by content hash in OMem."""
        if not data_list:
            return DocumentData(chunks=[])
        return DocumentData(
            chunks=[chunk for data in data_list for chunk in data.chunks]
        )

    def parse(self, text: str, *, source_id: str | None = None) -> "AutoDocument":
        """Parse into a NEW instance, recording the source ledger entry.

        The ledger entry is recorded on this instance's memory and adopted
        by the returned instance (mirroring the graph-family flow).
        """
        if source_id:
            self._memory.record_source(
                source_id, [chunk.model_dump() for chunk in self._chunk_text(text)]
            )
        return super().parse(text, source_id=source_id)

    def _adopt_source_ledger(self, other: "AutoDocument", source_id: str) -> None:
        """Transfer the ledger entry for ``source_id`` from ``other``."""
        if source_id in other._memory._sources:
            self._memory._sources[source_id] = other._memory._sources[source_id]

    def _dump_provenance(self, root: Path) -> None:
        """Persist the chunk source ledger alongside the KA."""
        try:
            self._memory.dump_sources(Path(root) / "sources_chunks.json")
        except Exception as e:
            logger.warning("provenance_dump_failed", error=str(e))

    def _load_provenance(self, root: Path) -> None:
        """Restore the chunk source ledger alongside the KA."""
        try:
            ledger_path = Path(root) / "sources_chunks.json"
            if ledger_path.exists():
                self._memory.load_sources(ledger_path)
        except Exception as e:
            logger.warning("provenance_load_failed", error=str(e))

    # ==================== Ingestion ====================

    def feed_text(
        self,
        text: str,
        *,
        source_id: str | None = None,
        content_hash: str | None = None,
    ) -> "AutoDocument":
        """Ingest text as chunks with document-level upsert semantics.

        When ``source_id`` was attributed before, the previous version's
        chunks are rolled back first (exact re-merge from surviving
        sources), so content removed from the updated document does not
        linger. No LLM calls are made.
        """
        logger.debug("stage=feed_text_start input_chars=%d", len(text))
        chunks = self._chunk_text(text)

        if (
            source_id
            and self._memory.track_sources
            and source_id in self._memory.sources()
        ):
            logger.info("stage=source_upsert rollback source=%s", source_id)
            self._memory.remove_source(source_id)

        if source_id:
            self._memory.record_source(
                source_id,
                [chunk.model_dump() for chunk in chunks],
                content_hash=content_hash,
            )
        self._memory.add(chunks)

        self.metadata["updated_at"] = datetime.now()
        logger.debug("stage=feed_text_complete num_chunks=%d", len(chunks))
        return self

    # ==================== Indexing & Search & Chat ====================

    def build_index(self):
        """Builds the vector index over chunk contents."""
        if not self.empty():
            self._memory.build_index()

    def has_index(self) -> bool:
        """True when a chunk index is built."""
        return self._memory.has_index()

    def dump_index(self, folder_path: str | Path) -> None:
        """Saves the chunk index to disk."""
        self._memory.dump_index(folder_path)

    def load_index(self, folder_path: str | Path) -> None:
        """Loads the chunk index from disk."""
        self._memory.load_index(folder_path)

    def search(
        self,
        query: str,
        top_k: int = 3,
        *,
        source_ids: list[str] | None = None,
        tags: list[str] | None = None,
    ) -> list[TextChunk]:
        """Semantic search over chunks.

        Args:
            query: Search query string.
            top_k: Number of results to return.
            source_ids: Optional scope — only chunks contributed by these
                source documents.
            tags: Optional scope — only chunks from sources carrying any of
                these tags.

        Returns:
            List of matching chunks ranked by similarity.
        """
        if not self.has_index():
            raise ValueError("Index not built. Call build_index() first.")
        return self._memory.search(query, top_k=top_k, source_ids=source_ids, tags=tags)

    # ==================== Source Ledger (provenance) ====================

    def sources(self) -> dict[str, dict[str, Any]]:
        """Summarize the source ledger."""
        return {
            source_id: dict(info) for source_id, info in self._memory.sources().items()
        }

    def source_content_hash(self, source_id: str) -> str | None:
        """Return the recorded content hash of a source (None if unknown)."""
        record = self._memory._sources.get(source_id)
        return record.content_hash if record else None

    def source_tags(self, source_id: str) -> list[str]:
        """Return the tags of one source (empty if unknown/untagged)."""
        return self._memory.source_tags(source_id)

    def tag_source(
        self,
        source_id: str,
        *,
        add: list[str] | None = None,
        remove: list[str] | None = None,
    ) -> list[str]:
        """Add/remove tags on one source. Returns the resulting tag list."""
        return self._memory.tag_source(source_id, add=add, remove=remove)

    def remove_source(self, source_id: str, *, strategy: str = "exact") -> dict:
        """Remove every chunk contributed by one source document.

        Chunks shared with other documents are re-merged from the surviving
        sources' raw contents. The search index is patched in place when built.
        """
        report = self._memory.remove_source(source_id, strategy=strategy)
        return {
            "source_id": source_id,
            "removed_chunks": report["removed_keys"],
            "remerged_chunks": report["remerged_keys"],
            "index_patched": report["index_patched"],
        }

    # ==================== Visualization ====================

    def show(self, *, top_k: int = 5) -> None:
        """Print a corpus summary instead of launching a graph visualization."""
        total_chars = sum(len(chunk.content) for chunk in self._memory.items)
        print(f"Document corpus: {self._memory.size} chunks, {total_chars} chars")
        print(f"Sources: {len(self.sources())}")
        for i, chunk in enumerate(list(self._memory.items)[:top_k], 1):
            preview = chunk.content[:80].replace("\n", " ")
            print(f"  [{i}] {preview}{'…' if len(chunk.content) > 80 else ''}")
        if self._memory.size > top_k:
            print(f"  … and {self._memory.size - top_k} more chunks")
