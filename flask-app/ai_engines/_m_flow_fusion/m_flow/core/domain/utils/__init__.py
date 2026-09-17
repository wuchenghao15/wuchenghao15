"""
Graph element identifier utilities.

Provides consistent ID and name generation for nodes and edges in the
knowledge graph. Import from this package for all graph element naming needs.

Available functions:

- :func:`generate_node_id` - Create unique node identifiers
- :func:`generate_node_name` - Generate human-readable node names
- :func:`generate_edge_id` - Create unique edge identifiers
- :func:`generate_edge_name` - Generate descriptive edge names
"""

from m_flow.core.domain.utils.generate_edge_id import generate_edge_id as generate_edge_id
from m_flow.core.domain.utils.generate_edge_name import generate_edge_name as generate_edge_name
from m_flow.core.domain.utils.generate_node_id import generate_node_id as generate_node_id
from m_flow.core.domain.utils.generate_node_name import generate_node_name as generate_node_name

__all__: list[str] = [
    "generate_node_id",
    "generate_node_name",
    "generate_edge_id",
    "generate_edge_name",
]
