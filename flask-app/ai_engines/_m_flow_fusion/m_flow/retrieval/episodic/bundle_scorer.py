"""
EpisodeBundle scoring module

Responsible for:
- Building relationship index (Episode-Facet-Point-Entity)
- Computing node/edge path costs
- Episode ranking (Bundle scoring)
"""

import math
from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Tuple

from m_flow.knowledge.graph_ops.m_flow_graph.MemoryGraph import MemoryGraph
from m_flow.knowledge.graph_ops.m_flow_graph.MemoryGraphElements import Edge

from .config import EpisodicConfig


@dataclass
class EpisodeBundle:
    """Episode retrieval result unit"""

    episode_id: str
    score: float
    best_path: str  # "direct_episode" | "facet" | "point" | "entity" | "facet_entity"
    best_support_id: Optional[str] = None
    best_facet_id: Optional[str] = None
    best_point_id: Optional[str] = None
    best_entity_id: Optional[str] = None


@dataclass
class RelationshipIndex:
    """Graph relationship index"""

    episode_ids: Set[str]
    facet_ids: Set[str]
    point_ids: Set[str]
    entity_ids: Set[str]

    # Edges lookup
    ep_facet_edge: Dict[Tuple[str, str], Edge]
    facet_point_edge: Dict[Tuple[str, str], Edge]
    ep_entity_edge: Dict[Tuple[str, str], Edge]
    facet_entity_edge: Dict[Tuple[str, str], Edge]  # NEW: Facet → Entity

    # Adjacency
    facets_by_episode: Dict[str, Set[str]]
    points_by_facet: Dict[str, Set[str]]
    entities_by_episode: Dict[str, Set[str]]
    entities_by_facet: Dict[str, Set[str]]  # NEW: Facet → Entity adjacency


def build_relationship_index(memory_fragment: MemoryGraph) -> RelationshipIndex:
    """
    Build graph relationship index.

    Args:
        memory_fragment: Projected subgraph

    Returns:
        RelationshipIndex: Relationship index
    """
    index = RelationshipIndex(
        episode_ids=set(),
        facet_ids=set(),
        point_ids=set(),
        entity_ids=set(),
        ep_facet_edge={},
        facet_point_edge={},
        ep_entity_edge={},
        facet_entity_edge={},  # NEW
        facets_by_episode={},
        points_by_facet={},
        entities_by_episode={},
        entities_by_facet={},  # NEW
    )

    for e in memory_fragment.edges:
        rel = get_edge_relationship(e)
        t1 = e.node1.attributes.get("type", "")
        t2 = e.node2.attributes.get("type", "")
        id1 = str(e.node1.id)
        id2 = str(e.node2.id)

        if rel == "has_facet":
            if t1 == "Episode" and t2 == "Facet":
                ep, fa = id1, id2
            elif t2 == "Episode" and t1 == "Facet":
                ep, fa = id2, id1
            else:
                continue
            index.episode_ids.add(ep)
            index.facet_ids.add(fa)
            index.facets_by_episode.setdefault(ep, set()).add(fa)
            index.ep_facet_edge[(ep, fa)] = e

        elif rel == "has_point":
            if t1 == "Facet" and t2 == "FacetPoint":
                fa, pt = id1, id2
            elif t2 == "Facet" and t1 == "FacetPoint":
                fa, pt = id2, id1
            else:
                continue
            index.facet_ids.add(fa)
            index.point_ids.add(pt)
            index.points_by_facet.setdefault(fa, set()).add(pt)
            index.facet_point_edge[(fa, pt)] = e

        elif rel == "involves_entity":
            # Handle both Episode → Entity and Facet → Entity edges
            # Support both "Entity" (new) and "Entity" (legacy) type values
            if t1 == "Episode" and t2 in ("Entity", "Entity"):
                ep, en = id1, id2
                index.episode_ids.add(ep)
                index.entity_ids.add(en)
                index.entities_by_episode.setdefault(ep, set()).add(en)
                index.ep_entity_edge[(ep, en)] = e
            elif t2 == "Episode" and t1 in ("Entity", "Entity"):
                ep, en = id2, id1
                index.episode_ids.add(ep)
                index.entity_ids.add(en)
                index.entities_by_episode.setdefault(ep, set()).add(en)
                index.ep_entity_edge[(ep, en)] = e
            elif t1 == "Facet" and t2 in ("Entity", "Entity"):
                # Facet → Entity edge
                fa, en = id1, id2
                index.facet_ids.add(fa)
                index.entity_ids.add(en)
                index.entities_by_facet.setdefault(fa, set()).add(en)
                index.facet_entity_edge[(fa, en)] = e
            elif t2 == "Facet" and t1 in ("Entity", "Entity"):
                # Facet → Entity edge (reversed)
                fa, en = id2, id1
                index.facet_ids.add(fa)
                index.entity_ids.add(en)
                index.entities_by_facet.setdefault(fa, set()).add(en)
                index.facet_entity_edge[(fa, en)] = e

    return index


