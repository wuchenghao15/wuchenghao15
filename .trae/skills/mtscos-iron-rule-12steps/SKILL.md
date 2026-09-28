---
name: "mtscos-iron-rule-12steps"
description: 基于《§14 强制开发12步骤独立约束规则》的方法论 Skill。解决核心问题：解决 AI 辅助开发中跳过规范步骤直接产出代码的风险。适合人群：AI Agent + 人类开发者, 所有涉及该领域的活动。典型使用场景：AI Agent 准备修改该领域代码 → Trae 自动触发此 Skill；人类开发者不确定合规性 → 查 Skill；CI 自检失败 → 回溯规则原因。
---

# §14 强制开发12步骤独立约束规则 - 方法论 Skill

> 基于 MTSCOS AI 项目规则治理体系 的《§14 强制开发12步骤独立约束规则》
>
> 本 Skill 仅供个人学习使用

## 概述

### 解决什么问题
解决 AI 辅助开发中跳过规范步骤直接产出代码的风险

### 目标受众
AI Agent + 人类开发者, 所有涉及该领域的活动

### 核心收益
- 硬约束不可绕过
- 自动拦截机制 (4 层)
- AI 自动遵守
- 落库留痕可追溯

---

## 快速上手

> 一句话概括：解决 AI 辅助开发中跳过规范步骤直接产出代码的风险

**最简使用流程：**
1. **Preflight**
2. **Execute**
3. **Verify**
4. **Close**

**核心原则速记：**
- 9 条铁律: 任何开发活动必须先过 Preflight
- 禁止 Jump-Step, exit_code=2 为永久失败
- mandatory_upgrade_flag 不可关闭

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

按 §14 强制开发12步骤独立约束规则 条款执行

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

- **9 条铁律: 任何开发活动必须先过 Preflight**
- **禁止 Jump-Step, exit_code=2 为永久失败**
- **mandatory_upgrade_flag 不可关闭**
- **SA bypass 需 VIKEY 在线**
- **落库表不可删**
- **版本号四级强制**
- **CI 自检失败阻断合并**
- **before_request 拦截生效**

### 注意事项与警告

- ⚠️ AI Agent 未走 Preflight 就改代码 → 3 层拦截 (git hook + Flask before_request + CI)
- ⚠️ 违反事件永久落库 mt_iron_rule_violations 不可删除

**避坑指南：**
- 执行前先读 RULE_META
- 规则修改走 7 步审批
- CI 自检必过

---

## 使用指南

### 适用场景

✅ **推荐使用：**
- 任何新建功能/修改源码/Bug修复/配置调整/SQL变更

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

1. RULE_ID=MT_IRON_RULE_12STEPS, STATUS=ACTIVE, 我是否遵守了所有硬约束?
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
- Trae 自动触发于任何开发活动
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

> 以下为 §14强制开发12步骤独立约束规则.md 全文, 所有条款均为**硬约束**, 不可绕过。

---

---
alwaysApply: true
---
<!-- RULE_META_START
RULE_ID: MT_IRON_RULE_12STEPS
RULE_NAME: §14 强制开发12步骤独立约束规则
RULE_LEVEL: L0 IRON_RULE
RULE_VERSION: v1.5.0
EFFECTIVE_DATE: 2026-08-10
STATUS: ACTIVE
VIOLATION_CODE: DEV-FLOW-VIOLATION-IRON-RULE
INTERCEPT_LAYERS: [dev_activity_preflight, pre_commit, before_request, ci_check, git_hook]
RESPONSIBLE_ROLE: super_admin
DEPENDS_ON: []
MODIFY_APPROVAL_FLOW: 7_STEP (提议→2管理员同意→EigenFlux 5人磋商≥4/5→SA终审→保密撤回)
BYPASS_ALLOWED: false
LAST_CHANGED: 2026-09-20
CHANGELOG:
  v1.5.0 (2026-09-20, MINOR): 新增 MT_IR_D10 铁律 — A轮/B轮强制轮换, 非核心人员(含A组51人/专家团队/AI代表团)每 cycle 必须换, 仅核心角色固定; 新增 §5.3 核心/非核心人员定义; STEP_2A_ROUND / STEP_31_B_ROUND 轮换约束; 新增违反触发详表; 新增落库字段 rotation_required + rotation_done
RULE_META_END -->
# MTSCOS AI 项目 §14 强制开发12步骤独立约束规则

> **规则层级**：IRON_RULE (L0) - 最高级别铁律
> **规则代码**：MT_IR_DEV_12_STEPS
> **规则版本**：v1.0.0
> **生效日期**：2026-08-10
> **绕过许可**：bypass_allowed = False（**禁止任何绕过，包括超级管理员调试**）
> **触发方式**：所有开发活动入口、代码提交钩子、规则引擎 before_request 链
> **违反异常**：`DEV-FLOW-VIOLATION-IRON-RULE` - 立即阻断 + 审计 + EigenFlux告警

---

## 🔒 §0. 声明：本规则的至高无上地位

### 0.1 本规则独立于其他所有规则

| 属性 | 说明 |
|------|------|
| **独立性** | 本规则单独成章，不依赖任何其他规则文件，不被任何其他规则覆盖或推翻 |
| **优先级** | IRON_RULE(L0) 最高层级，即使与其他规则冲突也以本规则为准 |
| **不可绕开** | `bypass_allowed=False`，除超级管理员 wuchenghao15 外，其他任何人不得调用任何 bypass 接口 |
| **不可修改** | 本规则的任何修改必须经过：7步完整审批 + EigenFlux AI5人全票通过 + SA VIKEY终审 + 保密撤回双重校验 |
| **无条件执行** | 无论任何条件（紧急修复、生产事故、调试模式、开发模式）都必须完整执行12步骤 |

### 0.2 违反后果（绝对强制执行）

任何开发活动（新建功能、修改代码、修复Bug、调整配置、数据库变更）只要违反以下任一条款，将触发：
> **维护活动条件补充**：系统维护、版本升级、安全补丁、数据迁移、架构优化、性能调优、巡检排查等所有维护活动同样适用本规则，必须从 STEP_1_PROPOSAL 起步完整执行12步骤，不得豁免、不得简化、不得以"紧急维护"为由绕过。维护活动的 flow_id 创建、状态转移、落库、投喂、Git同步、1000轮测试等所有条款与开发活动执行标准完全一致。

