# MTSCOS AI 版本说明文档

> 版本: v17.22.0
> 更新日期: 2026-07-26

---

## 📋 目录

- [1. 版本管理规则](#1-版本管理规则)
- [2. 当前版本信息](#2-当前版本信息)
- [3. 版本历史](#3-版本历史)
- [4. 版本对比](#4-版本对比)
- [5. 升级指南](#5-升级指南)
- [6. 版本 API](#6-版本api)

---

## 1. 版本管理规则

### 版本号格式

```text
MAJOR.MINOR.PATCH
```

| 字段 | 说明 | 递增规则 |
|------|------|---------|
| MAJOR | 主版本号 | 不兼容的 API 变更或重大架构重构时递增 |
| MINOR | 次版本号 | 新增功能且向下兼容时递增 |
| PATCH | 修订号 | Bug 修复或小优化时递增 |

### 版本范围约束

| 字段 | 最小值 | 最大值 |
|------|-------|--------|
| MAJOR | 1 | 99 |
| MINOR | 0 | 99 |
| PATCH | 0 | 999 |

### 版本命名规范

```text
v<MAJOR>.<MINOR>.<PATCH> (<Codename>)
```

### 版本状态

| 状态 | 说明 |
|------|------|
| alpha | 内部测试版 |
| beta | 公开测试版 |
| rc | 候选发布版 |
| stable | 稳定版 |

---

## 2. 当前版本信息

### v17.22.0 - SuperAdmin UX Unified Edition

| 项目 | 内容 |
|------|------|
| 版本号 | v17.22.0 |
| 代号 | SuperAdmin UX Unified Edition |
| 状态 | stable |
| 构建号 | 20260726a |
| 构建日期 | 2026-07-26 |

### 版本摘要

超管 UX 统一版本，主要新增超管识别隐藏「记住我 / 忘记密码 / 创建账号」入口、VIKEY 全链路打通、主版本 + 20 子系统统一对齐、CI 接入 Dependabot + Trivy + Bandit 等特性，锁定 MTS 架构 v2.0 双引擎核心。

### 主要特性

1. **超管 UX 统一** - 超级管理员识别后隐藏「记住我 / 忘记密码 / 创建账号」入口，统一登录交互体验
2. **VIKEY 全链路打通** - USB 硬件密钥 7 要素强认证全链路验证（用户名、密码、随机挑战码、USB Key 序列号、USB Key PIN、SSL 指纹、硬件绑定校验）
3. **统一版本 API** - 1 个主版本 + 20 个子系统版本统一对齐，支持批量升级 / 回滚 / 版本锁定 / 变更历史
4. **MTS 架构 v2.0 双引擎** - 命题引擎 + 诊断引擎双核调度，规划引擎与执行 AI 员工阵列分离
5. **AI 引擎矩阵扩展** - 550+ 专业 AI 员工/引擎与 47 个 Agent，技能可进化、故障可自愈
6. **分布式数据库架构** - 9+ 独立 SQLite 分片（auth/exam/question/learning/user/system/admin/log/ai），共 87 张表（0 空表）
7. **企业级权限管理** - RBAC 16 级角色 + ABAC 属性过滤，50+ 权限规则，全链路不可篡改审计
8. **AI 防火墙 + 应用安全** - WAF 10 条规则 + pip-audit / Trivy / Bandit / CodeQL 安全扫描矩阵
9. **自维护运维 OS** - 8 维自动修复（表结构 / 配置 / 缓存 / 连接池 / 回滚 / 数据恢复 / 索引 / ACL）+ 8 维预防式健康诊断
10. **LayoutAI 排版调节** - LayoutAdjusterAI 员工 20 条割裂检测规则（LF001-LF020）
11. **公祭日自动主题** - 国家公祭日自动切换黑灰追思主题
12. **CI 安全扫描矩阵** - Dependabot（pip 日更 + Actions 周更）、Trivy FS、Bandit、CodeQL 接入

---

## 3. 版本历史

### v17.x.x 系列

| 版本 | 代号 | 日期 | 状态 |
|------|------|------|------|
| v17.22.0 | SuperAdmin UX Unified Edition | 2026-07-26 | stable |

### v16.x.x 系列

| 版本 | 代号 | 日期 | 状态 |
|------|------|------|------|
| v16.0.0 | Security & Education Enhancement Edition | 2026-07-22 | stable |

### v15.x.x 系列

| 版本 | 代号 | 日期 | 状态 |
|------|------|------|------|
| v15.4.0 | Enhanced AI Learning & Analytics Edition | 2026-07-21 | stable |
| v15.0.0 | AI Enhanced Education Edition | 2026-07-20 | stable |

### v14.x.x 系列

| 版本 | 代号 | 日期 | 状态 |
|------|------|------|------|
| v14.0.0 | AI Employee Orchestration & Integration Edition | 2026-07-18 | stable |

### v13.x.x 系列

| 版本 | 代号 | 日期 | 状态 |
|------|------|------|------|
| v13.1.0 | AI Professional Role & Personality Edition | 2026-07-17 | stable |
| v13.0.0 | AI Intelligent Decision & Prediction Edition | 2026-07-16 | stable |

### v12.x.x 系列

| 版本 | 代号 | 日期 | 状态 |
|------|------|------|------|
| v12.0.0 | AI Advanced Cognitive & Adaptive Edition | 2026-07-15 | stable |

### v11.x.x 系列

| 版本 | 代号 | 日期 | 状态 |
|------|------|------|------|
| v11.0.0 | AI Cognitive Enhancement Edition | 2026-07-15 | stable |

### v10.x.x 系列

| 版本 | 代号 | 日期 | 状态 |
|------|------|------|------|
| v10.0.0 | AI Evolution & System Expansion Edition | 2026-07-15 | stable |

### v9.x.x 系列

| 版本 | 代号 | 日期 | 状态 |
|------|------|------|------|
| v9.0.0 | AI Empowerment & Unified Version Edition | 2026-07-14 | stable |

### v8.x.x 系列

| 版本 | 代号 | 日期 | 状态 |
|------|------|------|------|
| v8.0.0 | Full Function Expansion Edition | 2026-07-13 | stable |

### v7.x.x 系列

| 版本 | 代号 | 日期 | 状态 |
|------|------|------|------|
| v7.2.0 | Comprehensive Enhanced Edition | 2026-07-07 | stable |
| v7.1.0 | Intelligent Modular Enhanced Edition | 2026-07-07 | stable |
| v7.0.0 | Intelligent Modular Edition | 2026-07-07 | stable |

### v6.x.x 系列

| 版本 | 代号 | 日期 | 状态 |
|------|------|------|------|
| v6.0.0 | Distributed Database Edition | 2026-07-06 | stable |

### v5.x.x 系列

| 版本 | 代号 | 日期 | 状态 |
|------|------|------|------|
| v5.0.0 | AI Integration Edition | 2026-06-01 | stable |

### v4.x.x 系列

| 版本 | 代号 | 日期 | 状态 |
|------|------|------|------|
| v4.0.0 | Exam System Edition | 2026-05-01 | stable |

### v3.x.x 系列

| 版本 | 代号 | 日期 | 状态 |
|------|------|------|------|
| v3.0.0 | Learning Edition | 2026-04-01 | stable |

### v2.x.x 系列

| 版本 | 代号 | 日期 | 状态 |
|------|------|------|------|
| v2.0.0 | Admin Edition | 2026-03-01 | stable |

### v1.x.x 系列

| 版本 | 代号 | 日期 | 状态 |
|------|------|------|------|
| v1.0.0 | Initial Edition | 2026-02-01 | stable |

---

## 4. 版本对比

### v17.22.0 vs v16.0.0

| 功能类别 | v16.0.0 | v17.22.0 |
|----------|---------|---------|
| 超管 UX | 标准登录入口 | 超管识别隐藏入口 |
| VIKEY 认证 | 基础验证 | 7 要素强认证全链路 |
| 版本管理 | 单一主版本 | 主版本 + 20 子系统统一对齐 |
| 架构版本 | MTS v1.0 | MTS v2.0 双引擎 |
| AI 引擎矩阵 | 41+ 员工 | 550+ 员工/引擎、47 Agent |
| 数据库架构 | 20+ 数据库 | 9+ SQLite 分片、87 张表（0 空表） |
| LayoutAI | 无 | 20 条割裂检测规则 |
| 公祭日主题 | 无 | 自动切换黑灰主题 |
| CI 安全扫描 | 基础扫描 | Dependabot + Trivy + Bandit + CodeQL |

### v16.0.0 vs v15.4.0

| 功能类别 | v15.4.0 | v16.0.0 |
|----------|---------|---------|
| 安全防护 | 基础防护 | 企业级防火墙（10+ 规则） |
| 安全漏洞管理 | 无 | 漏洞特征库 / 攻击模拟 / 代码扫描 |
| AI 安全建议 | 无 | 智能漏洞分析与建议 |
| 教学大纲管理 | 无 | 完整大纲管理系统 |
| 题库与大纲同步 | 无 | 智能映射与同步 |
| 学习与大纲追踪 | 基础追踪 | 知识点掌握度 / 评估报告 |
| 看门狗守护进程 | 无 | 自动重启 / 指数退避 |
| Docker 部署 | 基础配置 | 完整配置 + 快速配置 |
| 系统文档 | 基础文档 | 中英文完整文档 |
| GitHub 曝光度 | 基础配置 | 徽章 / CI/CD / PR 模板 |
| 版本管理 | 基础版本 | 统一版本管理 |

---

## 5. 升级指南

### 从 v16.x.x 升级到 v17.22.0

#### 升级步骤

1. **备份数据**

```bash
# 备份所有分布式数据库分片
cp -r split_databases/ split_databases_backup_17/
```

2. **拉取最新代码**

```bash
git pull origin main
```

3. **更新依赖**

```bash
pip install -r flask-app/requirements.txt
```

4. **数据库迁移**

```bash
python3 server_real_db.py --migrate
```

5. **重启服务**

```bash
# 停止旧服务
pkill -f "python server_real_db.py"

# 启动新服务
python3 server_real_db.py --host 0.0.0.0 --port 8888
```

#### 注意事项

- v17.22.0 引入 MTS 架构 v2.0 双引擎核心，建议完整阅读架构变更说明
- VIKEY 全链路打通后，超级管理员登录需插入 USB 硬件密钥
- 数据库已重构为 9+ 分布式分片（87 张表），首次启动会自动迁移
- 建议在升级前备份所有数据

### 从 v15.x.x 升级到 v16.0.0

#### 升级步骤

1. **备份数据**

```bash
cp -r split_databases/ split_databases_backup_16/
```

2. **拉取最新代码**

```bash
git pull origin main
```

3. **更新依赖**

```bash
pip install -r flask-app/requirements.txt
```

4. **数据库迁移**

```bash
python3 server_real_db.py --migrate
```

5. **重启服务**

```bash
python3 server_real_db.py --host 0.0.0.0 --port 8888
```

---

## 6. 版本 API

### 获取当前版本

```bash
curl http://localhost:8888/api/system/version
```

**响应：**

```json
{
  "version": "17.22.0",
  "codename": "SuperAdmin UX Unified Edition",
  "status": "stable",
  "build_number": "20260726a",
  "build_date": "2026-07-26",
  "description": "超管 UX 统一版本..."
}
```

### 获取版本历史

```bash
curl http://localhost:8888/api/system/version/history
```

**响应：**

```json
{
  "history": [
    {
      "version": "17.22.0",
      "codename": "SuperAdmin UX Unified Edition",
      "status": "stable",
      "build_date": "2026-07-26",
      "upgrade_time": "2026-07-26T10:00:00",
      "upgrade_type": "manual"
    }
  ]
}
```

### 检查更新

```bash
curl http://localhost:8888/api/system/version/check
```

**响应：**

```json
{
  "available": false,
  "current_version": "17.22.0",
  "latest_version": "17.22.0",
  "data": {...}
}
```

### 获取版本对比

```bash
curl http://localhost:8888/api/system/version/compare?v1=16.0.0&v2=17.22.0
```

**响应：**

```json
{
  "version1": "16.0.0",
  "version2": "17.22.0",
  "v1_features": [...],
  "v2_features": [...],
  "new_features": [...],
  "removed_features": []
}
```

---

## 📊 版本统计

| 统计项 | 数值 |
|--------|------|
| 总版本数 | 17 |
| 主版本数 | 17 |
| 次版本数 | 7 |
| 修订版本数 | 2 |
| 第一个版本 | v1.0.0（2026-02-01） |
| 最新版本 | v17.22.0（2026-07-26） |
| 开发周期 | 约 6 个月 |

---

**版本管理系统由 version_manager.py 自动维护** ✨
