# 提案完善：测试报告驱动的后续修复方案（综合12条专家意见）

> **flow_id**: flow_test_repair_20260818_002  
> **依据**: 测试报告 TEST_20260818_104856 (通过率80.6%) + EigenFlux 5人磋商 + 专业AI员工团队6人意见  
> **综合意见数**: 12条 (6建设性 + 6专业性不同意)  
> **完善时间**: 2026-08-18  

---

## 一、专家意见综合结论

### 全员共识（无需表决，直接采纳）
1. **修复顺序**：先修 B1 守卫（议题1），再迁移单体路由（议题4）——顺序不可颠倒（专3）
2. **路由行为分支**：page_* → 302重定向登录页；api_* → 401 JSON；static → 放行（建2共识）

### 方案综合（建1 + 专1 + 专5 三方融合）
**核心冲突**：catch-all 单段路由（`/<path:copy_key>`、`/<test_id>`）正则过宽 vs 这些路由可能是合法功能

**综合结论**：采用「**精确路径优先匹配 + 通配低优先级 + guest通配放行**」三段式策略：
- 第一优先级：精确字符串路由（如 `/admin/dashboard`）→ 按建议角色校验
- 第二优先级：多段通配路由（如 `/static/<path:filename>`）→ 按 suggested_role 校验
- 第三优先级（最低）：单段通配路由（`/<path:x>`、`/<param>`）→ **仅当 suggested_role != guest 时参与匹配，且仅在无精确/多段匹配时生效**
- guest 级通配直接放行（不拦）

> 否决「直接排除单段通配」（专1：`/exam`合法会漏校验）  
> 否决「删除 catch-all 路由」（专5：`/<path:copy_key>`可能是文件下载功能）

### 架构层建议（建1·EF战略组长）
- 中期演进：守卫从 `before_request` 全量拦截改为「路由匹配后校验」——让 Flask 先确定路由存在性（404自然处理），再对已注册路由做权限校验，从架构层消除 catch-all 误匹配。本期先做三段式修复，中期再做架构演进。

---

## 二、最终修复方案（按优先级）

### P0-1：B1 守卫三段式匹配修复
**文件**：[b1_global_permission_guard.py](file:///Users/wuchenghao/Library/CloudStorage/OneDrive-%E4%B8%AA%E4%BA%BA/%E6%96%87%E6%A1%A3/MTSCOS_AI_Project/flask-app/app/utils/b1_global_permission_guard.py)

修改 `_match_route_role`：
1. 将审计表路由分三层加载：精确表 / 多段通配表 / 单段通配表
2. 匹配时按 精确 → 多段通配 → 单段通配 顺序，首个命中即返回
3. 单段通配仅当 `suggested_role != 'guest'` 且无更高优先级匹配时生效

### P0-2：守卫按 category 分支响应
修改 `_b1_global_permission_guard`：
- `page_*` 类别未登录 → `redirect(login_url)` 302（而非 abort 401）
- `api_*` 类别未登录 → `jsonify({code:401})` 401
- `static` / `guest` 级 → `return None` 放行
- 权限不足（已登录但角色不够）→ `page_*` 403 / `api_*` 403 JSON

### P1-1：登录态回归测试套件（建4 + 专2 + 专4）
新增测试用例：
- 构造 `requests.Session` 保持 admin/test_student 登录态（复用 auth 登录接口）
- 验证：`/admin/dashboard` 登录后 200 + 统计卡片 JS fetch 真实数据非0
- 验证：`/student/home` 登录后 200 + 菜单 AI 徽标 `data-emp-id` 属性
- **超级管理员 wuchenghao15**：7要素+VIKEY 认证链路测试（专2强制）
- **越权测试**：student session 访问 `/admin/dashboard` → 403（建5）
- 验收标准（专4加权）：功能性失败 0 + 边界性失败 ≤2（非纯通过率≥95%）

### P1-2：单体路由模块化迁移（建3 + 专3）
**前置条件**：P0-1/P0-2 守卫修复完成并回归通过后
迁移清单（按用户使用频率排序）：
1. `teacher_dashboard` → 新建 `routes/teacher_routes.py` + `teacher_bp`
2. `exam_review` → 迁入 `routes/exam_system_routes.py`
3. 其余 server_real_db.py 中未迁移的 `admin_app/*` 页面路由

### P1-3：数据源补全（专6）
- `login_logs` 表不存在 → 建表 OR 改用 `user_activities WHERE activity_type='login'` 做登录统计源
- `dashboard_stats` 的 `today_logins` 改用可靠数据源

### P2：异常页回归测试
守卫修复后验证：
- 不存在路径 → 404（异常页渲染，非401）
- 未登录访问 page_* → 302 重定向
- 未登录访问 api_* → 401 JSON
- 已登录越权 → 403

---

## 三、验收阈值

| 维度 | 阈值 | 来源 |
|------|------|------|
| 功能性失败 | 0 | 专4 加权标准 |
| 边界性失败 | ≤2 | 专4 加权标准 |
| 通过率 | ≥90%（参考） | 原 STEP_311 阈值 |
| 登录态覆盖 | admin/student/super_admin 3角色 | 专2 |
| 越权拦截 | student→/admin/* 必403 | 建5 |
| 404 渲染 | 不存在路径必404+异常页 | P2 回归 |

---

## 四、永久保存清单

| 文件 | 类型 | 路径 |
|------|------|------|
| 测试报告(JSON) | 数据 | `_runtime/dev_flows/test_report_20260818_104856.json` |
| 测试报告(MD) | 报告 | `_runtime/dev_flows/test_report_20260818_104856.md` |
| 提案flow脚本 | 方案 | `_runtime/dev_flows/flow_testrepair_step1_step2a.py` |
| 完善修复方案 | 方案 | `_runtime/dev_flows/refined_repair_plan_20260818.md`（本文件） |
| 脑库投喂 | 知识 | `mt_dev_flow_brain_bank` 表(experience/exception/knowledge 3条) |
| 专家意见 | 记录 | `mt_dev_flow_session.discussion_opinions` 列(12条) |
| flow会话 | 记录 | `mt_dev_flow_session` flow_test_repair_20260818_002 |
| flow事件 | 记录 | `mt_dev_flow_events` (CREATE + PROPOSAL_TO_DISCUSSION) |

---

## 五、专家意见原档索引

### EigenFlux 5人磋商（3人发言）
- EF_战略决策组长：建1(路由匹配后校验) + 专1(单段路由合法不排除)
- EF_安全架构_SEC：建2(category分支响应) + 专2(super_admin VIKEY必测)
- EF_前端架构_FE：建3(Playwright端到端) + 专3(先修守卫再迁移顺序)

### 专业AI员工团队（3人发言）
- AI测试工程师 EMP-000002：建4(登录态session用例) + 专4(加权验收非纯通过率)
- AI安全专家 EMP-000005：建5(渗透+越权测试) + 专5(catch-all不删改精确优先)
- AI数据库架构 刘DB：建6(exam_attempts索引) + 专6(login_logs表缺失改数据源)
