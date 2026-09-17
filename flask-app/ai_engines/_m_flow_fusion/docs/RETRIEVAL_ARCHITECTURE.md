# M-Flow Core Retrieval Architecture

## The Problem with Flat Retrieval

Every RAG system faces the same question: given a user query, which pieces of stored knowledge are relevant?

The dominant approach — embed chunks into a vector store, retrieve by cosine similarity — answers this at a single level: "which text fragment is semantically closest to the query?" This works for simple factual lookups, but collapses when:

- **The answer spans multiple documents** — chunks have no structural link between them; the system cannot combine related information scattered across different documents
- **The user asks at the wrong granularity** — broad questions retrieve overly specific fragments; precise questions retrieve overly vague summaries
- **Two documents discuss the same entity in different contexts** — they may be far apart in vector space, with no way to bridge them

The core issue is that flat vector search **discards structure**. It knows a chunk is "close" to the query, but has no idea *where that chunk sits in the topology of knowledge*.

## M-Flow's Approach: Graph-Routed Bundle Search

M-Flow replaces flat retrieval with **graph-routed retrieval** that operates on a layered knowledge topology. The key insight is:

> Don't just find what matches — find which *knowledge structure* the match belongs to, and score the structure as a whole.

### The Knowledge Topology: Inverted Cone

M-Flow organizes all ingested knowledge into a four-level directed graph forming an **inverted cone**:

| Level | Role | Position in the Cone |
|-------|------|---------------------|
| **FacetPoint** | Atomic assertion — a precise fact or data point | **Tip**: sharpest semantics, most precise match |
| **Entity** | Named thing — a bridge that cuts across all levels | **Tip**: semantics tightly focused on a single name |
| **Facet** | Cross-sectional dimension — one angle or aspect of a semantic focus | **Middle layer** |
| **Episode** | A bounded semantic focus | **Base**: richest semantics, the final recall landing point |

The directionality of this structure is **counter-intuitive**: in traditional knowledge graphs or taxonomies, deeper means more specific. In M-Flow, the search **enters at the tip** (fine-grained Entities and FacetPoints are the easiest to hit precisely with vector search) and the search **targets the base** (Episodes are the knowledge units ultimately returned to the user). Information flows from sharp match points downward, converging into broad semantic landing zones.

This breaks the traditional "browse top-down" retrieval paradigm. The user does not narrow scope level by level. Instead, the system captures signal at the sharpest point and **propagates downward through graph structure** to the complete semantic unit it belongs to.

### Design Break #1: Edges Have Semantics

In virtually every knowledge graph system, edges are just type labels (`works_at`, `located_in`). When querying a graph, you either traverse edges or ignore them — edges carry no searchable semantics of their own.

M-Flow breaks this: every edge carries a natural language description, and these edge texts are vectorized and searched alongside nodes.

This means edges are no longer passive connectors but **active semantic filters**. During cost propagation, the system knows not just "a connection exists between two nodes" but "how relevant this connection is to the current query." A semantically irrelevant edge contributes high cost, effectively blocking the path — even if both endpoint nodes were hit by vector search.

### How Bundle Search Works

When a query arrives, the system does not simply find the closest node. It finds the **best Episode** by evaluating all paths through the graph that could reach it.

**Phase 1 — Cast a wide net at the tip**

The query is embedded and searched simultaneously against seven vector collections — covering every layer from tip to base. Each collection returns up to 100 candidates.

The easiest to hit precisely are nodes at the cone tip: an Entity name, a FacetPoint assertion. These fine-grained anchors have tightly focused semantics and small vector distances. Episode summaries at the cone base may also be hit, but their broader semantics typically produce less precise matches.

**Phase 2 — Project into the graph**

These anchors serve as entry nodes into the knowledge graph. The system extracts the surrounding subgraph — edges, neighbors, connections — then expands one hop further. This transforms a set of isolated vector hits into a connected topological structure.

**Phase 3 — Propagate cost from tip to base**

This is the core step, the essence of Bundle Search: **capture signal at the tip, propagate along graph edges toward the base, aggregate scores at Episodes.**

For each Episode in the subgraph, the system evaluates every possible path from an anchor to that Episode:

| Path | Starting from | Traverses through |
|------|--------------|-------------------|
| Direct hit | Episode itself | None (but penalized — see below) |
| Facet path | Facet | → Episode |
| FacetPoint path | FacetPoint | → Facet → Episode |
| Entity direct path | Entity | → Episode |
| Entity-Facet path | Entity | → Facet → Episode |

Each path accumulates cost:
- **Starting cost** — the anchor's vector distance (sharpness of the signal)
- **Edge cost** — each traversal adds the edge's own vector distance (relevance of the connection to the query) plus a hop penalty
- **Miss penalty** — a high default cost for edges not matched by vector search

The Episode's final score is the **minimum cost across all paths**.

**Phase 4 — Rank and assemble**

