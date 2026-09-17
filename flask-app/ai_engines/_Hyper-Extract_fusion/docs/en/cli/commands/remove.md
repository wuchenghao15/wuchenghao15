# he remove

Delete knowledge from an existing knowledge abstract: hard-delete nodes/edges by key, or soft-remove a single fact with LLM assistance.

---

## Synopsis

```bash
he remove KA_PATH [OPTIONS]
```

## Options

| Option | Default | Description |
|--------|---------|-------------|
| `--node TEXT` | — | Node key(s) to **hard-delete**; edges anchored by a removed node are removed too |
| `--edge TEXT` | — | Edge key(s) to **hard-delete** |
| `--edit-node TEXT` | — | Node key to **soft-edit** (LLM rewrites it minus `--fact`) |
| `--edit-edge TEXT` | — | Edge key to **soft-edit** |
| `--document TEXT` | — | **Roll back** all knowledge contributed by a source document (requires the KA to have been fed with `--source`) |
| `--strategy` | `exact` | Rollback strategy for `--document`: `exact` or `touched` |
| `--fact TEXT` | — | The fact to remove from the `--edit-node` / `--edit-edge` item |
| `--instruction TEXT` | — | Free-form edit instruction (alternative to `--fact`) |
| `--dry-run` | off | Preview the change without persisting it |
| `--backup / --no-backup` | on | Back up `data.json` as `data.json.bak.<timestamp>` before writing |
| `--yes` | `-y` | Skip the confirmation prompt |

Hard delete (`--node` / `--edge`) and soft delete (`--edit-node` / `--edit-edge`) are mutually exclusive.

---

## Hard Delete: by Key

Remove whole items. Keys are the values produced by the template's `identifiers` (typically the entity name for nodes, `"{source}|{type}|{target}"`-style keys for edges). Use [`he show`](show.md) or read `data.json` to find them.

```bash
# Remove two nodes; any edge touching them is removed as well
he remove ./ka/ --node Apple --node Nokia

# Remove one edge by its exact key
he remove ./ka/ --edge "Apple-partner-Google"
```

The command prints a removal report (removed items, keys not found, orphaned edges pruned).

!!! warning
    Hard delete is **permanent** for the deleted items. A `data.json.bak.<timestamp>` backup is written next to the KA before writing unless `--no-backup` is passed.

---

## Soft Delete: remove a single fact (LLM-assisted)

Sometimes a node should stay, but one claim inside it is wrong or obsolete:

```bash
# Preview first (nothing is written)
he remove ./ka/ --edit-node Apple \
  --fact "founded by Steve Jobs" --dry-run

# Apply
he remove ./ka/ --edit-node Apple \
  --fact "founded by Steve Jobs" -y
```

The LLM rewrites the item under the **same schema**, removing the fact while keeping every other field unchanged. Guardrails:

- **Key invariance** — a rewrite that changes the item's key is rejected (renaming is not an edit; delete the old item and add the new one instead).
- **Dry run** — `--dry-run` prints the old and proposed items and writes nothing.
- **No-op detection** — if the fact was not found, the command reports `No change` and writes nothing.
- **Backup** — `data.json.bak.<timestamp>` is written before the edit unless `--no-backup`.

For edges, remember that fields used by the edge key (e.g. `relation_type`) cannot be changed by a soft edit — the rewrite would be rejected; hard-delete the edge instead.

```bash
he remove ./ka/ --edit-edge "Apple-acquired-Beats" \
  --instruction "Remove the price from the description"
```

---

## After removal

When the knowledge abstract already has a search index, `he remove` **patches it in place** — only the affected vectors are deleted/re-embedded, and `he build-index` is *not* required afterwards. Search stays usable immediately.

If no index had been built (or in-place patching was not possible), any stale on-disk index is removed instead; rebuild it before searching or chatting again:

```bash
he build-index ./ka/
```

---

## Document Rollback: remove a whole source document

When documents were ingested with a source attribution, their entire contribution can be rolled back:

```bash
# Ingest with attribution
he feed ./ka/ doc1.md --source doc-1
he feed ./ka/ doc2.md --source doc-2

# Later: roll back everything doc-1 contributed ("b" remains via doc-2 if shared)
he remove ./ka/ --document doc-1

# Or delete every key the document touched, even when other documents share it
he remove ./ka/ --document doc-1 --strategy touched
```

## Rollback Strategies (`--strategy`)

| Strategy | Behavior |
|----------|----------|
| `exact` (default) | Keys contributed solely by the removed document are deleted; keys **shared** with other documents are re-merged from the surviving sources' raw results — deterministic with classic merge strategies (LLM strategies preserve semantics with approximate wording) |
| `touched` | Every key the document touched is deleted outright, including keys other documents also contributed to |

Requires the KA's memories to track sources (graph-family KAs do by default). If the document has no recorded contributions, the command reports `Nothing matched` and exits successfully.

---

## Python API

```python
ka.remove_nodes("Apple", "Nokia")   # -> {"removed_nodes": [...], "not_found_nodes": [...], "removed_orphan_edges": [...]}
ka.remove_edges("Apple-partner-Google")

report = ka.edit_node("Apple", remove_fact="founded by Steve Jobs", dry_run=True)
# report: {"changed": bool, "applied": bool, "old": <item>, "new": <item>}
ka.edit_node("Apple", remove_fact="founded by Steve Jobs")  # applies

ka.dump("./ka/")  # persist
```

Works for graph, hypergraph, and temporal/spatial graph knowledge abstracts.

---

## See Also

- [`he clean`](clean.md) — remove the search index or the whole KA
- [`he show`](show.md) — inspect keys before deleting
- [`he build-index`](build-index.md) — rebuild the search index after removal

## See Also

- [`he feed --source`](feed.md) — attributed ingestion (the other half of the lifecycle)
- [`he tag`](tag.md) — tag sources for scoped search
- [Managing Documents Over Time](managing-documents.md) — the complete lifecycle guide
