# MTSCOS AI 智能考试系统

[![Python Version](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/downloads/)
[![Flask Version](https://img.shields.io/badge/flask-2.0%2B-green.svg)](https://flask.palletsprojects.com/)
[![License](https://img.shields.io/badge/license-MIT-yellow.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-v7.7.0-orange.svg)](CHANGELOG.md)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

> 版本: v7.7.0 (AI-Powered Comprehensive Enhancement Suite)
> 更新日期: 2026-07-11

[English](README_EN.md) | 中文

MTSCOS AI 是一个基于 Flask 框架开发的分布式智能考试管理平台，提供完整的题库系统、考试管理、学习分析、AI智能引擎等功能，支持成人教育和K12全科目。

---

## 📋 目录

- [🌟 核心特性](#-核心特性)
- [📁 项目结构](#-项目结构)
- [🚀 快速开始](#-快速开始)
- [📡 API接口](#-api接口)
- [📊 数据库架构](#-数据库架构)
- [🌐 管理后台页面](#-管理后台页面)
- [📈 功能使用流程](#-功能使用流程)
- [🧪 测试账号](#-测试账号)
- [🤝 贡献指南](#-贡献指南)
- [📄 许可证](#-许可证)
- [📞 联系方式](#-联系方式)

---

## 🌟 核心特性

### 🏗️ 架构特性
- **模块化启动系统**：8阶段配置加载 + 6阶段功能模块加载
- **分布式数据库架构**：20+ 独立数据库，智能路由
- **AI智能引擎矩阵**：41+ AI员工，6+ AI Agent，590+ 检索模型
- **响应式前端布局**：支持桌面端和移动端，适配手机客户端

### 📚 题库系统
- **37,000+ 题目**：覆盖成人教育和K12全科目（语文、数学、英语、物理、化学、生物、历史、地理、政治、科学、日语）
- **7种题型**：单选题、多选题、判断题、填空题、简答题、论述题、听力题
- **智能出题**：基于知识点/难度/题型批量出题
- **AI题目生成器**：从文本内容自动生成考试题目

### 🔐 权限管理
- **16+ 角色**：guest→student→parent→designer→teacher→exam_proctor→question_manager→ai_manager→cluster_manager→admin→super_admin→hardware_admin
- **细粒度权限**：50+权限规则覆盖，6级访问控制
- **审计日志**：完整操作记录、实时审计
- **权限矩阵**：支持自定义权限规则配置

### 🤖 AI集群与模型库
- **15+ AI模型**：GPT-4、Claude-3、Qwen、Llama-3、Gemini、DeepSeek等
- **性能监控**：延迟、吞吐量、准确率指标
- **动态扩展**：节点自动扩展、负载均衡
- **多模型配置**：支持模型切换和版本管理

### ✨ AI智能功能
- **AI题目生成器**：从文本内容自动生成考试题目，支持6种题型、11个科目、3级难度，自动保存到题库
- **AI学习路径推荐**：分析学生错题数据，生成个性化学习路径，包含薄弱分析和知识图谱
- **AI试卷自动组卷**：根据科目、难度、题型智能组卷，自动计算分数分布和考试时长，知识覆盖率分析，质量评分
- **AI智能答疑**：学生在线提问，AI自动解答，支持多科目、多题型，会话管理，知识库搜索
- **智能错题本**：自动收集错题，艾宾浩斯遗忘曲线复习，薄弱知识点分析，掌握程度追踪
- **学生成绩分析仪表盘**：多维度数据可视化分析，成绩分布直方图、各科平均分雷达图、学习时间趋势图、错题率分析
- **智能学习助手**：个性化学习推荐、智能作业辅导、学习效果分析

### 🔐 安全防护
- **企业级防火墙**：10+安全规则（SQL注入/XSS/命令注入/SSRF/文件包含/路径遍历/敏感文件/暴力破解/扫描器防护/API限流）
- **AI安全建议**：智能分析安全漏洞，生成优化建议和实施步骤

### 🚀 自我维护能力
- **自动修复引擎**：8种修复能力（表结构修复/配置校正/缓存清理/连接池重建/配置回滚/数据恢复/索引重建/权限修复）
- **预防式维护**：8项维护内容，预测准确率100%
- **系统健康诊断**：8项核心检查（数据库/API响应/内存/CPU/磁盘/网络/缓存/错误日志）

### 🌐 端口与集群管理
- **21个端口配置**：HTTP/HTTPS、API、WebSocket、数据库等
- **端口管理**：扫描、分配、预留、释放、自动修复
- **负载均衡**：轮询、最小连接数、加权轮询、IP哈希
- **健康检查**：心跳检测、自动故障转移、节点状态监控

### 📊 系统监控
- **实时监控**：CPU、内存、磁盘、网络
- **慢查询检测**：自动识别和优化慢查询
- **性能分析**：索引建议、查询统计
- **性能监控API**：提供系统状态和性能指标接口

### 🚀 自动化运维
- **Git自动同步**：变更检测、自动提交、推送
- **每日健康检查**：数据库清理、日志清理、备份
- **自动升级**：版本检测、灰度发布、健康检查回滚
- **版本管理**：系统历史版本记录、自动更新说明文档

---

## 📁 项目结构

```
flask-app/
├── app.py                      # 应用入口
├── modular_start.py            # 模块化启动脚本
├── simple_start.py             # 简化启动脚本
├── VERSION                     # 版本文件
├── SYSTEM_DOC.md               # 系统说明书
├── requirements.txt            # Python依赖
├── ai_engines/                 # AI引擎模块 (20+核心引擎)
│   ├── ai_cluster_manager.py   # AI集群管理
│   ├── ai_employee_manager.py  # AI员工管理
│   ├── ai_question_bank.py     # 题库生成引擎
│   ├── adaptive_learning_engine.py    # 自适应学习引擎
│   ├── knowledge_graph_engine.py      # 知识图谱引擎
│   ├── reward_achievement_engine.py   # 奖励成就引擎
│   ├── wrong_book_engine.py           # 错题本智能引擎
│   ├── learning_prediction_engine.py  # 学习预测分析引擎
│   ├── ai_tutor_engine.py             # AI助教答疑引擎
│   └── ...
├── app/                        # 应用模块
│   ├── routes/                 # 路由模块 (API蓝图)
│   ├── services/               # 服务模块
│   │   ├── ai_question_generation_service.py   # AI题目生成服务
│   │   ├── ai_study_path_service.py           # AI学习路径服务
│   │   ├── ai_exam_composition_service.py     # AI试卷组卷服务
│   │   ├── ai_learning_assistant.py           # 智能学习助手服务
│   │   ├── db_performance_service.py          # 数据库性能服务
│   │   ├── cluster_service.py                 # 集群管理服务
│   │   └── port_monitor_service.py            # 端口监控服务
│   ├── models/                 # 数据模型 (20+个)
│   ├── exceptions/             # 自定义异常体系
│   ├── utils/                  # 工具模块
│   │   ├── redis_manager.py    # Redis管理器（支持内存缓存降级）
│   │   ├── db.py               # 数据库连接池管理
│   │   └── ...
│   ├── extensions.py           # 扩展初始化
│   └── __init__.py             # 应用初始化
├── split_databases/            # 分布式数据库 (20+个)
│   ├── auth.db                 # 认证和用户管理
│   ├── exam.db                 # 考试管理
│   ├── question.db             # 题库管理
│   ├── learning.db             # 学习系统
│   ├── system.db               # 系统配置
│   ├── ai.db                   # AI引擎数据
│   ├── api_management.db       # API管理
│   ├── routes_management.db    # 路由管理
│   └── ...
├── templates/                  # HTML模板 (100+个)
│   ├── admin_app/              # 管理后台页面
│   │   ├── ai_question_generator.html   # AI题目生成器
│   │   ├── ai_study_path.html           # AI学习路径推荐
│   │   ├── ai_exam_composer.html        # AI试卷组卷
│   │   ├── student_analytics.html       # 学生成绩分析仪表盘
│   │   └── ...
│   └── ...
├── src/html/assets/            # 设计系统资源
│   ├── css/                    # 样式文件
│   │   ├── mtscos-design-system.css    # 设计系统
│   │   └── ...
│   ├── js/                     # JavaScript文件
│   └── font-awesome/           # Font Awesome图标库
├── static/                     # Flask静态文件
├── scripts/                    # 脚本工具
├── tests/                      # 测试文件
├── migrations/                 # 数据库迁移脚本
└── startup_modules/            # 模块化启动器
    ├── db_config_loader.py     # 数据库配置加载器
    ├── core_init.py            # 核心初始化
    └── module_loader.py        # 功能模块加载器
```

---

## 🚀 快速开始

### 环境要求
- Python 3.9+
- SQLite 3.30+
- Redis 7.0+（可选，系统支持内存缓存降级）
- Git
- pip 20.0+

### 安装步骤

```bash
# 克隆仓库
git clone https://github.com/MTSCOS/MTSCOS_AI_Project.git
cd MTSCOS_AI_Project/flask-app

# 创建虚拟环境（推荐）
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 启动服务（简化启动）
python simple_start.py --port 8888

# 或使用模块化启动（完整功能）
# python modular_start.py --port 8888
```

### 启动参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| --port | 服务端口 | 8888 |
| --host | 绑定地址 | 0.0.0.0 |
| --debug | 调试模式 | False |
| --ssl | 启用SSL | False |
| --ssl-port | SSL端口 | 8443 |

### 访问地址
- 系统首页: http://localhost:8888/
- 登录页面: http://localhost:8888/login
- 管理后台: http://localhost:8888/admin_app/login
- 增强管理器仪表板: http://localhost:8888/enhancement

---

## 📡 API接口

### 认证接口
| 接口 | 方法 | 说明 |
|------|------|------|
| /api/auth/login | POST | 用户登录 |
| /api/auth/logout | POST | 用户登出 |
| /api/auth/check | GET | 检查登录状态 |

### 系统管理接口
| 接口 | 方法 | 说明 |
|------|------|------|
| /api/system/status | GET | 获取系统状态 |
| /api/system/configs | GET | 获取系统配置 |
| /api/system/modules | GET | 获取模块状态 |
| /api/system/version | GET | 获取系统版本 |

### AI题目生成接口
| 接口 | 方法 | 说明 |
|------|------|------|
| /api/ai/generate-questions | POST | 从文本生成题目 |
| /api/ai/generate-questions/save | POST | 保存生成的题目 |
| /api/ai/generate-questions/stats | GET | 获取生成统计 |
| /api/ai/detect-subject | POST | 自动检测科目 |
| /api/ai/extract-key-points | POST | 提取关键点 |

### AI学习路径接口
| 接口 | 方法 | 说明 |
|------|------|------|
| /api/ai/study-path/generate | POST | 生成学习路径 |
| /api/ai/study-path/analyze | POST | 分析薄弱环节 |
| /api/ai/study-path/knowledge-graph | GET | 获取知识图谱 |
| /api/ai/study-path/progress | POST | 获取学习进度 |

### AI学习助手接口
| 接口 | 方法 | 说明 |
|------|------|------|
| /api/learning_assistant/recommendations | GET | 获取学习推荐 |
| /api/learning_assistant/generate_recommendations | POST | 生成学习推荐 |
| /api/learning_assistant/homework/analyze | POST | 分析作业答案 |
| /api/learning_assistant/report | GET | 获取学习报告 |

### AI试卷组卷接口
| 接口 | 方法 | 说明 |
|------|------|------|
| /api/ai/exam-compose | POST | 自动组卷 |
| /api/ai/exam-compose/preview | POST | 预览试卷 |
| /api/ai/exam-compose/save | POST | 保存试卷 |
| /api/ai/exam-compose/statistics | GET | 获取组卷统计 |

### 增强管理器接口
| 接口 | 方法 | 说明 |
|------|------|------|
| /api/enhancement/status | GET | 增强管理器总览状态 |
| /api/enhancement/database/health | GET | 数据库健康检查 |
| /api/enhancement/cluster/monitor | GET | 集群状态监控 |
| /api/enhancement/system/resources | GET | 系统资源多维度监控 |
| /api/enhancement/git/sync | POST | Git一键同步 |

---

## 📊 数据库架构

### 主要数据库
| 数据库 | 用途 | 核心表 |
|--------|------|--------|
| auth.db | 认证和用户管理 | users, roles, permissions, sessions |
| exam.db | 考试管理 | exams, exam_questions, exam_results |
| question.db | 题库管理 | questions, ai_generated_questions |
| learning.db | 学习系统 | learning_records, study_paths, knowledge_points |
| system.db | 系统配置 | configs, versions, logs |
| ai.db | AI引擎数据 | ai_models, ai_clusters, ai_results |
| admin.db | 管理后台 | admin_users, admin_logs |
| log.db | 日志系统 | system_logs, audit_logs, error_logs |
| api_management.db | API管理 | api_endpoints, api_stats |
| routes_management.db | 路由管理 | routes, route_stats |

---

## 🌐 管理后台页面

| 页面路由 | 说明 | 权限要求 |
|---------|------|---------|
| /admin_app/login | 管理员登录 | 所有角色 |
| /admin/ai-question-generator | AI题目生成器 | admin/super_admin |
| /admin/ai-study-path | AI学习路径推荐 | admin/super_admin |
| /admin/ai-exam-composer | AI试卷组卷 | admin/super_admin |
| /admin/student-analytics | 学生成绩分析仪表盘 | admin/super_admin |
| /admin/question-bank | 题库管理 | question_manager |
| /admin/ai-cluster | AI集群管理 | ai_manager |
| /admin/cluster-management | 集群管理 | cluster_manager |
| /enhancement | 增强管理器仪表板 | admin/super_admin |

---

## 📈 功能使用流程

### AI题目生成流程
1. 输入文本内容 → 系统自动检测科目 → 提取关键点 → 生成题目 → 保存到题库

### AI学习路径推荐流程
1. 分析学生错题数据 → 识别薄弱环节 → 生成个性化学习路径 → 跟踪学习进度

### AI试卷组卷流程
1. 设置科目/题型/难度 → 智能选题 → 分析知识覆盖率 → 预览试卷 → 保存试卷

### 学生成绩分析流程
1. 选择科目/班级/时间范围 → 加载统计数据 → 可视化展示 → 导出分析报告

### 智能学习助手流程
1. 获取学习推荐 → 完成推荐学习 → 提交作业 → AI分析作业 → 生成学习报告

---

## 🧪 测试账号

系统已预置11个测试账号，供开发者和测试人员使用：

| 用户名 | 角色 | 权限等级 |
|--------|------|---------|
| `test_student` | 学生 | 1 |
| `test_parent` | 家长 | 1 |
| `test_designer` | 设计师 | 1 |
| `test_teacher` | 教师 | 2 |
| `test_proctor` | 监考员 | 2 |
| `test_qm` | 题库管理员 | 3 |
| `test_aim` | AI管理员 | 3 |
| `test_cm` | 集群管理员 | 3 |
| `test_admin` | 系统管理员 | 4 |
| `test_superadmin` | 超级管理员 | 5 |
| `test_hwadmin` | 硬件管理员 | 6 |

**统一密码**: `Test@2026`

详细使用指南请参考 [TEST_ACCOUNTS.md](docs/TEST_ACCOUNTS.md)

---

## 🤝 贡献指南

欢迎加入 MTSCOS AI 项目！无论是代码贡献、文档完善、Bug报告还是功能建议，我们都非常欢迎。

### 代码规范

项目遵循以下规范文档，所有贡献必须严格遵守：

- [设计规范](../.trae/rules/设计规范.md) - 统一UI设计标准和视觉风格
- [开发规则](../.trae/rules/开发规则.md) - 统一开发标准和代码规范

### 分支管理策略

| 分支 | 用途 |
|------|------|
| `main` | 主分支，生产环境代码 |
| `develop` | 开发分支，集成所有功能 |
| `feature/xxx` | 功能分支，开发新功能 |
| `bugfix/xxx` | Bug修复分支 |
| `hotfix/xxx` | 紧急修复分支 |

### 提交信息规范

```
<类型>(<范围>): <描述>

<详细说明>
```

| 类型 | 说明 |
|------|------|
| `feat` | 新功能 |
| `fix` | Bug修复 |
| `docs` | 文档更新 |
| `style` | 样式修改 |
| `refactor` | 代码重构 |
| `test` | 测试代码 |
| `chore` | 构建/工具更新 |

### 开发环境搭建

1. **克隆仓库**
```bash
git clone https://github.com/MTSCOS/MTSCOS_AI_Project.git
cd MTSCOS_AI_Project/flask-app
```

2. **安装依赖**
```bash
pip install -r requirements.txt
```

3. **启动开发服务器**
```bash
python simple_start.py --port 8888
```

4. **运行测试**
```bash
python -m pytest
```

### 提交PR流程

1. **Fork仓库** - 在GitHub上Fork本仓库到自己的账户
2. **创建分支** - 基于 `develop` 分支创建新分支
3. **开发功能** - 实现功能或修复Bug，遵循代码规范
4. **提交代码** - 使用规范的提交信息
5. **推送分支** - 推送到自己的Fork仓库
6. **创建PR** - 在GitHub上创建Pull Request到 `develop` 分支
7. **代码审查** - 等待项目维护者审查
8. **合并分支** - PR通过审查后合并到 `develop`

---

## 📄 许可证

MIT License

---

## 📞 联系方式

- 项目地址: https://github.com/MTSCOS/MTSCOS_AI_Project
- 系统文档: [SYSTEM_DOC.md](SYSTEM_DOC.md)
- 版本历史: [SYSTEM_VERSION_HISTORY.md](SYSTEM_VERSION_HISTORY.md)
- 测试账号: [TEST_ACCOUNTS.md](docs/TEST_ACCOUNTS.md)

---

**MTSCOS AI** - 让考试更智能，让学习更高效 🚀