"""
Database bootstrapping for the m_flow persistence layer.

Initialises both the relational store (used for metadata and
configuration) and the PGVector store (used for embedding-based
similarity search).  Can also be invoked directly from the
command line for one-off environment provisioning::

    python -m m_flow.core.domain.operations.setup
"""

from __future__ import annotations

import asyncio
import logging
from typing import Sequence, Tuple

from m_flow.adapters.relational import (
    create_db_and_tables as init_relational_db,
)
from m_flow.adapters.vector.pgvector import (
    create_db_and_tables as init_pgvector_db,
)

_log = logging.getLogger(__name__)

# Ordered list of (label, coroutine-factory) pairs so that new stores
# can be added without touching the orchestration logic.
_INIT_STEPS: Sequence[Tuple[str, object]] = [
    ("relational", init_relational_db),
    ("pgvector", init_pgvector_db),
]


async def setup() -> None:
    """Provision every configured data store.

    Iterates through ``_INIT_STEPS`` in declaration order, calling each
    asynchronous factory.  A log line is emitted after each store is
    ready so that operators can trace bootstrap progress.
    """
    for store_label, initialiser in _INIT_STEPS:
        _log.debug("Initialising %s store …", store_label)
        await initialiser()
        _log.debug("%s store ready.", store_label)


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    asyncio.run(setup())
