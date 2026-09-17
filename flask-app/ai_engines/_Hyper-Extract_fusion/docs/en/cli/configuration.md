# CLI Configuration Reference

Configuration guide for Hyper-Extract CLI, supporting **OpenAI**, **Anthropic**, **DeepSeek**, **Alibaba Cloud Bailian**, and **Local vLLM** deployments.

---

## Quick Start

Choose your deployment method and follow the steps.

=== "OpenAI"

    ```bash
    he config init -p openai -k YOUR_OPENAI_API_KEY
    ```

    This creates `~/.he/config.toml` with OpenAI presets:
    - **LLM**: `gpt-4o-mini`
    - **Embedder**: `text-embedding-3-small`

=== "Bailian (Alibaba Cloud)"

    ```bash
    he config init -p bailian -k YOUR_BAILIAN_API_KEY
    ```

    This creates `~/.he/config.toml` with Bailian presets:
    - **LLM**: `qwen3.6-plus`
    - **Embedder**: `text-embedding-v4`

=== "Anthropic (Claude)"

    Anthropic provides LLM only — pair with an OpenAI-compatible embedder:

    ```bash
    he config llm -p anthropic -k YOUR_ANTHROPIC_API_KEY
    he config embedder -p openai -k YOUR_OPENAI_API_KEY
    ```

    This creates `~/.he/config.toml` with:
    - **LLM**: `claude-opus-4-8` (Anthropic)
    - **Embedder**: `text-embedding-3-small` (OpenAI)

=== "DeepSeek"

    DeepSeek provides LLM only — pair with an OpenAI-compatible embedder:

    ```bash
    he config llm -p deepseek -k YOUR_DEEPSEEK_API_KEY
    he config embedder -p openai -k YOUR_OPENAI_API_KEY
    ```

    This creates `~/.he/config.toml` with:
    - **LLM**: `deepseek-v4-flash` (DeepSeek, auto-disables thinking mode)
    - **Embedder**: `text-embedding-3-small` (OpenAI)

=== "Local vLLM"

    Start the LLM and Embedding services first, then configure separately:

    ```bash
    # LLM service
    he config llm -p vllm \
      -u http://localhost:8000/v1 \
      -k dummy \
      -m Qwen/Qwen3.5-9B

    # Embedding service
    he config embedder -p vllm \
      -u http://localhost:8001/v1 \
      -k dummy \
      -m BAAI/bge-m3
    ```

---

## Verify Configuration

```bash
he config show
```

=== "Cloud API (OpenAI / Bailian)"

    ```
    ┌─────────────────────────────────────────────────────────────┐
    │              Hyper-Extract Configuration                    │
    ├──────────┬──────────┬─────────────────────┬────────────┬────┤
    │ Service  │ Provider │ Model               │ API Key    │ ...│
    ├──────────┼──────────┼─────────────────────┼────────────┼────┤
    │ LLM      │ bailian  │ qwen3.6-plus        │ sk-xxxx... │ ...│
    │ Embedder │ bailian  │ text-embedding-v4   │ sk-xxxx... │ ...│
    └──────────┴──────────┴─────────────────────┴────────────┴────┘
    ```

=== "Local vLLM"

    ```
    ┌──────────────────────────────────────────────────────────────────┐
    │                Hyper-Extract Configuration                       │
    ├──────────┬──────────┬─────────────────────┬──────────┬───────────┤
    │ Service  │ Provider │ Model               │ API Key  │ Base URL  │
    ├──────────┼──────────┼─────────────────────┼──────────┼───────────┤
    │ LLM      │ vllm     │ Qwen/Qwen3.5-9B     │ dummy... │ localhost…│
    │ Embedder │ vllm     │ BAAI/bge-m3         │ dummy... │ localhost…│
    └──────────┴──────────┴─────────────────────┴──────────┴───────────┘
    ```

---

## CLI Command Reference

### Command Overview

| Command | Common Flags | Description |
|---------|-------------|-------------|
| `he config init` | `-p, --provider` — Provider preset<br>`-k, --api-key` — API key<br>`-u, --base-url` — Custom API endpoint | Initialize configuration (first time) |
| `he config llm` | `-p, --provider` — Provider<br>`-m, --model` — Model name<br>`-k, --api-key` — API key<br>`-u, --base-url` — Custom API endpoint<br>`--show` — Show current config<br>`--unset` — Clear configuration | Configure LLM |
| `he config embedder` | `-p, --provider` — Provider<br>`-m, --model` — Model name<br>`-k, --api-key` — API key<br>`-u, --base-url` — Custom API endpoint<br>`--show` — Show current config<br>`--unset` — Clear configuration | Configure embedder |
| `he config show` | — | View full configuration |

### Common Usage Examples

**Interactive initialization (recommended for first-time users):**

```bash
he config init
# Follow prompts to select provider, enter model name and API key
```

**View LLM configuration:**

```bash
he config llm --show
```

**Clear configuration (reset to defaults):**

```bash
he config llm --unset
he config embedder --unset
```

---

## Per-Platform Configuration Examples

=== "OpenAI"

    ```bash
    # One-click setup
    he config init -p openai -k sk-your-key

    # Or switch model
    he config llm -p openai -k sk-your-key -m gpt-4o
    ```

=== "Bailian (Alibaba Cloud)"

    ```bash
    # One-click setup (default qwen3.6-plus + text-embedding-v4)
    he config init -p bailian -k sk-your-key

    # Or switch model
    he config llm -p bailian -k sk-your-key -m qwen-plus
    ```

