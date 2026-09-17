# he talk

Chat with your knowledge abstract using natural language.

---

## Synopsis

```bash
he talk KA_PATH [OPTIONS]
```

## Arguments

| Argument | Description |
|----------|-------------|
| `KA_PATH` | Path to knowledge abstract directory |

## Options

| Option | Short | Description |
|--------|-------|-------------|
| `--query` | `-q` | Single question to ask |
| `--top-k` | `-n` | Number of context items to retrieve | 3 |
| `--interactive` | `-i` | Enter interactive chat mode |
| `--source` | — | Scope: only knowledge contributed by these source documents (repeatable) |
| `--tag` | — | Scope: only knowledge from sources carrying these tags (repeatable) |

---

## Description

The `talk` command lets you have a conversation with your knowledge abstract:

1. **Retrieves relevant context** — Searches for information related to your question
2. **Generates answer** — Uses LLM to synthesize a natural language response
3. **Shows sources** — Displays which items were used to generate the answer

**Requires**: Search index must be built.

---

## Examples

### Single Question

```bash
he talk ./output/ -q "What were Tesla's major achievements?"
```

**Output:**
```
Query: What were Tesla's major achievements?
Knowledge Abstract: ./output/
Top K: 3

Nikola Tesla made numerous groundbreaking contributions to electrical 
engineering. His major achievements include:

1. Development of the alternating current (AC) electrical system, which 
   became the dominant method of power transmission worldwide.

2. Invention of the Tesla coil, used in radio technology and electrical 
   resonant circuits.

3. Contributions to the development of X-ray imaging and wireless 
   communication technologies.

Retrieved context:
1. Nikola Tesla: Serbian-American inventor, electrical engineer...
2. AC Power System: Type: invention, Description: System for alternating...
3. Tesla Coil: Type: invention, Description: Resonant transformer circuit...
```

### Interactive Mode

```bash
he talk ./output/ -i
```

**Session:**
```
Entering interactive mode. Type 'exit' or 'quit' to stop.

Knowledge Abstract: ./output/
Template: general/biography_graph
Top K: 3

> Who was Nikola Tesla?
Nikola Tesla was a Serbian-American inventor, electrical engineer, 
mechanical engineer, and futurist best known for his contributions 
to the design of the modern alternating current (AC) electricity 
supply system.

> When was he born?
Nikola Tesla was born on July 10, 1856, in Smiljan, Croatia.

> What about his relationship with Edison?
Tesla worked for Thomas Edison in New York City in 1884. They had 
a contentious relationship due to differing views on direct current 
(DC) versus alternating current (AC) power systems.

> exit
Goodbye!

Other useful commands:
  he show ./output/              # Visualize
  he search ./output/ "keyword"  # Search
  he info ./output/              # View info
```

### With More Context

Increase context for complex questions:

```bash
he talk ./output/ -q "Explain the War of Currents" -n 10
```

---

## Scoped chat

Restrict generated answers to a subset of sources with `--source` (specific source documents) or `--tag` (any source carrying the tag — set tags with [`he tag`](tag.md)), the same filters as [`he search`](search.md):

```bash
# Only answer from sources tagged `legal`
he talk ./ka/ -q "What are the termination conditions?" --tag legal

# Only answer from two specific documents
he talk ./ka/ -q "What are the termination conditions?" --source contract-2024 --source annex-b
```

`--source` and `--tag` combine as a union: a key matches when **any** of its contributing sources fits either filter. Interactive mode (`-i`) keeps the same scope on every turn.

> Scoping requires the KA to have been fed with `--source`, so the source ledger exists — see [Source Attribution & Provenance](../../python/guides/provenance.md). Types without a ledger (for example AutoList / AutoModel) reject `--source` / `--tag` with a scoped-chat error.

---

## Interactive Commands

In interactive mode (`-i`):

| Command | Action |
|---------|--------|
| `exit`, `quit`, `q` | Exit interactive mode |
| `help` | Show available commands |

---

## Use Cases

### Research Assistant

```bash
he talk ./paper_kb/ -q "Summarize the main contributions of this paper"
```

### Legal Analysis

```bash
he talk ./contract_kb/ -q "What are the termination conditions?"
```

### Historical Research

```bash
he talk ./bio_kb/ -q "What events led to Tesla's financial difficulties?"
```

---

## How It Works

1. **Semantic Search** — Finds relevant items in the knowledge abstract
2. **Context Assembly** — Combines retrieved items into context
3. **LLM Generation** — Generates answer using the context
4. **Source Attribution** — Shows which items informed the answer

---

## Tips for Better Answers

1. **Be specific** — "What inventions did Tesla create?" vs "Tell me about Tesla"
2. **Ask follow-ups** — Build context through conversation
3. **Adjust top-k** — Use `-n 5` or higher for complex questions
4. **Check sources** — Review "Retrieved context" for accuracy

---

## Comparison with `he search`

| Feature | `he search` | `he talk` |
|---------|-------------|-----------|
| Output | Raw entities/relations | Natural language |
| Best for | Finding specific data | Understanding/explaining |
| Speed | Fast | Slower (LLM call) |
| Source visibility | Direct | Cited in context |

---

## Troubleshooting

### "Index not found"

```bash
he build-index ./output/
```

### "No relevant information"

- Try rephrasing your question
- Increase context with `-n 10`
- Verify knowledge abstract has relevant data: `he info ./output/`

---

## See Also

- [`he search`](search.md) — Search for specific items
- [`he build-index`](build-index.md) — Build search index
- [`he show`](show.md) — Visualize knowledge graph
