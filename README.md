# MTSCOS AI Project

> **MTSCOS** = **M**ulti-Agent **T**win-Track **S**elf-evolving **C**ollaborative **O**perating **S**ystem

A distributed multi-agent intelligent education and exam platform driven by the MTS Architecture v2.0. It unifies AI-powered question generation, smart exam composition, weakness diagnosis, personalized learning paths, and enterprise-grade RBAC + ABAC governance, covering K12, adult education, and higher education scenarios.

[![Version](https://img.shields.io/badge/version-v17.22.0-purple)](CHANGELOG.md)
[![Python](https://img.shields.io/badge/python-3.9%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/flask-3.x-000000?logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![License](https://img.shields.io/badge/license-MIT-yellow)](LICENSE)

> The full documentation has been migrated to the [`docs/`](docs/) directory:
> - English: [docs/README.md](docs/README.md) · [docs/README_EN.md](docs/README_EN.md)
> - 中文文档: [README.zh-CN.md](README.zh-CN.md) · [docs/README.zh-CN.md](docs/README.zh-CN.md)

---

## Highlights

| Dimension | Capability |
| :--- | :--- |
| **MTS Architecture v2.0 Dual-Engine** | A Planning Engine for strategy and an Execution Array of AI employees for delivery; 8-phase config loading + 6-phase module loading |
| **550+ AI Employees / Engines** | 47 Agents covering question authoring, exam composition, grading, diagnosis, learning planning, security auditing, Git ops, DevOps, layout repair, and code fixing — skills are evolvable and failures self-heal |
| **87 Database Tables** | 9+ domain-sharded SQLite databases (auth / exam / question / learning / user / system / admin / log / ai) with transparent routing and zero-config bootstrap |
| **Education & Exam System** | 11 subjects × 7 question types × 3 Bloom levels, 37,000+ questions, AI smart composition, anti-cheat proctoring, IRT + RL adaptive learning paths |
| **Lunar Calendar Service** | Built-in lunar calendar service ([`core/services/lunar_calendar_service.py`](core/services/lunar_calendar_service.py)) for schedule-aware education scenarios |
| **Enterprise RBAC + ABAC** | 16-level roles, 50+ permission rules, full-chain immutable audit, VIKEY USB hardware key login for super admins |
| **AI Firewall & App Security** | WAF (SQLi/XSS/RCE/SSRF/LFI/traversal/rate-limit) + pip-audit / Trivy / Bandit / CodeQL in CI, Dependabot daily updates |

---

## Requirements

| Dependency | Minimum | Required |
| :--- | :---: | :---: |
| Python | **3.9+** (3.10+ recommended) | Required |
| SQLite | 3.30+ | Required |
| pip | 20.0+ | Required |
| Git | latest | Required |
| Redis | 7.0+ | Optional (falls back to in-memory cache) |
| LLM API Key | any | Optional (non-AI features run without it) |

---

## Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/wuchenghao15/MTSCOS-AI-Project.git
cd MTSCOS-AI-Project

# 2. Create a virtual environment and install dependencies
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 3. Launch the production entry point
python3 server_real_db.py --host 0.0.0.0 --port 8888
```

Open <http://localhost:8888/> in your browser.

**Command-line options:**

| Option | Description | Default |
| :--- | :--- | :--- |
| `--host` | Bind address | `127.0.0.1` |
| `--port` | HTTP port | `8888` |
| `--ssl` | Enable HTTPS | `False` |
| `--ssl-port` | HTTPS port | `8443` |
| `--debug` | Debug mode | `False` |

### Docker

```bash
docker build -t mtscos-ai:v17.22.0 .
docker run -d -p 8888:8888 --name mtscos-ai \
  -v $(pwd)/split_databases:/app/split_databases:rw \
  -v $(pwd)/data:/app/data:rw \
  mtscos-ai:v17.22.0
```

### Entry Points

- **Production entry**: `server_real_db.py` — boots sharded databases, version manager, VIKEY driver, and decoupled startup modules.
- **Preview entry**: `server_preview.py` — for local debugging.
- **Legacy compatibility entry**: `app.py` — still available for backward compatibility.

---

## Test Accounts

10+ role-based accounts are pre-provisioned. Default password: `Test@2026`.

| Username | Role | Level |
| :--- | :--- | :---: |
| `test_student` | Student | 1 |
| `test_parent` | Parent | 1 |
| `test_designer` | Designer | 1 |
| `test_teacher` | Teacher | 2 |
| `test_proctor` | Proctor | 2 |
| `test_qm` | Question Bank Manager | 3 |
| `test_aim` | AI Manager | 3 |
| `test_cm` | Cluster Manager | 3 |
| `test_admin` | System Administrator | 4 |
| `test_hwadmin` | Hardware Administrator | 5 |
| `wuchenghao15` | **Super Administrator** | 9 · **requires VIKEY hardware key** |

---

## Documentation

| Document | Purpose |
| :--- | :--- |
| [MTS Architecture v2.0 Whitepaper](docs/MT_ARCHITECTURE.md) | Dual-engine pipeline with 47 AI Agents |
| [System Specification](docs/SYSTEM_DOC.md) | System rules, dev constraints, API surface, compliance |
| [Deployment Guide](docs/DEPLOYMENT_GUIDE.md) | Production / Docker / K8s / TLS / HA |
| [Security Policy](SECURITY.md) · [docs/SECURITY.md](docs/SECURITY.md) | Vulnerability reporting, WAF rules, CI scan matrix |
| [Contributing Guide](CONTRIBUTING.md) | Code style, commit format, PR workflow |
| [Project Structure](docs/PROJECT_STRUCTURE.md) | Full directory tree and module ownership |
| [Changelog](CHANGELOG.md) · [docs/CHANGELOG.md](docs/CHANGELOG.md) | Full change history from v1.0 to v17.22.0 |
| [AI Engine Architecture](ai_engines/AI_ENGINE_ARCHITECTURE.md) | 550+ AI employee / engine matrix |

---

## License

MIT License © 2026 wuchenghao15 / MTSCOS AI — see [`LICENSE`](LICENSE) for the full text.

- Auto-generated question bank content must be used in accordance with academic integrity; any cheating or misuse is prohibited.
- **Non-commercial / education scenarios**: free to use; no additional attribution beyond MIT is required.
- **Commercial / institutional users**: please open a thread in GitHub Discussions or email `contact@mtscos.com` first.
