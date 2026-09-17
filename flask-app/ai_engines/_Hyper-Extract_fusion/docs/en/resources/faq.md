# Frequently Asked Questions

Common questions about Hyper-Extract.

---

## General

### What is Hyper-Extract?

Hyper-Extract is an LLM-powered knowledge extraction framework that transforms unstructured text into structured knowledge graphs, lists, models, and more.

### What can I use it for?

- Research paper analysis
- Knowledge base construction
- Document processing
- Information extraction
- Question-answering systems

### Is it free?

The software is open-source (Apache-2.0). You need an API key from a supported LLM provider (OpenAI, Anthropic, DeepSeek, Alibaba Bailian, or local vLLM).

---

## Installation

### What are the requirements?

- Python 3.11+
- An API key from any supported provider (OpenAI, Anthropic, DeepSeek, Bailian, or local vLLM)

### How do I install it?

```bash
pip install hyperextract
```

### Installation fails with "No module named 'hyperextract'"

Try:
```bash
pip install --upgrade hyperextract
```

Or use a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install hyperextract
```

---

## Configuration

### Where do I set my API key?

**Option 1**: CLI

```bash
# OpenAI / Bailian (one-step)
he config init -p openai -k YOUR_API_KEY
he config init -p bailian -k YOUR_API_KEY

# Anthropic / DeepSeek (LLM + separate embedder)
he config llm -p deepseek -k YOUR_DEEPSEEK_API_KEY
he config embedder -p openai -k YOUR_OPENAI_API_KEY
```

**Option 2**: Environment variable

```bash
export OPENAI_API_KEY=your-api-key        # OpenAI/Bailian
export ANTHROPIC_API_KEY=your-api-key     # Anthropic
export DEEPSEEK_API_KEY=your-api-key      # DeepSeek
```

**Option 3**: `.env` file
```
OPENAI_API_KEY=your-api-key
```

## Can I use a different LLM provider?

Yes! Hyper-Extract supports OpenAI, Anthropic, DeepSeek, Alibaba Bailian, and local vLLM out of the box:

```bash
# OpenAI / Bailian
he config init -p openai -k YOUR_API_KEY

# DeepSeek / Anthropic (LLM only, pair with OpenAI embedder)
he config llm -p deepseek -k YOUR_DEEPSEEK_API_KEY
he config embedder -p openai -k YOUR_OPENAI_API_KEY
```

For custom OpenAI-compatible endpoints:
```bash
he config llm --base-url https://your-provider.com/v1 -k YOUR_API_KEY
```

See [Provider System](../concepts/provider-system.md) for the full compatibility list.

## Which models are supported?

- **OpenAI**: gpt-4o, gpt-4o-mini, gpt-5
- **Anthropic**: claude-opus-4-8, claude-sonnet-4-6, claude-haiku-4-5
- **DeepSeek**: deepseek-v4-flash, deepseek-v4-pro
- **Alibaba Bailian**: qwen-plus, qwen-turbo, qwen3.6-plus
- **Local vLLM**: Any model served via vLLM (e.g. Qwen/Qwen3.5-9B)

See [Provider System](../concepts/provider-system.md) for the full compatibility table.

---

## Usage

### Which template should I use?

See the [How to Choose](../templates/how-to-choose.md) guide or use:
```bash
he list template
```

### How do I process a PDF?

Feed it directly (requires the optional ingest extra — also supports Word, PowerPoint, Excel, HTML, EPUB and more):
```bash
pip install "hyperextract[ingest]"
he parse document.pdf -t general/graph -o ./ka/ -l en
```

Scanned (image-only) PDFs have no text layer — run OCR first. See [he parse](../cli/commands/parse.md) for the full format table.

### Can I process multiple documents?

**Option 1**: Feed incrementally
```bash
he parse doc1.md -t general/graph -o ./ka/ -l en
he feed ./ka/ doc2.md
he feed ./ka/ doc3.md
```

**Option 2**: Process directory
```bash
he parse ./docs/ -t general/graph -o ./ka/ -l en
```

### How do I extract in Chinese?

```bash
he parse doc.md -t general/biography_graph -l zh
```

### How do I delete knowledge from an existing KA?

```bash
# Hard-delete a node (edges anchored by it are removed too)
he remove ./ka/ --node Apple

# Soft-remove one wrong/obsolete fact, keeping the rest of the node
he remove ./ka/ --edit-node Apple --fact "founded by Steve Jobs" --dry-run
he remove ./ka/ --edit-node Apple --fact "founded by Steve Jobs" -y
```

Soft delete uses the LLM to rewrite the item under the same schema, with a key-invariance check and an automatic `data.json` backup. To delete **everything a specific document contributed**, rebuild the KA without that document — per-document provenance tracking is not implemented yet. See [`he remove`](../cli/commands/remove.md).

---

## Performance

### Why is extraction slow?

- Long documents are chunked and processed in parallel
- Each chunk requires an LLM call
- Consider using `--no-index` during batch processing

### How can I speed it up?

1. Use smaller chunk sizes
2. Reduce `max_workers` if hitting rate limits
3. Process documents in parallel (manually)

### Memory issues with large documents?

Process in smaller batches:
```python
for batch in chunks(documents, 5):
    for doc in batch:
        ka.feed_text(doc)
    ka.dump("./checkpoint/")
```

---

## Results

### Where is my data stored?

```
./output/
├── data.json      # Extracted knowledge
├── metadata.json  # Extraction info
└── index/         # Search index
```

### How do I visualize results?

```bash
he show ./output/
```

Or in Python:
```python
# Build index for interactive search/chat in visualization
result.build_index()

result.show()
```

![Interactive Visualization](../../assets/en_show.jpg)

## Can I export to other formats?

```python
import json

# To JSON
json_data = result.data.model_dump_json()

# To dict
data_dict = result.data.model_dump()
```

---

## Troubleshooting

### "API key not found"

```bash
# Specify your provider
he config init -p openai -k YOUR_API_KEY
# or: -p bailian, -p deepseek, etc.
```

## "Template not found"

List available templates:
```bash
he list template
```

### "Index not found" error

Build the index:
```bash
he build-index ./output/
```

### Search returns no results

Try:
- Different search terms
- Increase `top_k`: `he search ./ka/ "query" -n 10`
- Check if index is built: `he info ./ka/`

---

## Advanced

### Can I create custom templates?

Yes! See [Custom Templates](../python/guides/custom-templates.md).

### Can I use my own extraction method?

Yes, implement and register:
```python
from hyperextract.methods import register_method

class MyMethod:
    def extract(self, text):
        # Your logic
        pass

register_method("my_method", MyMethod, "graph", "Description")
```

### How do I integrate with my application?

```python
from hyperextract import Template

class MyApp:
    def __init__(self):
        self.ka = Template.create("general/graph", "en")
    
    def process_document(self, text):
        return self.ka.parse(text)
```

---

## Getting More Help

- [GitHub Issues](https://github.com/yifanfeng97/hyper-extract/issues)
- [Troubleshooting Guide](troubleshooting.md)
- [CLI Documentation](../cli/index.md)
- [Python SDK](../python/index.md)
