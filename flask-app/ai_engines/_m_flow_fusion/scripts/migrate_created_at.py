#!/usr/bin/env python3
"""
Migration script to fix created_at timestamps in Kuzu graph database.

This script:
1. Reads correct created_at from ContentFragment.properties JSON
2. Updates ContentFragment.created_at column with the correct value
3. Infers Episode.created_at from linked ContentFragments (earliest fragment time)
4. Updates Episode.created_at column

Usage:
    python migrate_created_at.py --dry-run  # Preview changes without applying
    python migrate_created_at.py            # Apply changes
"""

import argparse
import asyncio
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent.parent))

from m_flow.shared.logging_utils import get_logger

_log = get_logger()


def _ms_to_utc_str(ms_timestamp: int) -> str:
    """Convert millisecond timestamp to UTC datetime string for Kuzu."""
    dt = datetime.fromtimestamp(ms_timestamp / 1000, tz=timezone.utc)
    return dt.strftime("%Y-%m-%d %H:%M:%S.%f")


def _datetime_to_ms(dt: datetime) -> int:
    """Convert datetime to millisecond timestamp."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return int(dt.timestamp() * 1000)


async def migrate_content_fragments(engine, dry_run: bool = True) -> dict:
    """
    Migrate ContentFragment nodes: copy created_at from properties JSON to column.

    Returns:
        dict with migration statistics
    """
    stats = {"total": 0, "updated": 0, "skipped": 0, "errors": 0}

    cypher = """
    MATCH (n:Node {type: 'ContentFragment'})
    RETURN n.id, n.properties, n.created_at
    """

    try:
        results = await engine.query(cypher, {})
        stats["total"] = len(results)

        for row in results:
            node_id, props_raw, col_created_at = row

            try:
                props = json.loads(props_raw) if props_raw else {}
            except (json.JSONDecodeError, TypeError):
                props = {}

            props_created_at = props.get("created_at")

            if props_created_at is None:
                _log.debug(f"ContentFragment {node_id}: no created_at in properties, skipping")
                stats["skipped"] += 1
                continue

            col_created_at_ms = None
            if col_created_at is not None:
                if isinstance(col_created_at, datetime):
                    col_created_at_ms = _datetime_to_ms(col_created_at)
                else:
                    col_created_at_ms = col_created_at

            if col_created_at_ms == props_created_at:
                _log.debug(f"ContentFragment {node_id}: already correct, skipping")
                stats["skipped"] += 1
                continue

            new_created_at_str = _ms_to_utc_str(props_created_at)

            if dry_run:
                old_time = (
                    datetime.fromtimestamp(col_created_at_ms / 1000, tz=timezone.utc) if col_created_at_ms else "None"
                )
                new_time = datetime.fromtimestamp(props_created_at / 1000, tz=timezone.utc)
                _log.info(f"[DRY-RUN] ContentFragment {node_id[:8]}...: {old_time} -> {new_time}")
                stats["updated"] += 1
            else:
                update_cypher = """
                MATCH (n:Node {id: $id})
                SET n.created_at = timestamp($ts)
                """
                try:
                    await engine.query(update_cypher, {"id": node_id, "ts": new_created_at_str})
                    stats["updated"] += 1
                except Exception as e:
                    _log.error(f"Failed to update ContentFragment {node_id}: {e}")
                    stats["errors"] += 1

    except Exception as e:
        _log.error(f"Failed to query ContentFragments: {e}")
        raise

    return stats


async def migrate_episodes(engine, dry_run: bool = True) -> dict:
    """
    Migrate Episode nodes: infer created_at from linked ContentFragments.

    For each Episode, set created_at to the earliest ContentFragment.created_at.

    Returns:
        dict with migration statistics
    """
    stats = {"total": 0, "updated": 0, "skipped": 0, "errors": 0}

    cypher = """
    MATCH (ep:Node {type: 'Episode'})-[:EDGE {relationship_name: 'includes_chunk'}]->(cf:Node {type: 'ContentFragment'})
    RETURN ep.id, ep.created_at, collect(cf.created_at) as cf_times
    """

    try:
        results = await engine.query(cypher, {})
        stats["total"] = len(results)

        for row in results:
            ep_id, ep_created_at, cf_times = row

            cf_times_ms = []
            for t in cf_times:
                if t is not None:
                    if isinstance(t, datetime):
                        cf_times_ms.append(_datetime_to_ms(t))
                    else:
                        cf_times_ms.append(t)

            if not cf_times_ms:
                _log.debug(f"Episode {ep_id}: no ContentFragment timestamps, skipping")
                stats["skipped"] += 1
                continue

            earliest_cf_time = min(cf_times_ms)

            ep_created_at_ms = None
            if ep_created_at is not None:
                if isinstance(ep_created_at, datetime):
                    ep_created_at_ms = _datetime_to_ms(ep_created_at)
                else:
                    ep_created_at_ms = ep_created_at

            if ep_created_at_ms == earliest_cf_time:
                _log.debug(f"Episode {ep_id}: already correct, skipping")
                stats["skipped"] += 1
                continue

            new_created_at_str = _ms_to_utc_str(earliest_cf_time)

            if dry_run:
                old_time = (
                    datetime.fromtimestamp(ep_created_at_ms / 1000, tz=timezone.utc) if ep_created_at_ms else "None"
                )
                new_time = datetime.fromtimestamp(earliest_cf_time / 1000, tz=timezone.utc)
                _log.info(f"[DRY-RUN] Episode {ep_id[:8]}...: {old_time} -> {new_time}")
                stats["updated"] += 1
            else:
                update_cypher = """
                MATCH (n:Node {id: $id})
                SET n.created_at = timestamp($ts)
                """
                try:
                    await engine.query(update_cypher, {"id": ep_id, "ts": new_created_at_str})
                    stats["updated"] += 1
                except Exception as e:
                    _log.error(f"Failed to update Episode {ep_id}: {e}")
                    stats["errors"] += 1

    except Exception as e:
        _log.error(f"Failed to query Episodes: {e}")
        raise

    return stats


async def migrate_facets(engine, dry_run: bool = True) -> dict:
    """
    Migrate Facet nodes: infer created_at from linked Episode.

    For each Facet, set created_at to the Episode's created_at.

    Returns:
        dict with migration statistics
    """
    stats = {"total": 0, "updated": 0, "skipped": 0, "errors": 0}

    # Query: Get Facet and its parent Episode's created_at
    cypher = """
    MATCH (ep:Node {type: 'Episode'})-[:EDGE {relationship_name: 'has_facet'}]->(fa:Node {type: 'Facet'})
    RETURN fa.id, fa.created_at, ep.created_at
    """

    try:
        results = await engine.query(cypher, {})
        stats["total"] = len(results)

        for row in results:
            fa_id, fa_created_at, ep_created_at = row

            # Convert Episode created_at to ms
            ep_created_at_ms = None
            if ep_created_at is not None:
                if isinstance(ep_created_at, datetime):
                    ep_created_at_ms = _datetime_to_ms(ep_created_at)
                else:
                    ep_created_at_ms = ep_created_at

            if ep_created_at_ms is None:
                _log.debug(f"Facet {fa_id}: Episode has no created_at, skipping")
                stats["skipped"] += 1
                continue

            # Convert Facet created_at to ms
            fa_created_at_ms = None
            if fa_created_at is not None:
                if isinstance(fa_created_at, datetime):
                    fa_created_at_ms = _datetime_to_ms(fa_created_at)
                else:
                    fa_created_at_ms = fa_created_at

            # Check if already correct
            if fa_created_at_ms == ep_created_at_ms:
                _log.debug(f"Facet {fa_id}: already correct, skipping")
                stats["skipped"] += 1
                continue

            new_created_at_str = _ms_to_utc_str(ep_created_at_ms)

            if dry_run:
                old_time = (
                    datetime.fromtimestamp(fa_created_at_ms / 1000, tz=timezone.utc) if fa_created_at_ms else "None"
                )
                new_time = datetime.fromtimestamp(ep_created_at_ms / 1000, tz=timezone.utc)
                _log.info(f"[DRY-RUN] Facet {fa_id[:8]}...: {old_time} -> {new_time}")
                stats["updated"] += 1
            else:
                update_cypher = """
                MATCH (n:Node {id: $id})
                SET n.created_at = timestamp($ts)
                """
                try:
                    await engine.query(update_cypher, {"id": fa_id, "ts": new_created_at_str})
                    stats["updated"] += 1
                except Exception as e:
                    _log.error(f"Failed to update Facet {fa_id}: {e}")
                    stats["errors"] += 1

    except Exception as e:
        _log.error(f"Failed to query Facets: {e}")
        raise

    return stats


async def migrate_facet_points(engine, dry_run: bool = True) -> dict:
    """
    Migrate FacetPoint nodes: infer created_at from linked Facet.

    For each FacetPoint, set created_at to the Facet's created_at.

    Returns:
        dict with migration statistics
    """
    stats = {"total": 0, "updated": 0, "skipped": 0, "errors": 0}

    # Query: Get FacetPoint and its parent Facet's created_at
    cypher = """
    MATCH (fa:Node {type: 'Facet'})-[:EDGE {relationship_name: 'has_point'}]->(fp:Node {type: 'FacetPoint'})
    RETURN fp.id, fp.created_at, fa.created_at
    """

    try:
        results = await engine.query(cypher, {})
        stats["total"] = len(results)

        for row in results:
            fp_id, fp_created_at, fa_created_at = row

            # Convert Facet created_at to ms
            fa_created_at_ms = None
            if fa_created_at is not None:
                if isinstance(fa_created_at, datetime):
                    fa_created_at_ms = _datetime_to_ms(fa_created_at)
                else:
                    fa_created_at_ms = fa_created_at

            if fa_created_at_ms is None:
                _log.debug(f"FacetPoint {fp_id}: Facet has no created_at, skipping")
                stats["skipped"] += 1
                continue

            # Convert FacetPoint created_at to ms
            fp_created_at_ms = None
            if fp_created_at is not None:
                if isinstance(fp_created_at, datetime):
                    fp_created_at_ms = _datetime_to_ms(fp_created_at)
                else:
                    fp_created_at_ms = fp_created_at

            # Check if already correct
            if fp_created_at_ms == fa_created_at_ms:
                _log.debug(f"FacetPoint {fp_id}: already correct, skipping")
                stats["skipped"] += 1
                continue

            new_created_at_str = _ms_to_utc_str(fa_created_at_ms)

            if dry_run:
                old_time = (
                    datetime.fromtimestamp(fp_created_at_ms / 1000, tz=timezone.utc) if fp_created_at_ms else "None"
                )
                new_time = datetime.fromtimestamp(fa_created_at_ms / 1000, tz=timezone.utc)
                _log.info(f"[DRY-RUN] FacetPoint {fp_id[:8]}...: {old_time} -> {new_time}")
                stats["updated"] += 1
            else:
                update_cypher = """
                MATCH (n:Node {id: $id})
                SET n.created_at = timestamp($ts)
                """
                try:
                    await engine.query(update_cypher, {"id": fp_id, "ts": new_created_at_str})
                    stats["updated"] += 1
                except Exception as e:
                    _log.error(f"Failed to update FacetPoint {fp_id}: {e}")
                    stats["errors"] += 1

    except Exception as e:
        _log.error(f"Failed to query FacetPoints: {e}")
        raise

    return stats


async def migrate_documents(engine, dry_run: bool = True) -> dict:
    """
    Migrate Document nodes: copy created_at from properties JSON to column.

    Returns:
        dict with migration statistics
    """
    stats = {"total": 0, "updated": 0, "skipped": 0, "errors": 0}

    doc_types = ["TextDocument", "PdfDocument", "AudioDocument", "ImageDocument", "UnstructuredDocument", "Document"]
    type_filter = " OR ".join(f"n.type = '{t}'" for t in doc_types)

    cypher = f"""
    MATCH (n:Node)
    WHERE {type_filter}
    RETURN n.id, n.properties, n.created_at
    """

    try:
        results = await engine.query(cypher, {})
        stats["total"] = len(results)

        for row in results:
            node_id, props_raw, col_created_at = row

            try:
                props = json.loads(props_raw) if props_raw else {}
            except (json.JSONDecodeError, TypeError):
                props = {}

            props_created_at = props.get("created_at")

            if props_created_at is None:
                _log.debug(f"Document {node_id}: no created_at in properties, skipping")
                stats["skipped"] += 1
                continue

            col_created_at_ms = None
            if col_created_at is not None:
                if isinstance(col_created_at, datetime):
                    col_created_at_ms = _datetime_to_ms(col_created_at)
                else:
                    col_created_at_ms = col_created_at

            if col_created_at_ms == props_created_at:
                _log.debug(f"Document {node_id}: already correct, skipping")
                stats["skipped"] += 1
                continue

            new_created_at_str = _ms_to_utc_str(props_created_at)

            if dry_run:
                old_time = (
                    datetime.fromtimestamp(col_created_at_ms / 1000, tz=timezone.utc) if col_created_at_ms else "None"
                )
                new_time = datetime.fromtimestamp(props_created_at / 1000, tz=timezone.utc)
                _log.info(f"[DRY-RUN] Document {node_id[:8]}...: {old_time} -> {new_time}")
                stats["updated"] += 1
            else:
                update_cypher = """
                MATCH (n:Node {id: $id})
                SET n.created_at = timestamp($ts)
                """
                try:
                    await engine.query(update_cypher, {"id": node_id, "ts": new_created_at_str})
                    stats["updated"] += 1
                except Exception as e:
                    _log.error(f"Failed to update Document {node_id}: {e}")
                    stats["errors"] += 1

    except Exception as e:
        _log.error(f"Failed to query Documents: {e}")
        raise

    return stats


async def migrate_single_dataset(dataset_id: str, user_id: str, dry_run: bool = True) -> dict:
    """Migrate a single dataset's graph database."""
    from uuid import UUID
    from m_flow.context_global_variables import set_db_context
    from m_flow.auth.methods import get_user
    from m_flow.adapters.graph.get_graph_provider import get_graph_provider

    _log.info(f"Migrating dataset {dataset_id}...")

    await set_db_context(UUID(dataset_id), UUID(user_id))
    engine = await get_graph_provider()

    result = await engine.query("MATCH (n:Node) RETURN count(n)", {})
    node_count = result[0][0] if result else 0
    _log.info(f"Dataset {dataset_id}: {node_count} total nodes")

    if node_count == 0:
        return {
            "documents": {"total": 0},
            "content_fragments": {"total": 0},
            "episodes": {"total": 0},
            "facets": {"total": 0},
            "facet_points": {"total": 0},
        }

    doc_stats = await migrate_documents(engine, dry_run)
    cf_stats = await migrate_content_fragments(engine, dry_run)
    ep_stats = await migrate_episodes(engine, dry_run)

    # Migrate Facets and FacetPoints (must run after Episodes are migrated)
    fa_stats = await migrate_facets(engine, dry_run)
    fp_stats = await migrate_facet_points(engine, dry_run)

    return {
        "documents": doc_stats,
        "content_fragments": cf_stats,
        "episodes": ep_stats,
        "facets": fa_stats,
        "facet_points": fp_stats,
    }