def compute_episode_bundles(
    index: RelationshipIndex,
    best_by_id: Dict[str, float],
    edge_hit_map: Dict[str, float],
    config: EpisodicConfig,
) -> List[EpisodeBundle]:
    """
    Compute Bundle scores for all Episodes.

    Args:
        index: Relationship index
        best_by_id: Node vector distances
        edge_hit_map: Edge vector distances
        config: Configuration

    Returns:
        List[EpisodeBundle]: Bundle list before sorting
    """
    INF = float("inf")

    def direct_cost(nid: str) -> float:
        return float(best_by_id.get(nid, INF))

    def edge_cost(edge_obj: Edge) -> float:
        key = _get_edge_key_for_embedding(edge_obj)
        if key and key in edge_hit_map:
            return float(edge_hit_map[key])
        return float(config.edge_miss_cost)

    # Compute node direct costs
    point_direct = {pid: direct_cost(pid) for pid in index.point_ids}
    facet_direct = {fid: direct_cost(fid) for fid in index.facet_ids}
    episode_direct = {eid: direct_cost(eid) for eid in index.episode_ids}
    entity_direct = {eid: direct_cost(eid) for eid in index.entity_ids}

    # Facet cost: min(direct hit, propagated via Point, propagated via Entity)
    facet_cost: Dict[str, float] = {}
    facet_best_from: Dict[str, Tuple[str, str, float]] = {}

    for fid in index.facet_ids:
        best = facet_direct.get(fid, INF)
        facet_best_from[fid] = ("direct", fid, best)

        # Via FacetPoint
        for pid in index.points_by_facet.get(fid, set()):
            pd = point_direct.get(pid, INF)
            if math.isinf(pd):
                continue
            eobj = index.facet_point_edge.get((fid, pid))
            if not eobj:
                continue
            c = pd + edge_cost(eobj) + config.hop_cost
            if c < best:
                best = c
                facet_best_from[fid] = ("point", pid, c)

        # Via Entity (NEW: Facet → Entity path)
        for en in index.entities_by_facet.get(fid, set()):
            ed = entity_direct.get(en, INF)
            if math.isinf(ed):
                continue
            eobj = index.facet_entity_edge.get((fid, en))
            if not eobj:
                continue
            c = ed + edge_cost(eobj) + config.hop_cost
            if c < best:
                best = c
                facet_best_from[fid] = ("facet_entity", en, c)

        facet_cost[fid] = best

    # Episode cost: min(direct hit, via Facet, via Entity)
    bundles: List[EpisodeBundle] = []

    for ep in index.episode_ids:
        raw_direct = episode_direct.get(ep, INF)
        best = raw_direct + config.direct_episode_penalty if not math.isinf(raw_direct) else INF
        best_path = "direct_episode"
        best_support = ep
        best_facet_id: Optional[str] = None
        best_point_id: Optional[str] = None
        best_entity_id: Optional[str] = None

        # via facet (includes paths: direct → facet, point → facet, entity → facet)
        for fid in index.facets_by_episode.get(ep, set()):
            fc = facet_cost.get(fid, INF)
            if math.isinf(fc):
                continue
            eobj = index.ep_facet_edge.get((ep, fid))
            if not eobj:
                continue

            # Facet direct match discount
            facet_direct_score = facet_direct.get(fid, INF)
            if facet_direct_score < 0.1:
                effective_edge_cost = 0.1
                effective_hop_cost = 0.05
            elif facet_direct_score < 0.2:
                effective_edge_cost = edge_cost(eobj) * 0.3
                effective_hop_cost = config.hop_cost * 0.3
            else:
                effective_edge_cost = edge_cost(eobj)
                effective_hop_cost = config.hop_cost

            c = fc + effective_edge_cost + effective_hop_cost
            if c < best:
                best = c
                src_kind, src_id, _ = facet_best_from.get(fid, ("direct", fid, fc))
                # Determine path type based on how facet was reached
                if src_kind == "point":
                    best_path = "point"
                    best_support = src_id
                    best_point_id = src_id
                    best_entity_id = None
                elif src_kind == "facet_entity":
                    # NEW: Entity → Facet → Episode path
                    best_path = "facet_entity"
                    best_support = src_id  # Entity ID
                    best_point_id = None
                    best_entity_id = src_id
                else:
                    best_path = "facet"
                    best_support = fid
                    best_point_id = None
                    best_entity_id = None
                best_facet_id = fid

        # via entity
        for en in index.entities_by_episode.get(ep, set()):
            ed = entity_direct.get(en, INF)
            if math.isinf(ed):
                continue
            eobj = index.ep_entity_edge.get((ep, en))
            if not eobj:
                continue
            c = ed + edge_cost(eobj) + config.hop_cost
            if c < best:
                best = c
                best_path = "entity"
                best_support = en
                best_facet_id = None
                best_point_id = None
                best_entity_id = en

        if not math.isinf(best):
            bundles.append(
                EpisodeBundle(
                    episode_id=ep,
                    score=best,
                    best_path=best_path,
                    best_support_id=best_support,
                    best_facet_id=best_facet_id,
                    best_point_id=best_point_id,
                    best_entity_id=best_entity_id,
                )
            )

    return bundles


def get_edge_relationship(edge: Edge) -> str:
    """Get edge relationship name"""
    return edge.attributes.get("relationship_name") or edge.attributes.get("relationship_type") or ""


# Backward compatibility alias
_get_edge_relationship = get_edge_relationship


def _get_edge_key_for_embedding(edge: Edge) -> str:
    """Get edge embedding key"""
    return (
        edge.attributes.get("edge_text")
        or edge.attributes.get("relationship_type")
        or edge.attributes.get("relationship_name")
        or ""
    )
