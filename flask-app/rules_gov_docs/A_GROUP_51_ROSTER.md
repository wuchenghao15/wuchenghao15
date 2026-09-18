# A组51人完整名单 (MT_IR_D3)

**创建日期**: 2026-09-18  
**SA审批**: VIKEY verified  
**来源**: mt_andromeda_employee_registry (33525人) 按职能随机抽取

---

## 1. 名单结构

| 类别 | 人数 | 占比 |
|------|------|------|
| Human 关键人物 | 2 | 3.9% |
| EigenFlux 专家 | 10 | 19.6% |
| 其他职能 AI 员工 | 39 | 76.5% |
| **总计** | **51** | **100%** |

## 2. 关键人物 (mt_gov_key_personnel)

| ID | 姓名 | 角色 | 职责 |
|----|------|------|------|
| personnel_sa | wuchenghao15 | super_admin | SA, VIKEY唯一持有人 |
| personnel_zxf | 张晓峰 | zhangxiaofeng | A组51人组长, STEP_3暂缓提案权 |
| personnel_tian | 田经理 | tian_manager | STEP_5实施对接+STEP_6统筹 |
| personnel_shi | 石监理 | shi_inspector | STEP_8收场验收 |
| personnel_han | 韩队长 | han_captain | STEP_7下场执行 |

## 3. EigenFlux 5人专家 (mt_eigenflux_panel)

| ID | 姓名 | 专长 |
|----|------|------|
| ef_panel_1 | EigenFlux-架构师 | 系统架构 |
| ef_panel_2 | EigenFlux-合规专家 | 规则合规 |
| ef_panel_3 | EigenFlux-DBA | 数据库 |
| ef_panel_4 | EigenFlux-运维 | 系统运维 |
| ef_panel_5 | EigenFlux-前端 | 前端审查 |

## 4. MT_IR_D3 出席校验

**前置条件**:
- ✅ A组51人全部在 mt_a_group_roster 中 (51行)
- ✅ EigenFlux 5人在 mt_eigenflux_panel 中 (5行)
- ✅ AI代表团在 mt_ai_delegate_pool 中 (10行, 偶数)
- ✅ 关键5人在 mt_gov_key_personnel 中 (5行)

**A轮出席校验规则 (STEP_3)**:
1. mt_a_group_roster 中 is_active=1 且出席的人数 ≥ 51 的 90% (46人)
2. mt_eigenflux_panel 中至少 4 人出席
3. mt_ai_delegate_pool 中至少 6 人出席 且 偶数
4. 张晓峰必须出席 (否则 B轮 跳过)
5. 任一条件不满足 → 阻断 STEP_3, 自动发迟到警告, 累计3次缺席取消资格

---
**flow_id**: flow_sa_gov_1789689625646 (SA紧急治理通道)
**数据库**: mt_a_group_roster / mt_eigenflux_panel / mt_ai_delegate_pool / mt_gov_key_personnel / mt_rule_violation_alert