async def run_migration(dry_run: bool = True):
    """Run the full migration across all datasets."""
    from m_flow.auth.methods import get_seed_user
    from m_flow.auth.permissions.methods import get_all_user_permission_datasets
    from m_flow.context_global_variables import backend_access_control_enabled

    _log.info(f"Starting migration (dry_run={dry_run})")
    _log.info("=" * 60)

    all_stats = {
        "datasets_processed": 0,
        "total_documents_updated": 0,
        "total_cf_updated": 0,
        "total_episodes_updated": 0,
        "total_facets_updated": 0,
        "total_facet_points_updated": 0,
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
                all_stats["total_documents_updated"] += result["documents"].get("updated", 0)
                all_stats["total_cf_updated"] += result["content_fragments"].get("updated", 0)
                all_stats["total_episodes_updated"] += result["episodes"].get("updated", 0)
                all_stats["total_facets_updated"] += result["facets"].get("updated", 0)
                all_stats["total_facet_points_updated"] += result["facet_points"].get("updated", 0)
                all_stats["total_errors"] += (
                    result["documents"].get("errors", 0)
                    + result["content_fragments"].get("errors", 0)
                    + result["episodes"].get("errors", 0)
                    + result["facets"].get("errors", 0)
                    + result["facet_points"].get("errors", 0)
                )

                _log.info(
                    f"Dataset {dataset.id}: "
                    f"docs={result['documents'].get('updated', 0)}, "
                    f"cf={result['content_fragments'].get('updated', 0)}, "
                    f"ep={result['episodes'].get('updated', 0)}, "
                    f"fa={result['facets'].get('updated', 0)}, "
                    f"fp={result['facet_points'].get('updated', 0)}"
                )

            except Exception as e:
                _log.error(f"Failed to migrate dataset {dataset.id}: {e}")
                all_stats["total_errors"] += 1
    else:
        from m_flow.adapters.graph.get_graph_provider import get_graph_provider

        engine = await get_graph_provider()

        doc_stats = await migrate_documents(engine, dry_run)
        cf_stats = await migrate_content_fragments(engine, dry_run)
        ep_stats = await migrate_episodes(engine, dry_run)
        fa_stats = await migrate_facets(engine, dry_run)
        fp_stats = await migrate_facet_points(engine, dry_run)

        all_stats["datasets_processed"] = 1
        all_stats["total_documents_updated"] = doc_stats.get("updated", 0)
        all_stats["total_cf_updated"] = cf_stats.get("updated", 0)
        all_stats["total_episodes_updated"] = ep_stats.get("updated", 0)
        all_stats["total_facets_updated"] = fa_stats.get("updated", 0)
        all_stats["total_facet_points_updated"] = fp_stats.get("updated", 0)
        all_stats["total_errors"] = (
            doc_stats.get("errors", 0)
            + cf_stats.get("errors", 0)
            + ep_stats.get("errors", 0)
            + fa_stats.get("errors", 0)
            + fp_stats.get("errors", 0)
        )

    _log.info("=" * 60)
    _log.info("Migration Summary")
    _log.info("=" * 60)
    _log.info(f"Datasets processed: {all_stats['datasets_processed']}")
    _log.info(f"Documents updated: {all_stats['total_documents_updated']}")
    _log.info(f"ContentFragments updated: {all_stats['total_cf_updated']}")
    _log.info(f"Episodes updated: {all_stats['total_episodes_updated']}")
    _log.info(f"Facets updated: {all_stats['total_facets_updated']}")
    _log.info(f"FacetPoints updated: {all_stats['total_facet_points_updated']}")
    _log.info(f"Errors: {all_stats['total_errors']}")

    if dry_run:
        _log.info("DRY RUN completed. Run without --dry-run to apply changes.")
    else:
        _log.info("Migration completed.")

    return all_stats


def main():
    parser = argparse.ArgumentParser(description="Migrate created_at timestamps in Kuzu graph database")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without applying")
    args = parser.parse_args()

    asyncio.run(run_migration(dry_run=args.dry_run))


if __name__ == "__main__":
    main()
