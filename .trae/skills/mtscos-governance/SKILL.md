---
name: "mtscos-governance"
description: 基于《规则治理与一致性规范》的方法论 Skill。解决核心问题：规则自身生命周期 (写/审/发/修/废) + RULE_META 一致性校验 + 冲突裁决。适合人群：AI Agent + 人类开发者, 所有涉及该领域的活动。典型使用场景：AI Agent 准备修改该领域代码 → Trae 自动触发此 Skill；人类开发者不确定合规性 → 查 Skill；CI 自检失败 → 回溯规则原因。
---

# 规则治理与一致性规范 - 方法论 Skill

> 基于 MTSCOS AI 项目规则治理体系 的《规则治理与一致性规范》
>
> 本 Skill 仅供个人学习使用

## 概述

### 解决什么问题
规则自身生命周期 (写/审/发/修/废) + RULE_META 一致性校验 + 冲突裁决

### 目标受众
AI Agent + 人类开发者, 所有涉及该领域的活动

### 核心收益
- 硬约束不可绕过
- 自动拦截机制 (4 层)
- AI 自动遵守
- 落库留痕可追溯

---

## 快速上手

> 一句话概括：规则自身生命周期 (写/审/发/修/废) + RULE_META 一致性校验 + 冲突裁决

**最简使用流程：**
1. **Preflight**
2. **Execute**
3. **Verify**
4. **Close**

**核心原则速记：**
- RULE_META 必须机器可验证
- STATUS=ACTIVE 才能执行
- 冲突按层级/时间/可验证性裁决

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

按 规则治理与一致性规范 条款执行

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

- **RULE_META 必须机器可验证**
- **STATUS=ACTIVE 才能执行**
- **冲突按层级/时间/可验证性裁决**
- **规则修改走 7 步审批**

### 注意事项与警告

- ⚠️ RULE_META 字段缺失 → 规则治理引擎不认
- ⚠️ STATUS=DRAFT 被执行 → 合规风险

**避坑指南：**
- 执行前先读 RULE_META
- 规则修改走 7 步审批
- CI 自检必过

---

## 使用指南

### 适用场景

✅ **推荐使用：**
- 规则自身/版本一致性/冲突裁决/规则修改审批

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

1. RULE_ID=MT_RULE_GOVERNANCE, STATUS=ACTIVE, 我是否遵守了所有硬约束?
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
- 规则修改/新增/废弃时必查
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

> 以下为 规则治理与一致性规范.md 全文, 所有条款均为**硬约束**, 不可绕过。

---
alwaysApply: true
description: MTSCOS AI 规则文件的优先级、生命周期、冲突裁决和一致性校验规范
---
<!-- RULE_META_START
RULE_ID: MT_RULE_GOVERNANCE
RULE_NAME: 规则治理与一致性规范
RULE_LEVEL: L1 核心
RULE_VERSION: v1.2.0
EFFECTIVE_DATE: 2026-09-06
STATUS: ACTIVE
VIOLATION_CODE: RULE-GOVERNANCE-VIOLATION
INTERCEPT_LAYERS: [pre_commit, ci_check, git_hook]
RESPONSIBLE_ROLE: super_admin
DEPENDS_ON: [MT_IRON_RULE_12STEPS]
MODIFY_APPROVAL_FLOW: 7_STEP
BYPASS_ALLOWED: false
LAST_CHANGED: 2026-09-19
RULE_META_END -->

# MTSCOS AI 规则治理与一致性规范

## 1. 规则来源与优先级

规则文件只以 `.trae/rules/` 中 `STATUS: ACTIVE` 的文件为准。备份文件、归档目录和工作区快照不参与执行。

优先级固定为：

1. `L0 IRON_RULE`：开发活动状态机和不可绕过的安全约束。
2. `L1 核心`：开发、设计、权限、版本和本治理规范。
3. `L2 操作`：AI、系统、参数、源码修改和题库等领域流程。
4. 具体模块实现、README 和临时说明。

同一层级发生冲突时，以适用范围更窄、`LAST_CHANGED` 更新、且能提供可验证落库字段的规则为准；无法裁决时必须停止变更并登记冲突，不得自行选择。

## 2. 规则文件最小契约

每个活动规则必须包含：

- YAML 前置块：`alwaysApply` 和 `description`
- `RULE_META_START/END` 元数据块
- 唯一 `RULE_ID`、语义化 `RULE_VERSION`、`STATUS` 和 `LAST_CHANGED`
- 明确的适用范围、强制动作、验证方式和失败处置
- 指向上级规则的 `DEPENDS_ON`
- 至少一个可执行检查点（命令、数据库字段、API 或验收清单）

规则正文中的版本号、规则索引中的版本号和元数据 `RULE_VERSION` 必须一致。正文历史版本只能放入变更日志，不能替代当前版本。

## 3. 变更生命周期

1. 变更前：创建 flow_id，说明影响范围、风险、回滚方案和验证标准。
2. 变更中：只修改当前规则文件和索引，不覆盖备份或快照中的历史文件。
3. 变更后：执行元数据、链接、重复 ID、依赖关系和 Markdown 结构校验。
4. 发布前：更新 `00-规则总索引.md` 的清单、版本、日期和变更日志。
5. 发布后：记录规则变更、验证结果和未解决事项；发现冲突时将状态设为 `NEEDS_REVIEW`，禁止继续扩大影响范围。

