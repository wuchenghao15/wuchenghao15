---
name: "mtscos-version"
description: 基于《版本升级规则》的方法论 Skill。解决核心问题：四级版本号体系 major.minor.patch+build + 自动检测 + mandatory_upgrade_flag。适合人群：AI Agent + 人类开发者, 所有涉及该领域的活动。典型使用场景：AI Agent 准备修改该领域代码 → Trae 自动触发此 Skill；人类开发者不确定合规性 → 查 Skill；CI 自检失败 → 回溯规则原因。
---

# 版本升级规则 - 方法论 Skill

> 基于 MTSCOS AI 项目规则治理体系 的《版本升级规则》
>
> 本 Skill 仅供个人学习使用

## 概述

### 解决什么问题
四级版本号体系 major.minor.patch+build + 自动检测 + mandatory_upgrade_flag

### 目标受众
AI Agent + 人类开发者, 所有涉及该领域的活动

### 核心收益
- 硬约束不可绕过
- 自动拦截机制 (4 层)
- AI 自动遵守
- 落库留痕可追溯

---

## 快速上手

> 一句话概括：四级版本号体系 major.minor.patch+build + 自动检测 + mandatory_upgrade_flag

**最简使用流程：**
1. **Preflight**
2. **Execute**
3. **Verify**
4. **Close**

**核心原则速记：**
- mandatory_upgrade_flag=True 不可关闭
- 跨大版本必须先跑 migration
- CI 版本号自增

---

## 核心方法

### 方法步骤

#### 步骤 1: Preflight

确认规则适用 + STATUS=ACTIVE

**具体操作：**
- 查 RULE_META
- 确认 intercept_layers

**依赖关系：** L0 §14

---

#### 步骤 2: Execute

按 版本升级规则 条款执行

**具体操作：**
- 遵守硬约束
- 禁止违反
- 落库

**依赖关系：** Preflight

---

#### 步骤 3: Verify

CI 自检 + 规则完整性扫描

**具体操作：**
- mt_rule_integrity_scan PASS
- 无 mt_rule_violation_alert

**依赖关系：** Execute

---

#### 步骤 4: Close

落库 changelog + 结案

**具体操作：**
- 更新 RULE_META version
- 记录变更

**依赖关系：** Verify

---

### 核心原则

- **mandatory_upgrade_flag=True 不可关闭**
- **跨大版本必须先跑 migration**
- **CI 版本号自增**
- **五级 bump 规则 (MAJOR/MINOR/PATCH/META)**

### 注意事项与警告

- ⚠️ 改大版本号没 migration → 数据库结构不匹配
- ⚠️ mandatory_upgrade_flag=False → 安全绕过

**避坑指南：**
- 执行前先读 RULE_META
- 规则修改走 7 步审批
- CI 自检必过

---

## 使用指南

### 适用场景

✅ **推荐使用：**
- 版本号/升级/发布

❌ **不推荐使用：**
- 与该领域无关的纯只读活动

### 前置准备

**知识准备：**
- 读懂 RULE_META
- 理解层级优先级 (L0 > L1 > L2)
- 知道 intercept_layers 是什么

**工具准备：**
- rules_engine 8 组件
- CI 流水线
- sys_rule_enforcer daemon

**环境准备：**
- Flask before_request hook 生效
- Git pre-commit hook 已安装

### 预期产出

**直接产出：**
变更已落库 + 无规则违反事件

**阶段性产出：**
- CI 自检通过
- mt_rule_changelog 记录

**成功标准：**
- 无 mt_rule_violation_alert
- mt_rule_integrity_scan PASS

### 检验标准

CI 自检 + 落库检查 + 违反事件表空

**自测清单：**
- [ ] RULE_META 完整
- [ ] 硬约束未被修改
- [ ] CI PASS
- [ ] 违反事件表空

---

## 深入理解

### 核心原理

规则引擎 + 有限状态机 + 拦截器模式 + Fail-Closed

**为什么有效：**
4 层拦截 (git hook + Flask before_request + CI + git push) + daemon 自动执行 + 落库留痕 → 无法绕过

### 关键提问

在使用此方法时，请思考以下问题：

1. RULE_ID=MT_RULE_VERSION, STATUS=ACTIVE, 我是否遵守了所有硬约束?
2. 有没有跳步?
3. 落库了吗?
4. CI 会过吗?

---

## 实践资源

### 配套工具与模板

