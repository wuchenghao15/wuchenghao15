# Copilot instructions for MTSCOS AI Project

## Repository shape

- The repository root contains project-level rules, configuration, scripts, documentation, and some legacy/generated artifacts.
- The canonical application code is the nested `flask-app/` repository. Make application changes there unless the task explicitly targets root-level tooling or documentation.
- `flask-app/server_real_db.py` is the production-style Flask entry point. `flask-app/app.py` is the modular application entry point used by the Docker image and quick/standard Compose profiles.
- `flask-app/routes/` and `flask-app/api/` define HTTP routes and blueprints; keep business logic in `flask-app/services/` or `flask-app/app/services/`.
- `flask-app/core/` owns shared infrastructure such as database-path routing, configuration, caching, and system services. Database access is SQLite-first and may be routed across the project’s shard/data directories.
- `flask-app/ai_engines/` contains AI/agent functionality; `flask-app/engines/` contains broader system engines. Do not put route handlers or ordinary business services in these directories.
- Jinja templates live in `flask-app/templates/`; browser assets live in `flask-app/static/` and `flask-app/src/html/`.
- Tests are primarily in `flask-app/tests/unit/`; the root `tests/` directory contains additional smoke/integration/system checks. Many tests import modules for side effects, so run them from the directory expected by the test and avoid changing the working-directory assumptions.

## Environment, initialization, and running

Use Python 3.9+ for the application. The main requirements file currently targets newer Python versions; use `flask-app/requirements-python39.txt` when working specifically on Python 3.9.

```bash
# 首次启动 (macOS · Metal iGPU 原生 · v22.1.0)
cd flask-app
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Python 必须用系统 3.9 (Code CLT), 不能用 brew python
PYTHON="/Library/Developer/CommandLineTools/Library/Frameworks/Python3.framework/Versions/3.9/bin/python3"

# 启动 Flask: modular_start.py 自动 patch Thread.__init__ + patch_sqlite3_connect
# (33 关键词拦截后台线程 · 纯 HTTP · WAL 强制 · db_path 修正)
$PYTHON modular_start.py    # 直接跑, 不需要 --host/--port 参数

# 健康检查
curl -s --max-time 5 http://127.0.0.1:8888/api/autosync/health | head -c 200
# Ollama: localhost:11435 (launch agent com.mtscos.ollama-native · Metal iGPU)
ollama list  # 应输出 5 模型: qwen2.5:14b 🥇 + coder:14b 🆕 + 7b 兜底 + embed
```

> **v22.1.0 架构变更**：项目已从 Docker/Compose 转型为 **macOS Metal iGPU 原生部署**。Ollama launch agent (`com.mtscos.ollama-native`) 负责模型推理 (端口 11435)，Flask Thread patch 让 Flask 进程变纯 HTTP server，守护任务由 `ai_smart_mount_engine` 独立进程管理。Docker 历史配置仍保留但不再作为主部署路径。

## AI model and engine conventions

- **Local AI 优先** (零 token)：Ollama `localhost:11435` (launch agent · Metal iGPU · 24GB 共享).
  Models: `qwen2.5:14b` 🥇 dev 档通用主力 · `qwen2.5:7b` 🥈 通用兜底 ·
  `qwen2.5-coder:14b` 🆕 neural_hub 代码主力 · `qwen2.5-coder:7b` 代码兜底 ·
  `nomic-embed-text` 768维向量 (仙女座 Stage 2).
- **3-tier fallback**: local 14b → local 7b → Volcengine ARK 🛡️ (云端兜底 · 133 模型).
  Default: `doubao-seed-2-0-lite` (3.6s). API key in `_runtime/config/ai_secrets.json` (gitignore).
- **Do NOT hard-code model names**. Use `ai_engines/ai_ollama_engine._select_model(use_coder=...)`
  or `engines/andromeda_auto_evolution.DERIVE_MODEL`. These auto-follow tier/machine detection.
- **Flask is pure HTTP server** (`modular_start.py` patches `Thread.__init__`, 33 关键词 neutralize
  daemon threads). Do NOT start long-running threads inside Flask routes — use `ai_smart_mount_engine`
  or `engines/` module-level loops instead.
