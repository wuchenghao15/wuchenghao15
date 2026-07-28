<div align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="static/images/logo.svg">
    <img alt="MTSCOS AI Logo" src="static/images/logo.svg" width="120" height="120">
  </picture>

  <h1>MTSCOS AI — MTS Architecture Intelligent Learning &amp; Assessment Platform</h1>
  <p>
    <b>Distributed, AI-driven, MTS-Architecture (v2.0) powered Exam &amp; Adaptive Learning Platform.</b><br>
    Auto-generates questions, composes papers, diagnoses weaknesses, personalizes learning paths,
    audits RBAC+ABAC permissions, and orchestrates <b>550+ AI Employees / Engines and 47 Agents</b> as a self-healing staff —
    end-to-end, K12 through Lifelong Education.
  </p>

  <p>
    <a href="README.zh-CN.md">
      <img src="https://img.shields.io/badge/%E4%B8%AD%E6%96%87-%E8%AF%BB%E6%88%91-ff5722?style=for-the-badge&logo=readme&logoColor=white" alt="中文文档">
    </a>
    &nbsp;
    <a href="#getting-started--quick-start">
      <img src="https://img.shields.io/badge/Get%20Started-2ea44f?style=for-the-badge&logo=rocket&logoColor=white" alt="Get Started">
    </a>
    &nbsp;
    <a href="https://github.com/wuchenghao15/MTSCOS-AI-Project/releases">
      <img src="https://img.shields.io/badge/Releases-v17.22.0-purple?style=for-the-badge&logo=semver&logoColor=white" alt="Releases">
    </a>
  </p>
</div>

---

<div align="center">

