# he clean

Clean a knowledge abstract — remove its search index, or the entire KA with `--all`.

---

## Synopsis

```bash
he clean KA_PATH [OPTIONS]
```

## Arguments

| Argument | Description |
|----------|-------------|
| `KA_PATH` | Path to the knowledge abstract directory |

## Options

| Option | Alias | Default | Description |
|--------|-------|---------|-------------|
| `--all` | `-a` | off | Remove the **entire** KA directory (data, metadata, and index) |
| `--yes` | `-y` | off | Skip the confirmation prompt |

---

## Description

`he clean` deletes parts of a knowledge abstract:

- **Default** — removes only the vector index (the `index/` subdirectory). The extracted data (`data.json`) and metadata are kept; rebuild later with [`he build-index`](build-index.md).
- **`--all`** — removes the entire KA directory.

Deletion is **permanent**. The command asks for confirmation first; pass `--yes` to skip the prompt (e.g. in scripts).

For safety, `he clean` only operates on a real knowledge abstract — a directory containing `data.json`. It refuses to delete an arbitrary directory, so a mistyped path cannot wipe unrelated files.

---

## Examples

### Clean the index (keep data)

```bash
he clean ./tesla_kb/
# → deletes ./tesla_kb/index/ after confirmation
```

## Remove the whole knowledge abstract

```bash
he clean ./tesla_kb/ --all
```

### Non-interactive (scripts / CI)

```bash
he clean ./tesla_kb/ --all --yes
```

---

## What gets deleted

| Mode | Deleted | Kept |
|------|---------|------|
| default | `index/` | `data.json`, `metadata.json` |
| `--all` | the entire `KA_PATH` directory | — |

> An Obsidian vault produced by [`he export obsidian`](export.md) is a separate folder and is **not** touched by `he clean`. Remove it with your shell (`rm -rf ./vault/`).

---

## See Also

- [`he build-index`](build-index.md) — Rebuild the search index after cleaning it
- [`he info`](info.md) — Inspect a knowledge abstract before cleaning
- [`he parse`](parse.md) — Re-create a knowledge abstract
