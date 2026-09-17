"""
Neo4j graph metrics utilities.

Provides functions for calculating graph statistics using Neo4j
Graph Data Science (GDS) library.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from m_flow.adapters.graph.neo4j_driver.adapter import Neo4jAdapter


async def get_edge_density(adapter: "Neo4jAdapter") -> float:
    """
    Compute graph edge density.

    Edge density = actual_edges / maximum_possible_edges
    For n nodes: max_edges = n * (n - 1)

    Returns:
        Edge density as float, 0 if fewer than 2 nodes.
    """
    cypher = """
    MATCH (n)
    WITH count(n) AS node_count
    MATCH ()-[r]->()
    WITH node_count, count(r) AS edge_count
    RETURN CASE
        WHEN node_count < 2 THEN 0.0
        ELSE edge_count * 1.0 / (node_count * (node_count - 1))
    END AS density
    """
    rows = await adapter.query(cypher)
    return rows[0]["density"] if rows else 0.0


async def get_num_connected_components(
    adapter: "Neo4jAdapter",
    graph_name: str,
) -> int:
    """
    Count weakly connected components via GDS.

    Requires a projected graph created with gds.graph.project.

    Returns:
        Number of connected components.
    """
    cypher = f"""
    CALL gds.wcc.stats('{graph_name}')
    YIELD componentCount
    RETURN componentCount AS count
    """
    rows = await adapter.query(cypher)
    return rows[0]["count"] if rows else 0


async def get_size_of_connected_components(
    adapter: "Neo4jAdapter",
    graph_name: str,
) -> list[int]:
    """
    Get sizes of all connected components.

    Returns:
        List of component sizes, sorted descending.
    """
    cypher = f"""
    CALL gds.wcc.stream('{graph_name}')
    YIELD componentId
    RETURN componentId, count(*) AS size
    ORDER BY size DESC
    """
    rows = await adapter.query(cypher)
    return [r["size"] for r in rows] if rows else []


async def count_self_loops(adapter: "Neo4jAdapter") -> int:
    """
    Count self-referential relationships.

    Returns:
        Number of edges where source == target.
    """
    cypher = """
    MATCH (n)-[r]->(n)
    RETURN count(r) AS self_loops
    """
    rows = await adapter.query(cypher)
    return rows[0]["self_loops"] if rows else 0


async def get_shortest_path_lengths(
    adapter: "Neo4jAdapter",
    graph_name: str,
) -> list[float]:
    """
    Retrieve all shortest path distances via GDS.

    Returns:
        List of path distances.
    """
    cypher = f"""
    CALL gds.allShortestPaths.stream('{graph_name}')
    YIELD distance
    RETURN distance
    """
    rows = await adapter.query(cypher)
    return [r["distance"] for r in rows] if rows else []


async def get_avg_clustering(
    adapter: "Neo4jAdapter",
    graph_name: str,
) -> float:
    """
    Compute average local clustering coefficient.

    Returns:
        Average clustering coefficient across all nodes.
    """
    cypher = f"""
    CALL gds.localClusteringCoefficient.stats('{graph_name}')
    YIELD averageClusteringCoefficient
    RETURN averageClusteringCoefficient AS avg
    """
    rows = await adapter.query(cypher)
    return rows[0]["avg"] if rows else 0.0
