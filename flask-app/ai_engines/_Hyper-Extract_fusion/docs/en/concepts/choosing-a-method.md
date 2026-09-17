# Choosing a method: baseline vs structured

When do you pay for graph extraction, and when are raw chunks enough?

This page is a decision aid, not an evaluation framework. It does not define recall metrics, QA pairs, or CI scores. For a same-corpus walkthrough of answers, latency, and token use, run the companion script on `examples/en/tesla.md` once it is in `examples/en/methods/` (`chunk_vs_graph_rag.py`). That script is a manual demo — CI will not run it.

The catalog of algorithms lives in [Methods](methods.md). How to call them is in [Using Methods](../python/guides/using-methods.md).

---

## Two defaults

| Need | Start with | Why |
|------|------------|-----|
| Lookup, quote the original wording, or locate a passage | `chunk_rag` | Ingest is embed-only. No LLM extraction cost. Retrieval returns the chunks themselves. |
| Multi-hop or relationship-dense questions | `graph_rag` | Extraction builds nodes and edges so answers can follow links, not only lexical overlap. |

`chunk_rag` shipped as the zero-extraction baseline. Use it first; pay for `graph_rag` (or another structured method) only when that extra ingest cost changes the answers you care about.

---

## When chunks are enough

Prefer `chunk_rag` when:

- The question is **lookup-style**: “What year…?”, “Quote the clause…”, “Where does the document say…?”
- You need **the original wording**, not a synthesized graph fact.
- The corpus is large and **ingest LLM cost** is the constraint.
- You are deciding whether extraction is worth it at all — this is the baseline.

Ingest path: chunk → embed → index. Query path: retrieve chunks → (optional) chat over those chunks.

---

## When graph extraction pays off

Prefer `graph_rag` (or another graph/hypergraph method) when:

- The question is **multi-hop**: “Who funded the company that acquired X?”
- The question is **relationship-dense**: rivals, successors, ownership, causation.
- You will **reuse the graph** (export, scoped graph search, visualization), not only ask once.

You pay an LLM at ingest to extract structure. That cost is wasted if every question could have been answered by pointing at a chunk.

---

## Same corpus, same provenance

`chunk_rag` and `graph_rag` share the provenance machinery: source ledger, `he tag`, scoped `he search` / `he talk`, and per-document rollback. A comparison on one corpus (`examples/en/tesla.md`) is apples-to-apples — the difference is extraction, not tagging or rollback.

See [Source Attribution & Provenance](../python/guides/provenance.md).

---

## This is not an eval harness

This page does not define hit-rate metrics, expected spans, or a benchmark set. Hash embeddings in CI would make recall numbers meaningless. A separate RFC would be needed before any harness — that work is out of scope here.

---

## See Also

- [Methods](methods.md) — algorithm catalog and comparison table
- [Using Methods](../python/guides/using-methods.md) — `Template.create("method/…")`
- [Search and Chat](../python/guides/search-and-chat.md) — `search` / `chat` after you pick a method
