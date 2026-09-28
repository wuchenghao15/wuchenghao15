# 📜 MTSCOS AI 版本变更日志

> 仙女座智能体宇宙 · 从 v1.0 到 v22.0+ 的进化记录

---

## 版本号规则

```
MAJOR.MINOR.PATCH+build
  │     │     │  │
  │     │     │  └── Build 号 (git commit)
  │     │     └───── PATCH: Bug 修复 / 文档优化
  │     └─────────── MINOR: 新功能 / API 扩展
  └───────────────── MAJOR: 架构变更 / 破坏性更新
```

---

## v22.0.0 — 仙女座整合 (2026-09-10)

### 🎉 重大里程碑

- **仙女座星系 25 恒星命名** — 25 功能域 → 25 颗仙女座恒星（α-ω + Nebula），每颗有独立视觉图标
- **Neural Hub 域路由化** — 41 路由 / 25 域，`domain` 字段成为一级分类
- **设计域 (design) 独立域** — 新增 `design_ingest` / `beautify_plan` / `eigenflux_design_review` 3 路由
- **前端美化层 (§11)** — +320 行 CSS，13 章节仙女座渐变主题
- **外部知识管道** — `knowledge_ingest` 通用消化 / `bilibili_sub_extract` yt-dlp B站字幕
- **首页 AI 员工数修复** — `_get_homepage_stats()` 补查 `mt_andromeda_employee_registry` (33,525)，合并旧表 32 → **33,557**

### 📊 数据变化

| 指标 | v21.x | v22.0.0 |
|------|-------|---------|
| AI 员工 | 10,840 | **33,557** |
| Neural Hub 路由 | 37 | **41** |
| 功能域 | 22 | **25** |
| 仙女座恒星 | 0 | **25** |
| 规则知识 chunks | 463 | **490** |
| 外部知识 chunks | 18 | **73** |

### 🗃️ 新增表

- `mt_andromeda_stars` — 25 颗恒星元数据（域→星映射）

### 🛠️ 新增 HTTP API

| Path | 说明 |
|------|------|
| `GET /api/andromeda/stars` | 全部恒星 |
| `GET /api/andromeda/stars/<domain>` | 单颗详情 |
| `POST /api/neuralhub/knowledge_feed` | 知识投喂 |
| `POST /api/neuralhub/bili_extract` | B 站字幕 |

### ⚙️ Daemon 周期调整

- `sys_rule_enforcer`: 300s → 300s（保持）
- 新增 knowledge_daemon 预留（1800s 周期巡检）

### 🐛 Bug 修复

| 问题 | 修复 |
|------|------|
| 首页 AI 员工数显示 120 | 补查 `mt_andromeda_employee_registry` |
| knowledge_inventory 401 AUTH_REQUIRED | 加入 `_API_PUBLIC_WHITELIST` + `_MT_HOTLINK_API_ALLOW_PREFIXES` |
| Flask 双进程遮挡（旧 PID 28523 + 新 PID 28570） | 全部 kill -9 + 单进程重启 |

---

## v21.x — EigenFlux 网络 (2026-08-22 ~ 2026-09-06)

### 主要变更

- **AI-EigenFlux 自动连线** — daemon 周期自动注册/交友/心跳
- **规则治理 3 张表** — `mt_rule_changelog` / `mt_rule_violation_alert` / `mt_rule_integrity_scan`
- **Git Hook 层** — pre-commit + pre-push 双重拦截
- **规则 12 篇体系建立** — L0 IRON_RULE → L1/L2 层级
- **confidentiality 机密等级 3 级** — 极密/机密/秘密 + 脱敏

---

## v20.x — Arduino 体系 (2026-07)

### 主要变更

- Arduino 教程 19 / 组件 15 / 实验 3 / 板卡 7
- 设备自动检测（VID:PID）+ 驱动适配
- C++ 代码编译 AI 辅助

---

## v19.x — 本地推理引擎 (2026-06)

### 主要变更

- **ai_local_inference_engine** — 零 token 本地推理
- tokens_saved 累计节省（不消耗任何云端 API）
- 15 daemon 进程体系完成

---

## v18.x — 规则引擎 8 组件 (2026-05)

### 主要变更

- rules_engine 模块：rule_meta / rule_version / rule_db / rule_interceptor / rule_pre_commit / rule_integrity_scanner / rule_violation_alert
- 规则版本自动 bump（MAJOR/MINOR/PATCH）
- 7 步审批流程

---

## v1.x → v17.x — 基础架构建设 (2024 ~ 2026)

Flask 300+ 路由 / SQLite 429 表 / Vue 前端 / 权限体系 11 级 / VIKEY 加密狗 / 三重保活 / macOS LaunchD + Crontab ...

---

## 里程碑一览

```
v1.0  ─── Flask 雏形 + SQLite 真源
v5.0  ─── 权限体系 + @system_container 装饰器
v10.0 ─── VIKEY 加密狗 + 7 要素认证
v12.0 ─── §14 IRON_RULE 12 步骤 (L0)
v15.0 ─── 三重保活架构 (Engine + LaunchD + Crontab)
v18.0 ─── 规则引擎 8 组件
v20.0 ─── Arduino IoT 体系
v22.0 ─── ⭐ 仙女座星系 25 恒星 + Neural Hub 域路由化
```

---

*CHANGELOG · 2026-09-10 · 仙女座 v22.0.0+*