**工具清单：**
- rules_engine 8 组件
- sys_rule_enforcer daemon
- auto_rule_strengthener
- auto_patrol 6 人巡逻队

**模板：**
- mt_rule_changelog schema
- pre-commit hook 模板

**参考案例：**
- session 端口漂移事故 → 复盘后新增 §14 网络治理

### 学习路径

**入门阶段：**
- 读懂 RULE_META 的每个字段
- 理解层级优先级
- 看一次拦截事件

**进阶路径：**
- 扩展 intercept_layers
- 自定义 activity_type
- 写 CI 自检规则

**关键里程碑：**
- 首次活动完全合规
- CI 自检 100% PASS
- 7 天无拦截

### 方法变体

**常见变体：**
- MINIMAL (仅 CI + before_request)
- FULL (4 层全拦)

**场景调整：**
- 紧急修复: Security 缩短但不跳过

### 进阶技巧

- **弱约束自动强化**: auto_rule_strengthener 检测到 '应该'/'建议' 自动改成 '必须'

---

## AI 辅助建议

### 适合 AI 辅助的步骤

- **sys_rule_enforcer 规则自动学习 + 弱约束扫描**: 可由 AI 协助完成
- **auto_rule_strengthener 弱约束自动修复为强约束**: 可由 AI 协助完成
- **rule_integrity_scanner CI 自检**: 可由 AI 协助完成
- **auto_patrol 6 人巡逻队自动修复**: 可由 AI 协助完成

### 人机协作模式

AI 自动执行规则 + 自动修复弱约束, 人类做终审 + 规则修改审批 (7 步)

### 自动化机会

- 弱约束 → 强约束自动修复
- 拦截事件 → 自动告警 → 自动投喂脑库
- CI 自检 → 自动阻断合并

---

## Skill 使用说明

### 典型调用场景

- AI Agent 准备修改该领域代码 → Trae 自动触发此 Skill
- 人类开发者不确定合规性 → 查 Skill
- CI 自检失败 → 回溯规则原因

### 触发条件

当用户出现以下情况时，触发此 Skill：
- 每次 commit/发布前必查
- 用户请求 '改一下 XX' 且 XX 在此领域
- Trae 需要判断合规性

### 输入参数

- 活动类型
- 影响范围
- 安全等级

### 输出格式

规则约束清单 + 执行步骤 + 验证标准 + 交叉引用 + RULE_ID/LEVEL

---

## 

---

## 规则原文 (完整嵌入)

> 以下为 版本升级规则.md 全文, 所有条款均为**硬约束**, 不可绕过。

---
alwaysApply: true
---
<!-- RULE_META_START
RULE_ID: MT_RULE_VERSION
RULE_NAME: 版本升级规则
RULE_LEVEL: L1 核心
RULE_VERSION: v1.2.0
EFFECTIVE_DATE: 2026-08-22
STATUS: ACTIVE
VIOLATION_CODE: VERSION-RULE-VIOLATION
INTERCEPT_LAYERS: [pre_commit, before_request, ci_check, git_hook]
RESPONSIBLE_ROLE: super_admin
DEPENDS_ON: [MT_IRON_RULE_12STEPS, MT_RULE_GOVERNANCE]
MODIFY_APPROVAL_FLOW: 7_STEP (提议→2管理员同意→EigenFlux 5人磋商≥4/5→SA终审→保密撤回)
BYPASS_ALLOWED: false
LAST_CHANGED: 2026-09-19
RULE_META_END -->
<!-- WEAK_CONSTRAINT_CLEAR: 0处 | TRIGGER_BLOCK_DEFINED: 10处 -->
# 项目版本升级机制规则文档

## 版本号规则定义

当前运行时权威格式为 `MAJOR.MINOR.PATCH`，由 `flask-app/VERSION` 和
`flask-app/core/version_source.py` 提供。本文早期的日期型四段版本示例仅保留作历史记录，
不得用于新版本或修改 `VERSION` 文件。

### 一级版本号 (Major)
- **规则**: 手动增加
- **示例**: 1.x.x.x → 2.x.x.x
- **使用场景**: 重大架构变更、破坏性 API 变更、核心功能重构

### 二级版本号 (Minor)
- **规则**: 向后兼容的新功能
- **示例**: 22.2.0 → 22.3.0
- **使用场景**: 新增功能或兼容性扩展

### 三级版本号 (Patch)
- **规则**: 向后兼容的错误修复和小幅优化
- **示例**: 22.2.0 → 22.2.1
- **使用场景**: Bug 修复和不改变 API 契约的优化

