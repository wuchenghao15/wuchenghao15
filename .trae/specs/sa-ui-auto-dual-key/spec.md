# SA 专有界面与双硬件密钥自动加载适配 (v1.0) - Product Requirements Document

## Overview
- **Summary**: 自动复写超级管理员 (wuchenghao15) 所有页面的界面布局，创建一套 SA 专有排版骨架与视觉体系；实现 VIKEY 加密狗 + SZU100 专用 U 盘「同时插入即触发自动加载与适配」的端到端链路（后端检测 → 模板/路由切换 → 前端动态应用 → 拔出回退）。
- **Purpose**: 落实硬约束「SA = wuchenghao15 唯一，仅双硬件密钥 (VIKEY + SZU100) 同时连接才可访问专有界面」；并保证其他账号绝对看不到 SA 专有视觉层（零暴露）；SA 插拔双硬件时页面布局无感切换，无需刷新或重新登录即自动适配/解除适配。
- **Target Users**:
  - **wuchenghao15 (super_admin, 唯一)**：双硬件插入时自动进入 SA 专有布局 + 专有能力；任意一把拔出后自动锁定并回退普通 admin 界面。
  - **admin / hardware_admin / student / parent / adult_student**：永远走 admin_app/base.html / student_base.html，SA 专属视觉层与相关 API 不可访问 (403 或静默不可见)。

## Goals
1. **SA 专有界面与排版复写**：对 `/admin_app/*` 全部页面 + `admin_center.html` + `super_admin_dashboard.html` 注入统一的 SA 专属排版骨架（侧栏宽度/色板/topbar/硬件徽章/Arduino 入口/监控模块/巡检面板）。
2. **双硬件自动加载触发器**：一旦 `VIKEY present=True AND SZU100 present=True AND is_authentic=True AND session.role=super_admin(wuchenghao15)`，后端 before_request 将 `layout_mode=SA_PROPRIETARY` 注入模板上下文，前端 JS 按 5s 心跳轮询 + WebSocket/SSE 双保险自动应用/解除。
3. **强制认证双密钥硬链**：在现有 `VikeyEnforcementMiddleware` 补齐 SZU100 校验 — SA 访问强制路径必须 VIKEY + SZU100 **同时存在且合法**，缺一即 `allowed=False` 并走审计告警链。
4. **Arduino 页面 SA-only 强约束复现**：`/admin_app/arduino_ide` + `/api/arduino/*` 走单一 `_check_arduino_api_permission()`（`username == wuchenghao15` + 双硬件同时在线），其他角色返回 403 HOTLINK_BLOCKED 风格。
5. **拔出锁定自动回退**：SA 会话中 VIKEY 或 SZU100 任一拔出，30s 内前端心跳检测到后立即弹锁定遮罩（`overlay-scrim-dark`）并销毁 SA 专属令牌，服务端返回 401 触发重定向 `/auth/login?reason=hardware_removed`。

## Non-Goals
- 不修改或弱化任何现有的学生/家长/老师/普通管理员界面与访问路径。
- 不改变用户认证流程 (7 要素/双硬件登录) 的登录 UI；仅在登录成功后的布局注入与自动适配生效。
- 不引入新的前端框架或依赖；在现有 `super_admin_base.html` 与 `admin_app/base.html` 之上以 CSS class 切换 + 新 `sa_proprietary.css/js` 增量实现。
- 不对 VIKEY/SZU100 硬件驱动层做底层改造；仅复用 `VikeyAPI.detect()` 与 `detect_szu100()` 既有 API。
- 不构建移动端专用 SA 界面，但响应式布局在 ≤768px 下必须可用（继承现有 mobile 断点）。

## Background & Context
### 代码现状审计 (2026-08-30 抽样)
1. **两套 layout 基础并存**：
   - `frontend/templates/super_admin_base.html`：设计令牌注入 + `layout/sidebar/main-content/topbar` 五段骨架，SA 账号专用。
   - `flask-app/templates/admin_app/base.html`：art_layer 风格 `art-layout/art-sidebar/art-main/art-header` 四段骨架，供 `/admin_app/*` 65+ 个页面继承。
   - 两套互不统一，SA 专有视觉在后者中缺失。
2. **VikeyEnforcementMiddleware (L3378 server_real_db.py → `_output/app/middlewares/vikey_enforcement_middleware.py`)**：
   - **当前缺口**：`check_vikey_enforcement` 仅调 `_check_vikey()` 校验 VIKEY 加密狗 (L170)，完全未校验 SZU100 — 单把 VIKEY 插入就能放行 SA 页面，违反双硬件硬约束。
   - `VIKEY_REQUIRED_PATHS`：覆盖 `/admin_app/`、`/super_admin`、`/dashboard` 等，本 spec 无需修改列表，但补齐 SZU100 检查。
