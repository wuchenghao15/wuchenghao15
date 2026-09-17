# m_flow/api/v1/manual/manual.py
"""
Manual Episodic Memory Ingestion API

Core logic for manually constructing and ingesting episodic memory structures.
Bypasses the LLM extraction pipeline, allowing users to directly specify
Episode, Facet, FacetPoint, and Entity contents.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, List, Optional
from uuid import UUID

from m_flow.adapters.graph import get_graph_provider
from m_flow.auth.methods import get_seed_user
from m_flow.core import Edge
from m_flow.core.domain.models import (
    Entity,
    Episode,
    Facet,
    FacetPoint,
)  # Entity is new, Entity is alias
from m_flow.core.domain.models.memory_space import MemorySpace
from m_flow.core.domain.utils.generate_node_id import generate_node_id
from m_flow.memory.episodic.edge_text_generators import (
    make_has_facet_edge_text,
    make_has_point_edge_text,
    make_involves_entity_edge_text,
)
from m_flow.shared.logging_utils import get_logger
from m_flow.storage import persist_memory_nodes

from .models import (
    ManualConceptInput,
    ManualEpisodeInput,
    ManualFacetInput,
    ManualFacetPointInput,
    ManualIngestRequest,
    ManualIngestResult,
    PatchNodeRequest,
    PatchNodeResult,
)

if TYPE_CHECKING:
    from m_flow.auth.models import User

_log = get_logger("manual_ingest")


# ============================================================
# Node Construction Helpers
# ============================================================


def _make_aliases_text(aliases: Optional[List[str]], max_chars: int = 400) -> Optional[str]:
    """Concatenate aliases into a single text for indexing."""
    if not aliases:
        return None
    text = "\n".join(a.strip() for a in aliases if a and a.strip())
    return text[:max_chars] if text else None


def _build_facet_point(
    point_input: ManualFacetPointInput,
    facet_id: UUID,
) -> FacetPoint:
    """Build a FacetPoint node from user input."""
    point_id = generate_node_id(f"fp:{facet_id}:{point_input.search_text}")

    return FacetPoint(
        id=point_id,
        name=point_input.search_text,
        search_text=point_input.search_text,
        aliases=point_input.aliases,
        aliases_text=_make_aliases_text(point_input.aliases),
        description=point_input.description,
        display_only=point_input.display_only,
    )


def _build_facet(
    facet_input: ManualFacetInput,
    episode_id: UUID,
    dataset_id: Optional[str] = None,
) -> tuple[Facet, List[FacetPoint]]:
    """Build a Facet node and its FacetPoints from user input."""
    facet_id = generate_node_id(f"facet:{episode_id}:{facet_input.search_text}")

    # Build FacetPoints
    facet_points: List[FacetPoint] = []
    has_point_edges: List[tuple[Edge, FacetPoint]] = []

    if facet_input.points:
        for point_input in facet_input.points:
            point = _build_facet_point(point_input, facet_id)
            facet_points.append(point)

            # Create has_point edge
            edge_text = make_has_point_edge_text(
                facet_type=facet_input.facet_type,
                facet_search_text=facet_input.search_text,
                point_search_text=point.search_text,
                point_description=point.description or "",
            )
            edge = Edge(edge_text=edge_text, relationship_name="has_point")
            has_point_edges.append((edge, point))

    facet = Facet(
        id=facet_id,
        name=facet_input.search_text,
        facet_type=facet_input.facet_type or "chapter",
        search_text=facet_input.search_text,
        aliases=facet_input.aliases,
        aliases_text=_make_aliases_text(facet_input.aliases),
        description=facet_input.description,
        anchor_text=facet_input.anchor_text or facet_input.description,
        display_only=facet_input.display_only,
        has_point=has_point_edges if has_point_edges else None,
        dataset_id=dataset_id,
    )

    return facet, facet_points


def _build_concept(
    entity_input: ManualConceptInput,
    episode_id: UUID,
    memory_type: Optional[str] = None,
) -> Entity:
    """Build a Entity node from user input."""
    # Generate canonical_name if not provided
    canonical = entity_input.canonical_name
    if not canonical:
        canonical = entity_input.name.lower().replace(" ", "_").strip()

    concept_id = generate_node_id(f"concept:{episode_id}:{entity_input.name}")

    return Entity(
        id=concept_id,
        name=entity_input.name,
        description=entity_input.description,
        canonical_name=canonical,
        memory_type=memory_type,
        display_only=entity_input.display_only,
    )


def _build_episode(
    episode_input: ManualEpisodeInput,
    nodeset_name: str = "Episodic",
    dataset_id: Optional[str] = None,
) -> tuple[Episode, List[Facet], List[FacetPoint], List[Entity]]:
    """Build an Episode node with all associated structures from user input.

    Args:
        episode_input: User-provided episode definition
        nodeset_name: Name for the MemorySpace nodeset
        dataset_id: Dataset ID for isolation (prevents cross-dataset merging)
    """
    episode_id = generate_node_id(f"episode:{episode_input.name}:{episode_input.summary[:50]}")

    # Build Facets and FacetPoints
    all_facets: List[Facet] = []
    all_points: List[FacetPoint] = []
    has_facet_edges: List[tuple[Edge, Facet]] = []

    if episode_input.facets:
        for facet_input in episode_input.facets:
            facet, points = _build_facet(facet_input, episode_id, dataset_id=dataset_id)
            all_facets.append(facet)
            all_points.extend(points)

            # Create has_facet edge
            edge_text = make_has_facet_edge_text(
                facet_type=facet_input.facet_type,
                facet_search_text=facet_input.search_text,
                facet_description=facet_input.description or "",
            )
            edge = Edge(edge_text=edge_text, relationship_name="has_facet")
            has_facet_edges.append((edge, facet))

    # Build Concepts/Entities
    all_concepts: List[Entity] = []
    involves_entity_edges: List[tuple[Edge, Entity]] = []

    if episode_input.entities:
        for entity_input in episode_input.entities:
            concept = _build_concept(
                entity_input,
                episode_id,
                memory_type=episode_input.memory_type,
            )
            all_concepts.append(concept)

            # Create involves_entity edge
            edge_text = make_involves_entity_edge_text(
                entity=concept,
                context_description=entity_input.description,
            )
            edge = Edge(edge_text=edge_text, relationship_name="involves_entity")
            involves_entity_edges.append((edge, concept))

    # Build MemorySpace for nodeset
    nodeset = MemorySpace(
        id=generate_node_id(f"nodeset:{nodeset_name}"),
        name=nodeset_name,
    )

    # Build Episode
    episode = Episode(
        id=episode_id,
        name=episode_input.name,
        summary=episode_input.summary,
        signature=episode_input.signature,
        status=episode_input.status or "open",
        memory_type=episode_input.memory_type or "episodic",
        display_only=episode_input.display_only,
        has_facet=has_facet_edges if has_facet_edges else None,
        involves_entity=involves_entity_edges if involves_entity_edges else None,
        memory_spaces=[nodeset],
        dataset_id=dataset_id,
    )

    # Set memory_spaces for all child nodes
    for facet in all_facets:
        facet.memory_spaces = [nodeset]
    for point in all_points:
        point.memory_spaces = [nodeset]
    for concept in all_concepts:
        concept.memory_spaces = [nodeset]

    return episode, all_facets, all_points, all_concepts


# ============================================================
# Public API: Manual Ingest
# ============================================================


async def manual_ingest(
    request: ManualIngestRequest,
    user: "User | None" = None,
) -> ManualIngestResult:
    """
    Manually ingest episodic memory structures.

    Bypasses the LLM extraction pipeline. Users directly specify
    Episode, Facet, FacetPoint, and Entity contents, which are then
    embedded and stored in the graph and vector databases.

    Args:
        request: ManualIngestRequest containing episodes to ingest.
        user: Optional user context (for future access control).

    Returns:
        ManualIngestResult with counts of created nodes.

    Example:
        >>> request = ManualIngestRequest(
        ...     episodes=[
        ...         ManualEpisodeInput(
        ...             name="Project Meeting 2026-02-23",
        ...             summary="Discussed Q1 product roadmap and technical solutions",
        ...             facets=[
        ...                 ManualFacetInput(
        ...                     facet_type="decision",
        ...                     search_text="Adopt microservices architecture",
        ...                     description="Decided to adopt microservices for horizontal scaling",
        ...                 )
        ...             ],
        ...             entities=[
        ...                 ManualConceptInput(
        ...                     name="John",
        ...                     description="Tech Lead, leading architecture design",
        ...                 )
        ...             ],
        ...         )
        ...     ],
        ... )
        >>> result = await manual_ingest(request)
    """
    _log.info(f"[manual_ingest] Starting manual ingestion of {len(request.episodes)} episodes")

    # === Resolve dataset, grant permissions, and set DB context ===
    dataset_id: Optional[str] = None
    active_user = user
    if active_user is None:
        try:
            active_user = await get_seed_user()
        except Exception as e:
            _log.debug("Failed to get default user: %s", e)

    if active_user is not None and request.dataset_name:
        try:
            from m_flow.data.methods.create_authorized_dataset import create_authorized_dataset
            from m_flow.context_global_variables import (
                current_dataset_id,
                set_db_context,
            )

            # Step 1: Ensure Dataset record exists + user has full permissions.
            # Idempotent: returns existing dataset if found.
            dataset = await create_authorized_dataset(request.dataset_name, active_user)
            dataset_id = str(dataset.id)

            # Step 2: Set Episode Routing isolation (works regardless of ACL).
            current_dataset_id.set(dataset_id)

            # Step 3: Set graph/vector DB context for per-dataset storage isolation.
            # Pass dataset_name as STRING so get_or_create_dataset_database provisions
            # DatasetStore with graph/vector bindings if needed.
            # When ACL is disabled, this is a safe no-op.
            await set_db_context(
                request.dataset_name,
                active_user.id,
            )
            _log.info(
                "[manual_ingest] Dataset created & DB context set: %s (id=%s)",
                request.dataset_name,
                dataset_id,
            )
        except Exception as e:
            _log.warning("[manual_ingest] Could not set DB context: %s, using global DB", e)

    errors: List[str] = []
    all_memory_nodes = []

    episode_count = 0
    facet_count = 0
    point_count = 0
    entity_count = 0

    try:
        # Step 1: Build all nodes first (validation)
        # This ensures atomicity: either all episodes are valid, or none are written
        for ep_input in request.episodes:
            try:
                episode, facets, points, concepts = _build_episode(ep_input, dataset_id=dataset_id)

                # Collect all nodes
                all_memory_nodes.append(episode)
                all_memory_nodes.extend(facets)
                all_memory_nodes.extend(points)
                all_memory_nodes.extend(concepts)

                episode_count += 1
                facet_count += len(facets)
                point_count += len(points)
                entity_count += len(concepts)

            except Exception as e:
                error_msg = f"Failed to build episode '{ep_input.name}': {str(e)}"
                _log.error(f"[manual_ingest] {error_msg}")
                errors.append(error_msg)

        # Step 2: Atomicity check - if any episode failed to build, abort entirely
        # This prevents partial writes that could lead to data inconsistency
        if errors:
            _log.warning(
                f"[manual_ingest] Aborting: {len(errors)} episode(s) failed validation. "
                f"No data will be written to ensure consistency."
            )
            return ManualIngestResult(
                success=False,
                episodes_created=0,  # Nothing written
                facets_created=0,
                facet_points_created=0,
                entities_created=0,
                errors=errors,
            )

        # Step 3: All episodes validated, proceed with persistence
        if all_memory_nodes:
            _log.info(
                f"[manual_ingest] Built {len(all_memory_nodes)} nodes: "
                f"{episode_count} episodes, {facet_count} facets, "
                f"{point_count} points, {entity_count} entities"
            )

            # Persist to graph and vector databases
            await persist_memory_nodes(
                all_memory_nodes,
                embed_triplets=request.embed_triplets,
            )

            _log.info("[manual_ingest] Successfully persisted all nodes")

        return ManualIngestResult(
            success=True,
            episodes_created=episode_count,
            facets_created=facet_count,
            facet_points_created=point_count,
            entities_created=entity_count,
            errors=None,
        )

    except Exception as e:
        _log.error(f"[manual_ingest] Critical error during persistence: {str(e)}")
        return ManualIngestResult(
            success=False,
            episodes_created=0,  # Persistence failed, counts are unreliable
            facets_created=0,
            facet_points_created=0,
            entities_created=0,
            errors=[f"Critical error during persistence: {str(e)}"],
        )


# ============================================================
# Public API: Patch Node
# ============================================================


# Node type mapping for reconstruction
_NODE_TYPE_MAP = {
    "episode": Episode,
    "facet": Facet,
    "facetpoint": FacetPoint,
    "concept": Entity,
}


def _reconstruct_node_from_props(node_type: str, props: dict) -> "Episode | Facet | FacetPoint | Entity | None":
    """
    Reconstruct a MemoryNode from graph database properties.

    Uses a safe approach that only sets fields that exist in the model.
    Handles JSON-serialized fields (like aliases list) appropriately.

    Supports all graph databases (Neo4j, Kuzu, Neptune) by normalizing
    their different property storage formats.
    """
    import json
    from uuid import UUID

    type_key = node_type.lower().replace("_", "")
    node_cls = _NODE_TYPE_MAP.get(type_key)

    if not node_cls:
        _log.warning(f"[patch_node] Unknown node type: {node_type}")
        return None

    # Get model field names and required fields
    model_fields = set(node_cls.model_fields.keys())
    required_fields = {name for name, field_info in node_cls.model_fields.items() if field_info.is_required()}

    # Filter props to only include fields that exist in the model
    filtered_props = {}
    for key, value in props.items():
        if key in model_fields:
            # Handle JSON-serialized fields (common in Kuzu properties column)
            if isinstance(value, str) and key in ("aliases", "metadata", "memory_spaces"):
                try:
                    value = json.loads(value)
                except (json.JSONDecodeError, TypeError):
                    pass
            # Handle UUID fields
            if key == "id" and isinstance(value, str):
                try:
                    value = UUID(value)
                except ValueError:
                    pass
            filtered_props[key] = value

    # Ensure required fields have values
    if "id" not in filtered_props:
        _log.error("[patch_node] Node props missing 'id' field")
        return None

    # Provide sensible defaults for required string fields that may be missing
    # This handles cases where the database doesn't store all required fields
    required_str_defaults = {
        "name": str(filtered_props["id"]),
        "summary": "",  # Episode required field
        "search_text": "",  # Facet/FacetPoint required field
        "facet_type": "unknown",  # Facet required field
        "description": "",  # Entity required field
    }

    for field in required_fields:
        if field not in filtered_props:
            if field in required_str_defaults:
                filtered_props[field] = required_str_defaults[field]
                _log.debug(f"[patch_node] Using default for missing required field: {field}")

    try:
        return node_cls(**filtered_props)
    except Exception as e:
        _log.error(f"[patch_node] Failed to reconstruct {node_type}: {e}")
        return None


async def patch_node(
    request: PatchNodeRequest,
    user: "User | None" = None,
) -> PatchNodeResult:
    """
    Update specific fields of an existing node.

    Currently supports updating the display_only field.
    The node must exist in the graph database.

    Uses a safe read-modify-write pattern that works across all
    supported graph databases (Neo4j, Kuzu, Neptune).

    Args:
        request: PatchNodeRequest with node_id, node_type, and new values.
        user: Optional user context (for future access control).

    Returns:
        PatchNodeResult indicating success or failure.

    Example:
        >>> result = await patch_node(PatchNodeRequest(
        ...     node_id=uuid,
        ...     node_type="Episode",
        ...     display_only="Important meeting notes",
        ... ))
    """
    _log.info(f"[patch_node] Updating node {request.node_id} ({request.node_type})")

    graph_engine = await get_graph_provider()
    node_id_str = str(request.node_id)

    try:
        # Step 1: Read - Get existing node
        existing = await graph_engine.get_node(node_id_str)
        if not existing:
            return PatchNodeResult(
                success=False,
                node_id=request.node_id,
                node_type=request.node_type,
                message=f"Node {node_id_str} not found.",
            )

        _log.debug(f"[patch_node] Found existing node: {existing.get('type', 'unknown')}")

        # Step 2: Modify - Reconstruct node and update display_only
        # Determine the display_only value
        display_only_value = request.display_only
        if display_only_value == "":
            display_only_value = None  # Clear the field

        # Detect node type from stored data if available
        detected_type = existing.get("type", request.node_type)

        # Reconstruct the node object
        reconstructed = _reconstruct_node_from_props(detected_type, existing)
        if not reconstructed:
            # Fallback: try with user-provided type
            reconstructed = _reconstruct_node_from_props(request.node_type, existing)

        if not reconstructed:
            return PatchNodeResult(
                success=False,
                node_id=request.node_id,
                node_type=request.node_type,
                message=f"Failed to reconstruct node. Type '{detected_type}' may not be supported for patching.",
            )

        # Update the display_only field
        reconstructed.display_only = display_only_value

        # Step 3: Write - Use add_node to update (MERGE ON MATCH SET)
        # This leverages the existing, well-tested upsert mechanism
        await graph_engine.add_node(reconstructed)

        _log.info(f"[patch_node] Successfully updated node {node_id_str}")
        return PatchNodeResult(
            success=True,
            node_id=request.node_id,
            node_type=request.node_type,
            message="Node updated successfully.",
        )

    except Exception as e:
        _log.error(f"[patch_node] Error updating node: {str(e)}")
        return PatchNodeResult(
            success=False,
            node_id=request.node_id,
            node_type=request.node_type,
            message=f"Error: {str(e)}",
        )


# ============================================================
# Convenience Functions
# ============================================================


async def manual_add_episode(
    name: str,
    summary: str,
    facets: Optional[List[dict]] = None,
    entities: Optional[List[dict]] = None,
    signature: Optional[str] = None,
    status: str = "open",
    memory_type: str = "episodic",
    display_only: Optional[str] = None,
    dataset_name: str = "main_dataset",
    embed_triplets: bool = False,
) -> ManualIngestResult:
    """
    Convenience function to manually add a single episode.

    Args:
        name: Episode title.
        summary: Episode summary (main content, will be indexed).
        facets: List of facet dicts with keys: facet_type, search_text, description, etc.
        entities: List of entity dicts with keys: name, description, canonical_name, etc.
        signature: Optional short handle.
        status: Status marker (default: "open").
        memory_type: "episodic" or "atomic" (default: "episodic").
        display_only: Display-only content (not indexed).
        dataset_name: Target dataset name.
        embed_triplets: Whether to create triplet embeddings.

    Returns:
        ManualIngestResult with operation details.
    """
    # Build facet inputs
    facet_inputs = None
    if facets:
        facet_inputs = [ManualFacetInput(**f) for f in facets]

    # Build entity inputs
    entity_inputs = None
    if entities:
        entity_inputs = [ManualConceptInput(**e) for e in entities]

    episode_input = ManualEpisodeInput(
        name=name,
        summary=summary,
        signature=signature,
        status=status,
        memory_type=memory_type,
        display_only=display_only,
        facets=facet_inputs,
        entities=entity_inputs,
    )

    request = ManualIngestRequest(
        episodes=[episode_input],
        dataset_name=dataset_name,
        embed_triplets=embed_triplets,
    )

    return await manual_ingest(request)
