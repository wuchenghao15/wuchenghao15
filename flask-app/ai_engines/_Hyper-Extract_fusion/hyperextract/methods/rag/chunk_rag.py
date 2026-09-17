"""Chunk RAG - baseline retrieval over raw text chunks.

The baseline retrieval method: documents are chunked and embedded as-is;
retrieval returns the raw chunks without any LLM structuring. Useful as a
reference point for graph-based methods, for quick corpora, or when
extraction cost/quality is a concern.
"""

from hyperextract.types.document import AutoDocument
from hyperextract.utils.logging import get_logger

logger = get_logger(__name__)


class Chunk_RAG(AutoDocument):
    """Chunk_RAG - chunk-level retrieval without knowledge extraction.

    Inherits the full AutoDocument pipeline: local chunking (no LLM calls
    at ingestion), content-hash dedup, source ledger with per-document
    rollback and tags, and scoped semantic search.
    """