=== "Anthropic (Claude)"

    ```bash
    # LLM via Anthropic, Embedder via OpenAI
    he config llm -p anthropic -k sk-ant-your-key
    he config embedder -p openai -k sk-your-openai-key
    ```

=== "DeepSeek"

    ```bash
    # LLM via DeepSeek, Embedder via OpenAI
    he config llm -p deepseek -k sk-your-key
    he config embedder -p openai -k sk-your-openai-key
    ```

=== "Local vLLM"

    ```bash
    # Start services first, then configure separately
    he config llm -p vllm \
      -u http://localhost:8000/v1 \
      -k dummy \
      -m Qwen/Qwen3.5-9B

    he config embedder -p vllm \
      -u http://localhost:8001/v1 \
      -k dummy \
      -m BAAI/bge-m3
    ```

=== "Mixed Deployment"

    LLM and Embedder can use different providers:

    ```bash
    # LLM via Bailian, Embedding via local vLLM
    he config llm -p bailian -k sk-your-key
    he config embedder -p vllm \
      -u http://localhost:8001/v1 \
      -k dummy \
      -m BAAI/bge-m3

    # Or LLM via local, Embedding via Bailian
    he config llm -p vllm \
      -u http://localhost:8000/v1 \
      -k dummy \
      -m Qwen/Qwen3.5-9B
    he config embedder -p bailian -k sk-your-key
    ```

---

## Configuration File Details

Running `he config init` automatically creates `~/.he/config.toml`.

### File Location

- **Linux/macOS**: `~/.he/config.toml`
- **Windows**: `%USERPROFILE%\.he\config.toml`

On Linux/macOS, `he config` saves this file as mode `0600` (owner read/write only). If an existing file is group- or world-readable, the CLI warns on load and tightens the mode on the next save. Prefer environment variables over writing API keys into the file.

### Configuration Format

=== "Cloud API — Bailian"

    ```toml
    [llm]
    provider = "bailian"
    model = "qwen3.6-plus"
    api_key = "sk-your-api-key"
    base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"

    [embedder]
    provider = "bailian"
    model = "text-embedding-v4"
    api_key = ""
    base_url = ""
    ```

=== "Local vLLM"

    ```toml
    [llm]
    provider = "vllm"
    model = "Qwen/Qwen3.5-9B"
    api_key = "dummy"
    base_url = "http://localhost:8000/v1"

    [embedder]
    provider = "vllm"
    model = "BAAI/bge-m3"
    api_key = "dummy"
    base_url = "http://localhost:8001/v1"
    ```

=== "Mixed Deployment"

    ```toml
    [llm]
    provider = "bailian"
    model = "qwen3.6-plus"
    api_key = "sk-your-api-key"
    base_url = ""

    [embedder]
    provider = "vllm"
    model = "BAAI/bge-m3"
    api_key = "dummy"
    base_url = "http://localhost:8001/v1"
    ```

### Configuration Options

| Section | Key | Description | Default |
|---------|-----|-------------|---------|
| `[llm]` | `provider` | Provider preset | — |
| `[llm]` | `model` | LLM model name | Depends on provider preset |
| `[llm]` | `api_key` | API key | Required |
| `[llm]` | `base_url` | API base URL | Depends on provider preset |
| `[embedder]` | `provider` | Provider preset | — |
| `[embedder]` | `model` | Embedding model name | Depends on provider preset |
| `[embedder]` | `api_key` | API key (empty inherits from llm) | — |
| `[embedder]` | `base_url` | API base URL (empty inherits from llm) | — |

> See the [Provider System](../concepts/provider-system.md) compatibility table for default models per provider.

---

## Environment Variables

The following environment variables can be used as configuration fallback:

| Variable | Maps To | Example |
|----------|---------|---------|
| `OPENAI_API_KEY` | `llm.api_key`, `embedder.api_key` | `sk-...` |
| `OPENAI_BASE_URL` | `llm.base_url` | `https://api.openai.com/v1` |

**Priority Note:** Environment variables take precedence over config file, but are overridden by command-line flags.

**Use Cases:**
- Temporarily switch API keys
- Inject secrets in CI/CD environments
- Avoid hardcoding keys in config files

---

## Troubleshooting

=== "Cloud API Issues"

    **"API key not found"**

    ```bash
    he config init -p bailian -k YOUR_API_KEY
    ```

    **"The model does not exist" / 404**

    Check that the configured model name is available on the platform. See available models in [Provider System](../concepts/provider-system.md).

    **"Failed to connect to API"**

    ```bash
    # Check configuration
    he config llm --show

    # Reset base_url
    he config llm --base-url https://dashscope.aliyuncs.com/compatible-mode/v1
    ```

=== "Local vLLM Issues"

    **"Connection refused"**

    vLLM service is not running or has stopped:

    ```bash
    # Check if services are running
    curl http://localhost:8000/v1/models
    curl http://localhost:8001/v1/models

    # Restart services
    ```

    **"CUDA out of memory"**

    Lower `--gpu-memory-utilization` or use a smaller model / quantized version.

---

## See Also

- [`he config`](commands/config.md) — Detailed configuration command reference
- [Provider System](../concepts/provider-system.md) — Full model compatibility list
- [Installation Guide](../getting-started/installation.md) — Initial setup steps
