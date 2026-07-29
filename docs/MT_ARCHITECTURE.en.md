# MTS Architecture v2.0

> **Document Version**: 2.0
> **Updated**: 2026-07-26
> **Codename**: MTSCOS AI Architecture
> **System**: MTSCOS AI Intelligent Exam System

[中文版本 / Chinese Version](MT_ARCHITECTURE.md)

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Design Philosophy](#2-design-philosophy)
3. [Layered Architecture](#3-layered-architecture)
4. [AI Engine Matrix](#4-ai-engine-matrix)
5. [Data Architecture](#5-data-architecture)
6. [Security Architecture](#6-security-architecture)
7. [Deployment Architecture](#7-deployment-architecture)
8. [Extensibility Design](#8-extensibility-design)
9. [Version Roadmap](#9-version-roadmap)

---

## 1. Architecture Overview

### 1.1 Definition

**MTS Architecture (MTSCOS Twin-Synergy Architecture)** is the second-generation core technical architecture of MTSCOS AI — a dual-engine layered collaboration architecture (Question-Diagnosis dual-core scheduling).

### 1.2 Positioning

| Dimension | Description |
|-----------|-------------|
| **System Type** | Distributed intelligent education platform |
| **Core Positioning** | AI-driven intelligent exam and learning management system |
| **Tech Stack** | Python 3.9+, Flask 3.x, SQLite/MySQL, JavaScript, HTML5, CSS3 |
| **Deployment** | Monolithic app + distributed database + AI cluster |

### 1.3 Key Features

- **MTS Dual-Engine Core**: Question Engine + Diagnostic Engine dual-core scheduling, intelligent question generation and learning analysis
- **AI Self-Evolution**: Built-in AI self-learning system v2.0, automatically acquires knowledge from the network
- **Distributed Architecture**: 9+ independent SQLite shards (87 tables, 0 empty), supports shadow nodes + 3-factor data replication
- **High Availability**: Cluster management, health checks, automatic failover, 10% canary releases
- **Security-First**: VIKEY hardware key 7-factor strong authentication, AI firewall 360° scanning
- **Modular Design**: 550+ core AI engines/employees and 47 Agents, supporting independent deployment
- **LayoutAI Adjustment**: LayoutAdjusterAI employee with 20 split detection rules (LF001-LF020)
- **Memorial Day Theme**: Automatic black-and-white remembrance theme on National Memorial Day

---

## 2. Design Philosophy

### 2.1 Core Principles

**1. AI-First**
- All core business logic driven by AI engines
- AI self-learning system enables automatic knowledge updates

**2. Modular Architecture**
- Each module designed for independent deployment
- Modules communicate through well-defined APIs
- Event-driven communication for loose coupling

**3. Distributed Thinking**
- Data partitioned by business domain
- AI engines support cluster deployment
- Transparent routing across shards

**4. Self-Healing Design**
- Automatic fault detection and recovery
- 8-dimensional auto-repair system
- Preventive health diagnosis

**5. Human-Centered**
- AI augments human capabilities
- Teacher productivity focus
- Student learning experience prioritized

---

## 3. Layered Architecture

### 3.1 Architecture Layers

```text
┌─────────────────────────────────────────────────────┐
│                  Presentation Layer                │
│  Web │ Mobile H5 │ Admin UI │ API Gateway          │
├─────────────────────────────────────────────────────┤
│              MTS Dual-Engine Core                 │
│  ┌─────────────────┐  ┌─────────────────┐        │
│  │  Question Engine  │  │ Diagnostic Engine │        │
│  │  · Smart Generation│  │ · Multi-dimensional   │        │
│  │  · Adaptive Compose│  │   Analysis           │        │
│  │  · Difficulty Calib│  │ · Error Attribution  │        │
│  │  · Bank Maintenance │  │ · Path Recommendation │        │
│  └─────────────────┘  └─────────────────┘        │
├─────────────────────────────────────────────────────┤
│                  Business Layer                    │
│  User │ Exam │ Question │ Learning │ AI │ ...     │
├─────────────────────────────────────────────────────┤
│              AI Engine Matrix                      │
│  Learning │ Question │ Teaching │ Mgmt │ ...      │
├─────────────────────────────────────────────────────┤
│                  Data Layer                        │
│  SQLite Shards │ Redis │ MySQL (optional)          │
├─────────────────────────────────────────────────────┤
│              Infrastructure Layer                  │
│  Servers │ Docker │ Monitoring │ CI/CD             │
└─────────────────────────────────────────────────────┘
```

### 3.2 MTS Dual-Engine Core

The dual-engine core is inserted between the Business Layer and AI Engine Matrix:

- **Question Engine**: Smart question generation, adaptive exam composition, difficulty calibration, question bank maintenance
- **Diagnostic Engine**: Multi-dimensional learning analysis, error attribution, weakness identification, personalized path recommendation

### 3.3 Module Division Principles

1. **High Cohesion, Low Coupling**: Single responsibility, clear interfaces
2. **Independently Testable**: Each module testable in isolation
3. **Independently Deployable**: Supports modular release and canary
4. **Replaceable**: Modules can be replaced with better implementations
5. **No Circular Dependencies**: Strictly prohibited

---

## 4. AI Engine Matrix

### 4.1 Engine Categories

| Engine Category | Core Engines | Responsibility |
|----------------|-------------|---------------|
| **Learning** | Adaptive learning, intelligent diagnosis, path planning, error analysis | Personalized learning |
| **Question** | Question generation, exam composition, difficulty adjustment | Question bank construction |
| **Teaching** | Q&A, essay grading, teaching design | AI teaching assistance |
| **Management** | Behavior analysis, learning monitoring, scheduling | Educational administration |
| **Security** | Anomaly detection, content review, risk warning | System security |
| **Operations** | Performance monitoring, auto-repair, scheduling | Autonomous operations |
| **Self-Learning** | Knowledge acquisition, rule generation, strategy update | System self-evolution |

### 4.2 AI Employee Matrix

550+ AI employees organized into functional categories:

| Category | ID Format | Examples | Domain |
|----------|-----------|----------|--------|
| General | ai_gen_*** | general | general_programming |
| Arduino | ai_ard_*** | code_generator/debugger | arduino/electronics |
| Config Mgmt | ai_cfg_*** | config_manager | system_admin |
| Diagnostic | ai_diag_*** | diagnostics_repair | diagnostics |
| Question Bank | ai_qb_*** | question_bank_maintenance | question_bank/k12 |
| Exam Proctor | ai_exam_*** | exam_ai/exam_proctor | education/validation |
| Ops/Deploy | ai_ops_*** | git_manager/deployment_expert | devops/operations |
| Frontend Fix | ai_fe_*** | frontend_fixer | frontend/ux |
| AI Security | ai_sec_*** | ai_cybersecurity | cybersecurity |
| Data Governance | ai_data_*** | ai_data_analyzer | data_science/knowledge |
| AI Self-Evolution | ai_self_*** | ai_self_improvement | ai_evolution |
| Finance/CRM/HR | ai_biz_*** | ai_financial/ai_crm | business/finance/hr |

### 4.3 Agent System

47 Agents covering:
- Question authoring
- Exam composition
- Grading
- Diagnosis
- Learning planning
- Security auditing
- Git operations
- DevOps
- Layout repair
- Code fixing

---

## 5. Data Architecture

### 5.1 Distributed Shard Design

```text
Database Shards (9+ independent):
├── auth       - Authentication and authorization
├── exam       - Exam management
├── question   - Question bank
├── learning   - Learning analytics
├── user       - User management
├── system     - System configuration
├── admin      - Admin operations
├── log        - Logging
└── ai         - AI engine storage

Total: 87 tables (0 empty)
```

### 5.2 Data Flow

```text
Request → Shard Routing → Target Shard → Response
                ↓
          Cache (Redis) → Hit? → Return
                ↓ Miss
          Database Query → Result → Cache
```

### 5.3 Data Integrity

- Transparent routing
- Connection pool management
- Read/write splitting
- Replication support
- Backup verification

---

## 6. Security Architecture

### 6.1 Multi-Layer Protection

```text
Layer 1: WAF (Web Application Firewall)
  ├── SQL Injection Detection
  ├── XSS Filtering
  ├── RCE Prevention
  ├── SSRF Protection
  ├── LFI Prevention
  ├── Directory Traversal Blocking
  ├── Port Scan Detection
  ├── Brute Force Prevention
  ├── Rate Limiting
  └── Input Validation

Layer 2: Authentication
  ├── VIKEY Hardware Key
  ├── JWT Token (HS256, 2h + 7d refresh)
  ├── bcrypt Password Hashing
  └── 5-failure Lockout (15 min)

Layer 3: Authorization
  ├── RBAC (16-level roles)
  ├── ABAC (attribute-based filtering)
  ├── Permission Audit Trail
  └── Session Management

Layer 4: Application Security
  ├── Output Escaping
  ├── SQL Parameterization
  ├── Security Headers
  └── Content Security Policy

Layer 5: CI/CD Security
  ├── pip-audit scanning
  ├── Trivy container scanning
  ├── Bandit code analysis
  └── Dependabot updates
```

### 6.2 VIKEY Hardware Key

- 7-factor strong authentication
- Required for super admin login
- Forces logout on key removal
- USB hardware-based verification
- Audit logged

---

## 7. Deployment Architecture

### 7.1 Deployment Modes

| Mode | Description | Use Case |
|------|-------------|----------|
| **Single Node** | One server with all components | Development, testing |
| **Cluster** | Multiple nodes with load balancing | Production |
| **Cloud** | Cloud-native deployment | Scaling, high availability |

### 7.2 Production Stack

```text
Client → CDN → Nginx (SSL termination) → Flask App Cluster
                                              ↓
                                         Redis Cluster
                                              ↓
                                    SQLite Shards (9+)
                                              ↓
                                         AI Engine Cluster
```

### 7.3 Monitoring & Alerting

- Prometheus for metrics collection
- Grafana for visualization
- Alertmanager for alerts
- Health checks every 3-10 seconds
- Threshold-based alerting (CPU, memory, disk, latency)

---

## 8. Extensibility Design

### 8.1 Extension Mechanisms

- **Plugin System**: New functionality added as plugins
- **Module Hot-Swap**: Replace modules without downtime
- **API Versioning**: Backward-compatible API evolution
- **Database Migration**: Schema evolution with rollback support
- **AI Engine Registration**: New AI engines registered dynamically

### 8.2 Scaling Dimensions

- **Vertical**: More resources per node
- **Horizontal**: More nodes in cluster
- **Functional**: New features and modules
- **Geographic**: Multi-region deployment
- **AI Capacity**: More AI employees and agents

---

## 9. Version Roadmap

### 9.1 Current Version (v2.0)

- Dual-engine core architecture
- AI self-learning system
- 550+ AI employees
- VIKEY hardware integration
- LayoutAI adjustment system
- Memorial day theme

### 9.2 Planned Evolution

- **v2.1**: Enhanced self-learning capabilities, knowledge graph expansion
- **v2.2**: Multi-region deployment, geographic load balancing
- **v2.3**: Advanced AI planning, predictive analytics
- **v3.0**: Full AI autonomy, self-healing, zero-touch operations

---

## Appendix: Architecture Decision Record

| Decision | Date | Context | Consequence |
|----------|------|---------|-------------|
| Dual-engine core | 2026-07 | Need for separation of planning and execution | More flexible and evolvable |
| Distributed SQLite | 2026-07 | Avoid MySQL complexity while scaling | Zero-config bootstrap, transparent routing |
| VIKEY hardware key | 2026-07 | Enterprise-grade super admin security | Hardware-reinforced authentication |
| AI employee matrix | 2026-07 | Scaling AI capabilities beyond single models | Complete AI team, not just tools |
| Self-learning system | 2026-07 | Keep AI knowledge up-to-date | Automatic knowledge acquisition |

---

> © 2026 MTSCOS AI · MTS Architecture v2.0 · Twin-Synergy Dual-Engine