3. **SZU100 检测能力** (`core/services/szu100_driver.py:detect_szu100`)：已实现 ioreg BSD 映射 + 卷标/VID/PID/制造商/CD-ROM/尺寸 六维判断，返回 `{present, is_authentic, devices, auth_status}`，可直接调用。
4. **双硬件原子校验在登录流已具备** (`auth_routes.py L421-L439`)：`HardwareKeyProvider` 层做了 VIKEY + SZU100 双密钥原子校验，但 **会话后的页面访问链未继承此校验** — 这是本 spec 的核心补项。
5. **Arduino 权限**：server_real_db.py L15941 仅在注释声明「arduino_* 前缀仅 wuchenghao15 可访问」，未找到 `_check_arduino_api_permission()` 实函数 — 无守卫代码，需在本 spec 补齐并挂到所有 arduino_* 路由入口。
6. **前端无硬件热插拔心跳**：现有 `vikey_client.js` 存在，但无 5s 级「双硬件同时在线 → 切换 layout_mode」的客户端闭环。

### 硬约束来源 (规则文档)
- §用户权限.md L1：「超级管理员只能有且仅有一个，就是wuchenghao15」；L1.1：7 要素强认证 + VIKEY/SZU100 双密钥同时连接。
- §用户权限.md 「Arduino 页面」：仅 wuchenghao15，其他角色 403。
- §14 IRON_RULE：禁止任何绕过（bypass_allowed=False）。
- 开发规则.md §安全：防盗链 + @system_container 权限装饰器。

## Functional Requirements
### FR-1: 双密钥并发状态聚合 API
- 新增 `GET /api/hardware/dual-status`：返回 `{vikey: {present, serial, sa_bound_ok}, szu100: {present, is_authentic}, both_authenticated: bool, layout_mode: "SA_PROPRIETARY" | "STANDARD", username, role_canonical}`。
- 权限：鉴权路由。未登录 → 401；非 wuchenghao15 → `layout_mode=STANDARD` 且不返回敏感字段。
- 速率：客户端 ≤ 5s 一次，后端 `busy_timeout` 防锁。

### FR-2: 中间件强校验（双密钥 AND 关系）
- 改造 `VikeyEnforcementMiddleware.check_vikey_enforcement()`：当 `is_super_admin=True` 时，先调 VIKEY 再调 `detect_szu100()`；**任一返回不合法 → `allowed=False`**，写入 `vikey_enforcement_logs`，原因含「缺 VIKEY」/「缺 SZU100」/「SZU100 伪造」（仅 name 非硬件特征时）。
- 新增中间件方法 `get_dual_hardware_status()` 给 FR-1 复用。
- 保持 `_is_vikey_required` / VIKEY_WHITELIST_PATHS 不变。

### FR-3: 模板上下文自动注入 layout_mode
- Flask 在 `before_request` 末尾（after 鉴权）挂 `@app.context_processor` 注入 `_sa_layout_ctx = { layout_mode, dual_authenticated, vikey_serial, szu100_volume }` 到所有模板。
- 仅当：`session.username == "wuchenghao15" AND dual_authenticated == True` 时 `layout_mode = SA_PROPRIETARY`，否则 `STANDARD`。
- `super_admin_base.html` 与 `admin_app/base.html` 均支持 class 切换：`<body class="layout-mode-{{ layout_mode }}">`。

### FR-4: SA 专有排版布局 (CSS + HTML 骨架)
- 新增 `static/css/sa_proprietary.css`：仅 `.layout-mode-SA_PROPRIETARY` 作用域生效，复写以下语义：
  - **Sidebar SA**：宽 260px（比标准 240 宽 20），`border-left: 3px solid var(--sa-gold-accent)`（金色彩边）；新增 3 个区块：
    1. **硬件状态面板**：VIKEY 🟢/🔴、SZU100 🟢/🔴、双硬件在线徽章「双锁已启用 · SA PROPRIETARY MODE」
    2. **EigenFlux 顾问入口**：直接跳转 `/admin_app/eigenflux_center.html`，显示当前在线专家数
    3. **15 核心 daemon 状态条**：RUNNING/STOPPED/FAILED 数字速览（点击跳转 `/admin_app/process_monitor.html`）
  - **Topbar SA**：新增三模块 ① 双硬件图标徽章 ② SA 专属快捷入口：规则治理 / 恢复节点 / 影子系统 / 安全审计 ③ 7 要素 30s 心跳徽章「SESSION_LIVE」
  - **内容区 SA**：`content-sa` + 24px 栅格；dashboard cards 默认 4 列（标准 3 列），信息密度提升
  - **Arduino 专属入口徽标**：侧栏显式高亮 Arduino 项（仅 SA 专有模式中渲染；STANDARD 模式中此条目仅 wuchenghao15 可见，但色值保持非 SA 金）
