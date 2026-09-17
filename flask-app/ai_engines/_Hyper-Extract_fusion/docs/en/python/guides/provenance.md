# Source Attribution & Provenance

Track which documents contributed to a knowledge abstract, skip unchanged re-feeds, and roll back any document's contribution without touching the rest.

---

## Overview

Ingesting a document **with attribution** (`--source` on the CLI, `source_id=` in Python) makes the knowledge abstract remember that document: its raw extraction results are kept in a **source ledger**, together with a SHA-256 content hash of the input text.

Provenance gives you three capabilities:

| Capability | CLI | Python |
|------------|-----|--------|
| **Per-document rollback** | `he remove --document ID` | `ka.remove_source(ID)` |
| **Change detection** | `he feed --source` skips unchanged documents | `ka.source_content_hash(ID)` |
| **Audit** | `he info --sources` | `ka.sources()` |

Source tracking is on by default for graph-family KAs (graph, hypergraph, temporal/spatial graphs).

---

## Ingesting with Attribution

```bash
# Attribute at parse time (first document)
he parse doc1.md -t general/graph -o ./ka/ -l en --source doc-1

# Attribute when feeding into an existing KA
he feed ./ka/ doc2.md --source doc-2
```

```python
from hyperextract import Template

ka = Template.create("general/graph", language="en")

with open("doc1.md") as f:
    result = ka.parse(f.read(), source_id="doc-1")

result.feed_text(doc2_text, source_id="doc-2")
result.dump("./ka/")
```

## Change Detection

If the same source is fed again with unchanged content, `he feed` compares the content hash and skips the document entirely — **zero LLM calls**:

```bash
he feed ./ka/ doc2.md --source doc-2
# Source 'doc-2' is unchanged (content hash matches) — nothing to do.
# Use --refeed to re-ingest anyway.
```

```bash
# Force re-ingestion even when the hash matches
he feed ./ka/ doc2.md --source doc-2 --refeed
```

---

## Inspecting the Ledger

```bash
he info ./ka/ --sources
```

**Output:**
```
                        Source Ledger
┏━━━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Source ID  ┃ Raw Items ┃ Content Hash                       ┃
┡━━━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ doc-1      │        12 │ 9f86d081884c7d659a2febb0c0413a6e…  │
│ doc-2      │         8 │ 2c26b44babbfb4c6a5cc6b3f2a4b2f1d…  │
└────────────┴───────────┴────────────────────────────────────┘
```

In Python:

```python
ka.sources()
# {
#     "doc-1": {"raw_items": 12, "content_hash": "9f86d0…"},
#     "doc-2": {"raw_items": 8, "content_hash": "2c26b4…"},
# }
```

---

## Rolling Back a Document

Remove everything a document contributed:

```bash
he remove ./ka/ --document doc-1

# Explicit strategy
he remove ./ka/ --document doc-1 --strategy touched
```

```python
report = ka.remove_source("doc-1")                      # exact (default)
report = ka.remove_source("doc-1", strategy="touched")

result.dump("./ka/")  # persist
```

The strategy decides what happens to keys the document **shared** with other documents:

| Strategy | Shared keys | Sole keys |
|----------|-------------|-----------|
| `exact` (default) | Re-merged from the surviving sources' raw results (deterministic with classic merge strategies) | Deleted |
| `touched` | Deleted outright | Deleted |

`exact` keeps every surviving document's contribution intact; `touched` guarantees none of the document's influence remains, at the cost of also removing facts other documents support. With LLM merge strategies, the `exact` re-merge preserves semantics with approximate wording. Unknown or empty sources report `Nothing matched` and exit successfully. Either way, the search index is patched in place when built.

!!! note
    Hash-based change detection is built into `he feed --source`. Python callers get the same effect by comparing `ka.source_content_hash(source_id)` against their own hash of the text before calling `feed_text`.

---

## Fact-Level Editing

For surgical edits — keep a node but drop one wrong claim — use fact-level editing instead of a full rollback:

```python
report = ka.edit_node("Apple", remove_fact="founded by Steve Jobs", dry_run=True)
ka.edit_node("Apple", remove_fact="founded by Steve Jobs")  # applies
```

```bash
he remove ./ka/ --edit-node Apple --fact "founded by Steve Jobs" -y
```

See [`he remove`](../../cli/commands/remove.md) for all guardrails (key invariance, dry run, backups).

---

## Persistence

`ka.dump()` — and every `he parse` / `he feed` — writes the ledger next to `data.json`:

```
./ka/
├── data.json             # Extracted knowledge
├── metadata.json         # Extraction metadata
├── sources_nodes.json    # Node ledger: raw items per source
├── sources_edges.json    # Edge ledger: raw items per source
├── sources_chunks.json   # Chunk ledger (chunk-based KAs): raw chunks per source
└── documents/            # Archived originals, one current copy per source
```

- Keep the ledger files together with the KA (treat them like `data.json` in version control): the raw per-source results live only there, so deleting the ledger disables rollback and change detection for that KA.
- `he feed --source` also archives the original document under `documents/` (raw bytes, one current copy per source; disable with `--no-store-doc`). Pass `--purge-documents` to `he remove --document` to delete the archived copy together with the rollback.
- Before any write, `he remove` backs up `data.json` as `data.json.bak.<timestamp>` (unless `--no-backup`), so even a rollback can itself be undone.

---

## Roadmap

- **Shipped (v0.8.0)** — content-hash change detection: `he feed --source` hashes the input and skips unchanged documents before any LLM call.
- **Shipped (v0.9.0)** — original-document archiving (`documents/`) and the `chunk_rag` method, which retrieves raw text chunks directly (chunk-level *retrieval*).
- **Planned** — deeper lineage for extracted facts: mapping each node/edge in a graph KA back to the exact chunk (passage) it was extracted from. Note this is distinct from `chunk_rag`, which retrieves chunks but does not structure them.

---

## See Also

- [`he feed`](../../cli/commands/feed.md) — `--source` and `--refeed` flags
- [`he info`](../../cli/commands/info.md) — source ledger inspection
- [`he remove`](../../cli/commands/remove.md) — document rollback and fact-level editing reference
- [Incremental Updates](incremental-updates.md) — merge behavior when feeding