```
1. 立即阻断：DEV-FLOW-VIOLATION-IRON-RULE 异常抛出，操作终止
2. 审计记录：写入 mt_iron_rule_violations 表（不可删除、不可修改、不可覆盖）
3. EigenFlux 全票告警：5人磋商自动触发
4. 账号锁定：操作者账号锁定至 SA VIKEY 手动解锁
5. 代码回滚：已提交的代码自动回滚至上一合法版本
6. 脑库投喂：违规行为作为负面教材投喂AI脑库
```

---

## 📋 §1. 开发12步骤完整定义（18节点状态机）

### 1.1 12步骤 + 18节点全量枚举

| 步骤编号 | 节点代码 | 节点名称 | 强制要求 | 落库字段 |
|---------|---------|---------|---------|---------|
| **1** | `STEP_1_PROPOSAL` | 提案 | ✅ 必须填写完整提案（标题/摘要/范围/目标版本），禁止空提案 | `proposal_title`, `proposal_summary`, `proposal_json` |
| **2** | `STEP_2A_ROUND` | A轮讨论 | ✅ 4方强制出席（缺一不可）：<br>① A组51人含张晓峰<br>② EigenFlux网络<br>③ EigenFlux专家<br>④ AI员工代表团（偶数人数）<br>✅ **每个参与的AI员工必须提出建设性意见并表决**（禁止仅出席不表态）<br>✅ **EigenFlux AI与专家团队必须针对提案提出专业意见和决议，并记录为讨论议案**（`a_round_discussion_json.motions`）<br>🔄 **强制轮换**：A组51人中**非核心人员**（剔除张晓峰）必须每 cycle 轮换≥50%；EigenFlux 专家团队必须轮换≥40%；AI员工代表团必须**全部轮换**（核心角色见§5.3） | `a_round_panels_json`, `a_round_attendance_json`, `a_round_discussion_json`, `rotation_required`, `rotation_done` |
| **3** | `STEP_3_ZXF_DECISION` | 张晓峰当场表决 | ✅ 张晓峰必须二选一：<br>`SUSPEND`(暂缓权) → 走B轮<br>`NOT_USE_SUSPEND`(不使用) → 直过<br>✅ **若不使用暂缓提案权(NOT_USE_SUSPEND)**：张晓峰必须结合表决团和专家的综合意见和决议，提出决策性决议（`zhangxiaofeng_decision_advisory`）<br>✅ **若使用暂缓提案权(SUSPEND)**：张晓峰必须提出决策意见，一并上报SA最终裁决（`super_admin_judgment`） | `zhangxiaofeng_decision`, `zhangxiaofeng_decision_advisory` |
| **3.1** | `STEP_31_B_ROUND` | B轮再讨论 | ✅ 张晓峰**不得参加B轮**<br>🔄 **强制轮换**：B轮所有参与人员**必须与A轮不同**（核心角色也必须轮换，包括 EigenFlux 专家团队全部换人、AI 代表团全部换人）<br>✅ 3.1.1 有异议→SA决断<br>✅ 3.1.2 超半数→自动通过 | `b_round_*`, `super_admin_judgment`, `rotation_required`, `rotation_done` |
| **3.1.1** | `STEP_311_SA_JUDGMENT` | 超级管理员决断 | ✅ 仅 wuchenghao15 可执行<br>✅ 必须通过 VIKEY 实时检测 | `super_admin_judgment` |
| **3.1.2** | `STEP_312_AUTO_PASS` | 方案自动通过 | ✅ 不同意暂缓方案超半数<br>✅ 必须报备SA | `b_round_disagree_suspend` |
| **3.2** | `STEP_32_PASS_SKIP_B` | 直接通过跳过B轮 | ✅ 张晓峰 NOT_USE_SUSPEND<br>✅ 报备SA，B轮直接跳过 | - |
| **4** | `STEP_4_CLERK_RECORD` | 会议记录员全程记录 | ✅ 孙文档（AI文档专员）记录<br>✅ 记录讨论经过 + 异议 + 表决统计 | `clerk_record_json`, `clerk_vote_summary` |
| **5** | `STEP_5_IMPL_DOCKING` | 专业实施团队对接 | ✅ 田经理(AI团队经理)对接<br>✅ 记录详细名录 + 详细实施方案 | `impl_team_contact_json`, `impl_plan_detail_json` |
| **6** | `STEP_6_AI_TEAM_COORD` | 统筹AI实施团队 | ✅ 三角治理：<br>田经理(统筹) + 石监理(验收) + 韩队长(执行)<br>✅ 现有AI员工全员参与 | `ai_team_coord_json`, `ai_core_roles_json` |
| **7** | `STEP_7_EXECUTE` | 下场实施 | ✅ 按团队管理和实施方案执行<br>✅ 每步实施必须可追溯 | `execute_steps_json` |
| **8** | `STEP_8_ACCEPTANCE` | 收场验收 | ✅ 石监理验收<br>✅ 记录实施步骤 ↔ 实际结果映射<br>✅ 落库 mt_fix_implementations | `acceptance_json`, `acceptance_passed`, `acceptance_step_results_json` |
| **9A** | `STEP_9A_PASS_OR_LOOPBACK` | 验收结果分支 | ✅ 通过 → STEP_9B<br>✅ 不通过 → 投喂AI脑库复盘 → 跳回 STEP_1 (loopback_count+1) | `loopback_count` |
| **9B** | `STEP_9B_SUMMARY` | 汇总上报与投喂 | ✅ **四必落库**：<br>① 上报超级管理员<br>② 记录数据库<br>③ 投喂经验到AI脑库<br>④ 投喂系统异常错误特征库 | `summary_report_json`, `db_written`, `brain_fed`, `experience_fed`, `anomaly_fed`, `super_admin_report_status` |
| **10** | `STEP_10_SMART_VERSION_UPGRADE` | 智能判断版本升级 | ✅ `mandatory_upgrade_flag=True` 强制每次必评估<br>✅ 5项阈值规则任一命中即升级 | `smart_upgrade_version`, `smart_upgrade_should_upgrade`, `smart_upgrade_reasons_json`, `smart_upgrade_triggered`, `smart_upgrade_log_id` |
| **11** | `STEP_11_AUTO_GIT_SYNC` | 自动同步git和GitHub | ✅ 不得跳过<br>✅ SSH优先 / remote -v确认 / 结构化返回 | `git_sync_remote_name`, `git_sync_target_branch`, `git_sync_auth_mode`, `git_sync_commit_hash`, `git_sync_commit_subject`, `git_sync_status`, `git_sync_error`, `git_sync_json` |
| **12** | `STEP_12_TEST1000` | 1000轮测试 | ✅ 三大类占比固定：<br>正常逻辑40% + 异常逻辑30% + 黑客攻击30%<br>✅ 测试完毕重复步骤1-11后跳出 | `test1000_total`, `test1000_pass`, `test1000_fail`, `test1000_vuln`, `test1000_json` |
| **终态** | `FINAL_DONE` | 交付 | ✅ 所有前置步骤完成<br>✅ 最终状态不可回退 | `final_status='DONE'` |

