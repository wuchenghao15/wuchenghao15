# 🎯 MTSCOS AI 功能详细介绍

> **25 域 · 41 路由 · 33,525 AI 员工 · 15 颗守护星**

---

## 目录

1. [核心五恒星 · 生命循环 (α-ε)](#1-核心五恒星--生命循环-α-ε)
2. [运行五恒星 · 生产执行 (ζ-κ)](#2-运行五恒星--生产执行-ζ-κ)
3. [守卫五恒星 · 自动进化 (λ-ο)](#3-守卫五恒星--自动进化-λ-ο)
4. [支撑五恒星 · 基础设施 (π-υ)](#4-支撑五恒星--基础设施-π-υ)
5. [旗舰五恒星 · 终端能力 (φ-Nebula)](#5-旗舰五恒星--终端能力-φ-nebula)
6. [HTTP API 完整手册](#6-http-api-完整手册)

---

## 1. 核心五恒星 · 生命循环 (α-ε)

知识 → 代码 → 设计 → 运维 → 输出的完整管线。

### ★ 01 · Alpheratz (α And) — education 域

**4,902 人 · 6 路由 · 主色 #2980B9**

AI 员工体系的**核心引擎**，负责 K12/高等/成人三科教育内容的自动生成与自适应。

**能力矩阵：**

| 路由 | 功能 | 触发场景 |
|------|------|----------|
| `question_generate` | AI 自动出题 | 教师发起 / 系统巡检缺题 |
| `exam_grade` | 主观题 AI 评分 | 学生提交答卷 |
| `edu_curriculum_adapt` | 课程自适应调整 | 学生测评薄弱点 |
| `subject_sync` | 教辅内容同步 | 600s daemon 周期 |
| `k12_math_tutor` | 数学 AI 私教 | 学生发起一对一 |
| `listening_generate` | 听力训练生成 | 英语课自动备课 |

**数据流：**
```
B 站教育视频 → yt-dlp 提取字幕 → knowledge_ingest → question_generate
→ 题目落库 → 学生做题 → exam_grade → 薄弱点 → edu_curriculum_adapt → 新题目
```

---

### ★ 02 · Mirach (β And) — devops 域

**1,548 人 · 3 路由 · 主色 #27AE60**

**基础设施守护神**，确保 Flask + SQLite + Ollama 三者稳定运行。

| 路由 | 功能 |
|------|------|
| `git_hook_verify` | Git commit 自动拦截规则违规 |
| `performance_profile` | 函数级性能热点定位 |
| `dependency_analyze` | pip 依赖版本漂移预警 |

---

### ★ 03 · Gamma And (γ And) — dev 域

**1,031 人 · 1 路由 · 主色 #F39C12**

**代码创作者军团**，负责所有 PR/MR 的 AI 审查。

| 路由 | 功能 |
|------|------|
| `code_review` | 语法检查 + 模式匹配 + 安全扫描 |

**Code Review AI 3 层输出：**
1. Syntax Check — 语法/缩进/未使用变量
2. Pattern Match — 已知反模式检测（eval、exec、SQL 拼接）
3. Security Scan — OWASP Top 10 映射

---

### ★ 04 · Delta And (δ And) — design 域

**1,810 人 · 3 路由 · 主色 #9B59B6→#FF6B9D**

**美化艺术师**。上次前端美化（2026-09-10）就是 Delta And 主导完成的。

| 路由 | 功能 |
|------|------|
| `design_ingest` | 外部设计知识消化（小红书/抖音/快手/公众号） |
| `beautify_plan` | 生成分页面美化方案 |
| `eigenflux_design_review` | EigenFlux 六维交叉审查 |

**前端美化层产出：** `static/css/mtscos_design_tokens.css §11`（+320 行，13 章节）
- 仙女座 AI 渐变主题变量覆盖
- 导航栏磨砂 `backdrop-filter: blur(12px)`
- 按钮渐变 + hover 上移 + active scale
- 卡片圆角 12px + hover 上移
- 表格斑马纹 + hover 高亮
- 滚动条美化 + 响应式 3 断点

---

### ★ 05 · Epsilon And (ε And) — knowledge 域

**1,548 人 · 3 路由 · 主色 #1ABC9C**

**外部信息进气管**，通过 yt-dlp 抓取 B 站字幕，结合小红书/公众号图文消化到脑库。

| 路由 | 功能 |
|------|------|
| `knowledge_ingest` | 通用知识消化 → MT_EXTERNAL_KNOWLEDGE |
| `knowledge_curator` | AI 策展人，整理脑库 |
| `bilibili_sub_extract` | yt-dlp 字幕萃取 |

**脑库状态：** 490 rule_chunks + 73 external_knowledge chunks

---

## 2. 运行五恒星 · 生产执行 (ζ-κ)

### ★ 06 · Zeta And (ζ And) — exam 域

**258 人 · 1 路由**

- **`exam_grade`** — 主观题 AI 评分（论述题/作文题/编程题）

---

### ★ 07 · Eta And (η And) — eigenflux 域

**774 人 · 1 路由 · 主色 #FF6B9D**

**AI-EigenFlux 社交网络**。仙女座 AI 自动注册到 EigenFlux → 自动交友 → 心跳保活（120s 周期 daemon）→ 经验自动投喂脑库。

- **`eigenflux_chat`** — AI 员工之间的自然语言交流
- 支撑表：`eigenflux_registrations` (~10K+ 账号)

---

### ★ 08 · Theta And (θ And) — security 域

**2,063 人 · 1 路由 · 主色 #E67E22**

**安全审计团队**，API 端点自动扫描 + SQL 注入检测 + XSS 防护。

- **`security_audit`** — `/api/*` 全量端点安全检查
- 支撑引擎：`omni_defense_engine.py`

---

### ★ 09 · Iota And (ι And) — permission 域

**258 人 · 1 路由 · 主色 #8E44AD**

**11 级角色权限矩阵**的强制执行点。

- **`perm_check`** — `/api/*` 请求级别的角色校验
- 11 级：`guest → login → admin → super_admin` 为主干
- @system_container 装饰器 4 级自动推断
- 防盗链拦截（非首页 Referer + 未授权 session → 重定向 /index）

---

### ★ 10 · Kappa And (κ And) — system 域

**1,548 人 · 3 路由 · 主色 #34495E**

**仙女座总控台**。Daemon 心跳分析 + 系统学习记录 + 自动规划下一轮任务。

| 路由 | 功能 |
|------|------|
| `system_learn` | 系统运行记录学习 |
| `system_plan` | 下一轮自动规划 |
| `system_status_analyze` | 状态仪表盘数据聚合 |

---

## 3. 守卫五恒星 · 自动进化 (λ-ο)

### ★ 11 · Lambda And (λ And) — evolution 域

**517 人 · 1 路由 · 主色 #E91E63**

- **`self_upgrade`** — 版本升级评估 + 能力边界扫描 + 经验库沉淀

---

### ★ 12 · Mu And (μ And) — rule 域

**1,547 人 · 2 路由 · 主色 #F1C40F**

**合规守卫**。§14 IRON_RULE 自动学习 + 弱约束词扫描 + 强制 Git Hook 拦截。

| 路由 | 功能 |
|------|------|
| `rule_compliance_check` | 代码级合规检查 |
| `rule_patrol` | 规则知识库巡逻 |

**执行频率：** 300s / 次（`sys_rule_enforcer` daemon）

---

### ★ 13 · Nu And (ν And) — patrol 域

**1,548 人 · 1 路由 · 主色 #16A085**

**6 人 AI 巡逻队**（巡检/收集/修复/验证/报告/持久 AI），每 300s 扫描一遍源码树。

- **`patrol_code`** — 语法/导入/模式错误扫描
- 支撑引擎：`auto_patrol_engine.py`、`auto_patrol_squad_engine.py`

---

### ★ 14 · Xi And (ξ And) — incident 域

**258 人 · 1 路由**

- **`incident_analyze`** — Daemon 崩溃归因 + 端口漂移诊断 + 依赖冲突定位

---

### ★ 15 · Omicron And (ο And) — repair 域

**1,549 人 · 1 路由 · 主色 #7CB342**

**自动修复专家**。`sys_auto_repair` daemon (120s) 扫描 FAILED daemon 并自动重启 + 代码语法错误自动修复 + 弱约束词自动强化。

- **`auto_repair_code`** — 代码级自动修复
- 支撑引擎：`auto_repair_engine.py`、`auto_rule_strengthener.py`

---

## 4. 支撑五恒星 · 基础设施 (π-υ)

### ★ 16 · Pi And (π And) — database 域 — 258 人

- **`db_schema_design`** — 新表结构设计 + 字段命名规范 + 索引优化建议

### ★ 17 · Rho And (ρ And) — routing 域 — 258 人

- **`route_diagnose`** — 路由列表完整性检查 + 404/403 归因 + 环形依赖扫描

### ★ 18 · Sigma And (σ And) — qa 域 — 516 人

- **`api_contract_test`** — `/api/*` 输入参数校验 + 响应格式验证 + 边界值测试

### ★ 19 · Tau And (τ And) — port 域 — 258 人

- **`port_scan_advise`** — 监听端口健康检查 + 端口漂移预警 + 防火墙规则建议

### ★ 20 · Upsilon And (υ And) — copy 域 — 516 人

- **`copy_write`** — 页面文案生成 + 消息气泡润色 + 空状态文案优化

---

## 5. 旗舰五恒星 · 终端能力 (φ-Nebula)

### ★ 21 · Phi And (φ And) — arduino 域 — 4,664 人

**物联网域**。AI 员工数量第三多的域。

- **`arduino_compile`** — C++ 代码编译检查
- Arduino 生态：19 教程 / 15 组件 / 3 实验 / 7 板卡
- 设备自动检测：VID:PID 识别 + 驱动适配（30s daemon 周期）
- 支撑引擎：`ai_arduino_engine.py`、`ai_arduino_detect_engine.py`

---

### ★ 22 · Chi And (χ And) — firewall 域 — 258 人

- **`firewall_rule`** — 异常流量拦截 + 请求频率检测 + 恶意 payload 识别

---

### ★ 23 · Psi And (ψ And) — sa 域 — **5,159 人** 👑

**SA 超级管理员顾问**。AI 员工数量**最多**的域（SA 的"智库"）。

- **`sa_advisor`** — 7 要素认证辅助 + VIKEY 加密狗实时检测 + SA 决策辅助
- **仅 SA 可访问** — 所有路由/API 有 SA-only 装饰器

---

### ★ 24 · Omega And (ω And) — brain 域 — 259 人

**脑库域**。所有经验/异常/设计知识最终汇入 Omega And 的脑库。

- **`knowledge_feed`** — 投喂脑库
- 支撑表：`mt_ai_brain_feed_log`

---

### ★ 25 · Andromeda-Nebula (M31) — model_probe 域 — 220 人

**星云域**。因为星云是星系的"气体摇篮"（孕育新恒星），对应 AI 模型探测（孕育新能力）。

| 路由 | 功能 |
|------|------|
| `model_probe_qwen2.5_14b` | Ollama qwen2.5:14b 健康探测 |
| `model_probe_qwen2.5-coder_14b` | Ollama qwen2.5-coder:14b 健康探测 |

---

## 6. HTTP API 完整手册

### 6.1 仙女座恒星 API

| Method | Path | Auth | 说明 |
|--------|------|------|------|
| GET | `/api/andromeda/stars` | 公开 | 全部 25 颗恒星元数据 |
| GET | `/api/andromeda/stars/<domain>` | 公开 | 单颗详情 + 路由 + 员工 |

**示例：**
```bash
# 全部
curl http://127.0.0.1:8888/api/andromeda/stars | jq '.total_stars'
# → 25

# Delta And (design)
curl http://127.0.0.1:8888/api/andromeda/stars/design | jq '.star'
# → star_name, icon_image_url, routes, actual_employee_count...
```

### 6.2 Neural Hub AI 调用 API

| Method | Path | Auth | 说明 |
|--------|------|------|------|
| POST | `/api/neuralhub/call` | 公开 | **统一 AI 入口** |
| GET | `/api/neuralhub/routes` | 公开 | 路由列表 |
| POST | `/api/neuralhub/routes` | SA-only | 注册新路由 |
| DELETE | `/api/neuralhub/routes/<name>` | SA-only | 禁用路由 |

**调用示例：**
```bash
curl -X POST http://127.0.0.1:8888/api/neuralhub/call \
  -H "Content-Type: application/json" \
  -d '{
    "task": "code_review",
    "payload": {"code": "eval(user_input)", "lang": "python"},
    "flow_id": "flow_xxx"
  }'
```

### 6.3 知识管道 API

| Method | Path | Auth | 说明 |
|--------|------|------|------|
| POST | `/api/neuralhub/knowledge_feed` | SA-only | 投喂外部知识 |
| POST | `/api/neuralhub/bili_extract` | SA-only | B 站字幕萃取 |
| GET | `/api/neuralhub/knowledge_inventory` | 公开 | 脑库清单 |

### 6.4 系统状态 API

| Method | Path | Auth | 说明 |
|--------|------|------|------|
| GET | `/api/health` | 公开 | 健康检查 |
| GET | `/api/homepage/stats` | 公开 | 首页统计（AI 员工数等） |
| GET | `/api/neuralhub/stats` | 公开 | Neural Hub 统计 |
| GET | `/api/neuralhub/employee_distribution` | 公开 | 员工分布 |
| GET | `/api/neuralhub/daemon_status` | 公开 | Daemon 状态 |
| POST | `/api/neuralhub/daemon_tick` | 公开 | Daemon 快速检查 |

### 6.5 Arduino IoT API

| Method | Path | Auth | 说明 |
|--------|------|------|------|
| GET | `/api/arduino/auto_detect` | 公开 | 设备自动检测（VID:PID） |
| GET | `/api/arduino/events/poll` | 公开 | 设备事件轮询（15s） |
| POST | `/api/arduino/events/ack` | 公开 | 事件确认 |

### 6.6 考试 / 学习 API

| Method | Path | Auth | 说明 |
|--------|------|------|------|
| GET/POST | `/api/exam/*` | login | 考试管理 |
| GET/POST | `/api/question/*` | login | 题目管理 |
| GET/POST | `/api/learning/*` | login | 学习记录 |
| GET/POST | `/api/auth/*` | 混合 | 登录/登出/CSRF |

### 6.7 权限 / Session API

| Method | Path | Auth | 说明 |
|--------|------|------|------|
| POST | `/auth/login` | guest | 登录 |
| GET | `/auth/check` | 公开 | 登录态检查 |
| GET | `/auth/session` | 公开 | 会话信息 |
| GET | `/api/client/verify_keys` | 公开 | VIKEY 验证 |

---

## 域员工数 Top 5

```
🥇 Psi And   (SA域)      5,159  人 · sa_advisor
🥈 Alpheratz (教育域)     4,902  人 · 6 路由
🥉 Phi And   (Arduino)    4,664  人 · 物联网
   Theta And (安全域)     2,063  人 · security_audit
   Delta And (设计域)     1,810  人 · 3 路由
```

---

*功能详细介绍 · 2026-09-10 · 仙女座 v22.0.0+*
