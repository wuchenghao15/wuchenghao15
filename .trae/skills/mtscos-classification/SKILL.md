---
name: "mtscos-classification"
description: 基于《机密等级与访问控制规范》的方法论 Skill。解决核心问题：极密 (SA 独占)/机密 (7 要素认证)/秘密 (授权) 三级分类 + 审计 + 脱敏。适合人群：AI Agent + 人类开发者, 所有涉及该领域的活动。典型使用场景：AI Agent 准备修改该领域代码 → Trae 自动触发此 Skill；人类开发者不确定合规性 → 查 Skill；CI 自检失败 → 回溯规则原因。
---

# 机密等级与访问控制规范 - 方法论 Skill

> 基于 MTSCOS AI 项目规则治理体系 的《机密等级与访问控制规范》
>
> 本 Skill 仅供个人学习使用

## 概述

### 解决什么问题
极密 (SA 独占)/机密 (7 要素认证)/秘密 (授权) 三级分类 + 审计 + 脱敏

### 目标受众
AI Agent + 人类开发者, 所有涉及该领域的活动

### 核心收益
- 硬约束不可绕过
- 自动拦截机制 (4 层)
- AI 自动遵守
- 落库留痕可追溯

---

## 快速上手

> 一句话概括：极密 (SA 独占)/机密 (7 要素认证)/秘密 (授权) 三级分类 + 审计 + 脱敏

**最简使用流程：**
1. **Preflight**
2. **Execute**
3. **Verify**
4. **Close**

**核心原则速记：**
- 极密数据不落盘
- 机密数据 7 要素强认证
- 秘密数据授权后可访问

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

按 机密等级与访问控制规范 条款执行

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

- **极密数据不落盘**
- **机密数据 7 要素强认证**
- **秘密数据授权后可访问**
- **审计日志不可删除**

### 注意事项与警告

- ⚠️ 极密数据泄露 → 最高级事故
- ⚠️ 脱敏不彻底 → 二次泄露风险

**避坑指南：**
- 执行前先读 RULE_META
- 规则修改走 7 步审批
- CI 自检必过

---

## 使用指南

### 适用场景

✅ **推荐使用：**
- 敏感数据/机密/授权/脱敏/访问控制

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

1. RULE_ID=MT_RULE_CLASSIFICATION, STATUS=ACTIVE, 我是否遵守了所有硬约束?
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
- 任何涉及敏感数据的活动必查
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

> 以下为 机密等级与访问控制规范.md 全文, 所有条款均为**硬约束**, 不可绕过。

---
alwaysApply: true
description: 机密、极密、秘密数据的统一分类、访问控制、审计和脱敏规范
---
<!-- RULE_META_START
RULE_ID: MT_RULE_CLASSIFICATION
RULE_NAME: 机密等级与访问控制规范
RULE_LEVEL: L1 核心
RULE_VERSION: v1.2.0
EFFECTIVE_DATE: 2026-09-06
STATUS: ACTIVE
VIOLATION_CODE: CLASSIFICATION-RULE-VIOLATION
INTERCEPT_LAYERS: [before_request, pre_commit, ci_check, git_hook]
RESPONSIBLE_ROLE: super_admin
DEPENDS_ON: [MT_IRON_RULE_12STEPS, MT_RULE_PERM, MT_RULE_GOVERNANCE]
MODIFY_APPROVAL_FLOW: 7_STEP
BYPASS_ALLOWED: false
LAST_CHANGED: 2026-09-19
RULE_META_END -->

# 机密等级与访问控制规范

## 1. 统一密级

系统使用 `EncryptionLevel` 作为唯一机器值，数值越小越敏感：

| 机器值 | 中文名称 | 访问要求 | 典型数据 |
|---|---|---|---|
| `L0_TOP_SECRET` | 极密 | 唯一超级管理员 + VIKEY 在线 + 专项审计 | VIKEY 状态、SA 活动、铁律违规记录 |
| `L1_CONFIDENTIAL` | 机密 | 已认证的管理/安全角色 + 专项审计 | 用户容器、会话、权限识别码 |
| `L2_SECRET` | 秘密 | 已认证用户且具有业务权限 + 访问审计 | 考试、题库、AI 员工和脑库 |

内部（L3）和公开（L4）仍由数据库加密模块管理，但本规范只定义前三个受保护等级。

## 2. 访问判定

- 所有受保护资源必须调用 `PermissionManager.can_access_classification()`，禁止按角色字符串自行判断。
- 未登录、未知角色和失效会话一律拒绝 L0/L1/L2。
- L0 不得仅凭 `super_admin` 字符串放行；必须通过唯一用户校验，并确认当前会话处于 VIKEY 保护状态。
- SA 会话必须持续通过 VIKEY 与 SZU100 双硬件复核；任一设备缺失、指纹异常或检测失败都必须销毁会话。
- 单独插入 VIKEY 或 SZU100 不得触发、续期或恢复 SA 认证；失败尝试必须清除残留 SA 会话状态。
- 权限不足时返回 403；不得返回资源是否存在、表名、字段名、密钥状态或内部错误详情。

