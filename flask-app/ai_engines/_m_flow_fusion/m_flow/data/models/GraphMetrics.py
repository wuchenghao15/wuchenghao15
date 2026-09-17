"""
Graph metrics ORM model.

Persists computed knowledge graph statistics.
"""

from __future__ import annotations

from uuid import uuid4

from sqlalchemy import UUID, Column, DateTime, Float, Integer, JSON
from sqlalchemy.sql import func

from m_flow.adapters.relational import Base


class GraphMetrics(Base):
    """Knowledge graph metrics snapshot."""

    __tablename__ = "graph_metrics"

    # Primary key
    id = Column(UUID, primary_key=True, default=uuid4)

    # Size: tokens, nodes, edges
    num_tokens = Column(Integer)
    num_nodes = Column(Integer)
    num_edges = Column(Integer)

    # Structure: degree, density, loops
    mean_degree = Column(Float)
    edge_density = Column(Float)
    num_selfloops = Column(Integer)

    # Connectivity: components, paths
    num_connected_components = Column(Integer)
    sizes_of_connected_components = Column(JSON)
    diameter = Column(Integer)
    avg_shortest_path_length = Column(Float)

    # Clustering
    avg_clustering = Column(Float)

    # Audit timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
