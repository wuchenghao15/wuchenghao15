# Python SDK

Build knowledge extraction pipelines with the Hyper-Extract Python API.

---

## Installation

```bash
pip install hyperextract
```

For development, clone the repository and install the `dev` dependency group:

```bash
git clone https://github.com/yifanfeng97/hyper-extract.git
cd hyper-extract
uv sync
```

---

## Quick Example

```python
from hyperextract import Template

# Create template
ka = Template.create("general/biography_graph", language="en")

# Extract knowledge
with open("document.md") as f:
    result = ka.parse(f.read())

# Access data
print(f"Nodes: {len(result.nodes)}")
print(f"Edges: {len(result.edges)}")

# Build index for search/chat capabilities
result.build_index()

# Visualize
result.show()
```

![Interactive Visualization](../../assets/en_show.jpg)

---

## Core Classes

### Template

The main entry point for template-based extraction.

```python
from hyperextract import Template

# Create from preset
ka = Template.create("general/biography_graph", language="en")

# Create from custom YAML
ka = Template.create("/path/to/custom_template.yaml", language="en")

# Create from method
ka = Template.create("method/light_rag")
```

## Auto-Types

Eight data structure types for different extraction needs, plus `AutoDocument` for chunk-only corpora (`type: document` in YAML; no LLM extraction).

| Class | Use Case |
|-------|----------|
| `AutoModel` | Structured data models |
| `AutoList` | Ordered collections |
| `AutoSet` | Deduplicated collections |
| `AutoGraph` | Entity-relationship graphs |
| `AutoHypergraph` | Multi-entity relationships |
| `AutoTemporalGraph` | Time-based relationships |
| `AutoSpatialGraph` | Location-based relationships |
| `AutoSpatioTemporalGraph` | Combined time + space |

---

## API Overview

### Template API

```python
# Create
ka = Template.create(template_path, language="en")

# Extract
result = ka.parse(text)           # New extraction
result.feed_text(text)            # Add to existing
result.feed_text(text, source_id="doc-1")  # attribute the source
...
result.remove_source("doc-1")              # roll back this document's facts

# Delete (graph-family KAs)
result.remove_nodes("Apple")      # Hard-delete a node + its orphan edges
report = result.edit_node("Apple", remove_fact="...", dry_run=True)  # Soft-remove one fact

# Query
result.build_index()              # Build search index
results = result.search(query)    # Semantic search
response = result.chat(query)     # Chat with knowledge

# Persist
result.dump("./output/")          # Save to disk
result.load("./output/")          # Load from disk

# Visualize
result.show()                     # Interactive visualization
```

![Interactive Visualization](../../assets/en_show.jpg)

---

## Documentation Structure

- **[Quickstart](quickstart.md)** — Your first Python extraction
- **[Core Concepts](core-concepts.md)** — Template, AutoType, Method explained
- **Guides:**
  - [Using Templates](guides/using-templates.md)
  - [Using Methods](guides/using-methods.md)
  - [Working with Auto-Types](guides/working-with-autotypes.md)
  - [Search and Chat](guides/search-and-chat.md)
  - [Incremental Updates](guides/incremental-updates.md)
  - [Saving and Loading](guides/saving-loading.md)
- **API Reference:**
  - [Template](api-reference/template.md)
  - [Auto-Types](api-reference/autotypes/base.md)
  - [Methods](api-reference/methods/registry.md)

---

## Examples by Use Case

### Research Paper Analysis

```python
from hyperextract import Template

ka = Template.create("general/concept_graph", language="en")

with open("paper.md") as f:
    paper = ka.parse(f.read())

# Build searchable knowledge abstract
paper.build_index()

# Ask questions
response = paper.chat("What are the main contributions?")
print(response.content)
```

## Financial Report Extraction

```python
from hyperextract import Template

ka = Template.create("finance/earnings_summary", language="en")

report = ka.parse(earnings_text)
print(report.data.revenue)
print(report.data.eps)
```

### Building a Knowledge Abstract

```python
from hyperextract import Template

ka = Template.create("general/graph", language="en")

# Initial extraction
ka = ka.parse(doc1_text)

# Add more documents
ka.feed_text(doc2_text)
ka.feed_text(doc3_text)

# Save for later
ka.dump("./my_ka/")
```

---

## Configuration

### Environment Variables

```python
import os

os.environ["OPENAI_API_KEY"] = "your-api-key"
os.environ["OPENAI_BASE_URL"] = "https://api.openai.com/v1"
```

### Using .env File

```python
from dotenv import load_dotenv
load_dotenv()  # Loads from .env file
```

### Custom Clients

```python
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from hyperextract import Template

llm = ChatOpenAI(model="gpt-4o")
embedder = OpenAIEmbeddings(model="text-embedding-3-large")

ka = Template.create(
    "general/biography_graph",
    language="en",
    llm_client=llm,
    embedder=embedder
)
```

---

## Type Hints

Hyper-Extract is fully typed for IDE support:

```python
from hyperextract import Template, AutoGraph

ka: AutoGraph = Template.create("general/graph", "en")
result = ka.parse(text)

# IDE autocomplete works
nodes = result.nodes
edges = result.edges
```

---

## Next Steps

- Follow the [Quickstart](quickstart.md)
- Learn [Core Concepts](core-concepts.md)
- Browse [Guides](guides/using-templates.md)
- Read [API Reference](api-reference/template.md)
