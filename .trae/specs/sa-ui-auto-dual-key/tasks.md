# SA 专有界面与双硬件密钥自动加载适配 - Implementation Plan

> 父规范: [spec.md](./spec.md) | 版本: v1.0 | 日期: 2026-08-30
> 所有任务均通过「双密钥 SA=wuchenghao15」约束，禁止通过任何 env/flag 绕过。

---

## Task 1: 补齐双密钥聚合能力层 (`_dual_hardware_probe`)
- **Status**: `pending`
- **Priority**: high
- **Depends On**: None
- **Description**:
  - 在 `VikeyEnforcementMiddleware` (`_output/app/middlewares/vikey_enforcement_middleware.py`) 新增静态方法/实例方法：`_check_szu100()` → `{present, is_authentic, volume_name, auth_status}`（内部调 `core.services.szu100_driver.detect_szu100`，try/except 兜底为 not present）。
  - 新增方法 `get_dual_hardware_status(username=None)` → `{vikey:{present,serial,sa_bound_ok,message}, szu100:{...}, both_authenticated: bool, layout_mode: SA_PROPRIETARY|STANDARD}`。
  - 内存级 TTL=2s 缓存 `_dual_cache`，避免 5s 轮询打爆 IO。
  - 如存在镜像 `flask-app/app/middlewares/vikey_enforcement_middleware.py` 同步更新。
- **Acceptance Criteria Addressed**: AC-1, AC-2, AC-3 (依赖)
- **Test Requirements**:
  - `rule` TR-1.1: 模拟四种硬件组合（双在线/仅VIKEY/仅SZU100/双离线）+ 伪造szu100(is_authentic=False)，调用 `get_dual_hardware_status(username=wuchenghao15)` 返回值字段完整、`both_authenticated` 仅真于第一种组合。
    - **Evidence**: pytest 脚本执行 5 组断言通过。
  - `rule` TR-1.2: 同一硬件态 1s 内连续 10 次调用 `get_dual_hardware_status`，实际底层 `detect_szu100` 与 `VikeyAPI.detect()` 调用次数 ≤ 3（命中缓存 2s TTL）。
    - **Evidence**: 侧载 monkeypatch 计数脚本输出。

## Task 2: 中间件 check_vikey_enforcement 改为双密钥 AND
- **Status**: `pending`
- **Priority**: high
- **Depends On**: Task 1
- **Description**:
  - 改造 `check_vikey_enforcement(path, username)`：当 `is_super_admin == True` 时，顺序执行 VIKEY → SZU100 检查；任一失败 → `allowed=False`，reason 含「缺 VIKEY / 缺 SZU100 / SZU100 未通过正版校验」。
  - 输出字典新增键 `szu100_status` 匹配原 `vikey_status`。
  - 审计写入: 失败 severity=critical；成功 severity=info。
- **Acceptance Criteria Addressed**: AC-2, AC-8
- **Test Requirements**:
  - `rule` TR-2.1: 模拟 `is_super_admin=True` 访问 `/admin_app/dashboard` 在 6 组态（双在线 / VIKEY拔 / SZU100拔 / SZU100伪造 / VIKEY错绑非SA / 双离线）下的 allowed 严格为 `[T,F,F,F,F,F]`。
    - **Evidence**: 测试脚本输出矩阵。
  - `rule` TR-2.2: 非SA 访问同路径返回 `allowed=True`（非 SA 不走双钥链）。
    - **Evidence**: 三组 (student/admin/anonymous) 断言输出。

## Task 3: 新增 GET /api/hardware/dual-status 接口
- **Status**: `pending`
- **Priority**: high
- **Depends On**: Task 1
- **Description**:
  - 路由位置：挂载到 `server_real_db.py` 现有 API 区（与 `/api/server-time` 同级），或 `routes/admin_routes.py`（走 @admin_bp 前缀 `/api/admin/hardware/dual-status`）。本项选前者：`/api/hardware/dual-status`，保持与 `/api/health` 风格一致。
  - 鉴权：复用 `@system_container(require_auth='login')`；鉴权失败返回 401 AUTH_REQUIRED。
  - 鉴权通过：读 session.username + role_canonical → 调 `get_dual_hardware_status`；对非 SA 返回时清空 `serial` / `volume_name` 等敏感字段。
  - 防盗链：before_request 现有链路已覆盖，本路由不额外处理。
- **Acceptance Criteria Addressed**: AC-1, AC-8
- **Test Requirements**:
  - `rule` TR-3.1: 4 组 curl：未登录(401)/student(200,STANDARD)/SA双钥(200,SA_PROPRIETARY)/SA缺SZU(200,STANDARD)。
    - **Evidence**: 4 条 curl 命令 + 返回片段。
  - `rule` TR-3.2: 伪造 Referer 非首页访问 → 返回 403/重定向（防盗链生效不变）。
    - **Evidence**: curl -e 输出。