### 1.2 状态转移边（硬编码不可修改）

```text
_MT_DEV_FLOW_EDGES_IRON_RULE = {
    STEP_1_PROPOSAL               → STEP_2A_ROUND
    STEP_2A_ROUND                 → STEP_3_ZXF_DECISION
    STEP_3_ZXF_DECISION           → {STEP_31_B_ROUND, STEP_32_PASS_SKIP_B}
    STEP_31_B_ROUND               → {STEP_311_SA_JUDGMENT, STEP_312_AUTO_PASS}
    STEP_311_SA_JUDGMENT          → STEP_4_CLERK_RECORD
    STEP_312_AUTO_PASS            → STEP_4_CLERK_RECORD
    STEP_32_PASS_SKIP_B           → STEP_4_CLERK_RECORD
    STEP_4_CLERK_RECORD           → STEP_5_IMPL_DOCKING
    STEP_5_IMPL_DOCKING           → STEP_6_AI_TEAM_COORD
    STEP_6_AI_TEAM_COORD          → STEP_7_EXECUTE
    STEP_7_EXECUTE                → STEP_8_ACCEPTANCE
    STEP_8_ACCEPTANCE             → STEP_9A_PASS_OR_LOOPBACK
    STEP_9A_PASS_OR_LOOPBACK      → {STEP_1_PROPOSAL(loopback), STEP_9B_SUMMARY}
    STEP_9B_SUMMARY               → STEP_10_SMART_VERSION_UPGRADE
    STEP_10_SMART_VERSION_UPGRADE → STEP_11_AUTO_GIT_SYNC
    STEP_11_AUTO_GIT_SYNC         → STEP_12_TEST1000
    STEP_12_TEST1000              → FINAL_DONE
    FINAL_DONE                    → FINAL_DONE  (自环，终态不可变更)
}
```

> **硬约束**：任何不在上述边集合中的转移直接抛出 `[DEV-FLOW-VIOLATION-IRON-RULE] 非法状态转移: X → Y`，不会执行任何兜底逻辑。

---

## 🚫 §2. 8条不可绕开核心铁律

| 铁律编号 | 铁律内容 | 违反触发 |
|---------|---------|---------|
| **MT_IR_D1** | **不得绕开**：所有开发活动必须从 STEP_1_PROPOSAL 起步，任何代码变更必须有对应的 flow_id | 直接操作代码/数据库但无合法 flow_id → 阻断 |
| **MT_IR_D2** | **不得跳步**：状态转移严格按 `_MT_DEV_FLOW_EDGES_IRON_RULE` 执行，跳步直接阻断 | 从 STEP_1 直接跳到 STEP_7 → 阻断 |
| **MT_IR_D3** | **强制出席**：A轮4方强制出席，缺任一不得进入 STEP_3；AI员工代表团人数必须为偶数 | 51人缺1 / AI代表团7人(奇数) → 阻断 |
| **MT_IR_D4** | **强制落库**：所有讨论/表决/实施/验收/测试结果必须实时落库5张表 | 任一步骤落库失败 → 回滚该步骤 |
| **MT_IR_D5** | **强制投喂**：验收不通过/异常特征/经验必须投喂AI脑库3张表 | step9不通过但未投喂 → 阻断进入下一步 |
| **MT_IR_D6** | **强制升级**：步骤10 `mandatory_upgrade_flag=True` 每次必评估，禁止跳过版本判断 | 跳过步骤10 → 阻断进入步骤11 |
| **MT_IR_D7** | **强制同步**：步骤11自动同步git和GitHub，禁止跳过（auth_mode=SSH优先） | 跳过git同步 → 阻断进入步骤12 |
| **MT_IR_D8** | **强制测试**：步骤12必须完成1000轮测试（正常400+异常300+黑客300），重复步骤1-11后才能跳出 | 测试轮数不足 / 占比不对 → 阻断进入FINAL_DONE |
| **MT_IR_D9** | **强制前置拦截**：所有开发活动入口（AI助手对话/CLI/API路由）必须执行 dev_activity_preflight 前置检查，检测到开发活动未启动合法 flow_id 则立即阻断+告警+落库 | AI助手收到开发请求但 flow_id 不在 mt_dev_flow_session 中 → 阻断 + 提示「必须先走12步骤」 |
| **MT_IR_D10** | **强制轮换**：A轮/B轮非核心人员每 cycle 必须轮换 — A轮A组非核心人员≥50%换、EigenFlux专家≥40%换、AI代表团**全部**换；B轮参与人员**全部**与A轮不同（核心角色含专家团队也必须轮换）。**核心角色仅 6 人固定**（张晓峰/孙文档/田经理/石监理/韩队长/wuchenghao15） | A轮 A组51人中非核心与上一 cycle 重合>50% → 阻断 STEP_3；A轮专家团队重合>60% → 阻断；B轮有任何 A轮 人员（含专家团队）重复 → 阻断 STEP_4 |

### 2.1 10条铁律违反触发详表（强制执行落地点）

> 以下为每条铁律的**精确违反触发条件 + 拦截层 + 落库表 + 告警动作**，由 `flask-app/ai_engines/rules_engine/` 模块在代码层强制执行，禁止绕过。

