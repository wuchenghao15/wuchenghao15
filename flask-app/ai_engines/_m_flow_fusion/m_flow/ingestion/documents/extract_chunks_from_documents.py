"""
Document Chunk Extraction
=========================

Utilities for splitting documents into manageable chunks
for processing through the M-flow pipeline.
"""

from __future__ import annotations

from typing import AsyncGenerator
from uuid import UUID

from sqlalchemy import select

from m_flow.data.processing.document_types.Document import Document
from m_flow.data.models import Data
from m_flow.adapters.relational import get_db_adapter
from m_flow.ingestion.chunking.TextChunker import TextChunker
from m_flow.ingestion.chunking.Chunker import Chunker
from m_flow.ingestion.documents.exceptions import (
    InvalidChunkSizeError,
    InvalidChunkerError,
)


async def update_document_token_count(document_id: UUID, token_count: int) -> None:
    """
    Update the token count for a document in the database.

    Parameters
    ----------
    document_id : UUID
        Unique identifier of the document to update.
    token_count : int
        Total number of tokens in the document.

    Raises
    ------
    ValueError
        If the document with the given ID is not found.
    """
    db = get_db_adapter()

    async with db.get_async_session() as session:
        query = select(Data).filter(Data.id == document_id)
        doc_record = (await session.execute(query)).scalar_one_or_none()

        if doc_record is None:
            raise ValueError(f"Document not found: {document_id}")

        doc_record.token_count = token_count
        await session.merge(doc_record)
        await session.commit()


async def segment_documents(
    documents: list[Document],
    max_chunk_size: int,
    chunker: Chunker = TextChunker,
) -> AsyncGenerator:
    """
    Split documents into chunks using the specified chunker.

    Iterates through each document, extracts chunks using the
    chunker's read method, and updates token counts in the database.

    Parameters
    ----------
    documents : list[Document]
        Documents to process.
    max_chunk_size : int
        Maximum size (in tokens or characters) for each chunk.
    chunker : Chunker
        Chunker class to use for splitting documents.

    Yields
    ------
    ContentFragment
        Individual chunks from each document.

    Raises
    ------
    InvalidChunkSizeError
        If max_chunk_size is not a positive integer.
    InvalidChunkerError
        If chunker is not a valid Chunker class.

    Notes
    -----
    The chunker class must implement a `read` method that accepts
    max_chunk_size and chunker_cls parameters.
    """
    # Validate chunk size
    if not isinstance(max_chunk_size, int) or max_chunk_size <= 0:
        raise InvalidChunkSizeError(max_chunk_size)

    # Validate chunker class
    if not isinstance(chunker, type) or not hasattr(chunker, "read"):
        raise InvalidChunkerError()

    # Process each document
    for doc in documents:
        total_tokens = 0

        async for chunk in doc.read(
            max_chunk_size=max_chunk_size,
            chunker_cls=chunker,
        ):
            total_tokens += chunk.chunk_size
            chunk.memory_spaces = doc.memory_spaces

            # Propagate created_at from Document to ContentFragment
            # This is the central fix point for time-aware memory processing:
            # ContentFragment.created_at will be used as anchor_time_ms in
            # _calculate_merged_time() for parsing relative time expressions
            if doc.created_at is not None:
                chunk.created_at = doc.created_at

            yield chunk

        # Persist token count
        await update_document_token_count(doc.id, total_tokens)
