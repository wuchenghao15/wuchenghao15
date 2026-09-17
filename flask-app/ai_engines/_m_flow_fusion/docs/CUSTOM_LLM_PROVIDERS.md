# Using Custom (OpenAI-Compatible) LLM Providers with M-Flow

M-Flow ships with a **`custom` provider** that lets you connect any
LLM endpoint that speaks the OpenAI chat-completions wire format.
This covers a wide range of third-party and self-hosted models,
including DeepSeek, Qwen (Tongyi Qianwen), Moonshot (Kimi),
Yi (01.AI), Zhipu (GLM), Groq, Together AI, local Ollama instances
behind an OpenAI-compatible proxy, and many others.

This guide explains how to configure the custom provider, lists
recommended presets for popular models, and describes common
pitfalls with their solutions.

---

## Quick Start

Set the following environment variables (or add them to your `.env` file)
and M-Flow will automatically route all LLM calls through your chosen
endpoint:

```bash
# Required
export MFLOW_LLM_PROVIDER=custom
export MFLOW_LLM_MODEL=deepseek-chat          # model identifier at the provider
export MFLOW_LLM_ENDPOINT=https://api.deepseek.com  # base URL (no trailing /v1)
export MFLOW_LLM_API_KEY=sk-your-key-here

# Optional — tune structured-output strategy
export MFLOW_LLM_INSTRUCTOR_MODE=json_mode     # see "Instructor Modes" below
export MFLOW_LLM_MAX_COMPLETION_TOKENS=4096
```

That is all. No code changes are needed — `create_llm_backend()` will
instantiate a `GenericAPIAdapter` that wraps LiteLLM + Instructor for
schema-validated structured output.

---

## Recommended Presets for Popular Providers

The table below lists tested configurations for widely used
OpenAI-compatible providers. Copy the environment block that matches
your provider and adjust the API key.

| Provider | `MFLOW_LLM_MODEL` | `MFLOW_LLM_ENDPOINT` | Instructor Mode | Notes |
|---|---|---|---|---|
| **DeepSeek** | `deepseek-chat` | `https://api.deepseek.com` | `json_mode` | Supports JSON mode natively since V3. |
| **Qwen (DashScope)** | `qwen-plus` | `https://dashscope.aliyuncs.com/compatible-mode` | `json_mode` | Use the OpenAI-compatible endpoint, not the native DashScope SDK. |
| **Moonshot (Kimi)** | `moonshot-v1-128k` | `https://api.moonshot.cn` | `json_mode` | 128k context window; ideal for long conversation histories. |
| **Yi (01.AI)** | `yi-large` | `https://api.lingyiwanwu.com` | `json_mode` | Also supports `yi-medium` and `yi-vision`. |
| **Zhipu (GLM)** | `glm-4-plus` | `https://open.bigmodel.cn/api/paas` | `json_mode` | Requires the `/api/paas` path suffix. |
| **Groq** | `llama-3.3-70b-versatile` | `https://api.groq.com/openai` | `json_mode` | Extremely fast inference; good for development. |
| **Together AI** | `meta-llama/Llama-3.3-70B-Instruct-Turbo` | `https://api.together.xyz` | `json_mode` | Full model path required. |
| **OpenRouter** | `openai/gpt-4o` | `https://openrouter.ai/api` | `json_mode` | Prefix model name with provider. |
| **Local (Ollama)** | `llama3.2` | `http://localhost:11434` | `json_mode` | Use the dedicated `ollama` provider for native support, or `custom` for the OpenAI-compat shim. |

---

## Instructor Modes