### 构建标识
- **规则**: 构建时间和流水线编号记录在发布元数据中，不拼接到运行时版本号
- **示例**: `build_number=20260906a`
- **使用场景**: 区分同一 SemVer 下的构建产物

## 版本升级触发条件

| 升级类型 | 触发条件 | 版本号变化 |
|---------|---------|----------|
| 自动升级 | 检测到代码变更 | 根据变更规模自动判断 |
| 功能升级 | 新增向后兼容功能 | 增加二级版本号 |
| 修复升级 | 错误修复或兼容优化 | 增加三级版本号 |
| 构建标识 | 生成新的构建产物 | 只更新构建元数据 |
| 手动升级 | 开发者操作 | 增加一级版本号 |

## 版本号格式

```
major.minor.patch
```

- **major**: 一级版本号 (手动增加)
- **minor**: 向后兼容的新功能
- **patch**: 向后兼容的修复和优化
- **build**: 仅作为发布元数据，不进入 SemVer 字符串

## 示例版本号（以三段 SemVer 为准，旧四段格式已废弃）

| 场景 | 版本号 | 说明 |
|------|--------|------|
| 初始版本 | 1.0.0 | 三段 SemVer 起点 |
| 日常开发 | 22.3.0 → 22.3.1 | patch bump |
| 新增功能 | 22.3.1 → 22.4.0 | minor bump |
| 架构重构 | 22.4.0 → 23.0.0 | major bump |
| 紧急安全修复 | 22.4.0 → 22.4.1 | patch bump + `[SECURITY]` 标签 |

> ⚠️ 旧文档中的四段格式（`1.20260118.0.xxxxx`）已由 RULE_META v1.0.0 声明废弃，
> 任何代码修改或文档更新**不得**再引用旧格式。违反按 `VERSION-RULE-VIOLATION` 落库。

## §3 强制约束条款（v1.1.0 新增，仙女座联动）

### 3.1 版本号语义铁律（FORCE，不可绕过）

| # | 约束 | 违反判定 | 仙女座联动 |
|---|------|---------|-----------|
| V-01 | **必须**使用三段 `MAJOR.MINOR.PATCH`，**不得**用四段日期型 | 版本号包含 `YYYYMMDD` 或 `build_number` 进入 SemVer 字符串 | rule_knowledge 扫描到 → 自动触发 evolution_log `version_format_error` |
| V-02 | MAJOR bump **必须**附带 EigenFlux 5人磋商记录 + mt_rule_changelog approved_by_7step=1 | 无磋商 / changelog 缺失就 bump major | 仙女座 auto_evolution 跳过此阶段，等待人工补录 |
| V-03 | **禁止**用同一 patch 版本号发布不同代码 | Git tag 相同 commit 不同 → reject push | 仙女座 rule_knowledge 标记旧版本为 STALE |
| V-04 | 升级**必须**写 mt_rule_changelog 记录 | 变更但 changelog 缺失 → 拦截 before_request | evolution_log 触发 `version_missing_changelog` |
| V-05 | **不得**在 git tag 之外的地方存储运行时版本号 | 除 `flask-app/VERSION` + `VERSION` git tag 外 | — |
| V-06 | 降级（版本号减小）**必须** SA VIKEY 实时检测 | 降级请求无 VIKEY 绑定 → 自动 fail-closed | evolution_log 记录为安全事件 |
| V-07 | 仙女座 auto_evolution 连续 3 次失败 → **强制** patch bump + `[EVOLUTION-FIX]` 标签 | 连续失败不 bump → daemon 心跳中断 | smart_mount_engine 触发 fail_repair + patch bump |
| V-08 | mt_andromeda_rule_knowledge 更新 ≥ 50 条规则分块 → **强制** minor bump + `[RULE-REFRESH]` 标签 | rule_knowledge 显著更新不 bump | — |
| V-09 | VIKEY 加密狗固件升级 → **强制** patch bump + `[SECURITY]` 标签 | 固件升级无版本 bump | — |
| V-10 | 任何含 `major=1` / `breaking_change=1` 的 PR → **强制** major bump | breaking PR 只 bump minor | EigenFlux auto_consult 自动追加磋商任务 |

### 3.2 自动触发版本 bump 的事件清单（仙女座 → 规则引擎闭环）