| 铁律编号 | 违反触发条件 | 拦截层 | 落库表 | 告警动作 |
|---------|------------|--------|--------|---------|
| **MT_IR_D1** | 检测到代码/数据库变更但 `flow_id` 不在 `mt_dev_flow_session` 中或 `current_step='OPEN'` | pre_commit + before_request + git_hook | mt_iron_rule_violations + mt_rule_violation_alert | 抛 `DEV-FLOW-VIOLATION-IRON-RULE` + 投喂 EigenFlux 5人磋商 + 投喂 AI脑库 + 锁定操作者账号 |
| **MT_IR_D2** | 状态转移 `from_step → to_step` 不在 `_MT_DEV_FLOW_EDGES_IRON_RULE` 边集合中 | before_request + ci_check | mt_iron_rule_violations + mt_dev_flow_events | 抛 `DEV-FLOW-VIOLATION-IRON-RULE` + 回滚当前步骤 + 投喂异常特征库 |
| **MT_IR_D3** | A轮4方任一缺席（A组51人缺1/EigenFlux网络离线/EigenFlux专家未到/AI代表团奇数人） | before_request | mt_iron_rule_violations | 阻断进入 STEP_3 + 记录缺席档案 + 累计3次取消资格 |
| **MT_IR_D4** | 任一步骤的必填字段为空或落库 `mt_dev_flow_session/events/brain_feed_log/experience_library/anomaly_feature_library` 失败 | ci_check | mt_iron_rule_violations | 回滚该步骤 + 阻断进入下一步 + 投喂异常特征库 |
| **MT_IR_D5** | STEP_9A 不通过但未投喂 AI脑库 3 张表（`mt_ai_brain_feed_log`/`mt_experience_library`/`mt_anomaly_feature_library`） | before_request + ci_check | mt_iron_rule_violations | 阻断进入 STEP_10 + 强制补投 + 投喂 EigenFlux |
| **MT_IR_D6** | STEP_10 未评估或 `mandatory_upgrade_flag=False` | before_request | mt_iron_rule_violations | 阻断进入 STEP_11 + 强制重新评估 |
| **MT_IR_D7** | STEP_11 跳过 Git 同步或 `auth_mode` 非 SSH 优先 | ci_check + git_hook | mt_iron_rule_violations | 阻断进入 STEP_12 + 强制重新同步 |
| **MT_IR_D8** | STEP_12 测试轮数<1000 或 正常/异常/黑客占比≠40%/30%/30% 或 未重复步骤1-11 | ci_check | mt_iron_rule_violations | 阻断进入 FINAL_DONE + 强制重新测试 + 投喂异常特征库 |
| **MT_IR_D9** | AI助手对话/CLI/API路由检测到开发活动（含代码修改/配置变更/数据库变更关键词）但 `flow_id` 不在 `mt_dev_flow_session` 中或 `current_step` 非 `STEP_7_EXECUTE`/`STEP_8_ACCEPTANCE`/`STEP_9*`/`STEP_10*`/`STEP_11*`/`STEP_12*` | dev_activity_preflight | mt_iron_rule_violations + mt_rule_violation_alert | 抛 `DEV-FLOW-VIOLATION-IRON-RULE` + 立即阻断 + 提示「检测到开发活动，必须先走§14 12步骤」+ 投喂 EigenFlux 5人磋商 + 投喂 AI脑库 |
| **MT_IR_D10** | A轮 A组非核心人员与上一 cycle 重合率>50% / 专家团队重合>60% / AI代表团未全部轮换; B轮有任何 A轮 参与人员（含专家团队/AI代表团）重复 | before_request + dev_activity_preflight | mt_iron_rule_violations + mt_rule_violation_alert | A轮 → 阻断进入 STEP_3 + 强制重新组 A轮 + 记录 rotation_violation + 投喂 EigenFlux; B轮 → 阻断进入 STEP_4 + 强制重新组 B轮 + 专家团队全部换人 + 投喂异常特征库 |

> **强制执行声明**：以上10条铁律的违反触发块由 `rules_engine.dev_activity_preflight`（第4层对话入口前置拦截）、`rules_engine.rule_interceptor`（Flask before_request）和 `rules_engine.rule_pre_commit`（Git pre-commit hook）在代码层强制执行，**禁止任何人（包括超级管理员 wuchenghao15）以任何理由绕过**。违反记录自动落库 `mt_iron_rule_violations` + `mt_rule_violation_alert`，并自动投喂 EigenFlux 5人磋商 + AI脑库。

---

## 🔐 §3. 强制拦截机制（4层拦截无死角）

### 3.1 第1层：入口拦截 - 开发活动必须创建 flow

```
触发时机：任何代码/配置/数据库变更操作入口
拦截逻辑：
  1. 检查是否存在合法 flow_id（来自 mt_dev_flow_session 且 current_step != 'OPEN'）
  2. 检查 flow_id 对应的 current_step 是否允许当前操作
  3. 无合法 flow_id → 抛出 DEV-FLOW-VIOLATION-IRON-RULE
```

### 3.2 第2层：状态转移拦截 - 禁止跳步

```
触发时机：每次调用 _mt_dev_flow_transition()
拦截逻辑：
  1. 校验 from_step → to_step 是否在 _MT_DEV_FLOW_EDGES_IRON_RULE 中
  2. 校验 from_step 对应的所有必填字段是否已落库且非空
  3. 校验 loopback 跳转必须来自 STEP_9A 且 loopback_count++
  4. 任一校验失败 → 抛出 DEV-FLOW-VIOLATION-IRON-RULE
```

### 3.3 第3层：代码提交拦截 - Git Hook 强制校验

```
触发时机：pre-commit / pre-push Git Hook
拦截逻辑：
  1. 读取最近一次 git commit message / branch name 中的 flow_id
  2. 查询 mt_dev_flow_session 校验 flow_id 存在且 final_status='DONE'
  3. 未完成12步骤的开发活动禁止提交和推送
  4. 校验失败 → git commit/push 被拒绝，提示补完12步骤
```

### 3.4 第4层：对话入口前置拦截 - 开发活动前置提示+违规即终止（v1.3.0 新增）

