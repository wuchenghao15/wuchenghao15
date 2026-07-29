# MTSCOS AI 智能考试系统 - 系统说明书 / System Manual

> 版本: v17.22.0 (SuperAdmin UX Unified Edition) | Version: v17.22.0
> 更新日期: 2026-07-26 | Updated: 2026-07-26
> 文档版本: 17.0 | Document Version: 17.0
>
> [English Version / 英文版](SYSTEM_DOC.en.md)

## 目录

1. [系统概述](#1-系统概述)
2. [设计哲学与灵感来源](#2-设计哲学与灵感来源)
3. [系统架构](#3-系统架构)
4. [模块化启动系统](#4-模块化启动系统)
5. [分布式数据库](#5-分布式数据库)
6. [AI智能引擎矩阵](#6-ai智能引擎矩阵)
7. [题库系统](#7-题库系统)
8. [权限管理体系](#8-权限管理体系)
9. [AI集群与模型库](#9-ai集群与模型库)
10. [安全架构](#10-安全架构)
11. [自维护运维OS](#11-自维护运维os)
12. [端口管理系统](#12-端口管理系统)
13. [集群管理系统](#13-集群管理系统)
14. [Git自动同步](#14-git自动同步)
15. [前端页面系统](#15-前端页面系统)
16. [移动端适配](#16-移动端适配)
17. [AI智能题目生成器](#17-ai智能题目生成器)
18. [AI智能学习路径推荐](#18-ai智能学习路径推荐)
19. [AI试卷自动组卷系统](#19-ai试卷自动组卷系统)
20. [学生成绩分析仪表盘](#20-学生成绩分析仪表盘)
21. [项目思维导图](#21-项目思维导图)
22. [版本历史](#22-版本历史)
23. [API接口文档](#23-api接口文档)
24. [部署指南](#24-部署指南)

---

## 1. 系统概述

MTSCOS AI 智能考试系统是一个基于 Flask 框架的分布式智能考试管理平台。v17.22.0 版本代号 "SuperAdmin UX Unified Edition"（超管UX统一版），主要新增超管识别隐藏记住我/忘记密码/创建账号、VIKEY 全链路打通、主版本+20子系统统一对齐、CI 接入 Dependabot+Trivy+Bandit 等特性。

### 核心特性
- **MTS架构v2.0双引擎**：规划引擎（策略）+ 执行AI员工阵列（550+ AI员工/引擎、47 Agent），8阶段配置加载 + 6阶段模块加载
- **分布式数据库架构**：9+ 独立SQLite分片（auth/exam/question/learning/user/system/admin/log/ai），共 87 张表（0 空表），透明路由，开箱零配置
- **AI智能引擎矩阵**：550+ 专业AI员工/引擎与 47 个 Agent，技能可进化、故障可自愈
- **完整题库系统**：11门学科 × 7种题型 × 3Bloom层级，实时AI生成 + 网络爬取
- **企业级权限管理**：RBAC 16级角色 + ABAC属性过滤，50+权限规则，全链路不可篡改审计
- **AI防火墙+应用安全**：WAF 10条规则（SQLi/XSS/RCE/SSRF/LFI/目录穿越/扫描/暴力破解/限流）+ pip-audit/Trivy/Bandit/CodeQL
- **自维护运维OS**：8维自动修复（表结构/配置/缓存/连接池/回滚/数据恢复/索引/ACL）+ 8维预防式健康诊断
- **统一版本API**：1个主版本 + 20个子系统版本，批量升级/回滚/版本锁定/变更历史
- **响应式 + 移动门户**：桌面/平板/手机布局全覆盖，移动端独立登录与考试页，VIKEY USB硬件密钥登录

### 系统优势矩阵

| 优势维度 | 核心能力 | 差异化价值 |
| :--- | :--- | :--- |
| **架构设计** | MTS双引擎分层协作 | 规划与执行分离，策略可进化，执行可扩展 |
| **AI能力** | 550+专业AI员工/引擎、47 Agent 自治协作 | 不是单点AI工具，而是完整的AI团队 |
| **安全性** | VIKEY硬件密钥+AI防火墙+多层防护 | 企业级安全，超管登录硬件加固 |
| **运维效率** | 8维自动修复+预防式诊断 | 系统自我维护，减少人工干预 |
| **学习效果** | IRT+RL自适应学习路径 | 科学的学习推荐，艾宾浩斯螺旋复习 |
| **部署体验** | 开箱零配置+Docker支持 | 分钟级部署，无需复杂配置 |
| **扩展性** | 模块化架构+热插拔 | 按需扩展，不影响核心运行 |
| **数据管理** | 分片数据库+智能路由 | 数据隔离，性能优化，故障隔离 |

---

## 2. 设计哲学与灵感来源

### 2.1 「AI学区」愿景

MTSCOS AI 源于一个简单而大胆的问题：**如果我们不仅仅自动化一个任务，而是自动化整个教育生态系统，会怎样？**

我们没有构建孤立的AI工具，而是设想了一个 **自治的AI学区** — 每个角色（教师、辅导员、批改员、监考员、安全官、IT管理员……）都由专业的AI员工担任，他们无缝协作，就像一个真实的团队。

### 2.2 核心设计原则

| 原则 | 描述 | 体现位置 |
| :--- | :--- | :--- |
| **AI优先（AI-First）** | 所有核心业务逻辑均由AI引擎驱动 | AI员工阵列、智能题目生成、自适应学习 |
| **模块化架构** | 每个功能模块独立封装，模块间通过API和事件总线通信 | ai_engines/、app/api/、蓝图模块 |
| **分布式思维** | 数据库按业务域划分，AI引擎支持集群部署 | split_databases/、集群管理系统 |
| **自我进化** | AI自动发现学习方向，自动生成学习规则，持续优化系统性能 | AI自我学习系统v2.0、自动修复机制 |
| **安全内置（Security by Design）** | 权限控制嵌入架构底层，敏感数据加密存储，漏洞自动扫描修复 | VIKEY驱动、AI防火墙、WAF规则 |
| **人机协同（Human-in-the-Loop）** | AI员工处理重复性工作，人类专注于创造性教学和决策 | 教师工作台、家长端、管理员仪表盘 |
| **零配置体验** | 开箱即用，智能默认值，复杂性按需暴露 | 一键启动、自动数据库初始化、默认演示账号 |

### 2.3 MTS架构的故事

MTS架构源于对成功教育机构运作方式的观察：

```text
┌─────────────────────────────────────────────────────────────────┐
│                    MTS架构设计灵感来源                          │
├─────────────────────────────────────────────────────────────────┤
│  现实教育机构                      MTS架构对应组件              │
│  ───────────                      ────────────────              │
│  校长                             规划引擎 (Plan Engine)       │
│  → 理解意图、分配资源、战略决策    → 意图识别、任务分解、路由决策│
│                                                                  │
│  教师/员工团队                     执行AI员工阵列 (Worker Agents)│
│  → 一人一岗、专业分工              → 550+位AI员工、技能可进化    │
│                                                                  │
│  学校基础设施                      基础设施层 (Fabric)          │
│  → 教室、图书馆、通信系统          → 分片数据库、消息队列、缓存  │
└─────────────────────────────────────────────────────────────────┘
```

### 2.4 双轨并行设计

MTS中的"双轨"指的是两条并行流：

```text
学习轨（Learning Track）:
  命题生成 → 智能组卷 → 批改评分 → 薄弱诊断 → 学习路径

运维轨（Ops Track）:
  安全防护 → 系统维护 → 实时监控 → 版本升级 → 故障恢复
```

### 2.5 未来方向

我们正在构建 **角色孪生AI学区**，让每位师生都拥有自己的AI孪生体：

| 阶段 | 目标 | 状态 |
| :--- | :--- | :--- |
| v17.22 | 超管UX统一版 | ✅ 已发布 |
| v17.23 | 题目扩展v3（多模态题目、反大模型水印、手写体OCR批改） | 🚧 设计中 |
| v17.24 | 角色孪生AI学区（AI孪生体、孪生体互委托图谱、本地LLM GPU卸载） | 🚧 设计中 |
| v18.0 | MTS架构v3（流式事件总线、热加载Agent、多地域分片、Rust防火墙侧车） | 🔭 规划中 |

---

## 3. 系统架构

### 3.1 目录结构

```text
MTSCOS-AI-Project/
├── server_real_db.py               # ✅ 生产入口（识别MTS架构+启动分片库）
├── server_preview.py               # 🧪 预览入口
├── app.py                          # 历史兼容入口
├── modular_start.py                # 模块化启动脚本
├── startup_modules/                # 模块化启动器
│   ├── db_config_loader.py         # 数据库配置加载器（8阶段）
│   ├── core_init.py                # 核心初始化（4步骤）
│   └── module_loader.py            # 功能模块加载器（6阶段）
├── ai_engines/                     # AI引擎模块（550+员工/引擎、47 Agent）
│   ├── ai_cluster_manager.py       # AI集群管理
│   ├── ai_employee_manager.py      # AI员工管理
│   ├── ai_question_bank.py         # 题库生成引擎
│   ├── adaptive_learning_engine.py # 自适应学习引擎
│   ├── knowledge_graph_engine.py   # 知识图谱引擎
│   ├── reward_achievement_engine.py# 奖励成就引擎
│   ├── wrong_book_engine.py        # 错题本智能引擎
│   ├── learning_prediction_engine.py # 学习预测分析引擎
│   ├── ai_tutor_engine.py          # AI助教答疑引擎
│   ├── collaborative_learning_engine.py # 协作学习引擎
│   ├── teaching_evaluation_engine.py # 智能教学评估引擎
│   ├── resource_recommendation_engine.py # 学习资源推荐引擎
│   ├── learning_report_engine.py  # 学情分析报告引擎
│   ├── homework_grading_engine.py  # 智能作业批改引擎
│   ├── home_school_communication_engine.py # 家校沟通引擎
│   ├── gamification_engine.py      # 学习游戏化引擎
│   ├── intelligent_warning_engine.py # 智能预警引擎
│   ├── ai_question_authoring_engine.py # AI辅助出题引擎
│   ├── learning_visualization_engine.py # 学习数据可视化引擎
│   ├── learning_diagnosis_engine.py # 智能学习诊断引擎
│   ├── knowledge_base_engine.py    # 智能知识库引擎
│   └── classroom_interaction_engine.py # AI课堂互动引擎
├── app/                            # 应用模块
│   ├── api/                        # API接口（120+个）
│   ├── ai/                         # AI子模块
│   ├── blueprints/                 # 蓝图模块
│   ├── services/                   # 服务模块
│   │   ├── cluster_service.py      # 集群管理服务
│   │   └── port_monitor_service.py # 端口监控服务
│   ├── models/                     # 数据模型
│   │   ├── permission.py           # 权限模型
│   │   └── role.py                 # 角色模型
│   ├── middlewares/                # 中间件
│   ├── routes/                     # 路由模块
│   ├── containers/                 # 容器模块
│   │   └── user_container.py       # 用户容器
│   └── utils/                      # 工具模块
│       └── permission_manager.py   # 权限管理器
├── split_databases/                # 分布式数据库（9+ SQLite分片，87张表）
├── templates/                      # HTML模板（100+个）
├── static/                         # 静态资源
├── scripts/                        # 脚本工具
│   └── expand_question_bank.py     # 题库拓展脚本
└── docs/                           # 文档目录
```

---

## 4. 模块化启动系统

### 4.1 启动流程（5大阶段）

#### 阶段1: 数据库配置加载（8个子阶段）

| 子阶段 | 配置项数 | 数据源 |
|--------|---------|--------|
| base | 12+ | system.db, admin.db |
| security | 11+ | auth.db, system.db |
| feature | 10+ | exam/question/learning等库 |
| advanced | 12+ | system.db, admin.db |
| ai | 12+ | ai.db, system.db |
| database | 12+ | system.db, admin.db |
| cache | 11+ | system.db, admin.db |
| api | 11+ | api_management.db |

#### 阶段2: 核心初始化（4步骤）
1. 创建Flask应用（模板、静态目录配置）
2. 注册Jinja2模板全局函数
3. 配置CORS跨域
4. 初始化数据库连接

#### 阶段3: 功能模块加载（6阶段）
1. 认证与基础路由（同步加载）
2. API接口模块（后台线程加载，120+个）
3. 蓝图模块（后台线程加载）
4. 服务模块（同步加载）
5. AI引擎模块（后台线程加载）
6. 中间件模块（同步加载）

#### 阶段4: 系统管理API注册
#### 阶段5: 启动Web服务器

### 4.2 启动命令

```bash
# 生产入口（推荐）
python3 server_real_db.py --host 0.0.0.0 --port 8888

# 调试模式
python3 server_preview.py --port 8888 --debug

# 指定主机
python3 server_real_db.py --host 0.0.0.0 --port 9000

# SSL模式
python3 server_real_db.py --ssl --ssl-port 8443
```

---

## 5. 分布式数据库

### 5.1 数据库列表（9+ SQLite分片，87张表，0空表）

| 数据库 | 用途 |
|--------|------|
| auth.db | 认证和用户管理（users/roles/permissions/sessions/2FA/VIKEY绑定） |
| exam.db | 考试管理（exams/exam_questions/exam_results/proctor events） |
| question.db | 题库管理（question_bank/ai_generated/tags/blooms/difficulty） |
| user.db | 用户信息（profiles/parent-student links/groups/avatar） |
| system.db | 系统配置（configs/system_versions/subsystem_versions/feature-flags） |
| admin.db | 管理后台（admin_ops/change-audit/super-admin audit log） |
| ai.db | AI引擎数据（ai_employees/clusters/llm model-pool/ai_results/brain_map） |
| learning.db | 学习系统（learning_records/knowledge_points/study_paths/wrong-book） |
| log.db | 日志系统（system_logs/audit_logs/error_logs/slow_query） |
| proctor.db | 监考系统（proctoring events / learning analytics ext.） |
| math.db / physics.db / other.db | 学科域扩展（预留） |

### 5.2 智能数据库路由
通过 `smart_db_router_simple.py` 实现 SQL 查询自动路由到正确的分布式数据库分片，业务层无感知。

---

## 6. AI智能引擎矩阵

### 6.1 核心引擎列表（20+）

| 引擎名称 | API前缀 | 功能描述 |
|---------|--------|---------|
| 题目生成引擎 | /api/question | AI自动生成题目 |
| 自适应学习引擎 | /api/adaptive | 个性化学习路径 |
| 知识图谱引擎 | /api/knowledge_graph | 知识关联分析 |
| 奖励成就引擎 | /api/reward | 积分与成就系统 |
| 错题本智能引擎 | /api/wrong_book | 艾宾浩斯遗忘曲线复习 |
| 学习预测分析引擎 | /api/prediction | 成绩预测与风险评估 |
| AI助教答疑引擎 | /api/tutor | 智能答疑系统 |
| 协作学习引擎 | /api/collaboration | 学习小组与知识分享 |
| 智能教学评估引擎 | /api/teaching_evaluation | 教师评估体系 |
| 学习资源推荐引擎 | /api/resource_recommendation | 个性化资源推荐 |
| 学情分析报告引擎 | /api/learning_report | 多维度学习报告 |
| 智能作业批改引擎 | /api/homework | 自动批改系统 |
| 家校沟通引擎 | /api/home_school | 三方沟通平台 |
| 学习游戏化引擎 | /api/game | 游戏化学习 |
| 智能预警引擎 | /api/warning | 风险预警系统 |
| AI辅助出题引擎 | /api/question_authoring | 批量出题系统 |
| 学习数据可视化引擎 | /api/visualization | 图表与仪表盘 |
| 智能学习诊断引擎 | /api/learning_diagnosis | 学习诊断与提升 |
| 智能知识库引擎 | /api/knowledge_base | 知识存储与检索 |
| AI课堂互动引擎 | /api/classroom_interaction | 课堂活动管理 |

### 6.2 AI员工（550+）
- 题目生成员工、考试分析员工、消息管理员工、奖励系统员工
- 练习学习员工、日语听力音频生成专家AI、AutomationPlanAgent
- 配置管理AI员工、端口监控AI员工、Git管理AI员工等

### 6.3 AI Agent（47个）
- 系统监控Agent、数据备份Agent、智能调度器、版本管理Agent
- Git同步Agent、自愈Agent、API管理Agent、数据库Agent等

---

## 7. 题库系统

### 7.1 科目覆盖

#### 成人教育科目（9个）
- 成人高考语文、成人高考数学、成人高考英语
- 成人高考政治、成人高考物理、成人高考化学
- 成人高考历史、成人高考地理、成人高考医学综合

#### K12科目（28个）
- 小学：语文、数学、英语、科学（4个）
- 初中：语文、数学、英语、物理、化学、生物、历史、地理、道德与法治（9个）
- 高中：语文、数学、英语、物理、化学、生物、历史、地理、政治（9个）
- 通用：语文、数学、英语、物理、化学、生物、历史、地理、政治、科学、日语（11个）

### 7.2 题型支持
- 单选题、多选题、判断题、填空题、简答题、论述题、听力题

### 7.3 题库规模
- 每个科目生成1000道题目
- 总计：37个科目 × 1000题 = 37,000+ 题目

### 7.4 难度分级
- 简单（easy）、中等（medium）、困难（hard）

---

## 8. 权限管理体系

### 8.1 角色体系（16个角色）

| 角色 | 中文名 | 权限级别 | 说明 |
|------|--------|---------|------|
| guest | 访客 | 0 | 无登录权限 |
| student | 学生 | 1 | 考试、学习、查看成绩 |
| parent | 家长 | 2 | 查看子女学习情况 |
| designer | 设计师 | 3 | 前端设计与模板管理 |
| teacher | 教师 | 4 | 课程管理、成绩管理 |
| exam_proctor | 监考员 | 5 | 考试监考与监控 |
| question_manager | 题库管理员 | 6 | 题库管理与维护 |
| ai_manager | AI管理员 | 7 | AI引擎配置与管理 |
| cluster_manager | 集群管理员 | 8 | 集群节点管理 |
| admin | 管理员 | 9 | 系统管理（只读） |
| super_admin | 超级管理员 | 9 | 超管UX，需VIKEY硬件密钥 |
| hardware_admin | 硬件管理员 | 14 | 最高权限，需加密狗认证 |

### 8.2 权限矩阵
每个角色拥有独立的权限列表，涵盖：
- 用户管理：view_profile, manage_account, change_password
- 考试系统：view_exams, take_exam, view_results, manage_exams
- 学习系统：view_learning_records, use_ai_chat, view_notifications
- 管理功能：view_dashboard, manage_users, manage_settings, manage_routes
- AI系统：manage_ai_employees, manage_ai_models, view_ai_stats
- 集群管理：manage_cluster, view_cluster_stats, manage_nodes
- 端口管理：manage_ports, view_port_stats, allocate_port

### 8.3 权限装饰器
- `@require_login` - 需要登录
- `@require_admin` - 需要管理员权限
- `@require_super_admin` - 需要超级管理员权限
- `@require_role(role)` - 需要指定角色权限

---

## 9. AI集群与模型库

### 9.1 AI模型配置（15个模型）

| 模型ID | 模型名称 | 类型 | 提供商 | 版本 |
|--------|---------|------|--------|------|
| gpt-4 | GPT-4 | llm | openai | 4.0 |
| gpt-4o | GPT-4o | llm | openai | 1.0 |
| claude-3-sonnet | Claude-3 Sonnet | llm | anthropic | 3.0 |
| claude-3-opus | Claude-3 Opus | llm | anthropic | 3.0 |
| qwen-7b | Qwen-7B | llm | alibaba | 1.0 |
| qwen-14b | Qwen-14B | llm | alibaba | 1.0 |
| llama-3-8b | Llama-3 8B | llm | meta | 3.0 |
| llama-3-70b | Llama-3 70B | llm | meta | 3.0 |
| gemini-pro | Gemini Pro | llm | google | 1.0 |
| gemini-1-5-pro | Gemini 1.5 Pro | llm | google | 1.5 |
| mistral-7b | Mistral-7B | llm | mistral | 1.0 |
| phi-3-mini | Phi-3 Mini | llm | microsoft | 3.0 |
| deepseek-chat | DeepSeek Chat | llm | deepseek | 1.0 |
| baichuan-7b | Baichuan-7B | llm | baichuan | 1.0 |
| zephyr-7b | Zephyr-7B | llm | huggingface | 1.0 |

### 9.2 模型性能指标
每个模型记录：
- 延迟（latency）：响应时间（秒）
- 吞吐量（throughput）：每秒处理请求数
- 准确率（accuracy）：回答准确率百分比

### 9.3 集群管理功能
- 节点动态扩展
- 负载均衡策略
- 健康检查与自动故障转移
- 模型版本管理
- 性能监控与日志

---

## 10. 安全架构

### 10.1 认证层
- **VIKEY硬件密钥**：USB驱动 → 挑战/响应 → 会话Token绑定
- **6位挑战码**：超管登录强制二次验证
- **Session Cookie + CSRF Token**：生产环境必须前端TLS

### 10.2 防护层（WAF 10条规则）

| 规则 | 防护内容 |
|------|---------|
| SQLi | SQL注入攻击 |
| XSS | 跨站脚本攻击 |
| RCE | 远程代码执行 |
| SSRF | 服务端请求伪造 |
| LFI | 本地文件包含 |
| 目录穿越 | 路径遍历攻击 |
| 扫描检测 | 自动化扫描工具识别 |
| 暴力破解 | 登录尝试限流 |
| 接口限流 | API调用频率限制 |
| 异常请求 | 异常参数/格式检测 |

### 10.3 CI安全扫描矩阵
- **pip-audit**：Python依赖安全审计
- **Trivy FS**：文件系统漏洞扫描
- **Bandit**：Python代码安全扫描
- **CodeQL**：GitHub代码安全分析
- **Dependabot**：pip日更 + Actions周更

### 10.4 审计层
- **操作日志**：所有管理操作记录
- **登录日志**：登录时间、IP、设备信息
- **数据变更日志**：数据增删改全链路追踪
- **不可篡改**：审计日志追加写入，禁止修改删除

### 10.5 AI防火墙服务
- 服务文件：`core/services/ai_firewall.py`
- API文件：`app/api/ai_firewall_api.py`
- 功能：实时安全扫描、威胁检测、自动防护

---

## 11. 自维护运维OS

### 11.1 8维自动修复

| 修复维度 | 修复内容 | 触发条件 |
|---------|---------|---------|
| 表结构修复 | 缺失表/字段自动创建 | 数据库连接异常 |
| 配置校正 | 配置参数验证与修正 | 配置文件变更 |
| 缓存清理 | 过期缓存自动清理 | 缓存命中率下降 |
| 连接池重建 | 数据库连接池重建 | 连接超时/断开 |
| 版本回滚 | 自动回滚到稳定版本 | 版本升级失败 |
| 数据恢复 | 基于备份的数据恢复 | 数据损坏 |
| 索引重建 | 数据库索引重建 | 查询性能下降 |
| ACL校准 | 权限规则重新计算 | 角色/权限变更 |

### 11.2 预防式诊断（8维健康检查）
- CPU使用率监控
- 内存使用率监控
- 磁盘空间监控
- 网络延迟监控
- 慢查询检测
- 索引建议
- 服务可用性检查
- 安全状态扫描

### 11.3 自动化任务系统
- **代码巡检员**：自动扫描代码异常和Bug
- **漏洞扫描员**：定期扫描系统安全漏洞
- **日志监控员**：实时监控错误日志和异常

### 11.4 异常退出处理机制
- 任务状态追踪（pending/running/completed/failed）
- 异常退出自动重试（最多3次）
- 失败任务自动上报
- 退出原因记录与分析

---

## 12. 端口管理系统

### 12.1 端口配置（21个端口）

| 端口 | 服务名称 | 状态 | 说明 |
|------|---------|------|------|
| 8888 | MTSCOS HTTP服务 | running | 主应用HTTP端口 |
| 8443 | MTSCOS HTTPS服务 | running | 主应用HTTPS端口 |
| 5000 | Flask开发服务 | running | 开发环境端口 |
| 5001 | API服务 | running | API服务端口 |
| 5002 | WebSocket服务 | running | 实时通信端口 |
| 3306 | MySQL数据库 | optional | MySQL数据库端口 |
| 27017 | MongoDB | optional | MongoDB数据库端口 |
| 6379 | Redis缓存 | running | Redis缓存端口 |
| 6380 | Redis哨兵 | optional | Redis哨兵端口 |
| 80 | 标准HTTP | optional | 标准HTTP端口 |
| 443 | 标准HTTPS | optional | 标准HTTPS端口 |
| 22 | SSH服务 | running | SSH远程连接端口 |
| 25 | SMTP服务 | optional | 邮件服务端口 |
| 587 | SMTP TLS | optional | 邮件加密端口 |
| 9200 | Elasticsearch | optional | 搜索服务端口 |
| 9092 | Kafka | optional | 消息队列端口 |
| 8080 | 管理控制台 | running | 管理控制台端口 |
| 8081 | 监控服务 | running | 监控服务端口 |
| 8082 | 日志服务 | running | 日志服务端口 |
| 8083 | 定时任务 | running | 定时任务服务端口 |

### 12.2 端口管理功能
- **端口扫描**：扫描指定范围端口状态
- **端口分配**：自动分配可用端口
- **端口预留**：为特定服务预留端口
- **端口释放**：释放不再使用的端口
- **使用统计**：端口使用情况统计
- **参数匹配**：配置参数验证与匹配
- **自动修复**：端口异常自动修复

### 12.3 API接口

| 接口 | 方法 | 说明 |
|------|------|------|
| /api/ports/status | GET | 获取所有端口状态 |
| /api/ports/stats | GET | 获取端口统计 |
| /api/ports/scan | POST | 扫描端口范围 |
| /api/ports/allocate | POST | 分配可用端口 |
| /api/ports/reserve | POST | 预留端口 |
| /api/ports/release | POST | 释放端口 |
| /api/ports/fix | POST | 修复端口问题 |

---

## 13. 集群管理系统

### 13.1 节点管理
- 节点注册与注销
- 节点状态监控（ACTIVE/HEALTHY/UNHEALTHY/DOWN/MAINTENANCE）
- 节点角色管理（MASTER/SLAVE/STANDBY）
- 节点权重配置

### 13.2 负载均衡策略（4种）

| 策略 | 说明 | 适用场景 |
|------|------|---------|
| ROUND_ROBIN | 轮询 | 节点性能相近 |
| LEAST_CONNECTIONS | 最小连接数 | 节点性能差异大 |
| WEIGHTED_ROUND_ROBIN | 加权轮询 | 需要按权重分配 |
| IP_HASH | IP哈希 | 需要会话保持 |

### 13.3 健康检查
- 心跳超时检测（30秒）
- HTTP健康检查（/health端点）
- 自动故障转移
- 主节点自动提升

### 13.4 数据复制
- 主从数据复制
- 实时同步机制

### 13.5 API接口

| 接口 | 方法 | 说明 |
|------|------|------|
| /api/cluster/nodes | GET | 获取节点列表 |
| /api/cluster/nodes | POST | 添加节点 |
| /api/cluster/nodes/<id> | DELETE | 删除节点 |
| /api/cluster/stats | GET | 获取集群统计 |
| /api/cluster/strategy | GET | 获取负载均衡策略 |
| /api/cluster/strategy | POST | 设置负载均衡策略 |
| /api/cluster/master | GET | 获取主节点 |
| /api/cluster/promote | POST | 提升节点为主节点 |

---

## 14. Git自动同步

### 14.1 自动同步功能
- 变更检测
- 自动提交（带审批机制）
- 自动推送
- 定时同步（每5分钟）

### 14.2 安全机制
- 保护分支禁止强制推送（main/master/develop）
- 大规模提交需审批（50+文件变更）
- 操作记录审计
- 差异对比保存

### 14.3 API接口

| 接口 | 方法 | 说明 |
|------|------|------|
| /api/git/status | GET | Git状态 |
| /api/git/commit | POST | 提交更改 |
| /api/git/push | POST | 推送到远程 |
| /api/git/pull | POST | 从远程拉取 |
| /api/git/sync | POST | 同步并备份 |
| /api/git/history | GET | 获取操作历史 |

---

## 15. 前端页面系统

### 15.1 模板系统
- 100+ HTML模板文件
- Jinja2模板引擎
- 全局模板函数（角色名称、日期格式化等）

### 15.2 布局优化
- 左侧固定标签栏（260px）+ 右侧Tab切换内容区
- 响应式设计，支持移动端适配
- 渐变进度条、统计卡片、实时日志

### 15.3 主要页面

| 页面 | 路由 | 说明 |
|------|------|------|
| 超级管理员仪表盘 | /super_admin_dashboard | 10个标签页，系统监控与管理 |
| 普通管理员仪表盘 | /admin_dashboard | 独立界面，只读权限 |
| AI自动完善拓展 | /ai_auto_expand | AI拓展管理页面 |
| 学生门户 | /student_portal | 学生统一入口 |
| 考试系统 | /exam_system | 考试列表与管理 |
| 测试系统 | /exam_system/tests | 日常练习与测试 |

---

## 16. 移动端适配

### 16.1 响应式布局
- 媒体查询适配不同屏幕尺寸
- 触控友好的按钮尺寸
- 滑动手势支持
- 移动端专属导航

### 16.2 移动端优化
- 页面宽度自适应
- 组件缩放适配
- 加载性能优化
- 离线缓存支持

### 16.3 手机管理端
- 独立路由：/admin_app
- 移动端专属界面设计
- 简化的操作流程
- 触控优化的交互

---

## 17. AI智能题目生成器

### 17.1 功能概述
AI智能题目生成器是一个基于文本内容自动生成考试题目的智能系统。用户输入任意文本内容，系统会自动分析文本、提取关键点，并生成多种题型的考试题目。

### 17.2 核心特性
- **文本分析**：自动检测文本科目（语文、数学、英语、物理、化学、生物、历史、地理、政治、科学、日语）
- **关键点提取**：从文本中提取关键信息作为题目基础
- **6种题型生成**：单选题、多选题、判断题、填空题、简答题、论述题
- **难度控制**：简单/中等/困难三级难度
- **自动保存**：支持将生成的题目保存到题库数据库

### 17.3 技术实现
- 服务文件：`app/services/ai_question_generation_service.py`
- API文件：`app/api/ai_generation_api.py`
- 前端页面：`templates/admin_app/ai_question_generator.html`
- 页面路由：`/admin/ai-question-generator`

### 17.4 API接口

| 接口 | 方法 | 说明 |
|------|------|------|
| /api/ai/generate-questions | POST | 从文本生成题目 |
| /api/ai/generate-questions/save | POST | 保存生成的题目 |
| /api/ai/generate-questions/stats | GET | 获取生成统计 |
| /api/ai/generate-questions/subjects | GET | 获取科目列表 |
| /api/ai/generate-questions/types | GET | 获取题型列表 |
| /api/ai/detect-subject | POST | 自动检测科目 |
| /api/ai/extract-key-points | POST | 提取关键点 |

### 17.5 使用示例

```json
POST /api/ai/generate-questions
{
    "text": "物理学是研究物质最一般的运动规律和物质基本结构的学科...",
    "count": 10,
    "types": ["单选题", "多选题", "判断题"],
    "difficulty": "medium",
    "subject": "物理"
}
```

---

## 18. AI智能学习路径推荐

### 18.1 功能概述
AI智能学习路径推荐系统分析学生学习数据，识别薄弱环节，生成个性化学习路径，帮助学生高效提升学习成绩。

### 18.2 核心特性
- **薄弱环节分析**：基于错题数据分析各知识点错误率，分级标记（紧急加强/重点复习/巩固练习/日常练习）
- **学习路径生成**：根据薄弱环节自动生成1-30天的个性化学习路径
- **知识图谱**：9个科目完整知识体系，每个科目5个主题，共45个主题
- **学习进度追踪**：按科目统计学习进度

### 18.3 技术实现
- 服务文件：`app/services/ai_study_path_service.py`
- API文件：`app/api/study_path_api.py`
- 前端页面：`templates/admin_app/ai_study_path.html`
- 页面路由：`/admin/ai-study-path`

### 18.4 API接口

| 接口 | 方法 | 说明 |
|------|------|------|
| /api/ai/study-path/generate | POST | 生成学习路径 |
| /api/ai/study-path/analyze | POST | 分析薄弱环节 |
| /api/ai/study-path/subjects | GET | 获取科目列表 |
| /api/ai/study-path/knowledge-graph | GET | 获取知识图谱 |
| /api/ai/study-path/progress | POST | 获取学习进度 |

### 18.5 使用示例

```json
POST /api/ai/study-path/generate
{
    "user_id": 1,
    "subject": "数学",
    "days": 7
}
```

---

## 19. AI试卷自动组卷系统

### 19.1 功能概述
AI试卷自动组卷系统根据科目、难度、题型自动从题库中选择题目组卷，确保知识覆盖率均衡，自动计算分数分布和考试时长，生成高质量试卷。

### 19.2 核心特性
- **智能组卷算法**：基于难度比例、题型比例自动选题，确保试卷质量
- **知识覆盖率分析**：分析试卷对各知识点的覆盖程度
- **质量评分系统**：综合难度和题型分布计算试卷质量分数
- **自动分数分配**：根据题型自动分配分数，确保总分符合要求
- **考试时长计算**：根据科目和题目数量自动计算考试时长
- **试卷预览与保存**：支持预览试卷摘要，一键保存到数据库

### 19.3 技术实现
- 服务文件：`app/services/ai_exam_composition_service.py`
- API文件：`app/api/exam_composition_api.py`
- 前端页面：`templates/admin_app/ai_exam_composer.html`
- 页面路由：`/admin/ai-exam-composer`

### 19.4 API接口

| 接口 | 方法 | 说明 |
|------|------|------|
| /api/ai/exam-compose | POST | 自动组卷 |
| /api/ai/exam-compose/preview | POST | 预览试卷 |
| /api/ai/exam-compose/save | POST | 保存试卷 |
| /api/ai/exam-compose/statistics | GET | 获取组卷统计 |
| /api/ai/exam-compose/subjects | GET | 获取科目列表 |
| /api/ai/exam-compose/types | GET | 获取题型列表 |

### 19.5 使用示例

```json
POST /api/ai/exam-compose
{
    "subject": "数学",
    "total_questions": 50,
    "types": ["单选题", "多选题", "判断题", "填空题", "简答题", "论述题"],
    "difficulty_ratio": {"easy": 0.3, "medium": 0.5, "hard": 0.2},
    "total_score": 100,
    "exam_name": "高三数学模拟试卷"
}
```

---

## 20. 学生成绩分析仪表盘

### 20.1 功能概述
学生成绩分析仪表盘提供多维度的学生学习数据可视化分析，包括成绩分布、学习时间趋势、薄弱知识点分析等，帮助教师和管理员全面了解学生学习状况。

### 20.2 核心特性
- **实时统计面板**：学生总数、平均分、及格率、不及格率、学习时长
- **数据可视化图表**：成绩分布直方图、各科平均分雷达图、学习时间趋势图、错题率分析饼图
- **成绩排名表**：Top 10学生排名，显示进步幅度
- **薄弱知识点分析**：按错误率排序，显示掌握程度进度条
- **筛选功能**：支持按科目、班级、时间范围筛选数据

### 20.3 技术实现
- 前端页面：`templates/admin_app/student_analytics.html`
- 页面路由：`/admin/student-analytics`
- 图表库：Chart.js

### 20.4 图表类型

| 图表名称 | 类型 | 用途 |
|---------|------|------|
| 成绩分布直方图 | Bar | 展示各分数段人数分布 |
| 各科平均分对比 | Radar | 展示各科成绩对比 |
| 学习时间趋势 | Line | 展示一周学习时间变化 |
| 错题率分析 | Doughnut | 展示各掌握程度占比 |

---

## 21. 项目思维导图

完整的项目思维导图请参见独立文档：[docs/MIND_MAP.md](MIND_MAP.md)

### 思维导图概览

```mindmap
## **MTSCOS AI**
### **核心愿景**
- 自治AI学区运营团队
- 自动化整个教育生态系统
- 人机协同，让教师专注创造性工作
### **MTS架构v2.0**
- 规划引擎（意图识别、任务分解、ACL校验、路由决策）
- 执行AI员工阵列（550+专业AI员工/引擎、47 Agent、技能可进化、任务可委托）
- 基础设施层（分片SQLite、内存发布订阅、多级缓存）
### **AI员工体系**
- 教学领域：教师AI、命题专家、作业批改员、AI辅导老师
- 运维领域：Git管家、DevOps Agent、代码修复员、日志监控员
- 安全领域：安全审计员、漏洞扫描员、AI防火墙
- 数据领域：数据分析员、脑库管理员、知识图谱工程师
### **核心功能矩阵**
- 题库与考试：统一题库、动态题目引擎、AI智能组卷、智能监考
- 学习与辅导：自适应学习路径、薄弱诊断、智能错题本、学情分析
- 管理门户：10角色权限管理、超管UX、VIKEY硬件密钥登录
- 安全与治理：RBAC+ABAC、企业级WAF、不可变审计日志
### **安全架构**
- 认证层：VIKEY硬件密钥、6位挑战码、Session+CSRF
- 防护层：SQLi/XSS/RCE/SSRF/LFI防护、暴力破解限流
- 审计层：操作日志、登录日志、数据变更日志
### **自维护能力**
- 8维自动修复：表结构/配置/缓存/连接池/回滚/数据恢复/索引/ACL
- 预防式诊断：8维健康检查、性能监控、异常检测、自动上报
```

---

## 22. 版本历史

| 版本 | 代号 | 日期 | 主要特性 |
|------|------|------|---------|
| v17.22.0 | SuperAdmin UX Unified Edition | 2026-07-26 | 超管UX统一、VIKEY全链路打通、主版本+20子系统统一对齐、CI接入Dependabot+Trivy+Bandit、9+ SQLite分片（87张表）、550+ AI员工/引擎、47 Agent |
| v7.2.0 | Comprehensive Enhancement Edition | 2026-07-09 | 题库拓展(37K题)、权限矩阵(12角色)、AI集群(15模型)、端口管理(21端口)、集群管理(4种策略)、AI题目生成器、AI学习路径推荐、AI试卷自动组卷、学生成绩分析仪表盘 |
| v7.1.0 | Dashboard Refactor Edition | 2026-07-08 | 仪表盘重构、AI拓展系统、629路由、41AI员工 |
| v7.0.0 | Intelligent Modular Edition | 2026-07-07 | 模块化启动、AI智能检索、API/路由数据库管理 |
| v6.0.0 | Distributed Database Edition | 2026-07-06 | 分布式数据库架构（13个独立数据库） |
| v5.0.0 | AI Integration Edition | 2026-06-01 | AI集成版本，AI助教引擎 |
| v4.0.0 | Exam System Edition | 2026-05-01 | 在线考试和监考功能 |
| v3.0.0 | Learning Edition | 2026-04-01 | 学习管理系统 |
| v2.0.0 | Admin Edition | 2026-03-01 | 权限和用户管理 |
| v1.0.0 | Initial Edition | 2026-02-01 | 初始版本 |

---

## 23. API接口文档

### 23.1 系统管理API

| 接口 | 方法 | 说明 |
|------|------|------|
| /api/system/status | GET | 获取系统完整状态 |
| /api/system/configs | GET | 获取系统配置 |
| /api/system/configs/reload | POST | 重新加载配置 |
| /api/system/modules | GET | 获取模块加载状态 |

### 23.2 认证API

| 接口 | 方法 | 说明 |
|------|------|------|
| /api/auth/login | POST | 用户登录 |
| /api/auth/register | POST | 用户注册 |
| /api/auth/logout | GET/POST | 用户登出 |
| /api/auth/check | GET | 检查登录状态 |

### 23.3 AI员工API

| 接口 | 方法 | 说明 |
|------|------|------|
| /api/ai_employees/status | GET | AI员工状态 |
| /api/ai_employees/list | GET | AI员工列表 |
| /api/ai_employees/register | POST | 注册AI员工 |
| /api/ai_employees/auto_extend | POST | AI自动拓展 |

### 23.4 路由管理API

| 接口 | 方法 | 说明 |
|------|------|------|
| /api/routes/list | GET | 获取路由列表 |
| /api/routes/reload | POST | 重新加载路由 |
| /api/routes/check | GET | 检查路由状态 |

### 23.5 版本管理API

| 接口 | 方法 | 说明 |
|------|------|------|
| /api/version/status | GET | 版本状态 |
| /api/version/check | GET | 版本检查 |
| /api/version/upgrade | POST | 版本升级 |

### 23.6 监控API

| 接口 | 方法 | 说明 |
|------|------|------|
| /api/monitoring/stats | GET | 系统监控统计 |
| /api/monitoring/errors | GET | 错误统计 |
| /api/monitoring/logs | GET | 监控日志 |

---

## 24. 部署指南

### 24.1 环境要求
- Python 3.9+
- SQLite 3.30+
- pip 20.0+
- Git
- 推荐：Redis 7.0+（可选，系统支持内存缓存降级）

### 24.2 安装步骤

```bash
# 克隆仓库
git clone https://github.com/wuchenghao15/MTSCOS-AI-Project.git
cd MTSCOS-AI-Project

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 启动服务（生产入口，推荐）
python3 server_real_db.py --host 0.0.0.0 --port 8888
```

### 24.3 配置说明
- 配置文件：`app/config/config.py`
- 数据库路径：`split_databases/`
- 静态资源：`static/`
- 模板文件：`templates/`

### 24.4 安全建议
- 生产环境启用HTTPS
- 设置管理员密码（非默认值）
- 定期备份数据库
- 监控系统日志

---

*文档结束 - MTSCOS AI 智能考试系统 v17.22.0*
