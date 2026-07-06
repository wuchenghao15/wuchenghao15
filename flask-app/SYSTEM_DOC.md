# MTSCOS AI 智能考试系统 - 系统说明书

> 版本: v7.0.0 (Intelligent Modular Edition)
> 更新日期: 2026-07-07
> 文档版本: 7.0

## 目录

1. [系统概述](#1-系统概述)
2. [系统架构](#2-系统架构)
3. [模块化启动系统](#3-模块化启动系统)
4. [分布式数据库](#4-分布式数据库)
5. [AI智能引擎](#5-ai智能引擎)
6. [API和路由数据库管理](#6-api和路由数据库管理)
7. [权限管理体系](#7-权限管理体系)
8. [集群和端口管理](#8-集群和端口管理)
9. [前端页面系统](#9-前端页面系统)
10. [Git自动同步](#10-git自动同步)
11. [版本历史](#11-版本历史)
12. [API接口文档](#12-api接口文档)

---

## 1. 系统概述

MTSCOS AI 智能考试系统是一个基于 Flask 框架的分布式智能考试管理平台。v7.0.0 版本代号 "Intelligent Modular Edition"（智能模块化版本），主要新增了模块化启动系统、AI智能检索模型、API/路由数据库管理等特性。

### 核心特性
- 模块化启动系统（8阶段配置加载 + 6阶段功能模块加载）
- 分布式数据库架构（16+ 独立数据库）
- AI智能引擎（45+ AI员工，6+ AI Agent，590+ 检索模型）
- AI智能API和路由数据库管理
- 完整的RBAC权限管理体系
- 多维度集群监控和管理
- Git/GitHub自动同步

---

## 2. 系统架构

### 2.1 目录结构
```
flask-app/
├── modular_start.py           # 模块化启动脚本（主入口）
├── simple_start.py            # 简化启动脚本
├── app.py                     # 原始应用文件
├── startup_modules/           # 模块化启动器
│   ├── __init__.py
│   ├── db_config_loader.py   # 数据库配置加载器（8阶段）
│   ├── core_init.py           # 核心初始化（4步骤）
│   └── module_loader.py       # 功能模块加载器（6阶段）
├── ai_engines/                # AI引擎模块
│   ├── all_ai_employees_loader.py    # AI员工加载器
│   ├── ai_search_query_model.py      # AI智能检索模型
│   ├── ai_api_database_manager.py    # API数据库管理
│   ├── ai_routes_database_manager.py # 路由数据库管理
│   └── ai_cluster_manager.py         # AI集群管理
├── app/                       # 应用模块
│   ├── api/                   # API接口（79+个）
│   ├── blueprints/            # 蓝图模块
│   ├── services/              # 服务模块
│   ├── models/                # 数据模型
│   ├── middlewares/           # 中间件
│   └── routes/                # 路由模块
├── split_databases/           # 分布式数据库（16+个）
├── templates/                 # HTML模板（100+个）
└── static/                    # 静态资源
```

---

## 3. 模块化启动系统

### 3.1 启动流程（5大阶段）

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
2. API接口模块（后台线程加载，79+个）
3. 蓝图模块（后台线程加载）
4. 服务模块（同步加载）
5. AI引擎模块（后台线程加载）
6. 中间件模块（同步加载）

#### 阶段4: 系统管理API注册
#### 阶段5: 启动Web服务器

### 3.2 启动命令
```bash
# 标准启动
python modular_start.py --port 8888

# 调试模式
python modular_start.py --port 8888 --debug

# 指定主机
python modular_start.py --host 127.0.0.1 --port 9000
```

---

## 4. 分布式数据库

### 4.1 数据库列表（16+个）
| 数据库 | 大小 | 用途 |
|--------|------|------|
| auth.db | 268KB | 认证和用户管理 |
| exam.db | 3.8MB | 考试管理 |
| question.db | 757MB | 题库管理 |
| user.db | 1.4MB | 用户信息 |
| system.db | 85MB | 系统配置 |
| admin.db | 1.8MB | 管理后台 |
| ai.db | 956KB | AI引擎 |
| learning.db | 1.1MB | 学习系统 |
| proctor.db | 144KB | 监考系统 |
| log.db | 96MB | 日志系统 |
| api_management.db | 80KB | API管理 |
| routes_management.db | 116KB | 路由管理 |
| search_models.db | 312KB | 检索模型 |

### 4.2 智能数据库路由
通过 `smart_db_router.py` 实现 SQL 查询自动路由到正确的分布式数据库。

---

## 5. AI智能引擎

### 5.1 AI员工（45+）
- AI开发工程师、AI测试工程师、AI设计师
- AI数据分析师、AI安全专家、AI运维工程师
- 验证AI员工、路由AI员工、测试系统AI员工
- 诊断修复AI员工等

### 5.2 AI Agent（6+）
- 系统监控Agent、数据备份Agent
- 智能调度器、版本管理Agent
- Git同步Agent、自愈Agent

### 5.3 AI智能检索模型（590+）
- 自动为所有数据库表创建检索模型
- 智能索引推荐和创建
- 查询性能监控和自动适配
- 模型适配历史记录

### 5.4 自动化任务（6个）
- 定时Git同步（每5分钟）
- 系统健康检查（每分钟）
- 数据库维护（每小时）
- 日志清理（每2小时）
- 权限规则同步（每30分钟）
- 题库更新检查（每30分钟）

---

## 6. API和路由数据库管理

### 6.1 API数据库（api_management.db）
- 73+个API注册
- 10个API分组
- API调用日志记录
- API权限配置
- API参数定义

### 6.2 路由数据库（routes_management.db）
- 81+个路由注册
- 14个路由分组
- 7个默认标签
- 路由访问日志
- 路由依赖关系

---

## 7. 权限管理体系

### 7.1 角色体系
| 角色 | 中文名 | 权限级别 |
|------|--------|---------|
| super_admin | 超级管理员 | 最高 |
| admin | 管理员 | 高 |
| hardware_admin | 硬件管理员 | 中 |
| teacher | 教师 | 中 |
| student | 学生 | 低 |
| user | 用户 | 基础 |
| guest | 访客 | 无 |

### 7.2 权限装饰器
- `@require_login` - 需要登录
- `@require_admin` - 需要管理员权限
- `@require_super_admin` - 需要超级管理员权限

---

## 8. 集群和端口管理

### 8.1 集群管理
- 集群节点注册和管理
- 节点状态监控
- 负载均衡配置

### 8.2 端口管理
- 端口使用统计
- 端口分配管理
- 端口冲突检测

---

## 9. 前端页面系统

### 9.1 模板系统
- 100+ HTML模板文件
- Jinja2模板引擎
- 全局模板函数（角色名称、日期格式化等）

### 9.2 静态资源
- Tailwind CSS（本地版本）
- Font Awesome（本地版本）
- 自定义CSS和JS

---

## 10. Git自动同步

### 10.1 自动同步功能
- 变更检测
- 自动提交
- 自动推送
- 定时同步（每5分钟）

### 10.2 API接口
- `GET /api/git/status` - Git状态
- `POST /api/git/sync` - 手动同步
- `POST /api/git/auto_sync` - 启用自动同步

---

## 11. 版本历史

| 版本 | 代号 | 日期 | 主要特性 |
|------|------|------|---------|
| v7.0.0 | Intelligent Modular Edition | 2026-07-07 | 模块化启动、AI智能检索、API/路由数据库管理 |
| v6.0.0 | Distributed Database Edition | 2026-07-06 | 分布式数据库架构（13个独立数据库） |
| v5.0.0 | AI Integration Edition | 2026-06-01 | AI集成版本，AI助教引擎 |
| v4.0.0 | Exam System Edition | 2026-05-01 | 在线考试和监考功能 |
| v3.0.0 | Learning Edition | 2026-04-01 | 学习管理系统 |
| v2.0.0 | Admin Edition | 2026-03-01 | 权限和用户管理 |
| v1.0.0 | Initial Edition | 2026-02-01 | 初始版本 |

---

## 12. API接口文档

### 12.1 系统管理API
| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/system/status` | GET | 获取系统完整状态 |
| `/api/system/configs` | GET | 获取系统配置 |
| `/api/system/configs/reload` | POST | 重新加载配置 |
| `/api/system/modules` | GET | 获取模块加载状态 |

### 12.2 认证API
| 接口 | 方法 | 说明 |
|------|------|------|
| `/auth/login` | POST | 用户登录 |
| `/auth/register` | POST | 用户注册 |
| `/auth/logout` | GET/POST | 用户登出 |
| `/auth/check` | GET | 检查登录状态 |

### 12.3 AI引擎API
| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/ai_employees/status` | GET | AI员工状态 |
| `/api/ai_employees/list` | GET | AI员工列表 |
| `/api/ai_agents/list` | GET | AI Agent列表 |
| `/api/search_models/status` | GET | 检索模型状态 |
| `/api/search_models/list` | GET | 检索模型列表 |
| `/api/api_database/status` | GET | API数据库状态 |
| `/api/routes_database/status` | GET | 路由数据库状态 |

---

*文档结束 - MTSCOS AI 智能考试系统 v7.0.0*
