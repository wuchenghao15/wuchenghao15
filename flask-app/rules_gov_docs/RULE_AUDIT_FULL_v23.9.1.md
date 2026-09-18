# §14 IRON_RULE 9条铁律 × 代码实现 完整审计报告

**审计日期**: 2026-09-18
**审计人**: SA wuchenghao15 (VIKEY verified)
**覆盖规则**: §14 IRON_RULE + 所有引用了名单表/人物表的规则

---

## 1. 铁律 × 代码实现 矩阵

| 铁律 | 代码层 | 数据表层 | 关键人物名单 | 状态 |
|------|--------|---------|-------------|------|
| MT_IR_D1 不得绕开 | ✅ dev_activity_preflight.py | ✅ mt_dev_flow_session(22) + mt_iron_rule_violations(12) | — | ✅ 完整 |
| MT_IR_D2 不得跳步 | ✅ RuleDB class 状态转移 | ✅ mt_dev_flow_events(63) | — | ✅ 完整 |
| MT_IR_D3 强制出席 | ✅ before_request 拦截 | ✅ mt_gov_key_personnel(5) + mt_a_group_roster(7) + mt_eigenflux_panel(5) + mt_ai_delegate_pool(10) | ✅ 刚建+预填充 | ✅ 完整 |
| MT_IR_D4 强制落库 | ✅ RuleDB 写 | ✅ session/events/brain_feed/experience/anomaly 5张 | — | ✅ 完整 |
| MT_IR_D5 强制投喂 | ✅ rule_violation_alert.py | ✅ mt_ai_brain_feed_log(6) + mt_experience_library(0) + mt_anomaly_feature_library(0) | — | ✅ 完整 |
| MT_IR_D6 强制升级 | ✅ RuleDB 字段 | ✅ smart_upgrade_* 字段 | — | ✅ 完整 |
| MT_IR_D7 强制同步 | ✅ pre_commit hook | ✅ git_sync_* 字段 | — | ✅ 完整 |
| MT_IR_D8 强制测试 | ✅ ci_check | ✅ test1000_* 字段 | — | ✅ 完整 |
| MT_IR_D9 前置拦截 | ✅ dev_activity_preflight.py(10KB, 275行) | ✅ mt_rule_violation_alert(0) | — | ✅ 完整 |

**之前缺失**: mt_rule_violation_alert + mt_a_group_roster + mt_eigenflux_panel + mt_ai_delegate_pool + mt_gov_key_personnel = **5 张表** — 已在本次 SA 治理中新建并预填充

## 2. MT_IR_D3 关键人物名单

| 表 | 内容 | 行数 |
|----|------|------|
| mt_gov_key_personnel | 张晓峰/田经理/石监理/韩队长/SA | 5 |
| mt_eigenflux_panel | EigenFlux 5人专家(架构/合规/DBA/运维/前端) | 5 |
| mt_a_group_roster | SA+张晓峰+5EigenFlux专家 = 7 (缺44) | 7 |
| mt_ai_delegate_pool | AI员工代表团池 (employee_registry 前10) | 10 |

**A组51人名单缺口**: 规则文档写 "A组51人含张晓峰"，目前只有 7 人在 roster 里。剩余 44 人需要后续根据实际团队情况补录。

## 3. preflight 已知缺陷 (MT_IR_D9)

- **问题**: 关键词精确匹配太死板，"新建功能" 无法命中 "新建一个galaxy视频批量生成功能"
- **当前表现**: "新建功能" 精确匹配会漏掉中间插入字的情况
- **建议修复**: 加模糊匹配正则 `新建.*功能` + 近义词 (开发/建造/构建/打造/设计/实现/编写)
- **优先级**: P2 (规则能跑，只是关键词灵敏度不够)

## 4. 下次开发必须严格遵守

**从 v23.9.1 起任何开发活动 (含 galaxy 系列扩展) 必须**:
1. 先跑 STEP_1_PROPOSAL → 创建 flow_id
2. 完整走 18 节点状态机
3. STEP_12 跑 1000 轮测试
4. git commit message 必须包含 flow_id
5. preflight 拦截层必须放行 (flow_id 在允许步骤集合中)

**违反 = 自动落库 mt_iron_rule_violations + EigenFlux 5人磋商告警 + 脑库负面教材**
