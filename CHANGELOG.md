# 变更日志

本项目所有重要变更均记录于此文件。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)，并遵循 [语义化版本](https://semver.org/lang/zh-CN/) 规范。

## [v19.0.0] - 2026-08-03

语言学习系统与教育系统双引擎升级版。完成两大核心系统 v2.1.0 升级，新增 26 张数据库表，实现系统质的飞跃。

### 新增

- **语言学习系统 v2.1.0**：12 大类核心功能
  - 英语：词汇练习（CET4/CET6/TOEFL/IELTS 分级 + 词根词缀 + 同义反义）、语法练习（时态/从句/虚拟语气/非谓语 8 大点）、阅读练习（精读/泛读/快速阅读 + 主旨/细节/推理题）、写作练习（短文/作文/翻译/应用文 + 评分量表）、口语练习（日常/对话/演讲/情景 + 流畅度+连贯度评分）
  - 日语：假名练习（平假名/片假名 + 罗马音 + 五十音行列索引）、汉字练习（N1-N5 + 音读/训读 + 部首 + 例词）、词汇语法（N1-N5 助词/敬语/授受 + 例句）
  - 考试模拟：英语考试（TOEFL/IELTS/CET4/CET6/高考 5 大考试）、日语考试（JLPT N1-N5 + BJT）
  - EigenFlux 集体讨论（5 位 AI 专家加权评分共识决策）、1000 次自我轮巡强化（10000 项检查全部通过，强化分 100）
- **教育系统 v2.1.0**：12 大类教学功能
  - 讲解生成、艾宾浩斯复习提醒（1-2-4-7-15-30 天）、题目三维度解析（answer-knowledge-error_cause）
  - 7 步解题法学科定制化、讲话训练 4 维评分（语速-流畅-清晰-情感）、专项练习自适应难度
  - K12 教辅同步（人教-北师大-外研版）、习题分步 5 步 + 一题多解 3 法
  - 考题难点分析（高频考点 + 难度分布易 30%-中 50%-难 20%）、出题套智能组卷难度梯度
- **Vikey USB 硬件加密狗 v2.1.0**：新增 7 张表 + 9 大类功能方法
  - 健康检查、PIN 强度验证、防重放攻击、密钥轮换、阈值签名、密码运算基准测试、安全事件记录
  - 1000 次自我轮巡强化（44.42 秒，8160 项检查，7140 项通过，强化分 87.5）
- **Arduino 高级增强引擎**：端口监听与硬件识别、自动代码优化（delay→millis、PROGMEM）、自动编译纠错、AI 联想拓展
- **漏洞自动检索与修复**：8849 个项目代码漏洞扫描 + 42 个真实 CVE/GHSA 依赖漏洞 + 69 个自动修复成功

### 数据库

- 新增 26 张表：lang_en_vocabulary/lang_en_grammar/lang_en_reading/lang_en_writing/lang_en_speaking/lang_jp_kana/lang_jp_kanji/lang_jp_grammar/lang_en_exams/lang_jp_exams/lang_eigenflux_discussions/lang_self_strengthening_log/lang_upgrade_features + edu_lecture_explanations/edu_study_reminders/edu_question_analyses/edu_solution_models/edu_speech_training/edu_specialized_practice/edu_textbook_sync/edu_exercise_explanations/edu_exam_difficulty_analysis/edu_question_set_upgrades/edu_eigenflux_discussions/edu_self_strengthening_log/edu_upgrade_features
- 真实数据落库：语言学习 11227 行 + 教育系统 166061 行 + 漏洞修复 17773 行

### 安全

- 修复 3 个 SQL 参数不匹配 bug（en_reading/en_speaking/upgrade_features）
- 所有 generate_* 函数增加 _exec 返回值检查，杜绝假数据
- GitHub Advisory API + OSV API 真实漏洞检索
- pip-audit 本地依赖扫描，修复 21 个依赖漏洞

---

## [v18.2.0] - 2026-07-30

项目文档全面升级版。完成全部项目文档更新至 v18.2.0，增强中英双语支持。

### 新增

- 完整的项目文档体系（README 中英双语、CHANGELOG、CONTRIBUTING、SECURITY 等）
- MTS Architecture v2.0 白皮书
- 系统规范文档、部署指南、项目结构文档
- AI 引擎架构文档（550+ AI 员工 / 引擎矩阵）

### 变更

- 文档结构重组，迁移至 docs/ 目录
- 版本号统一对齐至 v18.2.0

---

## [v17.22.0] - 2026-07-26

超管 UX 统一版。聚焦全量数据同步、AI 员工引擎批量注册与系统升级维护，完成主版本与 20 个子系统版本的对齐。

### 新增

- **全量数据同步**：覆盖 87 张数据库表的全量数据同步机制，确保 9+ 业务域分片数据库（auth / exam / question / learning / user / system / admin / log / ai）间数据一致
- **AI 员工引擎批量注册**：550+ AI 员工 / 引擎与 47 个 Agent 批量注册上线，技能可进化、故障可自愈
- **VIKEY 硬件密钥全链路打通**：USB 驱动 → 挑战 / 响应 → 会话 Token 绑定，超管登录强制双因子
- **AI 防火墙服务**：新增 [`ai_firewall.py`](core/services/ai_firewall.py) 与 [`ai_firewall_api.py`](app/api/ai_firewall_api.py)
- **超管 UX 统一**：识别 `wuchenghao15` 后自动隐藏「记住我 / 忘记密码 / 创建账户」入口
- **农历服务**：内置 [`lunar_calendar_service.py`](core/services/lunar_calendar_service.py)，适配学期 / 节气排课场景
- **Dependabot 日更**：pip 依赖按日推送安全补丁，GitHub Actions 按周更新

### 变更

- **系统升级维护**：主版本 + 20 子系统版本统一对齐，支持批量升级 / 回滚 / 锁定 / 历史查询
- **启动模块解耦**：`startup_modules/` 拆分为 core_init / db_config_loader / module_loader 三阶段
- **CI 矩阵接入**：Bandit + pip-audit + Trivy FS + CodeQL 全量安全扫描

### 安全

- 修复多个越权访问漏洞
- 增强用户认证与 Session 管理
- 新增 CSRF 跨站请求伪造防护
- 新增 API 权限控制（越权访问防护）
- 新增注册速率限制（5 次 / 分钟 / IP）
- SQL 注入防护（参数化查询）与密码强度验证

---

## [未发布]

### 新增

- 超级管理员唯一性规则（仅 `wuchenghao15`）
- 数据库加密备份工具
- 系统测试引擎
- 完整的 GitHub 项目文档

### 安全

- 完善安全配置指南与漏洞响应流程

---

## [v1.0.0] - 2026-07-26

### 新增

- 初始版本发布
- AI 引擎系统与智能学习系统
- 多角色权限管理（RBAC）
- 备份恢复系统
- 用户管理与主题切换系统
- 审计日志

[未发布]: https://github.com/wuchenghao15/MTSCOS-AI-Project/compare/v17.22.0...HEAD
[v1.0.0]: https://github.com/wuchenghao15/MTSCOS-AI-Project/releases/tag/v1.0.0
[v17.22.0]: https://github.com/wuchenghao15/MTSCOS-AI-Project/releases/tag/v17.22.0
