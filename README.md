# MTSCOS AI 智能考试系统

> 版本 v7.0.0 - Intelligent Modular Edition
> 构建日期: 2026-07-07

## 📋 系统简介

MTSCOS AI 智能考试系统是一个基于 Flask 的分布式智能考试管理平台，支持模块化启动、AI集群管理、分布式数据库架构。

## ✨ 核心特性

- 🚀 **模块化启动系统** - 8阶段数据库配置加载，6阶段功能模块加载
- 🗄️ **分布式数据库架构** - 16+ 独立数据库，智能路由
- 🤖 **AI智能引擎** - 45+ AI员工，6+ AI Agent，590+ 检索模型
- 📡 **API/路由数据库管理** - 智能API和路由注册管理
- 🔐 **RBAC权限管理** - 完整的角色权限控制体系
- 📊 **集群管理** - 多维度监控和负载均衡
- 🔄 **Git自动同步** - 代码自动提交和推送

## 🏗️ 系统架构

### 目录结构
- `flask-app/` - 主应用目录
- `flask-app/modular_start.py` - 模块化启动脚本
- `flask-app/startup_modules/` - 启动模块（配置加载、核心初始化、模块加载）
- `flask-app/ai_engines/` - AI引擎模块
- `flask-app/app/` - 应用模块（API、蓝图、服务、模型）
- `flask-app/split_databases/` - 分布式数据库（16+个）

### 分布式数据库
| 数据库 | 用途 |
|--------|------|
| auth.db | 认证和用户管理 |
| exam.db | 考试管理 |
| question.db | 题库管理 |
| user.db | 用户信息 |
| system.db | 系统配置 |
| admin.db | 管理后台 |
| ai.db | AI引擎 |
| learning.db | 学习系统 |
| proctor.db | 监考系统 |
| log.db | 日志系统 |
| api_management.db | API管理 |
| routes_management.db | 路由管理 |
| search_models.db | 检索模型 |

## 🚀 快速开始

### 环境要求
- Python 3.9+
- Flask 2.0+

### 安装
```bash
cd flask-app
pip install -r requirements.txt
```

### 启动
```bash
# 模块化启动（推荐）
python modular_start.py --port 8888

# 简化启动
python simple_start.py --port 8888
```

### 访问
- 系统首页: http://localhost:8888/
- 登录页面: http://localhost:8888/login
- 系统状态API: http://localhost:8888/api/system/status

## 📚 API文档

### 系统管理
- `GET /api/system/status` - 系统状态
- `GET /api/system/configs` - 系统配置
- `GET /api/system/modules` - 模块状态

### AI引擎
- `GET /api/ai_employees/status` - AI员工状态
- `GET /api/ai_agents/list` - AI Agent列表
- `GET /api/search_models/status` - 检索模型状态

### 数据库管理
- `GET /api/api_database/status` - API数据库状态
- `GET /api/routes_database/status` - 路由数据库状态

## 📖 版本历史

| 版本 | 代号 | 日期 | 说明 |
|------|------|------|------|
| v7.0.0 | Intelligent Modular Edition | 2026-07-07 | 模块化启动、AI智能检索、API/路由数据库管理 |
| v6.0.0 | Distributed Database Edition | 2026-07-06 | 分布式数据库架构 |
| v5.0.0 | AI Integration Edition | 2026-06-01 | AI集成版本 |
| v4.0.0 | Exam System Edition | 2026-05-01 | 考试系统版本 |

## 📄 许可证

MIT License

## 👥 贡献

欢迎提交 Issue 和 Pull Request。
