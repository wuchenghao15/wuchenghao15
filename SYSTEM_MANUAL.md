# MTSCOS AI 智能考试系统 - 系统说明书

> 版本 v7.0.0 - Intelligent Modular Edition
> 文档更新日期: 2026-07-07

## 📖 目录

1. [系统概述](#系统概述)
2. [系统架构](#系统架构)
3. [模块化启动系统](#模块化启动系统)
4. [分布式数据库架构](#分布式数据库架构)
5. [AI智能引擎矩阵](#ai智能引擎矩阵)
6. [系统综合增强管理器](#系统综合增强管理器)
7. [权限管理体系](#权限管理体系)
8. [API接口文档](#api接口文档)
9. [版本历史](#版本历史)
10. [运维指南](#运维指南)

---

## 系统概述

MTSCOS AI 智能考试系统是一个基于 Flask 的分布式智能考试管理平台，专为多层级教育场景设计，支持九年制义务教育和成人制教育。系统集成了完整的AI引擎矩阵、分布式数据库架构、模块化启动系统和综合增强管理器。

### 核心数据
- **版本**: v7.0.0 (Intelligent Modular Edition)
- **构建日期**: 2026-07-07
- **数据库数量**: 16+ 独立数据库
- **API路由数量**: 629+ (含32个增强管理器路由)
- **AI员工数量**: 45+
- **AI Agent数量**: 6+
- **AI检索模型**: 590+
- **AI引擎数量**: 20+

---

## 系统架构

### 目录结构
```
MTSCOS_AI_Project/
├── flask-app/                          # 主应用目录
│   ├── modular_start.py                # 模块化启动脚本 (主入口)
│   ├── version_manager.py              # 版本管理系统
│   ├── db_manager.py                   # 数据库管理器
│   ├── startup_modules/                # 启动模块
│   │   ├── db_config_loader.py         # 数据库配置加载器 (8阶段)
│   │   ├── core_init.py                # 核心初始化 (4步骤)
│   │   └── module_loader.py            # 功能模块加载器 (6阶段)
│   ├── ai_engines/                     # AI引擎模块
│   │   ├── system_enhancement_manager.py  # 系统综合增强管理器
│   │   ├── system_enhancement_api.py      # 增强管理器API蓝图
│   │   ├── ai_search_query_model.py      # AI智能检索模型
│   │   ├── ai_api_database_manager.py    # API数据库管理
│   │   ├── ai_routes_database_manager.py # 路由数据库管理
│   │   ├── all_ai_employees_loader.py    # AI员工加载器
│   │   └── ... (20+ AI引擎)
│   ├── templates/                      # 前端模板
│   │   ├── index.html                  # 系统首页
│   │   ├── enhancement_dashboard.html  # 增强管理器仪表板
│   │   └── ...
│   ├── split_databases/               # 分布式数据库 (16+个)
│   └── app/                           # 应用模块
└── README.md                          # GitHub说明文档
```

---

## 模块化启动系统

### 启动流程 (5大阶段)

#### 阶段1: 数据库配置加载 (8个子阶段)
- base - 基础配置
- security - 安全配置
- feature - 功能配置
- advanced - 高级配置
- ai - AI配置
- database - 数据库配置
- cache - 缓存配置
- api - API配置

#### 阶段2: 核心初始化 (4个步骤)
1. 创建Flask应用 (含静态文件配置)
2. 注册Jinja2模板全局函数
3. 配置CORS跨域
4. 初始化数据库连接

#### 阶段3: 功能模块加载 (6个阶段)
1. 认证与基础路由
2. API接口模块 (后台线程加载)
3. 蓝图模块
4. 服务模块
5. AI引擎模块 (后台线程加载)
6. 中间件模块

#### 阶段4: 系统管理API注册
- 系统状态API
- 配置管理API
- 模块管理API
- 系统增强管理器蓝图注册
- 增强管理器默认数据初始化

#### 阶段5: 启动Web服务器

### 启动命令
```bash
# 标准启动
python modular_start.py --port 8888

# 调试模式
python modular_start.py --port 8888 --debug

# 不加载AI引擎
python modular_start.py --port 8888 --no-ai
```

---

## 分布式数据库架构

### 16+ 独立数据库

| 数据库 | 用途 | 主要表 |
|--------|------|--------|
| auth.db | 认证和用户管理 | users, sessions, enh_permission_rules |
| exam.db | 考试管理 | exams, exam_results |
| question.db | 题库管理 | questions, enh_question_categories |
| user.db | 用户信息 | user_profiles |
| system.db | 系统配置 | system_params, enh_port_registry, enh_cluster_nodes, enh_frontend_layout |
| admin.db | 管理后台 | admin_logs |
| ai.db | AI引擎 | enh_ai_nodes, enh_ai_models |
| learning.db | 学习系统 | learning_paths |
| proctor.db | 监考系统 | proctor_logs |
| log.db | 日志系统 | system_logs |
| api_management.db | API管理 | api_registry |
| routes_management.db | 路由管理 | route_registry |
| search_models.db | 检索模型 | search_models (590+) |

---

## AI智能引擎矩阵

系统包含20+ AI引擎，均采用单例模式：

1. 题目生成引擎 (question_generation_engine)
2. 自适应学习引擎 (adaptive_learning_engine)
3. 知识图谱引擎 (knowledge_graph_engine)
4. 奖励成就引擎 (reward_achievement_engine)
5. 错题本智能引擎 (wrong_book_engine)
6. 学习预测分析引擎 (learning_prediction_engine)
7. AI助教答疑引擎 (ai_tutor_engine)
8. 协作学习引擎 (collaborative_learning_engine)
9. 智能教学评估引擎 (teaching_evaluation_engine)
10. 学习资源推荐引擎 (resource_recommendation_engine)
11. 学情分析报告引擎 (learning_report_engine)
12. 智能作业批改引擎 (homework_grading_engine)
13. 家校沟通引擎 (home_school_communication_engine)
14. 学习游戏化引擎 (gamification_engine)
15. 智能预警引擎 (intelligent_warning_engine)
16. AI辅助出题引擎 (ai_question_authoring_engine)
17. 学习数据可视化引擎 (learning_visualization_engine)
18. 智能学习诊断引擎 (learning_diagnosis_engine)
19. 智能知识库引擎 (knowledge_base_engine)
20. AI课堂互动引擎 (classroom_interaction_engine)

---

## 系统综合增强管理器

### 十大功能模块

#### 1. 数据库功能拓展
- `db_health_check()` - 数据库健康检查 (16库完整性验证)
- `analyze_table_structure(db_name)` - 表结构分析
- `suggest_index_optimization(db_name)` - 索引优化建议
- `manage_db_cluster(action, node_info)` - 数据库集群管理

#### 2. 端口管理
- `scan_ports(host, port_range)` - 端口扫描
- `get_port_usage_stats()` - 端口使用统计
- `allocate_port(service, preferred)` - 端口分配

#### 3. 集群管理
- `manage_cluster_nodes(action, node)` - 集群节点管理
- `monitor_cluster_status()` - 集群状态监控
- `load_balance(strategy)` - 负载均衡 (round_robin/least_load)

#### 4. 多维度管理
- `monitor_system_resources()` - 系统资源监控 (CPU/磁盘/内存)
- `analyze_performance()` - 性能分析 (评分+等级)

#### 5. 权限规则升级
- `manage_permission_rules(action, rule)` - 权限规则CRUD
- `get_role_permission_matrix()` - 角色权限矩阵

#### 6. 题库升级
- `get_question_bank_stats()` - 题库统计
- `manage_question_categories(action, category)` - 题目分类管理
- `evaluate_question_quality(limit)` - 题目质量评估 (A/B/C/D等级)

#### 7. AI集群升级
- `manage_ai_nodes(action, node)` - AI节点管理
- `schedule_ai_models(model_id)` - AI模型调度
- `ai_load_balance()` - AI负载均衡

#### 8. AI模型库升级
- `register_model(model)` - 模型注册
- `manage_model_versions(model_name)` - 模型版本管理
- `evaluate_model_performance(model_id, score)` - 模型性能评估

#### 9. 前端布局优化
- `manage_layout_config(action, layout)` - 布局配置管理
- `manage_themes(action, theme)` - 主题管理

#### 10. Git自动同步
- `detect_changes(repo_path)` - 变更检测
- `auto_commit(message, repo_path)` - 自动提交
- `auto_push(remote, branch, repo_path)` - 自动推送

### 默认初始化数据
- 端口: 8888 (mtscos_web)
- 集群节点: node_local_01 (master, 127.0.0.1:8888)
- AI节点: ai_node_01 (本地AI节点, GPT-4)
- 前端布局: default_layout (蓝色主题)
- 权限规则: 5条 (admin/super_admin/student/teacher)
- AI模型: 6个 (GPT-4/GPT-3.5/Claude-3/Qwen-72B/embedding/whisper)

---

## 权限管理体系

### 角色等级 (14级)
1. guest - 访客
2. user - 用户
3. student - 学生
4. student_vip - VIP学生
5. designer - 设计师
6. teacher - 教师
7. researcher - 研究员
8. admin - 管理员 (只读L9)
9. super_admin - 超级管理员
10. hardware_admin - 硬件管理员 (最高权限)
11. hardware_vikey_admin - 硬件维凯管理员
12. system_admin - 系统管理员
13. maintenance - 维护人员
14. auditor - 审计员

### 路由权限策略
- `/exam_system` - student, student_vip
- `/k12` - 公开访问
- `/settings` - admin, super_admin, hardware_admin
- `/super_admin_dashboard` - super_admin, hardware_admin
- `/enhancement` - 需登录
- `/api/enhancement/*` - 需登录

---

## API接口文档

### 系统管理 API
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/system/status | 系统状态 |
| GET | /api/system/configs | 系统配置 |
| POST | /api/system/configs/reload | 重新加载配置 |
| GET | /api/system/modules | 模块状态 |

### 增强管理器 API (32个路由)
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/enhancement/status | 总览状态 |
| GET | /api/enhancement/modules | 模块列表 |
| GET | /api/enhancement/database/health | 数据库健康 |
| GET | /api/enhancement/database/structure | 表结构分析 |
| GET | /api/enhancement/database/index-suggestions | 索引建议 |
| GET | /api/enhancement/ports/scan | 端口扫描 |
| GET | /api/enhancement/ports/stats | 端口统计 |
| POST | /api/enhancement/ports/allocate | 端口分配 |
| GET | /api/enhancement/cluster/monitor | 集群监控 |
| GET | /api/enhancement/cluster/load-balance | 负载均衡 |
| GET | /api/enhancement/system/resources | 系统资源 |
| GET | /api/enhancement/system/performance | 性能分析 |
| GET | /api/enhancement/permissions/rules | 权限规则 |
| GET | /api/enhancement/permissions/matrix | 权限矩阵 |
| GET | /api/enhancement/questions/stats | 题库统计 |
| GET | /api/enhancement/questions/quality | 题目质量 |
| GET | /api/enhancement/ai-cluster/nodes | AI节点 |
| GET | /api/enhancement/ai-cluster/load-balance | AI负载均衡 |
| GET | /api/enhancement/ai-models/versions | 模型版本 |
| GET | /api/enhancement/frontend/layouts | 布局配置 |
| GET | /api/enhancement/frontend/themes | 主题管理 |
| GET | /api/enhancement/git/changes | Git变更 |
| POST | /api/enhancement/git/commit | Git提交 |
| POST | /api/enhancement/git/push | Git推送 |
| POST | /api/enhancement/git/sync | Git一键同步 |

---

## 版本历史

| 版本 | 代号 | 日期 | 主要特性 |
|------|------|------|----------|
| v7.0.0 | Intelligent Modular Edition | 2026-07-07 | 模块化启动、AI智能检索、API/路由数据库管理、系统综合增强管理器 |
| v6.0.0 | Distributed Database Edition | 2026-07-06 | 分布式数据库架构 (13个独立数据库) |
| v5.0.0 | AI Integration Edition | 2026-06-01 | AI集成版本 (AI引擎矩阵) |
| v4.0.0 | Exam System Edition | 2026-05-01 | 考试系统版本 |
| v3.0.0 | Learning Edition | 2026-04-01 | 学习系统版本 |
| v2.0.0 | Admin Edition | 2026-03-01 | 管理系统版本 |
| v1.0.0 | Initial Edition | 2026-02-01 | 初始版本 |

---

## 运维指南

### 日常维护
1. **数据库健康检查**: `GET /api/enhancement/database/health`
2. **系统资源监控**: `GET /api/enhancement/system/resources`
3. **性能分析**: `GET /api/enhancement/system/performance`
4. **集群状态**: `GET /api/enhancement/cluster/monitor`

### Git自动同步
```bash
# 一键同步 (提交+推送)
curl -X POST http://localhost:8888/api/enhancement/git/sync \
  -H "Content-Type: application/json" \
  -d '{"message": "日常同步"}'
```

### 故障排查
1. 查看 `/api/system/status` 获取系统状态
2. 查看 `/api/system/modules` 检查模块加载状态
3. 查看 `/api/enhancement/database/health` 检查数据库健康
4. 查看 `/api/enhancement/system/performance` 检查性能评分

### 备份策略
- 数据库自动备份 (每日/每周/每月)
- Git自动提交和推送
- 版本历史记录到数据库

---

## 许可证

MIT License

---

## 技术支持

如有问题，请通过 GitHub Issues 提交。
