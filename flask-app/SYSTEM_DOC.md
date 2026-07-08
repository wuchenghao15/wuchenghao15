# MTSCOS AI 智能考试系统 - 系统说明书

> 版本: v7.2.0 (Comprehensive Enhancement Edition)
> 更新日期: 2026-07-09
> 文档版本: 7.2

## 目录

1. [系统概述](#1-系统概述)
2. [系统架构](#2-系统架构)
3. [模块化启动系统](#3-模块化启动系统)
4. [分布式数据库](#4-分布式数据库)
5. [AI智能引擎矩阵](#5-ai智能引擎矩阵)
6. [题库系统](#6-题库系统)
7. [权限管理体系](#7-权限管理体系)
8. [AI集群与模型库](#8-ai集群与模型库)
9. [端口管理系统](#9-端口管理系统)
10. [集群管理系统](#10-集群管理系统)
11. [Git自动同步](#11-git自动同步)
12. [前端页面系统](#12-前端页面系统)
13. [移动端适配](#13-移动端适配)
14. [AI智能题目生成器](#14-ai智能题目生成器)
15. [AI智能学习路径推荐](#15-ai智能学习路径推荐)
16. [版本历史](#16-版本历史)
17. [API接口文档](#17-api接口文档)
18. [部署指南](#18-部署指南)

---

## 1. 系统概述

MTSCOS AI 智能考试系统是一个基于 Flask 框架的分布式智能考试管理平台。v7.2.0 版本代号 "Comprehensive Enhancement Edition"（全面增强版），主要新增了题库拓展、权限矩阵完善、AI集群升级、端口管理增强、集群多维度管理等特性。

### 核心特性
- 模块化启动系统（8阶段配置加载 + 6阶段功能模块加载）
- 分布式数据库架构（16+ 独立数据库）
- AI智能引擎矩阵（20+ 核心引擎，60+ AI员工）
- 完整题库系统（成人教育 + K12全科目，37,000+ 题目）
- 精细化RBAC权限管理体系（12角色，细粒度权限控制）
- AI集群与模型库管理（15+ AI模型，节点动态扩展）
- 多维度端口管理（21个端口配置，扫描/分配/预留/释放）
- 集群管理系统（4种负载均衡策略，健康检查，自动故障转移）
- Git/GitHub自动同步
- 响应式前端布局（移动端适配）

---

## 2. 系统架构

### 2.1 目录结构
```
flask-app/
├── app.py                     # 应用主入口
├── modular_start.py           # 模块化启动脚本
├── startup_modules/           # 模块化启动器
│   ├── db_config_loader.py   # 数据库配置加载器（8阶段）
│   ├── core_init.py           # 核心初始化（4步骤）
│   └── module_loader.py       # 功能模块加载器（6阶段）
├── ai_engines/                # AI引擎模块（20+核心引擎）
│   ├── ai_cluster_manager.py         # AI集群管理
│   ├── ai_employee_manager.py        # AI员工管理
│   ├── ai_question_bank.py           # 题库生成引擎
│   ├── adaptive_learning_engine.py   # 自适应学习引擎
│   ├── knowledge_graph_engine.py     # 知识图谱引擎
│   ├── reward_achievement_engine.py  # 奖励成就引擎
│   ├── wrong_book_engine.py          # 错题本智能引擎
│   ├── learning_prediction_engine.py # 学习预测分析引擎
│   ├── ai_tutor_engine.py            # AI助教答疑引擎
│   ├── collaborative_learning_engine.py # 协作学习引擎
│   ├── teaching_evaluation_engine.py # 智能教学评估引擎
│   ├── resource_recommendation_engine.py # 学习资源推荐引擎
│   ├── learning_report_engine.py      # 学情分析报告引擎
│   ├── homework_grading_engine.py    # 智能作业批改引擎
│   ├── home_school_communication_engine.py # 家校沟通引擎
│   ├── gamification_engine.py        # 学习游戏化引擎
│   ├── intelligent_warning_engine.py # 智能预警引擎
│   ├── ai_question_authoring_engine.py # AI辅助出题引擎
│   ├── learning_visualization_engine.py # 学习数据可视化引擎
│   ├── learning_diagnosis_engine.py  # 智能学习诊断引擎
│   ├── knowledge_base_engine.py      # 智能知识库引擎
│   └── classroom_interaction_engine.py # AI课堂互动引擎
├── app/                       # 应用模块
│   ├── api/                   # API接口（120+个）
│   ├── ai/                    # AI子模块
│   ├── blueprints/            # 蓝图模块
│   ├── services/              # 服务模块
│   │   ├── cluster_service.py       # 集群管理服务
│   │   └── port_monitor_service.py  # 端口监控服务
│   ├── models/                # 数据模型（20+个）
│   │   ├── permission.py            # 权限模型
│   │   └── role.py                  # 角色模型
│   ├── middlewares/           # 中间件
│   ├── routes/                # 路由模块
│   ├── containers/            # 容器模块
│   │   └── user_container.py        # 用户容器
│   └── utils/                 # 工具模块
│       └── permission_manager.py    # 权限管理器
├── split_databases/           # 分布式数据库（16+个）
├── templates/                 # HTML模板（100+个）
├── static/                    # 静态资源
├── scripts/                   # 脚本工具
│   └── expand_question_bank.py # 题库拓展脚本
└── docs/                      # 文档目录
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
2. API接口模块（后台线程加载，120+个）
3. 蓝图模块（后台线程加载）
4. 服务模块（同步加载）
5. AI引擎模块（后台线程加载）
6. 中间件模块（同步加载）

#### 阶段4: 系统管理API注册
#### 阶段5: 启动Web服务器

### 3.2 启动命令
```bash
# 标准启动
python app.py --port 8888

# 调试模式
python app.py --port 8888 --debug

# 指定主机
python app.py --host 0.0.0.0 --port 9000

# SSL模式
python app.py --ssl --ssl-port 8443
```

---

## 4. 分布式数据库

### 4.1 数据库列表（16+个）
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
| mtscos.db | 端口监控数据 |

### 4.2 智能数据库路由
通过 `smart_db_router.py` 实现 SQL 查询自动路由到正确的分布式数据库。

---

## 5. AI智能引擎矩阵

### 5.1 核心引擎列表（20个）
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

### 5.2 AI员工（60+）
- 题目生成员工、考试分析员工、消息管理员工、奖励系统员工
- 练习学习员工、日语听力音频生成专家AI、AutomationPlanAgent
- 配置管理AI员工、端口监控AI员工、Git管理AI员工等

### 5.3 AI Agent（8+）
- 系统监控Agent、数据备份Agent、智能调度器、版本管理Agent
- Git同步Agent、自愈Agent、API管理Agent、数据库Agent

---

## 6. 题库系统

### 6.1 科目覆盖
#### 成人教育科目（9个）
- 成人高考语文、成人高考数学、成人高考英语
- 成人高考政治、成人高考物理、成人高考化学
- 成人高考历史、成人高考地理、成人高考医学综合

#### K12科目（28个）
- 小学：语文、数学、英语、科学（4个）
- 初中：语文、数学、英语、物理、化学、生物、历史、地理、道德与法治（9个）
- 高中：语文、数学、英语、物理、化学、生物、历史、地理、政治（9个）
- 通用：语文、数学、英语、物理、化学、生物、历史、地理、政治、科学、日语（11个）

### 6.2 题型支持
- 单选题、多选题、判断题、填空题、简答题、论述题、听力题

### 6.3 题库规模
- 每个科目生成1000道题目
- 总计：37个科目 × 1000题 = 37,000+ 题目

### 6.4 难度分级
- 简单（easy）、中等（medium）、困难（hard）

---

## 7. 权限管理体系

### 7.1 角色体系（12个角色）
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
| super_admin | 超级管理员 | 13 | 完整管理权限 |
| hardware_admin | 硬件管理员 | 14 | 最高权限，需加密狗认证 |

### 7.2 权限矩阵
每个角色拥有独立的权限列表，涵盖：
- 用户管理：view_profile, manage_account, change_password
- 考试系统：view_exams, take_exam, view_results, manage_exams
- 学习系统：view_learning_records, use_ai_chat, view_notifications
- 管理功能：view_dashboard, manage_users, manage_settings, manage_routes
- AI系统：manage_ai_employees, manage_ai_models, view_ai_stats
- 集群管理：manage_cluster, view_cluster_stats, manage_nodes
- 端口管理：manage_ports, view_port_stats, allocate_port

### 7.3 权限装饰器
- `@require_login` - 需要登录
- `@require_admin` - 需要管理员权限
- `@require_super_admin` - 需要超级管理员权限
- `@require_role(role)` - 需要指定角色权限

---

## 8. AI集群与模型库

### 8.1 AI模型配置（15个模型）
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

### 8.2 模型性能指标
每个模型记录：
- 延迟（latency）：响应时间（秒）
- 吞吐量（throughput）：每秒处理请求数
- 准确率（accuracy）：回答准确率百分比

### 8.3 集群管理功能
- 节点动态扩展
- 负载均衡策略
- 健康检查与自动故障转移
- 模型版本管理
- 性能监控与日志

---

## 9. 端口管理系统

### 9.1 端口配置（21个端口）
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

### 9.2 端口管理功能
- **端口扫描**：扫描指定范围端口状态
- **端口分配**：自动分配可用端口
- **端口预留**：为特定服务预留端口
- **端口释放**：释放不再使用的端口
- **使用统计**：端口使用情况统计
- **参数匹配**：配置参数验证与匹配
- **自动修复**：端口异常自动修复

### 9.3 API接口
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

## 10. 集群管理系统

### 10.1 节点管理
- 节点注册与注销
- 节点状态监控（ACTIVE/HEALTHY/UNHEALTHY/DOWN/MAINTENANCE）
- 节点角色管理（MASTER/SLAVE/STANDBY）
- 节点权重配置

### 10.2 负载均衡策略（4种）
| 策略 | 说明 | 适用场景 |
|------|------|---------|
| ROUND_ROBIN | 轮询 | 节点性能相近 |
| LEAST_CONNECTIONS | 最小连接数 | 节点性能差异大 |
| WEIGHTED_ROUND_ROBIN | 加权轮询 | 需要按权重分配 |
| IP_HASH | IP哈希 | 需要会话保持 |

### 10.3 健康检查
- 心跳超时检测（30秒）
- HTTP健康检查（/health端点）
- 自动故障转移
- 主节点自动提升

### 10.4 数据复制
- 主从数据复制
- 实时同步机制

### 10.5 API接口
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

## 11. Git自动同步

### 11.1 自动同步功能
- 变更检测
- 自动提交（带审批机制）
- 自动推送
- 定时同步（每5分钟）

### 11.2 安全机制
- 保护分支禁止强制推送（main/master/develop）
- 大规模提交需审批（50+文件变更）
- 操作记录审计
- 差异对比保存

### 11.3 API接口
| 接口 | 方法 | 说明 |
|------|------|------|
| /api/git/status | GET | Git状态 |
| /api/git/commit | POST | 提交更改 |
| /api/git/push | POST | 推送到远程 |
| /api/git/pull | POST | 从远程拉取 |
| /api/git/sync | POST | 同步并备份 |
| /api/git/history | GET | 获取操作历史 |

---

## 12. 前端页面系统

### 12.1 模板系统
- 100+ HTML模板文件
- Jinja2模板引擎
- 全局模板函数（角色名称、日期格式化等）

### 12.2 布局优化
- 左侧固定标签栏（260px）+ 右侧Tab切换内容区
- 响应式设计，支持移动端适配
- 渐变进度条、统计卡片、实时日志

### 12.3 主要页面
| 页面 | 路由 | 说明 |
|------|------|------|
| 超级管理员仪表盘 | /super_admin_dashboard | 10个标签页，系统监控与管理 |
| 普通管理员仪表盘 | /admin_dashboard | 独立界面，只读权限 |
| AI自动完善拓展 | /ai_auto_expand | AI拓展管理页面 |
| 学生门户 | /student_portal | 学生统一入口 |
| 考试系统 | /exam_system | 考试列表与管理 |
| 测试系统 | /exam_system/tests | 日常练习与测试 |

---

## 13. 移动端适配

### 13.1 响应式布局
- 媒体查询适配不同屏幕尺寸
- 触控友好的按钮尺寸
- 滑动手势支持
- 移动端专属导航

### 13.2 移动端优化
- 页面宽度自适应
- 组件缩放适配
- 加载性能优化
- 离线缓存支持

### 13.3 手机管理端
- 独立路由：/admin_app
- 移动端专属界面设计
- 简化的操作流程
- 触控优化的交互

---

## 14. AI智能题目生成器

### 14.1 功能概述
AI智能题目生成器是一个基于文本内容自动生成考试题目的智能系统。用户输入任意文本内容，系统会自动分析文本、提取关键点，并生成多种题型的考试题目。

### 14.2 核心特性
- **文本分析**：自动检测文本科目（语文、数学、英语、物理、化学、生物、历史、地理、政治、科学、日语）
- **关键点提取**：从文本中提取关键信息作为题目基础
- **6种题型生成**：单选题、多选题、判断题、填空题、简答题、论述题
- **难度控制**：简单/中等/困难三级难度
- **自动保存**：支持将生成的题目保存到题库数据库

### 14.3 技术实现
- 服务文件：`app/services/ai_question_generation_service.py`
- API文件：`app/api/ai_generation_api.py`
- 前端页面：`templates/admin_app/ai_question_generator.html`
- 页面路由：`/admin/ai-question-generator`

### 14.4 API接口
| 接口 | 方法 | 说明 |
|------|------|------|
| /api/ai/generate-questions | POST | 从文本生成题目 |
| /api/ai/generate-questions/save | POST | 保存生成的题目 |
| /api/ai/generate-questions/stats | GET | 获取生成统计 |
| /api/ai/generate-questions/subjects | GET | 获取科目列表 |
| /api/ai/generate-questions/types | GET | 获取题型列表 |
| /api/ai/detect-subject | POST | 自动检测科目 |
| /api/ai/extract-key-points | POST | 提取关键点 |

### 14.5 使用示例
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

## 15. AI智能学习路径推荐

### 15.1 功能概述
AI智能学习路径推荐系统分析学生学习数据，识别薄弱环节，生成个性化学习路径，帮助学生高效提升学习成绩。

### 15.2 核心特性
- **薄弱环节分析**：基于错题数据分析各知识点错误率，分级标记（紧急加强/重点复习/巩固练习/日常练习）
- **学习路径生成**：根据薄弱环节自动生成1-30天的个性化学习路径
- **知识图谱**：9个科目完整知识体系，每个科目5个主题，共45个主题
- **学习进度追踪**：按科目统计学习进度

### 15.3 技术实现
- 服务文件：`app/services/ai_study_path_service.py`
- API文件：`app/api/study_path_api.py`
- 前端页面：`templates/admin_app/ai_study_path.html`
- 页面路由：`/admin/ai-study-path`

### 15.4 API接口
| 接口 | 方法 | 说明 |
|------|------|------|
| /api/ai/study-path/generate | POST | 生成学习路径 |
| /api/ai/study-path/analyze | POST | 分析薄弱环节 |
| /api/ai/study-path/subjects | GET | 获取科目列表 |
| /api/ai/study-path/knowledge-graph | GET | 获取知识图谱 |
| /api/ai/study-path/progress | POST | 获取学习进度 |

### 15.5 使用示例
```json
POST /api/ai/study-path/generate
{
    "user_id": 1,
    "subject": "数学",
    "days": 7
}
```

---

## 16. 版本历史

| 版本 | 代号 | 日期 | 主要特性 |
|------|------|------|---------|
| v7.2.0 | Comprehensive Enhancement Edition | 2026-07-09 | 题库拓展(37K题)、权限矩阵(12角色)、AI集群(15模型)、端口管理(21端口)、集群管理(4种策略)、AI题目生成器、AI学习路径推荐、性能监控API |
| v7.1.0 | Dashboard Refactor Edition | 2026-07-08 | 仪表盘重构、AI拓展系统、629路由、14数据库481表、41AI员工 |
| v7.0.0 | Intelligent Modular Edition | 2026-07-07 | 模块化启动、AI智能检索、API/路由数据库管理 |
| v6.0.0 | Distributed Database Edition | 2026-07-06 | 分布式数据库架构（13个独立数据库） |
| v5.0.0 | AI Integration Edition | 2026-06-01 | AI集成版本，AI助教引擎 |
| v4.0.0 | Exam System Edition | 2026-05-01 | 在线考试和监考功能 |
| v3.0.0 | Learning Edition | 2026-04-01 | 学习管理系统 |
| v2.0.0 | Admin Edition | 2026-03-01 | 权限和用户管理 |
| v1.0.0 | Initial Edition | 2026-02-01 | 初始版本 |

---

## 15. API接口文档

### 15.1 系统管理API
| 接口 | 方法 | 说明 |
|------|------|------|
| /api/system/status | GET | 获取系统完整状态 |
| /api/system/configs | GET | 获取系统配置 |
| /api/system/configs/reload | POST | 重新加载配置 |
| /api/system/modules | GET | 获取模块加载状态 |

### 15.2 认证API
| 接口 | 方法 | 说明 |
|------|------|------|
| /api/auth/login | POST | 用户登录 |
| /api/auth/register | POST | 用户注册 |
| /api/auth/logout | GET/POST | 用户登出 |
| /api/auth/check | GET | 检查登录状态 |

### 15.3 AI员工API
| 接口 | 方法 | 说明 |
|------|------|------|
| /api/ai_employees/status | GET | AI员工状态 |
| /api/ai_employees/list | GET | AI员工列表 |
| /api/ai_employees/register | POST | 注册AI员工 |
| /api/ai_employees/auto_extend | POST | AI自动拓展 |

### 15.4 路由管理API
| 接口 | 方法 | 说明 |
|------|------|------|
| /api/routes/list | GET | 获取路由列表 |
| /api/routes/reload | POST | 重新加载路由 |
| /api/routes/check | GET | 检查路由状态 |

### 15.5 版本管理API
| 接口 | 方法 | 说明 |
|------|------|------|
| /api/version/status | GET | 版本状态 |
| /api/version/check | GET | 版本检查 |
| /api/version/upgrade | POST | 版本升级 |

### 15.6 监控API
| 接口 | 方法 | 说明 |
|------|------|------|
| /api/monitoring/stats | GET | 系统监控统计 |
| /api/monitoring/errors | GET | 错误统计 |
| /api/monitoring/logs | GET | 监控日志 |

---

## 16. 部署指南

### 16.1 环境要求
- Python 3.8+
- SQLite 3.30+
- Git
- 推荐：Redis、MySQL（可选）

### 16.2 安装步骤
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

### 16.3 配置说明
- 配置文件：`app/config/config.py`
- 数据库路径：`split_databases/`
- 静态资源：`static/`
- 模板文件：`templates/`

### 16.4 安全建议
- 生产环境启用HTTPS
- 设置管理员密码（非默认值）
- 定期备份数据库
- 监控系统日志

---

*文档结束 - MTSCOS AI 智能考试系统 v7.2.0*