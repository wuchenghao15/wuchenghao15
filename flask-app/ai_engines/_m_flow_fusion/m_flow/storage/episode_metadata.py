# m_flow/storage/episode_metadata.py
"""
Episode Metadata Storage

Stores episode-level metadata that cannot be stored as node properties
in Kuzu (which doesn't support dynamic property addition).

Uses SQLite for simplicity and reliability.

Features:
- Lazy initialization (database created on first access)
- WAL mode for concurrent access safety
- Thread-safe operations
"""

from __future__ import annotations

import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from m_flow.shared.logging_utils import get_logger

logger = get_logger("episode_metadata")

_METADATA_DB_FILENAME = "episode_metadata.db"

# Thread-local storage for connections
_local = threading.local()
_db_initialized = False
_init_lock = threading.Lock()


def _get_db_path() -> Path:
    """Get the absolute path to the metadata database.

    Derives the path from BaseConfig.system_root_directory so that it
    respects the SYSTEM_ROOT_DIRECTORY environment variable, consistent
    with how relational, graph, and vector databases resolve their paths.
    """
    from m_flow.base_config import get_base_config

    return Path(get_base_config().system_root_directory) / "databases" / _METADATA_DB_FILENAME


def _ensure_db() -> None:
    """
    Lazy initialization of the metadata database.

    Thread-safe: uses lock to prevent race conditions during initialization.
    """
    global _db_initialized

    if _db_initialized:
        return

    with _init_lock:
        # Double-check after acquiring lock
        if _db_initialized:
            return

        db_path = _get_db_path()
        db_path.parent.mkdir(parents=True, exist_ok=True)

        conn = sqlite3.connect(str(db_path))
        try:
            # Enable WAL mode for better concurrent access
            conn.execute("PRAGMA journal_mode=WAL;")

            # Create the thresholds table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS episode_thresholds (
                    episode_id TEXT PRIMARY KEY,
                    adapted_threshold INTEGER NOT NULL,
                    last_check_time TEXT,
                    check_count INTEGER DEFAULT 0
                )
            """)

            # Create index for faster lookups
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_episode_thresholds_id 
                ON episode_thresholds(episode_id)
            """)

            conn.commit()
            logger.debug(f"[episode_metadata] Database initialized at {db_path}")
        finally:
            conn.close()

        _db_initialized = True


def _get_connection() -> sqlite3.Connection:
    """
    Get a thread-local database connection.

    Each thread gets its own connection for thread safety.
    """
    _ensure_db()

    if not hasattr(_local, "connection") or _local.connection is None:
        db_path = _get_db_path()
        _local.connection = sqlite3.connect(str(db_path), timeout=30.0)
        # Enable WAL mode for this connection too
        _local.connection.execute("PRAGMA journal_mode=WAL;")

    return _local.connection


def get_adapted_threshold(episode_id: str) -> Optional[int]:
    """
    Get the adapted threshold for an episode.

    Args:
        episode_id: The unique identifier of the episode

    Returns:
        The adapted threshold value, or None if not set
    """
    try:
        conn = _get_connection()
        cursor = conn.execute("SELECT adapted_threshold FROM episode_thresholds WHERE episode_id = ?", (episode_id,))
        row = cursor.fetchone()
        return row[0] if row else None
    except Exception as e:
        logger.warning(f"[episode_metadata] Failed to get threshold for {episode_id}: {e}")
        return None


def set_adapted_threshold(episode_id: str, threshold: int) -> bool:
    """
    Set the adapted threshold for an episode.

    Uses INSERT OR REPLACE to handle both new and existing records.
    Increments check_count on each update.

    Args:
        episode_id: The unique identifier of the episode
        threshold: The new threshold value

    Returns:
        True if successful, False otherwise
    """
    try:
        conn = _get_connection()

        # Get current check_count if exists
        cursor = conn.execute("SELECT check_count FROM episode_thresholds WHERE episode_id = ?", (episode_id,))
        row = cursor.fetchone()
        current_count = row[0] if row else 0

        # Insert or replace with incremented count
        conn.execute(
            """
            INSERT OR REPLACE INTO episode_thresholds 
            (episode_id, adapted_threshold, last_check_time, check_count)
            VALUES (?, ?, ?, ?)
            """,
            (
                episode_id,
                threshold,
                datetime.now(timezone.utc).replace(tzinfo=None).isoformat(),
                current_count + 1,
            ),
        )
        conn.commit()

        logger.debug(
            f"[episode_metadata] Set threshold for {episode_id}: {threshold} (check_count: {current_count + 1})"
        )
        return True
    except Exception as e:
        logger.error(f"[episode_metadata] Failed to set threshold for {episode_id}: {e}")
        return False


def delete_threshold(episode_id: str) -> bool:
    """
    Delete the threshold record for an episode.

    Called when an episode is deleted or split.

    Args:
        episode_id: The unique identifier of the episode

    Returns:
        True if successful (or record didn't exist), False on error
    """
    try:
        conn = _get_connection()
        conn.execute("DELETE FROM episode_thresholds WHERE episode_id = ?", (episode_id,))
        conn.commit()
        logger.debug(f"[episode_metadata] Deleted threshold for {episode_id}")
        return True
    except Exception as e:
        logger.error(f"[episode_metadata] Failed to delete threshold for {episode_id}: {e}")
        return False


def get_all_thresholds() -> dict[str, int]:
    """
    Get all episode thresholds.

    Useful for debugging and bulk operations.

    Returns:
        Dictionary mapping episode_id to threshold value
    """
    try:
        conn = _get_connection()
        cursor = conn.execute("SELECT episode_id, adapted_threshold FROM episode_thresholds")
        return {row[0]: row[1] for row in cursor.fetchall()}
    except Exception as e:
        logger.error(f"[episode_metadata] Failed to get all thresholds: {e}")
        return {}


def clear_all_thresholds() -> bool:
    """
    Clear all threshold records.

    Used for testing or data reset.

    Returns:
        True if successful, False otherwise
    """
    try:
        conn = _get_connection()
        conn.execute("DELETE FROM episode_thresholds")
        conn.commit()
        logger.info("[episode_metadata] Cleared all thresholds")
        return True
    except Exception as e:
        logger.error(f"[episode_metadata] Failed to clear thresholds: {e}")
        return False


def close_connection() -> None:
    """
    Close the thread-local database connection.

    Should be called when a thread is done with database operations.
    """
    if hasattr(_local, "connection") and _local.connection is not None:
        try:
            _local.connection.close()
        except Exception:
            pass
        _local.connection = None
