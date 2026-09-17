"""
pgvector database adapter for M-flow.

Provides PostgreSQL with pgvector extension support for
vector similarity search operations.
"""

from __future__ import annotations

# Public API
from .create_db_and_tables import create_db_and_tables

__all__ = ["create_db_and_tables"]
