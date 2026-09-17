# CLI Quickstart

Get your first knowledge extraction running in 5 minutes using the terminal.

---

## Prerequisites

- [Hyper-Extract installed](installation.md)
- A text file to extract from (we'll use an example)

---

## Step 1: Configure API Key

Choose your deployment method and run the corresponding configuration command:

=== "OpenAI"

    ```bash
    he config init -p openai -k YOUR_OPENAI_API_KEY
    ```

=== "Bailian (Alibaba Cloud)"

    ```bash
    he config init -p bailian -k YOUR_BAILIAN_API_KEY
    ```

=== "DeepSeek"

    ```bash
    he config llm -p deepseek -k YOUR_DEEPSEEK_API_KEY
    he config embedder -p openai -k YOUR_OPENAI_API_KEY
    ```

=== "Local vLLM"

    ```bash
    he config llm -p vllm \
      -u http://localhost:8000/v1 \
      -k dummy \
      -m Qwen/Qwen3.5-9B

    he config embedder -p vllm \
      -u http://localhost:8001/v1 \
      -k dummy \
      -m BAAI/bge-m3
    ```

=== "Anthropic (Claude)"

    Anthropic provides LLM only — pair with an OpenAI-compatible embedder for search/chat:

    ```bash
    he config llm -p anthropic -k YOUR_ANTHROPIC_API_KEY
    he config embedder -p openai -k YOUR_OPENAI_API_KEY
    ```

This creates a configuration file at `~/.he/config.toml`. You only need to do this once.

> **Note:** Anthropic and DeepSeek provide LLM only. For search (`he search`) and chat (`he talk`) features, pair them with an OpenAI-compatible embedder as shown above.

---

## Step 2: Download Sample Document

```bash
# Download a sample biography
curl -o tesla.md https://raw.githubusercontent.com/yifanfeng97/hyper-extract/main/examples/en/tesla.md
```

Or create a simple test file:

```bash
cat > sample.txt << 'EOF'
Nikola Tesla was a Serbian-American inventor, electrical engineer, 
mechanical engineer, and futurist. He is best known for his 
contributions to the design of the modern alternating current 
(AC) electricity supply system.

Born: July 10, 1856, Smiljan, Croatia
Died: January 7, 1943, New York City, NY

Tesla immigrated to the United States in 1884 and briefly worked 
with Thomas Edison before the two parted ways due to conflicting 
business and scientific interests. He later established his own 
laboratory and developed numerous revolutionary inventions, 
including the Tesla coil, induction motor, and wireless transmission 
technologies.

Despite his brilliance, Tesla struggled financially in his later years
and died impoverished in a New York hotel room. His legacy was 
largely overlooked during his lifetime but has since been recognized 
worldwide, with the Tesla unit of magnetic flux density named in his honor.
EOF
```

---

## Step 3: Extract Knowledge

Run the `parse` command to extract knowledge:

```bash
he parse tesla.md -t general/biography_graph -o ./output/ -l en
```

What this does:
- `-t general/biography_graph` — Use the biography graph template
- `-o ./output/` — Save results to the output directory
- `-l en` — Process in English

**Output:**
```
Input: tesla.md
Output: ./output/
Template: general/biography_graph
Language: en
Build Index: Yes

Template resolved: Biography Graph Template
✓ Knowledge extracted to ./output/

What's next?
  he show ./output/                    # Visualize knowledge graph
  he feed ./output/ <new_document>     # Append more documents
  he search ./output/ "keyword"        # Semantic search
  he talk ./output/ -i                 # Interactive chat
```

---

## Step 4: Visualize the Knowledge Graph

```bash
he show ./output/
```

This opens an interactive visualization in your browser, showing:
- **Entities** (people, places, events) as nodes
- **Relationships** as edges connecting the nodes

![Knowledge Graph Visualization](../../assets/en_show.jpg)

---

## Step 5: Search Your Knowledge Abstract

```bash
he search ./output/ "What were Tesla's major inventions?"
```

**Output:**
```
Found 3 result(s):

Result 1:
{
  "name": "Nikola Tesla",
  "type": "person",
  "description": "Serbian-American inventor..."
}
...
```

---

## Step 6: Chat with Your Knowledge

Interactive mode:

```bash
he talk ./output/ -i
```

Or ask a single question:

```bash
he talk ./output/ -q "Summarize Tesla's career in three sentences"
```

---

## Step 7: Incrementally Add Knowledge

Got more documents? Add them without reprocessing:

```bash
he feed ./output/ additional_document.md
```

Then visualize the updated knowledge:

```bash
he show ./output/
```

---

## What's Next?

Your knowledge abstract is a living artifact — as your source documents change:

- **Update** a document: `he feed ./ka/ updated-doc.md --source doc-1` (re-feed under the same source to upsert)
- **Roll back** a document: `he remove ./ka/ --document doc-1`
- **Tag and scope** your searches: `he tag ./ka/ --source doc-1 --add legal`
- **Audit** the ledger: `he info ./ka/ --sources`

→ [Managing Documents Over Time](../cli/commands/managing-documents.md) — the complete guide

## Complete Workflow

Here's the typical workflow:

```bash
# 1. Extract knowledge
he parse document.md -t general/biography_graph -o ./output/ -l en

# 2. Visualize
he show ./output/

# 3. Search
he search ./output/ "your query"

# 4. Chat
he talk ./output/ -i

# 5. Add more documents
he feed ./output/ another_document.md

# 6. Rebuild index if needed
he build-index ./output/
```

---

## What's Next?

- [CLI Workflow Guide](../cli/workflow.md) — Complete workflow walkthrough
- [All CLI Commands](../cli/index.md) — Detailed command reference
- [Template Library](../templates/index.md) — Find templates for your use case

---

## Troubleshooting

**"No API key found"**
→ Run `he config init -p openai -k YOUR_OPENAI_API_KEY` (or use `-p bailian`, `-p deepseek`, etc.)

**"Template not found"**
→ List available templates with `he list template`

**"Output directory already exists"**
→ Add `-f` flag to force overwrite, or choose a different output path
