"""
Database schema extraction and ingestion.

Converts relational database schema to MemoryNode models
for graph construction.
"""

from __future__ import annotations

import json
from typing import Dict, List
from uuid import NAMESPACE_OID, uuid5

from sqlalchemy import text

from m_flow.adapters.relational.config import get_migration_config
from m_flow.adapters.relational.get_migration_relational_engine import (
    get_migration_relational_engine,
)
from m_flow.core.models.MemoryNode import MemoryNode
from m_flow.ingestion.schema.models import (
    DatabaseSchema,
    SchemaRelationship,
    SchemaTable,
)


async def ingest_database_schema(
    schema: dict,
    max_sample_rows: int = 0,
) -> Dict[str, List[MemoryNode] | MemoryNode]:
    """
    Extract database schema and sample data.

    Args:
        schema: Database schema dictionary.
        max_sample_rows: Sample rows per table (0 = none).

    Returns:
        Dict with:
          - database_schema: DatabaseSchema node
          - schema_tables: List of SchemaTable nodes
          - relationships: List of SchemaRelationship nodes
    """
    cfg = get_migration_config()
    engine = get_migration_relational_engine()

    tables_data = {}
    sample_data = {}
    schema_tables = []
    schema_rels = []

    # Normalize sample rows
    try:
        max_sample_rows = max(0, int(max_sample_rows))
    except (TypeError, ValueError):
        max_sample_rows = 0

    qi = engine.engine.dialect.identifier_preparer.quote

    def quote_name(name: str) -> str:
        return ".".join(qi(p) for p in name.split("."))

    async with engine.engine.begin() as cursor:
        for table_name, details in schema.items():
            quoted = quote_name(table_name)

            # Fetch sample rows
            if max_sample_rows > 0:
                result = await cursor.execute(
                    text(f"SELECT * FROM {quoted} LIMIT :limit;"),
                    {"limit": max_sample_rows},
                )
                rows = [dict(r) for r in result.mappings().all()]
            else:
                rows = []

            # Estimate row count
            row_count = await _estimate_row_count(cursor, engine, table_name, quoted)

            # Create table node
            table_node = SchemaTable(
                id=uuid5(NAMESPACE_OID, name=table_name),
                name=table_name,
                columns=json.dumps(details["columns"], default=str),
                primary_key=details.get("primary_key"),
                foreign_keys=json.dumps(details.get("foreign_keys", []), default=str),
                sample_rows=json.dumps(rows, default=str),
                row_count_estimate=row_count,
                description=(
                    f"Table '{table_name}' with {len(details['columns'])} columns, "
                    f"~{row_count} rows. Columns: {details['columns']}"
                ),
            )
            schema_tables.append(table_node)
            tables_data[table_name] = details
            sample_data[table_name] = rows

            # Process foreign keys
            for fk in details.get("foreign_keys", []):
                ref_table = _resolve_ref_table(fk["ref_table"], table_name)
                rel_name = f"{table_name}:{fk['column']}->{ref_table}:{fk['ref_column']}"

                rel_node = SchemaRelationship(
                    id=uuid5(NAMESPACE_OID, name=rel_name),
                    name=rel_name,
                    source_table=table_name,
                    target_table=ref_table,
                    relationship_type="foreign_key",
                    source_column=fk["column"],
                    target_column=fk["ref_column"],
                    description=f"FK: {table_name}.{fk['column']} -> {ref_table}.{fk['ref_column']}",
                )
                schema_rels.append(rel_node)

    # Create database schema node
    db_id = f"{cfg.migration_db_provider}:{cfg.migration_db_name}"
    db_node = DatabaseSchema(
        id=uuid5(NAMESPACE_OID, name=db_id),
        name=cfg.migration_db_name,
        database_type=cfg.migration_db_provider,
        tables=json.dumps(tables_data, default=str),
        sample_data=json.dumps(sample_data, default=str),
        description=(
            f"Database '{cfg.migration_db_name}' ({cfg.migration_db_provider}) "
            f"with {len(schema_tables)} tables and {len(schema_rels)} relationships."
        ),
    )

    return {
        "database_schema": db_node,
        "schema_tables": schema_tables,
        "relationships": schema_rels,
    }


async def _estimate_row_count(cursor, engine, table_name: str, quoted: str) -> int:
    """Get row count estimate (fast for PostgreSQL)."""
    if engine.engine.dialect.name == "postgresql":
        schema_part, table_part = table_name.split(".", 1) if "." in table_name else ("public", table_name)
        result = await cursor.execute(
            text(
                "SELECT reltuples::bigint AS est FROM pg_class c "
                "JOIN pg_namespace n ON n.oid = c.relnamespace "
                "WHERE n.nspname = :schema AND c.relname = :table"
            ),
            {"schema": schema_part, "table": table_part},
        )
        return result.scalar() or 0

    # Fallback to COUNT(*)
    result = await cursor.execute(text(f"SELECT COUNT(*) FROM {quoted};"))
    return result.scalar()


def _resolve_ref_table(ref_table: str, source_table: str) -> str:
    """Add schema prefix to ref table if needed."""
    if "." not in ref_table and "." in source_table:
        schema_prefix = source_table.split(".", 1)[0]
        return f"{schema_prefix}.{ref_table}"
    return ref_table
