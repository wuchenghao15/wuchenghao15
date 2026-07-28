# MTSCOS AI Intelligent Exam System

[![Python Version](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/downloads/)
[![Flask Version](https://img.shields.io/badge/flask-3.x-green.svg)](https://flask.palletsprojects.com/)
[![License](https://img.shields.io/badge/license-MIT-yellow.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-v17.22.0-orange.svg)](CHANGELOG.md)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)
[![Documentation](https://img.shields.io/badge/docs-complete-green.svg)](SYSTEM_DOC.md)
[![Build Status](https://img.shields.io/badge/build-passing-brightgreen.svg)](https://github.com/wuchenghao15/MTSCOS-AI-Project/actions)
[![Code Quality](https://img.shields.io/badge/code-quality-high-blue.svg)](SECURITY.md)
[![Community](https://img.shields.io/badge/community-active-blue.svg)](https://github.com/wuchenghao15/MTSCOS-AI-Project/discussions)

> Version: v17.22.0 (SuperAdmin UX Unified Edition)
> Update Date: 2026-07-26

[中文](README.md) | English

MTSCOS AI is a distributed intelligent exam management platform based on the Flask framework, providing a complete question bank system, exam management, learning analytics, an AI engine matrix, and other capabilities. It supports adult education and K12 subjects and is orchestrated by the MTS Architecture v2.0 (Multi-Agent Twin-Track Self-evolving Collaborative Architecture).

---

## Table of Contents

- [Core Features](#core-features)
- [Project Structure](#project-structure)
- [Quick Start](#quick-start)
  - [Native Deployment](#native-deployment)
  - [Docker Deployment](#docker-deployment)
  - [Quick Docker Deployment](#quick-docker-deployment)
- [API Interfaces](#api-interfaces)
- [Database Architecture](#database-architecture)
- [Admin Pages](#admin-pages)
- [Workflow](#workflow)
- [Test Accounts](#test-accounts)
- [Contributing](#contributing)
- [License](#license)
- [Contact](#contact)

---

## Core Features

### Architecture Features
- **Modular Startup System**: 8-stage configuration loading + 6-stage functional module loading
- **Sharded Database Fabric**: 9+ independent SQLite shards (87 tables, 0 empty) with intelligent routing
- **AI Engine Matrix**: 550+ AI employees/engines and 47 Agents
- **Responsive Frontend**: Desktop and mobile support, adapted for mobile clients

### Question Bank System
- **37,000+ Questions**: Covering adult education and K12 subjects (Chinese, Math, English, Physics, Chemistry, Biology, History, Geography, Politics, Science, Japanese)
- **7 Question Types**: Single choice, multiple choice, true/false, fill-in-the-blank, short answer, essay, listening
- **Smart Question Generation**: Batch question generation based on knowledge points/difficulty/type
- **AI Question Generator**: Automatic question generation from text content

### Education Management
- **Syllabus Management**: Create syllabi, manage chapters, knowledge points, curriculum standards, version control (K12 and adult education)
- **Question Bank & Syllabus Sync**: Question-knowledge mapping, batch mapping, exam-syllabus sync, smart question/exam generation
- **Learning & Syllabus Tracking**: Student progress tracking, knowledge mastery recording, chapter progress updating, learning recommendation generation, evaluation reports
- **Education API**: RESTful API for syllabus CRUD, question bank sync, learning tracking

### Permission Management
- **16+ Roles**: guest→student→parent→designer→teacher→exam_proctor→question_manager→ai_manager→cluster_manager→admin→hardware_admin
- **Fine-grained Permissions**: 50+ permission rules, 6-level access control
- **Audit Logs**: Complete operation records, real-time auditing
- **Permission Matrix**: Custom permission rule configuration

### AI Cluster & Model Library
- **15+ AI Models**: GPT-4, Claude-3, Qwen, Llama-3, Gemini, DeepSeek, etc.
- **Performance Monitoring**: Latency, throughput, accuracy metrics
- **Dynamic Scaling**: Auto node scaling, load balancing
- **Multi-model Configuration**: Model switching and version management

### AI Intelligent Functions
- **AI Question Generator**: Auto-generate questions from text, 6 types, 11 subjects, 3 difficulty levels, auto-save to question bank
- **AI Study Path Recommendation**: Analyze wrong answers, generate personalized study paths, weakness analysis, knowledge graph
- **AI Exam Composition**: Smart exam composition based on subject/difficulty/type, auto-score distribution, knowledge coverage analysis, quality scoring
- **AI Intelligent Q&A**: Online student Q&A, AI auto-answer, multi-subject, multi-type support, session management, knowledge base search
- **Smart Wrong Answer Book**: Auto-collect wrong answers, Ebbinghaus forgetting curve review, weakness analysis, mastery tracking
- **Student Analytics Dashboard**: Multi-dimensional data visualization, score distribution histogram, subject average radar chart, learning time trend, error rate analysis
- **Smart Learning Assistant**: Personalized learning recommendations, smart homework assistance, learning effect analysis

### Security Protection
- **Enterprise Firewall**: 10+ security rules (SQL injection/XSS/Command injection/SSRF/File inclusion/Path traversal/Sensitive file/Brute force/Scanner protection/API rate limiting)
- **AI Security Suggestions**: Smart vulnerability analysis, optimization recommendations and implementation steps
- **Security Vulnerability Management**: Vulnerability signature database (9 types, 17 detection features, 13 fixes), attack simulation engine (SQL injection/XSS simulation), code security scanner (13 detection rules), AI closed-loop learning (auto-sync to knowledge base)
- **Code Security Scan**: Auto-scan Python/HTML code, detect eval injection, command injection, path traversal, hardcoded secrets, scan results stored in database

### Self-Maintenance
- **Auto-repair Engine**: 8 repair capabilities (table structure repair/config correction/cache cleanup/connection pool rebuild/config rollback/data recovery/index rebuild/permission repair)
- **Preventive Maintenance**: 8 maintenance items, 100% prediction accuracy
- **System Health Diagnosis**: 8 core checks (database/API response/memory/CPU/disk/network/cache/error logs)

### Port & Cluster Management
- **21 Port Configurations**: HTTP/HTTPS, API, WebSocket, database, etc.
- **Port Management**: Scan, allocate, reserve, release, auto-repair
- **Load Balancing**: Round-robin, least connections, weighted round-robin, IP hash
- **Health Check**: Heartbeat detection, auto-failover, node status monitoring

### System Monitoring
- **Real-time Monitoring**: CPU, memory, disk, network
- **Slow Query Detection**: Auto-identify and optimize slow queries
- **Performance Analysis**: Index suggestions, query statistics
- **Performance Monitoring API**: System status and metrics API

### Automated Operations
- **Git Auto-sync**: Change detection, auto-commit, push
- **Daily Health Check**: Database cleanup, log cleanup, backup
- **Auto-upgrade**: Version detection, canary release, health check rollback
- **Version Management**: System version history, auto-update documentation

---

## Project Structure

```text
MTSCOS-AI-Project/
├── server_real_db.py           # Production entrypoint (sharded-db-aware)
├── server_preview.py           # Preview entrypoint
├── app.py                      # Legacy entrypoint
├── version_manager.py          # Version manager
├── scheduler_control.py        # Scheduler control (with watchdog daemon)
├── auto_scheduler.py           # Auto scheduler
├── requirements.txt            # Python dependencies
├── Dockerfile                  # Docker build config
├── docker-compose.yml          # Docker Compose full config
├── docker-compose.quick.yml    # Quick Docker deployment config
├── CHANGELOG.md                # Change log
├── SYSTEM_DOC.md               # System documentation
├── DEPLOYMENT_GUIDE.md         # Deployment guide
├── SECURITY.md                 # Security documentation
├── CONTRIBUTING.md             # Contribution guide
├── CODE_OF_CONDUCT.md          # Code of conduct
├── LICENSE                     # License
├── ai_engines/                 # AI engine modules (550+ employees/engines, 47 agents)
│   ├── ai_cluster_manager.py   # AI cluster management
│   ├── ai_employee_manager.py  # AI employee management
│   ├── ai_question_bank.py     # Question bank generation engine
│   └── ...
├── app/                        # Application modules
│   ├── routes/                 # Route modules (API blueprints)
│   ├── services/               # Service modules
│   ├── models/                 # Data models
│   ├── api/                    # API blueprint modules
│   ├── utils/                  # Utility modules
│   ├── middlewares/            # Middleware
│   └── __init__.py             # Application initialization
├── templates/                  # HTML templates (100+)
├── static/                     # Flask static files
├── data/                       # Data directory
├── logs/                       # Log directory
└── .github/                    # GitHub configuration
    ├── workflows/              # CI/CD workflows
    └── ISSUE_TEMPLATE/         # Issue templates
```

---

## Quick Start

### Environment Requirements
- Python 3.9+
- SQLite 3.30+
- Redis 7.0+ (optional, system supports memory cache fallback)
- Git
- pip 20.0+

---

### Native Deployment (Recommended)

```bash
# Clone repository
git clone https://github.com/wuchenghao15/MTSCOS-AI-Project.git
cd MTSCOS-AI-Project

# Create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start service (production entrypoint recommended)
python3 server_real_db.py --host 0.0.0.0 --port 8888
```

**Startup Parameters**

| Parameter | Description | Default |
|-----------|-------------|---------|
| --port | Service port | 8888 |
| --host | Bind address | 0.0.0.0 |
| --debug | Debug mode | False |
| --ssl | Enable SSL | False |
| --ssl-port | SSL port | 8443 |

---

### Docker Deployment

**Full Deployment (with Redis)**

```bash
# Clone repository
git clone https://github.com/wuchenghao15/MTSCOS-AI-Project.git
cd MTSCOS-AI-Project

# Build and start
docker-compose up -d --build

# View logs
docker-compose logs -f
```

**Quick Deployment (application only)**

```bash
# Quick start (no Redis dependency)
docker-compose -f docker-compose.quick.yml up -d

# View logs
docker-compose -f docker-compose.quick.yml logs -f
```

**Docker Deployment Comparison**

| Feature | docker-compose.yml | docker-compose.quick.yml |
|---------|-------------------|------------------------|
| Redis | ✅ Included | ❌ Not included |
| AI Self-learning | ✅ Enabled | ❌ Disabled |
| Git Auto-sync | ✅ Enabled | ❌ Disabled |
| Auto Backup | ✅ Enabled | ❌ Disabled |
| Deployment Speed | Slower (needs build) | Faster (direct run) |
| Use Case | Production | Development/Testing |

---

### Access URLs
- System Home: http://localhost:8888/
- Login: http://localhost:8888/login
- Admin: http://localhost:8888/admin_app/login
- Enhancement Manager: http://localhost:8888/enhancement
- AI Learning Dashboard: http://localhost:8888/ai_learning_dashboard

---

## API Interfaces

### Authentication
| Interface | Method | Description |
|-----------|--------|-------------|
| /api/auth/login | POST | User login |
| /api/auth/logout | POST | User logout |
| /api/auth/check | GET | Check login status |

### System Management
| Interface | Method | Description |
|-----------|--------|-------------|
| /api/system/status | GET | Get system status |
| /api/system/configs | GET | Get system configs |
| /api/system/modules | GET | Get module status |
| /api/system/version | GET | Get system version |

### AI Question Generation
| Interface | Method | Description |
|-----------|--------|-------------|
| /api/ai/generate-questions | POST | Generate questions from text |
| /api/ai/generate-questions/save | POST | Save generated questions |
| /api/ai/generate-questions/stats | GET | Get generation statistics |
| /api/ai/detect-subject | POST | Auto-detect subject |
| /api/ai/extract-key-points | POST | Extract key points |

### AI Study Path
| Interface | Method | Description |
|-----------|--------|-------------|
| /api/ai/study-path/generate | POST | Generate study path |
| /api/ai/study-path/analyze | POST | Analyze weaknesses |
| /api/ai/study-path/knowledge-graph | GET | Get knowledge graph |
| /api/ai/study-path/progress | POST | Get learning progress |

### AI Learning Assistant
| Interface | Method | Description |
|-----------|--------|-------------|
| /api/learning_assistant/recommendations | GET | Get learning recommendations |
| /api/learning_assistant/generate_recommendations | POST | Generate learning recommendations |
| /api/learning_assistant/homework/analyze | POST | Analyze homework answers |
| /api/learning_assistant/report | GET | Get learning report |

### AI Exam Composition
| Interface | Method | Description |
|-----------|--------|-------------|
| /api/ai/exam-compose | POST | Auto compose exam |
| /api/ai/exam-compose/preview | POST | Preview exam |
| /api/ai/exam-compose/save | POST | Save exam |
| /api/ai/exam-compose/statistics | GET | Get composition statistics |

### Enhancement Manager
| Interface | Method | Description |
|-----------|--------|-------------|
| /api/enhancement/status | GET | Enhancement manager overview |
| /api/enhancement/database/health | GET | Database health check |
| /api/enhancement/cluster/monitor | GET | Cluster status monitoring |
| /api/enhancement/system/resources | GET | System resource multi-dimensional monitoring |
| /api/enhancement/git/sync | POST | Git one-click sync |

---

## Database Architecture

### Main Databases
| Database | Purpose | Core Tables |
|----------|---------|-------------|
| auth.db | Authentication & user management | users, roles, permissions, sessions |
| exam.db | Exam management | exams, exam_questions, exam_results |
| question.db | Question bank management | questions, ai_generated_questions |
| learning.db | Learning system | learning_records, study_paths, knowledge_points |
| system.db | System configuration | configs, versions, logs |
| ai.db | AI engine data | ai_models, ai_clusters, ai_results |
| admin.db | Admin backend | admin_users, admin_logs |
| log.db | Log system | system_logs, audit_logs, error_logs |
| api_management.db | API management | api_endpoints, api_stats |
| routes_management.db | Route management | routes, route_stats |

---

## Admin Pages

| Route | Description | Permission |
|-------|-------------|------------|
| /admin_app/login | Admin login | All roles |
| /admin/ai-question-generator | AI Question Generator | admin |
| /admin/ai-study-path | AI Study Path | admin |
| /admin/ai-exam-composer | AI Exam Composer | admin |
| /admin/student-analytics | Student Analytics | admin |
| /admin/question-bank | Question Bank | question_manager |
| /admin/ai-cluster | AI Cluster | ai_manager |
| /admin/cluster-management | Cluster Management | cluster_manager |
| /enhancement | Enhancement Dashboard | admin |

---

## Workflow

### AI Question Generation
1. Input text → Auto-detect subject → Extract key points → Generate questions → Save to question bank

### AI Study Path Recommendation
1. Analyze wrong answers → Identify weaknesses → Generate personalized path → Track progress

### AI Exam Composition
1. Set subject/type/difficulty → Smart question selection → Knowledge coverage analysis → Preview → Save

### Student Analytics
1. Select subject/class/time → Load statistics → Visualize → Export report

### Smart Learning Assistant
1. Get recommendations → Complete learning → Submit homework → AI analysis → Generate report

---

## Test Accounts

11 test accounts are pre-configured for developers and testers:

| Username | Role | Permission Level |
|----------|------|------------------|
| `test_student` | Student | 1 |
| `test_parent` | Parent | 1 |
| `test_designer` | Designer | 1 |
| `test_teacher` | Teacher | 2 |
| `test_proctor` | Exam Proctor | 2 |
| `test_qm` | Question Manager | 3 |
| `test_aim` | AI Manager | 3 |
| `test_cm` | Cluster Manager | 3 |
| `test_admin` | System Admin | 4 |
| `test_hwadmin` | Hardware Admin | 5 |
| `wuchenghao15` | Super Admin | 9 (requires VIKEY token) |

**Default Password**: `Test@2026`

---

## Contributing

Welcome to MTSCOS AI Project! We welcome code contributions, documentation improvements, bug reports, and feature suggestions.

### Code Standards

The project follows these standards; all contributions must comply:

- [Design Standards](../.trae/rules/设计规范.md) - Unified UI design standards and visual style
- [Development Rules](../.trae/rules/开发规则.md) - Unified development standards and code conventions

### Branch Management

| Branch | Purpose |
|--------|---------|
| `main` | Main branch, production code |
| `develop` | Development branch, integrates all features |
| `feature/xxx` | Feature branch, developing new features |
| `bugfix/xxx` | Bug fix branch |
| `hotfix/xxx` | Emergency fix branch |

### Commit Message Format

```text
<type>(<scope>): <description>

<detailed description>
```

| Type | Description |
|------|-------------|
| `feat` | New feature |
| `fix` | Bug fix |
| `docs` | Documentation update |
| `style` | Style changes |
| `refactor` | Code refactoring |
| `test` | Test code |
| `chore` | Build/tools update |

### Development Setup

1. **Clone Repository**

```bash
git clone https://github.com/wuchenghao15/MTSCOS-AI-Project.git
cd MTSCOS-AI-Project
```

2. **Install Dependencies**

```bash
pip install -r requirements.txt
```

3. **Start Development Server**

```bash
python3 server_preview.py --port 8888 --debug
```

4. **Run Tests**

```bash
python -m pytest
```

### PR Submission Process

1. **Fork Repository** - Fork to your GitHub account
2. **Create Branch** - Create new branch from `develop`
3. **Develop** - Implement feature or fix bug following code standards
4. **Commit** - Use standard commit message format
5. **Push** - Push to your forked repository
6. **Create PR** - Create Pull Request to `develop` branch
7. **Review** - Wait for project maintainer review
8. **Merge** - PR merged after approval

---

## License

MIT License

---

## Contact

- Project: https://github.com/wuchenghao15/MTSCOS-AI-Project
- System Doc: [SYSTEM_DOC.md](SYSTEM_DOC.md)
- Deployment Guide: [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)
- Changelog: [CHANGELOG.md](CHANGELOG.md)

---

**MTSCOS AI** - Make exams smarter, make learning more efficient

If this project helps you, please give it a Star!