```
触发时机：AI助手对话入口 / CLI开发命令 / API路由收到开发活动请求
拦截逻辑：
  1. dev_activity_preflight 检测请求中是否包含开发活动关键词
     （代码修改/配置变更/数据库变更/新建功能/修复Bug/调整配置等）
  2. 若检测到开发活动：
     a. 检查请求中是否携带合法 flow_id（来自 mt_dev_flow_session 且 current_step ∈ 允许实施步骤集合）
     b. flow_id 合法 → 放行，记录 dev_activity_type
     c. flow_id 缺失/非法 → 立即阻断 + 返回前置提示：
        「[§14 IRON_RULE MT_IR_D9] 检测到开发活动，必须先走12步骤。
         请先创建 flow_id（step1_create_proposal），完成 STEP_1→STEP_7 后方可实施。」
  3. 违规记录自动落库 mt_iron_rule_violations (viol_rule='MT_IR_D9')
  4. 自动投喂 mt_rule_violation_alert → EigenFlux 5人磋商 + AI脑库
  5. 性能要求：前置检查 < 5ms，使用内存级 LRU 缓存 flow_id 状态（TTL=30s）
```

> **dev_activity_preflight 白名单**（非开发活动不拦截，0 开销）：
> - 纯查询/浏览/只读操作（GET 请求、首页、静态资源）
> - 公开 API（/api/health, /api/homepage/stats）
> - 已携带合法 flow_id 且 current_step ∈ {STEP_7_EXECUTE, STEP_8_ACCEPTANCE, STEP_9A_*, STEP_9B_SUMMARY, STEP_10_*, STEP_11_*, STEP_12_*}
>
> **dev_activity 关键词检测清单**（任一命中即视为开发活动）：
> ```
> 开发活动关键词：新建功能|修改代码|修复Bug|调整配置|数据库变更|新增路由|新增API|
>               重构|部署|安装|升级|迁移|删除文件|编辑文件|写入文件|
>               创建表|ALTER TABLE|INSERT|UPDATE|DELETE|DROP|
>               git commit|git push|git add|pip install|npm install|
>               ollama|docker|systemctl|launchctl|crontab
> ```
> **性能优化**：flow_id 状态使用 `functools.lru_cache(maxsize=1024)` 缓存，TTL=30s，避免每次查询数据库。

---

## 🗄️ §4. 5张强制落库表（不可省略任一张）

| 表名 | 用途 | 必填字段 | 不可删除 |
|------|------|---------|---------|
| `mt_dev_flow_session` | 流程当前步骤+状态快照+投喂标记+git同步记录+版本升级记录 | flow_id, current_step, proposal_title, created_at | ✅ |
| `mt_dev_flow_events` | 每次状态推进的事件/触发人/时间戳/载荷 | ev_id, flow_id, from_step, to_step, event_kind, triggered_at | ✅ |
| `mt_ai_brain_feed_log` | 投喂AI脑库日志（步骤9不通过复盘 & 步骤9B总结必触发） | feed_id, flow_id, feed_kind, feed_content, triggered_at | ✅ |
| `mt_experience_library` | 投喂经验库（成功流程沉淀） | exp_id, flow_id, exp_content, exp_rating, created_at | ✅ |
| `mt_anomaly_feature_library` | 投喂系统异常错误特征库（测试1000轮失败特征） | feat_id, flow_id, anomaly_type, anomaly_feature, created_at | ✅ |

> **附加表**：`mt_iron_rule_violations` - 违反本独立约束规则的审计日志（不可删除、不可修改）

---

## 🤖 §5. AI员工角色与人数强制约束

### 5.1 固定角色（不可变更）

| 步骤 | 角色 | 姓名 | 职责 | 缺席处理 |
|------|------|------|------|---------|
| A轮讨论 | 会议记录员 | 孙文档 | 全程记录 | 阻断进入STEP_4 |
| A轮讨论 | 强制出席方 | 张晓峰 | A轮当场表决 | 阻断进入STEP_3 |
| 步骤5 | 实施团队对接 | 田经理 | 记录对接名录和方案 | 阻断进入STEP_6 |
| 步骤6 | AI团队监理 | 石监理 | 制定验收标准 | 阻断进入STEP_7 |
| 步骤6 | AI团队队长 | 韩队长 | 统筹执行 | 阻断进入STEP_7 |
| 步骤8 | 收场验收 | 石监理 | 验收+记录 | 阻断进入STEP_9A |

### 5.2 AI员工代表团人数强制偶数

当前代表团（6人 ✅ 偶数合规）：
```
陈安全 / 林审计 / 赵性能 / 钱合规 / 方数据 / 孙文档
```

> **约束**：`len(AI_EMPLOYEE_DELEGATION) % 2 == 0`，奇数直接阻断A轮。

### 5.3 核心角色 vs 非核心人员定义（v1.5.0 新增）

**核心角色（固定，不轮换，仅 6 人）**：

| 角色 | 姓名 | 固定职责 | 可被轮换的条件 |
|------|------|---------|---------------|
| 超级管理员 | wuchenghao15 | SA 终审 + VIKEY | 永不轮换 |
| A轮表决人 | 张晓峰 | A轮 SUSPEND/NOT_USE_SUSPEND | 永不轮换 |
| 会议记录员 | 孙文档 | STEP_4 全程记录 | 永不轮换 |
| AI团队经理 | 田经理 | STEP_5 对接 + STEP_6 统筹 | 永不轮换 |
| AI团队监理 | 石监理 | STEP_6 验收标准 + STEP_8 验收 | 永不轮换 |
| AI团队队长 | 韩队长 | STEP_6 执行统筹 | 永不轮换 |

**非核心人员（每 cycle 强制轮换）**：

| 群体 | 当前规模 | 轮换要求 | 轮换方式 | 违反触发 |
|------|---------|---------|---------|---------|
| A组（剔除张晓峰后） | 50 人 | **≥50% 必须换** | 按 `employee_id` hash round-robin + 排除上 cycle 出席者 | 重合率>50% → 阻断 STEP_3 |
| EigenFlux 专家团队 | 12 人 | **≥40% 必须换**（B轮**全部**换） | 按专家专业领域分组 + 排除上 cycle 出席者 | 重合率>60% → 阻断 STEP_3 / B轮有重复 → 阻断 STEP_4 |
| AI 员工代表团 | 6 人 | **100% 必须换**（每 cycle 全部新人，B轮同样全部新人） | 从 AI员工池（33,525）里按 `cycle_index % pool_size` 选 | 有任何上 cycle 成员 → 阻断 STEP_3 / STEP_4 |
| EigenFlux 网络成员 | 动态 | **≥50% 必须换** | 同 AI 代表团 | 重合率>50% → 阻断 STEP_3 |

