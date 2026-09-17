# 🏗️ MTSCOS AI 系统说明书

> **版本**: v22.0.0+ · **生成时间**: 2026-09-10 · **数据库快照**: 429 表

---

## 目录

1. [系统架构总览](#1-系统架构总览)
2. [Flask 核心 — server_real_db.py](#2-flask-核心--server_real_dbpy)
3. [Neural Hub — AI 母体内核](#3-neural-hub--ai-母体内核)
4. [仙女座星系 — 25 恒星 · 25 域](#4-仙女座星系--25-恒星--25-域)
5. [AI 员工体系 — 33,525 人](#5-ai-员工体系--33525-人)
6. [引擎清单 — 55+ 文件](#6-引擎清单--55-文件)
7. [Daemon 体系 — 15 个自愈进程](#7-daemon-体系--15-个自愈进程)
8. [三重保活架构](#8-三重保活架构)
9. [规则体系 — 12 篇文档 · L0 IRON_RULE](#9-规则体系--12-篇文档--l0-iron_rule)
10. [数据库 Schema — 429 张表](#10-数据库-schema--429-张表)
11. [HTTP API 矩阵](#11-http-api-矩阵)
12. [部署架构](#12-部署架构)
13. [性能特征](#13-性能特征)

---

## 1. 系统架构总览

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        MTSCOS AI · 仙女座智能体宇宙                       │
│                                                                         │
│  ┌─ Frontend ────────────────────────────────────────────────────────┐  │
│  │  Jinja2 模板 + Vue 2 组件 + Element Plus + Tailwind CSS          │  │
│  │  / · /dashboard · /admin · /arduino · /exam · /learning · ...     │  │
│  └───────────────────────────────┬───────────────────────────────────┘  │
│                                  │ HTTP :8888                           │
│  ┌─ Flask 核心 ──────────────────┴───────────────────────────────────┐  │
│  │  server_real_db.py                                                 │  │
│  │  300+ @app.route · Blueprint 32 文件 · 405 路由                    │  │
│  │                                                                    │  │
│  │  Middleware 链:                                                    │  │
│  │  ┌─ before_request ──────────────────────────────────────────┐     │  │
│  │  │ ① 防盗链 _MT_HOTLINK_WHITELIST                            │     │  │
│  │  │ ② §14 IRON_RULE 开发流程拦截                              │     │  │
│  │  │  │  ②a _api_auto_auth_gate (权限自动推断)                  │     │  │
│  │  │  │  ②b @system_container (11 级角色)                       │     │  │
│  │  │  │  ②c VIKEY 加密狗实时检测                                │     │  │
│  │  │  │  ②d 用户容器 6 字段验证                                 │     │  │
│  │  │  ③ 规则引擎 Flask 拦截器                                   │     │  │
│  │  └─────────────────────────────────────────────────────────────┘   │  │
│  └───────────────────────────────┬───────────────────────────────────┘  │
│                                  │                                      │
│  ┌─ Neural Hub — AI 内核 ─────────┴───────────────────────────────────┐  │
│  │  ai_neural_hub.py + ai_local_inference_engine.py                   │  │
│  │  41 路由 · 25 域 · localhost:11435 (Ollama)                        │  │
│  │  qwen2.5:14b (通用) + qwen2.5-coder:14b (代码)                       │  │
│  │  零 token 消耗 · 本地推理                                          │  │
│  └───────────────────────────────┬───────────────────────────────────┘  │
│                                  │                                      │
│  ┌─ 仙女座星系 ───────────────────┴───────────────────────────────────┐  │
│  │  25 颗恒星 → 25 功能域 → 33,525 AI 员工                            │  │
│  │  mt_andromeda_stars (25) · mt_andromeda_employee_registry          │  │
│  └───────────────────────────────┬───────────────────────────────────┘  │
│                                  │                                      │
│  ┌─ Daemon 层 ────────────────────┴───────────────────────────────────┐  │
│  │  smart_mount_engine 管理 15 个循环进程 (bg-init)                    │  │
│  │  心跳 · 巡逻 · 规则执行 · 自动修复 · 本地推理 · ...                │  │
│  └───────────────────────────────┬───────────────────────────────────┘  │
│                                  │                                      │
│  ┌─ SQLite ──────────────────────┴───────────────────────────────────┐  │
│  │  429 张表 · WAL 模式 · 零假数据                                    │  │
│  │  mt_andromeda_* (7) · mt_ai_* (40+) · mt_arduino_* (5)             │  │
│  │  mt_rule_* (3) · mt_dev_flow_* (6) · mt_edu_* (4) · ...            │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│  ┌─ 规则体系 (垂直约束) ──────────────────────────────────────────────┐  │
│  │  §14 IRON_RULE L0 → 12 步骤 · 9 铁律 · 4 层拦截                    │  │
│  │  L1 核心规范 (4 篇) · L2 操作规范 (7 篇)                            │  │
│  │  rules_engine 8 组件 + Git pre-commit Hook                         │  │
│  └───────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Flask 核心 — server_real_db.py

### 2.1 入口

- **文件**: `flask-app/server_real_db.py`
- **监听**: `0.0.0.0:8888`（IPv4+IPv6 双栈）
- **启动方式**: `python server_real_db.py` 或 LaunchD wrapper
- **线程模型**: `threaded=True`

### 2.2 路由分层

| 层级 | 文件/来源 | 路由数 | 说明 |
|------|----------|--------|------|
| 主文件 | `server_real_db.py` | ~100 | 核心业务路由 |
| Blueprint | `app/api/*.py` | ~300 | 32 个 API Blueprint |
| Neural Hub | `/api/neuralhub/*` | 15+ | AI 调用/注册/查询 |
| 仙女座 | `/api/andromeda/stars*` | 2 | 恒星查询（2026-09-10 新增） |
| Arduino | 独立蓝图 | ~20 | IoT 设备管理 |
| 静态文件 | `/static/*` | — | CSS/JS/图片 |

### 2.3 中间件链 (before_request)

```
Request →
  ① _mt_hotlink_checker (防盗链)
  ② mt_rules_engine_before_request (规则拦截器)
  ③ _api_auto_auth_gate (API 权限自动推断)
  ④ @system_container 装饰器 (显式声明的路由)
  ⑤ session + VIKEY 检查
  → Route Handler → Response
```

### 2.4 权限模型

| 等级 | 说明 |
|------|------|
| `guest` | 未登录可访问（首页/公开 API） |
| `login` | 登录后可访问 |
| `admin` | 管理员（除 SA 外） |
| `super_admin` | 仅 `wuchenghao15`，7 要素认证 + VIKEY 实时检测 |

---

## 3. Neural Hub — AI 母体内核

### 3.1 架构

```python
# 调用示例
from engines.ai_neural_hub import get_hub
hub = get_hub()
result = hub.call(
    task_name="code_review",
    payload={"code": "...", "lang": "python"},
    flow_id="flow_xxx",
)
```

### 3.2 模型配置

| 模型 | 用途 | Ollama 端口 |
|------|------|-------------|
| `qwen2.5:14b` | 🥇 通用推理主力 (dev 档强制首选) | 11435 · Metal iGPU · 2.2s/字 |
| `qwen2.5:7b` | 🥈 通用兜底 (14b OOM/超时自动降级) | 11435 · Metal iGPU · 1.5s/字 |
| `qwen2.5-coder:14b` | 🆕 代码推理主力 (neural_hub 8 路由) | 11435 · Metal iGPU |
| `qwen2.5-coder:7b` | 代码兜底 | 11435 · Metal iGPU |
| `nomic-embed-text` | 🧠 768维向量 (仙女座 Stage 2 auto_retrieve) | 11435 · Metal iGPU · 0.3s |
| **Volcengine ARK** | 🛡️ 云端兜底 (本地全挂时激活) | ark.cn-beijing.volces.com |
| · doubao-seed-2-0-lite | 默认云端兜底 (3.6s) | — |
| · deepseek-v4-pro | 数学/逻辑/深度思考 | — |

### 3.3 路由域分布 (41 路由 · 25 域)

| Domain | 路由数 | AI 员工 | 说明 |
|--------|--------|---------|------|
| education | 6 | 4,902 | K12/高等/成人 · 题目生成/私教/课程 |
| system | 3 | 1,548 | 状态管理 · 学习 · 规划 |
| knowledge | 3 | 1,548 | 外部知识消化 · B站字幕 · 策展人 |
| devops | 3 | 1,548 | Git Hook · 性能 Profile · 依赖分析 |
| design | 3 | 1,810 | 设计知识吸收 · 美化方案 · EigenFlux 审查 |
| rule | 2 | 1,547 | 合规检查 · 规则巡逻 |
| model_probe | 2 | 220 | Ollama 健康探测 (通用+Coder) |
| security | 1 | 2,063 | 安全审计 |
| sa | 1 | 5,159 | SA 超级管理员顾问 · 员工最多域 |
| patrol | 1 | 1,548 | 源码巡逻 |
| repair | 1 | 1,549 | 自动修复 |
| dev | 1 | 1,031 | Code Review |
| eigenflux | 1 | 774 | AI-EigenFlux 社交网络 |
| arduino | 1 | 4,664 | C++ 编译检查 |
| incident | 1 | 258 | 故障分析 |
| permission | 1 | 258 | 权限检查 |
| database | 1 | 258 | Schema 设计 |
| routing | 1 | 258 | 路由诊断 |
| qa | 1 | 516 | API 契约测试 |
| port | 1 | 258 | 端口扫描 |
| copy | 1 | 516 | 文案写作 |
| firewall | 1 | 258 | AI 防火墙 |
| exam | 1 | 258 | 考试评分 |
| evolution | 1 | 517 | 自我升级 |
| brain | 1 | 259 | 知识投喂 |

### 3.4 HTTP 端点

| Method | Path | Auth | 说明 |
|--------|------|------|------|
| POST | `/api/neuralhub/call` | 公开 | 统一 AI 调用入口 |
| GET | `/api/neuralhub/routes` | 公开 | 路由列表 |
| POST | `/api/neuralhub/routes` | SA-only | 注册新路由 |
| DELETE | `/api/neuralhub/routes/<name>` | SA-only | 禁用路由 |
| GET | `/api/neuralhub/stats` | 公开 | Neural Hub 统计 |
| GET | `/api/neuralhub/employee_distribution` | 公开 | AI 员工布局 |
| GET | `/api/neuralhub/models` | 公开 | Ollama 模型发现 |
| GET | `/api/neuralhub/knowledge_inventory` | 公开 | 外部知识脑库 |
| POST | `/api/neuralhub/knowledge_feed` | SA-only | 投喂外部知识 |
| POST | `/api/neuralhub/bili_extract` | SA-only | yt-dlp B站字幕萃取 |
| GET | `/api/neuralhub/evolution_logs` | 公开 | 自进化日志 |
| GET | `/api/neuralhub/daemon_status` | 公开 | Daemon 状态 |
| POST | `/api/neuralhub/daemon_tick` | 公开 | Daemon 快速检查 |

---

## 4. 仙女座星系 — 25 恒星 · 25 域

### 4.1 恒星命名映射

```
#   恒星名               域               AI员工  主色       图标
1   Alpheratz (α And)    education        4,902  #2980B9    📚
2   Mirach (β And)       devops           1,548  #27AE60    ⚙️
3   Gamma And (γ)        dev              1,031  #F39C12    💻
4   Delta And (δ)        design           1,810  #9B59B6    🎨
5   Epsilon And (ε)      knowledge        1,548  #1ABC9C    🧠
6   Zeta And (ζ)         exam               258  #E74C3C    🏆
7   Eta And (η)          eigenflux          774  #FF6B9D    🤝
8   Theta And (θ)        security         2,063  #E67E22    🛡️
9   Iota And (ι)         permission         258  #8E44AD    🔑
10  Kappa And (κ)        system           1,548  #34495E    📊
11  Lambda And (λ)       evolution          517  #E91E63    🦅
12  Mu And (μ)           rule             1,547  #F1C40F    ⚖️
13  Nu And (ν)           patrol           1,548  #16A085    🔭
14  Xi And (ξ)           incident           258  #C0392B    ⚠️
15  Omicron And (ο)      repair           1,549  #7CB342    🔧
16  Pi And (π)           database           258  #6C3483    🗄️
17  Rho And (ρ)          routing            258  #5DADE2    🧭
18  Sigma And (σ)        qa                 516  #D4AC0D    🧪
19  Tau And (τ)          port               258  #1B2631    📡
20  Upsilon And (υ)      copy               516  #E59866    ✒️
21  Phi And (φ)          arduino          4,664  #C0392B    🔌
22  Chi And (χ)          firewall           258  #CA6F1E    🧱
23  Psi And (ψ)          sa               5,159  #ECF0F1    👑
24  Omega And (ω)        brain              259  #5B2C6F    🧠
25  Andromeda-Nebula     model_probe        220  🌈         🌌
```

### 4.2 恒星 HTTP API

| Method | Path | 说明 |
|--------|------|------|
| GET | `/api/andromeda/stars` | 全部 25 颗恒星元数据（公开） |
| GET | `/api/andromeda/stars/<domain>` | 单颗详情 + 域内路由 + 实际员工数 |

### 4.3 视觉图标

每颗恒星有一张 AI 生成的 `square_hd` 艺术化图标（渐变主色 + 域符号 + 星空背景），存储 URL 见 `mt_andromeda_stars.icon_image_url`。

---

## 5. AI 员工体系 — 33,525 人

### 5.1 数据源

| 表 | 数量 | 说明 |
|----|------|------|
| `mt_andromeda_employee_registry` | **33,525** | 主力员工注册表 |
| `ai_employees` (旧表) | 32 | 遗留表，首页统计时合并 |
| `eigenflux_registrations` | ~10,000+ | EigenFlux 社交网络账号 |

### 5.2 员工 → 路由映射

每个员工通过 `neuralhub_task` 字段归属一个 Neural Hub 路由，路由再归属于域。`rebalance_employee_routes('weighted_round_robin')` 函数可重新分配。

### 5.3 域路由分配

域按员工数量排序：

```
Psi And (SA域)    5,159  🥇 员工最多
Alpheratz (教育)  4,902  🥈
Phi And (Arduino) 4,664  🥉
Theta And (安全)  2,063
Delta And (设计)  1,810
```

---

## 6. 引擎清单 — 55+ 文件

核心引擎位于 `flask-app/engines/`，辅助组件分散在 `ai_engines/`、`core/services/`、`app/ai/`。

### 6.1 关键引擎

| 文件 | 职责 |
|------|------|
| `ai_neural_hub.py` | AI 母体内核 — 统一路由/模型/员工管理 |
| `ai_smart_mount_engine.py` | daemon 管理器 — 15 个循环进程生命周期 |
| `ai_local_inference_engine.py` | 本地推理 — 聊天/分类/审查/Bug 分析，零 token |
| `ai_rule_learning_engine.py` | 规则学习 — 9 篇规则自动学习 + 严格执行 |
| `auto_rule_strengthener.py` | 弱约束词自动强化 → 强约束 |
| `ai_auto_hire_engine.py` | 自动雇佣 — AI 员工 + EigenFlux 邀请 + 巡逻队补编 |
| `auto_patrol_engine.py` | 6 人 AI 巡逻队 — 巡检/收集/修复/验证/报告/持久 |
| `auto_patrol_squad_engine.py` | 巡逻小队委派 |
| `auto_repair_engine.py` | FAILED daemon 自动修复 |
| `deep_inspection_engine.py` | 深度巡检 — 页面/路由/代码逐行扫描 |
| `copy_inspection_engine.py` | 文案合规巡检 — 缺失/重复/占位符/硬编码 |
| `ai_file_organizer.py` | 智能文件整理 — 归类 + 清理临时 + 删除空目录 |
| `ai_eigenflux_network_engine.py` | AI-EigenFlux 自动连线/交友/心跳保活 |
| `ai_edu_sync_engine.py` | 教辅教改同步 (K12/高等/成人/文科/理化) |
| `ai_arduino_engine.py` | Arduino 教程/组件/实验/板卡同步 |
| `ai_arduino_detect_engine.py` | 设备自动检测 (VID:PID) + 驱动适配 |

### 6.2 rules_engine (8 组件)

| 组件 | 职责 |
|------|------|
| `rule_meta.py` | RULE_META 块解析 + 完整性校验 |
| `rule_version.py` | 版本号 bump 算法 + changelog |
| `rule_db.py` | 3 张规则治理表 DAO |
| `rule_interceptor.py` | Flask before_request 拦截规则修改请求 |
| `rule_pre_commit.py` | Git pre-commit Hook 主入口（含 SA bypass） |
| `rule_integrity_scanner.py` | 9 篇规则覆盖率扫描 + 弱约束词检测 |
| `rule_violation_alert.py` | 违反自动告警投喂 EigenFlux + 脑库 |
| 模板 `pre-commit-rule-check.sh` | Git Hook 部署模板 |

---

## 7. Daemon 体系 — 15 个自愈进程

### 7.1 smart_mount_engine 管理的 15 个 daemon

| # | 进程名 | 周期 | 职责 |
|---|--------|------|------|
| 1 | `sys_heartbeat_writer` | 30s | 系统心跳写入 |
| 2 | `sys_patrol_inspector` | 60s | daemon 状态巡检 |
| 3 | `auto_方向1_调度中枢_7` | 60s | AI 建议自动挂载 |
| 4 | `sys_arduino_detect` | 30s | Arduino 设备检测 + 驱动 |
| 5 | `sys_eigenflux_network` | 120s | AI-EigenFlux 连线/交友/心跳 |
| 6 | `sys_auto_repair` | 120s | FAILED daemon 自动修复 |
| 7 | `sys_local_inference` | 120s | 本地推理 (零 token) |
| 8 | `sys_rule_enforcer` | 300s | 规则学习 + 弱约束词扫描 |
| 9 | `sys_auto_patrol` | 300s | 源码巡逻队 (6 人 AI) |
| 10 | `sys_auto_hire` | 300s | AI 自动雇佣 + EigenFlux 邀请 |
| 11 | `sys_arduino_sync` | 600s | Arduino 内容同步 |
| 12 | `sys_deep_inspection` | 600s | 页面/路由/代码深度巡检 |
| 13 | `sys_edu_sync` | 600s | 教辅教改同步 |
| 14 | `sys_file_organizer` | 600s | 智能文件整理 |
| 15 | `sys_copy_inspection` | 900s | 文案合规巡检 |

---

## 8. 三重保活架构

```
Layer 1 — ENGINE 内置 (进程内)
├── reap_stale_pid() 清理硬杀后的残留 PID 文件
├── 3-heartbeat timeout → 自动重连 eigenflux_registrations
├── SIGTERM handler → 优雅写 last_heartbeat + 删 PID + 关 DB
└── 每个 daemon 有自己的循环 + try-except + 错误计数

Layer 2 — LAUNCHD (macOS, 用户登录触发)
├── ~/Library/LaunchAgents/com.mtscos.ai-eigenflux.plist
├── ~/Library/LaunchAgents/com.mtscos.smart-mount.plist
├── RunAtLoad=true → 用户登录立刻触发
└── wrapper → open -a Terminal .command (OneDrive TCC 绕过)

Layer 3 — CRONTAB (每分钟巡检)
├── * * * * * start_smart_mount_daemon.command check-keepalive
├── */10 * * * * python3 ai_file_organizer.py organize
└── check-keepalive: engine DOWN → open(1) fallback 补拉
```

---

## 9. 规则体系 — 12 篇文档 · L0 IRON_RULE

### 9.1 层级

```
L0 IRON_RULE (最高, 不可绕开)
└── §14 强制开发 12 步骤独立约束规则

L1 核心规范 (全局强制)
├── 开发规则.md · 设计规范.md · 用户权限.md
├── 版本升级规则.md · 规则治理与一致性规范.md
└── 机密等级与访问控制规范.md

L2 操作规范 (领域强制)
├── AI 系统操作规范.md · 系统操作规范.md
├── 系统参数数据规范与操作规范.md
├── 源码修改准则参考与思路方案.md
└── 题库管理规范与准则.md
```

### 9.2 §14 IRON_RULE 12 步骤

```
Step 1  → flow_created (提议)
Step 2  → EigenFlux 分析
Step 3  → EigenFlux 5 人 A 轮 (5/5 APPROVE)
Step 4  → AI 代表团 6/6 + 人工批准
Step 5  → 实施团队对接
Step 6  → SA 审批 + 验收
Step 7  → 方案/设计/代码产出
Step 8  → 验收通过
Step 9  → PASS + 经验沉淀
Step 10 → 版本升级评估
Step 11 → Git 同步
Step 12 → 1000 轮测试
Final  → FINAL_DONE
```

### 9.3 4 层强制执行拦截

```
Layer 1: Git pre-commit Hook
Layer 2: Flask before_request 拦截器
Layer 3: CI 自检流水线 (1000 轮测试)
Layer 4: Git pre-push Hook (FINAL_DONE 检查)
```

### 9.4 规则治理表

| 表 | 说明 |
|----|------|
| `mt_rule_changelog` | 规则版本变更记录（7 步审批留痕） |
| `mt_rule_violation_alert` | 违反自动告警投喂记录 |
| `mt_rule_integrity_scan` | 规则完整性自检报告 |

---

## 10. 数据库 Schema — 429 张表

### 10.1 核心表组

| 前缀 | 表数 | 说明 |
|------|------|------|
| `mt_andromeda_*` | 7 | 仙女座员工/恒星/规则知识/脑库 |
| `mt_ai_*` | 40+ | Neural Hub 路由/调用日志/心跳/集群/神经网络 |
| `mt_arduino_*` | 5 | Arduino 教程/组件/实验/板卡/同步日志 |
| `mt_edu_*` | 4 | 教辅同步内容/题型/实验/日志 |
| `mt_rule_*` | 3 | 规则治理 (changelog/violation/integrity) |
| `mt_dev_flow_*` | 6 | 开发流程 12 步骤跟踪 (session/event/state) |
| `mt_daemon_*` | 3 | daemon 注册表/状态/日志 |
| `mt_local_ai_*` | 2 | 本地推理日志/token 节省日汇总 |
| `mt_experience_*` | 1 | 经验库 |
| `mt_iron_rule_*` | 1 | IRON_RULE 违反记录（不可删除） |
| 其他 | ~370 | 考试/题库/用户权限/认证/文件/监控 ... |

### 10.2 关键表详情

#### `mt_andromeda_stars` (25 行)

| 列 | 类型 | 说明 |
|----|------|------|
| `star_id` | INTEGER PK | 1-25 |
| `star_name` | TEXT | 恒星英文名 |
| `greek_letter` | TEXT | 希腊字母 (α And) |
| `domain` | TEXT UNIQUE | 功能域 |
| `color_hex` | TEXT | 主色 |
| `icon_symbol` | TEXT | Emoji |
| `icon_image_url` | TEXT | AI 生成图标 URL |
| `employee_count` | INTEGER | 域内员工数快照 |
| `route_count` | INTEGER | 域内路由数 |

#### `mt_ai_neural_routes` (41 行)

| 列 | 类型 | 说明 |
|----|------|------|
| `route_id` | INTEGER PK | |
| `task_name` | TEXT | 路由名 (code_review) |
| `domain` | TEXT | 域 |
| `primary_model` | TEXT | qwen2.5:14b / qwen2.5-coder:14b |
| `fallback_model` | TEXT | 回退模型 |
| `system_prompt` | TEXT | System prompt |
| `temperature` | REAL | 温度 |
| `enabled` | INTEGER | 1=启用 |
| `call_count` | INTEGER | 累计调用次数 |
| `success_rate` | REAL | 成功率 |

#### `mt_andromeda_employee_registry` (33,525 行)

| 列 | 类型 | 说明 |
|----|------|------|
| `employee_id` | INTEGER PK | |
| `employee_name` | TEXT | AI 员工名 |
| `neuralhub_task` | TEXT | 归属路由 |
| `domain` | TEXT | 归属域 |
| `employee_type` | TEXT | employee_type 映射 |
| `created_at` | TEXT | |

---

## 11. HTTP API 矩阵

### 11.1 公开 API（无需登录）

| Path | 说明 |
|------|------|
| `/` / `/index` | 首页渲染 |
| `/api/health` | 健康检查 |
| `/api/system_version` | 版本信息 |
| `/api/homepage/stats` | 首页统计（公开） |
| `/api/neuralhub/routes` | 路由列表 |
| `/api/neuralhub/call` | AI 调用（公开） |
| `/api/neuralhub/knowledge_inventory` | 外部知识清单 |
| `/api/neuralhub/employee_distribution` | 员工分布 |
| `/api/andromeda/stars` | 25 颗恒星 |
| `/api/andromeda/stars/<domain>` | 单颗恒星详情 |
| `/api/arduino/events/poll` | Arduino 设备轮询 |
| `/auth/login` | 登录 |
| `/auth/check` | 登录态检查 |

### 11.2 登录后 API

| Path | 说明 |
|------|------|
| `/api/exam/*` | 考试管理 |
| `/api/learning/*` | 学习记录 |
| `/api/question/*` | 题目管理 |
| `/api/console/*` | 控制台 |

### 11.3 SA-only API

| Path | 说明 |
|------|------|
| `/api/neuralhub/knowledge_feed` | 知识投喂 |
| `/api/neuralhub/bili_extract` | B 站字幕 |
| `/api/neuralhub/routes` (POST) | 注册路由 |
| `/api/neuralhub/routes/<name>` (DELETE) | 禁用路由 |
| `/api/rules/*` | 规则修改（需 7 步审批） |

---

## 12. 部署架构

```
macOS MacBook Pro
├── Flask server_real_db.py :8888 (主进程)
├── Ollama :11435 (Metal iGPU · 24GB 共享)
│   ├── qwen2.5:14b 🥇 (通用主力) · qwen2.5:7b 🥈 (兜底)
│   ├── qwen2.5-coder:14b 🆕 (代码主力) · qwen2.5-coder:7b (兜底)
│   ├── nomic-embed-text (768维语义向量)
│   └── Volcengine ARK 🛡️ 云端兜底 (133 模型 · 3.6s)
├── SQLite app.db (OneDrive 同步)
├── LaunchDaemon (开机自动启动)
├── Crontab (每分钟巡检 + 每 10 分钟文件整理)
└── VIKEY USB 加密狗 (SA 认证)

数据流:
  Flask → Neural Hub → Ollama → 返回
  Daemon → Flask API → Neural Hub → Ollama
  Git pre-commit → rules_engine → 7 步审批检查
```

---

## 13. 性能特征

| 指标 | 数值 |
|------|------|
| 本地推理延迟 | ~1-3s (qwen2.5:14b) |
| 数据库查询 | <100ms (WAL 模式) |
| Daemon 心跳 | 30s-900s 分级别 |
| 内存占用 | ~80-120MB (Flask) |
| CPU 峰值 | Ollama 推理时 ~200% (多核) |
| Token 成本 | **0** (全本地) |
| 并发 Flask 线程 | threaded=True (GIL, CPU 密集型放 Ollama) |

---

*系统说明书 · 2026-09-10 · 仙女座星系 v22.0.0+*
