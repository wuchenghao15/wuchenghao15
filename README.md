<div align="center">

  ![MTSCOS AI](https://img.shields.io/badge/MTSCOS-AI_Intelligent_System-blue?style=for-the-badge&logo=ai)
  ![Version](https://img.shields.io/badge/Version-6.0.0-blue?style=for-the-badge)
  ![Python](https://img.shields.io/badge/Python-3.8+-yellow?style=for-the-badge&logo=python)
  ![Flask](https://img.shields.io/badge/Flask-2.3.3-lightgrey?style=for-the-badge&logo=flask)
  ![License](https://img.shields.io/badge/License-MIT-red?style=for-the-badge)
  ![Stars](https://img.shields.io/github/stars/wuchenghao15/MTSCOS-AI?style=for-the-badge)
  ![Forks](https://img.shields.io/github/forks/wuchenghao15/MTSCOS-AI?style=for-the-badge)
  ![Last Commit](https://img.shields.io/github/last-commit/wuchenghao15/MTSCOS-AI?style=for-the-badge)

</div>

---

<div align="center">

# 🧠 MTSCOS AI 智能管理系统
## MTSCOS AI Intelligent Management System

**AI-Driven Intelligent Management Platform | AI驱动的智能管理平台**

[简体中文](#-简体中文) • [English](#-english) • [Features](#-核心功能) • [Architecture](#-系统架构) • [Quick Start](#-快速开始) • [API](#-api文档)

</div>

---

<div align="center">

### 🌟 最新版本 v6.0.0 - 分布式数据库版 🚀
**Distributed Database Edition - 智能数据库拆分与系统全面升级**

</div>

---

## 📖 简体中文

### 🎯 项目简介

**MTSCOS AI 智能管理系统**是一个基于 Flask 框架的全栈 AI 驱动智能管理平台，深度融合机器学习、自然语言处理、知识图谱和自动化运维等前沿技术。系统采用模块化微服务架构，支持多角色权限管理、智能运维自动化、AI员工协作和知识脑库自学习能力。

> 💡 **核心理念**：从"自动化"到"智能化"，从"被动响应"到"主动预见"，让AI真正成为系统的大脑。

---

### ✨ 核心亮点

<table>
  <tr>
    <td align="center" width="16.66%">
      <img src="https://img.shields.io/badge/🧠_AI脑库-知识驱动-blue?style=for-the-badge" width="100%"/>
    </td>
    <td align="center" width="16.66%">
      <img src="https://img.shields.io/badge/🤖_AI员工-自主协作-green?style=for-the-badge" width="100%"/>
    </td>
    <td align="center" width="16.66%">
      <img src="https://img.shields.io/badge/⚡_主动AI-预见未来-orange?style=for-the-badge" width="100%"/>
    </td>
    <td align="center" width="16.66%">
      <img src="https://img.shields.io/badge/🔐_数据完整性-安全可靠-red?style=for-the-badge" width="100%"/>
    </td>
    <td align="center" width="16.66%">
      <img src="https://img.shields.io/badge/📚_K12教育-全学段覆盖-purple?style=for-the-badge" width="100%"/>
    </td>
    <td align="center" width="14.28%">
      <img src="https://img.shields.io/badge/🎓_智能课堂-互动教学-pink?style=for-the-badge" width="100%"/>
    </td>
    <td align="center" width="14.28%">
      <img src="https://img.shields.io/badge/📊_智能评估-个性化-teal?style=for-the-badge" width="100%"/>
    </td>
  </tr>
</table>

---

### 📊 v5.3.0 新功能 - 权限增强版 ⭐⭐⭐

**权限管理全面升级，新增29项权限规则，实现精细化角色访问控制**

#### 1. 权限管理系统 (Permission Management System) v2.0
| 特性 | 描述 |
|------|------|
| 🛡️ 29项权限规则 | 覆盖AI功能、学习诊断、智能评估、知识库、审计等全功能 |
| 🎯 14种角色等级 | guest→user→student→teacher→admin→super_admin→hardware_admin |
| 🔐 6级访问控制 | NONE/VIEW/EDIT/MANAGE/ADMIN/SUPER_ADMIN |
| 📋 动态权限分配 | 支持角色权限动态绑定与撤销 |
| 🔗 角色继承体系 | 高级角色自动继承低级角色权限 |

#### 2. 权限分类体系
| 分类 | 权限项 | 说明 |
|------|--------|------|
| 👁️ VIEW_ONLY | 6项 | 仪表盘、设置、日志、监控、学习分析、审计日志查看 |
| 👥 USER_MANAGEMENT | 2项 | 用户管理、删除用户 |
| ⚙️ SYSTEM_ADMIN | 5项 | 数据库管理、路由管理、系统配置、安全配置、数据完整性 |
| 🤖 AI_FEATURES | 7项 | AI聊天、学习诊断、智能评估、学习路径、AI推荐、知识库、课堂互动 |
| 👨‍💻 AI_ADMIN | 3项 | AI员工管理、脑库管理、主动AI管理 |
| 📚 EXAM_FEATURES | 4项 | 参加考试、创建考试、管理考试、题库管理 |
| 📖 LEARNING_FEATURES | 3项 | 学习记录管理、错题本管理、报表生成 |

#### 3. 审计日志系统 (Audit Logging System) v1.0
| 特性 | 描述 |
|------|------|
| 📝 完整操作记录 | 登录/登出/授权/撤销/访问拒绝全记录 |
| ⏱️ 实时审计 | 操作实时记录，支持实时告警 |
| 🔍 精准查询 | 支持按用户、操作类型、时间范围筛选 |
| 📊 可视化分析 | 审计统计报表与趋势分析 |
| 🔒 安全存储 | 90天日志保留，加密存储 |

#### 4. 安全增强 (Security Enhancements)
| 特性 | 描述 |
|------|------|
| 🔐 强密码策略 | 最小8位、复杂度要求 |
| 🔑 会话安全 | 30分钟超时、自动锁定 |
| 📁 数据加密 | 敏感数据AES-256加密 |
| 🚨 威胁检测 | 异常登录检测、访问拒绝告警 |

---

### 📊 v5.2.0 新功能 - 智能评估版 ⭐⭐⭐

**第9轮AI引擎拓展完成，新增三大核心引擎，实现真正的个性化智能教育**

#### 1. 智能评估分析引擎 (Intelligent Evaluation Engine) v1.0
| 特性 | 描述 |
|------|------|
| 🎯 6维度评估 | 知识掌握 / 能力运用 / 思维品质 / 创新能力 / 实践应用 / 学科素养 |
| 📊 4级评估等级 | 优秀(A) / 良好(B) / 合格(C) / 待提升(D) |
| 📈 多层级报告 | 学生报告 / 班级报告 / 年级报告 / 学科报告 |
| 🔮 AI预测分析 | 基于历史数据预测未来表现，提前预警 |
| 📉 成长轨迹 | 历次评估对比，可视化成长曲线 |

#### 2. 个性化学习路径引擎 (Personalized Learning Path Engine) v1.0
| 特性 | 描述 |
|------|------|
| 🗺️ 3种路径算法 | 知识图谱 / 能力进阶 / 兴趣驱动 |
| 🎨 VARK学习风格 | 视觉型 / 听觉型 / 动觉型 / 读写型 |
| 📏 5级难度自适应 | 入门 / 基础 / 进阶 / 提高 / 挑战 |
| 🎯 学习目标管理 | 短期 / 中期 / 长期目标设定与追踪 |
| ⏱️ 进度实时追踪 | 节点完成状态 / 总体进度 / 预计时间 |

#### 3. AI智能推荐引擎 (AI Smart Recommendation Engine) v1.0
| 特性 | 描述 |
|------|------|
| 🎯 5种推荐类型 | 题目 / 课程 / 资源 / 路径 / 同伴推荐 |
| 🤖 4种推荐算法 | 协同过滤 / 基于内容 / 知识图谱 / 混合推荐 |
| 👤 用户行为分析 | 学习行为记录 / 偏好画像 / 学习模式识别 |
| 💡 推荐理由 | 每条推荐附带可解释的理由 |
| 📊 效果评估 | 点击率 / 完成率 / 满意度统计 |

#### 📚 题库系统升级
- **新增高中学段** - 高一数学 / 物理 / 化学3大学科
- **9道高中高质量题目** - 集合函数 / 运动学 / 电解质等知识点
- **题库总量** - 27题，覆盖初高中全学段

---

### 🎓 v5.1.0 新功能 - 智能课堂版 ⭐⭐⭐

**第8轮AI引擎拓展完成，新增三大核心教学引擎，全面覆盖教学全流程**

#### 1. 智能学习诊断引擎 (Learning Diagnosis Engine) v1.0
| 特性 | 描述 |
|------|------|
| 🎯 掌握度模型 | 4级掌握度 - 完全掌握 / 熟练掌握 / 初步了解 / 薄弱环节 |
| 📊 能力评估 | 5维能力 - 知识掌握 / 概念理解 / 应用能力 / 解题能力 / 拓展能力 |
| 🔄 自适应测试 | 根据答题情况动态调整题目难度，精准定位薄弱点 |
| 📈 提升计划 | 基于诊断结果生成个性化学习路径与建议 |
| 📑 多维报告 | 个人报告 / 班级报告 / 年级报告 / 学科对比分析 |

#### 2. 智能知识库引擎 (Knowledge Base Engine) v1.0
| 特性 | 描述 |
|------|------|
| 📚 知识类型 | 8种 - 概念 / 公式 / 定理 / 解题方法 / 例题 / 总结 / 实验 / 词汇 |
| 🗂️ 分类体系 | 学科-年级-章节-小节四级分类，支持多维度检索 |
| 🔍 语义检索 | 倒排索引 + 关键词提取 + 重要性加权排序 |
| 🌐 知识图谱 | 节点-边关系模型，支持深度关联查询与知识导航 |
| 📝 版本管理 | 知识条目变更历史与版本追溯 |
| 📖 学习追踪 | 学习行为记录 / 理解度评估 / 学习笔记管理 |

#### 3. AI课堂互动引擎 (Classroom Interaction Engine) v1.0
| 特性 | 描述 |
|------|------|
| 🎯 活动类型 | 7种 - 随机点名 / 随堂测验 / 抢答竞赛 / 投票问卷 / 分组讨论 / 头脑风暴 / 课堂小测 |
| 👥 分组策略 | 5种 - 随机 / 能力均衡 / 同质 / 兴趣 / 自由组合 |
| ✏️ 实时答题 | 单选 / 多选 / 判断 / 填空，自动判分与统计 |
| ⚡ 毫秒抢答 | 精确时间戳排名，支持多轮抢答与积分 |
| 🏆 积分体系 | 奖励激励 / 积分排行 / 历史记录 / 成就徽章 |
| 📋 模板库 | 可复用活动配置，一键创建标准化课堂活动 |

#### 📚 题库系统升级
- **6大学科覆盖** - 数学 / 语文 / 英语 / 物理 / 化学 / 历史
- **高质量种子题目** - 初中学段，含详细解析与知识点标注
- **结构化管理** - 难度分级 / 知识点标签 / 答案解析 / 分值配置

---

### 🧠 AI脑库系统 (v1.0) ⭐⭐⭐

**知识就是力量，脑库就是AI的灵魂**

#### 10种知识类型
| 类型 | 描述 | 应用场景 |
|------|------|----------|
| 📝 经验知识 | 从实践中积累的经验 | 问题解决、决策参考 |
| 🔄 模式知识 | 识别出的规律模式 | 预测分析、异常检测 |
| 📋 规则知识 | 提炼的规则和原则 | 自动判断、合规检查 |
| 💡 解决方案 | 完整的问题解法 | 故障修复、优化方案 |
| 🔮 洞见知识 | 深度分析的洞察 | 战略决策、趋势判断 |
| ⭐ 最佳实践 | 经过验证的最优方案 | 标准化、质量保证 |
| 📖 教训知识 | 失败中学习的教训 | 风险规避、错误预防 |
| 💭 启发式知识 | 经验法则和直觉 | 快速决策、探索创新 |
| 📊 预测性知识 | 基于数据的预测 | 趋势预判、资源规划 |
| 🔗 因果知识 | 因果关系分析 | 根因分析、效果评估 |

#### 11个知识领域
错误修复 • 性能优化 • 安全 • 数据库 • 前端 • 后端 • 运维 • AI/ML • 用户体验 • 业务 • 通用

#### 5种智能触发类型
阈值评估 • 模式匹配 • 状态变化 • 时间周期 • 事件驱动

> **自动学习进化**：触发条件自动从事件中学习，不断优化置信度和优先级

---

### 🤖 AI员工系统 (v2.0)

**不是一个AI在战斗，而是一支AI团队**

| 角色 | 职责 | 能力等级 |
|------|------|----------|
| 👨‍💻 前端修复专家 | 页面美化、CSS修复、交互优化 | ⭐⭐⭐⭐⭐ |
| 🔧 后端架构师 | API设计、性能优化、架构改进 | ⭐⭐⭐⭐⭐ |
| 🗄️ 数据库管理员 | 查询优化、索引设计、数据安全 | ⭐⭐⭐⭐ |
| 🔐 安全审计师 | 漏洞扫描、安全加固、合规检查 | ⭐⭐⭐⭐ |
| 📊 监控分析师 | 性能监控、异常检测、趋势预测 | ⭐⭐⭐⭐ |
| 📚 知识管理员 | 脑库维护、知识整合、质量评估 | ⭐⭐⭐⭐⭐ |
| 🎯 主动发现者 | 需求挖掘、问题预见、改进建议 | ⭐⭐⭐⭐⭐ |

**协作能力**：事件总线通信 • 任务自动分配 • 结果自动汇总 • 知识自动共享

---

### ⚡ 主动AI系统 (v1.0)

**从被动触发到主动运作，从"要我做"到"我要做"**

#### 5级主动性等级
| 等级 | 名称 | 描述 |
|------|------|------|
| L1 | PASSIVE 被动 | 仅在明确指令下行动 |
| L2 | REACTIVE 反应 | 响应事件和告警 |
| L3 | PROACTIVE 主动 | 主动发现问题和机会 |
| L4 | SELF_DRIVEN 自驱 | 自我设定目标和优先级 |
| L5 | AUTONOMOUS 自主 | 完全自主决策和执行 |

#### 核心能力
- 🔍 **自主需求发现** - 8个发现模块持续扫描系统
- 📅 **智能任务调度** - 优先级评估、资源分配、依赖管理
- 📈 **自我学习优化** - 从结果中学习，持续改进策略
- 🤝 **协作式工作流** - 多AI员工协同完成复杂任务

---

### 🔐 数据完整性中心 (v1.0)

**数据是系统的血液，完整性是生命的保障**

#### 12种数据校验规则
必填校验 • 类型校验 • 长度校验 • 范围校验 • 正则模式 • 枚举值 • 邮箱格式 • 手机号 • URL格式 • SQL注入防护 • XSS防护 • 自定义规则

#### 四大保障体系
| 体系 | 功能 |
|------|------|
| ✅ 合法性校验 | 数据格式、业务规则、安全过滤 |
| 🎯 唯一性约束 | 内存缓存加速 + 数据库级双重验证 |
| 🔒 并发控制 | 共享锁/排他锁/乐观锁/事务管理 |
| 📝 审计监控 | 完整变更日志、违规统计、实时告警 |

---

### 📚 教育系统 (v4.0)

**K12全学段覆盖，AI驱动个性化学习**

| 模块 | 功能 | 版本 |
|------|------|------|
| 📖 学习系统 | 课程学习、智能推荐、学习路径 | v3.0 |
| ✍️ 考试系统 | 在线考试、自动阅卷、错题本 | v3.2 |
| 👨‍🏫 教师后台 | 学情分析、成绩管理、教学备课 | v2.0 |
| 📋 教学内容 | 大纲管理、教案管理、规则引擎 | v1.0 |
| 🏆 成就系统 | 升级体系、徽章奖励、排行榜 | v2.0 |

**支持9年义务教育 + 3年高中教育全覆盖**

---

### 🏗 系统架构

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          MTSCOS AI 系统架构                               │
├─────────────────────────────────────────────────────────────────────────┤
│  🌐 接入层 Access Layer                                                 │
│  Web UI • Mobile UI • REST API • WebSocket                              │
├─────────────────────────────────────────────────────────────────────────┤
│  🎯 业务层 Business Layer                                               │
│  教育系统 • 权限管理 • 版本管理 • 内容管理 • 安全中心                    │
├─────────────────────────────────────────────────────────────────────────┤
│  🧠 AI引擎层 AI Engine Layer  ⭐ NEW                                   │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐                  │
│  │  AI脑库   │ │ AI员工   │ │ 主动AI   │ │ 自学习   │                  │
│  │ Knowledge│ │ Employee │ │ Proactive│ │ Learning │                  │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘                  │
├─────────────────────────────────────────────────────────────────────────┤
│  🔐 保障层 Assurance Layer                                              │
│  数据完整性 • 安全防护 • 审计监控 • 并发控制                            │
├─────────────────────────────────────────────────────────────────────────┤
│  💾 数据层 Data Layer                                                   │
│  SQLite • Redis Cache • File Storage • Knowledge Graph                 │
└─────────────────────────────────────────────────────────────────────────┘
```

---

### 📁 项目结构

```
MTSCOS_AI_Project/
├── 📂 flask-app/                    # 🚀 主应用目录
│   ├── 📂 app/                       # 应用核心
│   │   ├── 📂 ai/                    # 🧠 AI模块 (NEW)
│   │   │   ├── knowledge_brain_bank.py    # AI脑库系统
│   │   │   ├── proactive_ai_system.py     # 主动AI系统
│   │   │   └── ai_employee_enhanced_system.py  # AI员工增强
│   │   ├── 📂 api/                   # 🔌 API接口
│   │   ├── 📂 models/                # 💾 数据模型
│   │   ├── 📂 utils/                 # 🛠️ 工具模块
│   │   └── 📂 middlewares/           # 🔒 中间件
│   ├── 📂 templates/                 # 🎨 前端模板
│   └── app.py                        # 应用入口
├── 📂 scripts/                       # 📜 脚本工具
│   ├── 📂 ai/                        # AI相关脚本
│   ├── 📂 database/                  # 数据库脚本
│   ├── 📂 security/                  # 安全脚本
│   └── 📂 git/                       # Git工具
├── 📂 docs/                          # 📚 文档目录
│   └── 📂 reports/                   # 项目报告
├── 📄 README.md                      # 项目说明 (本文件)
├── 📄 CHANGELOG.md                   # 更新日志
├── 📄 VERSION                        # 版本信息
└── 📄 LICENSE                        # 许可证
```

---

### 🚀 快速开始

#### 环境要求

| 依赖 | 最低版本 | 推荐版本 |
|------|----------|----------|
| Python | 3.8+ | 3.11 |
| pip | 21.0+ | 最新版 |
| SQLite | 3.x | 3.39+ |

#### 安装步骤

```bash
# 1. 克隆仓库
git clone https://github.com/wuchenghao15/MTSCOS-AI.git
cd MTSCOS-AI/flask-app

# 2. 安装依赖
pip install -r requirements.txt

# 3. 初始化数据库
python init.py

# 4. 启动服务
python app.py --port 8888
```

#### 访问地址

| 页面 | 地址 | 说明 |
|------|------|------|
| 🌐 主站 | http://localhost:8888 | 系统首页 |
| 🔐 管理后台 | http://localhost:8888/admin_app | 管理员面板 |
| ⭐ 超级管理员 | http://localhost:8888/super_admin_dashboard | 超级管理仪表盘 |
| 📚 API文档 | http://localhost:8888/api/docs | API接口文档 |

---

### 🔌 API文档

#### 核心API模块

| 模块 | 接口数 | 前缀 |
|------|--------|------|
| 🧠 AI脑库 | 18 | `/api/brain-bank` |
| ⚡ 主动AI | 15+ | `/api/proactive-ai` |
| 🤖 AI员工 | 20+ | `/api/ai-employee` |
| 🔐 数据完整性 | 20+ | `/api/data-integrity` |
| 👤 用户认证 | 10+ | `/api/auth` |
| 📚 考试系统 | 15+ | `/api/exam` |

#### 快速测试

```bash
# 检查系统状态
curl http://localhost:8888/api/brain-bank/status

# 获取AI脑库统计
curl http://localhost:8888/api/brain-bank/stats

# 搜索知识
curl -X POST http://localhost:8888/api/brain-bank/knowledge/search \
  -H "Content-Type: application/json" \
  -d '{"query": "性能优化", "limit": 5}'
```

---

### 🔒 安全特性

| 特性 | 描述 | 级别 |
|------|------|------|
| HTTPS强制 | 生产环境自动重定向HTTPS | 🔴 高级 |
| XSS防护 | 输入过滤 + 输出编码 | 🔴 高级 |
| CSRF令牌 | 跨站请求伪造防护 | 🟡 中级 |
| SQL注入 | 参数化查询 + 注入检测 | 🔴 高级 |
| 数据加密 | AES-256敏感数据加密 | 🔴 高级 |
| 权限控制 | 13级角色细粒度权限 | 🔴 高级 |
| 硬件认证 | 加密狗双重认证 | 🔴 高级 |
| 操作审计 | 完整操作日志追溯 | 🟡 中级 |
| 会话安全 | 30分钟超时自动锁定 | 🟡 中级 |

---

### 📊 系统统计

```
📈 当前版本:      v6.0.0
🤖 AI员工数量:    10+
🧠 知识类型:      10种
📚 知识领域:      11个
⚡ 触发类型:      5种
🔌 API接口:      460+
📄 模板文件:      130+
🔀 路由数量:      629+
📅 历史版本:      27+
🧠 AI引擎矩阵:   30+
📚 题库总量:      27+
🛡️ 权限规则:      50+项
👤 角色等级:      14种
📝 审计日志:      已启用
🗄️ 数据库:        13个(分布式)
```

---

### 🛣 发展路线图

#### ✅ 已完成 (v1.0 - v6.0)
- [x] v1.0 - 基础系统搭建
- [x] v2.0 - 考试系统上线
- [x] v3.0 - 学习系统集成
- [x] v3.4 - K12全学段 + 成就系统
- [x] v4.0 - 数据库加密 + 云端服务
- [x] v4.3 - 教学内容管理系统
- [x] v5.0 - AI脑库 + 主动AI + 数据完整性
- [x] v5.1 - 智能课堂版（学习诊断/知识库/课堂互动）
- [x] v5.2 - 智能评估版（智能评估/个性化路径/AI推荐）
- [x] v5.3 - 权限增强版（29项权限规则/审计日志/安全增强）
- [x] **v6.0 - 分布式数据库版（智能分库/权限升级/题库升级）** ⭐ 当前

#### 🔮 未来规划

| 版本 | 时间 | 核心特性 |
|------|------|----------|
| v6.1 | 2026 Q3 | 多语言国际化、语音交互 |
| v6.2 | 2026 Q3 | AI教师助手、智能辅导 |
| v6.3 | 2026 Q4 | 微服务架构、容器化部署 |
| v7.0 | 2027 Q1 | 边缘计算、IoT设备管理 |
| v7.5 | 2027 Q2 | 区块链存证、VR学习 |

---

### 👥 社区与贡献

我们欢迎各种形式的贡献！

| 方式 | 说明 |
|------|------|
| 🐛 提交Bug | [GitHub Issues](https://github.com/wuchenghao15/MTSCOS-AI/issues) |
| 💡 功能建议 | 提交 Feature Request |
| 🔧 代码贡献 | Fork 项目并提交 PR |
| 📚 文档改进 | 帮助完善Wiki和文档 |
| 🌍 翻译贡献 | 多语言国际化支持 |

**贡献指南**：
1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

---

### 📄 许可证

本项目采用 **MIT License** 开源许可。

Copyright © 2024-2026 MTSCOS AI Team. All rights reserved.

---

### 🙏 致谢

- Flask Framework & Community
- Python Open Source Community
- All Contributors & Supporters
- AI Technologies that make this possible

---

<div align="center">

### ⭐ 如果这个项目对您有帮助，请给我们一个Star！
### ⭐ If this project helps you, please give us a Star!

[![GitHub Stars](https://img.shields.io/github/stars/wuchenghao15/MTSCOS-AI?style=social)](https://github.com/wuchenghao15/MTSCOS-AI)
[![GitHub Forks](https://img.shields.io/github/forks/wuchenghao15/MTSCOS-AI?style=social)](https://github.com/wuchenghao15/MTSCOS-AI)
[![GitHub Watchers](https://img.shields.io/github/watchers/wuchenghao15/MTSCOS-AI?style=social)](https://github.com/wuchenghao15/MTSCOS-AI)

---

**Made with ❤️ by MTSCOS AI Team**

</div>

---

## 📖 English

### 🎯 Project Introduction

**MTSCOS AI Intelligent Management System** is a full-stack AI-driven intelligent management platform built on Flask framework, integrating cutting-edge technologies like machine learning, natural language processing, knowledge graphs, and automated operations.

> 💡 **Core Philosophy**: From "automation" to "intelligence", from "passive response" to "proactive anticipation", making AI the true brain of the system.

---

### ✨ Key Highlights

| Feature | Description |
|---------|-------------|
| 🧠 **Knowledge Brain Bank** | Knowledge-driven AI evolution with 10 knowledge types and 11 domains |
| 🤖 **AI Employee System** | Collaborative AI workforce with specialized roles |
| ⚡ **Proactive AI** | From passive trigger to active operation, 5 initiative levels |
| 🔐 **Data Integrity Center** | 12 validation rules, concurrency control, audit monitoring |
| 📚 **K12 Education** | Full grade coverage with AI-powered personalized learning |

---

### 🧠 Knowledge Brain Bank (v1.0) ⭐⭐⭐

**Knowledge is power, and the brain bank is the soul of AI**

#### 10 Knowledge Types
Experience • Pattern • Rule • Solution • Insight • Best Practice • Lesson Learned • Heuristic • Predictive • Causal

#### 11 Knowledge Domains
Error Fix • Performance • Security • Database • Frontend • Backend • DevOps • AI/ML • UX • Business • General

#### 5 Smart Trigger Types
Threshold • Pattern Match • State Change • Time-based • Event-driven

> **Auto-Learning**: Triggers automatically learn from events, continuously optimizing confidence and priority

---

### 🤖 AI Employee System (v2.0)

**Not one AI fighting alone, but an AI team working together**

| Role | Responsibility | Level |
|------|---------------|-------|
| 👨‍💻 Frontend Fixer | Page beautification, CSS fix, interaction optimization | ⭐⭐⭐⭐⭐ |
| 🔧 Backend Architect | API design, performance optimization, architecture | ⭐⭐⭐⭐⭐ |
| 🗄️ DBA | Query optimization, index design, data security | ⭐⭐⭐⭐ |
| 🔐 Security Auditor | Vulnerability scanning, hardening, compliance | ⭐⭐⭐⭐ |
| 📊 Monitoring Analyst | Performance monitoring, anomaly detection | ⭐⭐⭐⭐ |
| 📚 Knowledge Manager | Brain bank maintenance, knowledge integration | ⭐⭐⭐⭐⭐ |
| 🎯 Proactive Discoverer | Requirement mining, problem foresight | ⭐⭐⭐⭐⭐ |

---

### ⚡ Proactive AI System (v1.0)

**From passive trigger to active operation**

#### 5 Initiative Levels
| Level | Name | Description |
|-------|------|-------------|
| L1 | PASSIVE | Only acts on explicit commands |
| L2 | REACTIVE | Responds to events and alerts |
| L3 | PROACTIVE | Proactively finds problems and opportunities |
| L4 | SELF_DRIVEN | Self-set goals and priorities |
| L5 | AUTONOMOUS | Fully autonomous decision and execution |

---

### 🚀 Quick Start

#### Requirements
- Python 3.8+
- pip 21.0+
- SQLite 3.x

#### Installation

```bash
# Clone the repository
git clone https://github.com/wuchenghao15/MTSCOS-AI.git
cd MTSCOS-AI/flask-app

# Install dependencies
pip install -r requirements.txt

# Initialize database
python init.py

# Start server
python app.py --port 8888
```

#### Access URLs

| Page | URL | Description |
|------|-----|-------------|
| 🌐 Main | http://localhost:8888 | System homepage |
| 🔐 Admin | http://localhost:8888/admin_app | Admin panel |
| ⭐ Super Admin | http://localhost:8888/super_admin_dashboard | Super admin dashboard |
| 📚 API Docs | http://localhost:8888/api/docs | API documentation |

---

### 🔒 Security Features

HTTPS Enforcement • XSS Protection • CSRF Tokens • SQL Injection Prevention • AES-256 Encryption • 13-level Role Permissions • Hardware Key Auth • Operation Audit Logs • Session Timeout

---

### 📊 Stats

```
📈 Current Version:   v5.3.0
🤖 AI Employees:      10+
🧠 Knowledge Types:   10
📚 Knowledge Domains: 11
⚡ Trigger Types:     5
🔌 API Endpoints:     460+
📄 Templates:         130+
🔀 Routes:            629+
📅 Versions:          26+
🧠 AI Engines:        30+
📚 Questions:         27+
🛡️ Permission Rules:  29
👤 Roles:             14
📝 Audit Logging:     Enabled
```

---

### 📄 License

This project is licensed under the **MIT License**.

Copyright © 2024-2026 MTSCOS AI Team. All rights reserved.

---

<div align="center">

**Made with ❤️ by MTSCOS AI Team**

</div>
