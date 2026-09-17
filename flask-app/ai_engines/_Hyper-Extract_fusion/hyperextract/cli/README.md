# Hyper-Extract CLI

> **"Stop reading. Start understanding."**

A powerful command-line tool for extracting structured knowledge from unstructured text.

---

## ⚡ Quick Start

```bash
# Install
uv tool install hyperextract

# First-time setup
he config init

# Extract knowledge from a document
he parse document.md -o my_ka -l zh

# Visualize the knowledge graph
he show my_ka

# Search within your Knowledge Abstract
he search my_ka "key insights"
```

---

## ⚙️ Configuration

### One-Command Setup (Simplest)

```bash
# Just provide your API key - defaults work for most users
he config init --api-key YOUR_API_KEY

# With custom base URL
he config init -k YOUR_KEY -u https://your-endpoint.com/v1
```

This automatically configures both LLM and Embedder with:
- LLM: gpt-4o-mini
- Embedder: text-embedding-3-small

## Interactive Setup

```bash
he config init
```

### Manual Configuration

For advanced users who need separate configurations:

```bash
# Configure LLM
he config llm --api-key YOUR_KEY --model gpt-4o

# Configure Embedder
he config embedder --api-key YOUR_KEY --model text-embedding-3-small
```

## Environment Variables

You can also use environment variables as an alternative:

```bash
export OPENAI_API_KEY=your_api_key
export OPENAI_BASE_URL=https://api.openai.com/v1  # Optional
```

Environment variables take precedence over config file settings.

### View Current Configuration

```bash
he config show
```

---

## 📄 Parse Command

Extract knowledge from documents into structured Knowledge Abstracts.

### Basic Usage

```bash
# Parse with interactive template selection
he parse document.md -o my_ka -l zh

# Parse with specific template
he parse document.md -o my_ka -t general/knowledge_graph -l zh

# Parse with specific method
he parse document.md -o my_ka -m light_rag
```

## Options

- `<input>` - Input file path, directory, or `-` for stdin
- `-o, --output` - Output Knowledge Abstract directory (required)
- `-t, --template` - Template ID (omit for interactive selection)
- `-m, --method` - Method template (e.g., `light_rag`, `hyper_rag`)
- `-l, --lang` - Language (`zh` or `en`, required for knowledge templates)
- `-f, --force` - Force overwrite existing output
- `--no-index` - Skip building search index

### List Available Templates

```bash
he list template
he list template -l zh  # Filter by language
he list template -a graph  # Filter by type
he list template -q finance  # Search by keyword
```

### List Available Methods

```bash
he list method
he list method -q rag  # Search by keyword
```

---

## 🔍 Other Commands

### Build Search Index

Required for semantic search and chat functionality.

```bash
he build-index my_ka
he build-index my_ka --force  # Rebuild existing index
```

### Search Knowledge Abstract

Perform semantic search within your Knowledge Abstract.

```bash
he search my_ka "What are the key findings?"
he search my_ka "key insights" -n 5  # Return top 5 results
```

### Chat with Knowledge Abstract

Ask questions about your Knowledge Abstract.

```bash
# Single query
he talk my_ka -q "What was discussed in the meeting?"

# Interactive mode
he talk my_ka -i
```

## Visualize Knowledge Graph

View your Knowledge Abstract as an interactive graph.

```bash
he show my_ka
```

### View Knowledge Abstract Info

Display statistics and metadata about your Knowledge Abstract.

```bash
he info my_ka
```

### Add Knowledge to Existing KA

Append new knowledge to an existing Knowledge Abstract.

```bash
he feed my_ka new_document.md
```

---

## 📝 Examples

### Example 1: Extract Financial Data

```bash
# Configure API keys
he config init

# List finance templates
he list template -l zh | grep finance

# Extract earnings report
he parse earnings_report.md -o finance_ka -t finance/earnings_summary -l zh

# Build index for search
he build-index finance_ka

# Search for insights
he search finance_ka "What was the revenue growth?"
```

## Example 2: Extract Legal Contracts

```bash
# List legal templates
he list template -l zh | grep legal

# Extract contract information
he parse contract.md -o legal_ka -t legal/contract_summary -l zh

# View as knowledge graph
he show legal_ka
```

## Example 3: Use Method Templates

```bash
# Use Light RAG method
he parse document.md -o ka -m light_rag

# Use Hyper RAG method
he parse document.md -o ka -m hyper_rag
```

---

## ❓ FAQ

### Q: How do I choose between template and method?

**A:** Use **templates** when you need domain-specific extraction (finance, legal, medicine, etc.). Use **methods** when you want algorithm-driven extraction (RAG-based approaches).

### Q: Why do I need to build an index?

**A:** The index enables semantic search and chat functionality. Without it, you can still extract and visualize knowledge, but search and talk commands won't work.

### Q: How do I switch between languages?

**A:** Use the `-l` or `--lang` option:
- `-l zh` for Chinese
- `-l en` for English

### Q: Can I use custom API endpoints?

**A:** Yes! Configure with `--base-url` to use API-compatible endpoints:
```bash
he config llm --api-key YOUR_KEY --base-url https://your-custom-api.com/v1
```

### Q: Where is the configuration stored?

**A:** Configuration is stored in `~/.he/config.toml`

### Q: How do I update my API key?

**A:** Simply run the configuration command again:
```bash
he config llm --api-key NEW_API_KEY
```

---

## 🆘 Need Help?

```bash
# View all available commands
he --help

# View help for specific command
he parse --help
he config --help
he search --help
```

---

## 📚 Learn More

- [Full Documentation](../README.md)
- [Template Gallery](../templates/)
- [Examples](../examples/)