M-Flow uses [Instructor](https://github.com/jxnl/instructor) to coerce
raw LLM output into Pydantic models. The `MFLOW_LLM_INSTRUCTOR_MODE`
variable controls which strategy Instructor uses:

| Mode | Description | When to Use |
|---|---|---|
| `json_mode` | Requests `response_format: { type: "json_object" }` | Default. Works with most OpenAI-compatible providers. |
| `tool_call` | Uses the function/tool-calling API | Providers with strong tool-call support (OpenAI, Anthropic). |
| `markdown_json_mode` | Extracts JSON from Markdown code fences | Fallback for providers that do not support `json_mode`. |

If structured output fails with your provider, try switching to
`markdown_json_mode` — it is the most universally compatible option.

---

## Fallback Configuration

M-Flow supports an optional fallback LLM that activates automatically
when the primary model returns a content-policy violation. This is
useful when your primary model has aggressive content filters:

```bash
export MFLOW_FALLBACK_MODEL=gpt-4o-mini
export MFLOW_FALLBACK_ENDPOINT=https://api.openai.com
export MFLOW_FALLBACK_API_KEY=sk-openai-key
```

The fallback is only invoked on `ContentPolicyFilterError`; all other
errors (rate limits, network timeouts) are handled by the built-in
retry logic (exponential back-off, 120 s ceiling).

---

## Common Pitfalls

### "Model not found" errors

LiteLLM maintains an internal model registry. If your model is not in
that registry, prefix the model name with `openai/` to force the
OpenAI-compatible code path:

```bash
export MFLOW_LLM_MODEL=openai/my-custom-model
```

### Structured output returns raw text

Some providers ignore `response_format` silently. Switch to
`markdown_json_mode`:

```bash
export MFLOW_LLM_INSTRUCTOR_MODE=markdown_json_mode
```

### Rate limiting

Enable M-Flow's built-in rate limiter to stay within provider quotas:

```bash
export MFLOW_LLM_RATE_LIMIT_ENABLED=true
export MFLOW_LLM_RATE_LIMIT_REQUESTS=30    # requests per interval
export MFLOW_LLM_RATE_LIMIT_INTERVAL=60    # interval in seconds
```

### Endpoint URL format

Some providers expect the base URL without `/v1`, others with it.
LiteLLM appends `/v1/chat/completions` automatically, so in most
cases you should **omit** the `/v1` suffix:

```bash
# Correct
export MFLOW_LLM_ENDPOINT=https://api.deepseek.com

# Usually wrong (double /v1)
export MFLOW_LLM_ENDPOINT=https://api.deepseek.com/v1
```

---

## Architecture Overview

```
┌─────────────────────────────────────────────────┐
│                  M-Flow Core                     │
│                                                  │
│  extract_structured(text, prompt, ResponseModel) │
└────────────────────┬────────────────────────────┘
                     │
          ┌──────────▼──────────┐
          │  GenericAPIAdapter   │  ← MFLOW_LLM_PROVIDER=custom
          │  (generic_llm_api)   │
          └──────────┬──────────┘
                     │
          ┌──────────▼──────────┐
          │  Instructor          │  ← Schema validation
          │  + LiteLLM           │  ← HTTP transport
          └──────────┬──────────┘
                     │
          ┌──────────▼──────────┐
          │  Any OpenAI-compat   │
          │  endpoint             │
          │  (DeepSeek, Qwen, …) │
          └─────────────────────┘
```

The `GenericAPIAdapter` implements the `LLMBackend` protocol, which
requires a single async method: `extract_structured()`. This method
accepts free-form text, a system prompt, and a Pydantic response model,
then returns a validated instance of that model. The adapter delegates
HTTP transport to LiteLLM and schema enforcement to Instructor.

---

## Verifying Your Setup

After configuring environment variables, run the built-in smoke test:

```bash
python -c "
import asyncio
from pydantic import BaseModel
from m_flow.llm.backends.litellm_instructor.llm.get_llm_client import create_llm_backend

class TestResponse(BaseModel):
    greeting: str

async def main():
    backend = create_llm_backend()
    result = await backend.extract_structured(
        text_input='Say hello',
        system_prompt='Respond with a JSON greeting.',
        response_model=TestResponse,
    )
    print(f'Success: {result.greeting}')

asyncio.run(main())
"
```

If this prints a greeting, your custom provider is correctly configured.