**轮换落库字段**（STEP_2A_ROUND + STEP_31_B_ROUND 必须写入）：
```python
# mt_dev_flow_session 新增字段
rotation_required: {
    "a_group": {"prev_attended": [...], "rotation_rate": 0.50, "actual_rotated": [...], "ok": True/False},
    "experts":  {"prev_attended": [...], "rotation_rate": 0.40, "actual_rotated": [...], "ok": True/False},
    "ai_delegation": {"prev_attended": [...], "rotation_rate": 1.00, "actual_rotated": [...], "ok": True/False},
}
rotation_done: true/false  # STEP_2A_ROUND 落库时必须为 true
```

**轮换算法**（由 `sys_rule_enforcer` 每 cycle 自动执行）：
```
1. 读上一 cycle 的 a_round_attendance_json → prev_attended 列表
2. 从 employee_registry 里按 role 过滤候选池
3. 排除 prev_attended 成员
4. cycle_index 递增 → 不同 cycle 自动选不同人
5. 最终出席列表落库 rotation_required.actual_rotated
6. rotation_done = True → 才能进入 STEP_3
```

**轮换豁免**（仅 SA VIKEY 实时检测后可用）：
- cycle 启动时候选池人数 < 轮换要求人数 → 自动降级（如 AI 代表团池子只剩 4 人可轮换 → 允许保留 2 人上 cycle 成员）
- 豁免必须落库 `rotation_exemption_reason` + `rotation_exemption_signed_by=SA`
- SA 终审时必须在 `zhangxiaofeng_decision_advisory` 里引用豁免理由，否则不生效

> **设计原理**：强制轮换防止"固定小圈子垄断决策"、"路径依赖思维固化"、"AI 员工与人类专家长期形成利益小团体"；每 cycle 新成员能带来新视角，减少集体盲点。核心 6 人固定是因为职责不可替代（SA 终审、石监理验收、韩队长执行）。

---

## 🧪 §6. 步骤10智能版本升级强制阈值

### 6.1 5项阈值（任一命中即**必须**升级，每次必评估）

| 条件 | 阈值 | 升级类型 |
|------|------|---------|
| `files_changed` ≥ | 1 | 基础触发 |
| `fixes_count` ≥ | 1 | 基础触发 |
| `vuln_found` ≥ | 1 | 基础触发 |
| `\|risk_score_delta\|` ≥ | 100 | 基础触发 |
| `new_tables` ≥ | 1 | 基础触发 |

### 6.2 智能bump版本号规则（不可修改）

```
vuln ≥ 10  或  new_tables ≥ 2                   →  L1 bump (主版本号, vX.0.0.0.0)
fixes ≥ 5  或  Δrisk ≥ 1000                     →  L2 bump (次版本号, v0.X.0.0.0)
vuln ≥ 3  或  new_tables ≥ 1                    →  L3 bump (修订号, v0.0.X.0.0)
fixes ≥ 2  或  vuln ≥ 1                          →  L4 bump (补丁号, v0.0.0.X.0)
其他所有情况                                      →  L5 bump (构建号, v0.0.0.0.X)
```

> **强制要求**：`mandatory_upgrade_flag` 必须恒为 `True`，不可设置为 `False`。

---

## ⚙️ §7. 步骤11 Git同步强制配置

遵循经验959804，6条铁律：

| 编号 | 强制配置 | 违反处理 |
|------|---------|---------|
| 1 | 路径双引号 + `cwd=project_dir` 传参 | 阻断进入步骤12 |
| 2 | 先 `git remote -v` 确认URL → 再决定 set-url/add/push | 阻断进入步骤12 |
| 3 | `auth_mode` 默认SSH优先，避免PAT交互式认证卡住 | 阻断进入步骤12 |
| 4 | 返回结构化结果：`{status, commit_hash, commit_subject, error, git_output[]}` | 阻断进入步骤12 |
| 5 | 状态枚举：`SUCCESS / DRY_RUN_OK / PARTIAL / FAILED / SKIPPED` | 阻断进入步骤12 |
| 6 | 非仓库目录安全返回FAILED不panic | 阻断进入步骤12 |

---

## 🧪 §8. 步骤12 1000轮测试强制占比

| 测试类型 | 说明 | 强制轮数 | 占比 |
|---------|------|---------|------|
| `NORMAL_LOGIC` | 正常按照系统或功能设计要求正常逻辑测试 | 400轮 | 40% |
| `ABNORMAL_LOGIC` | 按照非正常逻辑及要求测试 | 300轮 | 30% |
| `HACKER_ATTACK` | 按照黑客攻击方式测试 | 300轮 | 30% |

> **附加约束**：测试完毕后必须**重复步骤1-11一遍**，然后才能从STEP_12跳出到FINAL_DONE。

---

## ✅ §9. 自查清单（开发前/开发中/上线前必查）

### 9.1 开发活动启动前
- [ ] 已创建 STEP_1_PROPOSAL，flow_id 已生成
- [ ] 提案包含完整的标题/摘要/范围/目标版本
- [ ] A轮4方全部确认出席
### 1.1 12步骤 + 18节点全量枚举