| 触发源 | 条件 | 最小 bump | 标签 | 拦截层 |
|--------|------|-----------|------|--------|
| mt_ai_self_evolution_log | evolution_error_count ≥ 3 / 24h | patch | `[EVOLUTION-FIX]` | pre_commit + daemon heartbeat |
| mt_andromeda_rule_knowledge | chunk 新增 ≥ 50 条 / 7d | minor | `[RULE-REFRESH]` | before_request |
| mt_eigenflux_comm_messages | 安全告警消息 ≥ 10 / 24h | patch | `[SECURITY]` | ci_check |
| git commit | commit message 含 `BREAKING CHANGE:` | major | — | git_hook pre-push |
| mt_permission_audit_detail | 新增越权案例 ≥ 5 条 / 7d | patch | `[PERM-FIX]` | before_request |
| 仙女座 employee_registry | status 异常 ≥ 20 名 | patch | `[EMPLOYEE-HEAL]` | daemon heartbeat |

> 闭环代码位置: `ai_engines/rules_engine/rule_version.py` — `_auto_bump_from_events()` 函数，
> 每 300s 由 sys_rule_enforcer daemon 调用一次。

### 3.3 仙女座版本感知（v1.1.0 新增）

仙女座自演化引擎**必须**感知当前系统版本：
- `engines/andromeda_auto_evolution.py` 启动时读取 `VERSION` + `rule_knowledge` 表
- 版本 < 规则要求的 minimum_version → evolution_log 标记 `version_too_old`，跳过演化阶段
- 版本 bump 后 15 分钟内，rule_knowledge 分块**必须**被重新 ingest（触发 `trigger_type='version_bump'`）
- 双向同步守护（autosync_andromeda.py）**禁止**在两端版本差 ≥ major 时执行 rsync（避免 schema 不兼容）

违反 → 按 `VERSION-RULE-VIOLATION` 落库 + EigenFlux 告警。

## §4 规则治理闭环（仙女座 ↔ 规则引擎）

```
仙女座 evolution_log  (错误 spike / 慢响应 / employee 异常)
        │
        ▼
rule_version.py _auto_bump_from_events()  (每 300s)
        │
        ├── mt_rule_changelog  INSERT (自动记录 bump 原因)
        ├── mt_andromeda_rule_knowledge  重新 ingest (规则新版本分块)
        └── before_request  版本检查中间件  (强制 bump 生效)
        │
        ▼
规则引擎 rule_enforcer daemon  (每 300s)
        │
        └── mt_rule_integrity_scan  自检报告  (覆盖率 + 弱约束词清零)
                │
                ▼
        EigenFlux 5人 AI 专家磋商  (如需 major bump)
```

**强制**：此闭环**不得**被禁用。禁用等于关闭规则保护，触发 §14 IRON_RULE fail-closed 分支。

## 版本管理功能

### 1. 代码变更检测
- 自动扫描项目文件
- 检测文件修改时间
- 计算修改文件数量
- 统计修改代码行数
- 记录修改次数

### 2. 版本升级逻辑
- **自动升级**: 根据代码变更自动判断升级类型
- **每日升级**: 检测日期变更自动更新二级版本号
- **批量升级**: 文件数>15 或行数>500 时增加三级版本号
- **实时升级**: 每次修改自动更新四级版本号
- **手动升级**: 支持手动触发各级版本升级

### 3. 版本文件更新
- 更新 package.json 版本号
- 记录版本升级历史
- 生成版本变更日志
- 支持数据库存储版本信息

## 使用方法

### 自动升级
```javascript
const { getVersionManager } = require('./src/core/version/version-manager');
const versionManager = getVersionManager();

// 自动检测并升级版本
const upgradedVersion = await versionManager.upgradeVersion('auto');
console.log('新版本:', upgradedVersion.versionString);
```

### 手动升级
```javascript
// 升级一级版本
await versionManager.upgradeVersion('major');

// 升级二级版本（当日时间）
await versionManager.upgradeVersion('minor');

// 升级三级版本
await versionManager.upgradeVersion('patch');

// 只更新四级版本
await versionManager.upgradeVersion('build');
```

### 检查版本信息
```javascript
const versionInfo = await versionManager.getVersionInfo();
console.log('当前版本:', versionInfo.currentVersion.versionString);
console.log('版本历史:', versionInfo.versionHistory);
```

