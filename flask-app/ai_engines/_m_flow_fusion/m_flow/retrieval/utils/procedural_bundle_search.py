"""
Procedural Bundle Search (v2 - simplified triplet architecture).

Retrieval triplet: (Procedure → edge_text → Point)
- No intermediate Pack nodes
- 1-hop scoring: point_direct + edge_cost + hop
- 2-phase graph projection (no Stage B / skeleton forcing)
- Backward compatible with old Pack-based data (legacy expansion)

Collections:
- Procedure_summary: coarse-grained anchor
- ProcedureStepPoint_search_text: fine-grained key points
- ProcedureContextPoint_search_text: fine-grained context points
- RelationType_relationship_name: edge text retrieval
"""

import asyncio
import heapq
import math
import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Tuple

from m_flow.retrieval.time.query_time_parser import parse_query_time, QueryTimeInfo
from m_flow.retrieval.time.time_bonus import compute_time_match, TimeBonusConfig

from m_flow.shared.logging_utils import get_logger, ERROR
from m_flow.shared.tracing import TraceManager
from m_flow.knowledge.graph_ops.exceptions.exceptions import ConceptNotFoundError
from m_flow.adapters.vector.exceptions import CollectionNotFoundError
from m_flow.adapters.vector import get_vector_provider

from m_flow.knowledge.graph_ops.m_flow_graph.MemoryGraphElements import Edge

from m_flow.retrieval.utils.procedural_memory_fragment import get_procedural_memory_fragment

logger = get_logger(level=ERROR)


# ─────────────────────────────────────────────
# Query preprocessing
# ─────────────────────────────────────────────

_STRIP_WORDS = [
    "是什么",
    "是啥",
    "什么是",
    "啥是",
    "怎么做",
    "怎样做",
    "如何做",
    "为什么",
    "为啥",
    "怎么",
    "怎样",
    "如何",
    "吗",
    "呢",
    "？",
    "?",
]


def _strip_question_words(query: str) -> str:
    out = query
    for w in _STRIP_WORDS:
        out = out.replace(w, "")
    return out.strip()


def _should_use_hybrid(query: str, threshold: int = 3) -> bool:
    if bool(re.search(r"\d", query)):
        return True
    if bool(re.search(r"[\u4e00-\u9fff]", query)) and bool(re.search(r"[A-Za-z]", query)):
        return True
    core = _strip_question_words(query)
    core = re.sub(r"[\s，,。.；;：:！!]+", "", core)
    return len(core) <= threshold


def _keyword_bonus(keyword: str, text: str) -> float:
    k = re.sub(r"[\s，,。.；;：:！!]+", "", (keyword or "").lower())
    t = re.sub(r"[\s，,。.；;：:！!]+", "", (text or "").lower())
    if not k:
        return 0.0
    return -0.12 if k in t else 0.0


def _exact_bonus(query: str, node_text: str) -> float:
    if not query or not node_text:
        return 0.0
    bonus = 0.0
    # Number match
    q_nums = re.findall(r"\d+\.?\d*", query)
    if q_nums:
        hit = sum(1 for n in q_nums if n in node_text)
        bonus -= min(0.10 * hit, 0.20)
    # English term match
    if bool(re.search(r"[\u4e00-\u9fff]", query)):
        q_en = {m.lower() for m in re.findall(r"[A-Za-z][A-Za-z0-9\-]*[A-Za-z0-9]|[A-Za-z]{2,}", query)}
        if q_en:
            n_en = {m.lower() for m in re.findall(r"[A-Za-z][A-Za-z0-9\-]*[A-Za-z0-9]|[A-Za-z]{2,}", node_text)}
            bonus -= min(0.08 * len(q_en & n_en), 0.16)
    return bonus


def _apply_bonuses(query: str, keyword: str, scored_results: list, use_hybrid: bool) -> None:
    for r in scored_results or []:
        try:
            txt = str((getattr(r, "payload", {}) or {}).get("text", "") or "")
            if not txt:
                continue
            base = float(getattr(r, "score", 1.0))
            b = _exact_bonus(query, txt) + (_keyword_bonus(keyword, txt) if use_hybrid else 0.0)
            if b < 0 and base >= 0.1:
                r.score = max(0.0, base + b)
        except Exception:
            continue