<!-- ── GitHub Metrics ── -->
[![GitHub stars](https://img.shields.io/github/stars/wuchenghao15/MTSCOS-AI-Project?style=for-the-badge&logo=github&color=ffd60a&labelColor=2b2b2b)](https://github.com/wuchenghao15/MTSCOS-AI-Project/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/wuchenghao15/MTSCOS-AI-Project?style=for-the-badge&logo=github&color=8ecae6&labelColor=2b2b2b)](https://github.com/wuchenghao15/MTSCOS-AI-Project/network/members)
[![GitHub watchers](https://img.shields.io/github/watchers/wuchenghao15/MTSCOS-AI-Project?style=for-the-badge&logo=github&color=a2d2ff&labelColor=2b2b2b)](https://github.com/wuchenghao15/MTSCOS-AI-Project/watchers)
[![GitHub contributors](https://img.shields.io/github/contributors/wuchenghao15/MTSCOS-AI-Project?style=for-the-badge&logo=github&color=06d6a0&labelColor=2b2b2b)](https://github.com/wuchenghao15/MTSCOS-AI-Project/graphs/contributors)
[![Last Commit](https://img.shields.io/github/last-commit/wuchenghao15/MTSCOS-AI-Project/main?style=for-the-badge&logo=git&color=ef476f&labelColor=2b2b2b)](https://github.com/wuchenghao15/MTSCOS-AI-Project/commits/main)
[![Commit Activity](https://img.shields.io/github/commit-activity/m/wuchenghao15/MTSCOS-AI-Project?style=for-the-badge&logo=git&color=118ab2&labelColor=2b2b2b)](https://github.com/wuchenghao15/MTSCOS-AI-Project/pulse)

<br>

<!-- ── Repo Health & Quality ── -->
[![Version](https://img.shields.io/badge/version-v17.22.0_–_SuperAdmin_UX_Unified_Edition-f77f00?style=for-the-badge&logo=semver&logoColor=white)](docs/CHANGELOG.md)
[![Python](https://img.shields.io/badge/python-3.9_%7C_3.10_%7C_3.11_%7C_3.12-3776AB?style=for-the-badge&logo=python&logoColor=ffd54f&labelColor=2b2b2b)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/flask-3.x-000000?style=for-the-badge&logo=flask&logoColor=white&labelColor=2b2b2b)](https://flask.palletsprojects.com/)
[![SQLite](https://img.shields.io/badge/sqlite-3.x%2B-003B57?style=for-the-badge&logo=sqlite&logoColor=white&labelColor=2b2b2b)](https://www.sqlite.org/)
[![License](https://img.shields.io/github/license/wuchenghao15/MTSCOS-AI-Project?style=for-the-badge&logo=opensourceinitiative&color=0ead69&labelColor=2b2b2b)](LICENSE)
[![Code Size](https://img.shields.io/github/languages/code-size/wuchenghao15/MTSCOS-AI-Project?style=for-the-badge&color=9d4edd&labelColor=2b2b2b)](https://github.com/wuchenghao15/MTSCOS-AI-Project)
[![Repo Size](https://img.shields.io/github/repo-size/wuchenghao15/MTSCOS-AI-Project?style=for-the-badge&color=2d00f7&labelColor=2b2b2b)](https://github.com/wuchenghao15/MTSCOS-AI-Project)
[![Top Language](https://img.shields.io/github/languages/top/wuchenghao15/MTSCOS-AI-Project?style=for-the-badge&labelColor=2b2b2b)](https://github.com/wuchenghao15/MTSCOS-AI-Project)

<br>

<!-- ── CI/CD, Security & Bot Status ── -->
[![CI/CD Pipeline](https://img.shields.io/github/actions/workflow/status/wuchenghao15/MTSCOS-AI-Project/ci-cd.yml?branch=main&label=CI%2FCD&style=for-the-badge&logo=githubactions&color=118ab2&labelColor=2b2b2b)](https://github.com/wuchenghao15/MTSCOS-AI-Project/actions/workflows/ci-cd.yml)
[![Dependabot](https://img.shields.io/badge/Dependabot-Active-025e4b?style=for-the-badge&logo=dependabot&logoColor=white&labelColor=2b2b2b)](.github/dependabot.yml)
[![Security: Bandit + pip-audit + Trivy](https://img.shields.io/badge/Security-Bandit_%2B_pip_audit_%2B_Trivy-sandybrown?style=for-the-badge&logo=snyk&logoColor=white&labelColor=2b2b2b)](docs/SECURITY.md)
[![CodeQL](https://img.shields.io/badge/CodeQL-Enabled-success?style=for-the-badge&logo=github&labelColor=2b2b2b)](.github/workflows/ci-cd.yml)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg?style=for-the-badge&logo=github&labelColor=2b2b2b)](docs/CONTRIBUTING.md)
[![Open Issues](https://img.shields.io/github/issues/wuchenghao15/MTSCOS-AI-Project?style=for-the-badge&logo=github&color=ffba08&labelColor=2b2b2b)](https://github.com/wuchenghao15/MTSCOS-AI-Project/issues)
[![GitHub Discussions](https://img.shields.io/badge/Discussions-Join_us!-5865F2?style=for-the-badge&logo=github&labelColor=2b2b2b)](https://github.com/wuchenghao15/MTSCOS-AI-Project/discussions)

</div>

---

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://cdn.jsdelivr.net/gh/thmsgbrt/mtscos-preview-assets@main/hero-dark.svg">
  <img alt="Preview banner" src="https://raw.githubusercontent.com/andreasbm/readme/master/assets/lines/solar.png" width="100%">
</picture>

---

## Why MTSCOS AI

K-12, adult-education and higher-ed educators spend **80% of their working hours** on mechanical drudgery: composing papers, grading homework, tabulating exam results, diagnosing weak knowledge points, writing study plans, and hunting for question-bank content.

MTSCOS AI replaces all of that with **a self-staffing "AI school district"** — 550+ specialized AI employees/engines and 47 Agents each own a responsibility (question generation, paper composition, homework grading, diagnostics, learning planning, firewall & audit, layout adjusting, git ops, etc.) orchestrated by the **MTS Architecture v2.0 (Multi-Agent Twin-Track Self-evolving Collaborative Architecture)**. Plug in text → get graded exams + personalized learning paths, automatically.

> **MTSCOS** = **M**ulti-Agent **T**win-Track **S**elf-evolving **C**ollaborative **O**perating **S**ystem

---

## Design Philosophy & Inspiration

### The "AI School District" Vision

MTSCOS AI was born from a simple yet audacious question: **What if we could automate not just one task, but an entire educational ecosystem?**

Instead of building isolated AI tools, we imagined a **self-governing AI school district** where every role — teacher, tutor, grader, proctor, security officer, IT administrator, and more — is performed by specialized AI employees who work together seamlessly.

### Core Design Principles

| Principle | Description |
| :--- | :--- |
| **Human-in-the-Loop by Design** | AI employees handle the drudgery, humans focus on creative teaching and decision-making |
| **Self-Evolution** | The system continuously learns from data, user interactions, and external knowledge sources |
| **Decentralized Intelligence** | 550+ AI employees/engines and 47 Agents each master their domain, collaborating like a real team |
| **Security as DNA** | Every component is built with enterprise-grade security from the ground up |
| **Zero-Config Experience** | Out-of-the-box functionality with intelligent defaults; complexity hidden until needed |

### The MTS Architecture Story

The MTS architecture evolved from observing how successful educational institutions operate:
1. **Plan Engine** → Like a school principal: understands intent, allocates resources, makes strategic decisions
2. **Worker Agents** → Like specialized teachers/staff: each excels at one responsibility
3. **Fabric** → Like the school infrastructure: databases, communication, monitoring, backups

The "Twin-Track" in MTS refers to the dual flow:
- **Learning Track**: Question generation → Exam composition → Grading → Diagnosis → Learning Path
- **Ops Track**: Security → Maintenance → Monitoring → Upgrades → Recovery

### Future Direction

We're building toward a **Role-Twin AI School District** where every teacher and student gets their own AI twin:
- Personal AI tutors that know each student's learning style
- AI teaching assistants that understand each teacher's methodology
- Twin-to-twin collaboration graphs for peer learning and knowledge sharing

---

## Highlights (what makes this repo different)

| Pillar | Capability |
| :---: | :--- |
| **MTS Architecture v2.0** | Dual-engine layered pipeline: *Plan Engine* (strategy) + *Worker Agents* (execution). 8-stage config loader + 6-stage module loader. See [docs/MT_ARCHITECTURE.md](docs/MT_ARCHITECTURE.md). |
| **550+ AI Employees / 47 Agents** | Teacher AI, Student AI, Exam Expert, Homework Grader, Question Generator, Security Auditor, Git Manager, DevOps Agent, Layout Adjuster, Code Repair, Data Analyst, Brain Librarian, Translator… — self-healing, skill-evolvable. |
| **15+ LLM Models Unified** | GPT-4o / Claude-3.5 / Qwen2.5 / Llama-3 / Gemini / DeepSeek / Volcengine DashScope / Tongyi Qianwen — auto-routed by capability, load & latency SLA. |
| **Dynamic Question Engine v2** | Real-time AI-generated + web-sourced multi-modal questions, avoids collision across attempts; no static q-bank lock-in. 7 question types × 11 subjects × 3 Bloom levels. |
| **Sharded DB Fabric** | 9+ split SQLite shards (`auth / exam / question / learning / user / system / admin / log / ai / question / other / math / physics …`) with 87 tables (0 empty) and transparent smart routing — out-of-box zero-config. |
| **Enterprise RBAC + ABAC** | 16 role levels guest→parent→designer→teacher→proctor→qm→ai_mgr→cluster_mgr→admin→super_admin + hardware-admin; 50+ permission rules + full immutable audit log, VIKEY hardware token support. |
| **AI Firewall + AppSec** | WAF rules (SQLi/XSS/RCE/SSRF/LFI/traversal/scanner/brute), pip-audit, Trivy FS scan, Bandit code sweep, Dependabot pip+actions weekly, CodeQL. |
| **Self-Maintenance OS** | 8 auto-repair paths (schema fix / config correction / cache purge / connection-pool rebuild / rollback / data recovery / index rebuild / ACL repair); preventive health 8-plex diagnostics. |
| **Version Unified API** | 1 main version + 20 subsystem versions, batch-upgrade, rollback, lock-history; mirrored in DB (`system_versions` / `subsystem_versions`) for audit. |
| **Responsive + Mobile Portal** | Desktop, tablet, mobile layouts; dedicated mobile login & exam pages; VIKEY token-auth + 6-digit challenge for super-admin login. |

---

## MTS Architecture v2.0 (Quick View)

```text
                    ┌─────────────────────────────────────────────┐
                    │  MTS ARCHITECTURE v2.0 — DUAL-ENGINE PIPELINE  │
                    └─────────────────────────────────────────────┘

    ┌────────────┐   ┌────────────────────┐   ┌──────────────────────┐   ┌────────────┐
    │  Request   │→  │   PLAN ENGINE      │→  │  WORKER AGENTS       │→  │  Response  │
    │ Ingress    │   │ (Strategy/Orchestr.)│   │ (550+ AI Employees)  │   │  Egress    │
    └──────┬─────┘   └─────────┬──────────┘   └──────────┬───────────┘   └──────┬─────┘
           │                   │                       │                      │
           ▼                   ▼                       ▼                      ▼
   auth.db / admin.db   ai_collab / decision    exam_engine / q_engine   log.db / audit
   user.db / session    capability router       homework / diagnosis    split_databases/*
```

- **Plan Engine** — intent recognition, decomposition, security ACL, route selection
- **Worker Agents** — one agent = one role; pluggable skill evolution, task delegation, fault recovery
- **Fabric** — sharded SQLite + shared in-memory pub/sub + cache; transparent failover
- **MTS Docs** → [docs/MT_ARCHITECTURE.md](docs/MT_ARCHITECTURE.md) · [docs/ARCHITECTURE_REPORT.md](docs/ARCHITECTURE_REPORT.md) · [docs/PROJECT_STRUCTURE.md](docs/PROJECT_STRUCTURE.md)

---

## Feature Matrix (Everything Included)

### Question & Exam
- **Unified Question Bank** — 11 subjects (Chinese / Math / English / Physics / Chem / Bio / Hist / Geog / Politics / Sci / Japanese), 7 formats (single/multi/judge/fill/short/essay/listening), 3 Bloom levels + difficulty + discrimination auto-validated
- **Dynamic Question Engine** — real-time AI generation + web crawling; collision-avoidance random injection
- **AI Paper Composer** — knowledge-coverage analysis, score distribution calculator, quality score + preview + save
- **Proctoring** — browser-focus / copy-paste / tab-switch monitoring + anti-cheat flags

### Learning & Tutoring
- **Learning Path Engine (IRT + RL)** — IRT scoring + Q-value recommended sequence, Ebbinghaus review spiral, scaffolded teaching
- **Weakness Diagnosis** — ability radar + knowledge-point heatmap + wrong-answer causal tree
- **Smart Wrong Book** — auto-collects wrong answers; spaced repetition; mastery tracking
- **AI Tutor** — per-subject coaching, writing grading (Chinese essay / English writing), step-by-step math solver
- **Student Analytics Dashboard** — distributions / radar / time-trend / wrong-rate quadrant

### Management Portal (10 Personas)
- Teacher Workbench / Exam Center / Question Bank Manager / Student Learning Portal / Parent Console /
- Designer Console / AI Ops / Cluster Ops / Admin Dashboard / **Super Admin UX (hardened)** + VIKEY USB Token auth + 6-digit challenge

### Security & Governance
- RBAC (16 roles) + ABAC attribute filters; 6-level ACL matrix
- Enterprise WAF (SQLi / XSS / RCE / SSRF / LFI / traversal / scanner / brute-force / rate-limit)
- **VIKEY Hardware Token** — super-admin login USB token flow + challenge/response + session-token binding
- **AI Firewall** — in-app firewall service + API
- Immutable audit trail (operation / login / data-change / API call); dashboards + exports
- Dependabot daily for pip + weekly for GitHub Actions; pip-audit / Trivy / Bandit / CodeQL on CI

### Ops & Self-Healing
- **Unified Version Manager** — main version + 20 subsystem versions; batch upgrade / rollback / lock / history
- 8-plex auto repair (schema / config / cache / pool / rollback / recovery / index / ACL)
- Full cluster monitoring (CPU / mem / disk / net / slow-query / indexes)
- Git auto-sync + daily health + backups + hot-swap deploy
- Decoupled startup: `startup_modules/` (core_init, db_config_loader, module_loader)

---

## Getting Started / Quick Start

### Environment Requirements

| Dependency | Min Version | Optional / Required |
| :--- | :---: | :---: |
| Python | **3.9+** (3.10+ recommended for full CVEs patched) | ✔️ Required |
| SQLite | 3.30+ | ✔️ Required |
| pip | 20.0+ | ✔️ Required |
| Git | latest | ✔️ Required |
| Redis | 7.0+ | ⚪ Optional (gracefully degrades to memory cache) |
| OpenAI / DashScope / etc. API key | any | ⚪ Optional (offline mode still runs all non-AI functions) |

### Option 1 — Native Run (Mac / Linux / WSL — recommended for developers)

```bash
# 1. Clone
git clone https://github.com/wuchenghao15/MTSCOS-AI-Project.git
cd MTSCOS-AI-Project

# 2. Virtual env + deps
python3 -m venv venv
source venv/bin/activate        # Win:  venv\Scripts\activate
pip install -r requirements.txt  # pip 20.0+ required

# 3. Launch the PRODUCTION entrypoint (recommended)
python3 server_real_db.py --host 0.0.0.0 --port 8888

# Alternative — Preview entrypoint
# python3 server_preview.py --port 8888
```

Now open:
- **Homepage / Login** → <http://localhost:8888/>
- **MTS Architecture v2.0 Showcase** → <http://localhost:8888/mt_architecture>
- **System Spec page** → <http://localhost:8888/system_spec>
- **Super-Admin UX** → login with `wuchenghao15` *(the SA UX auto-hides "remember me / forgot password / create account" and requires VIKEY hardware token + 6-digit challenge for production login)*

**CLI flags:**

```text
--host      Bind address      (default 127.0.0.1)
--port      HTTP port         (default 8888)
--ssl       Enable HTTPS      (default False)
--ssl-port  HTTPS port        (default 8443)
--debug     Debug mode        (default False)
```

### Option 2 — Docker (production)

```bash
git clone https://github.com/wuchenghao15/MTSCOS-AI-Project.git && cd $_
docker build -t mtscos-ai:v17.22.0 .
docker run -d -p 8888:8888 --name mtscos-ai \
  -v $(pwd)/split_databases:/app/split_databases:rw \
  -v $(pwd)/data:/app/data:rw \
  mtscos-ai:v17.22.0
```

Full container & k8s guidance → [docs/DEPLOYMENT_GUIDE.md](docs/DEPLOYMENT_GUIDE.md).

### Option 3 — `app.py` (Legacy entrypoint)

Still supported but **`server_real_db.py` is now the default production entrypoint**
(sharded-db-aware, starts version manager + VIKEY driver + startup modules correctly).

---

## Demo Credentials

10 demo personas ship out-of-the-box — **shared password** `Test@2026`

| Username | Role | Level |
|---|---|---|
| `test_student` | Student | 1 |
| `test_parent` | Parent | 1 |
| `test_designer` | Designer | 1 |
| `test_teacher` | Teacher | 2 |
| `test_proctor` | Proctor | 2 |
| `test_qm` | Question Mgr | 3 |
| `test_aim` | AI Mgr | 3 |
| `test_cm` | Cluster Mgr | 3 |
| `test_admin` | Admin | 4 |
| `test_hwadmin` | Hardware Admin | 5 |
| `wuchenghao15` | **SUPER ADMIN** | 9 — requires VIKEY hardware token |

---

## REST API Highlights (all Blueprint-registered)

Authentication is **Session Cookie + CSRF Token**; production deployments MUST front with TLS.
Interactive Swagger-style OpenAPI lives at `/api/versions` when logged in as admin.

| Group | Endpoint | Method | Purpose |
|---|---|:---:|---|
| **Auth** | `/api/auth/login` | POST | Login |
| | `/api/auth/logout` | POST | Logout (clears vikey token too) |
| | `/api/auth/check` | GET | Session alive check |
| **AI Question** | `/api/ai/generate-questions` | POST | Gen questions from text |
| | `/api/ai/generate-questions/stats` | GET | Generation stats |
| **AI Learning Path** | `/api/ai/study-path/generate` | POST | Personalized learning path |
| | `/api/ai/study-path/knowledge-graph` | GET | Knowledge graph |
| **AI Paper Compose** | `/api/ai/exam-compose` | POST | Auto compose paper |
| | `/api/ai/exam-compose/statistics` | GET | Compose coverage stats |
| **Unified Version API** | `/api/version/list` | GET | Main + subsystem versions |
| | `/api/version/upgrade` | POST | Batch-upgrade subsystems |
| | `/api/version/rollback` | POST | Rollback subsystem |
| **System** | `/api/system/status` | GET | Health, 8-plex diagnostics |
| | `/api/system/version` | GET | Server version info |

More → [docs/SYSTEM_DOC.md §7 — APIs](docs/SYSTEM_DOC.md)

---

## Database Fabric (Sharded SQLite by Domain)

```text
split_databases/
├── auth.db          users / roles / permissions / sessions / 2fa / vikey bindings
├── user.db          user-profiles / parent-student links / groups / avatar
├── system.db        config / system_versions / subsystem_versions / feature-flags
├── admin.db         admin_ops / change-audit / super-admin audit log
├── exam.db          exams / exam_users / exam_questions / results / proctor events
├── question.db      question_bank / ai_generated / tags / blooms / difficulty
├── learning.db      learning_records / knowledge_points / study_paths / wrong-book
├── ai.db            ai_employees / clusters / llm model-pool / ai_results / brain_map
├── log.db           system_logs / access / audit / error / slow_query
├── math.db / physics.db / other.db   subject-domain extensions (reserve)
└── proctor.db / learning.db ext.     proctoring events / learning analytics
```

Smart DB router → see [`smart_db_router_simple.py`](smart_db_router_simple.py)

---

## Project Layout

```text
MTSCOS-AI-Project/
├── server_real_db.py         ✅ Production entrypoint (MT-arch-aware, starts shards)
├── server_preview.py         🧪 Preview entrypoint
├── app.py                    Legacy entrypoint
├── smart_db_router_simple.py SQLite shard router
├── requirements.txt          Runtime deps
├── VERSION                   17.22.0
├── Dockerfile                Container build
├── .github/
│   ├── workflows/ci-cd.yml   CI: bandit/pip-audit/trivy + CodeQL
│   ├── dependabot.yml        pip + actions weekly (with protobuf/paho whitelist)
│   ├── ISSUE_TEMPLATE/       Bug / question templates
│   └── PULL_REQUEST_TEMPLATE.md
├── core/services/
│   ├── version_manager.py    Main + history / next-major-minor-patch helpers
│   ├── ai_firewall.py        AppSec firewall service
│   └── vikey_driver.py       VIKEY hardware-token USB driver
├── startup_modules/          core_init / db_config_loader / module_loader
├── ai_engines/               550+ AI employees / 47 agents / mechanism_ai / layout-adjuster …
├── app/
│   ├── ai/                   Per-domain AI engines (exam/learning/diagnosis…)
│   ├── middlewares/          access_control / security_middleware / CSRF…
│   └── api/                  ai_firewall / ai_security_workforce / layout_ai / vikey / version
├── templates/                100+ Jinja2 pages (index.html, mt_architecture.html, system_spec.html…)
├── static/                   images/logo.svg + favicon / css / js/vikey/
├── split_databases/          ☝️ 9+ domain SQLite shards (87 tables, mount for persistence)
├── docs/                     Full doc set → see "Documentation Index" below
└── data/                     backups / exports / uploads
```

Extended tree → [docs/PROJECT_STRUCTURE.md](docs/PROJECT_STRUCTURE.md)

---

## Roadmap

| Milestone | Target | Status |
|---|:---:|:---:|
| **v17.22.x — SuperAdmin UX Unified Edition** | 2026-07-26 | ✅ **Released** — this version. SA UI auto-hide for remember-me/forgot/register; VIKEY integrated; main+20 subsystems version aligned; Dependabot+Trivy+Bandit on CI. |
| **v17.23 — Question Expansion v3** | Aug 2026 | 🚧 In design — multimodal (image/audio) questions; anti-LLM watermark; OCR-in for handwritten grading. |
| **v17.24 — Role-Twin AI School District** | Sep 2026 | 🚧 In design — every teacher/student has a private AI twin; twin-to-twin delegation graph; GPU offload for local-LLM. |
| **v18.0 — MTS Architecture v3** | Q4 2026 | 🔭 Planned — streaming event bus (Kafka-compatible pub/sub); hot-reload agents; multi-region sharding; Rust firewall proxy. |

Live changelog → [docs/CHANGELOG.md](docs/CHANGELOG.md)

---

## Contributing

We welcome every contribution:
- ⭐ **Star this repo** ⭐ — helps newcomers find us
- [Open a bug report](https://github.com/wuchenghao15/MTSCOS-AI-Project/issues/new?template=bug_report.md)
- [Open a feature/discussion](https://github.com/wuchenghao15/MTSCOS-AI-Project/discussions)
- Translate docs / refine English
- Add subjects, question types, new AI employees

### Quick Dev Loop

```bash
# Fork & clone
gh repo fork wuchenghao15/MTSCOS-AI-Project --clone && cd MTSCOS-AI-Project
# Branch
git checkout -b feature/my-contribution
# Dev server
python3 server_preview.py --port 8888 --debug
# Before PR
python3 -m pytest tests/ -x  # if any
```

Commit format (Conventional Commits 1.0):

```text
feat(question): add image-based comprehension questions
fix(security): patch SSRF in URL fetcher
docs(readme): fix quickstart flags
```

Full contributing rules → [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md) ·
Code of conduct → [docs/CODE_OF_CONDUCT.md](docs/CODE_OF_CONDUCT.md) ·
Security disclosures → [docs/SECURITY.md](docs/SECURITY.md)

---

## Documentation Index

| Document | Purpose |
|---|---|
| 🇨🇳 [中文 README](README.zh-CN.md) | 面向中文用户的完整文档 |
| 🏛️ [MTS Architecture v2.0](docs/MT_ARCHITECTURE.md) | 550+ AI employees / 47 agents dual-engine pipeline explained |
| 📋 [System Spec (§1–§9 hard rules)](docs/SYSTEM_DOC.md) | 系统完整说明书（中文） |
| 🚀 [Deployment Guide](docs/DEPLOYMENT_GUIDE.md) | Prod / docker / k8s / TLS / HA |
| 🚧 [Security](docs/SECURITY.md) | Vulnerability reporting / WAF / CI scanners |
| ➕ [Contributing](docs/CONTRIBUTING.md) | Code style / commit format / PR flow |
| 📦 [Project Structure](docs/PROJECT_STRUCTURE.md) | Full directory tree, what-goes-where |
| 🗺️ [Changelog](docs/CHANGELOG.md) | Every version since v1.0 |
| 🧠 [AI Engine Architecture](ai_engines/AI_ENGINE_ARCHITECTURE.md) | 550+ AI employees matrix |
| 🏷️ [Releases](https://github.com/wuchenghao15/MTSCOS-AI-Project/releases) | Tagged releases on GitHub |

---

## License

MIT License © 2026 wuchenghao15 / MTSCOS AI — see [`LICENSE`](LICENSE) for full text.

- All **question-bank content** generated by the platform must be used responsibly (academic integrity).
- **Educational users (non-commercial):** free, no attribution beyond the MIT notice.
- **Commercial / institutional customers:** please open a GitHub discussion first or email `contact@mtscos.com`.

---

<div align="center">

### If this project saves you time → please ⭐ star it!

[![Stargazers over time](https://starchart.cc/wuchenghao15/MTSCOS-AI-Project.svg?variant=adaptive)](https://starchart.cc/wuchenghao15/MTSCOS-AI-Project)

<sub>

Made with :octocat: + 🤖 multi-agents in Beijing · **MTSCOS AI · MTS Architecture v2.0** ·
[Home](https://github.com/wuchenghao15/MTSCOS-AI-Project) ·
[Discussions](https://github.com/wuchenghao15/MTSCOS-AI-Project/discussions) ·
[Issues](https://github.com/wuchenghao15/MTSCOS-AI-Project/issues) ·
[Contact](mailto:contact@mtscos.com)

</sub>
</div>
