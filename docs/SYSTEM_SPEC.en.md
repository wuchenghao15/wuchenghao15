# MTSCOS AI System Specification

> **Version**: v1.3
> **Updated**: 2026-07-26
> **Architecture**: MTS Architecture v2.0
> **Related Rules**: System Rules v1.2
> **Scope**: MTSCOS AI Intelligent Learning & Assessment Platform - Development, Operations, Testing

[中文版本 / Chinese Version](系统规范.md)

---

## Table of Contents

| Section | Description |
|---------|-------------|
| [1. Technical Architecture](#1-technical-architecture) | Frontend/Backend Tech Stack, Architecture Layers, Module Division |
| [2. Frontend Development](#2-frontend-development) | HTML/CSS/JS, Components, Styling, Responsive |
| [3. Backend Development](#3-backend-development) | Python/Flask, API, Database, Logging |
| [4. AI Engine](#4-ai-engine) | AI Invocation, Model Management, Knowledge Graph |
| [5. Database](#5-database) | Design, SQL, Optimization, Backup |
| [6. Security](#6-security) | Authentication, Authorization, Encryption, Audit |
| [7. Testing](#7-testing) | Unit Tests, Integration Tests, Performance Tests |
| [8. Deployment & Operations](#8-deployment--operations) | Environment, Release, Monitoring, Alerts |
| [9. Code Quality](#9-code-quality) | Review, Metrics, Refactoring |
| [10. Documentation](#10-documentation) | Types, Format, Management |
| [11. UI/UX Design](#11-uiux-design) | Color Scheme, Components, Interaction, Branding |
| [12. Education Business](#12-education-business) | K12/Adult/Higher Education Standards |
| [13. Hook & Heartbeat](#13-hook--heartbeat) | Hook Lifecycle, Heartbeat, Background Processes |
| [14. AI Employee Matrix](#14-ai-employee-matrix) | AI Employee Type Mapping, Trigger Conditions |

---

## 1. Technical Architecture

### 1.1 Overall Architecture

```text
┌─────────────────────────────────────────────────────────────┐
│                   Presentation Layer                        │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐    │
│  │ Web Front│  │ Mobile H5│  │ Admin UI │  │ API Gateway│  │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘    │
├─────────────────────────────────────────────────────────────┤
│                   Business Layer                            │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐    │
│  │User Module│ │Exam Module│ │Question  │ │Learning  │    │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘    │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐    │
│  │AI Engine │  │Education │  │Permission│  │Logging   │    │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘    │
├─────────────────────────────────────────────────────────────┤
│                 AI Engine Matrix                           │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐          │
│  │Learning │ │Question │ │Teaching │ │Management│          │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘          │
│  ┌─────────┐ ┌─────────┐ ┌─────────────────────┐          │
│  │Security │ │Ops      │ │ Self-Learning System │          │
│  └─────────┘ └─────────┘ └─────────────────────┘          │
├─────────────────────────────────────────────────────────────┤
│                   Data Layer                               │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐    │
│  │  MySQL   │  │  Redis   │  │  SQLite  │  │Object Store│   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘    │
├─────────────────────────────────────────────────────────────┤
│              Infrastructure Layer                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐    │
│  │  Servers │  │ Docker   │  │Monitoring│  │ CI/CD    │    │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘    │
└─────────────────────────────────────────────────────────────┘
```

### 1.1.1 MTS Dual-Engine Core (v2.0)

```text
┌─────────────────────────────────────────────────────────────────┐
│              MTS Core (Question Engine + Diagnostic Engine)     │
│  ┌───────────────────────────┐  ┌───────────────────────────┐   │
│  │   Question Engine          │  │   Diagnostic Engine        │   │
│  │ · Smart question generation│  │ · Multi-dimensional analysis│   │
│  │ · Adaptive exam composition│  │ · Error attribution        │   │
│  │ · Difficulty calibration  │  │ · Weakness identification  │   │
│  │ · Question bank maintenance│  │ · Personalized path design │   │
│  └───────────────────────────┘  └───────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### 1.2 Tech Stack

| Layer | Technology | Version | Notes |
|-------|-----------|---------|-------|
| **Frontend** | HTML5 + CSS3 + JavaScript | ES6+ | Native JS, no heavy frameworks |
| **UI Framework** | Font Awesome | 6.4.0+ | Icon library |
| **Backend Lang** | Python | 3.9+ | Development language |
| **Backend Framework** | Flask | 2.0+ | Web framework |
| **Primary DB** | SQLite (distributed 9+ shards, 87 tables) | 3.30+ | Relational DB, transparent routing |
| **Cache** | Redis | 6.0+ | Cache and session storage |
| **AI Interface** | Ollama / OpenAI / Tongyi Qianwen | - | Large model LLM |
| **Vector Store** | ChromaDB / FAISS | - | Knowledge vectorization |
| **ORM** | SQLAlchemy | 1.4+ | Database ORM |
| **Auth** | PyJWT + bcrypt | - | JWT token authentication |
| **Monitoring** | Prometheus + Grafana | - | Metrics visualization |
| **Deployment** | Docker + Nginx | - | Containerization and reverse proxy |

### 1.3 Module Division Principles

1. **High Cohesion, Low Coupling**: Single responsibility, clear interfaces
2. **Independently Testable**: Each module can run and be tested independently
3. **Independently Deployable**: Supports modular release and canary
4. **Replaceable**: Modules can be replaced with better implementations
5. **No Circular Dependencies**: Strictly prohibited between modules

---

## 2. Frontend Development

### 2.1 HTML Standards

| Item | Standard |
|------|----------|
| DOCTYPE | `<!DOCTYPE html>` declaration |
| Encoding | `<meta charset="UTF-8">` unified UTF-8 |
| Viewport | `<meta name="viewport" content="width=device-width, initial-scale=1.0">` |
| ID Naming | Lowercase underscore `user_info_panel` or kebab `user-info-panel` |
| Class Naming | Kebab case `btn-primary` `card-header` |
| Attribute Order | id → class → name → type → src → href → placeholder → required |
| Semantic | Use `<header>` `<nav>` `<main>` `<section>` `<article>` `<footer>` |
| Tag Closing | All tags must be properly closed |
| Comments | Key modules and complex logic must have comments |

### 2.2 CSS Standards

#### 2.2.1 Design Tokens (CSS Variables)

```css
:root {
    /* Primary - MTS Purple */
    --primary-color: #6366f1;
    --primary-light: #8b5cf6;
    --primary-accent: #a855f7;
    --primary-dark: #4f46e5;

    /* Background Colors */
    --bg-gradient-start: #050510;
    --bg-gradient-mid: #0c0c24;
    --bg-gradient-end: #070718;
    --card-bg: rgba(12, 12, 30, 0.7);

    /* Text Colors */
    --text-primary: #f8fafc;
    --text-secondary: #cbd5e1;
    --text-muted: #64748b;
    --text-accent: #a5b4fc;

    /* Glassmorphism */
    --glass-blur: 28px;
    --glass-border: 1px solid rgba(99, 102, 241, 0.18);
    --glass-shadow: 0 8px 40px rgba(0, 0, 0, 0.5);

    /* Border Radius */
    --radius-sm: 8px;
    --radius-md: 12px;
    --radius-lg: 20px;
    --radius-xl: 28px;

    /* Spacing */
    --space-xs: 4px;
    --space-sm: 8px;
    --space-md: 16px;
    --space-lg: 24px;
    --space-xl: 40px;
}
```

#### 2.2.2 CSS Property Order

1. Position: `position` `top` `left` `z-index`
2. Box Model: `display` `width` `height` `margin` `padding` `border`
3. Text: `font-*` `color` `text-align` `line-height`
4. Visual: `background` `opacity` `box-shadow` `transform` `filter`
5. Animation: `transition` `animation` `cursor`

### 2.3 JavaScript Standards

| Item | Standard |
|------|----------|
| Indentation | 4 spaces, no tabs |
| Semicolons | Required at end of statements |
| Strings | Single quotes preferred, template literals with backticks |
| Variables | `const` preferred, `let` for mutable, `var` prohibited |
| Functions | Arrow functions preferred: `const fn = () => {}` |
| Naming | camelCase for variables/functions, UPPER_SNAKE_CASE for constants |
| Blank Lines | Between logic blocks, two lines between functions |
| Comments | JSDoc required for functions: `/** Description */` |

---

## 3. Backend Development

### 3.1 Python Coding Standards

| Item | Standard | Reference |
|------|----------|-----------|
| Indentation | 4 spaces | PEP8 |
| Line Length | Max 120 characters | PEP8 |
| Naming | Functions/variables: `snake_case`; Classes: `PascalCase`; Constants: `UPPER_CASE` | PEP8 |
| Import Order | Stdlib → Third-party → Local | PEP8 |
| Type Hints | Required for function params and returns | PEP484 |
| Docstrings | Required for all public functions/classes | Google style |

### 3.2 Flask Route Standards

```python
# Blueprint module structure
from flask import Blueprint, jsonify, request

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')
api_bp = Blueprint('api', __name__, url_prefix='/api')

@auth_bp.route('/login', methods=['POST'])
def login():
    """User login"""
    data = request.get_json()
    # Business logic...
    return jsonify({'success': True, 'message': 'Login successful', 'data': {...}})
```

### 3.3 Database Operation Standards

```python
# ✅ Recommended: Use ORM + parameterized
from sqlalchemy import text

user = session.query(User).filter(User.id == user_id).first()

# Raw SQL must be parameterized
result = session.execute(
    text("SELECT * FROM users WHERE id = :id"),
    {'id': user_id}
)

# ❌ Prohibited: String concatenation SQL
query = f"SELECT * FROM users WHERE id = {user_id}"  # DANGEROUS!
```

### 3.4 Logging Standards

```python
import logging
logger = logging.getLogger(__name__)

logger.debug('Variable value: %s', var)
logger.info('User login: %s', username)
logger.warning('Retry attempt %s', retry)
logger.error('Database connection failed: %s', e)
logger.critical('System crash: %s', e)

# Structured logging (recommended)
logger.info(
    'Operation completed',
    extra={'user': uid, 'action': 'update', 'duration': duration_ms}
)
```

---

## 4. AI Engine

### 4.1 AI Engine Matrix

| Engine Category | Core Engines | Primary Responsibility |
|----------------|-------------|----------------------|
| **Learning Engine** | Adaptive learning, intelligent diagnosis, path planning, error analysis | Personalized learning |
| **Question Engine** | Question generation, exam composition, difficulty adjustment, answer generation | Question bank construction |
| **Teaching Engine** | Intelligent Q&A, essay grading, teaching design, interactive teaching | AI teaching assistance |
| **Management Engine** | Behavior analysis, learning monitoring, intelligent scheduling, resource recommendation | Educational administration |
| **Security Engine** | Anomaly detection, content review, risk warning, security audit | System security |
| **Ops Engine** | Performance monitoring, auto-repair, intelligent scheduling, fault diagnosis | Autonomous operations |
| **Self-Learning** | Knowledge acquisition, rule generation, strategy update, capability evolution | System self-evolution |

---

## 5. Database

### 5.1 Design Standards

| Item | Standard |
|------|----------|
| Table Names | Lowercase underscore, plural `users` `exam_results` |
| Field Names | Lowercase underscore `created_at` `user_name` |
| Primary Key | `id INTEGER PRIMARY KEY AUTOINCREMENT` (SQLite) / `BIGINT` (MySQL) |
| Timestamp | Must have `created_at` `updated_at` DATETIME |
| Soft Delete | `is_deleted INTEGER DEFAULT 0` (SQLite) / `TINYINT` (MySQL) |
| Indexes | Must index query fields, FK, and sort fields |
| Charset | UTF-8 (SQLite default); utf8mb4 for MySQL |
| Engine | SQLite (default); InnoDB (MySQL optional) |

### 5.2 Optimization Standards

```sql
-- ✅ Use EXPLAIN to analyze queries
EXPLAIN SELECT * FROM users WHERE username = 'test';

-- ✅ Avoid full table scans, use LIMIT for pagination
SELECT * FROM large_table WHERE id > ? ORDER BY id LIMIT 1000;

-- ❌ Prohibited: Full table queries without WHERE
SELECT * FROM huge_table;

-- ❌ Prohibited: SELECT *
SELECT id, name, email FROM users;
```

---

## 6. Security

### 6.1 Authentication & Authorization

| Item | Standard |
|------|----------|
| Password Hashing | bcrypt with cost factor >= 12 |
| JWT Token | HS256 algorithm, 2-hour expiry, refresh token 7 days |
| Token Storage | HttpOnly + Secure + SameSite Cookie |
| Permission Check | Every endpoint must verify RBAC permissions |
| Login Security | 5 failures → 15 min lockout,异地登录告警 |
| Session Management | Force logout supported, single device login (optional) |

### 6.2 Input/Output Security

```python
# ✅ Input validation with schema
from pydantic import BaseModel, constr

class LoginRequest(BaseModel):
    username: constr(min_length=3, max_length=50)
    password: constr(min_length=8, max_length=128)

# ✅ Output escaping
import html
def safe_text(text: str) -> str:
    return html.escape(text.strip())
```

---

## 7. Testing

### 7.1 Test Pyramid

```text
        /\       /\
       /  \     / E2E \       < 10%  End-to-End Tests
      /____\   /________\
     /      \ / INTEG  \      ~ 30%  Integration Tests
    /________/\__________\
   /         \  UNIT     \    ~ 60%  Unit Tests
  /___________\____________\
```

### 7.2 Coverage Requirements

| Type | Coverage | Target |
|------|----------|--------|
| Unit Tests | ≥ 80% | Utilities, services, business logic |
| Integration Tests | ≥ 50% | APIs, database interactions |
| E2E Tests | ≥ 20% | Key user flows (login, exam, learning) |

---

## 8. Deployment & Operations

### 8.1 Environment Standards

| Environment | Domain Example | Data Strategy | Release Permission |
|-------------|---------------|---------------|--------------------|
| Local Dev | localhost:8888 | Mock data | Developers |
| Test | test.mtscos.ai | Anonymized production snapshot | Test Engineers |
| Pre-production | pre.mtscos.ai | Production real data (read-only) | Operations |
| Production | www.mtscos.ai | Real user data | CTO approval |

### 8.2 Monitoring Thresholds

| Metric | Warning | Critical |
|--------|---------|----------|
| API Error Rate | > 5% | > 15% |
| Response Time P95 | > 800ms | > 2s |
| CPU Usage | > 70% | > 90% |
| Memory Usage | > 75% | > 90% |
| Disk Usage | > 80% | > 90% |
| DB Connections | > 80% limit | > 95% limit |

---

## 9. Code Quality

### 9.1 Code Review Checklist

- [ ] **Functionality**: Logic meets requirements
- [ ] **Edge Cases**: Null, extreme values, exception handling
- [ ] **Security**: No injection, permission checks, sensitive data protection
- [ ] **Performance**: No N+1 queries, reasonable algorithm complexity
- [ ] **Readability**: Naming conventions, clear comments, low complexity
- [ ] **Testability**: Injectable dependencies, no implicit global state
- [ ] **Compatibility**: API backward compatibility, safe DB migrations

### 9.2 Code Metrics Thresholds

| Metric | Threshold | Description |
|--------|-----------|-------------|
| Cyclomatic Complexity | ≤ 10 | Split if exceeded |
| Function Lines | ≤ 60 lines | Split if exceeded |
| Class Lines | ≤ 500 lines | Split if exceeded |
| File Lines | ≤ 1000 lines | Split if exceeded |
| Duplicate Code Rate | ≤ 5% | Use tools to detect |
| TODO/FIXME | ≤ 5 per file | Fix within deadline |

---

## 10. Documentation

### 10.1 Document Types

| Document | Format | Update Frequency | Owner |
|----------|--------|-----------------|-------|
| README.md | Markdown | Major versions | Architect |
| CHANGELOG.md | Markdown | Each release | Developer |
| API Docs | Swagger/Markdown | API changes | Backend |
| Architecture Doc | Markdown | Quarterly | Architect |
| Deployment Manual | Markdown | Environment changes | Operations |
| Database Dictionary | Markdown/HTML | Schema changes | DBA |
| Operations Manual | Markdown | Feature changes | Product |

---

## 11. UI/UX Design

### 11.1 Brand Color Palette

| Color | Value | Usage |
|-------|-------|-------|
| Primary Purple | `#6366f1` | Primary buttons, branding, highlights |
| Light Purple | `#8b5cf6` | Gradients, secondary emphasis |
| Accent Purple | `#a855f7` | Accent color, decorative gradients |
| Dark Purple | `#4f46e5` | Pressed state, dark emphasis |
| Background Start | `#050510` | Dark background gradient start |
| Background Mid | `#0c0c24` | Background gradient midpoint |
| Card Background | `rgba(12,12,30,0.7)` | Glassmorphism cards |

### 11.2 Component Standards

| Component | Radius | Height | Font Size |
|-----------|--------|--------|-----------|
| Small Button | 10px | 36px | 13px 600 |
| Standard Button | 12px | 46px | 15px 700 |
| Large Button | 14px | 52px | 16px 700 |
| Input Field | 12px | 46px | 14px |
| Card | 24px | - | - |

### 11.3 Responsive Breakpoints

```css
/* Mobile-first */
@media (min-width: 480px)  { /* Large phone */ }
@media (min-width: 768px)  { /* Tablet */ }
@media (min-width: 1024px) { /* Laptop */ }
@media (min-width: 1440px) { /* Desktop */ }
```

---

## 12. Education Business

### 12.1 Stage-Subject Matrix

| Stage | Main Subjects |
|-------|--------------|
| **Primary (1-6)** | Chinese, Math, English, Science, Ethics, PE, Arts |
| **Junior High (7-9)** | Chinese, Math, English, Physics, Chemistry, Biology, History, Geography, Politics, IT |
| **Senior High (10-12)** | Chinese, Math, English, Physics, Chemistry, Biology, History, Geography, Politics + Electives |
| **Higher Education** | Philosophy, Economics, Law, Education, Literature, History, Science, Engineering, Agriculture, Medicine, Management, Arts, Military (13 categories) |
| **Adult Education** | Continuing education, vocational training, skill certification, job training |

### 12.2 Difficulty Levels

| Level | Description | Cognitive Level |
|-------|-------------|-----------------|
| ★☆☆☆☆ Easy | Direct recall, basic concepts | Memory/Comprehension |
| ★★☆☆☆ Fairly Easy | Simple application, formula application | Comprehension/Application |
| ★★★☆☆ Medium | Comprehensive application, multiple concepts | Application/Analysis |
| ★★★★☆ Hard | Deep understanding, logical derivation | Analysis/Evaluation |
| ★★★★★ Expert | Innovative application, open-ended problems | Evaluation/Creation |

---

## 13. Hook & Heartbeat

### 13.1 Hook Lifecycle

| Hook Name | Trigger Timing | Purpose | Priority |
|-----------|---------------|---------|----------|
| `before_app_start` | Before Flask app starts | Init AI employees, load rules, preheat cache | critical |
| `after_app_start` | After Flask app starts | Start scheduler, register heartbeat, write start log | high |
| `before_request` | Before each request | Security check, permission verify, SA whitelist | critical |
| `after_request` | After each response | LayoutAI injection, error stats, logging | high |
| `before_login` | Before login verification | Username check, SA UI switch, password dot display | high |
| `after_login` | After login verification | USB Key verify, session write, 7-element check | critical |

### 13.2 Heartbeat Health Check

```text
Heartbeat Topology
├── Client Polling
│   ├── /auth/session_health every 10 seconds
│   ├── Trigger 2.5s after first visit
│   ├── Trigger immediately on visibilitychange
│   └── Exception → cacheOpsAndExit → logout → replace("/")
├── Server Heartbeat
│   ├── AIMonitor(monitoring.py) every 3 seconds
│   ├── AutoScheduler writes back after each task
│   ├── VIKEY hardware key insert/remove events
│   └── Container network connectivity check
└── Alert Thresholds
    ├── CPU > 80%
    ├── Memory > 85%
    ├── Disk > 90%
    ├── Response Time > 1000ms
    ├── Error Rate > 5%
    └── VIKEY: vikey_present=false or vikey_bound=false
```

---

## 14. AI Employee Matrix

### 14.1 AI Employee Type Mapping

| Category | ID Format | Typical Types | Knowledge Domain | Personality |
|----------|-----------|--------------|-----------------|-------------|
| General | ai_gen_*** | general | general_programming | analytical |
| Arduino | ai_ard_*** | arduino_code_generator/debugger | arduino/electronics | creative/analytical |
| Config Mgmt | ai_cfg_*** | config_manager/rule_base_maintenance | system_admin | cautious |
| Diagnostic | ai_diag_*** | diagnostics_repair/powerful_fix | diagnostics | driven |
| Question Bank | ai_qb_*** | question_bank_maintenance/k12_question | question_bank/k12 | analytical |
| Exam Proctor | ai_exam_*** | exam_ai/exam_proctor | education/validation | cautious |
| Ops/Deploy | ai_ops_*** | git_manager/deployment_expert | devops/operations | driven |
| Frontend Fix | ai_fe_*** | frontend_fixer/route_fixer | frontend/ux | creative |
| AI Security | ai_sec_*** | ai_cybersecurity/ai_vulnerability_scanner | cybersecurity | cautious |
| Data Governance | ai_data_*** | ai_data_analyzer/ai_knowledge_graph | data_science/knowledge | analytical |
| AI Self-Evolution | ai_self_*** | ai_self_improvement/ai_system_upgrader | ai_evolution | driven |
| Finance/CRM/HR | ai_biz_*** | ai_financial/ai_crm/ai_hr | business/finance/hr | supportive |

### 14.2 Trigger Conditions

1. **Explicit API Call**: `/api/ai_employee/{id}/execute`
2. **Scheduler Trigger**: AutoScheduler cron schedule
3. **Event Hook Trigger**: Hook callback from Section 13.1
4. **Error Report Trigger**: error_rate > 5% → auto-dispatch diagnostics cluster
5. **Learning Cycle Trigger**: before/after_learning_cycle dispatches AI employees
6. **Threshold Alert Trigger**: CPU/MEM/DISK/LATENCY exceeds threshold
7. **User Behavior Trigger**: Exam exit deducts points → reward_achievement_engine
8. **USB Key Event**: vikey_present=false → force super_admin session logout

---

## Appendix A: Version Information

| Item | Value |
|------|-------|
| System Name | MTSCOS AI · Intelligent Learning & Assessment Platform |
| Architecture Brand | MTS Architecture |
| Architecture Version | v2.0 |
| System Version | v17.22.0 |
| Rule Version | v1.2 (260+) |
| Release Date | 2026-07-26 |

## Appendix B: References

1. PEP 8 – Style Guide for Python Code
2. OWASP Top 10 Web Application Security Risks
3. Ministry of Education "Compulsory Education Curriculum Standards"
4. Ministry of Education "General High School Curriculum Plan"
5. "National Education Examination Security and Confidentiality Regulations"
6. Flask Official Documentation, SQLAlchemy Official Documentation
7. WAI-ARIA Accessibility Design Guide

---

> © 2026 MTSCOS AI · System Specification v1.3 · Based on MTS Architecture