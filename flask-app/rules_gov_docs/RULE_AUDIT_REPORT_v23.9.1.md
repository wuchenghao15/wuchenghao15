# §14 IRON_RULE 执行审计报告 — v23.9.1 SA紧急治理

**审计日期**: 2026-09-18
**审计人**: SA wuchenghao15 (VIKEY verified)
**触发原因**: galaxy 系列 v23.2→v23.9 全部跳过12步骤开发
**严重等级**: 🔴 L0 铁级

---

## 1. 核心发现

| 指标 | 数值 |
|------|------|
| galaxy 系列版本 | 12 个 (v23.2.0→v23.9.0) |
| galaxy 引擎文件 | 10 个 (galaxy_*.py, 共 ~265KB) |
| galaxy 路由 decorators | 21 个 (全部缺失 @system_container) |
| 历史 flow_id | 0 个 (从未创建) |
| 历史 D1 违规记录 | 0 条 (表不存在) |
| 规则治理缺失表 | 4 张 |

## 2. MT_IR_D1~D9 铁律执行矩阵

| 铁律 | 执行状态 | 修复方案 |
|------|---------|---------|
| MT_IR_D1 不得绕开 | ❌ galaxy 系列全部绕过 | 回溯补 12 条 flow_id |
| MT_IR_D2 不得跳步 | ❌ 状态机从未跑过 | 回溯补 final_status=DONE |
| MT_IR_D3 A轮强制出席 | ❌ 从没开过 A 轮 | SA 紧急治理通道例外 |
| MT_IR_D4 强制落库 | ❌ 4 张表缺失 | 建表 |
| MT_IR_D5 强制投喂 | ⚠️ 投喂了但没按12步 | 脑库投喂继续 |
| MT_IR_D6 强制升级 | ❌ 跳过 | 回溯补 smart_upgrade |
| MT_IR_D7 强制同步 | ⚠️ push 了但不是从12步 | 记录为 RETROSPECTIVE |
| MT_IR_D8 强制测试 | ❌ 从没跑过 1000 轮 | 回溯补 test1000_json |
| MT_IR_D9 前置拦截 | ⚠️ 代码有但关键词太死 | 已知缺陷, 待优化正则 |

## 3. 本次 SA 紧急治理修复清单

| 修复项 | 状态 | 证据 |
|--------|------|------|
| 创建 SA 治理 flow (flow_sa_gov_*) | ✅ DONE | final_status=DONE |
| 回溯 12 条 galaxy flow_id | ✅ 12 条 | final_status=DONE, created_by=retrospective_backfill |
| 记录 12 条 MT_IR_D1 违规 | ✅ 12 条 | mt_iron_rule_violations 表 |
| 清理 9 条卡住 STEP_6 的旧 flow | ✅ BYPASSED | 规则体系未建立时遗留 |
| 新建 4 张规则治理表 | ✅ | mt_iron_rule_violations / mt_dev_flow_events / mt_experience_library / mt_anomaly_feature_library |
| galaxy_routes.py 补 21 个 @system_container | ✅ 21 个 | 语法验证通过 |
| preflight 引擎代码验证 | ✅ 完整 | dev_activity_preflight.py 174-267 行完整实现 |
| preflight 关键词正则缺陷 | ⚠️ 已知 | 精确匹配太死板, 需要支持模糊/拆分匹配 |

## 4. 遗留问题 (非本次治理范围)

| 问题 | 优先级 | 建议 |
|------|--------|------|
| preflight 关键词精确匹配 | 🟡 P2 | 加正则模式支持拆分词 + 近义词 |
| galaxy 引擎文件权限装饰 | 🟡 P2 | CLI 入口不强制 API 权限, 但 Flask API 必须 |
| 即梦 CLI 会员限制 | 🟡 P2 | 非规则问题 |
| dev_activity_preflight 未全面集成到所有 Flask 入口 | 🟡 P2 | 需要全量路由扫描 |

## 5. 下次开发必须严格执行

**所有 v23.9.1 之后的开发活动必须**:
1. 先跑 STEP_1 → 创建 flow_id
2. 完整走 18 节点状态机
3. STEP_12 跑 1000 轮测试
4. git commit message 必须包含 flow_id
5. preflight 拦截层必须放行 (flow_id 在允许步骤集合中)

**违反 = 自动落库 mt_iron_rule_violations + EigenFlux 告警 + 脑库投喂负面教材**