## Task 4: 模板上下文注入 layout_mode (context_processor)
- **Status**: `pending`
- **Priority**: high
- **Depends On**: Task 1
- **Description**:
  - 在 Flask 应用层添加 `@app.context_processor` 注入 `_sa_layout_context_processor`：读 session.username/role_canonical，调 `get_dual_hardware_status` 返回 `{layout_mode, dual_authenticated, vikey_serial, szu100_volume, sa_proprietary=True if SA_PROPRIETARY else False}`。
  - 位置：server_real_db.py before_request 注册后或 `app/__init__.py` create_app 内。
  - 确保注入不抛异常：所有调用 try/except → 降级 STANDARD。
- **Acceptance Criteria Addressed**: AC-3
- **Test Requirements**:
  - `rule` TR-4.1: 注入测试：双钥SA → ctx.layout_mode == SA_PROPRIETARY；普通admin → STANDARD；异常mock → STANDARD + 无 exception 冒泡。
    - **Evidence**: Flask test_client 渲染 `admin_center.html` → grep `layout-mode-` 输出。
  - `rule` TR-4.2: 敏感字段非 SA 登录必为 None（vikey_serial / szu100_volume）。
    - **Evidence**: test_client 上下文断言。

## Task 5: 两处基础模板的 body class 接入
- **Status**: `pending`
- **Priority**: high
- **Depends On**: Task 4
- **Description**:
  - 修改 `frontend/templates/super_admin_base.html` 的 `<body>`：添加 `class="layout-mode-{{ layout_mode }}"`。
  - 修改 `flask-app/templates/admin_app/base.html` 的 `<body>`：添加 `class="layout-mode-{{ layout_mode }}"`。
  - 在 `{% block extra_head %}` 中，若 `sa_proprietary==True`，额外加载 `sa_proprietary.css` 与 `sa_proprietary.js`（否则不加载以避免前端下载 SA 专有关联脚本）。
- **Acceptance Criteria Addressed**: AC-3, AC-4
- **Test Requirements**:
  - `rule` TR-5.1: `GET /admin_center`（前者）与 `GET /admin_app/dashboard`（后者）在 SA 双钥态的 HTML 源码里出现 `layout-mode-SA_PROPRIETARY` 与 `sa_proprietary.css/js` 资源引用；普通态下类为 STANDARD 且不加载这两个资源。
    - **Evidence**: 2 条 URL × 2 种态 = 4 次 grep。

## Task 6: 实现 SA 专有 CSS (`static/css/sa_proprietary.css`)
- **Status**: `pending`
- **Priority**: high
- **Depends On**: Task 5
- **Description**:
  - 输出目录：`flask-app/static/css/sa_proprietary.css`（前端 symlink 如已有同步部署则镜像）。
  - 所有选择器必须前缀 `.layout-mode-SA_PROPRIETARY` 以实现作用域。
  - 覆盖项：
    1. Sidebar SA：width 260px / `border-left: 3px solid var(--sa-gold-accent, #f59e0b)` / `.sa-hardware-panel`（VIKEY+SZU100 图标+双锁徽章）/ `.sa-eigenflux-info` / `.sa-daemon-strip`。
    2. Topbar SA：`.sa-topbar-hardware-badge` / `.sa-quick-links` / `.sa-session-heartbeat`（SESSION_LIVE 徽章）。
    3. 内容栅格：`.sa-card-grid`（4列，@media ≤1024px 降级为 3列 / ≤768px 降级为 2 列）。
    4. Arduino 高亮：`.sa-arduino-entry` 金色脉冲。
    5. 锁定遮罩 `sa-lock-overlay`：默认隐藏，JS 在拔出时 `.sa-lock-active` 显示。
  - 设计 token：完全引用 `--el-color-*` / `--dark-*` / `--sa-gold-accent`（在 CSS 首段的 `:root` 中定义一次，避免硬编码）。
- **Acceptance Criteria Addressed**: AC-4, AC-5
- **Test Requirements**:
  - `rubric` TR-6.1: 视觉完整性；Scale 1-5；1=无作用域前缀或元素全缺失 / 3=作用域生效但硬件面板缺失2项以上 / 5=六要素全出现(侧栏彩边/硬件面板双图标双锁徽章/EF专家数/daemon条/顶栏三件/栅格4列)；阈值 >= 4。
    - **Evidence**: 选择器命中计数脚本 + 渲染截图。
  - `rule` TR-6.2: 体积 ≤ 20KB（gzip前）。
    - **Evidence**: `wc -c` 输出。

## Task 7: 实现 SA 专有 JS (`static/js/sa_proprietary.js`)
- **Status**: `pending`
- **Priority**: high
- **Depends On**: Task 3 + Task 6
- **Description**:
  - 输出：`flask-app/static/js/sa_proprietary.js`。
  - 导出 `window.SAUIManager = { start, stop, applyState, lastState }`。
  - 行为：
    - `start(pollMs=5000)`: 轮询 `/api/hardware/dual-status`（带 credentials），失败指数退避（5→10→20→40→60s，不超过60）。
    - 状态变化：`both_authenticated` true↔false → toggle `layout-mode-SA_PROPRIETARY` class；dispatch `CustomEvent('sa-layout-updated', {detail: {...}})`；console 打 `[SA-UI] layout: X → Y`。
    - 失锁 → 在 `<body>` 追加 `.sa-lock-overlay`（首次从 document.createElement，避免依赖模板修改），并禁用所有 `<a>` / `<button>` 的默认行为 1 秒（class 加 `pointer-events: none` 到根节点）。
    - 重锁成功 → 清除 overlay，移除 pointer-events none。
