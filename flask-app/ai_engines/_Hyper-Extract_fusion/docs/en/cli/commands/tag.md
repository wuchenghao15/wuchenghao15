# he tag

Manage tags on source documents of a knowledge abstract — organize sources for scoped search and rollback.

---

## Synopsis

```bash
he tag KA_PATH --source SOURCE_ID [--add TAG ...] [--remove TAG ...]
he tag KA_PATH --list
he tag KA_PATH --source SOURCE_ID          # show current tags
```

## Arguments

| Argument | Description |
|----------|-------------|
| `KA_PATH` | Path to the knowledge abstract directory |

## Options

| Option | Alias | Default | Description |
|--------|-------|---------|-------------|
| `--source TEXT` | — | **required** | Source document id to tag |
| `--add TEXT` | — | — | Tag(s) to add (repeatable) |
| `--remove TEXT` | — | — | Tag(s) to remove (repeatable) |
| `--list` | `-l` | off | List all sources with their tags |

---

## Description

`he tag` attaches free-form labels to the source documents inside a knowledge abstract:

- **Persistence** — tags are stored in the **source ledger** (`sources_nodes.json` / `sources_edges.json`), the same files that record [`he feed --source`](feed.md) attribution, so they persist with the KA across `he dump` / `he load`.
- **Scoped retrieval** — tags let you restrict [`he search`](search.md) to knowledge contributed by sources carrying a given tag (see [Scoped Search](#scoped-search)).
- **Availability** — works for graph-family knowledge abstracts, i.e. any KA whose source ledger tracks provenance (see [Source Attribution & Provenance](../../python/guides/provenance.md)).

---

## Examples

### Add tags to a source

```bash
he tag ./ka/ --source contract-2024 --add legal --add reviewed
# → Tagged! contract-2024: legal, reviewed
```

## Remove tags from a source

```bash
he tag ./ka/ --source contract-2024 --remove reviewed
```

### Show current tags of a source

```bash
he tag ./ka/ --source contract-2024
# → contract-2024 tags: legal
```

## List all sources with their tags

```bash
he tag ./ka/ --list
```

Prints a table of the source ledger: source id, number of raw items, and tags.

---

## Scoped Search

Tags become useful together with the `--tag` option of [`he search`](search.md):

```bash
# Only search knowledge contributed by sources tagged `legal`
he search ./ka/ "termination" --tag legal
```

Scoping requires the sources to have been ingested with attribution (`he feed ./ka/ doc.md --source contract-2024`), so the ledger exists.

---

## See Also

- [`he remove`](remove.md) — document rollback (`--document`), including the same source ledger
- [Source Attribution & Provenance](../../python/guides/provenance.md) — source attribution, the ledger, and change detection
