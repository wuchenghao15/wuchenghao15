# MTSCOS AI 教育系统 - Code Wiki

## 文档信息
- **版本**: 4.3.0
- **更新日期**: 2026-06-04
- **项目路径**: `/MTSCOS_AI_Project`

---

## 目录

1. [项目概述](#1-项目概述)
2. [项目架构](#2-项目架构)
3. [核心模块 (core)](#3-核心模块-core)
4. [Flask应用 (flask-app)](#4-flask应用-flask-app)
5. [集群管理 (cluster)](#5-集群管理-cluster)
6. [前端模块](#6-前端模块)
7. [移动应用](#7-移动应用)
8. [依赖关系](#8-依赖关系)
9. [API文档](#9-api文档)
10. [数据模型](#10-数据模型)
11. [运行方式](#11-运行方式)

---

## 1. 项目概述

### 1.1 项目简介
MTSCOS AI 是一个完整的K12教育系统，提供题库管理、AI智能学习、考试系统、教师管理等功能。系统采用前后端分离架构，支持集群部署和水平扩展。

### 1.2 版本信息
```
当前版本: 4.3.0
构建日期: 2026-06-04
构建编号: 20260604002

组件版本:
- FRONTEND_VERSION: 2.4.0
- BACKEND_VERSION: 3.8.0
- DATABASE_VERSION: 3.8.0
- API_VERSION: 3.8.0
- AI_ENGINE_VERSION: 4.2.0
- LEARNING_PATH_VERSION: 2.2.0
- EXAM_SYSTEM_VERSION: 3.2.0
```

### 1.3 技术栈
| 层级 | 技术 |
|------|------|
| 后端 | Python 3.11, Flask 2.3.3 |
| 前端 | JavaScript, HTML5, CSS3 |
| 数据库 | SQLite (主), Redis (缓存) |
| 消息队列 | Celery |
| AI引擎 | OpenAI, Anthropic, Ollama |
| 移动端 | React Native (Expo) |
| 集群 | 自研集群管理器 |

---

## 2. 项目架构

### 2.1 整体架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                        MTSCOS AI 系统                           │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│  │   Web前端   │  │  移动端App  │  │   API客户端 │              │
│  │  (HTML/JS)  │  │   (Expo)   │  │             │              │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘              │
│         │                │                │                     │
│         └────────────────┼────────────────┘                     │
│                          ▼                                        │
│  ┌───────────────────────────────────────────────────────────┐   │
│  │                    Flask API 网关                         │   │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐          │   │
│  │  │Auth API │ │Exam API │ │ AI API  │ │Admin API│          │   │
│  │  └─────────┘ └─────────┘ └─────────┘ └─────────┘          │   │
│  └───────────────────────────────────────────────────────────┘   │
│                          │                                        │
│         ┌────────────────┼────────────────┐                     │
│         ▼                ▼                ▼                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐               │
│  │Core Modules │  │AI Engines  │  │  Cluster    │               │
│  │  (core/)   │  │ (ai_engines)│  │ (cluster/)  │               │
│  └─────────────┘  └─────────────┘  └─────────────┘               │
│                          │                                        │
│         ┌────────────────┼────────────────┐                     │
│         ▼                ▼                ▼                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐               │
│  │   SQLite    │  │    Redis    │  │  Celery     │               │
│  │  (主数据库)  │  │   (缓存)    │  │ (任务队列)   │               │
│  └─────────────┘  └─────────────┘  └─────────────┘               │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 目录结构

```
MTSCOS_AI_Project/
├── core/                      # 核心业务模块
│   ├── __init__.py
│   ├── __main__.py
│   ├── ai.py                  # AI服务
│   ├── application_management.py  # 申请管理
│   ├── cache.py                # 缓存管理
│   ├── config.py               # 配置管理
│   ├── database.py            # 数据库管理
│   ├── education.py            # 教育AI
│   ├── event_tracker.py        # 事件追踪
│   ├── exceptions.py           # 异常定义
│   ├── grade_management.py     # 年级管理
│   ├── intelligence.py         # 智能服务
│   ├── knowledge_graph.py       # 知识图谱
│   ├── logging.py              # 日志系统
│   ├── question_bank.py         # 题库管理
│   ├── queue.py                # 队列管理
│   ├── recommendation.py       # 推荐系统
│   ├── scheduler.py            # 任务调度
│   ├── session.py              # 会话管理
│   ├── settings.py             # 设置管理
│   ├── system.py               # 系统监控
│   ├── system_integrator.py     # 系统集成
│   ├── teacher_management.py    # 教师管理
│   └── utils.py                # 工具函数
│
├── flask-app/                  # Flask Web应用
│   ├── app.py                  # 应用入口
│   ├── app/
│   │   ├── api/                # API路由
│   │   │   ├── routes.py       # 基础路由
│   │   │   ├── auth_api.py     # 认证API
│   │   │   ├── config_api.py   # 配置API
│   │   │   ├── exam_api.py     # 考试API
│   │   │   ├── cluster_api.py  # 集群API
│   │   │   └── ...
│   │   ├── models/             # 数据模型
│   │   │   ├── user.py         # 用户模型
│   │   │   ├── question.py     # 题库模型
│   │   │   ├── exam_system.py  # 考试模型
│   │   │   └── ...
│   │   ├── views/              # 视图
│   │   ├── services/           # 业务服务
│   │   ├── utils/              # 工具函数
│   │   └── config/             # 配置
│   ├── ai_engines/             # AI引擎
│   │   ├── ai.py
│   │   ├── ai_brain.py
│   │   ├── ai_lab.py
│   │   └── ...
│   └── requirements.txt
│
├── cluster/                    # 集群管理
│   ├── cluster_manager.py     # 集群管理器
│   ├── cluster_api.py
│   ├── load_balancer.py       # 负载均衡
│   └── load_balancer_api.py
│
├── JavaScript/                 # 前端JavaScript
│   ├── server.js              # Node服务器
│   ├── api-client.js          # API客户端
│   ├── api-server.js          # API服务器
│   └── ...
│
├── HTML/                       # HTML页面
├── CSS/                        # 样式文件
│
├── cross-platform-app/         # 跨平台应用 (React Native)
│   ├── App.js
│   ├── index.js
│   └── screens/
│
├── exam_app/                   # 考试应用 (Expo)
│   ├── App.js
│   ├── screens/
│   └── services/
│
└── docs/                      # 文档
    ├── guides/
    ├── Architecture/
    └── Changelogs/
```

---

## 3. 核心模块 (core)

### 3.1 模块概述
core模块是MTSCOS AI系统的基础业务逻辑层，提供AI服务、缓存管理、数据库操作、任务调度等核心功能。

### 3.2 ai.py - AI服务模块

#### AICache 类
内存缓存机制，用于缓存AI响应。

| 方法 | 说明 |
|------|------|
| `generate_key(prompt, **kwargs)` | 生成缓存键 |
| `get_cached_response(prompt, **kwargs)` | 获取缓存响应 |
| `set_cache(prompt, response, **kwargs)` | 设置缓存 |
| `clear_cache()` | 清空缓存 |
| `clean_expired()` | 清理过期缓存 |

#### AIService 类
核心AI服务类，管理多个AI提供商。

| 方法 | 说明 |
|------|------|
| `__init__(config)` | 初始化AI服务 |
| `get_available_providers()` | 获取可用提供商列表 |
| `generate_text(prompt, provider, model, **kwargs)` | 生成文本 |
| `stream_generate(prompt, provider, model, **kwargs)` | 流式生成 |
| `chat(messages, provider, model, **kwargs)` | 对话接口 |
| `analyze_code(code, language, **kwargs)` | 代码分析 |
| `generate_code(description, language, **kwargs)` | 代码生成 |
| `summarize_text(text, **kwargs)` | 文本摘要 |
| `translate_text(text, target_lang, **kwargs)` | 翻译 |
| `extract_keywords(text, **kwargs)` | 关键词提取 |
| `rewrite_text(text, style, **kwargs)` | 文本改写 |
| `get_model_list(provider)` | 获取模型列表 |

### 3.3 cache.py - 缓存管理

#### LocalCache 类
本地内存缓存，支持TTL过期机制。

| 方法 | 说明 |
|------|------|
| `generate_key(*args, **kwargs)` | 生成缓存键 |
| `get(key)` | 获取缓存 |
| `set(key, value, ttl)` | 设置缓存 |
| `delete(key)` | 删除缓存 |
| `clear()` | 清空缓存 |
| `has(key)` | 检查键是否存在 |

#### RedisCache 类
Redis缓存封装，接口与LocalCache一致。

#### CacheManager 类
统一缓存管理器，支持切换本地/Redis后端。

### 3.4 database.py - 数据库管理

#### DatabaseManager 类
SQLite数据库操作管理器。

| 方法 | 说明 |
|------|------|
| `connect()` | 建立连接 |
| `execute(sql, params)` | 执行SQL |
| `fetch_one(sql, params)` | 获取单行 |
| `fetch_all(sql, params)` | 获取所有行 |
| `commit()` | 提交事务 |
| `rollback()` | 回滚事务 |
| `close()` | 关闭连接 |
| `backup()` | 备份数据库 |
| `restore(backup_file)` | 恢复数据库 |

### 3.5 education.py - 教育AI

#### EducationalAI 基类
为不同角色提供知识库和经验的AI基类。

#### ResearcherAI 类
专注于教学大纲分析和课程设计。

#### ExpertAI 类
提供学科专业知识，回答问题并生成知识点体系。

#### TeacherAI 类
辅助教师教学工作，包括生成教案、分析学生进度等。

#### StudentAI 类
服务于学生学习，提供学习路径和建议。

### 3.6 question_bank.py - 题库管理

#### QuestionBankOptimizer 类
题库优化功能。

| 方法 | 说明 |
|------|------|
| `optimize_question(question)` | 优化单道题目 |
| `calculate_difficulty(question)` | 计算难度 |
| `determine_cognitive_level(question)` | 确定认知层次 |
| `generate_tags(question)` | 生成标签 |

#### CurriculumMatcher 类
匹配题目到教学大纲。

| 方法 | 说明 |
|------|------|
| `match_to_curriculum(question, curriculum)` | 匹配教学大纲 |
| `generate_by_curriculum(curriculum, requirements)` | 根据大纲生成题目 |

### 3.7 scheduler.py - 任务调度

#### Scheduler 类
任务调度器，支持周期性和一次性任务。

| 方法 | 说明 |
|------|------|
| `add_task(task_func, interval, **kwargs)` | 添加任务 |
| `remove_task(task_id)` | 移除任务 |
| `start()` | 启动调度器 |
| `pause()` | 暂停调度器 |
| `shutdown()` | 关闭调度器 |

### 3.8 session.py - 会话管理

#### SessionManager 类
会话管理器。

| 方法 | 说明 |
|------|------|
| `create_session(user_id, **kwargs)` | 创建会话 |
| `get_session(session_id)` | 获取会话 |
| `update_session(session_id, **kwargs)` | 更新会话 |
| `delete_session(session_id)` | 删除会话 |
| `refresh_session(session_id)` | 刷新会话 |

### 3.9 system.py - 系统监控

#### SystemMonitor 类
系统状态监控。

| 方法 | 说明 |
|------|------|
| `get_system_status()` | 获取系统状态 |
| `get_memory_usage()` | 内存使用率 |
| `get_cpu_usage()` | CPU使用率 |
| `get_disk_space()` | 磁盘空间 |
| `get_network_info()` | 网络信息 |
| `to_dict()` | 转换为字典 |

### 3.10 intelligence.py - 智能服务

#### IntelligenceService 类
智能服务包装器，整合AI和教育模块。

| 方法 | 说明 |
|------|------|
| `generate_code(description, language)` | 代码生成 |
| `understand_code(code)` | 代码理解 |
| `analyze_code(code)` | 代码分析 |
| `multimodal_interaction(input_data)` | 多模态交互 |

### 3.11 recommendation.py - 推荐系统

#### RecommendationEngine 类
个性化推荐引擎。

| 方法 | 说明 |
|------|------|
| `recommend_for_user(user_id, items, context)` | 用户推荐 |
| `recommend_items(user_id, num)` | 物品推荐 |

---

## 4. Flask应用 (flask-app)

### 4.1 应用入口 (app.py)
Flask应用主入口，定义应用初始化、蓝图注册、路由、认证等功能。

### 4.2 API路由 (app/api/)

| 文件 | 说明 |
|------|------|
| `routes.py` | 基础路由定义 |
| `auth_api.py` | 用户认证API |
| `config_api.py` | 系统配置API |
| `exam_api.py` | 考试系统API |
| `cluster_api.py` | 集群管理API |
| `question_bank_api.py` | 题库API |
| `student_learning_api.py` | 学生学习API |
| `self_learning_api.py` | 自学API |
| `auto_learning_api.py` | 自动学习API |
| `version_api.py` | 版本管理API |
| `settings_api.py` | 设置API |
| `middleware.py` | 中间件 |
| `cluster_api.py` | 集群API |
| `distributed_db_api.py` | 分布式数据库API |
| `cdn_proxy_api.py` | CDN代理API |
| `firewall_api.py` | 防火墙API |
| `auto_upgrade_api.py` | 自动升级API |
| `scheduler_api.py` | 调度器API |
| `optimized_api.py` | 优化API |

### 4.3 数据模型 (app/models/)

| 模型文件 | 说明 |
|----------|------|
| `user.py` | 用户模型 |
| `question.py` | 题库模型 |
| `exam_system.py` | 考试系统模型 |
| `rule.py` | 规则模型 |
| `backup.py` | 备份模型 |
| `logs.py` | 日志模型 |
| `security_model.py` | 安全模型 |
| `learning_system.py` | 学习系统模型 |
| `teaching_content.py` | 教学内容模型 |
| `system_config.py` | 系统配置模型 |
| `student_behavior.py` | 学生行为模型 |
| `ai_employee.py` | AI员工模型 |
| `approval_system.py` | 审批系统模型 |
| `database_version_manager.py` | 数据库版本管理 |
| `enhanced_exam.py` | 增强考试模型 |
| `exam_tournament.py` | 考试竞赛模型 |
| `interaction_model.py` | 交互模型 |
| `logic_model.py` | 逻辑模型 |
| `rule_model.py` | 规则模型 |

### 4.4 AI引擎 (ai_engines/)

| 文件 | 说明 |
|------|------|
| `ai.py` | AI基础类 |
| `ai_brain.py` | AI大脑 |
| `ai_lab.py` | AI实验室 |
| `auth.py` | AI认证 |
| `cleanup.py` | 清理模块 |
| `exam_ai.py` | 考试AI |
| `git_ai.py` | Git AI |
| `learning.py` | 学习AI |
| `login.py` | 登录AI |
| `theme.py` | 主题AI |

### 4.5 配置 (app/config/)

| 文件 | 说明 |
|------|------|
| `config.py` | 主配置 |
| `settings.py` | 设置 |
| `logging.py` | 日志配置 |

### 4.6 工具函数 (app/utils/)

| 目录/文件 | 说明 |
|----------|------|
| `db.py` | 数据库工具 |
| `cache.py` | 缓存工具 |
| `security.py` | 安全工具 |
| `logging.py` | 日志工具 |
| `network.py` | 网络工具 |

---

## 5. 集群管理 (cluster)

### 5.1 ClusterManager 类

| 属性 | 说明 |
|------|------|
| `nodes` | 节点字典 |
| `current_master` | 当前主节点 |
| `cluster_name` | 集群名称 |

| 方法 | 说明 |
|------|------|
| `start()` | 启动集群管理器 |
| `stop()` | 停止集群管理器 |
| `get_cluster_status()` | 获取集群状态 |
| `add_node(node_config)` | 添加节点 |
| `remove_node(node_id)` | 移除节点 |

### 5.2 节点角色 (NodeRole)

| 角色 | 说明 |
|------|------|
| `MASTER` | 主节点 |
| `WORKER` | 工作节点 |
| `STANDBY` | 备用节点 |

### 5.3 节点状态 (NodeStatus)

| 状态 | 说明 |
|------|------|
| `HEALTHY` | 健康 |
| `DEGRADED` | 降级 |
| `UNHEALTHY` | 不健康 |
| `JOINING` | 加入中 |
| `LEAVING` | 离开中 |

### 5.4 负载均衡器 (load_balancer.py)

| 方法 | 说明 |
|------|------|
| `add_backend(host, port)` | 添加后端 |
| `remove_backend(host, port)` | 移除后端 |
| `get_next_backend()` | 获取下一后端 |
| `health_check()` | 健康检查 |

---

## 6. 前端模块

### 6.1 JavaScript模块 (JavaScript/)

| 文件 | 说明 |
|------|------|
| `server.js` | 主服务器 |
| `api-client.js` | API客户端 |
| `api-server.js` | API服务器 |
| `config.js` | 配置文件 |
| `database-manager.js` | 数据库管理 |
| `database.js` | 数据库 |
| `captcha-manager.js` | 验证码管理 |
| `captcha-service.js` | 验证码服务 |
| `cleanup-manager.js` | 清理管理 |
| `error_handler.js` | 错误处理 |
| `mtscos-ui.js` | UI组件 |
| `mtscos-utils.js` | 工具函数 |
| `oauth-service.js` | OAuth服务 |
| `theme-manager.js` | 主题管理 |
| `unified-logger.js` | 统一日志 |
| `version-manager.js` | 版本管理 |

### 6.2 加密JS模块 (Encrypted_JS/)

| 文件 | 说明 |
|------|------|
| `ViKeyInterface.js` | ViKey接口 |
| `admin-script.js` | 管理脚本 |
| `anti_hotlink.js` | 防盗链 |
| `client.js` | 客户端 |
| `common-utils.js` | 公共工具 |
| `css-auto-loader.js` | CSS自动加载 |
| `login-script.js` | 登录脚本 |
| `security-module.js` | 安全模块 |

### 6.3 HTML页面 (HTML/)

| 文件 | 说明 |
|------|------|
| `index.html` | 主页面 |
| `service_monitor.html` | 服务监控 |
| `backup_monitor.html` | 备份监控 |

### 6.4 样式文件 (CSS/)

| 目录 | 说明 |
|------|------|
| `common_styles/` | 公共样式 |
| `component_styles/` | 组件样式 |
| `page_styles/` | 页面样式 |
| `other_styles/` | 其他样式 |

---

## 7. 移动应用

### 7.1 跨平台应用 (cross-platform-app)

基于React Native的跨平台应用。

```
cross-platform-app/
├── App.js              # 主应用组件
├── index.js           # 入口文件
├── package.json       # 依赖配置
└── README.md          # 文档
```

### 7.2 考试应用 (exam_app)

基于Expo的考试应用。

```
exam_app/
├── App.js             # 主应用
├── index.js           # 入口
├── screens/           # 页面
│   ├── ExamScreen.js
│   ├── HomeScreen.js
│   └── LoginScreen.js
├── services/          # 服务
│   └── api.js
└── README.md
```

---

## 8. 依赖关系

### 8.1 Python依赖 (flask-app/requirements.txt)

```
Flask==3.0.0
Flask-SQLAlchemy==3.1.1
Flask-Login==0.6.3
Flask-Session==0.5.0
requests==2.31.0
pyjwt==2.8.0
python-dotenv==1.0.0
psutil==5.9.8
gunicorn==21.2.0
numpy==1.26.4
cryptography==42.0.0
redis==5.0.1
celery==5.3.6
prometheus-client==0.19.0
websockets==12.0
paho-mqtt==1.6.1
grpcio==1.62.0
```

### 8.2 模块依赖图

```
app.py (Flask入口)
├── core/
│   ├── ai.py
│   ├── cache.py
│   ├── database.py
│   ├── education.py
│   ├── question_bank.py
│   ├── scheduler.py
│   ├── session.py
│   ├── system.py
│   └── intelligence.py
├── flask-app/app/
│   ├── api/ → 依赖 models/, services/
│   ├── models/ → 依赖 utils/db.py
│   ├── views/
│   ├── services/
│   └── utils/
└── cluster/
    └── cluster_manager.py
```

---

## 9. API文档

### 9.1 基础端点

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/health` | 健康检查 |
| GET | `/api/status` | 系统状态 |
| POST | `/api/handshake` | API握手 |
| POST | `/api/heartbeat` | 心跳检测 |
| GET | `/api/docs` | API文档 |

### 9.2 考试相关API

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/exam/list` | 获取考试列表 |
| GET | `/api/exam/questions` | 获取考试题目 |
| POST | `/api/exam/generate` | 生成试卷 |
| GET | `/api/exam/<exam_id>` | 获取考试详情 |

### 9.3 AI相关API

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/ai/chat` | AI对话 |
| POST | `/api/ai/analyze` | 代码分析 |
| POST | `/api/ai/summarize` | 文本摘要 |
| POST | `/api/ai/translate` | 文本翻译 |
| GET | `/api/ai/providers` | AI提供商列表 |
| GET | `/api/ai-brain/status` | AI大脑状态 |

### 9.4 系统API

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/system/performance` | 性能报告 |
| GET | `/api/system/network` | 网络接口 |
| GET | `/api/system/disks` | 磁盘分区 |
| GET | `/api/system/processes` | 进程列表 |
| POST | `/api/config/reload` | 重载配置 |

### 9.5 规则API

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/rules` | 获取所有规则 |
| GET | `/api/rules/<rule_type>` | 按类型获取规则 |

---

## 10. 数据模型

### 10.1 用户模型 (User)

```python
class User:
    user_id: int          # 用户ID
    username: str         # 用户名
    email: str            # 邮箱
    password: str         # 密码哈希
    role: str             # 角色 (user/admin/super_admin)
    is_active: int        # 激活状态
    created_at: str       # 创建时间
    updated_at: str       # 更新时间
    avatar: str           # 头像
    phone: str            # 电话
```

### 10.2 题目模型 (Question)

```python
class Question:
    id: int               # 题目ID
    subject: str          # 学科 (japanese等)
    difficulty: str       # 难度 (easy/medium/hard/all)
    question_type: str    # 类型 (single_choice/multiple_choice等)
    content: str          # 题干内容
    options: List[str]    # 选项
    answer: str           # 答案
    explanation: str      # 解析
    category_id: int      # 分类ID
    tags: List[str]       # 标签
    created_at: str       # 创建时间
    updated_at: str       # 更新时间
```

### 10.3 考试模型 (Exam)

```python
class Exam:
    id: str               # 考试ID
    title: str            # 考试标题
    description: str      # 描述
    language: str         # 语言
    level: str            # 级别 (beginner/intermediate/advanced/expert)
    duration: int         # 时长(分钟)
    question_count: int   # 题目数量
    total_points: float   # 总分
    passing_score: float # 及格分
    status: ExamStatus   # 状态 (draft/active/inactive/archived)
    shuffle_questions: bool  # 打乱题目
    shuffle_options: bool     # 打乱选项
    allow_retake: bool    # 允许重考
    max_retakes: int      # 最大重考次数
    created_by: str       # 创建者
    created_at: datetime  # 创建时间
```

### 10.4 试卷模型 (ExamPaper)

```python
class ExamPaper:
    id: str               # 试卷ID
    exam_id: str          # 考试ID
    user_id: str          # 用户ID
    questions: List[str]  # 题目ID列表
    scores: Dict         # 分数 {question_id: score}
    answers: Dict         # 答案 {question_id: answer}
    status: ExamPaperStatus  # 状态
    start_time: datetime # 开始时间
    end_time: datetime   # 结束时间
    submitted_at: datetime # 提交时间
```

### 10.5 题目类型枚举 (QuestionType)

```python
class QuestionType(Enum):
    SINGLE_CHOICE = "single_choice"      # 单选题
    MULTIPLE_CHOICE = "multiple_choice"  # 多选题
    TRUE_FALSE = "true_false"            # 判断题
    FILL_BLANK = "fill_blank"            # 填空题
    SHORT_ANSWER = "short_answer"        # 简答题
    ESSAY = "essay"                      # 论述题
    LISTENING = "listening"              # 听力题
    READING = "reading"                  # 阅读题
```

---

## 11. 运行方式

### 11.1 环境要求

| 要求 | 版本 |
|------|------|
| Python | >= 3.11 |
| Node.js | >= 14.0.0 |
| npm | >= 6.0.0 |
| Redis | >= 6.0 |
| SQLite | 3.x |

### 11.2 快速启动

#### Flask后端
```bash
cd flask-app
pip install -r requirements.txt
python app.py
# 访问 http://localhost:5000
```

#### 使用Makefile
```bash
make install
make run
make health-check
make backup-db
```

#### 使用启动脚本
```bash
./start.sh          # 交互式菜单
./start.sh start    # 命令行启动
./start.sh status   # 查看状态
./start.sh stop     # 停止服务
```

### 11.3 Docker部署

```bash
docker-compose up -d
```

### 11.4 集群启动

```bash
# 启动集群管理器
./cluster/start_cluster.sh

# 启动负载均衡器
./cluster/start_load_balancer.sh
```

### 11.5 访问地址

| 服务 | 地址 |
|------|------|
| 主界面 | http://localhost:3000 |
| API接口 | http://localhost:3000/api |
| 管理后台 | http://localhost:3000/admin |
| Flask API | http://localhost:5000 |

### 11.6 日志文件

| 日志 | 路径 |
|------|------|
| 启动日志 | `Logs/startup.log` |
| 服务日志 | `Logs/service.log` |
| 错误日志 | `Logs/error.log` |

---

## 附录

### A. 版本历史
- v4.3.0 (2026-06-04): 最新稳定版本
- v4.3.3: 归档版本
- v1.1.0: 初始归档版本

### B. 特性标志
```
K12_SUPPORT, ACHIEVEMENT_SYSTEM, ADVANCED_STATS,
VERSION_MANAGEMENT_V3, CLOUD_SYNC, AI_ENGINE_V4,
INTELLIGENT_LEARNING_PATH, ENHANCED_EXAM_SYSTEM,
DATABASE_VERSION_HISTORY, AUTO_ARCHIVE,
TEACHING_CONTENT_MANAGEMENT, TEACHING_RULE_ENGINE
```

### C. 增强功能
```
AI_LEARNING_RECOMMENDER, ADAPTIVE_LEARNING,
KNOWLEDGE_GRAPH, INTELLIGENT_PATH_PLANNING,
ENHANCED_EXAM_SYSTEM, PERSONALIZED_PRACTICE,
SCORE_PREDICTION, ERROR_NOTEBOOK,
DATABASE_VERSION_TRACKING, AUTO_ARCHIVE_SYSTEM,
TEACHING_SYLLABUS, TEACHING_PREPARATION,
TEACHING_PLAN, TEACHING_RULE_ENGINE
```

---

*本文档由MTSCOS AI系统自动生成*
*最后更新: 2026-06-18*
