# 变更日志

本项目所有重要变更均记录于此文件。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)，并遵循 [语义化版本](https://semver.org/lang/zh-CN/) 规范。

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
