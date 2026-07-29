# MTSCOS AI Intelligent Exam System - System Manual

> Version: v17.22.0 (SuperAdmin UX Unified Edition)
> Updated: 2026-07-26
> Document Version: 17.0

[中文版本 / Chinese Version](SYSTEM_DOC.md)

## Table of Contents

1. [System Overview](#1-system-overview)
2. [Design Philosophy](#2-design-philosophy)
3. [System Architecture](#3-system-architecture)
4. [Modular Startup System](#4-modular-startup-system)
5. [Distributed Database](#5-distributed-database)
6. [AI Engine Matrix](#6-ai-engine-matrix)
7. [Question Bank System](#7-question-bank-system)
8. [Permission Management](#8-permission-management)
9. [AI Cluster & Model Library](#9-ai-cluster--model-library)
10. [Security Architecture](#10-security-architecture)
11. [Self-Maintaining OS](#11-self-maintaining-os)
12. [Port Management](#12-port-management)
13. [Cluster Management](#13-cluster-management)
14. [Git Auto-Sync](#14-git-auto-sync)
15. [Frontend System](#15-frontend-system)
16. [Mobile Adaptation](#16-mobile-adaptation)
17. [AI Question Generator](#17-ai-question-generator)
18. [AI Learning Path Recommendation](#18-ai-learning-path-recommendation)
19. [AI Auto Exam Composer](#19-ai-auto-exam-composer)
20. [Student Analytics Dashboard](#20-student-analytics-dashboard)
21. [Project Mind Map](#21-project-mind-map)
22. [Version History](#22-version-history)
23. [API Documentation](#23-api-documentation)
24. [Deployment Guide](#24-deployment-guide)

---

## 1. System Overview

MTSCOS AI is a distributed intelligent exam management platform based on the Flask framework. Version v17.22.0, codenamed "SuperAdmin UX Unified Edition", adds super admin recognition with hidden remember me/forgot password/create account, full VIKEY integration, unified main version + 20 sub-systems, CI integration with Dependabot+Trivy+Bandit.

### Core Features
- **MTS Architecture v2.0 Dual-Engine**: Planning Engine (strategy) + Execution AI Employee Array (550+ AI employees/engines, 47 Agents), 8-stage config loading + 6-stage module loading
- **Distributed Database Architecture**: 9+ independent SQLite shards (auth/exam/question/learning/user/system/admin/log/ai), 87 tables (0 empty), transparent routing, zero-config bootstrap
- **AI Engine Matrix**: 550+ professional AI employees/engines and 47 Agents, evolvable skills, self-healing failure recovery
- **Complete Question Bank**: 11 subjects × 7 question types × 3 Bloom levels, real-time AI generation + web crawling
- **Enterprise Permission Management**: RBAC 16-level roles + ABAC attribute filtering, 50+ permission rules, full-chain immutable audit
- **AI Firewall + Application Security**: WAF 10 rules (SQLi/XSS/RCE/SSRF/LFI/traversal/scanning/brute-force/rate-limit) + pip-audit/Trivy/Bandit/CodeQL
- **Self-Maintaining OS**: 8-dimensional auto-repair (schema/config/cache/connection pool/rollback/data recovery/index/ACL) + 8-dimensional preventive health diagnosis
- **Unified Version API**: 1 main version + 20 sub-system versions, batch upgrade/rollback/version lock/change history
- **Responsive + Mobile Portal**: Desktop/tablet/mobile layout, mobile-specific login and exam pages, VIKEY USB hardware key login

### System Advantage Matrix

| Dimension | Core Capability | Differentiation |
|-----------|----------------|-----------------|
| **Architecture** | MTS dual-engine layered collaboration | Separation of planning and execution, evolvable strategy, extensible execution |
| **AI Capability** | 550+ professional AI employees/engines, 47 Agents autonomous collaboration | Not a single AI tool, but a complete AI team |
| **Security** | VIKEY hardware key + AI firewall + multi-layer protection | Enterprise security, super admin hardware hardening |
| **Ops Efficiency** | 8-dimensional auto-repair + preventive diagnosis | Self-maintaining system, reduce manual intervention |
| **Learning Effect** | IRT+RL adaptive learning paths | Scientific learning recommendation, Ebbinghaus spiral review |
| **Deployment** | Zero-config bootstrap + Docker support | Minute-level deployment, no complex configuration |
| **Extensibility** | Modular architecture + hot-plug | On-demand extension without impacting core |
| **Data Management** | Sharded database + intelligent routing | Data isolation, performance optimization, fault isolation |

---

## 2. Design Philosophy

### 2.1 "AI School District" Vision

MTSCOS AI originated from a simple yet bold question: **What if we don't just automate a single task, but automate the entire education ecosystem?**

Instead of building isolated AI tools, we envision an **autonomous AI school district** — every role (teacher, counselor, grader, invigilator, security officer, IT administrator...) is filled by professional AI employees who collaborate seamlessly, just like a real team.

### 2.2 Core Design Principles

| Principle | Description | Implementation |
|-----------|-------------|---------------|
| **AI-First** | All core business logic driven by AI engines | AI employee array, smart question generation, adaptive learning |
| **Modular Architecture** | Each module independently encapsulated, modules communicate via API and event bus | ai_engines/, app/api/, blueprint modules |
| **Distributed Thinking** | Databases divided by business domain, AI engines support cluster deployment | split_databases/, cluster management |
| **Self-Healing** | System automatically detects and recovers from failures | Auto-repair OS, health diagnosis |
| **Human-Centered** | AI augments human capabilities, not replaces them | Teacher AI assistant, learning path guidance |
| **Continuous Evolution** | System learns and improves from usage data | Self-learning engine, knowledge graph evolution |

---

## 3. System Architecture

### 3.1 Layered Architecture

```text
┌─────────────────────────────────────────────────┐
│              Presentation Layer                │
│  Web Frontend │ Mobile H5 │ Admin UI │ API GW  │
├─────────────────────────────────────────────────┤
│              MTS Dual-Engine Core              │
│  ┌────────────────┐  ┌────────────────┐       │
│  │  Planning Engine│  │Diagnostic Engine│       │
│  └────────────────┘  └────────────────┘       │
├─────────────────────────────────────────────────┤
│              Business Layer                    │
│  User │ Exam │ Question │ Learning │ AI │ ...  │
├─────────────────────────────────────────────────┤
│              AI Engine Matrix                  │
│  Learning │ Question │ Teaching │ Mgmt │ ...  │
├─────────────────────────────────────────────────┤
│              Data Layer                        │
│  SQLite Shards │ Redis │ MySQL (optional)     │
├─────────────────────────────────────────────────┤
│              Infrastructure Layer              │
│  Servers │ Docker │ Monitoring │ CI/CD        │
└─────────────────────────────────────────────────┘
```

### 3.2 Technology Stack

| Layer | Technology | Version |
|-------|-----------|---------|
| Frontend | HTML5 + CSS3 + JavaScript | ES6+ |
| Backend | Python + Flask | 3.9+ / 3.x |
| Database | SQLite (9+ shards, 87 tables) | 3.30+ |
| Cache | Redis | 7.0+ |
| AI | Ollama / OpenAI / Tongyi Qianwen | - |
| Vector Store | ChromaDB / FAISS | - |
| Auth | PyJWT + bcrypt | - |
| Deploy | Docker + Nginx | - |

---

## 4. Modular Startup System

### 4.1 Eight-Stage Configuration Loading

```text
Stage 1: Environment detection and initialization
Stage 2: Core configuration loading
Stage 3: Database connection establishment
Stage 4: AI engine initialization
Stage 5: Permission system loading
Stage 6: Module registration
Stage 7: Background task scheduling
Stage 8: Health check and ready signal
```

### 4.2 Six-Stage Module Loading

```text
Phase 1: Core services (auth, user, permission)
Phase 2: Business modules (exam, question, learning)
Phase 3: AI engines (learning, question, teaching, management)
Phase 4: Security modules (firewall, audit, monitoring)
Phase 5: Ops modules (backup, sync, maintenance)
Phase 6: Self-learning module
```

---

## 5. Distributed Database

### 5.1 Shard Architecture

| Shard | Tables | Purpose |
|-------|--------|---------|
| auth | users, roles, permissions | Authentication and authorization |
| exam | exams, exam_questions, submissions | Exam management |
| question | questions, knowledge_points, tags | Question bank |
| learning | learning_paths, progress, analytics | Learning analytics |
| user | profiles, preferences, history | User management |
| system | config, versions, hooks | System configuration |
| admin | audit_logs, operation_logs | Admin operations |
| log | system_logs, error_logs | Logging |
| ai | ai_employees, knowledge_graph | AI engine storage |

### 5.2 Routing

- Transparent routing based on domain
- Zero-config bootstrap
- Connection pool management
- Read/write splitting support

---

## 6. AI Engine Matrix

### 6.1 Engine Categories

| Category | Core Engines | Responsibility |
|----------|-------------|---------------|
| **Learning** | Adaptive learning, diagnosis, path planning, error analysis | Personalized learning |
| **Question** | Question generation, composition, difficulty, answer | Question bank construction |
| **Teaching** | Q&A, essay grading, teaching design | AI teaching assistance |
| **Management** | Behavior analysis, monitoring, scheduling | Educational administration |
| **Security** | Anomaly detection, content review, risk warning | System security |
| **Operations** | Monitoring, auto-repair, scheduling, diagnosis | Autonomous operations |
| **Self-Learning** | Knowledge acquisition, rule generation, strategy update | System self-evolution |

### 6.2 AI Employee Matrix

550+ AI employees / engines with 47 agents covering:
- Question authoring, exam composition, grading, diagnosis
- Learning planning, security auditing, Git ops, DevOps
- Layout repair, code fixing, and more

---

## 7. Question Bank System

### 7.1 Coverage

- **11 Subjects**: Chinese, Math, English, Physics, Chemistry, Biology, History, Geography, Politics, Science, Japanese
- **7 Question Types**: Single choice, multiple choice, judge, fill-in-blank, short answer, essay, listening
- **3 Bloom Levels**: Remember/Comprehension, Application/Analysis, Evaluation/Creation
- **37,000+ Questions**: Continuously growing through AI generation

### 7.2 AI Question Generation

- Subject-aware question generation
- Difficulty calibration
- Knowledge point mapping
- Answer auto-generation with explanation
- Quality validation pipeline

---

## 8. Permission Management

### 8.1 RBAC + ABAC Dual Model

- **16-Level Roles**: From super admin to student
- **50+ Permission Rules**: Granular access control
- **Attribute-Based Access Control**: Context-aware permissions
- **Full-Chain Immutable Audit**: All permission changes logged

### 8.2 VIKEY Hardware Key

- Super admin login requires VIKEY USB hardware key
- Forced session logout on key removal
- Hardware-based login verification
- Multi-factor authentication

---

## 9. AI Cluster & Model Library

### 9.1 AI Clustering

- Distributed AI engine deployment
- Load balancing across AI workers
- Auto-scaling based on demand
- Fallover and recovery

### 9.2 Model Library

- Multiple LLM providers supported
- Model version management
- A/B testing for model selection
- Performance tracking

---

## 10. Security Architecture

### 10.1 WAF Protection

10 WAF rules protecting against:
- SQL Injection (SQLi)
- Cross-Site Scripting (XSS)
- Remote Code Execution (RCE)
- Server-Side Request Forgery (SSRF)
- Local File Inclusion (LFI)
- Directory Traversal
- Port Scanning
- Brute Force
- Rate Limiting
- Input Validation

### 10.2 CI/CD Security

- pip-audit for Python dependency scanning
- Trivy for container vulnerability scanning
- Bandit for Python code security analysis
- CodeQL for semantic code analysis
- Dependabot daily dependency updates

---

## 11. Self-Maintaining OS

### 11.1 Eight-Dimensional Auto-Repair

1. Table structure repair
2. Configuration auto-correction
3. Cache invalidation
4. Connection pool recovery
5. Transaction rollback
6. Data recovery
7. Index rebuild
8. ACL repair

### 11.2 Eight-Dimensional Preventive Diagnosis

1. Database health check
2. Performance baseline monitoring
3. Security vulnerability scanning
4. AI engine health check
5. User behavior analysis
6. Resource usage forecasting
7. Compliance verification
8. Capacity planning

---

## 12. Port Management

- Dynamic port allocation
- Port conflict detection
- Service registration and discovery
- Health check endpoints
- Load balancing configuration

---

## 13. Cluster Management

- Node registration and discovery
- Cluster health monitoring
- Auto-scaling based on load
- Failover and recovery
- Distributed state management

---

## 14. Git Auto-Sync

- Automatic code synchronization
- Branch management automation
- Conflict detection and resolution
- Change tracking
- Deployment pipeline integration

---

## 15. Frontend System

### 15.1 Page System

- Landing page with hero section
- Login with VIKEY hardware key support
- Dashboard with learning analytics
- Exam interface with anti-cheat
- Admin panel with full management
- Chinese/English bilingual interface

### 15.2 UI Features

- Glassmorphism design system
- Dark/light theme switching
- Responsive layout (mobile/tablet/desktop)
- Accessibility (WAI-ARIA compliant)
- Bilingual (Chinese/English) support

---

## 16. Mobile Adaptation

- Mobile-optimized login page
- Mobile exam interface
- Touch-friendly interactions
- Offline support
- Push notification integration

---

## 17. AI Question Generator

### 17.1 Generation Pipeline

1. Subject and knowledge point selection
2. Difficulty level specification
3. Question type selection
4. AI generation with template constraints
5. Quality validation
6. Answer and explanation generation
7. Storage and indexing

### 17.2 Quality Assurance

- Automated quality scoring
- Human review workflow
- Difficulty calibration against curriculum
- Knowledge graph alignment

---

## 18. AI Learning Path Recommendation

### 18.1 Adaptive Algorithm

- Item Response Theory (IRT) for knowledge state estimation
- Reinforcement Learning (RL) for path optimization
- Ebbinghaus forgetting curve for review scheduling
- Multi-objective optimization for balance

### 18.2 Personalization Dimensions

- Learning style
- Knowledge level
- Time availability
- Goal orientation
- Historical performance

---

## 19. AI Auto Exam Composer

### 19.1 Composition Strategies

- Fixed ratio (staged proportion)
- Random (random shuffle)
- Weighted (knowledge point weighted)
- Adaptive (based on student profile)
- Exam template based

### 19.2 Quality Assurance

- Knowledge point coverage verification
- Difficulty distribution check
- Question duplication detection
- Time estimation accuracy

---

## 20. Student Analytics Dashboard

### 20.1 Analytics Dimensions

- Score trends
- Knowledge mastery
- Error pattern analysis
- Learning speed tracking
- Comparison with peers

### 20.2 Visualization

- Interactive charts
- Heat maps for knowledge points
- Progress indicators
- Recommendation cards

---

## 21. Project Mind Map

```text
MTSCOS AI
├── MTS Architecture v2.0
│   ├── Planning Engine
│   ├── Diagnostic Engine
│   └── AI Employee Array (550+)
├── Education System
│   ├── K12 (Primary/Secondary)
│   ├── Adult Education
│   └── Higher Education
├── Technical Stack
│   ├── Python + Flask
│   ├── SQLite + Redis
│   └── Docker + Nginx
└── Security
    ├── VIKEY Hardware Key
    ├── AI Firewall
    └── CI Security Scanning
```

---

## 22. Version History

| Version | Key Changes | Date |
|---------|------------|------|
| v17.22.0 | SuperAdmin UX Unified Edition | 2026-07-26 |
| v17.21.0 | AI Self-Learning System | 2026-07-21 |
| v17.20.0 | Rules System Refactoring | 2026-07-15 |
| v17.19.0 | Hook Lifecycle System | 2026-07-10 |

---

## 23. API Documentation

### 23.1 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/auth/login` | POST | User login |
| `/auth/logout` | POST | User logout |
| `/api/exams` | GET/POST | List/create exams |
| `/api/exams/{id}` | GET/PUT/DELETE | Exam operations |
| `/api/questions` | GET/POST | List/create questions |
| `/api/learning/path` | GET | Get learning path |
| `/api/ai/employees` | GET | List AI employees |
| `/admin/users` | GET | Admin: user management |

### 23.2 Response Format

```json
{
    "success": true,
    "message": "Operation successful",
    "data": { ... },
    "errors": null
}
```

---

## 24. Deployment Guide

### 24.1 Quick Start

```bash
# Clone the repository
git clone https://github.com/wuchenghao15/MTSCOS-AI-Project.git
cd MTSCOS-AI-Project

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r flask-app/requirements.txt

# Start development server
python3 server_preview.py --port 8888 --debug
```

### 24.2 Docker Deployment

```bash
# Build and run with Docker
docker-compose up -d

# Or build manually
docker build -t mtscos-ai .
docker run -p 8888:8888 -v ./data:/data mtscos-ai
```

### 24.3 Production Considerations

- Use Nginx as reverse proxy
- Enable HTTPS with Let's Encrypt
- Set up Redis for caching
- Configure regular backups
- Enable monitoring with Prometheus + Grafana

---

## Appendix: Key File Paths

| Path | Description |
|------|-------------|
| `server_real_db.py` | Main server entry point |
| `core/services/lunar_calendar_service.py` | Lunar calendar service |
| `core/services/ai_employee_matrix.py` | AI employee matrix |
| `templates/index.html` | Main frontend template |
| `flask-app/requirements.txt` | Python dependencies |
| `split_databases/` | Database shards |
| `ai_engines/` | AI engine implementations |

---

> © 2026 MTSCOS AI · System Manual v17.0 · Based on MTS Architecture v2.0