### 检查升级需求
```javascript
const requirements = versionManager.checkUpgradeRequirements();
console.log('是否需要升级:', requirements.shouldUpgrade);
console.log('升级类型:', requirements.upgradeType);
console.log('升级原因:', requirements.reasons);
```

## 技术实现

### 核心组件
- **VersionManager**: 版本管理核心类
- **代码变更检测**: 扫描文件系统检测修改
- **版本号计算**: 根据规则计算新版本号
- **版本文件更新**: 更新项目版本文件
- **版本历史记录**: 记录版本升级历史

### 依赖项
- Node.js
- fs (文件系统)
- path (路径处理)
- winston (日志记录)
- sqlite3 (数据库存储，可选)

## 配置项

### 配置文件
```javascript
{
    packageJsonFile: path.join(__dirname, '../../package.json'),
    logDir: path.join(__dirname, '../../Logs'),
    srcDir: path.join(__dirname, '../../')
}
```

### 环境变量
- 无特殊环境变量需求，使用默认配置即可

## 故障处理

### 数据库不可用
- 自动切换到文件系统存储
- 版本信息仍可正常更新
- 升级功能不受影响

### 文件系统错误
- 记录错误日志
- 尝试备选路径
- 保持版本管理功能可用

### 版本冲突
- 自动检测版本冲突
- 保留最新版本
- 记录冲突历史

## 性能优化

### 扫描优化
- 跳过不需要检查的目录 (node_modules, .git 等)
- 只检查代码文件
- 缓存扫描结果

### 计算优化
- 增量计算修改次数
- 缓存版本信息
- 异步处理文件操作

### 存储优化
- 压缩版本历史
- 限制日志文件大小
- 定期清理旧版本记录

## 总结

本版本升级机制实现了以下功能：
- ✅ 符合要求的四级版本号规则
- ✅ 自动代码变更检测
- ✅ 智能版本升级判断
- ✅ 完整的版本管理功能
- ✅ 健壮的错误处理
- ✅ 良好的性能优化

系统能够根据代码变更自动判断版本升级类型，确保版本号准确反映项目的变更状态，同时提供了灵活的手动升级选项，满足不同场景的需求。

## 🪐 仙女座 AI 审计师联动 (v1.2.0 新增)

> **修复原因**: 仙女座 AI 审计师发现"条款数偏少 (clauses=3)"。
> 实际规则正文有 15 个执行层 refs（所有 12 篇规则中最完善），
> 只是条款标记用的是 §3/§4 数字格式而非"第 N 条"。
> 执行层链路 2026-09-19 已修复，本条补充完整执行清单。

### A. 自动 bump 触发清单（sys_rule_enforcer 每 300s）

| 触发条件 | bump 类型 | 执行层 |
|---------|----------|--------|
| 代码变更 (git diff) | 自动分类 | rule_enforcer → 变更检测 |
| mt_andromeda_rule_knowledge chunk ≥ 50/7d | MINOR | before_request + changelog |
| 安全事件 ≥ 3/24h | PATCH ([SECURITY]) | auto_evolution + VIKEY |
| 弱约束词未清零 | PATCH ([RULE-FIX]) | auto_rule_strengthener |
| EigenFlux 演化 ≥ 100 条 | MINOR ([EVOLUTION]) | trigger_evolution() |
| DAO 新增越权案例 ≥ 5/7d | PATCH ([PERM-FIX]) | @system_container 拦截 |

### B. 仙女座 → 规则引擎闭环（强制）

```
仙女座 auto_evolution (每 300s)
  │
  ├─ 检测触发条件 (上表)
  ├─ mt_rule_changelog INSERT (自动)
  ├─ EigenFlux 5 人磋商 (consult_type='version_bump')
  ├─ before_request 拦截 (version_missing_changelog → 403)
  └─ mt_rule_integrity_scan 自检 (覆盖率 < 100% → 补扫)
```

### C. 版本降级安全（强制, fail-closed）

VERSION 减小（降级）**必须**:
  1. SA VIKEY 实检 (sa_vikey_verified=1)
  2. evolution_log 记录 (trigger_type='version_downgrade')
  3. mt_iron_rule_violations 新增一条
  4. EigenFlux 5 人紧急磋商

跳过任何一步 → fail-closed + mt_rule_violation_alert(alert_type='VERSION-DOWNGRADE-NOT-VIKED')。


参考资料

- 原书：《版本升级规则》
- 作者：MTSCOS AI 项目规则治理体系
- 免责声明：本 Skill 基于原书内容提炼，仅供个人学习使用
