"""
M-Flow 0.3 — single bootstrap migration.

The relational schema is owned by SQLAlchemy ORM models and materialised
via ``Base.metadata.create_all`` on first startup.  This stub exists
solely to anchor the Alembic revision graph so that future incremental
migrations can reference a ``down_revision``.

Revision ID: 92b3293baa66
Revises: —
Create Date: 2026-04-02
"""

from __future__ import annotations

from typing import Sequence, Union

revision: str = "92b3293baa66"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """No-op: schema is created by the application on startup."""


def downgrade() -> None:
    """No-op: full teardown is not supported via migration."""