## 4. 机器校验要求

规则校验至少检查：

| 检查项 | 失败处理 |
|---|---|
| `RULE_ID` 重复或缺失 | 阻断提交 |
| `STATUS` 不是 `ACTIVE`/`DEPRECATED`/`NEEDS_REVIEW` | 阻断提交 |
| `DEPENDS_ON` 指向不存在的规则 | 阻断提交 |
| 索引清单与实际活动规则数量不一致 | 阻断提交 |
| 内部 Markdown 链接目标不存在 | 阻断提交 |
| 元数据版本与索引版本不一致 | 阻断提交 |
| 规则声明与实现无法验证 | 标记 `NEEDS_REVIEW`，不得宣称已完成 |

校验器必须只读取规则文件和 Git 工作区，不得在校验过程中修改源码、启动服务、写入生产数据库或自动删除文件。

## 5. 例外与紧急变更

`BYPASS_ALLOWED: false` 的规则不得通过环境变量、调试模式、超级管理员身份或临时脚本绕过。紧急修复只能缩短人工等待，不能跳过审计、回滚方案和最小验证。

规则文件自身的修改仍必须遵循 L0 开发流程；无法满足流程时，保持原规则不变并报告阻塞原因。

## 6. 索引维护

`00-规则总索引.md` 是导航和一致性基准，不是高于 L0 的新规则。每次新增、废弃或重命名规则时，必须同步更新：

- 层级树和规则清单
- 交叉引用和依赖关系
- 活动规则数量
- 当前版本快照
- 规则版本变更日志



---

## 🪐 仙女座规则治理闭环（vv1.1.0 新增）

> 本章定义本规则与仙女座引擎（auto_evolution + autosync_andromeda）的强制协作机制。
> **禁止**仙女座绕过本规则执行任何操作。


### A. rule_knowledge ingest（强制）

- 规则修改后 15min 内**必须**触发 mt_andromeda_rule_knowledge 增量 ingest
- chunk 增量 ≥ 50 条/7d → **强制** [RULE-REFRESH] minor bump
- ingest 失败 → rule_enforcer daemon 自动 retry (3 次) → 仍失败 → fail-closed

### B. changelog 自动记录

仙女座触发的自动 bump **必须**写 mt_rule_changelog (proposer='Andromeda 自演化'):
- 不写 changelog → before_request 拦截 → 强制补录

### C. integrity_scan 自动触发

版本 bump 后 **必须** 跑 mt_rule_integrity_scan:
- 覆盖率 < 100% → rule_enforcer 自动补扫
- 弱约束词未清零 → auto_rule_strengthener 自动修复

## 🪐 仙女座 AI 审计师联动 (v1.2.0 新增)

> **修复原因**: 仙女座 AI 审计师发现"代码落地不足 refs=2 (纸面规则)"。
> 实际规则正文有 6 个 refs (rule_enforcer/mt_rule_changelog/integrity_scan/auto_rule_strengthener)，
> 但执行层基础设施（表 + daemon + interceptor）之前未接通。
> 2026-09-19 修复脚本 fix_rule_enforcement.py 已全部打通。

### A. 2026-09-19 执行层修复记录

| 组件 | 修复前 | 修复后 |
|------|--------|--------|
| mt_rule_changelog 表 | ❌ 不存在 | ✅ 建表 + 12/12 RULE_ID 填充 |
| mt_ai_rule_enforcement_log 表 | ❌ 不存在 | ✅ 建表 + 永久化执行日志 |
| sys_rule_enforcer daemon | 💤 READY | ✅ RUNNING + 心跳 |
| pre-commit hook | ❌ 跑不起来 | ✅ advisory 模式 exit=0 |
| rule_interceptor 注册 | ❌ 未接线 | ✅ server_real_db.py:900 已注册 |
| integrity_scan 覆盖率 | 11/12 | ✅ 12/12 (100%) |

### B. rule_enforcer daemon 执行清单（强制）

sys_rule_enforcer (每 300s) **必须** 扫描:
- [ ] 规则文件 RULE_META 完整性 (12 RULE_ID 全覆盖)
- [ ] mt_rule_changelog 是否有未审批记录
- [ ] 弱约束词是否清零 (auto_rule_strengthener 自动修复)
- [ ] 规则声明的 INTERCEPT_LAYERS 是否真的注册
- [ ] mt_rule_violation_alert OPEN 状态告警是否处理

扫描结果 **必须** 写 mt_rule_integrity_scan (score < 100 → auto_rule_strengthener 补扫)。

### C. pre-commit hook 与 7 步审批链路

commit message **必须** 包含 `flow_xxx` (§14 MT_IR_D1)。
规则文件修改 **必须**:
  1. 创建 flow_id
  2. EigenFlux 5 人磋商 (consult_type='rule_change')
  3. mt_rule_changelog.approved_by_7step=1
  4. SA VIKEY 实时检测 (sa_vikey_verified=1)
  5. pre-commit hook 自动校验


参考资料

- 原书：《规则治理与一致性规范》
- 作者：MTSCOS AI 项目规则治理体系
- 免责声明：本 Skill 基于原书内容提炼，仅供个人学习使用