- **SQLite WAL forced** at `core/db_path.patch_sqlite3_connect()`. Never open raw SQLite connections
  bypassing this — you will hit lock deadlocks. Real DB is `flask-app/database/app.db` (396MB);
  root-level `app.db` (5.6MB) is an empty stub.
- **Andromeda Evolution Engine** (`engines/andromeda_auto_evolution.py`) — 7-stage cycle
  (eigenflux_ingest → auto_detect → auto_retrieve → auto_associate → **auto_derive** 🥇 AI inference
  → auto_reinforce → auto_expand → auto_optimize · 26.9s/cycle). Do NOT modify `auto_derive` prompt
  system without rule review. Produces AE-* prefixed knowledge and drives eigenflux self-bootstrap.
- **autosync_andromeda.py** — Mac mini ↔ dev machine bidirectional sync. Checkpoint path is
  `~/Library/Application Support/MTSCOS AI/autosync_checkpoint.json` (OneDrive-conflict isolation —
  do NOT change this path). text_uuid tables use DELETE(PK)+INSERT UPSERT.


## Tests and checks

Run tests from the directory that owns them:

```bash
# Application tests
cd flask-app
python3 -m pytest tests/ -x

# One application test module or one test
python3 -m pytest tests/unit/test_login.py -q
python3 -m pytest tests/unit/test_login.py -k "login" -q

# Root-level system tests
cd ..
python3 -m pytest tests/ -x
python3 -m pytest tests/test_app_start.py -q
```

The CI workflows use these checks:

```bash
flake8 flask-app/app/ flask-app/ai_engines/ --count --select=E9,F63,F7,F82 --show-source --statistics
flake8 flask-app/app/ flask-app/ai_engines/ --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics
python3 -m py_compile flask-app/server_real_db.py
python3 -m py_compile flask-app/scripts/tools/mtscos_system_test_engine.py
```

Some historical CI jobs run `pytest tests/ -v` with a non-failing fallback when no tests are found; do not treat that fallback as proof that a failing test is acceptable. The CI/CD workflow also runs coverage, dependency audit, Bandit, and Trivy checks.

## Codebase-specific conventions

- Follow the directory responsibilities documented in `.trae/rules/开发规则.md`: routes stay in route modules, domain behavior stays in services, infrastructure stays in `core/`, and operational tooling stays in `scripts/`.
- Prefer the existing database path/router helpers (`core.db_path` and related `core.services` modules) instead of hard-coding database paths or opening a new database location.
- Preserve the application’s import/bootstrap order. `app.py` patches database connections and imports the database router before loading the Flask application; moving those imports can change route registration and database selection.
- Register new HTTP endpoints through the existing blueprint registration pattern (`routes/api_blueprint_registrar.py`) and match the surrounding authentication, session, response, and error-handling decorators.
- Configuration and secrets come from environment/config files. Do not commit credentials, private keys, `.env` values, runtime databases, logs, uploads, or generated backup files.
- Keep new runtime files out of the repository root; place code, configuration, migrations, tests, templates, and static assets in their designated application directories.
- Existing code uses both Chinese and English identifiers/messages. Preserve the local terminology and surrounding language when editing a module; do not perform broad language or formatting rewrites.
- Use 4-space Python indentation and `snake_case` for Python symbols. Frontend JavaScript uses ES6+ and 2-space indentation; CSS follows the project’s BEM-oriented naming.
- Commit and PR titles follow Conventional Commits (`feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`, etc.). PRs should use `.github/PULL_REQUEST_TEMPLATE.md` and identify affected tests/docs.
- Before changing behavior, consult the active `.trae/rules/` documents, especially `开发规则.md`, `设计规范.md`, and `§14强制开发12步骤独立约束规则.md`; these are repository-specific policy/configuration documents, not generic framework documentation.
- Treat `00-规则总索引.md` and `规则治理与一致性规范.md` as the source of truth for active-rule scope, precedence, dependencies, and conflict handling. Run `bash scripts/validate_rules.sh` after rule changes.
- For protected data, use `机密等级与访问控制规范.md`, `PermissionManager.can_access_classification()`, and `db_encryption.classify_table()`; never invent a local role or sensitivity check.
