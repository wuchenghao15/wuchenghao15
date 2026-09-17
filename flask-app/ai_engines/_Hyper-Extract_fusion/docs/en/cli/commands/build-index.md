# he build-index

Build or rebuild the vector search index for a knowledge abstract.

---

## Synopsis

```bash
he build-index KA_PATH [OPTIONS]
```

## Arguments

| Argument | Description |
|----------|-------------|
| `KA_PATH` | Path to knowledge abstract directory |

## Options

| Option | Short | Description |
|--------|-------|-------------|
| `--force` | `-f` | Force rebuild even if index exists |

---

## Description

Builds a vector search index for semantic search and chat functionality:

1. **Reads all entities/relations** — From the knowledge abstract data
2. **Generates embeddings** — Using the configured embedding model
3. **Builds FAISS index** — For fast similarity search
4. **Saves to disk** — In the `index/` subdirectory

**Required for**: `he search` and `he talk` commands.

---

## Examples

### Build Index

```bash
he build-index ./output/
```

**Output:**
```
Template: general/biography_graph
Language: en

Success! Index built for ./output/

Now you can:
  he search ./output/ "keyword"  # Semantic search
  he talk ./output/ -i           # Interactive chat
```

### Force Rebuild

If the index is corrupted or you want to rebuild:

```bash
he build-index ./output/ -f
```

---

## When to Build Index

### After Parse (Default)

By default, `he parse` builds the index automatically:

```bash
he parse doc.md -t general/biography_graph -o ./ka/ -l en
# Index is built automatically
```

Skip with `--no-index` if you don't need search/chat:

```bash
he parse doc.md -t general/biography_graph -o ./ka/ -l en --no-index
```

## After Feed

Always rebuild after feeding new documents:

```bash
he feed ./ka/ new_doc.md
he build-index ./ka/
```

### After Manual Changes

If you modify `data.json` manually:

```bash
he build-index ./ka/ -f
```

---

## Index Storage

The index is stored in the knowledge abstract directory. Layout depends on the Auto-Type:

**AutoModel / AutoList** (pickle-free JSON since v0.10.1):

```
./ka/
├── data.json
├── metadata.json
└── index/
    └── index.json      # vectors + documents, no pickle
```

**Graph family / AutoSet / AutoDocument** (still OMem — not the v0.10.1 JSON path):

```
./ka/
├── data.json
├── metadata.json
└── index/
    ├── index.faiss     # FAISS vector index
    └── docstore.json   # Document store mapping
```

Load an existing `index/` only from Knowledge Abstract directories you created or fully trust. For AutoModel / AutoList, v0.10.1+ writes `index.json` and loads it without executing code; leftover `index.faiss` / `index.pkl` from <= v0.10.0 still deserialize on load — rebuild with `--force` to migrate. Graph / set / document indexes stay on OMem, so the trust warning still applies.

---

## Performance

### Build Time

| Knowledge Abstract Size | Approximate Build Time |
|---------------------|----------------------|
| Small (< 100 items) | < 5 seconds |
| Medium (100-1000) | 5-30 seconds |
| Large (1000+) | 30+ seconds |

### Search Speed

Once built, searches are fast:

```bash
he search ./ka/ "query"  # Typically < 1 second
```

---

## Best Practices

1. **Build after feeding** — Index becomes stale after `he feed`
2. **Use `--no-index` for batch** — Build once after all parsing
3. **Force rebuild if issues** — Use `-f` if search returns unexpected results
4. **Backup large indices** — The `index/` directory can be large

---

## Batch Workflow

For processing multiple documents efficiently:

```bash
# Parse all without building index
he parse doc1.md -t general/biography_graph -o ./ka/ -l en --no-index
he feed ./ka/ doc2.md
he feed ./ka/ doc3.md

# Build index once at the end
he build-index ./ka/

# Now ready for search/chat
he search ./ka/ "query"
he talk ./ka/ -q "question"
```

---

## Troubleshooting

### "Index already exists"

Use `-f` to force rebuild:

```bash
he build-index ./ka/ -f
```

### "Failed to build index"

Check:
1. Knowledge base has data: `he info ./ka/`
2. API key is configured: `he config show`
3. Sufficient disk space for index

### Search still doesn't work

Try force rebuild:

```bash
he build-index ./ka/ -f
```

---

## See Also

- [`he parse`](parse.md) — Parse with optional index building
- [`he feed`](feed.md) — Add documents (requires rebuild)
- [`he search`](search.md) — Search the index
- [`he talk`](talk.md) — Chat using the index
