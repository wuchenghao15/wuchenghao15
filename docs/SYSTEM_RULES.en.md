# MTSCOS AI System Rules

> **Rule Version**: v1.2
> **Updated**: 2026-07-26
> **Total Rules**: 260+
> **Rule Domains**: 10
> **Architecture**: MTS Architecture v2.0
> **Scope**: MTSCOS AI Intelligent Learning & Assessment Platform

[中文版本 / Chinese Version](系统规则.md)

---

## Table of Contents

| Rule Domain | Prefix | Rules | Status |
|-------------|--------|-------|--------|
| [Development](#1-r-dev-development) | R-DEV | 25+ | ✅ Active |
| [AI Operations](#2-r-ai-ai-operations) | R-AI | 20+ | ✅ Active |
| [Security Compliance](#3-r-sec-security) | R-SEC | 20+ | ✅ Active |
| [Data Governance](#4-r-data-data-governance) | R-DATA | 20+ | ✅ Active |
| [Operations & Deployment](#5-r-ops-operations--deployment) | R-OPS | 20+ | ✅ Active |
| [K12 Education](#6-r-k12-k12-education) | R-K12 | 18+ | ✅ Active |
| [Adult Education](#7-r-adult-adult-education) | R-ADULT | 18+ | ✅ Active |
| [Higher Education](#8-r-higher-higher-education) | R-HIGHER | 20+ | ✅ Active |
| [User Management](#9-r-user-user-management) | R-USER | 22+ | ✅ Active |
| [System & MTS Architecture](#10-r-sys-system--mts-architecture) | R-SYS | 14+ | ✅ Active |
| [Self-Learning](#11-r-learn-self-learning) | R-LEARN | 72+ | ✅ Active |

---

## Rule Numbering System

```text
Format: R-{DOMAIN}-{SEQUENCE}
Example: R-DEV-001, R-AI-002, R-SEC-003

Domain Codes:
├── DEV    - Development
├── AI     - AI Operations
├── SEC    - Security
├── DATA   - Data Governance
├── OPS    - Operations & Deployment
├── K12    - K12 Education
├── ADULT  - Adult Education
├── HIGHER - Higher Education
├── USER   - User Management
├── SYS    - System & MTS Architecture
└── LEARN  - Self-Learning
```

### Priority Definitions

| Priority | Meaning | Enforcement |
|----------|---------|-------------|
| **high** | Must follow | Non-compliance causes system errors or security risks |
| **medium** | Should follow | Non-compliance may affect performance or experience |
| **low** | Reference only | Optimization suggestions, flexible handling |

### Status Definitions

| Status | Meaning |
|--------|---------|
| ✅ Active | Rule is enforced, must be followed |
| ⏳ Pending Review | Rule draft, awaiting review |
| 🔄 Pending Update | Existing rule needs iteration |
| ❌ Disabled | Rule temporarily inactive |

---

## 1. R-DEV Development

### R-DEV-001 Code Style
- **Priority**: high
- **Description**: All code must follow PEP 8, use 4-space indentation, single line max 120 chars, naming must be readable and semantic
- **Status**: ✅ Active

### R-DEV-002 Version Control
- **Priority**: high
- **Description**: All code changes must be managed through Git, commit messages must clearly describe changes and reasons, direct production modifications prohibited
- **Status**: ✅ Active

### R-DEV-003 Code Review
- **Priority**: high
- **Description**: All feature code must pass at least one code review before merging to main branch, focusing on security, performance, and architecture
- **Status**: ✅ Active

### R-DEV-004 Test Coverage
- **Priority**: high
- **Description**: Core feature code coverage must reach 80%+, new features must include unit and integration tests
- **Status**: ✅ Active

### R-DEV-005 Documentation Sync
- **Priority**: medium
- **Description**: Code changes must synchronize related documentation including API docs, config descriptions, and usage guides
- **Status**: ✅ Active

---

## 2. R-AI AI Operations

### R-AI-001 Model Invocation
- **Priority**: high
- **Description**: All AI model calls must go through unified interface, include timeout and retry mechanisms, and log full request/response
- **Status**: ✅ Active

### R-AI-002 Prompt Security
- **Priority**: high
- **Description**: All prompts must be validated for injection attacks, sensitive data must be filtered before sending to AI
- **Status**: ✅ Active

### R-AI-003 Output Validation
- **Priority**: high
- **Description**: AI outputs must be validated for format correctness, content safety, and business logic compliance before use
- **Status**: ✅ Active

### R-AI-004 Token Management
- **Priority**: medium
- **Description**: Token usage must be tracked per request and aggregated daily, alerts triggered when exceeding budgets
- **Status**: ✅ Active

### R-AI-005 Knowledge Graph Update
- **Priority**: medium
- **Description**: Knowledge graph must be updated quarterly, low-confidence knowledge (< 0.5) filtered, high-confidence (> 0.8) marked reliable
- **Status**: ✅ Active

---

## 3. R-SEC Security

### R-SEC-001 Password Policy
- **Priority**: high
- **Description**: Passwords must be at least 8 characters with complexity, stored with bcrypt (cost >= 12), rotated every 90 days
- **Status**: ✅ Active

### R-SEC-002 JWT Token Security
- **Priority**: high
- **Description**: JWT tokens use HS256, 2-hour access + 7-day refresh, stored in HttpOnly Secure SameSite cookies
- **Status**: ✅ Active

### R-SEC-003 Injection Prevention
- **Priority**: high
- **Description**: All user input must be sanitized, SQL uses parameterized queries, XSS output auto-escaped
- **Status**: ✅ Active

### R-SEC-004 RBAC Permission Check
- **Priority**: high
- **Description**: Every API endpoint must verify RBAC permissions, permission changes must be fully audited
- **Status**: ✅ Active

### R-SEC-005 Rate Limiting
- **Priority**: medium
- **Description**: API calls limited per IP/user, login attempts 5/15min, brute force detection enabled
- **Status**: ✅ Active

---

## 4. R-DATA Data Governance

### R-DATA-001 Data Quality
- **Priority**: high
- **Description**: All data must pass validation rules before storage, integrity checks on write, data lineage tracked
- **Status**: ✅ Active

### R-DATA-002 Data Privacy
- **Priority**: high
- **Description**: Personal data encrypted at rest and in transit, data minimization enforced, consent management required
- **Status**: ✅ Active

### R-DATA-003 Data Retention
- **Priority**: medium
- **Description**: Data retention follows business requirements, expired data auto-archived or deleted, retention policy documented
- **Status**: ✅ Active

### R-DATA-004 Data Backup
- **Priority**: high
- **Description**: Daily incremental + weekly full backup, backup verification weekly, point-in-time recovery tested quarterly
- **Status**: ✅ Active

---

## 5. R-OPS Operations & Deployment

### R-OPS-001 Environment Separation
- **Priority**: high
- **Description**: Dev/test/pre-prod/prod environments must be strictly separated, data anonymization between environments
- **Status**: ✅ Active

### R-OPS-002 Release Process
- **Priority**: high
- **Description**: All releases follow the process: dev → review → test → build → pre-prod → prod, rollback plan required
- **Status**: ✅ Active

### R-OPS-003 Monitoring Alerts
- **Priority**: high
- **Description**: CPU/MEM/DISK/RESP-TIME monitored, warnings at 70%/75%/80%/800ms, critical at 90%/90%/90%/2s
- **Status**: ✅ Active

### R-OPS-004 Container Management
- **Priority**: medium
- **Description**: Docker images must use multi-stage builds, base images pinned, security scan on every build
- **Status**: ✅ Active

---

## 6. R-K12 K12 Education

### R-K12-001 Subject Coverage
- **Priority**: high
- **Description**: K12 must cover: Chinese, Math, English, Physics, Chemistry, Biology, History, Geography, Politics, Science, IT
- **Status**: ✅ Active

### R-K12-002 Question Quality
- **Priority**: high
- **Description**: K12 questions must align with curriculum standards, difficulty distribution follows normal curve, knowledge points mapped
- **Status**: ✅ Active

### R-K12-003 Learning Path
- **Priority**: medium
- **Description**: K12 learning paths must be personalized based on grade, subject mastery, and exam preparation goals
- **Status**: ✅ Active

---

## 7. R-ADULT Adult Education

### R-ADULT-001 Credit System
- **Priority**: high
- **Description**: Adult education supports credit accumulation and conversion, credits valid across institutions
- **Status**: ✅ Active

### R-ADULT-002 Skill Certification
- **Priority**: high
- **Description**: Vocational skill certification exams must comply with national standards, exam content updated annually
- **Status**: ✅ Active

### R-ADULT-003 Learning Flexibility
- **Priority**: medium
- **Description**: Adult learning supports fragmented learning, mobile learning, and offline learning modes
- **Status**: ✅ Active

---

## 8. R-HIGHER Higher Education

### R-HIGHER-001 Academic Standards
- **Priority**: high
- **Description**: Higher education exams must comply with national academic standards, question difficulty aligned with course requirements
- **Status**: ✅ Active

### R-HIGHER-002 Major Coverage
- **Priority**: high
- **Description**: Must cover 13 academic categories: Philosophy, Economics, Law, Education, Literature, History, Science, Engineering, Agriculture, Medicine, Management, Arts, Military
- **Status**: ✅ Active

### R-HIGHER-003 Research Support
- **Priority**: medium
- **Description**: Higher education supports research method training, academic paper writing, and literature review capabilities
- **Status**: ✅ Active

---

## 9. R-USER User Management

### R-USER-001 User Registration
- **Priority**: high
- **Description**: Users must register with verified email/phone, password meets complexity requirements, agreement to terms required
- **Status**: ✅ Active

### R-USER-002 Role Management
- **Priority**: high
- **Description**: 16-level role system, RBAC+ABAC dual model, permission inheritance supported, role changes fully audited
- **Status**: ✅ Active

### R-USER-003 Profile Management
- **Priority**: medium
- **Description**: Users can manage profile info, preferences, learning history visible, account deletion supported
- **Status**: ✅ Active

---

## 10. R-SYS System & MTS Architecture

### R-SYS-001 MTS Architecture Compliance
- **Priority**: high
- **Description**: All system components must comply with MTS Architecture v2.0, dual-engine mode enabled, modular design enforced
- **Status**: ✅ Active

### R-SYS-002 Hook Lifecycle
- **Priority**: high
- **Description**: System hooks follow defined lifecycle: before_app_start → after_app_start → before_request → after_request → before_db_write
- **Status**: ✅ Active

### R-SYS-003 Heartbeat Monitoring
- **Priority**: high
- **Description**: Client heartbeat every 10s, server heartbeat every 3s, VIKEY hardware key event monitoring enabled
- **Status**: ✅ Active

### R-SYS-004 VIKEY Hardware Key
- **Priority**: high
- **Description**: Super admin login requires VIKEY USB hardware key, forced session logout on key removal
- **Status**: ✅ Active

---

## 11. R-LEARN Self-Learning

### R-LEARN-001 Knowledge Acquisition
- **Priority**: high
- **Description**: AI self-learning engine acquires knowledge from code, docs, and network sources, knowledge validated before storage
- **Status**: ✅ Active

### R-LEARN-002 Rule Generation
- **Priority**: high
- **Description**: Self-learning system generates new rules based on observed patterns, rules reviewed before activation
- **Status**: ✅ Active

### R-LEARN-003 Strategy Evolution
- **Priority**: medium
- **Description**: AI strategies evolve based on effectiveness metrics, A/B testing used for strategy comparison
- **Status**: ✅ Active

### R-LEARN-004 Capability Growth
- **Priority**: medium
- **Description**: AI employees' capabilities grow through experience, skill trees track proficiency levels
- **Status**: ✅ Active

### R-LEARN-005 Error Pattern Learning
- **Priority**: medium
- **Description**: Error patterns are learned from system logs, auto-repair triggers based on learned patterns
- **Status**: ✅ Active

### R-LEARN-006 Performance Feedback
- **Priority**: low
- **Description**: System collects performance feedback, optimizes algorithms based on usage patterns
- **Status**: ✅ Active

### R-LEARN-007 Auto Maintenance
- **Priority**: high
- **Description**: Auto maintenance runs every hour, includes backup, cache cleanup, and health verification
- **Status**: ✅ Active

---

## Appendix: Rule Domain Statistics

| Domain | Prefix | Rule Count | Key Priority |
|--------|--------|-----------|--------------|
| Development | R-DEV | 25+ | Code quality, review, testing |
| AI Operations | R-AI | 20+ | Model invocation, prompt security |
| Security | R-SEC | 20+ | Auth, injection prevention, RBAC |
| Data Governance | R-DATA | 20+ | Quality, privacy, backup |
| Operations | R-OPS | 20+ | Env separation, release, monitoring |
| K12 Education | R-K12 | 18+ | Subject coverage, question quality |
| Adult Education | R-ADULT | 18+ | Credit system, skill certification |
| Higher Education | R-HIGHER | 20+ | Academic standards, research |
| User Management | R-USER | 22+ | Registration, roles, profile |
| System & MTS | R-SYS | 14+ | Architecture compliance, hooks |
| Self-Learning | R-LEARN | 72+ | Knowledge, rules, strategy evolution |

---

> © 2026 MTSCOS AI · System Rules v1.2 · Based on MTS Architecture