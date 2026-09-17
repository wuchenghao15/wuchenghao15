"""Factory that wires the migration-specific DB engine from config."""

from __future__ import annotations

import logging

from .config import get_migration_config
from .create_relational_engine import create_relational_engine

_logger = logging.getLogger(__name__)


def get_migration_relational_engine():
    """Instantiate a relational engine configured for schema migrations.

    Reads connection coordinates from the migration configuration
    (provider, host, port, credentials, database name and path) and
    returns a ready-to-use engine instance.  No connection is opened
    until the caller actually executes a statement.

    Returns
    -------
    RelationalEngine
        A lazily-connected engine bound to the migration database.
    """
    migration_settings = get_migration_config()

    _logger.debug(
        "mflow.migration.engine provider=%s host=%s db=%s",
        migration_settings.migration_db_provider,
        migration_settings.migration_db_host,
        migration_settings.migration_db_name,
    )

    return create_relational_engine(
        db_path=migration_settings.migration_db_path,
        db_name=migration_settings.migration_db_name,
        db_host=migration_settings.migration_db_host,
        db_port=migration_settings.migration_db_port,
        db_username=migration_settings.migration_db_username,
        db_password=migration_settings.migration_db_password,
        db_provider=migration_settings.migration_db_provider,
    )