Episodes are ranked by bundle cost, top-K selected. Output content is determined by the caller's display mode: summary mode returns Episode summaries, detail mode returns the Episode's Facets and Entities, and highly_related_summary mode returns only the paragraphs of the Episode summary related to the matched Facet.

### Design Break #2: Minimum, Not Average

Why take the minimum? This is a deliberate retrieval philosophy: **one strong chain of evidence is sufficient to prove relevance.**

An Episode may have ten Facets, nine of which are irrelevant to the query. A traditional approach might average all path costs — dragged up by nine high-cost paths. Bundle Search only looks at the best path. As long as one Facet connects to the query through a low-cost path, this Episode should be retrieved.

This mirrors how human memory works: you recall something because one association is strong enough, not because every association points to it.

### Design Break #3: Penalize Direct Hits

The most counter-intuitive design: when a query directly matches an Episode summary, the system **applies an extra penalty to that path**.

Why penalize the most direct hit? Because Episode summaries are high-level generalizations — they "look relevant" to many queries. An Episode summary about "project management" may have a decent vector distance to any query mentioning "project" or "management." But this match is **broad and unfocused**, which also reflects the root cause of retrieval noise in many RAG systems.

The system's design preference is: **if a more precise path exists from the tip (FacetPoint, Entity), choose it even if it requires more hops.** Direct Episode hits win only when no better alternative path exists.

This ensures retrieval precision — not "vaguely related to everything" summaries, but Episodes backed by specific chains of evidence.

### Why It Works: The Topology Argument

The fundamental advantage is that **the graph topology encodes knowledge organization that vectors alone cannot capture**.

**Multi-granularity auto-routing.** "What happened with the database migration?" — a broad question directly matches an Episode summary; despite the direct hit penalty, it still wins because no more precise tip-level path exists. "Was the P99 target under 500ms?" — a precise question strongly matches a FacetPoint; though the path goes through two hops, the tiny starting distance keeps total cost low. The system doesn't need to "choose" a granularity — the inverted cone topology routes each query to its naturally matching level.

**Cross-document entity bridging.** When "Dr. Zhang works at MIT" appears in Document A and "MIT published a quantum computing breakthrough" appears in Document B, both Episodes share the same Entity node "MIT." A query about MIT hits the Entity at the tip, and path cost propagates downward to both Episodes. The user gets results from two independent sources, bridged not by LLM reasoning but by graph topology itself.

**Structural noise filtering.** In flat retrieval, a semantically similar but topically irrelevant chunk ranks high. In Bundle Search, that chunk must trace through edges to reach an Episode. If the connecting edges are irrelevant to the query (high edge vector distance), path cost inflates and the result drops in ranking. The graph acts as a structural filter on semantic noise.

**Cost propagation as reasoning.** Each path through the graph represents a chain of reasoning: "the query matches this fact, which belongs to this theme, which is part of this event." Path cost quantifies how tight that reasoning chain is. The system performs multi-hop reasoning within 2-3 hops through cost arithmetic, without invoking an LLM at retrieval time.

### Adaptive Confidence

Not all vector collections are equally reliable for a given query. The system computes two signals per collection: absolute match strength and discrimination. It then groups all collections into "node-type" and "edge-type" and allocates weights by confidence ratio. If the Entity collection's confidence far exceeds the Facet collection's, the system amplifies the influence of entity-derived paths.

The system adapts its retrieval strategy per query — not fixed weights, but dynamic allocation based on "which granularity produced the most reliable hits this time."

### Addendum: An Additional Tuning Mechanism

When a Facet's vector distance is extremely small (near-perfect match to the query), the system heavily discounts edge costs and hop costs along that path. The logic: if a Facet almost exactly corresponds to the query, the edge connecting it to its Episode is almost certainly correct — no need for edge semantics to verify.

The system also includes query preprocessing, parallel multi-mode orchestration, output trimming, and other mechanisms not detailed here.

## Summary

M-Flow's retrieval is not "vector search plus a graph database." The graph is the retrieval mechanism itself:

1. **Inverted cone topology** — fine-grained anchors (Entity, FacetPoint) capture precise signals at the tip; broad Episodes provide recall landing points at the base
2. **Edges as semantic filters** — not passive connectors but active participants in path scoring, blocking irrelevant paths
3. **Path cost propagation** — from tip to base, scoring each Episode by the tightest chain of evidence
4. **Minimum, not average** — one strong path is enough, mirroring single-cue triggering in human memory
5. **Penalize direct hits** — prefer paths from precise anchors, preventing broad matches from dominating rankings
6. **Adaptive confidence** — dynamically adjust strategy based on which cone layer (granularity) produced the most reliable hits per query

The result: the same query can naturally find a broad Episode summary, a precise atomic fact, or a cross-document entity connection — depending on where the lowest-cost path leads. Signal is captured at the tip and lands at the base.