- **Acceptance Criteria Addressed**: AC-5
- **Test Requirements**:
  - `rule` TR-7.1: 手动切换 API 返回（通过 monkeypatch fetch）测试：true→false→true 三态，DOM class 切换与 event 触发次数精确匹配；overlay 显隐正确。
    - **Evidence**: Playwright/JS 单元脚本输出。
  - `rule` TR-7.2: 连续失败 3 次后，下一次尝试间隔 ≥ 20s（指数退避生效）。
    - **Evidence**: `Date.now()` 差日志。

## Task 8: Arduino 统一守卫 `_check_arduino_api_permission()`
- **Status**: `pending`
- **Priority**: high
- **Depends On**: Task 1
- **Description**:
  - 实现：在 `flask-app/routes/admin_routes.py` 顶部导出 `_check_arduino_api_permission()`（无参数，内部读 flask.session + Task1 的双密钥聚合 API）。
  - 返回行为：命中 → `(True, None)`；未命中 → `(False, response_tuple)`；`response_tuple = jsonify({success=False, code="ARDUINO_SA_ONLY", message="Arduino 页面仅 wuchenghao15 可访问"}), 403`。
  - 挂接：
    - 所有 `/api/arduino/*` 路由的 before_request 级别或函数第一行。
    - `/admin_app/arduino_ide` 路由函数第一行。
    - 落库审计：未命中时，写 `automation_console_logs(source='arduino_guard', eigenflux_flag=1, severity='warning')`。
- **Acceptance Criteria Addressed**: AC-6, AC-7
- **Test Requirements**:
  - `rule` TR-8.1: 4 角色 × 2 接口 = 8 请求严格：SA双钥 200 / SA单钥 / admin / student 均 403 + ARDUINO_SA_ONLY。
    - **Evidence**: curl 8 条原始输出。
  - `rule` TR-8.2: 未命中案例 `automation_console_logs` 行数 ≥ 失败请求数。
    - **Evidence**: SQL 计数。

## Task 9: 审计落库补强
- **Status**: `pending`
- **Priority**: medium
- **Depends On**: Task 1, 2, 8
- **Description**:
  - 在 `VikeyEnforcementMiddleware._log_event` 基础上添加可选 username/ip 字段（若可用）。
  - 在 Task 1 的 `get_dual_hardware_status` 调用链中，「上一态 ≠ 当前态」时写入 `automation_console_logs(source='dual_hardware_switch', eigenflux_flag=1)`，结构含 `before/after/username/session_id`。
  - 新增表（如不存在则 CREATE TABLE IF NOT EXISTS）`sa_ui_layout_switch_log(id INTEGER PK, ts, username, role, before_mode, after_mode, ip, ua, session_id)` 作为明细审计。
- **Acceptance Criteria Addressed**: AC-7
- **Test Requirements**:
  - `rule` TR-9.1: 触发两次切换（T→F → F→T），明细行数 = 2，eigenflux_flag = 1。
    - **Evidence**: SQL 查询输出。

## Task 10: 高可见度页面 SA 专有布局视觉核对
- **Status**: `pending`
- **Priority**: medium
- **Depends On**: Task 5, 6, 7
- **Description**:
  - 核对页面：dashboard.html, dashboard_unified.html, security_dashboard.html, health_monitor.html, process_monitor.html。
  - 核对清单（每一页）：① body.class 正确 ② 侧栏金色 3px 边框 ③ 硬件徽章可见 ④ `sa-card-grid` 下卡片数 4 列。
  - 如页面有特定卡栅命名冲突，在 `sa_proprietary.css` 加对应选择器（增量）。
- **Acceptance Criteria Addressed**: AC-4, AC-5
- **Test Requirements**:
  - `rubric` TR-10.1: 5 页 SA 专有模式视觉一致性评分；Scale 1-5；1=3页以上不满足 / 3=1或2页缺彩边 / 5=5页全部 4 条核对项满足；阈值 ≥ 4。
    - **Evidence**: 页面截图 + 选择器命中表。

## Task 11: 系统级自测脚本 + 文档化验证步骤
- **Status**: `pending`
- **Priority**: medium
- **Depends On**: Task 1-10 全部
- **Description**:
  - 新脚本：`flask-app/scripts/verify_sa_dual_key_ui.py`：用 `requests.Session` 模拟登录 → 执行 AC-1/2/3/6/7 的核心断言并输出 PASS/FAIL 报告。
  - 输出：`stdout = 分阶段 PASS 列表；非 0 exit = 任一断言失败`。
- **Acceptance Criteria Addressed**: AC-1,2,3,6,7（可自动验证项）
- **Test Requirements**:
  - `rule` TR-11.1: 脚本在双硬件可用/不可用两种场景都能跑完并给出明确 exit code 0 或非 0。
    - **Evidence**: 脚本两次执行输出。
