# M-flow — Developer & Agent Reference

> This file is intended for AI coding assistants (Cursor, Copilot, etc.) and
> human contributors alike. It describes the repository layout, toolchain, and
> conventions needed to make changes safely.

---

## 1. Repository Map

```
m_flow/                 Python core (FastAPI + pipeline engine)
  api/                  HTTP routers: add, memorize, search, delete, …
  cli/                  CLI entrypoint (`mflow`)
  adapters/             DB adapters (graph, vector, cache)
  llm/                  LLM providers, prompts, structured output
  core/                 Domain models (Episode, Facet, FacetPoint, …)
  memory/               Memory processing (episodic, procedural)
  retrieval/            Search & retrieval algorithms
  pipeline/             Composable pipeline tasks & orchestration
  auth/                 Authentication & multi-tenancy
  eval/                 Evaluation harnesses & adapters
  shared/               Logging, settings, loaders, cross-cutting utilities
  tests/                Pytest suite (unit / integration / CLI)

m_flow-frontend/        Next.js console (pnpm)
m_flow-mcp/             MCP server — exposes memory as tool calls
mflow_workers/          Modal / worker helpers for distributed runs
examples/               Runnable demo scripts (Python, notebooks)
alembic/                SQL migration scripts (Alembic)
```

### Extension Points

- **New data source** → add a loader under `shared/loaders/`
- **New pipeline step** → add a task under `pipeline/`
- **New graph DB** → implement the adapter interface in `adapters/graph/`
- **New vector store** → implement adapter in `adapters/vector/`
- **New LLM provider** → extend `llm/LLMGateway.py`

---

## 2. Local Development

### Python backend (requires Python 3.10 – 3.13)

```bash
# Bootstrap
uv sync --dev --all-extras --reinstall

# Run the API server
uv run python -m m_flow.api.client

# CLI quick-start
uv run mflow add "M-flow builds structured memory for agents."
uv run mflow memorize
uv run mflow search "How does M-flow work?"
uv run mflow -ui          # launches backend + frontend + MCP
```

## Frontend console (Next.js / pnpm)

```bash
cd m_flow-frontend
pnpm install
pnpm dev              # http://localhost:3000
pnpm lint && pnpm build
```

### MCP server

```bash
cd m_flow-mcp
uv sync --dev --all-extras
uv run python src/server.py                  # stdio
uv run python src/server.py --transport sse  # SSE mode
```

See `m_flow-mcp/README.md` for Docker and API-mode options.

---

## 3. Quality Gates

### Tests

```bash
PYTHONPATH=. uv run pytest m_flow/tests/unit/ -v          # ~963 test cases
PYTHONPATH=. uv run pytest m_flow/tests/integration/ -v   # needs .env keys
```

Test layout:

| Directory | Scope |
|-----------|-------|
| `m_flow/tests/unit/` | Pure-logic, no network |
| `m_flow/tests/integration/` | Requires LLM / DB credentials |
| `m_flow/tests/cli_tests/` | CLI smoke tests |

### Linting & Formatting

```bash
uv run ruff check .       # lint (line-length 100, see pyproject.toml)
uv run ruff format .      # auto-format
uv run mypy m_flow/       # optional type-check
```

CI (`.github/workflows/`) runs the same commands; passing locally ≈ passing CI.

---

## 4. Conventions

### Code Style

| Aspect | Rule |
|--------|------|
| Indentation | 4 spaces (Python), 2 spaces (TS/YAML) |
| Naming | `snake_case` functions/modules, `PascalCase` classes |
| Type hints | Required on public API signatures |
| Error handling | Structured; use `m_flow.shared.logging_utils` |
| Imports | Sorted by `ruff`; no wildcard imports |

### Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
feat(graph): add temporal edge weighting
fix(api): handle missing auth cookie
docs: update installation instructions
```

### Pull Requests

1. Branch from `dev`.
2. Include scope, local test commands run, and any UI/MCP impacts.
3. Sign commits (`git commit -s`) and affirm the DCO (see `CONTRIBUTING.md`).
4. PR titles are validated by CI (`pr_lint` workflow).

---

## 5. Docker

```bash
docker compose up                       # backend only
docker compose --profile ui up          # backend + frontend
docker compose --profile neo4j up       # backend + Neo4j
```

Environment variables are documented in `.env.template`.