| 步骤编号 | 节点代码 | 节点名称 | 强制要求 | 落库字段 |
|---------|---------|---------|---------|---------|
| **1** | `STEP_1_PROPOSAL` | 提案 | ✅ 必须填写完整提案（标题/摘要/范围/目标版本），禁止空提案 | `proposal_title`, `proposal_summary`, `proposal_json` |
| **2** | `STEP_2A_ROUND` | A轮讨论 | ✅ 4方**必须**出席，但允许缺席并记录档案：<br>① 缺席1次记录档案；累计缺席**3次**→取消A/B轮讨论资格<br>② 累计缺席**5次及以上**→列入黑名单踢出讨论席<br>③ A轮累计缺席**5人及以上**→报SA VIKEY后直接跳至STEP_31_B_ROUND（B轮暂替A轮讨论）<br>④ AI员工代表大会人数须为偶数<br>🔄 **强制轮换（MT_IR_D10）**：A组51人中**非核心人员**（剔除张晓峰）每 cycle 轮换≥50%；EigenFlux 专家团队轮换≥40%；AI员工代表团**100% 全部换新**<br>✅ **每个参与的AI员工必须提出建设性意见并表决**：意见落库 `a_round_discussion_json.ai_employee_opinions`，表决落库 `a_round_discussion_json.ai_employee_votes`，禁止仅出席不表态（违反→该AI员工本次流程表决作废+记录档案）<br>✅ **EigenFlux AI与专家团队必须针对提案提出专业意见和决议**：落库 `a_round_discussion_json.eigenflux_motions`（含专家ID/专业领域/意见正文/决议结论），并记录为讨论议案 `a_round_discussion_json.motions` | `a_round_panels_json`, `a_round_attendance_json`, `a_round_discussion_json`, `rotation_required`, `rotation_done` |
| **3** | `STEP_3_ZXF_DECISION` | 张晓峰当场表决 | ✅ 张晓峰必须二选一：<br>`SUSPEND`(暂缓权) → 走B轮<br>`NOT_USE_SUSPEND`(不使用) → 直过<br>✅ 若张晓峰未出席A轮，在B轮加入讨论并行使表决权<br>✅ **若不使用暂缓提案权(NOT_USE_SUSPEND)**：张晓峰必须结合表决团(A组)和EigenFlux专家的综合意见和决议，提出决策性决议（落库 `zhangxiaofeng_decision_advisory`，须引用≥1条专家意见+≥1条AI员工意见）<br>✅ **若使用暂缓提案权(SUSPEND)**：张晓峰必须提出决策意见（`zhangxiaofeng_decision_advisory`），一并上报SA最终裁决（`super_admin_judgment`），SA须在VIKEY在线状态下裁决 | `zhangxiaofeng_decision`, `zhangxiaofeng_decision_advisory` |
| **3.1** | `STEP_31_B_ROUND` | B轮再讨论 | ✅ 正常流程：张晓峰**不得参加B轮**<br>🔄 **强制轮换（MT_IR_D10）**：B轮所有参与人员（**核心角色也不含**，含 EigenFlux 专家团队全部换人、AI 代表团全部换人）**必须**与A轮不同<br>✅ A轮特殊流程（缺席≥5人触发）：B轮暂替A轮讨论，**张晓峰加入B轮并行使表决权**<br>✅ 3.1.1 有异议→SA决断<br>✅ 3.1.2 超半数→自动通过 | `b_round_*`, `super_admin_judgment`, `rotation_required`, `rotation_done` |
| **3.1.1** | `STEP_311_SA_JUDGMENT` | 超级管理员决断 | ✅ 仅 wuchenghao15 可执行<br>✅ 必须通过 VIKEY 实时检测 | `super_admin_judgment` |
| **3.1.2** | `STEP_312_AUTO_PASS` | 方案自动通过 | ✅ 不同意暂缓方案超半数<br>✅ 必须报备SA | `b_round_disagree_suspend` |
| **3.2** | `STEP_32_PASS_SKIP_B` | 直接通过跳过B轮 | ✅ 张晓峰 NOT_USE_SUSPEND<br>✅ 报备SA，B轮直接跳过 | - |
| **4** | `STEP_4_CLERK_RECORD` | 会议记录员全程记录 | ✅ 孙文档（AI文档专员）记录<br>✅ 记录讨论经过 + 异议 + 表决统计 + 缺席档案 | `clerk_record_json`, `clerk_vote_summary` |
| **5** | `STEP_5_IMPL_DOCKING` | 专业实施团队对接 | ✅ 田经理(AI团队经理)对接<br>✅ 记录详细名录 + 详细实施方案 | `impl_team_contact_json`, `impl_plan_detail_json` |
| **6** | `STEP_6_AI_TEAM_COORD` | 统筹AI实施团队 | ✅ 三角治理：<br>田经理(统筹) + 石监理(验收) + 韩队长(执行)<br>✅ 现有AI员工全员参与 | `ai_team_coord_json`, `ai_core_roles_json` |
| **7** | `STEP_7_EXECUTE` | 下场实施 | ✅ 按团队管理和实施方案执行<br>✅ 每步实施必须可追溯 | `execute_steps_json` |
| **8** | `STEP_8_ACCEPTANCE` | 收场验收 | ✅ 石监理验收<br>✅ 记录实施步骤 ↔ 实际结果映射<br>✅ 落库 mt_fix_implementations | `acceptance_json`, `acceptance_passed`, `acceptance_step_results_json` |
| **9A** | `STEP_9A_PASS_OR_LOOPBACK` | 验收结果分支 | ✅ 通过 → STEP_9B<br>✅ 不通过 → 投喂AI脑库复盘 → 跳回 STEP_1 (loopback_count+1) | `loopback_count` |
| **9B** | `STEP_9B_SUMMARY` | 汇总上报与投喂 | ✅ **四必落库**：<br>① 上报超级管理员<br>② 记录数据库<br>③ 投喂经验到AI脑库<br>④ 投喂系统异常错误特征库 | `summary_report_json`, `db_written`, `brain_fed`, `experience_fed`, `anomaly_fed`, `super_admin_report_status` |
| **10** | `STEP_10_SMART_VERSION_UPGRADE` | 智能判断版本升级 | ✅ `mandatory_upgrade_flag=True` 强制每次必评估<br>✅ 5项阈值规则任一命中即升级 | `smart_upgrade_version`, `smart_upgrade_should_upgrade`, `smart_upgrade_reasons_json`, `smart_upgrade_triggered`, `smart_upgrade_log_id` |
| **11** | `STEP_11_AUTO_GIT_SYNC` | 自动同步git和GitHub | ✅ 不得跳过<br>✅ SSH优先 / remote -v确认 / 结构化返回 | `git_sync_remote_name`, `git_sync_target_branch`, `git_sync_auth_mode`, `git_sync_commit_hash`, `git_sync_commit_subject`, `git_sync_status`, `git_sync_error`, `git_sync_json` |
| **12** | `STEP_12_TEST1000` | 1000轮测试 | ✅ 三大类占比固定：<br>正常逻辑40% + 异常逻辑30% + 黑客攻击30%<br>✅ 测试完毕重复步骤1-11后跳出 | `test1000_total`, `test1000_pass`, `test1000_fail`, `test1000_vuln`, `test1000_json` |
| **终态** | `FINAL_DONE` | 交付 | ✅ 所有前置步骤完成<br>✅ 最终状态不可回退 | `final_status='DONE'` |

