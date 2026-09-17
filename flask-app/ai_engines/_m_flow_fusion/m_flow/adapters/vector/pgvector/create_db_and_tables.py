"""PGVector database initialization."""

from __future__ import annotations

from sqlalchemy import text

from m_flow.adapters.vector.get_vector_adapter import (
    get_vector_provider,
    get_vectordb_context_config,
)


async def create_db_and_tables() -> None:
    """Create vector extension if using PGVector."""
    cfg = get_vectordb_context_config()
    engine = get_vector_provider()

    if cfg["vector_db_provider"] == "pgvector":
        async with engine.engine.begin() as conn:
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
