#!/usr/bin/env python3
"""
Migration script to fix created_at timestamps in LanceDB vector database.

Problem:
- Kuzu graph database has correct historical created_at (already migrated)
- LanceDB Episode_summary.payload.created_at still has ingestion time (incorrect)

Solution:
1. Read correct created_at from Kuzu Episode nodes
2. Update LanceDB Episode_summary payload with correct created_at

Usage:
    python migrate_lancedb_created_at.py --dry-run  # Preview changes
    python migrate_lancedb_created_at.py            # Apply changes
"""

import argparse
import asyncio
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent.parent))

from m_flow.shared.logging_utils import get_logger

_log = get_logger()


def _datetime_to_ms(dt: datetime) -> int:
    """Convert datetime to millisecond timestamp."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return int(dt.timestamp() * 1000)


async def get_episode_created_at_from_kuzu(engine) -> dict:
    """
    Get all Episode IDs and their correct created_at from Kuzu.

    Returns:
        dict mapping episode_id -> created_at_ms
    """
    cypher = """
    MATCH (ep:Node {type: 'Episode'})
    RETURN ep.id, ep.created_at
    """

    results = await engine.query(cypher, {})

    episode_times = {}
    for ep_id, created_at in results:
        if created_at is not None:
            if isinstance(created_at, datetime):
                episode_times[ep_id] = _datetime_to_ms(created_at)
            else:
                episode_times[ep_id] = created_at

    return episode_times


async def migrate_lancedb_episode_summary(
    dataset_id: str, user_id: str, episode_times: dict, dry_run: bool = True
) -> dict:
    """
    Migrate Episode_summary payload.created_at in LanceDB.

    Args:
        dataset_id: Dataset ID
        user_id: User ID (owner)
        episode_times: dict mapping episode_id -> correct created_at_ms (from Kuzu)
        dry_run: If True, only preview changes

    Returns:
        dict with migration statistics
    """
    import lancedb

    from m_flow.base_config import get_base_config

    stats = {"total": 0, "updated": 0, "skipped": 0, "errors": 0}

    # Get LanceDB path from config
    root = get_base_config().system_root_directory
    db_root = Path(root) / "databases" / user_id
    db_path = db_root / f"{dataset_id}.lance.db"

    if not db_path.exists():
        _log.warning(f"LanceDB path not found: {db_path}")
        return stats

    db = lancedb.connect(str(db_path))

    table_names = db.table_names()
    if "Episode_summary" not in table_names:
        _log.warning(f"Episode_summary table not found in {dataset_id}")
        return stats

    table = db.open_table("Episode_summary")
    df = table.to_pandas()
    stats["total"] = len(df)

    if stats["total"] == 0:
        return stats

    updated_rows = []

    for idx, row in df.iterrows():
        ep_id = row["id"]

        if ep_id not in episode_times:
            _log.debug(f"Episode {ep_id}: not found in Kuzu, skipping")
            stats["skipped"] += 1
            continue

        correct_created_at = episode_times[ep_id]

        # Parse payload
        payload = row.get("payload")
        if payload is None:
            stats["skipped"] += 1
            continue

        if isinstance(payload, str):
            try:
                payload = json.loads(payload)
            except json.JSONDecodeError:
                stats["errors"] += 1
                continue

        current_created_at = payload.get("created_at")

        if current_created_at == correct_created_at:
            _log.debug(f"Episode {ep_id}: already correct, skipping")
            stats["skipped"] += 1
            continue

        # Update payload
        payload["created_at"] = correct_created_at

        if dry_run:
            old_time = (
                datetime.fromtimestamp(current_created_at / 1000, tz=timezone.utc) if current_created_at else "None"
            )
            new_time = datetime.fromtimestamp(correct_created_at / 1000, tz=timezone.utc)
            _log.info(
                f"[DRY-RUN] Episode {ep_id[:8]}...: {old_time.year if hasattr(old_time, 'year') else old_time} -> {new_time.year}"
            )
            stats["updated"] += 1
        else:
            # Build updated row
            updated_row = {
                "id": row["id"],
                "vector": row["vector"],
                "payload": payload,
            }
            updated_rows.append(updated_row)
            stats["updated"] += 1

    # Apply updates
    if not dry_run and updated_rows:
        try:
            # Use merge_insert for upsert
            table.merge_insert("id").when_matched_update_all().when_not_matched_insert_all().execute(updated_rows)
            _log.info(f"Updated {len(updated_rows)} Episode_summary records")
        except Exception as e:
            _log.error(f"Failed to update Episode_summary: {e}")
            stats["errors"] += len(updated_rows)
            stats["updated"] = 0

    return stats


async def migrate_single_dataset(dataset_id: str, user_id: str, dry_run: bool = True) -> dict:
    """Migrate a single dataset's LanceDB."""
    from uuid import UUID
    from m_flow.context_global_variables import set_db_context
    from m_flow.adapters.graph.get_graph_provider import get_graph_provider

    _log.info(f"Processing dataset {dataset_id}...")

    await set_db_context(UUID(dataset_id), UUID(user_id))
    engine = await get_graph_provider()

    # Get correct created_at from Kuzu
    episode_times = await get_episode_created_at_from_kuzu(engine)
    _log.info(f"Found {len(episode_times)} Episodes in Kuzu")

    if not episode_times:
        return {"total": 0, "updated": 0, "skipped": 0, "errors": 0}

    # Migrate LanceDB
    stats = await migrate_lancedb_episode_summary(dataset_id, user_id, episode_times, dry_run)

    return stats


