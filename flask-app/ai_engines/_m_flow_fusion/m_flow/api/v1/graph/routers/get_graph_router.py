"""
Graph API Router

Provides REST API endpoints for knowledge graph visualization,
including global graph data and subgraph queries.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from m_flow.api.DTO import OutDTO
from m_flow.shared.logging_utils import get_logger

if TYPE_CHECKING:
    from m_flow.auth.models import User

_logger = get_logger()


# ---------------------------------------------------------------------------
# Response Models
# ---------------------------------------------------------------------------


class GraphNodeDTO(OutDTO):
    """Knowledge graph node."""

    id: str
    name: str
    type: str = "Unknown"
    properties: dict = {}
    dataset_id: Optional[str] = None  # For multi-tenant support: frontend needs to know which dataset a node belongs to


class GraphEdgeDTO(OutDTO):
    """Knowledge graph edge."""

    source: str
    target: str
    relationship: str


class GraphDTO(OutDTO):
    """Complete knowledge graph structure."""

    nodes: list[GraphNodeDTO]
    edges: list[GraphEdgeDTO]


class EpisodeOverviewDTO(OutDTO):
    """Episode summary for Layer 0 overview (Phase 0.4)."""

    id: str
    name: str
    summary: Optional[str] = None
    facet_count: int = 0
    entity_count: int = 0
    created_at: Optional[str] = None
    dataset_id: Optional[str] = None


class EpisodesOverviewDTO(OutDTO):
    """Episodes overview response (Phase 0.4)."""

    episodes: list[EpisodeOverviewDTO]
    total: int
    limit: int
    offset: int


class EntityNetworkNodeDTO(OutDTO):
    """Entity network node (Phase 0.5)."""

    id: str
    name: str
    type: str
    relationship: str
    dataset_id: Optional[str] = None


class EntityNetworkDTO(OutDTO):
    """Entity network response (Phase 0.5)."""

    entity_id: str
    entity_name: str
    entity_type: str
    connected_episodes: list[EntityNetworkNodeDTO]
    connected_facets: list[EntityNetworkNodeDTO]
    same_entities: list[EntityNetworkNodeDTO] = []
    dataset_id: Optional[str] = None


# ---------------------------------------------------------------------------
# Dependency Helper
# ---------------------------------------------------------------------------


def _get_auth_user():
    """Return the authentication dependency."""
    from m_flow.auth.methods import get_authenticated_user

    return get_authenticated_user


# ---------------------------------------------------------------------------
# Route Handlers
# ---------------------------------------------------------------------------


def _register_get_global_graph(router: APIRouter) -> None:
    """Register GET / endpoint for global graph data."""

    @router.get("", response_model=GraphDTO)
    async def get_global_graph(
        dataset_id: Optional[UUID] = Query(
            default=None,
            description="Filter by specific dataset UUID. If not provided, returns graph from all accessible datasets.",
        ),
        user: "User" = Depends(_get_auth_user()),
    ):
        """
        Retrieve knowledge graph data.

        Args:
            dataset_id: Optional dataset UUID to filter by. If provided, returns
                       graph only from that dataset. If not, returns unified graph
                       from all datasets the user has read access to.

        Returns:
            GraphDTO with nodes and edges.
        """
        from m_flow.adapters.graph import get_graph_provider
        from m_flow.auth.permissions.methods import get_all_user_permission_datasets
        from m_flow.context_global_variables import (
            backend_access_control_enabled,
            set_db_context,
        )

        try:
            # Get datasets to query
            all_datasets = await get_all_user_permission_datasets(user, "read")

            # Filter by dataset_id if provided
            if dataset_id:
                datasets = [ds for ds in all_datasets if ds.id == dataset_id]
                if not datasets:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Dataset {dataset_id} not found or not accessible",
                    )
            else:
                datasets = all_datasets

            all_nodes = []
            all_edges = []
            seen_node_ids = set()
            seen_edge_keys = set()

            # When access control is disabled, all datasets share the same database.
            # Query once to avoid redundant database reads.
            if not backend_access_control_enabled():
                datasets = datasets[:1] if datasets else []

            for dataset in datasets:
                try:
                    await set_db_context(dataset.id, dataset.owner_id)
                    engine = await get_graph_provider()
                    nodes, edges = await engine.get_graph_data()

                    # Add nodes (avoiding duplicates)
                    # Pass dataset.id so frontend knows which dataset each node belongs to
                    for node in nodes:
                        node_id, props = node
                        if node_id not in seen_node_ids:
                            seen_node_ids.add(node_id)
                            all_nodes.append(_format_node(node, dataset.id))

                    # Add edges (avoiding duplicates)
                    for edge in edges:
                        edge_key = (str(edge[0]), str(edge[1]), str(edge[2]))
                        if edge_key not in seen_edge_keys:
                            seen_edge_keys.add(edge_key)
                            all_edges.append(_format_edge(edge))
                except Exception as e:
                    _logger.warning(f"Error fetching graph for dataset {dataset.id}: {e}")
                    continue

            return {"nodes": all_nodes, "edges": all_edges}

        except HTTPException:
            raise
        except Exception as err:
            _logger.error("Error fetching global graph: %s", err)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error retrieving graph data: {err}",
            ) from err


def _register_get_episode_subgraph(router: APIRouter) -> None:
    """Register GET /episode/{episode_id} endpoint."""

    # Allowed relationship types (Episode connects to both Facet and Entity directly)
    EPISODE_RELATIONSHIP_TYPES = {"has_facet", "involves_entity"}
    PROCEDURAL_RELATIONSHIP_TYPES = {"derived_procedure", "has_key_point", "has_context_point", "supersedes"}

    @router.get("/episode/{episode_id}", response_model=GraphDTO)
    async def get_episode_subgraph(
        episode_id: str,
        dataset_id: Optional[UUID] = Query(
            default=None, description="Dataset UUID. Required in multi-user mode, optional in single-user mode."
        ),
        include_procedural: bool = Query(
            default=False, description="If True, also include Procedure nodes derived from this episode."
        ),
        user: "User" = Depends(_get_auth_user()),
    ):
        """
        Retrieve subgraph for a specific episode.

        Returns nodes and edges related to the specified episode ID,
        including Facets and Entities directly connected to the episode.

        Key features:
        - Supports dataset_id parameter for multi-tenant isolation
        - Permission checking in multi-user mode
        - Returns actual relationship types (has_facet, involves_entity)
        - Returns 404 if episode not found
        """
        from m_flow.adapters.graph import get_graph_provider
        from m_flow.auth.permissions.methods import get_all_user_permission_datasets
        from m_flow.context_global_variables import (
            backend_access_control_enabled,
            set_db_context,
        )

        try:
            # Handle single-user vs multi-user mode
            if backend_access_control_enabled():
                # Multi-user mode: dataset_id is required
                if not dataset_id:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="dataset_id is required in multi-user mode",
                    )

                # Validate user permissions
                all_datasets = await get_all_user_permission_datasets(user, "read")
                authorized_dataset = next((ds for ds in all_datasets if ds.id == dataset_id), None)
                if not authorized_dataset:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Dataset {dataset_id} not found or not accessible",
                    )

                # Set dataset context for database operations
                await set_db_context(dataset_id, authorized_dataset.owner_id)

            engine = await get_graph_provider()

            # Single query: fetch episode node + all connected edges in one lock acquisition
            raw = await engine.query(
                """
                MATCH (ep:Node) WHERE ep.id = $id
                OPTIONAL MATCH (ep)-[r]-(m:Node)
                RETURN
                    {id: ep.id, name: ep.name, type: ep.type, properties: ep.properties,
                     created_at: ep.created_at, updated_at: ep.updated_at},
                    r.relationship_name,
                    {id: m.id, name: m.name, type: m.type, properties: m.properties,
                     created_at: m.created_at, updated_at: m.updated_at}
                """,
                {"id": episode_id},
            )

            if not raw:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Episode {episode_id} not found",
                )

            from m_flow.adapters.graph.kuzu.adapter import _merge_node_props

            episode_props = _merge_node_props(raw[0][0])

            actual_type = episode_props.get("type", "")
            if actual_type != "Episode":
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Node {episode_id} is type '{actual_type}', not Episode",
                )

            nodes = []
            result_edges = []
            seen_node_ids = set()

            ds_id_str = str(dataset_id) if dataset_id else None

            nodes.append(
                {
                    "id": episode_id,
                    "name": episode_props.get("name", f"Episode_{episode_id}"),
                    "type": "Episode",
                    "properties": episode_props,
                    "dataset_id": ds_id_str,
                }
            )
            seen_node_ids.add(episode_id)

            for row in raw:
                relationship_name = row[1]
                neighbor_raw = row[2]

                if relationship_name is None or neighbor_raw is None:
                    continue
                allowed = EPISODE_RELATIONSHIP_TYPES
                if include_procedural:
                    allowed = allowed | PROCEDURAL_RELATIONSHIP_TYPES
                if relationship_name not in allowed:
                    continue

                neighbor = _merge_node_props(neighbor_raw)
                neighbor_id = str(neighbor.get("id", ""))

                if neighbor_id and neighbor_id not in seen_node_ids:
                    seen_node_ids.add(neighbor_id)
                    nodes.append(
                        {
                            "id": neighbor_id,
                            "name": neighbor.get("name", f"Node_{neighbor_id}"),
                            "type": neighbor.get("type", "Unknown"),
                            "properties": neighbor,
                            "dataset_id": ds_id_str,
                        }
                    )

                result_edges.append(
                    {
                        "source": episode_id,
                        "target": neighbor_id,
                        "relationship": relationship_name,
                    }
                )

            return {"nodes": nodes, "edges": result_edges}

        except HTTPException:
            raise
        except Exception as err:
            _logger.error("Error fetching episode subgraph: %s", err)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error retrieving episode subgraph: {err}",
            ) from err


def _register_get_facet_subgraph(router: APIRouter) -> None:
    """Register GET /facet/{facet_id} endpoint."""

    # Allowed relationship types for facet subgraph
    FACET_RELATIONSHIP_TYPES = {"has_point", "involves_entity"}

    @router.get("/facet/{facet_id}", response_model=GraphDTO)
    async def get_facet_subgraph(
        facet_id: str,
        dataset_id: Optional[UUID] = Query(
            default=None, description="Dataset UUID. Required in multi-user mode, optional in single-user mode."
        ),
        user: "User" = Depends(_get_auth_user()),
    ):
        """
        Retrieve subgraph for a specific facet.

        Returns nodes and edges related to the specified facet ID,
        including FacetPoints and Entities directly connected to the facet.

        Key features:
        - Supports dataset_id parameter for multi-tenant isolation
        - Permission checking in multi-user mode
        - Returns actual relationship types (has_point, involves_entity)
        - Returns 404 if facet not found
        """
        from m_flow.adapters.graph import get_graph_provider
        from m_flow.auth.permissions.methods import get_all_user_permission_datasets
        from m_flow.context_global_variables import (
            backend_access_control_enabled,
            set_db_context,
        )

        try:
            # Handle single-user vs multi-user mode
            if backend_access_control_enabled():
                # Multi-user mode: dataset_id is required
                if not dataset_id:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="dataset_id is required in multi-user mode",
                    )

                # Validate user permissions
                all_datasets = await get_all_user_permission_datasets(user, "read")
                authorized_dataset = next((ds for ds in all_datasets if ds.id == dataset_id), None)
                if not authorized_dataset:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Dataset {dataset_id} not found or not accessible",
                    )

                # Set dataset context for database operations
                await set_db_context(dataset_id, authorized_dataset.owner_id)

            engine = await get_graph_provider()

            # Single query: fetch facet node + all connected edges in one lock acquisition
            raw = await engine.query(
                """
                MATCH (f:Node) WHERE f.id = $id
                OPTIONAL MATCH (f)-[r]-(m:Node)
                RETURN
                    {id: f.id, name: f.name, type: f.type, properties: f.properties,
                     created_at: f.created_at, updated_at: f.updated_at},
                    r.relationship_name,
                    {id: m.id, name: m.name, type: m.type, properties: m.properties,
                     created_at: m.created_at, updated_at: m.updated_at}
                """,
                {"id": facet_id},
            )

            if not raw:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Facet {facet_id} not found",
                )

            from m_flow.adapters.graph.kuzu.adapter import _merge_node_props

            facet_props = _merge_node_props(raw[0][0])

            actual_type = facet_props.get("type", "")
            if actual_type != "Facet":
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Node {facet_id} is type '{actual_type}', not Facet",
                )

            ds_id_str = str(dataset_id) if dataset_id else None

            nodes = []
            result_edges = []
            seen_node_ids = set()

            nodes.append(
                {
                    "id": facet_id,
                    "name": facet_props.get("name", f"Facet_{facet_id}"),
                    "type": "Facet",
                    "properties": facet_props,
                    "dataset_id": ds_id_str,
                }
            )
            seen_node_ids.add(facet_id)

            for row in raw:
                relationship_name = row[1]
                neighbor_raw = row[2]

                if relationship_name is None or neighbor_raw is None:
                    continue
                if relationship_name not in FACET_RELATIONSHIP_TYPES:
                    continue

                neighbor = _merge_node_props(neighbor_raw)
                neighbor_id = str(neighbor.get("id", ""))

                if neighbor_id and neighbor_id not in seen_node_ids:
                    seen_node_ids.add(neighbor_id)
                    nodes.append(
                        {
                            "id": neighbor_id,
                            "name": neighbor.get("name", f"Node_{neighbor_id}"),
                            "type": neighbor.get("type", "Unknown"),
                            "properties": neighbor,
                            "dataset_id": ds_id_str,
                        }
                    )

                result_edges.append(
                    {
                        "source": facet_id,
                        "target": neighbor_id,
                        "relationship": relationship_name,
                    }
                )

            return {"nodes": nodes, "edges": result_edges}

        except HTTPException:
            raise
        except Exception as err:
            _logger.error("Error fetching facet subgraph: %s", err)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error retrieving facet subgraph: {err}",
            ) from err


def _register_get_episodes_overview(router: APIRouter) -> None:
    """Register GET /episodes endpoint (Phase 0.4)."""

    @router.get("/episodes", response_model=EpisodesOverviewDTO)
    async def get_episodes_overview(
        dataset_id: Optional[UUID] = Query(
            default=None, description="Dataset UUID. If not provided, returns episodes from all accessible datasets."
        ),
        limit: int = Query(
            default=10000, ge=1, description="Maximum number of episodes to return. Set high to get all."
        ),
        offset: int = Query(default=0, ge=0, description="Number of episodes to skip"),
        user: "User" = Depends(_get_auth_user()),
    ):
        """
        Retrieve episodes overview for Layer 0 navigation.

        Returns all Episodes with aggregated information (facet_count, entity_count).
        Supports pagination via limit and offset parameters.

        Key features:
        - Returns episode list with aggregated counts
        - Supports pagination (limit/offset)
        - Permission checking for dataset access
        """
        from m_flow.adapters.graph import get_graph_provider
        from m_flow.auth.permissions.methods import get_all_user_permission_datasets
        from m_flow.context_global_variables import (
            backend_access_control_enabled,
            set_db_context,
        )

        try:
            # Get datasets the user has read access to
            all_datasets = await get_all_user_permission_datasets(user, "read")

            if dataset_id:
                datasets = [ds for ds in all_datasets if ds.id == dataset_id]
                if not datasets:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Dataset {dataset_id} not found or not accessible",
                    )
            else:
                datasets = all_datasets

            all_episodes = []
            seen_episode_ids: set = set()

            # When access control is disabled, all datasets share the same database.
            # Query once to avoid returning duplicate episodes.
            if not backend_access_control_enabled():
                datasets = datasets[:1] if datasets else []

            for dataset in datasets:
                try:
                    await set_db_context(dataset.id, dataset.owner_id)
                    engine = await get_graph_provider()

                    # Query all Episode nodes with aggregated counts
                    # Use WITH clauses to ensure proper aggregation across multiple OPTIONAL MATCHes
                    cypher = """
                    MATCH (ep:Node {type: 'Episode'})
                    OPTIONAL MATCH (ep)-[:EDGE {relationship_name: 'has_facet'}]->(f:Node {type: 'Facet'})
                    WITH ep, count(DISTINCT f) as facet_count
                    OPTIONAL MATCH (ep)-[:EDGE {relationship_name: 'involves_entity'}]->(e:Node)
                    WHERE e.type IN ['Entity', 'Entity']
                    RETURN ep.id, ep.name, ep.properties, ep.created_at, facet_count, count(DISTINCT e) as entity_count
                    """

                    results = await engine.query(cypher, {})

                    for row in results:
                        if row and len(row) >= 6:
                            ep_id, ep_name, ep_props, col_created_at, facet_count, entity_count = row
                            ep_id_str = str(ep_id)

                            # Skip duplicate episodes (same ID already processed)
                            if ep_id_str in seen_episode_ids:
                                continue
                            seen_episode_ids.add(ep_id_str)

                            # Handle properties - may be dict, JSON string, or None
                            props = ep_props or {}
                            if isinstance(props, str):
                                try:
                                    import json

                                    props = json.loads(props)
                                except (json.JSONDecodeError, TypeError):
                                    props = {}

                            # Prioritize column created_at over properties created_at
                            created_at = None
                            if col_created_at is not None:
                                from datetime import datetime

                                if isinstance(col_created_at, datetime):
                                    created_at = str(int(col_created_at.timestamp() * 1000))
                                else:
                                    created_at = str(col_created_at)
                            elif isinstance(props, dict) and props.get("created_at") is not None:
                                created_at = str(props.get("created_at"))

                            # Extract dataset_id from episode properties if available
                            ep_dataset_id = props.get("dataset_id") if isinstance(props, dict) else None

                            all_episodes.append(
                                {
                                    "id": ep_id_str,
                                    "name": ep_name or f"Episode_{ep_id}",
                                    "summary": props.get("summary") if isinstance(props, dict) else None,
                                    "facet_count": facet_count or 0,
                                    "entity_count": entity_count or 0,
                                    "created_at": created_at,
                                    "dataset_id": ep_dataset_id or str(dataset.id),
                                }
                            )
                except Exception as e:
                    _logger.warning(f"Error fetching episodes for dataset {dataset.id}: {e}")
                    continue

            # Apply pagination
            total = len(all_episodes)
            paginated = all_episodes[offset : offset + limit]

            return {
                "episodes": paginated,
                "total": total,
                "limit": limit,
                "offset": offset,
            }

        except HTTPException:
            raise
        except Exception as err:
            _logger.error("Error fetching episodes overview: %s", err)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error retrieving episodes overview: {err}",
            ) from err


def _register_get_entity_network(router: APIRouter) -> None:
    """Register GET /entity/{entity_id}/network endpoint (Phase 0.5)."""

    @router.get("/entity/{entity_id}/network", response_model=EntityNetworkDTO)
    async def get_entity_network(
        entity_id: str,
        dataset_id: Optional[UUID] = Query(
            default=None, description="Dataset UUID. Required in multi-user mode, optional in single-user mode."
        ),
        user: "User" = Depends(_get_auth_user()),
    ):
        """
        Retrieve entity network showing all connected Episodes and Facets.

        This endpoint is used for Layer 3 Entity network view.

        Key features:
        - Returns all Episodes and Facets connected to this entity
        - Permission checking in multi-user mode
        - Returns 404 if entity not found
        """
        from m_flow.adapters.graph import get_graph_provider
        from m_flow.auth.permissions.methods import get_all_user_permission_datasets
        from m_flow.context_global_variables import (
            backend_access_control_enabled,
            set_db_context,
        )

        try:
            # Permission check (same logic as subgraph APIs)
            if backend_access_control_enabled():
                if not dataset_id:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="dataset_id is required in multi-user mode",
                    )

                all_datasets = await get_all_user_permission_datasets(user, "read")
                authorized_dataset = next((ds for ds in all_datasets if ds.id == dataset_id), None)
                if not authorized_dataset:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Dataset {dataset_id} not found or not accessible",
                    )

                await set_db_context(dataset_id, authorized_dataset.owner_id)

            engine = await get_graph_provider()

            # Check if entity node exists
            entity_node = await engine.get_node(entity_id)
            if not entity_node:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Entity {entity_id} not found",
                )

            entity_name = entity_node.get("name", f"Entity_{entity_id}")
            entity_type = entity_node.get("type", "Entity")

            connected_episodes = []
            connected_facets = []
            same_entities = []

            # Use get_edges() to get all connections
            edges = await engine.get_edges(entity_id)

            for src_node, relationship_name, tgt_node in edges:
                src_id = str(src_node.get("id", ""))
                tgt_id = str(tgt_node.get("id", ""))

                # Determine neighbor node
                if src_id == entity_id:
                    neighbor_id = tgt_id
                    neighbor_node = tgt_node
                else:
                    neighbor_id = src_id
                    neighbor_node = src_node

                neighbor_type = neighbor_node.get("type", "Unknown")
                neighbor_name = neighbor_node.get("name", f"{neighbor_type}_{neighbor_id}")

                node_data = {
                    "id": neighbor_id,
                    "name": neighbor_name,
                    "type": neighbor_type,
                    "relationship": relationship_name,
                    "dataset_id": str(dataset_id) if dataset_id else None,
                }

                if neighbor_type == "Episode":
                    connected_episodes.append(node_data)
                elif neighbor_type == "Facet":
                    connected_facets.append(node_data)
                elif relationship_name == "same_entity_as" and neighbor_type in ("Entity", "Entity"):
                    same_entities.append(node_data)

            return {
                "entity_id": entity_id,
                "entity_name": entity_name,
                "entity_type": entity_type,
                "connected_episodes": connected_episodes,
                "connected_facets": connected_facets,
                "same_entities": same_entities,
                "dataset_id": str(dataset_id) if dataset_id else None,
            }

        except HTTPException:
            raise
        except Exception as err:
            _logger.error("Error fetching entity network: %s", err)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error retrieving entity network: {err}",
            ) from err


# ---------------------------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------------------------


def _format_node(node: tuple, dataset_id: Optional[UUID] = None) -> dict:
    """Convert node tuple to dict.

    Args:
        node: Tuple of (node_id, properties)
        dataset_id: Optional dataset UUID for multi-tenant support
    """
    node_id, props = node

    # Determine display name
    name = props.get("name", "")
    node_type = props.get("type", "Unknown")
    display_name = name if name else f"{node_type}_{node_id}"

    # Filter properties
    skip_keys = {"id", "type", "name", "created_at", "updated_at"}
    filtered = {k: v for k, v in props.items() if k not in skip_keys and v is not None}

    result = {
        "id": str(node_id),
        "name": display_name,
        "type": node_type,
        "properties": filtered,
    }

    # Add dataset_id if provided
    if dataset_id is not None:
        result["dataset_id"] = str(dataset_id)

    return result


def _format_edge(edge: tuple) -> dict:
    """Convert edge tuple to edge dict."""
    return {
        "source": str(edge[0]),
        "target": str(edge[1]),
        "relationship": str(edge[2]),
    }


# ---------------------------------------------------------------------------
# Router Factory
# ---------------------------------------------------------------------------


def _register_get_procedures_overview(router: APIRouter) -> None:
    """Register GET /procedures endpoint."""

    @router.get("/procedures")
    async def get_procedures_overview(
        dataset_id: Optional[UUID] = Query(default=None),
        user: "User" = Depends(_get_auth_user()),
    ):
        """Return all Procedure nodes for the overview, with step/context point counts."""
        from m_flow.adapters.graph import get_graph_provider
        from m_flow.auth.permissions.methods import get_all_user_permission_datasets
        from m_flow.context_global_variables import (
            backend_access_control_enabled,
            set_db_context,
        )

        all_datasets = await get_all_user_permission_datasets(user, "read")
        if dataset_id:
            datasets = [ds for ds in all_datasets if ds.id == dataset_id]
        else:
            datasets = all_datasets

        if not backend_access_control_enabled():
            datasets = datasets[:1] if datasets else []

        procedures = []
        seen = set()

        for ds in datasets:
            try:
                await set_db_context(ds.id, ds.owner_id)
                engine = await get_graph_provider()

                cypher = """
                MATCH (p:Node)
                WHERE p.type = 'Procedure'
                OPTIONAL MATCH (p)-[]->(sp:Node)
                WHERE sp.type IN ['ProcedureStepPoint', 'ProcedureContextPoint']
                RETURN p.id, p.name, p.properties, count(sp)
                """
                rows = await engine.query(cypher)
                for row in rows or []:
                    pid = row[0]
                    if pid in seen:
                        continue
                    seen.add(pid)

                    props = {}
                    if row[2]:
                        import json as _json

                        try:
                            props = _json.loads(row[2]) if isinstance(row[2], str) else (row[2] or {})
                        except Exception:
                            props = {}

                    procedures.append(
                        {
                            "id": pid,
                            "name": row[1] or props.get("name", "Procedure"),
                            "type": "Procedure",
                            "search_text": props.get("search_text", ""),
                            "version": props.get("version", 1),
                            "status": props.get("status", "active"),
                            "confidence": props.get("confidence", "high"),
                            "point_count": row[3] if row[3] else 0,
                            "datasetId": str(ds.id),
                        }
                    )
            except Exception:
                continue

        return {"procedures": procedures, "total": len(procedures)}


def _register_get_procedure_subgraph(router: APIRouter) -> None:
    """Register GET /procedure/{procedure_id} endpoint."""

    PROCEDURE_RELS = {"has_key_point", "has_context_point", "supersedes"}

    @router.get("/procedure/{procedure_id}", response_model=GraphDTO)
    async def get_procedure_subgraph(
        procedure_id: str,
        dataset_id: Optional[UUID] = Query(default=None),
        user: "User" = Depends(_get_auth_user()),
    ):
        """Retrieve subgraph for a Procedure node and its children."""
        from m_flow.adapters.graph import get_graph_provider
        from m_flow.auth.permissions.methods import get_all_user_permission_datasets
        from m_flow.context_global_variables import (
            backend_access_control_enabled,
            set_db_context,
        )

        if backend_access_control_enabled():
            all_datasets = await get_all_user_permission_datasets(user, "read")
            if dataset_id:
                authorized = [ds for ds in all_datasets if ds.id == dataset_id]
            else:
                authorized = all_datasets
            if not authorized:
                raise HTTPException(status_code=404, detail="Dataset not found")
            for ds in authorized:
                await set_db_context(ds.id, ds.owner_id)
                break
        else:
            all_datasets = await get_all_user_permission_datasets(user, "read")
            if all_datasets:
                await set_db_context(all_datasets[0].id, all_datasets[0].owner_id)

        engine = await get_graph_provider()

        cypher = """
        MATCH (p:Node)
        WHERE p.id = $pid AND p.type = 'Procedure'
        OPTIONAL MATCH (p)-[r]->(c:Node)
        RETURN p.id, p.name, p.type, p.properties,
               r.relationship_name, c.id, c.name, c.type, c.properties
        """
        rows = await engine.query(cypher, {"pid": procedure_id})

        all_nodes: list = []
        all_edges: list = []
        seen_ids: set = set()
        ds_id = str(dataset_id) if dataset_id else (str(all_datasets[0].id) if all_datasets else None)

        for row in rows or []:
            p_id, p_name, p_type, p_props = row[0], row[1], row[2], row[3]
            rel_name = row[4]
            c_id, c_name, c_type, c_props = row[5], row[6], row[7], row[8]

            if p_id and p_id not in seen_ids:
                seen_ids.add(p_id)
                props = _safe_parse_props(p_props)
                all_nodes.append(
                    GraphNodeDTO(
                        id=p_id,
                        name=p_name or "Procedure",
                        type=p_type or "Procedure",
                        properties=props,
                        datasetId=ds_id,
                    )
                )

            if c_id and rel_name and rel_name in PROCEDURE_RELS and c_id not in seen_ids:
                seen_ids.add(c_id)
                c_props_parsed = _safe_parse_props(c_props)
                all_nodes.append(
                    GraphNodeDTO(
                        id=c_id,
                        name=c_name or c_type or "",
                        type=c_type or "",
                        properties=c_props_parsed,
                        datasetId=ds_id,
                    )
                )
                all_edges.append(GraphEdgeDTO(source=p_id, target=c_id, relationship=rel_name))

        return GraphDTO(nodes=all_nodes, edges=all_edges)


def _safe_parse_props(raw) -> dict:
    """Parse properties JSON safely."""
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str) and raw:
        import json

        try:
            return json.loads(raw)
        except Exception:
            return {}
    return {}


def get_graph_router() -> APIRouter:
    """
    Construct and return the graph API router.

    Registers all graph-related endpoints including:
    - Global graph data retrieval
    - Episode subgraph queries
    - Facet subgraph queries
    - Episodes overview (Phase 0.4)
    - Entity network (Phase 0.5)
    - Procedures overview + subgraph
    """
    router = APIRouter()

    _register_get_global_graph(router)
    _register_get_episode_subgraph(router)
    _register_get_facet_subgraph(router)
    _register_get_episodes_overview(router)
    _register_get_entity_network(router)
    _register_get_procedures_overview(router)
    _register_get_procedure_subgraph(router)

    return router