# ─────────────────────────────────────────────
# Graph helpers
# ─────────────────────────────────────────────


def _node_type(n) -> str:
    return (n.attributes.get("type") or "").strip()


def _edge_text(e: Edge) -> str:
    return (
        e.attributes.get("edge_text")
        or e.attributes.get("relationship_type")
        or e.attributes.get("relationship_name")
        or ""
    )


def _best_node_distances(node_distances: Dict[str, list]) -> Dict[str, float]:
    best: Dict[str, float] = {}
    for col, scored in (node_distances or {}).items():
        if col == "RelationType_relationship_name":
            continue
        for r in scored or []:
            rid = str(getattr(r, "id", "") or "")
            if not rid:
                continue
            s = float(getattr(r, "score", 1.0))
            prev = best.get(rid)
            best[rid] = s if prev is None else min(prev, s)
    return best


# ─────────────────────────────────────────────
# Edge classification (new + legacy)
# ─────────────────────────────────────────────


def _classify_edge(e: Edge) -> str:
    t1 = _node_type(e.node1)
    t2 = _node_type(e.node2)
    pair = {t1, t2}

    # New structure: Procedure direct to Point
    if "Procedure" in pair and "ProcedureStepPoint" in pair:
        return "proc_key_point"
    if "Procedure" in pair and "ProcedureContextPoint" in pair:
        return "proc_ctx_point"

    # Legacy: Pack-based structure
    if "Procedure" in pair and "ProcedureStepsPack" in pair:
        return "legacy_proc_pack"
    if "Procedure" in pair and "ProcedureContextPack" in pair:
        return "legacy_proc_pack"
    if "ProcedureStepsPack" in pair and "ProcedureStepPoint" in pair:
        return "legacy_pack_point"
    if "ProcedureContextPack" in pair and "ProcedureContextPoint" in pair:
        return "legacy_pack_point"

    return "other"


# ─────────────────────────────────────────────
# Bundle dataclass
# ─────────────────────────────────────────────


@dataclass
class ProcedureBundle:
    """Procedural bundle with best path tracking."""

    procedure_id: str
    score: float
    best_path: str  # "direct_procedure" | "key_point" | "context_point"
    best_point_id: Optional[str] = None


# ─────────────────────────────────────────────
# Main search function
# ─────────────────────────────────────────────