- 新增 `static/js/sa_proprietary.js`：
  - `SAUIManager.start(poll_ms=5000)`：轮询 FR-1 API；`both_authenticated` 切换即：
    1. toggle `document.body.classList` `layout-mode-SA_PROPRIETARY`
    2. 触发窗口级事件 `sa-layout-updated` 以便子页仪表板重绘
    3. 任一硬件下线 → 渲染半透明锁定遮罩 `sa-lock-overlay`，写入浏览器 console error，等待下一次双硬件在线自动解锁。

### FR-5: 所有 admin_app 子页统一继承 SA 专有层
- 65+ 个 admin_app/*.html 通过 FR-3 的 body class 自动生效，**逐个手动改模板不允许**；以全局 CSS/JS 覆盖实现。
- 但保证 `dashboard.html`、`dashboard_unified.html`、`security_dashboard.html`、`health_monitor.html`、`process_monitor.html` 5 个高可见度页面的 SA 专有布局在视觉核对下完整（金色彩边 / 硬件徽章 / 4 列卡栅）。

### FR-6: Arduino 路由统一守卫
- 统一守卫函数 `_check_arduino_api_permission()` 实现（放在 `routes/admin_routes.py` 顶层或 `app/utils/`）：
  - 逻辑：`session.username == "wuchenghao15" AND dual_authenticated == True → OK`；否则 403，`{ code: "ARDUINO_SA_ONLY", message: "Arduino 页面仅 wuchenghao15 可访问" }`。
- `/admin_app/arduino_ide` 路由 + 所有 `/api/arduino/*` 路由前缀绑定此守卫。

### FR-7: 审计落库
- 双密钥状态每次切换：both=True→False 或 False→True 时，写入 `automation_console_logs(eigenflux_flag=1)` 与 `vikey_enforcement_logs`，记录 username/ip/ua/session_id/切换前后状态。
- Arduino 守卫触发 403 时落库 `security_credential_stuffing` 级日志。

### FR-8: 开发页面/路由走 @system_container
- 新增的 `/api/hardware/dual-status` 与改修的中间件不得绕过权限装饰器；`before_request` 链中防盗链逻辑保持原状作用，未授权且 Referer 非法的请求仍然 403 → 重定向 `/index?from=hotlink_blocked`。

## Non-Functional Requirements
### NFR-1: 安全
- SA 专有布局相关 CSS/JS 文件名可被任意用户下载，但敏感面板内容（硬件徽章数字、Arduino 入口高亮、EigenFlux 专家数）必须通过模板/上下文注入生成，纯静态 CSS/JS 不暴露敏感数据。静态文件不含任何硬编码用户名、序列号、路径。
- 双密钥检测与中间件校验链的失败均必须记录审计日志；任何「仅 VIKEY 在线 / 仅 SZU100 在线」尝试访问 SA 页面即告警级日志（severity=warning/critical）。

### NFR-2: 性能
- `/api/hardware/dual-status` 单次响应 P95 ≤ 400ms（含 VIKEY + SZU100 检测缓存命中）。
- 缓存：`detect_szu100()` 已自带缓存 TTL；`VikeyAPI.detect()` 本次调用结果在内存缓存 2s。
- SA 专有 CSS 体积 ≤ 20KB；JS ≤ 10KB（不压缩）。

### NFR-3: 兼容性
- 支持 macOS (主要) 与 Linux 下的驱动调用（`ioreg/lsusb/lsblk`）。
- 响应式断点：1440px / 1024px / 768px；SA 专有模式下 ≤768px 侧栏默认折叠。

### NFR-4: 可观测性
- `automation_console_logs` 中双密钥切换事件 100% 落库；前端切换 JS 在 console 输出 `[SA-UI] layout: STANDARD → SA_PROPRIETARY (both=True)` 等状态线。

### NFR-5: 健壮性
- 任一硬件驱动异常（VikeyAPI抛异常 / szu100 检测超时）时，服务端视为「不合法」返回 STANDARD 模式，绝不因为驱动错误误放行；同时记录 exception 级日志。
- 双密钥拔出后：前端最多 2 个周期（10s）内进入锁定遮罩，服务端后续请求（polling 除外）统一 401 注销 session。

### NFR-6: 设计规范
- 颜色：所有视觉增强项（SA 金、徽章色、边框色）走 Element Plus design token 变量，禁止硬编码 HEX；参考 `mtscos_design_tokens.css`。
- 字体与间距继承 super_admin_base.html 已定义 `--font-sans / --s-2 ~ --s-6 / --radius-md/--radius-lg`。

## Constraints
- **Technical**:
  1. 不可删除 `VikeyEnforcementMiddleware`，只可扩展；保持 `check_vikey_enforcement` 签名稳定。
  2. 不得在未登录上下文返回任何 SA 专有的双密钥检测结果字段。
  3. Arduino 守卫函数名必须为 `_check_arduino_api_permission()`（规则文档约定）。
  4. 保持与 `server_real_db.py` 的 before_request 拦截链兼容，不创建平行拦截链。
- **Business**:
  1. SA 唯一性：wuchenghao15 一人。
  2. 双硬件密钥「同时在线」是 SA 专有布局进入的唯一硬条件，无任何 flag 或 env 可绕过。
  3. 任何普通 admin 访问 SA 专有路由继续返回 403；SA 专有 class/CSS 不影响其视觉（body 无 `layout-mode-SA_PROPRIETARY` 即零样式泄漏）。
- **Dependencies**:
  - `core.services.vikey_api.VikeyAPI.detect()`（现成）
  - `core.services.szu100_driver.detect_szu100()`（现成）
  - `before_request` 链与 `@system_container`（现成）
  - `automation_console_logs` 审计表 + `vikey_enforcement_logs`（现成表创建）

## Assumptions
1. 热插拔检测在 macOS 下通过 `ioreg/ls /dev/cu.* /Volumes/` 实现，无需内核级 USB 通知（现有驱动已足够）。
2. SZU100 卷标 / VID:PID / 制造商组合足以区分伪造与正版。
3. 前端轮询 5s 周期足够；不强制建设 WebSocket 通道，JS 层可降级到 SSE，但本次仅实现轮询版本。
4. 所有 admin_app 子页面通过 `body` 上的 class 作用域即可覆盖 95%+ 视觉，无需逐一在子页添加特殊 block。

## Open Questions
- [x] Q1: Arduino IDE 页面 /api/arduino/* 的入口文件 — 确认：当前在 `server_real_db.py` L15941 有注释声明但无统一守卫，本 spec FR-6 新建单一守卫绑定所有 arduino 路由。
- [x] Q2: `VikeyEnforcementMiddleware` 实际生效位置 — 确认：`server_real_db.py` 的 before_request (L3382-L3400) 已注入，故 FR-2 改造直接修改 `_output/app/middlewares/vikey_enforcement_middleware.py` 类 + 如存在 `flask-app/app/middlewares/vikey_enforcement_middleware.py` 同步改。
- [x] Q3: SA 专有布局需要的 5 个高可见页面 — 确认：dashboard, dashboard_unified, security_dashboard, health_monitor, process_monitor（均继承 admin_app/base.html）。

## Acceptance Criteria

### AC-1: 双密钥状态聚合 API 契约正确
- **Type**: `rule`
- **Given**: 服务运行于 8888，当前会话角色不同组合
- **When**: 客户端请求 `GET /api/hardware/dual-status`（已登录 cookie）
- **Then**: 响应字段严格包含 `{vikey: {present,serial,sa_bound_ok}, szu100:{present,is_authentic}, both_authenticated: bool, layout_mode: str, username, role_canonical}`
- **Pass Condition**: 
  - 未登录 → 401 AUTH_REQUIRED；
  - 非 SA 登录 → `layout_mode=STANDARD, both_authenticated=False`；敏感字段（serial）为 null；
  - SA 登录 + 双硬件在线 → `layout_mode=SA_PROPRIETARY, both_authenticated=True`；
  - SA 登录 + 缺任一 → `both_authenticated=False`，且原因字段含缺失项名。
- **Evidence**: 4 组 curl 调用（未登录 / 学生 / SA 无双硬件 / SA 双硬件均在线）的原始输出 + status code。

### AC-2: 中间件 SA 强制路径必须双密钥 AND
- **Type**: `rule`
- **Given**: session.username = wuchenghao15
- **When**: 访问任一 `VIKEY_REQUIRED_PATHS`（如 `/admin_app/dashboard`），且 VIKEY 或 SZU100 缺任一
- **Then**: `VikeyEnforcementMiddleware.check_vikey_enforcement` 返回 `allowed=False`，HTML 请求重定向 `/auth/login?error=...`，API 请求返回 403 JSON 含 `vikey_status` / `szu100_status`。
- **Pass Condition**: 三组独立测试（VIKEY拔 / SZU100拔 / 伪造SZU100 is_authentic=False）均拦截成功 + 写入 `vikey_enforcement_logs` 一条 severity ≥ warning。
- **Evidence**: 中间件单元测试脚本输出；日志表 SQL 计数。

### AC-3: 模板上下文 layout_mode 注入正确性
- **Type**: `rule`
- **Given**: Flask 模板渲染任意 `admin_app/*.html` 或 `admin_center.html`
- **When**: 双密钥 SA 登录 vs 普通 admin 登录
- **Then**: `<body class="... layout-mode-XX">` 对应值正确：SA 双钥→SA_PROPRIETARY；否则 STANDARD。
- **Pass Condition**: `render_template` 上下文变量存在 `layout_mode` 且与双密钥状态一致；通过注入测试脚本 grep HTML 输出验证 class。
- **Evidence**: SA/普通 admin 登录分别 `GET /admin_app/dashboard` → grep `layout-mode-` 返回值对比。

### AC-4: SA 专有排版视觉层加载完整
- **Type**: `rubric`
- **Dimension**: 视觉层完整性与可见性
- **Scale**: 1-5
- **Anchors**: 1 = SA 专有 class 作用域不生效 / 关键组件缺失；3 = 核心 side/top/content 三段有视觉差异但硬件徽章缺失或未高亮 Arduino；5 = SA 模式下：侧栏彩边(3px金)/硬件面板(VIKEY+SZU100双图标+双锁徽章)/EigenFlux专家数/daemon 速览条、顶栏三模块、卡栅4列均已出现；非 SA 模式下以上元素完全不出现。
- **Pass Threshold**: >= 4
- **Evidence**: 两张对比截图（SA_PROPRIETARY vs STANDARD）+ CSS 选择器命中统计。

### AC-5: 前端自动切换（5s心跳）+ 拔出锁定回退
- **Type**: `rule`
- **Given**: SA 已双硬件登录 + 访问 `/admin_app/dashboard`
- **When**: 1) 拔出 VIKEY 或 SZU100；2) 下一次 5s 轮询后；3) 重新插回双硬件并再等一轮。
- **Then**:
  - 拔出：≤ 10s 内 body class 切回 STANDARD 并显示 `sa-lock-overlay`，页面交互元素不可点击；
  - 重插：≤ 10s 内 overlay 解除，body class 切回 SA_PROPRIETARY，`sa-layout-updated` 事件在 console 可见。
- **Pass Condition**: 拔出/重插各一次手动模拟，JS 控制台与 DOM 检查点均通过。
- **Evidence**: 浏览器 console 日志（`[SA-UI] ...`）的截图或文本抓包。

### AC-6: Arduino 守卫拦截 100%
- **Type**: `rule`
- **Given**: 不同角色组合 (SA双钥在线 / SA仅一钥 / admin / student)
- **When**: 访问 `GET /admin_app/arduino_ide` 与任一 `GET /api/arduino/components`
- **Then**: 仅 SA + 双钥 → 200；其余均 403 + `code=ARDUINO_SA_ONLY` + 审计落库。
- **Pass Condition**: 4 组合 × 2 接口 = 8 次请求，返回码严格符合。
- **Evidence**: curl 8 次原始输出 + 日志表计数。

### AC-7: 审计落库完整性
- **Type**: `rule`
- **Given**: 执行 AC-2/5/6 全部操作
- **When**: 查询 `automation_console_logs WHERE source IN ('dual_hardware_switch','arduino_guard') AND eigenflux_flag=1` 与 `vikey_enforcement_logs`
- **Then**: 双密钥切换次数 = both_true→false + false→true 次数；Arduino 403 次数 = AC-6 失败案例数；均 ≥ 1 且事件类型正确。
- **Pass Condition**: SQL 查询各分组计数 ≥ 对应期望值。
- **Evidence**: 两组 SQL 查询结果。

### AC-8: 防盗链/权限装饰器不被破坏
- **Type**: `rule`
- **Given**: 未登录 + 伪造 Referer 头非首页
- **When**: 请求 `/api/hardware/dual-status` 与 `/admin_app/dashboard`
- **Then**: 403 HOTLINK_BLOCKED 并重定向 `/index?from=hotlink_blocked`（页面类）/ JSON 401（API类），行为与本次改动前保持不变。
- **Pass Condition**: 2 接口 curl 带伪造 Referer 的返回与历史一致。
- **Evidence**: 2 组 curl 输出。
