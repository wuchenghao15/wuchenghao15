"""
System Pruning Module
=====================

Utilities for clearing all data from M-flow's storage backends.
This is a destructive operation intended for development and testing.

WARNING: These functions delete data without permission checks.
Do not expose through production APIs.
"""

from __future__ import annotations

import os
import shutil
import re

from sqlalchemy.exc import OperationalError

from m_flow.adapters.exceptions import ConceptNotFoundError
from m_flow.context_global_variables import backend_access_control_enabled
from m_flow.adapters.vector import get_vector_provider
from m_flow.adapters.graph.get_graph_adapter import get_graph_provider
from m_flow.adapters.relational import get_db_adapter
from m_flow.adapters.utils import (
    get_graph_dataset_database_handler,
    get_vector_dataset_database_handler,
)
from m_flow.shared.cache import delete_cache
from m_flow.shared.logging_utils import get_logger
from m_flow.base_config import get_base_config

_logger = get_logger(__name__)

# UUID pattern for memory space directories
_UUID_PATTERN = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.IGNORECASE)


async def prune_graph_databases() -> None:
    """
    Remove all graph data from dataset-specific databases.

    Iterates through all registered datasets and clears their
    associated graph storage.
    """
    db = get_db_adapter()

    try:
        all_datasets = await db.get_all_data_from_table("dataset_database")
        deleted_count = 0

        for dataset_record in all_datasets:
            try:
                handler_info = get_graph_dataset_database_handler(dataset_record)
                await handler_info["handler_instance"].delete_dataset(dataset_record)
                deleted_count += 1
            except Exception as e:
                _logger.debug(
                    "Failed to delete dataset graph %s: %s",
                    dataset_record.id if hasattr(dataset_record, "id") else "unknown",
                    e,
                )

        if deleted_count > 0:
            _logger.info(
                "[prune] Deleted %d dataset-specific graph databases",
                deleted_count,
            )

    except (OperationalError, ConceptNotFoundError) as err:
        _logger.debug(
            "Graph DB pruning skipped due to dataset_database access error: %s",
            err,
        )


async def prune_vector_databases() -> None:
    """
    Remove all vector data from dataset-specific databases.

    Iterates through all registered datasets and clears their
    associated vector storage.
    """
    db = get_db_adapter()

    try:
        all_datasets = await db.get_all_data_from_table("dataset_database")
        deleted_count = 0

        for dataset_record in all_datasets:
            try:
                handler_info = get_vector_dataset_database_handler(dataset_record)
                await handler_info["handler_instance"].delete_dataset(dataset_record)
                deleted_count += 1
            except Exception as e:
                _logger.debug(
                    "Failed to delete dataset vector %s: %s",
                    dataset_record.id if hasattr(dataset_record, "id") else "unknown",
                    e,
                )

        if deleted_count > 0:
            _logger.info(
                "[prune] Deleted %d dataset-specific vector databases",
                deleted_count,
            )

    except (OperationalError, ConceptNotFoundError) as err:
        _logger.debug(
            "Vector DB pruning skipped due to dataset_database access error: %s",
            err,
        )


async def prune_orphan_database_directories() -> None:
    """
    Remove orphan memory space directories from the file system.

    Scans the databases directory and removes any UUID-named directories
    that are not registered in the relational database. This handles
    cases where directories were created but their database records
    were lost or never created.

    Only removes directories matching UUID pattern to avoid accidentally
    deleting other files.
    """
    base_cfg = get_base_config()
    db_dir = os.path.join(base_cfg.system_root_directory, "databases")

    if not os.path.exists(db_dir):
        return

    # Get registered owner IDs from relational database
    registered_owner_ids: set[str] = set()
    try:
        db = get_db_adapter()
        all_datasets = await db.get_all_data_from_table("dataset_database")
        for record in all_datasets:
            if hasattr(record, "owner_id") and record.owner_id:
                registered_owner_ids.add(str(record.owner_id))
    except Exception as e:
        _logger.debug("[prune] Could not query dataset_database for orphan cleanup: %s", e)
        # If we can't query the database, assume all UUID directories are orphans
        # This is safe because prune.all() is a complete cleanup operation

    deleted_count = 0
    for item in os.listdir(db_dir):
        item_path = os.path.join(db_dir, item)

        # Only process directories matching UUID pattern
        if not os.path.isdir(item_path):
            continue
        if not _UUID_PATTERN.match(item):
            continue

        # Skip if this owner_id is registered (when we have database access)
        if registered_owner_ids and item in registered_owner_ids:
            continue

        # Remove the orphan directory
        try:
            shutil.rmtree(item_path)
            deleted_count += 1
            _logger.debug("[prune] Removed orphan directory: %s", item)
        except Exception as e:
            _logger.warning("[prune] Failed to remove orphan directory %s: %s", item, e)

    if deleted_count > 0:
        _logger.info("[prune] Removed %d orphan memory space directories", deleted_count)


async def prune_system(
    graph: bool = True,
    vector: bool = True,
    metadata: bool = True,
    cache: bool = True,
) -> None:
    """
    Clear all data from the M-flow system.

    This is a destructive operation that removes all stored data.
    Use only in development or testing environments.

    Parameters
    ----------
    graph : bool
        Clear graph database contents.
    vector : bool
        Clear vector database contents.
    metadata : bool
        Clear relational database contents.
    cache : bool
        Clear cached data.

    WARNING
    -------
    This function bypasses all permission checks and will delete
    ALL data if called. Never expose through production APIs.

    Implementation Note
    -------------------
    Due to a known issue where data may be written to the global database
    even when backend_access_control is enabled (if context variables are
    not properly set), we ALWAYS clear both:
    1. The global database (ensures CLI/script usage is cleaned)
    2. Dataset-specific databases (if access control is enabled)

    This ensures complete cleanup regardless of how data was ingested.
    """
    # Clear graph storage
    if graph:
        # ALWAYS clear the global graph database first
        # This is critical because data may be written to the global DB
        # even when backend_access_control is enabled (e.g., CLI usage
        # where context variables are not set)
        try:
            graph_db = await get_graph_provider()
            await graph_db.delete_graph()
            _logger.info("[prune] Global graph database cleared")
        except Exception as e:
            _logger.debug("[prune] Global graph DB cleanup skipped: %s", e)

        # Additionally clear dataset-specific databases if access control is enabled
        if backend_access_control_enabled():
            await prune_graph_databases()

    # Clear vector storage
    if vector:
        # ALWAYS clear the global vector database first (same reasoning as graph)
        try:
            vector_db = get_vector_provider()
            await vector_db.prune()
            _logger.info("[prune] Global vector database cleared")
        except Exception as e:
            _logger.debug("[prune] Global vector DB cleanup skipped: %s", e)

        # Additionally clear dataset-specific databases if access control is enabled
        if backend_access_control_enabled():
            await prune_vector_databases()

    # Clear relational storage
    if metadata:
        db = get_db_adapter()
        await db.delete_database()
        _logger.info("[prune] Relational database cleared")

    # Clear cache
    if cache:
        await delete_cache()
        _logger.info("[prune] Cache cleared")

    # Clean up orphan memory space directories
    # This should run after metadata cleanup to ensure we don't delete
    # directories that are still registered
    await prune_orphan_database_directories()
