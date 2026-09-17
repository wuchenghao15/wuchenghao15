"""Relational store configuration for M-Flow.

Provides Pydantic-settings models for the primary application database
and for schema-migration connections.  Both flavours (SQLite / PostgreSQL)
are supported; the active provider is selected via ``db_provider``.

Environment variables are loaded from ``.env`` automatically.
"""

from __future__ import annotations

import os
from functools import lru_cache
from typing import Any, Dict, Optional

import pydantic
from pydantic_settings import BaseSettings
from m_flow.config.env_compat import MflowSettings, SettingsConfigDict

from m_flow.base_config import get_base_config

_FIELD_NAMES_MAIN = (
    "db_path",
    "db_name",
    "db_host",
    "db_port",
    "db_username",
    "db_password",
    "db_provider",
)

_FIELD_NAMES_MIGRATION = (
    "migration_db_path",
    "migration_db_name",
    "migration_db_host",
    "migration_db_port",
    "migration_db_username",
    "migration_db_password",
    "migration_db_provider",
)


class RelationalConfig(MflowSettings):
    """Primary relational-database connection parameters.

    Defaults to an SQLite backend stored under the M-Flow system root.
    Set ``db_provider`` to ``"postgresql"`` and fill in the host / port /
    credential fields to switch to PostgreSQL.
    """

    db_path: str = ""
    db_name: str = "mflow_store"
    db_host: Optional[str] = None
    db_port: Optional[str] = None
    db_username: Optional[str] = None
    db_password: Optional[str] = None
    db_provider: str = "sqlite"

    model_config = SettingsConfigDict(env_prefix="MFLOW_", env_file=".env", extra="allow")

    @pydantic.model_validator(mode="after")
    def _set_default_path(self) -> "RelationalConfig":
        """Fall back to ``<system_root>/databases`` when no path given."""
        if not self.db_path:
            root_dir = get_base_config().system_root_directory
            self.db_path = os.path.join(root_dir, "databases")
        return self

    def to_dict(self) -> Dict[str, Any]:
        """Serialise the configuration into a plain mapping."""
        return {attr: getattr(self, attr) for attr in _FIELD_NAMES_MAIN}


@lru_cache(maxsize=1)
def get_relational_config() -> RelationalConfig:
    """Return the cached application-database configuration singleton."""
    return RelationalConfig()


class MigrationConfig(MflowSettings):
    """Connection parameters used exclusively by schema migrations.

    Every field mirrors its ``RelationalConfig`` counterpart but is
    prefixed with ``migration_`` so that a dedicated migration database
    can be targeted independently of the runtime store.
    """

    migration_db_path: Optional[str] = None
    migration_db_name: Optional[str] = None
    migration_db_host: Optional[str] = None
    migration_db_port: Optional[str] = None
    migration_db_username: Optional[str] = None
    migration_db_password: Optional[str] = None
    migration_db_provider: Optional[str] = None

    model_config = SettingsConfigDict(env_prefix="MFLOW_", env_file=".env", extra="allow")

    def to_dict(self) -> Dict[str, Any]:
        """Serialise the migration configuration into a plain mapping."""
        return {attr: getattr(self, attr) for attr in _FIELD_NAMES_MIGRATION}


@lru_cache(maxsize=1)
def get_migration_config() -> MigrationConfig:
    """Return the cached migration-database configuration singleton."""
    return MigrationConfig()