## 3. 审计与输出

- L0/L1/L2 的读取、写入、导出、解密和授权失败都必须记录操作类型、操作者、资源分类、结果和追踪 ID。
- 日志不得记录密码、令牌、VIKEY 原始信息、明文密钥或受保护内容。
- API、页面和日志输出默认脱敏；只有业务确实需要且通过同等级授权时才允许明文。
- 不得把 L0/L1/L2 内容发送到外部 AI、第三方服务或未标记的缓存。

## 4. 默认分类与降级

- 新表、新字段和无法识别的敏感资源默认按更高敏感等级处理，完成分类前不得降级为公开。
- 数据库分类以 `classify_table()` 为入口；数据库覆盖配置不得把 L0 降为低敏等级，除非完成规则变更审批。
- 加密依赖不可用时必须拒绝受保护操作，不得静默回退到明文。

## 5. 验证要求

规则校验必须覆盖：密级名称映射、角色清晰度、L0 VIKEY 门槛、未知角色拒绝、审计字段和脱敏输出。


---

## 🪐 仙女座安全事件联动（vv1.1.0 新增）

> 本章定义本规则与仙女座引擎（auto_evolution + autosync_andromeda）的强制协作机制。
> **禁止**仙女座绕过本规则执行任何操作。


### A. 安全事件自动 bump

mt_ai_self_evolution_log 含安全事件 (trigger_type='security_breach', stage_name='fail_closed'):
- ≥ 3 次 / 24h → **强制** [SECURITY] patch bump
- 自动触发 EigenFlux 5 人紧急磋商 (consult_type='security_incident')

### B. 脑库安全标签

brain_enhanced_knowledge 中 SECURITY 标签条目:
- 版本 bump 后**必须**重新 ingest (trigger_type='security_knowledge_refresh')
- 仙女座 auto_evolution 扫描到安全知识 → 自动触发规则重审

### C. 降级安全检测

版本降级 (VERSION 减小) → **必须** SA VIKEY 实检:
- 降级请求无 VIKEY 绑定 → evolution_log 记录为安全事件 → fail-closed

## 🪐 仙女座 AI 审计师联动 (v1.2.0 新增)

> **修复原因**: 仙女座 AI 审计师发现本规则正文无执行层落地条款（只有 RULE_META 里的 INTERCEPT_LAYERS 声明）。
> 仙女座审计结论: 代码落地引用为 0 (纸面规则)。
> 本轮补充 6 条强制落地条款，所有条目的执行层代码已在 2026-09-19 修复脚本中打通。

### A. rule_enforcer daemon 扫描（每 300s）

sys_rule_enforcer daemon **必须** 包含以下扫描项:
- [ ] 新创建的 DB 表/字段是否有 classify_table() 分类标注
- [ ] L0 数据是否有 VIKEY 保护失效的会话
- [ ] L1 数据是否有未审计的导出/解密操作
- [ ] L2 数据是否有外部 AI 调用 (禁止发送到未标记缓存)
- [ ] 审计日志是否脱敏 (不得含明文密钥/令牌/VIKEY)

扫描结果 **必须** 写入 mt_rule_integrity_scan (scan_type='classification_compliance')。
覆盖率 < 100% → fail-closed + before_request 拦截。

### B. before_request 拦截层（强制）

rule_interceptor.register_interceptor(app) **必须** 对以下路径做密级检查:
| 路径模式 | 检查内容 | 失败处置 |
|---------|---------|---------|
| `/api/admin/*` | L0 数据 VIKEY + SA 双校验 | 403 + 销毁会话 |
| `/api/auth/vikey` | VIKEY 状态完整性 | 403 + fail-closed |
| `/api/user/container` | L1 用户容器权限 | 403 + 审计记录 |
| `/api/db/export/*` | L2 数据导出审批 | 403 + 导出日志 |

### C. mt_rule_changelog 自动记录

本规则修改/升级 **必须** 写 mt_rule_changelog (violation_code='CLASSIFICATION-RULE-VIOLATION')。
仙女座 auto_evolution 触发的安全事件 bump **必须** 有 approved_by_7step=1 + sa_vikey_verified=1。

### D. 与其他规则执行层联动

- **联动 MT_IRON_RULE_12STEPS**: L0 VIKEY 失效 → 触发 MT_IR_D8 (安全 fail-closed)
- **联动 MT_RULE_PERM**: PermissionManager.can_access_classification() 是唯一入口
- **联动 MT_RULE_GOVERNANCE**: 弱约束词 **必须** 为 0 (auto_rule_strengthener 自动修复)
- **联动 MT_RULE_VERSION**: 安全事件 ≥ 3/24h → 强制 [SECURITY] patch bump


参考资料

- 原书：《机密等级与访问控制规范》
- 作者：MTSCOS AI 项目规则治理体系
- 免责声明：本 Skill 基于原书内容提炼，仅供个人学习使用