async def run_migration(dry_run: bool = True):
    """Run the full migration across all datasets."""
    from m_flow.auth.methods import get_seed_user
    from m_flow.auth.permissions.methods import get_all_user_permission_datasets
    from m_flow.context_global_variables import backend_access_control_enabled

    _log.info(f"Starting LanceDB migration (dry_run={dry_run})")
    _log.info("=" * 60)

    all_stats = {
        "datasets_processed": 0,
        "total_updated": 0,
        "total_skipped": 0,
        "total_errors": 0,
    }

    if backend_access_control_enabled():
        default_user = await get_seed_user()
        datasets = await get_all_user_permission_datasets(default_user, "read")

        _log.info(f"Found {len(datasets)} datasets to migrate")

        for dataset in datasets:
            try:
                result = await migrate_single_dataset(str(dataset.id), str(dataset.owner_id), dry_run)

                all_stats["datasets_processed"] += 1
                all_stats["total_updated"] += result.get("updated", 0)
                all_stats["total_skipped"] += result.get("skipped", 0)
                all_stats["total_errors"] += result.get("errors", 0)

                _log.info(
                    f"Dataset {dataset.id}: updated={result.get('updated', 0)}, skipped={result.get('skipped', 0)}"
                )

            except Exception as e:
                _log.error(f"Failed to migrate dataset {dataset.id}: {e}")
                all_stats["total_errors"] += 1
    else:
        _log.error("This script requires backend_access_control to be enabled")
        return all_stats

    _log.info("=" * 60)
    _log.info("Migration Summary")
    _log.info("=" * 60)
    _log.info(f"Datasets processed: {all_stats['datasets_processed']}")
    _log.info(f"Episodes updated: {all_stats['total_updated']}")
    _log.info(f"Episodes skipped: {all_stats['total_skipped']}")
    _log.info(f"Errors: {all_stats['total_errors']}")

    if dry_run:
        _log.info("DRY RUN completed. Run without --dry-run to apply changes.")
    else:
        _log.info("Migration completed.")

    return all_stats


def main():
    parser = argparse.ArgumentParser(description="Migrate created_at timestamps in LanceDB vector database")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without applying")
    args = parser.parse_args()

    asyncio.run(run_migration(dry_run=args.dry_run))


if __name__ == "__main__":
    main()
