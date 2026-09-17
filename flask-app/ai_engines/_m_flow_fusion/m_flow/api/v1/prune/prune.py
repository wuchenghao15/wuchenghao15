"""
System Pruning API
==================

Provides a clean interface for data and system cleanup operations.
These are administrative functions for development and testing.

WARNING: These operations are destructive and irreversible.
"""

from __future__ import annotations

import warnings

from m_flow.data.deletion import prune_data as _do_prune_data
from m_flow.data.deletion import prune_system as _do_prune_system
from m_flow.shared.logging_utils import get_logger

_logger = get_logger(__name__)


class prune:
    """
    Administrative cleanup operations.

    Provides static methods for clearing data and system state.
    Use with caution as these operations are destructive.

    Recommended Usage
    -----------------
    For complete cleanup, use :meth:`all` instead of calling
    :meth:`prune_data` and :meth:`prune_system` separately.

    Example
    -------
    >>> await m_flow.prune.all()  # Recommended: clears everything
    """

    @staticmethod
    async def all() -> None:
        """
        Clear all data completely (recommended for development/testing).

        This method performs a complete cleanup of all M-flow data:

        - File storage (.data_storage)
        - Relational database (Data, Dataset, ACL tables)
        - Graph database (all nodes and edges)
        - Vector database (all indices)
        - Cache

        Warnings
        --------
        - This operation is **irreversible**!
        - Clears **all** datasets (no per-dataset selection)
        - Not atomic: if interrupted, run ``maintenance.check_orphans()``
        - For development/testing only; not recommended for production

        Concurrency
        -----------
        - Do not call concurrently with ``add()`` or ``memorize()``
        - Do not call from multiple processes simultaneously

        Example
        -------
        >>> await m_flow.prune.all()

        Raises
        ------
        Exception
            If any cleanup step fails. Check logs for details.
        """
        _logger.info("[prune.all] Starting complete data cleanup...")

        try:
            # Step 1: Clear file storage
            await _do_prune_data()
            _logger.info("[prune.all] File storage cleared")

            # Step 2: Clear all databases (including metadata!)
            await _do_prune_system(
                graph=True,
                vector=True,
                metadata=True,  # Critical: must be True to avoid orphan records
                cache=True,
            )
            _logger.info("[prune.all] All databases and caches cleared")
            _logger.info("[prune.all] Complete data cleanup finished successfully")

        except Exception as e:
            _logger.error(
                f"[prune.all] Failed during cleanup: {e}. "
                "Data may be in an inconsistent state. "
                "Run `await m_flow.maintenance.check_orphans()` to verify."
            )
            raise

    @staticmethod
    async def prune_data() -> None:
        """
        Clear all stored data files.

        Removes uploaded documents and processed data from file storage.

        Note
        ----
        If you need complete cleanup, use :meth:`all` instead.
        This method alone does not clear database records.
        """
        await _do_prune_data()

    @staticmethod
    async def prune_system(
        graph: bool = True,
        vector: bool = True,
        metadata: bool = False,
        cache: bool = True,
    ) -> None:
        """
        Clear system databases and caches.

        Parameters
        ----------
        graph : bool
            Clear graph database contents.
        vector : bool
            Clear vector database contents.
        metadata : bool
            Clear relational database. Default is False for backward
            compatibility, but this may cause data inconsistency if
            :meth:`prune_data` was called without clearing metadata.
        cache : bool
            Clear cached data.

        Warnings
        --------
        Using ``metadata=False`` (the default) after calling
        :meth:`prune_data` will leave orphan records in the relational
        database, causing ``FileNotFoundError`` during subsequent
        ingestion.

        Recommendation
        --------------
        Use :meth:`all` for complete cleanup, or explicitly set
        ``metadata=True`` if you intend to clear everything.

        Example
        -------
        >>> # Complete cleanup (preferred)
        >>> await m_flow.prune.all()

        >>> # Manual cleanup (must set metadata=True!)
        >>> await m_flow.prune.prune_data()
        >>> await m_flow.prune.prune_system(metadata=True)
        """
        # Warn if metadata=False (the problematic default)
        if not metadata:
            msg = (
                "prune_system(metadata=False) may leave orphan records in the "
                "relational database if prune_data() was called. This can cause "
                "FileNotFoundError during subsequent ingestion. "
                "Consider using `await m_flow.prune.all()` for complete cleanup, "
                "or set `metadata=True` explicitly."
            )
            warnings.warn(msg, UserWarning, stacklevel=2)
            _logger.warning(f"[prune.prune_system] {msg}")

        await _do_prune_system(
            graph=graph,
            vector=vector,
            metadata=metadata,
            cache=cache,
        )


if __name__ == "__main__":
    import asyncio

    async def _run_cleanup() -> None:
        """Execute full system cleanup using the recommended method."""
        await prune.all()

    asyncio.run(_run_cleanup())
