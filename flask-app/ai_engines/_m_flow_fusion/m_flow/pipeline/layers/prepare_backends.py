"""
Environment setup and validation.

Initializes databases and validates LLM connections on first run.
"""

from __future__ import annotations

import asyncio

from m_flow.adapters.relational import create_db_and_tables as init_relational
from m_flow.adapters.vector.pgvector import create_db_and_tables as init_pgvector
from m_flow.context_global_variables import (
    graph_db_config as ctx_graph,
    vector_db_config as ctx_vector,
)

# One-time setup tracking
_initialized = False
_init_lock = asyncio.Lock()


async def prepare_backends(
    vector_db_config: dict = None,
    graph_db_config: dict = None,
) -> None:
    """
    Initialize environment for pipeline execution.

    Sets database configs, creates tables, and validates
    LLM connections on first invocation.

    Args:
        vector_db_config: Vector DB settings.
        graph_db_config: Graph DB settings.
    """
    # Apply configs
    if vector_db_config:
        ctx_vector.set(vector_db_config)
    if graph_db_config:
        ctx_graph.set(graph_db_config)

    # Initialize databases
    await init_relational()
    await init_pgvector()

    # First-run validations
    await _run_first_time_checks()


async def _run_first_time_checks() -> None:
    """Validate LLM connections once."""
    global _initialized

    async with _init_lock:
        if _initialized:
            return

        from m_flow.llm.utils import test_embedding_connection, test_llm_connection

        await test_llm_connection()
        await test_embedding_connection()

        _initialized = True