### 1.2 状态转移边（硬编码不可修改）

- [ ] AI员工代表团人数为偶数

### 9.2 开发实施中
- [ ] 状态转移严格按边进行，未跳步
- [ ] 张晓峰A轮表决已执行（SUSPEND / NOT_USE_SUSPEND）
- [ ] 若使用暂缓权，B轮张晓峰未参加
- [ ] 孙文档全程记录，无遗漏
- [ ] 田经理/石监理/韩队长三角治理到位
- [ ] 石监理验收记录了步骤↔结果映射

### 9.3 验收与交付前
- [ ] 验收通过/不通过分支处理正确
- [ ] 四必落库全部完成（上报SA/入库/投喂经验/投喂异常特征）
- [ ] 步骤10智能版本升级已评估（mandatory_upgrade_flag=True）
- [ ] 步骤11 Git同步已完成（SSH优先/remote -v确认/结构化返回）
- [ ] 步骤12 1000轮测试完成（正常400+异常300+黑客300）
- [ ] 步骤1-11已重复执行一遍后才跳出STEP_12
- [ ] final_status='DONE'，所有必填字段非空

### 9.4 违规检测
- [ ] 3层拦截机制（入口/状态转移/Git Hook）均生效
- [ ] 8条核心铁律无违反
- [ ] 任何跳步/绕开尝试均被 DEV-FLOW-VIOLATION-IRON-RULE 拦截
- [ ] 违规记录已写入 mt_iron_rule_violations 表

---

## 🔗 §10. 与5级规则体系的关系

| 维度 | 说明 |
|------|------|
| 规则层级 | IRON_RULE (L0) - 最高级别 |
| 代码前缀 | `MT_IR_DEV_12_STEPS_*` |
| 审批要求 | 修改本规则需完整7步审批 + EigenFlux AI5人全票通过 + SA VIKEY终审 |
| 单元测试 | 覆盖100%路径（每一条边、每一个铁律、每一层拦截都必须有测试用例） |
| 文档要求 | 必须附法律依据（《MTSCOS开发治理宪法》第1条） |
| 绕过许可 | `bypass_allowed=False` - 禁止任何绕过 |

---

## 📜 §11. 最终声明

> **本文件为 MTSCOS AI 项目最高级别开发约束规则，独立生效，无条件执行，不可绕开。**
>
> 自生效之日起，所有开发活动必须严格按照本规则的12步骤完整执行。
> 任何个人（包括超级管理员 wuchenghao15）、任何系统、任何AI引擎均无权修改、绕过或豁免本规则的任何条款。
>
> 违反者将按 §0.2 规定承担全部后果。

**规则签发人**：wuchenghao15（超级管理员）
**签发方式**：SA VIKEY 实时检测 + 7要素强认证
**签发日期**：2026-08-10

---

## 🪐 §12. 仙女座自演化引擎联动（v1.4.0 新增）

> 本章定义 §14 IRON_RULE 与仙女座引擎（auto_evolution + autosync）的强制协作机制。
> **禁止**任何 AI 引擎绕过 §14 铁律执行开发活动（包括自演化代码修改）。

### 12.1 仙女座代码变更铁律（FORCE，不可绕过）

| # | 约束 | 违反判定 | 仙女座联动 |
|---|------|---------|-----------|
| IA-01 | **禁止**仙女座 auto_evolution 自演化绕过 12 步骤直接改代码 | git diff 含仙女座改动但无 flow_id + no changelog | smart_mount_engine detect → fail-closed 回滚 |
| IA-02 | 仙女座自演化**必须**先写 mt_dev_flow_session (status='PLANNING') | 无 flow_session 就 commit → reject push | evolution_log 自动记录 `flow_skip_violation` |
| IA-03 | 仙女座双端同步（autosync_andromeda）**禁止**跨版本 major diff rsync | 版本差 ≥ major → 跳过同步并告警 | autosync daemon 检查 VERSION 文件 |
| IA-04 | 仙女座 AI 员工（employee_registry）**不得**拥有 git push 权限 | 员工账号有 push 权限 → fail-closed | smart_mount_engine 权限巡检拦截 |
| IA-05 | rule_knowledge 分块增量 ≥ 50 条/7d → **强制**触发 §14 流程 STEP-0 预扫 | 不触发预扫 → changelog 缺失 | rule_version._auto_bump_from_events() 自动触发 |

### 12.2 仙女座 → §14 触发自动 bump（v1.4.0 核心闭环）

```
仙女座 evolution_log (连续 3 次 auto_evolution 失败)
        │
        ▼
§14 STEP-0 (自动预扫) ──────────────────────────────┐
        │                                            │
        ├── flow_id: auto_fix_evolution_failure      │
        ├── 自动 proposal: 仙女座引擎修复            │
        ├── 自动触发 rule_enforcer 规则重扫描        │
        │                                            │
        ▼                                            ▼
§14 STEP-7 (自动代码修改) ← 自动补丁生成              │
        │                                            │
        ▼                                            │
mt_ai_self_evolution_log.status = 'fixed'  ←─────────┘
        │
        ▼
rule_version.apply_auto_bumps() → 自动 [EVOLUTION-FIX] patch bump
        │
        ▼
mt_rule_changelog (自动记录, proposer=仙女座引擎)
```

### 12.3 仙女座员工健康度阈值

mt_andromeda_employee_registry 异常员工 ≥ 20 名时 → **强制**：
1. smart_mount_engine 禁用异常员工调用权限
2. 触发 [EMPLOYEE-HEAL] patch bump
3. §14 STEP-7 自动生成修复补丁（重新注册 + 健康检查）

违反 → 按 DEV-FLOW-VIOLATION-IRON-RULE 落库 + EigenFlux 5 人紧急磋商。

<!-- PRECOMMIT_HOOK_TEST_MARKER verified at 1787060911 -->
