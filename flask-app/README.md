# MTSCOS AI 智能考试系统

> 版本: v7.2.0 (Comprehensive Enhancement Edition)
> 更新日期: 2026-07-09

MTSCOS AI 是一个基于 Flask 框架开发的分布式智能考试管理平台，提供完整的题库系统、考试管理、学习分析、AI智能引擎等功能。

## 🌟 核心特性

### 🏗️ 架构特性
- **模块化启动系统**：8阶段配置加载 + 6阶段功能模块加载
- **分布式数据库架构**：16+ 独立数据库，智能路由
- **AI智能引擎矩阵**：20+ 核心引擎，60+ AI员工
- **响应式前端布局**：支持桌面端和移动端

### 📚 题库系统
- **37,000+ 题目**：覆盖成人教育和K12全科目
- **7种题型**：单选题、多选题、判断题、填空题、简答题、论述题、听力题
- **智能出题**：基于知识点/难度/题型批量出题

### 🔐 权限管理
- **12个角色**：guest→student→parent→designer→teacher→exam_proctor→question_manager→ai_manager→cluster_manager→admin→super_admin→hardware_admin
- **细粒度权限**：覆盖全系统功能权限控制
- **审计日志**：完整操作记录、实时审计

### 🤖 AI集群与模型库
- **15+ AI模型**：GPT-4、Claude-3、Qwen、Llama-3、Gemini等
- **性能监控**：延迟、吞吐量、准确率指标
- **动态扩展**：节点自动扩展、负载均衡

### ✨ AI智能功能
- **AI题目生成器**：从文本内容自动生成考试题目，支持6种题型、11个科目、3级难度
- **AI学习路径推荐**：分析学生错题数据，生成个性化学习路径，包含薄弱分析和知识图谱

### 🌐 端口与集群管理
- **21个端口配置**：HTTP/HTTPS、API、WebSocket、数据库等
- **端口管理**：扫描、分配、预留、释放、自动修复
- **负载均衡**：轮询、最小连接数、加权轮询、IP哈希
- **健康检查**：心跳检测、自动故障转移

### 📊 系统监控
- **实时监控**：CPU、内存、磁盘、网络
- **慢查询检测**：自动识别和优化慢查询
- **性能分析**：索引建议、查询统计

### 🚀 自动化运维
- **Git自动同步**：变更检测、自动提交、推送
- **每日健康检查**：数据库清理、日志清理、备份
- **自动升级**：版本检测、灰度发布、健康检查回滚

## 📁 项目结构

```
flask-app/
├── app.py                      # 应用入口
├── modular_start.py            # 模块化启动脚本
├── SYSTEM_DOC.md               # 系统说明书
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
│   ├── api/                    # API接口 (120+个)
│   │   ├── auth_api.py         # 认证API
│   │   ├── exam_api.py         # 考试API
│   │   ├── performance_api.py  # 性能监控API
│   │   └── ...
│   ├── ai/                     # AI子模块
│   ├── blueprints/             # 蓝图模块
│   ├── services/               # 服务模块
│   │   ├── db_performance_service.py  # 数据库性能服务
│   │   ├── cluster_service.py         # 集群管理服务
│   │   └── port_monitor_service.py   # 端口监控服务
│   ├── models/                 # 数据模型 (20+个)
│   ├── middlewares/            # 中间件
│   ├── routes/                 # 路由模块
│   ├── containers/             # 容器模块
│   └── utils/                  # 工具模块
├── split_databases/            # 分布式数据库 (16+个)
├── templates/                  # HTML模板 (100+个)
├── static/                     # 静态资源
├── scripts/                    # 脚本工具
│   └── expand_question_bank.py # 题库拓展脚本
└── startup_modules/            # 模块化启动器
    ├── db_config_loader.py     # 数据库配置加载器
    ├── core_init.py            # 核心初始化
    └── module_loader.py        # 功能模块加载器
```

## 🚀 快速开始

### 环境要求
- Python 3.8+
- SQLite 3.30+
- Git

### 安装步骤

```bash
# 克隆仓库
git clone https://github.com/wuchenghao15/wuchenghao15.git
cd flask-app

# 安装依赖
pip install -r requirements.txt

# 初始化数据库
python -c "from app.utils.db import init_all_databases; init_all_databases()"

# 启动服务
python app.py --port 8888
```

### 启动参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| --port | 服务端口 | 8888 |
| --host | 绑定地址 | 127.0.0.1 |
| --debug | 调试模式 | False |
| --ssl | 启用SSL | False |
| --ssl-port | SSL端口 | 8443 |

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

### 性能监控接口
| 接口 | 方法 | 说明 |
|------|------|------|
| /api/performance/db/status | GET | 获取数据库状态 |
| /api/performance/db/query-stats | GET | 获取查询统计 |
| /api/performance/db/slow-queries | GET | 获取慢查询列表 |
| /api/performance/db/optimize | POST | 优化数据库 |

### 端口管理接口
| 接口 | 方法 | 说明 |
|------|------|------|
| /api/ports/status | GET | 获取端口状态 |
| /api/ports/scan | POST | 扫描端口范围 |
| /api/ports/allocate | POST | 分配可用端口 |

### 集群管理接口
| 接口 | 方法 | 说明 |
|------|------|------|
| /api/cluster/nodes | GET | 获取节点列表 |
| /api/cluster/stats | GET | 获取集群统计 |
| /api/cluster/strategy | POST | 设置负载均衡策略 |

## 📊 数据库架构

### 主要数据库
| 数据库 | 用途 |
|--------|------|
| auth.db | 认证和用户管理 |
| exam.db | 考试管理 |
| question.db | 题库管理 |
| learning.db | 学习系统 |
| system.db | 系统配置 |
| ai.db | AI引擎数据 |
| admin.db | 管理后台 |
| log.db | 日志系统 |

## 🤝 贡献

欢迎提交Issue和Pull Request！

## 📄 许可证

MIT License

## 📞 联系方式

- 项目地址: https://github.com/wuchenghao15/wuchenghao15
- 文档: [SYSTEM_DOC.md](SYSTEM_DOC.md)