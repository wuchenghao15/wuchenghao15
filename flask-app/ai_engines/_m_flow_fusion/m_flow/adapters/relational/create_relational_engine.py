"""
Factory for relational (SQL) database adapters.
"""

from __future__ import annotations

from functools import lru_cache

from .sqlalchemy.SqlAlchemyAdapter import SQLAlchemyAdapter

_POSTGRES_EXTRAS = (
    "PostgreSQL dependencies are not installed. Run: pip install 'm_flow[postgres]' or 'm_flow[postgres-binary]'"
)


@lru_cache(maxsize=4)
def create_relational_engine(
    db_path: str = "",
    db_name: str = "",
    db_host: str = "",
    db_port: str = "",
    db_username: str = "",
    db_password: str = "",
    db_provider: str = "sqlite",
) -> SQLAlchemyAdapter:
    """
    Instantiate the appropriate SQLAlchemy adapter.

    Parameters
    ----------
    db_path
        Filesystem path for SQLite databases.
    db_name
        Database name.
    db_host, db_port
        Host/port for networked databases.
    db_username, db_password
        Credentials for PostgreSQL.
    db_provider
        One of ``"sqlite"`` or ``"postgres"``.

    Returns
    -------
    SQLAlchemyAdapter
        Configured adapter instance.
    """
    conn = _build_connection_string(
        provider=db_provider,
        path=db_path,
        name=db_name,
        host=db_host,
        port=db_port,
        user=db_username,
        passwd=db_password,
    )
    return SQLAlchemyAdapter(conn)


def _build_connection_string(
    provider: str,
    path: str,
    name: str,
    host: str,
    port: str,
    user: str,
    passwd: str,
) -> str:
    """Create a SQLAlchemy async connection string."""
    prov = provider.lower()

    if prov == "sqlite":
        return f"sqlite+aiosqlite:///{path}/{name}"

    if prov in ("postgres", "postgresql"):
        try:
            import asyncpg  # noqa: F401
        except ImportError as exc:
            raise ImportError(_POSTGRES_EXTRAS) from exc
        return f"postgresql+asyncpg://{user}:{passwd}@{host}:{port}/{name}"

    raise ValueError(f"Unsupported db_provider: {provider}")
