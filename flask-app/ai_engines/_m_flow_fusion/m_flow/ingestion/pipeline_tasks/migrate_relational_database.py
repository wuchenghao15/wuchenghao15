"""
Relational to graph database migration.

Converts relational database tables and relationships into
graph nodes and edges for knowledge graph construction.
"""

from __future__ import annotations

from uuid import NAMESPACE_OID, uuid5

from sqlalchemy import text

from m_flow.adapters.relational.get_migration_relational_engine import (
    get_migration_relational_engine,
)
from m_flow.core.domain.models import ColumnValue, TableRow, TableType
from m_flow.ingestion.schema.ingest_database_schema import ingest_database_schema
from m_flow.shared.logging_utils import get_logger
from m_flow.storage.index_graph_links import index_relations
from m_flow.storage.index_memory_nodes import index_memory_nodes

_log = get_logger(__name__)


async def migrate_relational_database(
    graph_db,
    schema: dict,
    migrate_column_data: bool = True,
    schema_only: bool = False,
):
    """
    Migrate relational database to graph database.

    Creates:
      - TableType nodes for each table
      - TableRow nodes for each row
      - Edges for foreign key relationships

    Args:
        graph_db: Target graph database adapter.
        schema: Database schema dictionary.
        migrate_column_data: Include column values as nodes.
        schema_only: Only migrate schema, not row data.

    Returns:
        Graph data from the target database.
    """
    if schema_only:
        nodes, edges = await _schema_only_ingestion(schema)
    else:
        nodes, edges = await _full_database_ingestion(schema, migrate_column_data)

    # Deduplicate edges
    unique_edges = _dedupe_edges(edges)

    # Persist to graph
    await graph_db.add_nodes(list(nodes.values()))
    await graph_db.add_edges(unique_edges)

    # Index for search
    await index_memory_nodes(list(nodes.values()))
    await index_relations()

    _log.info("Relational database migration completed")
    return await graph_db.get_graph_data()


def _dedupe_edges(edges: list) -> list:
    """Remove duplicate edges based on (source, target, rel, attrs)."""
    seen = set()
    unique = []

    for src, tgt, rel, attrs in edges:
        frozen_attrs = frozenset(sorted(attrs.items()))
        key = (src, tgt, rel, frozen_attrs)

        if key not in seen:
            seen.add(key)
            unique.append((src, tgt, rel, attrs))

    return unique


async def _schema_only_ingestion(schema: dict) -> tuple[dict, list]:
    """Ingest only schema metadata."""
    nodes = {}
    edges = []

    result = await ingest_database_schema(schema=schema, max_sample_rows=5)
    db_schema = result["database_schema"]
    tables = result["schema_tables"]
    rels = result["relationships"]

    nodes[db_schema.id] = db_schema

    for table in tables:
        nodes[table.id] = table
        edges.append(
            (
                table.id,
                db_schema.id,
                "is_part_of",
                {
                    "source_node_id": table.id,
                    "target_node_id": db_schema.id,
                    "relationship_name": "is_part_of",
                },
            )
        )

    name_to_id = {t.name: t.id for t in tables}

    for rel in rels:
        src_id = name_to_id.get(rel.source_table)
        tgt_id = name_to_id.get(rel.target_table)

        nodes[rel.id] = rel

        # Source -> relationship node
        edges.append(
            (
                src_id,
                rel.id,
                "has_relationship",
                {
                    "source_node_id": src_id,
                    "target_node_id": rel.id,
                    "relationship_name": rel.relationship_type,
                },
            )
        )
        # Relationship node -> target
        edges.append(
            (
                rel.id,
                tgt_id,
                "has_relationship",
                {
                    "source_node_id": rel.id,
                    "target_node_id": tgt_id,
                    "relationship_name": rel.relationship_type,
                },
            )
        )
        # Direct relationship
        edges.append(
            (
                src_id,
                tgt_id,
                rel.relationship_type,
                {
                    "source_node_id": src_id,
                    "target_node_id": tgt_id,
                    "relationship_name": rel.relationship_type,
                },
            )
        )

    return nodes, edges


async def _full_database_ingestion(
    schema: dict,
    migrate_columns: bool,
) -> tuple[dict, list]:
    """Ingest full database with row data."""
    engine = get_migration_relational_engine()
    nodes = {}
    edges = []

    async with engine.engine.begin() as cursor:
        # Create table and row nodes
        for table_name, details in schema.items():
            table_node = TableType(
                id=uuid5(NAMESPACE_OID, name=table_name),
                name=table_name,
                description=f'Relational table: "{table_name}"',
            )
            nodes[table_name] = table_node

            # Fetch rows
            rows = (await cursor.execute(text(f"SELECT * FROM {table_name};"))).fetchall()
            pk_col = details.get("primary_key") or details["columns"][0]["name"]

            for row in rows:
                props = {c["name"]: row[i] for i, c in enumerate(details["columns"])}
                pk_val = props[pk_col]
                row_id = f"{table_name}:{pk_val}"

                row_node = TableRow(
                    id=uuid5(NAMESPACE_OID, name=row_id),
                    name=row_id,
                    is_a=table_node,
                    properties=str(props),
                    description=f'Row in "{table_name}": {props}',
                )
                nodes[row_id] = row_node

                edges.append(
                    (
                        row_node.id,
                        table_node.id,
                        "is_part_of",
                        {
                            "relationship_name": "is_part_of",
                            "source_node_id": row_node.id,
                            "target_node_id": table_node.id,
                        },
                    )
                )

                if migrate_columns:
                    fk_cols = {fk["ref_column"] for fk in details.get("foreign_keys", [])}

                    for key, val in props.items():
                        if key == pk_col or key in fk_cols:
                            continue

                        col_id = f"{table_name}:{key}:{val}"
                        col_node = ColumnValue(
                            id=uuid5(NAMESPACE_OID, name=col_id),
                            name=col_id,
                            properties=f"{key} {val} {table_name}",
                            description=f"Column {key}={val} in {table_name}",
                        )
                        nodes[col_id] = col_node

                        edges.append(
                            (
                                row_node.id,
                                col_node.id,
                                key,
                                {
                                    "relationship_name": key,
                                    "source_node_id": row_node.id,
                                    "target_node_id": col_node.id,
                                },
                            )
                        )

        # Process foreign keys
        for table_name, details in schema.items():
            pk_col = details.get("primary_key") or details["columns"][0]["name"]

            for fk in details.get("foreign_keys", []):
                a1 = f"{table_name}_e1"
                a2 = f"{fk['ref_table']}_e2"

                query = text(
                    f"SELECT {a1}.{pk_col} AS src, {a2}.{fk['ref_column']} AS ref "
                    f"FROM {table_name} AS {a1} "
                    f"JOIN {fk['ref_table']} AS {a2} "
                    f"ON {a1}.{fk['column']} = {a2}.{fk['ref_column']};"
                )

                for src_id, ref_val in (await cursor.execute(query)).fetchall():
                    src_node = nodes[f"{table_name}:{src_id}"]
                    tgt_node = nodes[f"{fk['ref_table']}:{ref_val}"]

                    edges.append(
                        (
                            src_node.id,
                            tgt_node.id,
                            fk["column"],
                            {
                                "source_node_id": src_node.id,
                                "target_node_id": tgt_node.id,
                                "relationship_name": fk["column"],
                            },
                        )
                    )

    return nodes, edges
