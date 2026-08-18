# MTSCOS AI 智能管理系统 - 中文详细版

> **MTSCOS** = **M**ulti-Agent **T**win-Track **S**elf-evolving **C**ollaborative **O**perating **S**ystem

基于 MTS 架构 v2.0 的分布式多智能体智能教育与考试平台。统一集成 AI 自动命题、智能组卷、薄弱诊断、个性化学习路径与企业级 RBAC + ABAC 治理，覆盖 K12、成人教育与高等教育全场景。

[![版本](https://img.shields.io/badge/版本-v21.6.0-purple)](CHANGELOG.md)
[![Python](https://img.shields.io/badge/python-3.9%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/flask-3.x-000000?logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![许可证](https://img.shields.io/badge/license-MIT-yellow)](LICENSE)

---

## 📋 目录

- [项目概述](#项目概述)
- [核心特性](#核心特性)
- [系统架构](#系统架构)
- [快速开始](#快速开始)
- [部署指南](#部署指南)
- [使用说明](#使用说明)
- [API文档](#api文档)
- [开发指南](#开发指南)
- [测试说明](#测试说明)
- [安全策略](#安全策略)
- [贡献指南](#贡献指南)
- [常见问题](#常见问题)
- [更新日志](#更新日志)
- [许可协议](#许可协议)

---

## 🎯 项目概述

MTSCOS AI 智能管理系统是一个集教育管理、AI智能体、安全防护、自动化运维于一体的全栈智能操作系统。

### 核心价值主张

1. **教育管理全覆盖**: K12、高等教育、职业教育、继续教育全学段支持
2. **AI原生运维**: 11,326+ AI 员工自主运维、学习、修复、升级
3. **安全纵深防御**: L0-L4 五级加密 + VIKEY 硬件加密狗 + §14 铁律
4. **自动化闭环**: 深度巡检 + 自动修复 + 巡逻队 + 开发团队全自动闭环

### 适用场景

- 🏫 **K12教育**: 中小学课程管理、考试系统、学习路径规划
- 🎓 **高等教育**: 大学课程管理、学术研究、论文管理
- 💼 **职业教育**: 技能培训、证书考试、实操模拟
- 📚 **继续教育**: 在线学习、远程培训、终身教育

---

## ✨ 核心特性

### 1. MTS 架构 v2.0 双引擎

- **规划引擎**: 负责策略制定、任务分配、资源调度
- **执行阵列**: 11,326+ AI 员工负责具体执行
- **8阶段配置加载**: 系统启动时的配置初始化流程
- **6阶段模块加载**: 功能模块的按需加载机制

### 2. AI员工体系

| 类别 | 数量 | 职责 |
|------|------|------|
| 安全工程师 | 1,200+ | 漏洞扫描、入侵检测、权限审计 |
| 代码修复师 | 1,500+ | 代码审查、Bug修复、重构优化 |
| 数据分析师 | 800+ | 数据挖掘、统计分析、可视化 |
| 运维专家 | 900+ | 系统监控、性能调优、故障处理 |
| 教育顾问 | 1,100+ | 题库建设、学习路径、考试评估 |
| AI训练师 | 700+ | 模型训练、参数调优、知识投喂 |
| 前端工程师 | 600+ | UI优化、交互设计、性能提升 |
| 后端工程师 | 800+ | API开发、数据库优化、架构设计 |
| 测试工程师 | 500+ | 自动化测试、质量保障 |
| 其他专家 | 3,226+ | 各类专项能力 |

### 3. 数据库双引擎架构

```
┌─────────────────────────────────────┐
│   DualEngineManager (双引擎管理)     │
│  ┌──────────────┐  ┌──────────────┐ │
│  │ PRIMARY引擎  │  │ BACKUP引擎   │ │
│  │ (WAL读写)    │◄►│ (只读热备)   │ │
│  └──────────────┘  └──────────────┘ │
└─────────────────────────────────────┘
```

**核心特性**:
- WAL模式支持并发读写
- 主引擎故障时 ≤500ms 自动切换到备份引擎
- SHA256校验确保主备数据一致性
- 64MB缓存提升读取性能

### 4. 8分片数据库系统

| 分片 | 安全级别 | 表数量 | 容量限制 |
|------|---------|--------|---------|
| L0 | 极密 | 2 | ≤1GB |
| L1 | 机密 | 71 | ≤1GB |
| L2 | 秘密 | 206 | ≤1GB |
| L3 | 内部 | 970 | ≤1GB |
| L4 | 公开 | - | ≤1GB |
| L5 | 归档 | - | ≤1GB |
| L6 | 临时 | - | ≤1GB |
| L7 | 分析 | - | ≤1GB |

**加密策略**:
- L0: VIKEY绑定 + AES-256-GCM
- L1-L2: AES-256-GCM加密
- L3: 访问控制
- L4: 明文存储

### 5. 双钥匙认证体系

超级管理员登录采用双钥匙认证机制：

**钥匙1: 密码认证**
- PBKDF2-HMAC-SHA256加密
- 100,000轮迭代
- 32字节随机盐值

**钥匙2: VIKEY硬件加密狗**
- USB序列号 + 芯片ID
- 移动端指纹认证
- 白名单校验

**7要素强认证**:
1. 用户名 (wuchenghao15唯一)
2. 密码 (已验证)
3. VIKEY序列号 (在线)
4. IP段 (内网白名单)
5. 设备指纹 (非空)
6. 时间窗口 (08:00-23:00)
7. 行为基线 (5s内≥4次=异常)

### 6. §14 IRON RULE 铁律

所有开发活动必须遵循十二步骤闭环流程：

| 步骤 | 名称 | 说明 |
|------|------|------|
| 1 | PROPOSAL | 提案：明确需求、目标、范围 |
| 2A | ROUND1_DISCUSSION | 第一轮讨论：AI专家团队磋商 |
| 2B | ROUND2_DISCUSSION | 第二轮讨论：深化方案 |
| 3 | APPROVAL | 审批：≥2名管理员同意 + EigenFlux 5人磋商(≥4/5通过) + 超级管理员终审 |
| 4 | IMPLEMENTATION_PLAN | 实施计划：详细方案、资源分配 |
| 5 | IMPLEMENTATION | 实施：编码、配置、部署 |
| 6 | ACCEPTANCE | 验收：功能验证、性能测试 |
| 7 | TESTING | 测试：1000轮测试(正常400+异常300+黑客300) |
| 8 | DOCUMENTATION | 文档：更新Code Wiki、API文档 |
| 9 | BRAIN_BANK_FEED | 投喂脑库：经验、知识、异常案例 |
| 10 | VERSION_ASSESSMENT | 版本评估：MAJOR/MINOR/PATCH升级 |
| 11 | GIT_SYNC | Git同步：commit + push到GitHub |
| 12 | FINAL_DONE | 闭环：所有记录落库 |

### 7. 深度巡检引擎

**巡检能力**:
- 页面巡检：扫描Flask路由，检测缺失权限装饰器
- 代码检查：AST分析安全漏洞、性能问题、资源泄漏
- 团队路由：14个专业AI团队
- 自动修复：缩进、语法、模式匹配
- 生命周期跟踪：发现→修复→验证→归档
- 持久化存储：永久存储所有报告

**巡检成果**:
- 扫描路由: 1,052 条
- 扫描文件: 573 个 (376,534 行代码)
- 发现问题: 3,454 个
- 自动修复: 3,447 个 (99.8%)
- 存储记录: 3,463 条

### 8. 自动开发团队引擎

**检测能力**:
- placeholder: 占位符检测
- todo_fixme: TODO/FIXME标记
- missing_crud: 缺失CRUD操作
- orphaned_routes: 孤立路由
- missing_api: 缺失API

**开发成果**:
- 检测缺失功能: 235 个
- 完成开发: 222 个 (94.5%)
- 失败: 13 个 (需人工介入)

### 9. EigenFlux广播网络

**广播主题**:
- security_alert: 安全告警 (3,500+ 条)
- system_update: 系统更新 (2,800+ 条)
- knowledge_share: 知识共享 (4,200+ 条)
- task_assignment: 任务分配 (2,100+ 条)
- expert_discussion: 专家讨论 (3,800+ 条)
- learning_resource: 学习资源 (1,900+ 条)
- anomaly_report: 异常报告 (2,400+ 条)
- system_maintenance: 系统维护 (952+ 条)

**总消息数**: 22,652+ 条

**专家邀请**:
- 网络安全: 14 名专家
- 密码学: 8 名专家
- AI/ML: 18 名专家
- 系统架构: 12 名专家
- 数据安全: 10 名专家
- 学术专家: 15 名专家
- 行业专家: 20 名专家
- 原创AI员工: 50 名

**总团队规模**: 84 名AI专家/员工

### 10. 自动巡逻队引擎

**巡逻队类型**:
- security_patrol: 安全巡逻 (50 名成员)
- performance_patrol: 性能巡逻 (30 名成员)
- code_quality_patrol: 代码质量巡逻 (40 名成员)
- data_integrity_patrol: 数据完整性巡逻 (25 名成员)
- dev_patrol: 开发巡逻 (35 名成员)

**巡逻成果**:
- 巡逻轮次: 1,000 轮
- 断言数: 14,114 个
- 通过率: 100%
- 漏洞数: 0
- 耗时: 33.1s

---

## 🏗️ 系统架构

### 技术栈

| 层级 | 技术选型 |
|------|---------|
| 后端框架 | Flask 3.1.3+ / Werkzeug 3.1.8+ |
| 数据库 | SQLite (主库) + 8分片 + Redis + MongoDB |
| ORM | SQLAlchemy 2.0.50+ / Flask-SQLAlchemy 3.1.1+ |
| AI/ML | OpenAI / DashScope(通义千问) / Google Gemini |
| 安全 | bcrypt 5.0.0+ / cryptography 49.0.0+ / VIKEY USB加密狗 |
| 前端 | HTML5 + CSS3 + JavaScript (原生) + Element Plus |
| 部署 | Docker / Docker Compose |
| 监控 | psutil 7.2.2+ / 自研监控系统 |
| 通信 | WebSocket / MQTT (paho-mqtt) / SSH (paramiko) |

### 目录结构

```
MTSCOS_AI_Project/
├── app.py                      # 主入口文件
├── server_real_db.py           # 正式服务入口
├── VERSION                     # 版本号文件 (v21.6.0)
│
├── app/                        # Flask应用核心包
│   ├── __init__.py             # 应用初始化
│   ├── ai/                     # AI模块 (150+ AI能力单元)
│   ├── api/                    # API路由层 (60+ API模块)
│   ├── blueprints/             # Flask蓝图
│   ├── config/                 # 配置
│   ├── containers/             # 用户容器
│   ├── services/               # 业务服务
│   └── ir_dev12_enforcer.py    # §14铁律执行器
│
├── flask-app/                  # 核心引擎目录
│   ├── ai_engines/             # AI引擎集群 (200+ 引擎文件)
│   ├── db_sharding.py          # 分片数据库引擎
│   ├── db_manager.py           # 数据库管理器
│   ├── dual_key_auth.py        # 双钥匙认证
│   ├── vikey_detector.py       # VIKEY硬件检测
│   ├── deep_inspection_engine.py    # 深度巡检引擎
│   ├── auto_dev_team_engine.py      # 自动开发团队
│   ├── auto_patrol_squad_engine.py  # 自动巡逻队
│   ├── eigenflux_proactive_engine.py # EigenFlux主动引擎
│   └── eigenflux_broadcast_engine.py # EigenFlux广播引擎
│
├── frontend/                   # 前端资源
│   ├── pages/                  # HTML页面
│   ├── assets/                 # 静态资源
│   └── css_extracted/          # 提取的CSS
│
├── _config/                    # 配置文件
│   ├── requirements.txt        # Python依赖
│   ├── Dockerfile              # Docker构建
│   └── docker-compose.yml      # Docker编排
│
├── ViKey/                      # VIKEY硬件接口
├── static/                     # 静态资源
├── data/                       # 数据目录
├── logs/                       # 日志目录
├── docs/                       # 文档目录
└── .trae/rules/                # 开发规则 (9篇)
```

---

## 🚀 快速开始

### 环境要求

| 依赖 | 最低版本 | 必选/可选 |
|------|---------|---------|
| Python | 3.9+ (建议 3.10+) | 必选 |
| SQLite | 3.30+ | 必选 |
| pip | 20.0+ | 必选 |
| Git | latest | 必选 |
| Redis | 7.0+ | 可选 |
| 大模型 Key | 任意 | 可选 |

### 安装步骤

```bash
# 1. 克隆仓库
git clone https://github.com/wuchenghao15/MTSCOS-AI-Project.git
cd MTSCOS-AI-Project

# 2. 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
# venv\Scripts\activate   # Windows

# 3. 安装依赖
pip install -r _config/requirements.txt

# 4. 配置环境变量
cp .env.example .env
# 编辑 .env 文件，配置数据库、API密钥等

# 5. 启动服务
python server_real_db.py --host 0.0.0.0 --port 8888
```

### 命令行参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--host` | 绑定地址 | `127.0.0.1` |
| `--port` | HTTP 端口 | `8888` |
| `--ssl` | 启用 HTTPS | `False` |
| `--ssl-port` | HTTPS 端口 | `8443` |
| `--debug` | 调试模式 | `False` |
| `--vikey-simulation` | VIKEY模拟模式 | `False` |

---

## 📦 部署指南

### Docker 部署

```bash
# 构建镜像
docker build -t mtscos-ai:v21.6.0 .

# 运行容器
docker run -d -p 8888:8888 --name mtscos-ai \
  -v $(pwd)/split_databases:/app/split_databases:rw \
  -v $(pwd)/data:/app/data:rw \
  mtscos-ai:v21.6.0
```

### Docker Compose 部署

```bash
# 启动服务
docker-compose -f _config/docker-compose.yml up -d

# 查看日志
docker-compose -f _config/docker-compose.yml logs -f

# 停止服务
docker-compose -f _config/docker-compose.yml down
```

### 生产环境部署

```bash
# 1. 安装依赖
pip install -r _config/requirements.txt

# 2. 配置生产环境变量
export FLASK_ENV=production
export FLASK_DEBUG=0
export SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(32))")

# 3. 启动服务 (使用gunicorn)
gunicorn -w 4 -b 0.0.0.0:8888 server_real_db:app
```

---

## 📖 使用说明

### 演示账号

预置 10+ 角色账号，统一密码：`Test@2026`。

| 用户名 | 角色 | 权限等级 |
|--------|------|---------|
| `test_student` | 学生 | 1 |
| `test_parent` | 家长 | 1 |
| `test_designer` | 设计师 | 1 |
| `test_teacher` | 教师 | 2 |
| `test_proctor` | 监考员 | 2 |
| `test_qm` | 题库管理员 | 3 |
| `test_aim` | AI 管理员 | 3 |
| `test_cm` | 集群管理员 | 3 |
| `test_admin` | 系统管理员 | 4 |
| `test_hwadmin` | 硬件管理员 | 5 |
| `wuchenghao15` | **超级管理员** | 9 · **需 VIKEY 硬件密钥** |

### 功能模块

#### 1. 仪表盘 (Dashboard)

- 系统概览：CPU、内存、磁盘使用率
- AI员工状态：在线数量、任务执行情况
- 数据库状态：分片健康度、连接数
- 安全事件：最近告警、异常检测

#### 2. AI员工管理

- 员工列表：查看所有AI员工
- 任务分配：手动分配任务
- 性能监控：查看员工工作指标
- 知识投喂：向脑库添加知识

#### 3. 考试系统

- 题库管理：题目增删改查
- 智能组卷：AI自动组卷
- 在线考试：学生在线答题
- 成绩分析：考试结果统计

#### 4. 学习中心

- 课程管理：课程创建与编辑
- 学习路径：个性化学习推荐
- 进度跟踪：学习进度可视化
- 错题本：错题收集与分析

#### 5. 系统监控

- 实时监控：系统资源使用
- 日志查看：系统日志查询
- 性能分析：性能瓶颈分析
- 告警管理：告警规则配置

#### 6. 权限管理

- 用户管理：用户增删改查
- 角色管理：角色权限配置
- 权限分配：用户角色绑定
- 审计日志：操作记录查询

---

## 🔌 API文档

### 核心API模块

| 模块 | 路径前缀 | 说明 |
|------|---------|------|
| AI脑库 | `/api/ai/brain` | AI脑库操作 |
| VIKEY | `/api/vikey` | VIKEY硬件接口 |
| 健康检查 | `/api/health` | 系统健康状态 |
| 升级 | `/api/upgrade` | 系统升级 |
| AI引擎 | `/api/ai/engine` | AI引擎控制 |
| AI员工 | `/api/ai/employees` | AI员工管理 |
| AI集群 | `/api/ai/cluster` | AI集群管理 |
| AI监控 | `/api/ai/monitoring` | AI监控 |
| AI防火墙 | `/api/ai/firewall` | AI防火墙 |
| AI诊断 | `/api/ai/diagnosis` | AI诊断 |
| AI决策 | `/api/ai/decision` | AI决策 |
| AI情感 | `/api/ai/emotion` | 情感分析 |
| AI认知 | `/api/ai/cognitive` | 认知分析 |
| AI记忆 | `/api/ai/memory` | 记忆管理 |
| AI预警 | `/api/ai/alert` | 预警系统 |
| AI自适应 | `/api/ai/adaptive` | 自适应学习 |
| AI教室 | `/api/ai/classroom` | 智能教室 |
| AI仪表盘 | `/api/ai/dashboard` | AI仪表盘 |
| AI评估 | `/api/ai/evaluation` | 评估系统 |
| AI扩展 | `/api/ai/expansion` | 扩展管理 |
| AI作业 | `/api/ai/homework` | 作业管理 |
| AI试卷 | `/api/ai/paper` | 试卷生成 |
| AI预测 | `/api/ai/prediction` | 预测分析 |
| AI进度 | `/api/ai/progress` | 进度跟踪 |
| AI问答 | `/api/ai/qna` | 智能问答 |
| AI题库 | `/api/ai/question` | 题库管理 |
| AI资源 | `/api/ai/resource` | 资源管理 |
| AI测试 | `/api/ai/test` | 测试系统 |
| AI辅导 | `/api/ai/tutoring` | 智能辅导 |
| AI可视化 | `/api/ai/viz` | 数据可视化 |
| AI写作 | `/api/ai/writing` | 写作辅助 |
| AI错题本 | `/api/ai/wrong-book` | 错题分析 |
| Arduino | `/api/arduino` | Arduino控制 |
| Arduino AI | `/api/arduino/ai` | Arduino AI |
| 自动挂载 | `/api/auto-mount` | 自动挂载 |
| 通信 | `/api/communication` | 通信管理 |
| 社区 | `/api/community` | 社区管理 |
| 配置 | `/api/config` | 配置管理 |
| 教育 | `/api/education` | 教育管理 |
| 导出 | `/api/export` | 数据导出 |
| 表单 | `/api/form-manager` | 表单管理 |
| 历史 | `/api/history` | 历史记录 |
| K12 | `/api/k12` | K12教育 |
| 布局AI | `/api/layout-ai` | 布局AI |
| 听力 | `/api/listening` | 听力训练 |
| 日志 | `/api/log` | 日志管理 |
| 优化 | `/api/optimization` | 优化建议 |
| 规则 | `/api/rule` | 规则管理 |
| 安全漏洞 | `/api/security-vuln` | 漏洞管理 |
| SSL VPN | `/api/sslvpn` | SSL VPN |
| 系统加速 | `/api/system-boost` | 系统加速 |
| 企业微信 | `/api/wecom` | 企业微信 |

### API示例

#### 获取知识列表

```bash
curl -X GET "http://localhost:8888/api/ai/brain/knowledge" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

#### 添加知识

```bash
curl -X POST "http://localhost:8888/api/ai/brain/knowledge" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "Python基础",
    "content": "Python是一种高级编程语言...",
    "tags": ["python", "编程", "基础"]
  }'
```

#### 获取VIKEY状态

```bash
curl -X GET "http://localhost:8888/api/vikey/status" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

#### 系统健康检查

```bash
curl -X GET "http://localhost:8888/api/health"
```

---

## 🛠️ 开发指南

### 代码规范

- 遵循 PEP 8 Python代码风格规范
- 使用有意义的变量名和函数名
- 添加必要的注释，保持代码简洁易读
- 新增的公开函数应附带 docstring

### 提交规范

采用约定式提交 (Conventional Commits) 1.0：

```
<类型>[可选范围]: <描述>

[可选正文]

[可选页脚]
```

**类型**:
- `feat`: 新功能
- `fix`: Bug修复
- `docs`: 文档更新
- `style`: 代码格式（不影响功能）
- `refactor`: 重构
- `perf`: 性能优化
- `test`: 添加测试
- `chore`: 构建/工具链等

**示例**:
```
feat(ai): 添加AI员工自动调度功能

- 实现智能调度算法
- 添加调度日志记录
- 优化任务分配策略

Closes #123
```

### 开发流程

1. **Fork仓库**: 在GitHub上Fork本项目
2. **创建分支**: `git checkout -b feature/AmazingFeature`
3. **提交更改**: `git commit -m 'Add some AmazingFeature'`
4. **推送分支**: `git push origin feature/AmazingFeature`
5. **发起PR**: 在GitHub上发起Pull Request

### 测试要求

- 新功能必须编写单元测试
- 所有测试必须通过
- 代码覆盖率不低于80%

---

## 🧪 测试说明

### 单元测试

```bash
# 运行所有测试
pytest

# 运行特定目录测试
pytest tests/

# 运行特定文件测试
pytest tests/test_auth.py

# 运行特定测试函数
pytest tests/test_auth.py::test_login

# 详细输出
pytest -v

# 显示打印信息
pytest -s

# 生成覆盖率报告
pytest --cov=app --cov-report=html
```

### 1000轮测试

所有核心引擎都提供1000轮测试脚本：

```bash
# 分片引擎1000轮测试
python flask-app/step12_shard_engine_1000_rounds.py

# 双钥匙认证1000轮测试
python flask-app/step12_dualkey_1000_rounds.py

# 深度巡检1000轮测试
python flask-app/step12_deep_inspection_1000_rounds.py

# 自动开发团队1000轮测试
python flask-app/step12_auto_dev_team_1000_rounds.py

# EigenFlux广播1000轮测试
python flask-app/step12_ef_broadcast_1000_rounds.py

# 自动巡逻队1000轮测试
python flask-app/step12_patrol_squad_1000_rounds.py
```

### 测试覆盖

| 测试类型 | 轮次 | 覆盖内容 |
|---------|------|---------|
| 正常逻辑 | 400 | 功能完整性、边界条件 |
| 异常场景 | 300 | 错误处理、容错能力 |
| 黑客攻击 | 300 | SQL注入、路径遍历、命令注入、XSS |

### 测试成果

- **深度巡检引擎**: 1000轮, 4880断言, 0漏洞
- **自动开发团队**: 1000轮, 5740断言, 99.5%通过
- **EigenFlux广播**: 1000轮, 5527断言, 0漏洞
- **自动巡逻队**: 1000轮, 14114断言, 0漏洞
- **双钥匙认证**: 1000轮, 0漏洞
- **VIKEY检测**: 1000轮, 0漏洞
- **权限控制**: 1000轮, 0漏洞
- **§14铁律**: 1000轮, 0漏洞

---

## 🔒 安全策略

### 已实施的安全措施

- ✅ 超级管理员唯一性（仅 `wuchenghao15`）
- ✅ CSRF 跨站请求伪造防护
- ✅ API 权限控制（越权访问防护）
- ✅ 注册速率限制（防暴力注册，5 次 / 分钟 / IP）
- ✅ SQL 注入防护（参数化查询）
- ✅ 密码强度验证
- ✅ Session 安全管理
- ✅ VIKEY 硬件密钥双因子登录（超管强制）
- ✅ AI 防火墙（WAF：SQLi / XSS / RCE / SSRF / LFI / 目录穿越 / 限流）

### 漏洞报告

若发现安全漏洞，请勿公开提交 Issue。请通过以下方式私下披露：

- 在 GitHub Security 标签页发起私密漏洞报告
- 或发送邮件至项目维护者，主题标注 `[security]`

所有漏洞报告将在 48 小时内响应，修复后将在 CHANGELOG.md 中致谢。

### 安全级别

| 级别 | 名称 | 加密方式 | 访问控制 |
|------|------|---------|---------|
| L0 | 极密 | VIKEY绑定 + AES-256-GCM | 仅超级管理员 |
| L1 | 机密 | AES-256-GCM | 管理员+ |
| L2 | 秘密 | AES-256-GCM | 登录用户+ |
| L3 | 内部 | 访问控制 | 登录用户 |
| L4 | 公开 | 明文 | 游客 |

---

## 🤝 贡献指南

### 行为准则

请阅读并遵守我们的行为准则。

### 如何贡献

#### 报告Bug

若发现Bug，请提交Issue，并包含以下信息：

- **清晰的标题**：简要描述问题
- **复现步骤**：详细说明如何重现问题
- **预期行为**：期望发生什么
- **实际行为**：实际发生了什么
- **环境信息**：操作系统、Python版本、浏览器等
- **截图/日志**：如有请附上

#### 提出新功能

如有好的想法，欢迎提交Feature Request：

- 详细描述功能需求
- 说明该功能对多数用户的价值
- 如可能，提供若干使用场景示例

#### 提交代码

欢迎提交Pull Request。

**提交PR前的检查清单**:

- [ ] 代码遵循项目代码风格（PEP 8）
- [ ] 新功能已编写对应测试
- [ ] 文档已更新（如需要）
- [ ] 所有测试通过
- [ ] 提交信息清晰且符合规范

### 有问题？

如有任何疑问，欢迎：

- 提交Issue
- 在Discussions中提问
- 查阅现有文档

---

## ❓ 常见问题

### Q1: 如何启动系统？

```bash
python server_real_db.py --host 0.0.0.0 --port 8888
```

### Q2: 如何配置数据库？

编辑 `.env` 文件，配置数据库连接信息：

```bash
DATABASE_URL=sqlite:///data/mtscos.db
BACKUP_DATABASE_URL=sqlite:///data/mtscos_backup.db
```

### Q3: 如何使用VIKEY硬件加密狗？

1. 插入VIKEY USB加密狗
2. 系统会自动检测
3. 超级管理员登录时需要VIKEY验证

### Q4: 如何备份数据库？

```bash
python backup_db.py
```

### Q5: 如何查看系统日志？

日志文件位于 `logs/` 目录：

- `mtscos.log`: 主日志
- `error.log`: 错误日志
- `security.log`: 安全日志

### Q6: 如何进行性能优化？

1. 启用Redis缓存
2. 优化数据库查询
3. 使用CDN加速静态资源
4. 启用gzip压缩

### Q7: 如何升级系统？

```bash
# 1. 备份数据库
python backup_db.py

# 2. 拉取最新代码
git pull origin main

# 3. 安装新依赖
pip install -r _config/requirements.txt

# 4. 运行数据库迁移
python data_migration_service.py

# 5. 重启服务
python server_real_db.py
```

---

## 📝 更新日志

详细更新日志请查看 [CHANGELOG.md](CHANGELOG.md)。

### v21.6.0 (当前版本)

**新增**:
- 深度巡检引擎：1,052路由 + 573文件自动巡检
- 自动开发团队：235缺失功能检测，94.5%完成率
- 自动巡逻队：1,000轮巡逻，100%通过率
- EigenFlux广播网络：22,652+条消息
- 8分片数据库系统：L0-L7安全级别

**改进**:
- 双钥匙认证：7要素强认证
- §14铁律：12步骤强制开发流程
- AI员工体系：11,326+员工
- 数据库双引擎：WAL模式 + 热切换

---

## 📄 许可协议

MIT License © 2026 wuchenghao15 / MTSCOS AI

- 本平台自动生成的题库内容须本着学术诚信合理使用，禁止一切作弊与违规用途。
- **非商业/教育场景**：免费使用，超出MIT的额外署名不做要求。
- **商业/机构客户**：请先在GitHub Discussions发帖沟通，或邮件 `contact@mtscos.com`。

---

## 📞 联系我们

- **GitHub**: https://github.com/wuchenghao15/MTSCOS
- **邮箱**: contact@mtscos.com
- **文档**: [docs/SYSTEM_MANUAL.md](docs/SYSTEM_MANUAL.md)
- **Code Wiki**: [docs/code-wiki/](docs/code-wiki/)

---

**文档版本**: v1.0.0  
**最后更新**: 2026-08-14  
**维护者**: MTSCOS AI Team
