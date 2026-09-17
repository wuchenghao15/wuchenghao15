"""
Factory for the relational (SQL) database engine.
"""

from __future__ import annotations

from .config import get_relational_config
from .create_relational_engine import create_relational_engine


def get_db_adapter():
    """
    Build a relational engine using the active configuration.

    Returns
    -------
    RelationalEngineInterface
        A configured engine instance (e.g., SQLAlchemy wrapper).
    """
    cfg = get_relational_config()
    return create_relational_engine(**cfg.to_dict())
