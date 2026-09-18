# 仙女座全盘点 — 功能闭环矩阵

**flow_id**: flow_inv_dyn_1789690567497
**盘点日期**: 2026-09-18
**范围**: Flask路由/引擎/DB表/CLI入口/功能断链

---

## 一、Flask 路由盘点

| 指标 | 数值 |
|------|------|
| 路由文件 | 40+ |
| 路由总数 | **343** |
| galaxy_* 路由 | 21 |
| ❌ 无 @system_container | **32** (arduino_session 为主) |

## 二、引擎盘点

| 指标 | 数值 |
|------|------|
| 引擎总数 | **66** |
| galaxy_* | 10 |
| smart/auto/ai_* | 36 |
| 有 CLI 入口 | 44/66 |

## 三、DB 表盘点

| 指标 | 数值 |
|------|------|
| 总表数 | **293** |
| mt_* 规则治理 | 6 |
| ai_* | 36 |
| galaxy_* | 10+ |
| eigenflux_* | 10 |
| system_* | 16 |

## 四、规则治理表状态

| 表 | 行数 | 说明 |
|----|------|------|
| mt_dev_flow_session | 24 | 13 DONE + 9 BYPASSED + 2 OPEN |
| mt_dev_flow_events | 68 | 状态转移事件 |
| mt_iron_rule_violations | 12 | galaxy 回溯补录 D1 |
| mt_experience_library | 9 | SA治理灌 |
| mt_anomaly_feature_library | 6 | SA治理灌 |
| mt_rule_violation_alert | 0 | 等真实违规触发 |

## 五、功能闭环矩阵 — 10条链路

| # | 链路 | 状态 | 断链点 |
|---|------|------|--------|
| 1 | composition → swarm_teams | ❌ | swarm_teams 0行 (落库失败) |
| 2 | swarm → publish_log | ❌ | swarm 0行 → publish 自然也 0 |
| 3 | pipeline → video file | ⚠️ | Phase B 即梦降级 moviepy |
| 4 | video → social publish | ❌ | credential_json 空 → 无法真实发布 |
| 5 | dyn_team → session | ❌ | mt_galaxy_dyn_team_sessions 表缺失 |
| 6 | mimicry → prompt | ⚠️ | 1条配置可复刻, 需积累 |
| 7 | compliance → log | ✅ | 315 行, 跑通 |
| 8 | db → api | ✅ | 10 表 CRUD |
| 9 | ai_router → model | ✅ | Ollama qwen2.5 本地推理 |
| 10 | daemon → monitor | ⚠️ | daemon 文件存在但未 systemd 化 |

### 3 个 P0 必须修

| # | 断链 | 修复 |
|---|------|------|
| 1 | swarm_teams 0行 | galaxy_composition_engine 落库修复 |
| 2 | dyn_team_sessions 表缺失 | CREATE TABLE + 引擎对接 |
| 3 | 32 条无 @system_container | 批量补 (arduino 为主) |

### 2 个 P1 用户操作

| # | 断链 | 修复 |
|---|------|------|
| 1 | credential_json 空 | 用户扫码补 cookie/token |
| 2 | 即梦 VIP='' | 用户开会员 |

### 2 个 P2 规则完善

| # | 缺失 | 修复 |
|---|------|------|
| 1 | Design Token CSS | static/css/design_tokens.css |
| 2 | 设计巡检引擎 | auto_patrol 新增 design_scan |

---
**flow_id**: flow_inv_dyn_1789690567497
**状态**: DONE (盘点完成, 修复见后续轨道)