async def procedural_bundle_search(
    query: str,
    top_k: int = 5,
    collections: Optional[List[str]] = None,
    procedural_nodeset_name: str = "Procedural",
    properties_to_project: Optional[List[str]] = None,
    wide_search_top_k: int = 100,
    max_relevant_ids: int = 300,
    strict_nodeset_filtering: bool = True,
    triplet_distance_penalty: float = 3.5,
    edge_miss_cost: float = 0.9,
    hop_cost: float = 0.1,
    direct_procedure_penalty: float = 0.3,
    inactive_penalty: float = 0.4,
    return_bundles: bool = False,
    # Time enhancement
    enable_time_bonus: bool = True,
    time_bonus_max: float = 0.06,
    time_score_floor: float = 0.08,
    time_conf_min: float = 0.4,
    # Legacy compatibility (ignored, kept for signature compat)
    max_step_points_per_procedure: int = 0,
    max_context_points_per_procedure: int = 0,
    fallback_full_nodeset_if_skeleton_missing: bool = True,
):
    """
    Procedural bundle search (v2 - simplified triplet).

    Retrieval triplet: (Procedure → edge_text → Point)
    Scoring: 1-hop from Point to Procedure.
    Backward compatible with old Pack-based data.
    """
    if not query or not isinstance(query, str):
        raise ValueError("query must be a non-empty string")
    if top_k <= 0:
        raise ValueError("top_k must be positive")

    TraceManager.event(
        "procedural.search.start",
        {
            "query": query[:100],
            "top_k": top_k,
        },
    )

    if collections is None:
        collections = [
            "Procedure_summary",
            "ProcedureStepPoint_search_text",
            "ProcedureContextPoint_search_text",
        ]
    if "RelationType_relationship_name" not in collections:
        collections.append("RelationType_relationship_name")

    vector_engine = get_vector_provider()

    # ── Query preprocessing ──
    original_query = query
    time_info: Optional[QueryTimeInfo] = None
    if enable_time_bonus:
        time_info = parse_query_time(query)
        if time_info.query_wo_time:
            query = time_info.query_wo_time

    vector_query = _strip_question_words(query) or query
    use_hybrid = _should_use_hybrid(query, threshold=3)
    keyword = re.sub(r"[\s，,。.；;：:！!]+", "", _strip_question_words(query))

    query_vector = (await vector_engine.embedding_engine.embed_text([vector_query]))[0]

    # ── Vector search ──
    async def search_col(col: str):
        try:
            return await vector_engine.search(
                collection_name=col,
                query_vector=query_vector,
                limit=wide_search_top_k,
            )
        except (CollectionNotFoundError, Exception):
            return []

    try:
        results = await asyncio.gather(*[search_col(c) for c in collections])
        if all(not r for r in results):
            return ([], []) if return_bundles else []

        node_distances: Dict[str, list] = {c: r for c, r in zip(collections, results)}
        edge_distances = node_distances.get("RelationType_relationship_name")

        # Apply bonuses
        for col, scored in node_distances.items():
            if col != "RelationType_relationship_name":
                _apply_bonuses(original_query, keyword, scored, use_hybrid)

        best_by_id = _best_node_distances(node_distances)

        # Collect hit IDs
        all_hit_ids = {
            str(getattr(r, "id"))
            for col, scored in node_distances.items()
            if col != "RelationType_relationship_name"
            for r in (scored or [])
            if getattr(r, "id", None)
        }
        relevant_ids = sorted(all_hit_ids, key=lambda nid: best_by_id.get(nid, float("inf")))
        if max_relevant_ids and len(relevant_ids) > max_relevant_ids:
            relevant_ids = relevant_ids[:max_relevant_ids]

        # ── Two-phase graph projection ──
        frag1 = await get_procedural_memory_fragment(
            procedural_nodeset_name=procedural_nodeset_name,
            properties_to_project=properties_to_project,
            relevant_ids_to_filter=relevant_ids if relevant_ids else None,
            triplet_distance_penalty=triplet_distance_penalty,
            strict_nodeset_filtering=strict_nodeset_filtering,
        )

        if relevant_ids and frag1 and frag1.nodes:
            # Step 2: expand neighbors
            ids_1_set = set(relevant_ids)
            neighbor_ids = [nid for nid in frag1.nodes.keys() if nid not in ids_1_set]
            TYPE_PRIO = {
                "Procedure": 0,
                "ProcedureStepPoint": 1,
                "ProcedureContextPoint": 1,
                "ProcedureStepsPack": 2,
                "ProcedureContextPack": 2,
            }

            def nkey(nid):
                n = frag1.nodes.get(nid)
                t = (n.attributes.get("type") if n else "") or ""
                return (TYPE_PRIO.get(t, 9), best_by_id.get(nid, float("inf")))

            neighbor_ids.sort(key=nkey)
            ids_2 = list(relevant_ids) + neighbor_ids
            max_expanded = max_relevant_ids * 2 if max_relevant_ids else None
            if max_expanded and len(ids_2) > max_expanded:
                ids_2 = ids_2[:max_expanded]

            frag2 = await get_procedural_memory_fragment(
                procedural_nodeset_name=procedural_nodeset_name,
                properties_to_project=properties_to_project,
                relevant_ids_to_filter=ids_2,
                triplet_distance_penalty=triplet_distance_penalty,
                strict_nodeset_filtering=strict_nodeset_filtering,
            )
            memory_fragment = frag2 if (frag2 and frag2.edges) else frag1
        else:
            memory_fragment = frag1

        if not memory_fragment or not memory_fragment.edges:
            return ([], []) if return_bundles else []

        # ── Edge hit map ──
        edge_hit_map: Dict[str, float] = {}
        if edge_distances:
            for r in edge_distances:
                try:
                    txt = str((getattr(r, "payload", {}) or {}).get("text", "") or "")
                    if txt:
                        s = float(getattr(r, "score", 1.0))
                        prev = edge_hit_map.get(txt)
                        edge_hit_map[txt] = s if prev is None else min(prev, s)
                except Exception:
                    continue

        INF = float("inf")

        def direct_cost(nid: str) -> float:
            return float(best_by_id.get(nid, INF))

        def edge_cost(e: Edge) -> float:
            k = _edge_text(e)
            return float(edge_hit_map.get(k, edge_miss_cost)) if k else float(edge_miss_cost)

        # ── Build adjacency (new + legacy) ──
        proc_ids: Set[str] = set()
        key_points_by_proc: Dict[str, Set[str]] = {}
        ctx_points_by_proc: Dict[str, Set[str]] = {}
        proc_point_edge: Dict[Tuple[str, str], Edge] = {}

        # Legacy intermediate
        proc_to_packs: Dict[str, Set[str]] = {}
        pack_to_points: Dict[str, Set[str]] = {}
        legacy_pack_point_edge: Dict[Tuple[str, str], Edge] = {}
        pack_is_steps: Dict[str, bool] = {}  # True=steps, False=context

        for e in memory_fragment.edges:
            kind = _classify_edge(e)
            id1, id2 = str(e.node1.id), str(e.node2.id)
            t1, t2 = _node_type(e.node1), _node_type(e.node2)

            if kind == "proc_key_point":
                pid = id1 if t1 == "Procedure" else id2
                pt = id2 if t1 == "Procedure" else id1
                proc_ids.add(pid)
                key_points_by_proc.setdefault(pid, set()).add(pt)
                proc_point_edge[(pid, pt)] = e

            elif kind == "proc_ctx_point":
                pid = id1 if t1 == "Procedure" else id2
                pt = id2 if t1 == "Procedure" else id1
                proc_ids.add(pid)
                ctx_points_by_proc.setdefault(pid, set()).add(pt)
                proc_point_edge[(pid, pt)] = e

            elif kind == "legacy_proc_pack":
                pid = id1 if t1 == "Procedure" else id2
                pack = id2 if t1 == "Procedure" else id1
                pack_type = t2 if t1 == "Procedure" else t1
                proc_ids.add(pid)
                proc_to_packs.setdefault(pid, set()).add(pack)
                pack_is_steps[pack] = pack_type == "ProcedureStepsPack"

            elif kind == "legacy_pack_point":
                pack = id1 if "Pack" in t1 else id2
                pt = id2 if "Pack" in t1 else id1
                pack_to_points.setdefault(pack, set()).add(pt)
                legacy_pack_point_edge[(pack, pt)] = e

        # Legacy expansion: proc→pack→point ⇒ proc→point
        for pid, packs in proc_to_packs.items():
            for pack_id in packs:
                is_steps = pack_is_steps.get(pack_id, True)
                for pt in pack_to_points.get(pack_id, set()):
                    if is_steps:
                        key_points_by_proc.setdefault(pid, set()).add(pt)
                    else:
                        ctx_points_by_proc.setdefault(pid, set()).add(pt)
                    # Use legacy edge (pack→point) if no direct edge exists
                    if (pid, pt) not in proc_point_edge:
                        leg_edge = legacy_pack_point_edge.get((pack_id, pt))
                        if leg_edge:
                            proc_point_edge[(pid, pt)] = leg_edge

        if not proc_ids:
            return ([], []) if return_bundles else []

        # ── Procedure status ──
        proc_status: Dict[str, str] = {}
        for nid, node in memory_fragment.nodes.items():
            if _node_type(node) == "Procedure":
                props = node.attributes.get("properties") or {}
                if isinstance(props, str):
                    import json

                    try:
                        props = json.loads(props)
                    except Exception:
                        props = {}
                proc_status[str(nid)] = props.get("status") or node.attributes.get("status") or "active"

        # ── Bundle scoring (1-hop, like Episodic) ──
        bundles: List[ProcedureBundle] = []

        for pid in proc_ids:
            raw = direct_cost(pid)
            best = (raw + direct_procedure_penalty) if not math.isinf(raw) else INF
            best_path = "direct_procedure"
            best_point_id = None

            # Via KeyPoint
            for pt in key_points_by_proc.get(pid, set()):
                pd = direct_cost(pt)
                if math.isinf(pd):
                    continue
                eobj = proc_point_edge.get((pid, pt))
                if not eobj:
                    continue
                c = pd + edge_cost(eobj) + hop_cost
                if c < best:
                    best, best_path, best_point_id = c, "key_point", pt

            # Via ContextPoint
            for pt in ctx_points_by_proc.get(pid, set()):
                pd = direct_cost(pt)
                if math.isinf(pd):
                    continue
                eobj = proc_point_edge.get((pid, pt))
                if not eobj:
                    continue
                c = pd + edge_cost(eobj) + hop_cost
                if c < best:
                    best, best_path, best_point_id = c, "context_point", pt

            if math.isinf(best):
                continue

            # Inactive penalty
            if proc_status.get(pid, "active") != "active":
                best += inactive_penalty

            bundles.append(
                ProcedureBundle(
                    procedure_id=pid,
                    score=best,
                    best_path=best_path,
                    best_point_id=best_point_id,
                )
            )

        if not bundles:
            return ([], []) if return_bundles else []

        # ── Time bonus ──
        if time_info and time_info.has_time and time_info.confidence >= time_conf_min:
            time_cfg = TimeBonusConfig(
                enabled=True,
                bonus_max=time_bonus_max,
                score_floor=time_score_floor,
                query_conf_min=time_conf_min,
                created_at_weight=0.8,
            )
            for b in bundles:
                proc_node = memory_fragment.nodes.get(b.procedure_id)
                if proc_node:
                    tb = compute_time_match({"payload": proc_node.attributes}, time_info, time_cfg)
                    if tb.bonus > 0:
                        b.score = max(time_score_floor, b.score - tb.bonus)

        # ── Top-K selection ──
        bundles = heapq.nsmallest(top_k, bundles, key=lambda b: b.score)
        top_proc_ids = {b.procedure_id for b in bundles}
        bundle_rank = {b.procedure_id: i for i, b in enumerate(bundles)}

        # ── Output assembly ──
        out_edges: List[Edge] = []
        out_seen: Set[Tuple[str, str]] = set()

        def push_edge(e: Edge):
            k = (str(e.node1.id), str(e.node2.id))
            rk = (k[1], k[0])
            if k in out_seen or rk in out_seen:
                return
            out_seen.add(k)
            out_edges.append(e)

        for b in bundles:
            pid = b.procedure_id

            # Best-path edge
            if b.best_point_id:
                e = proc_point_edge.get((pid, b.best_point_id))
                if e:
                    push_edge(e)

            # All direct point edges for this procedure
            for pt in key_points_by_proc.get(pid, set()):
                e = proc_point_edge.get((pid, pt))
                if e:
                    push_edge(e)
            for pt in ctx_points_by_proc.get(pid, set()):
                e = proc_point_edge.get((pid, pt))
                if e:
                    push_edge(e)

        # Sort by bundle rank → edge cost
        def _edge_proc(e: Edge) -> str:
            for nid in (str(e.node1.id), str(e.node2.id)):
                if nid in top_proc_ids:
                    return nid
            return ""

        def _sort_key(e: Edge):
            owner = _edge_proc(e)
            rank = bundle_rank.get(owner, 10**9)
            cost = min(direct_cost(str(e.node1.id)), direct_cost(str(e.node2.id)))
            return (rank, cost)

        out_edges.sort(key=_sort_key)

        logger.info(f"[procedural] Returning {len(out_edges)} edges for {len(bundles)} procedures")

        # ── Return ──
        if return_bundles:
            bundles_metadata = [
                {
                    "procedure_id": b.procedure_id,
                    "score": b.score,
                    "best_path": b.best_path,
                    "best_point_id": b.best_point_id,
                    # Legacy compat fields
                    "best_support_id": b.best_point_id,
                    "best_steps_pack_id": None,
                    "best_step_point_id": b.best_point_id if b.best_path == "key_point" else None,
                    "best_context_pack_id": None,
                    "best_context_point_id": b.best_point_id if b.best_path == "context_point" else None,
                }
                for b in bundles
            ]

            TraceManager.event(
                "procedural.search.done",
                {
                    "out_edges": len(out_edges),
                    "bundles": len(bundles_metadata),
                },
            )
            return out_edges, bundles_metadata

        TraceManager.event("procedural.search.done", {"out_edges": len(out_edges)})
        return out_edges

    except ConceptNotFoundError:
        return ([], []) if return_bundles else []
    except CollectionNotFoundError:
        return ([], []) if return_bundles else []
    except Exception as e:
        logger.error("procedural_bundle_search error. query=%s error=%s", query, e)
        raise
