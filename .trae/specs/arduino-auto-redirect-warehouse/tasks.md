# Arduino 设备插入自动跳转 + 充血路由 + 拔出锁定专仓 — 原子任务清单 (v1.0)
#
# 执行顺序：T00 → [T01,T02] → T03 → T04 → T05 → [T06,T07,T08,T09] → T10
#           → T11 → [T12,T13,T14] → T15 → T16 → T17 → T18 → T19 → T20
#
# 依赖声明：DONE 状态写入 mt_dev_flow_session.nodes；任何任务失败回滚到上一节点。
# ============================================================================

## ── Phase 0：数据库基座（AC-6） ────────────────────────────────────────

- id: T00
  title: 新增 3 张数据表 + 索引自动建表
  ac_refs: [AC-6]
  depends: []
  files:
    - flask-app/engines/ai_arduino_detect_engine.py
  spec:
    - 在 ensure_detect_tables() 内新增 CREATE TABLE（IF NOT EXISTS）：
        1. mt_arduino_user_vault：
           vault_id TEXT PRIMARY KEY,            -- ARD-VLT-<hash>-<uuid>
           bound_user_id INTEGER NOT NULL,       -- user_id FK
           session_id TEXT,                      -- mt_arduino_user_sessions.session_id
           snapshot_version INTEGER NOT NULL DEFAULT 1,
           label TEXT DEFAULT '拔出自动保存',
           payload_json TEXT NOT NULL,           -- {code, variant_actions, variant_params, ...}
           acl_json TEXT NOT NULL DEFAULT '{"owner":0,"readers":[]}',
           size_bytes INTEGER NOT NULL DEFAULT 0,
           committed_at TEXT NOT NULL
        2. mt_arduino_admin_settings：
           setting_version TEXT PRIMARY KEY,     -- ARD-SET-<ts>-<uuid>
           scope TEXT NOT NULL DEFAULT 'global', -- global / per_user
           key_name TEXT NOT NULL,               -- board_whitelist / toolchain_path / ...
           value_json TEXT NOT NULL,
           changed_by INTEGER NOT NULL,
           changed_at TEXT NOT NULL,
           active_flag INTEGER NOT NULL DEFAULT 1
        3. mt_arduino_lock_log：
           lock_id TEXT PRIMARY KEY,             -- ARD-LCK-<uuid>
           user_id INTEGER NOT NULL,
           session_id TEXT,
           lock_trigger TEXT NOT NULL,           -- device_removed / manual / api_423
           lock_reason TEXT,
           released_by TEXT,                     -- user_reinsert / commit / discard
           released_at TEXT,
           committed_vault_id TEXT
    - 索引：
        CREATE INDEX IF NOT EXISTS idx_arduino_vault_user
            ON mt_arduino_user_vault(bound_user_id, committed_at DESC);
        CREATE INDEX IF NOT EXISTS idx_arduino_settings_active
            ON mt_arduino_admin_settings(key_name, active_flag DESC);
        CREATE INDEX IF NOT EXISTS idx_arduino_lock_user
            ON mt_arduino_lock_log(user_id, released_at DESC);
    - 在 get_status() 顶部调用 ensure_detect_tables()，保证任意 DAO 访问触发建表。
  tests:
    - python3 -c "DROP 3 表 → import 引擎 → 调 get_status() → SELECT name 断言 3 表名齐全"
    - PRAGMA index_list 断言 3 条索引存在。

## ── Phase 1：后端权限守卫 & 路由分流（AC-2, AC-3） ─────────────────────

- id: T01
  title: 扩展守卫函数支持 scope 参数（ide/setup/vault）
  ac_refs: [AC-3, NFR-2]
  depends: [T00]
  files:
    - flask-app/routes/arduino_session_routes.py
  spec:
    - 重构 _check_arduino_api_permission(scope='ide')：
        scope='ide'   → 仅 username == 'wuchenghao15' + 双密钥（旧行为不变）
        scope='setup' → role_canonical ∈ {super_admin, admin, hardware_admin}；
                        super_admin 仍需双密钥；admin/hardware_admin 只需正常登录 session
        scope='vault' → 任意已登录用户（仅本人行可见，由 DAO 层过滤）
    - 守卫返回 (allowed: bool, resp_json_or_None, role_canonical)。
    - 新增辅助 _ensure_device_present(bound_vid_pid)：
        调 engine.get_status()；connected=0 → (False, 423 LOCKED)
        vid_pid ≠ bound → (False, 409 CONFLICT)
  tests:
    - flask test client 4 组账号 × 3 种 scope = 12 次调用，断言 HTTP 状态码。

- id: T02
  title: 登录成功充血路由 override（后端 + session.bind API）
  ac_refs: [AC-2, FR-2]
  depends: [T01]
  files:
    - flask-app/routes/auth_routes.py
    - flask-app/routes/arduino_session_routes.py
  spec:
    - auth_routes.py /auth/login POST：写 session 后，追加：
        if session.get('arduino_bound') or req_json.get('arduino_bound'):
            status = ai_arduino_detect_engine.get_status()
            if status.connected > 0:
                if user.role_canonical in {super_admin, admin, hardware_admin}:
                    redirect = '/admin_app/arduino_admin_setup'
                else:
                    redirect = '/admin_app/arduino_ide'
                session['bound_vid_pid'] = status.connected_vid_pids[0]
                session['bound_at'] = iso_now()
    - arduino_session_routes.py 新增：
        GET  /api/arduino/session/bind
            → session.arduino_bound = True + 写 bound_vid_pid/bound_at + 返回 {"bound": true}
        GET  /api/arduino/session/redirect_target
            → 返回 {"redirect": <按 FR-2 计算后的最终路径>}
  tests:
    - flask test client 3 种角色 (student / admin / SA) × arduino_bound=1 + mock connected=True
      → 断言 login JSON redirect 字段分别为 IDE / SETUP / SETUP。
    - 单独测 bind & redirect_target API：session 字段写入正确。

- id: T03
  title: 管理员特殊路由拦截（IDE 路由→管理员 302 设置页）
  ac_refs: [AC-3]
  depends: [T01]
  files:
    - flask-app/routes/arduino_session_routes.py
  spec:
    - 在 _arduino_sa_only_guard() 中 /admin_app/arduino_ide 路径命中时：
        role ∈ admin → 写 ARD_ROLE_REDIRECT_SETUP 审计（detect_log）
                       → return redirect('/admin_app/arduino_admin_setup', code=302)
        role ∉ admin → 必须 session.arduino_bound=True 且 engine.get_status().connected
                       → 否则 302 /index
    - 新增路由 GET /admin_app/arduino_admin_setup：
        scope='setup' 守卫通过后
        → render_template('admin_app/arduino_admin_setup.html',
                          page_type='form',
                          settings_dict=load_active_settings())
  tests:
    - admin session GET /admin_app/arduino_ide → 断言 302 Location 包含 arduino_admin_setup
    - student session + arduino_bound + connected → GET IDE → 200 + 响应体含 mtscos-canvas-stage
    - student 无 arduino_bound → GET IDE → 302 /index

## ── Phase 2：管理员设置页 API（FR-3） ──────────────────────────────────

- id: T04
  title: 管理员设置保存 & 读取 API
  ac_refs: [FR-3]
  depends: [T03]
  files:
    - flask-app/routes/arduino_session_routes.py
    - flask-app/engines/ai_arduino_detect_engine.py (DAO)
  spec:
    - 引擎新增 DAO：
        save_admin_setting(key_name, value_json, changed_by)
            → 旧 active_flag=0 + 插入新 setting_version=1
        load_active_settings_dict()
            → {key: value_json parsed dict}
    - 路由新增：
        GET  /api/arduino/admin/setup
            → scope='setup' → 返回 load_active_settings_dict()
        POST /api/arduino/admin/setup
            → scope='setup' + _ensure_device_present(bound_vid_pid)（拔出 423）
            → body: {board_whitelist:[], toolchain_path, port_whitelist:[],
                     library_mirror_url, vault_quota_mb, variant_templates_json,
                     allowed_action_types, auto_save_on_remove:bool,
                     default_theme, default_font_size}
            → 逐 key 调 save_admin_setting → 返回 {version, saved_keys:[...]}
  tests:
    - admin 账号 POST 设置 → GET 回读 → 断言 key/value 一致
    - admin 账号拔出状态 POST → 423 LOCKED

## ── Phase 3：前端全局热插拔（FR-1, AC-1） ──────────────────────────────

- id: T05
  title: 前端全局热插拔脚本 arduino_global_hotplug.js
  ac_refs: [AC-1, FR-1]
  depends: [T02]
  files:
    - flask-app/static/js/arduino_global_hotplug.js (NEW)
    - flask-app/templates/admin_app/base.html
    - flask-app/templates/index.html
  spec:
    - 新 JS 脚本（无内联 style、无 BEM -- 裸类）：
        · ARDUINO_GLOBAL.pollInterval = 2000
        · lastInsertConfirm = false
        · pollOnce(): 调 GET /api/arduino/events/poll?global=1
            → 若命中 insert 事件且 currentPage ∉ {IDE, SETUP}：
                - 下一轮 poll 若 still inserted → lastInsertConfirm=true
                  → 未登录: location = /index?arduino_inserted=1&vid_pid=&model=
                    + localStorage.ARDUINO_BOUND_VIDPID = vid_pid
                  → 已登录: fetch GET /api/arduino/session/bind
                    → 成功后 fetch GET /api/arduino/session/redirect_target
                    → location = response.redirect
            → 若命中 remove 事件：
                - 若当前页为 IDE/SETUP → dispatch CustomEvent('arduino-device-removed')
                  （由页面内 FR-4 监听方处理锁定遮罩）
                - 删除 localStorage.ARDUINO_BOUND_VIDPID
    - 在 admin_app/base.html </body> 前注入 <script src="/static/js/arduino_global_hotplug.js"></script>
    - 在 index.html </body> 前同样注入（未登录场景）。
  tests:
    - Playwright：访问 /index → mock poll 返回 insert×2 次 → 3s 内断言 URL含 arduino_inserted=1
                  + localStorage.ARDUINO_BOUND_VIDPID 非空。
    - 静态脚本：assert 无 style=、无 '--' 裸类。

## ── Phase 4：拔出锁定 fail-closed（FR-4, AC-4） ───────────────────────

- id: T06
  title: IDE 页拔出锁定遮罩 + 三按钮 Modal
  ac_refs: [AC-4, FR-4]
  depends: [T05]
  files:
    - flask-app/templates/admin_app/arduino_ide.html
    - flask-app/static/css/mtscos_pages.css §12 （锁定遮罩类族复用 mtscos-dialog）
  spec:
    - 在 arduino_ide.html 尾部 JS 新增：
        window.addEventListener('arduino-device-removed', lockOverlayShow)
        function lockOverlayShow(reason='device_removed'):
            · 生成 lock_id = ARD-LCK-<uuid>
            · 全屏 div 加类 arduino-lock-overlay--visible（z-index 高于 IDE 面板）
            · 停止 autosave 定时器、compile_upload queue disabled
            · append mtscos-dialog（三按钮）：
                确认保存并写入专仓 → call commitToVault({confirm_reason:'device_removed'})
                放弃 → location = /index
                我已重新插入 → fetch /api/arduino/events/repoll_now
                              → connected=true && vid_pid match → hideOverlay()
                              → 否则 toast 仍未检测到匹配设备
    - mtscos_pages.css §12 追加（复用 mtscos-dialog 家族）：
        .mtscos-ide-page .arduino-lock-overlay--visible
            → position:fixed; inset:0; background:rgba(0,0,0,.72);
               display:flex; align-items:center; justify-content:center; z-index:9999
  tests:
    - Playwright: IDE 加载后 dispatch('arduino-device-removed')
                  → 500ms 内断言 .arduino-lock-overlay--visible 存在
                  + 保存按钮 disabled 属性。

- id: T07
  title: 设置页拔出锁定遮罩（与 IDE 对称）
  ac_refs: [AC-4]
  depends: [T06]
  files:
    - flask-app/templates/admin_app/arduino_admin_setup.html (NEW 模板占位)
  spec:
    - lockOverlayShow 逻辑完全复用 T06；区别：放弃按钮跳 /admin，
      确认保存按钮调 POST /api/arduino/admin/setup（保存当前表单）+ 关闭遮罩。
  tests:
    - 与 T06 对称；确认保存时 form data 落库 mt_arduino_admin_settings。

- id: T08
  title: 后端写接口 423 / 409 拦截（_ensure_device_present 全链路挂接）
  ac_refs: [AC-4, FR-4]
  depends: [T01]
  files:
    - flask-app/routes/arduino_session_routes.py
  spec:
    - 所有写接口入口首行调：
        ok, resp = _ensure_device_present(session.get('bound_vid_pid'))
        if not ok: return resp
      覆盖接口：
        POST /api/arduino/session/save
        POST /api/arduino/session/commit    （AC-5）
        POST /api/arduino/admin/setup       （T04）
        POST /api/arduino/session/compile_upload（模拟写接口）
    - 新增 GET /api/arduino/events/repoll_now：
        立即调 scan_devices() 同步一次 → 返回 engine.get_status()
  tests:
    - flask test client：bound=正常 vid → remove → POST save → 423 + device_status=removed
    - bound=vidA → 插入 vidB 设备 → POST save → 409 CONFLICT

## ── Phase 5：专仓 commit & 查询 API（FR-5, AC-5） ─────────────────────

- id: T09
  title: 变异动作与参数采集（前端 side）
  ac_refs: [FR-5]
  depends: [T06]
  files:
    - flask-app/templates/admin_app/arduino_ide.html
    - flask-app/templates/admin_app/arduino_admin_setup.html
  spec:
    - IDE 页 JS 增加：
        window.VARIANT_ACTIONS = []  // {ts, type, detail}
        window.VARIANT_PARAMS  = {}  // board, port, baud, libs, build_flags,
                                     // upload_speed, variant_macros, wiring_json,
                                     // monitor_sample_rate
        - 每次 compile/upload/switch board/change baud/save 时
          append VARIANT_ACTIONS.push({ts, type, detail})
        - VARIANT_PARAMS 随每个选择器 onchange 同步更新。
    - 设置页 JS：VARIANT_PARAMS = 当前表单序列化键值对。
  tests:
    - Playwright: IDE 点 3 次操作 → 断言 VARIANT_ACTIONS.length ≥ 3。

- id: T10
  title: commitToVault() 前端调用 + 后端落库
  ac_refs: [AC-5, FR-5]
  depends: [T08, T09]
  files:
    - flask-app/templates/admin_app/arduino_ide.html
    - flask-app/routes/arduino_session_routes.py
    - flask-app/engines/ai_arduino_detect_engine.py (DAO: commit_to_user_vault)
  spec:
    - 前端 commitToVault(reason):
        fetch POST /api/arduino/session/commit
          body: { session_id, code_content: editor.getValue(),
                  variant_actions_json: JSON.stringify(VARIANT_ACTIONS),
                  variant_params_json: JSON.stringify(VARIANT_PARAMS),
                  confirm_reason: reason, pin_reinserted_if_any }
          → 成功 → toast 显示 vault_id + 刷新左侧 vault drawer
    - 引擎 DAO commit_to_user_vault(user_id, username, session_row):
        vault_id = f"ARD-VLT-{sha1(user_id)[:8]}-{uuid8}"
        payload = { code, variant_actions, variant_params,
                    usage_trace, edit_history,
                    device_snapshot: get_status() }
        写入 mt_arduino_user_vault 行 → size_bytes = len(payload_json)
        更新 mt_arduino_user_sessions: committed=1, committed_at, variant_*_json, locked_reason
        写入 mt_arduino_lock_log: committed_vault_id = vault_id, released_by='commit'
        return row
    - 路由 POST /api/arduino/session/commit：
        先 _ensure_device_present 可选跳过（reason=device_removed 时允许 commit 即使已拔除）
        → 查 session 行 → DAO → return {vault_id, snapshot_version,
                                           vault_size_bytes, committed_at}
  tests:
    - flask test client: student commit → SELECT vault WHERE user_id=uid
      → 断言 size_bytes>0, payload_json 顶层含 code_content/variant_actions/variant_params
    - 另一 student session GET /api/arduino/vault/list → 不含上述 vault_id（隔离）。

- id: T11
  title: 专仓 list / get API（带 ACL 过滤）
  ac_refs: [AC-5, NFR-2]
  depends: [T10]
  files:
    - flask-app/routes/arduino_session_routes.py
    - flask-app/engines/ai_arduino_detect_engine.py
  spec:
    - 引擎 DAO:
        list_user_vault(user_id, page=1, size=10, as_user=None):
            as_user 仅当 caller 是 SA 生效，否则 WHERE bound_user_id = user_id
            ORDER committed_at DESC → LIMIT size OFFSET (page-1)*size
        get_vault_by_id(vault_id, user_id, is_sa):
            row = SELECT * WHERE vault_id = ?
            if not is_sa and row.bound_user_id != user_id → 403
            return row
    - 路由:
        GET /api/arduino/vault/list?page&size&as_user=
        GET /api/arduino/vault/<vault_id>?as_user=
  tests:
    - 2 个普通用户各自 commit → cross-list GET 断言 0 行交叉返回。
    - SA 带 ?as_user=uid1 → 可返回 uid1 的行。

## ── Phase 6：用户专仓 UI（FR-6, AC-8） ────────────────────────────────

- id: T12
  title: IDE 左侧「用户专仓」抽屉 & 加载回填
  ac_refs: [FR-6, AC-8]
  depends: [T11]
  files:
    - flask-app/templates/admin_app/arduino_ide.html
    - flask-app/static/css/mtscos_pages.css §12 （ide-vault-drawer 族）
  spec:
    - IDE 左侧栏已有 Tab（文件/库）后追加 Tab「专仓」：
        Tab 激活 → fetch /api/arduino/vault/list?size=10
        → 渲染列表项（vault_id 尾6位 + 时间 + label + size_kb）
        → 点击某行 → confirm「载入此专仓快照？当前未保存代码将被覆盖」
          → fetch /api/arduino/vault/<id>
          → editor.setValue(row.payload_json.code_content)
          → 将 variant_params 回填到 board/port/baud 选择器
  tests:
    - Playwright: 点击专仓 Tab → 断言列表项数量 ≤ 10
                + 点击某行后 editor 内容变更。

- id: T13
  title: 设置页「用户专仓配额」Tab
  ac_refs: [FR-6]
  depends: [T04, T11]
  files:
    - flask-app/templates/admin_app/arduino_admin_setup.html
    - flask-app/routes/arduino_session_routes.py
  spec:
    - 设置页 Tab：全局设置 / 专仓配额
    - 专仓配额 Tab：GET /api/arduino/admin/vault_usage → 返回 [{user_id, username,
                  total_mb, commit_count, last_commit_at, over_quota}]
    - 表格行：超限标红；可跳转 SA 查看该用户所有 vault。
  tests:
    - 生成 3 用户各提交 1~3 次 → 断言 usage 行汇总正确。

- id: T14
  title: 前端登录页充血路由保险（localStorage 双保险）
  ac_refs: [AC-2, FR-2]
  depends: [T05]
  files:
    - flask-app/templates/index.html （或 login 组件所在模板）
  spec:
    - 登录表单 submit 成功（JSON {redirect}）落地后：
        if (localStorage.ARDUINO_BOUND_VIDPID) {
          fetch('/api/arduino/session/redirect_target').then(r=>r.json()).then(d=>{
            if (d.redirect && location.pathname !== new URL(d.redirect, location).pathname)
              location = d.redirect;
          });
        }
  tests:
    - Playwright: login 后带 VIDPID localStorage → 断言最终落地路径 /admin_app/arduino_ide。

## ── Phase 7：管理员设置页模板（AC-7） ─────────────────────────────────

- id: T15
  title: 管理员录入设置页 arduino_admin_setup.html（FORM 类型）
  ac_refs: [AC-7, NFR-4]
  depends: [T04]
  files:
    - flask-app/templates/admin_app/arduino_admin_setup.html (NEW)
    - flask-app/static/css/mtscos_pages.css §13 （arduino-setup 族 · 最小作用域）
  spec:
    - 模板骨架：
        {% extends 'admin_app/base.html' %}
        {% set page_type = 'form' %}
        {% block content %}
        <div class="mtscos-action-bar adp-slide-up">
          <div class="mtscos-action-bar-title">
            ⚙️ Arduino 管理员录入设置
            <span class="mtscos-action-bar-subtitle">板卡白名单 · 编译链 · 端口 · 专仓配额 · 变异模板 · 自动保存</span>
          </div>
          <div class="mtscos-action-bar-actions">
            <button class="mtscos-btn is-secondary is-sm" data-role="sa-only"
                    onclick="location.href='/admin_app/arduino_ide'">切换到 IDE（仅 SA）</button>
            <button class="mtscos-btn is-primary is-sm" id="btn-save-setup">保存设置</button>
          </div>
        </div>
        <form class="mtscos-form mtscos-stagger" id="arduino-setup-form">
          <!-- 每节字段使用 mtscos-form-group / mtscos-form-label / mtscos-form-input
               板卡白名单 (textarea JSON) · 编译链路径 (input) · 端口白名单 (input tags)
               库镜像 URL (input) · 专仓配额 MB (number) · 变异模板 (textarea JSON)
               允许动作类型 (checkbox group) · 拔出自动保存 (switch) · 默认主题/字号 -->
        </form>
        {% endblock %}
    - CSS 写入 mtscos_pages.css §13，**作用域限定**：
        .mtscos-content[data-page-type="form"] .mtscos-form（已存在）下 .arduino-setup-*
    - **零内联 style / style=**；所有宽度/颜色用 Token 类。
  tests:
    - 千轮扫描 V1~V4：V2 = 0 内联 style；V3 = 0 BEM -- 裸类。

## ── Phase 8：前端保险 & 角色回显（AC-2） ─────────────────────────────

- id: T16
  title: 前端充血路由双保险 & IDE 设置页头部角色标签
  ac_refs: [AC-2, AC-8]
  depends: [T14, T15]
  files:
    - flask-app/templates/admin_app/arduino_ide.html
    - flask-app/templates/admin_app/arduino_admin_setup.html
  spec:
    - IDE 顶部 ActionBar 右侧追加：
        <span class="mtscos-underline-chip" data-device-status>🔌 设备检测中…</span>
        JS poll 后改 innerText = 「已绑定 {model} {vid_pid}」 or 「未检测到设备」。
    - 设置页同位置追加「管理员录入模式 · role: {role}」标签。
  tests:
    - Playwright: 插入 IDE → 标签文本包含 已绑定。

## ── Phase 9：千轮测试 & 审计（AC-6, AC-7, AC-8） ──────────────────────

- id: T17
  title: AC-6 建表自动化脚本
  ac_refs: [AC-6]
  depends: [T00]
  files:
    - flask-app/_tests/test_arduino_tables_auto.py (NEW)
  spec:
    - 脚本内容：DROP 3 表 → import engine → get_status() → SELECT table/索引断言
    - 断言结果写入 test_report/arduino_ac6.json。
  tests:
    - 手动 python3 执行 → PASS。

- id: T18
  title: AC-2 + AC-3 + AC-5 后端 5 条路由接口脚本测试
  ac_refs: [AC-2, AC-3, AC-5]
  depends: [T10, T11]
  files:
    - flask-app/_tests/test_arduino_backend_ac.py (NEW)
  spec:
    - flask test client 覆盖：
        a) 3 角色 login + arduino_bound=1 → redirect 断言
        b) admin GET /admin_app/arduino_ide → 302 → SETUP
        c) student bound GET /admin_app/arduino_ide → 200 含工作台字符串
        d) commit vault → SELECT 行断言 + 跨用户 list 隔离
        e) 拔出 → POST save → 423
  tests:
    - 5/5 PASS → test_report/arduino_backend.json。

- id: T19
  title: AC-7 千轮子集 V1~V4 扫描 arduino_admin_setup.html + arduino_ide.html
  ac_refs: [AC-7]
  depends: [T15, T16]
  files:
    - 使用既有 §14_scan.py 脚本
  spec:
    - 扫描目标：arduino_admin_setup.html + arduino_ide.html
    - 维度：V1（未定义类引用，≤0 或 白名单）/ V2（内联 style=, ≤1 且为进度条带 data-fill）
          / V3（BEM -- 裸类，0）/ V4（绕过标记，0）
    - 维度 4 项每项 ≤ 1 处违规 → PASS（总分 ≥ 4）。
  tests:
    - 产出 arduino_ac7_v1v4_scan.json。

- id: T20
  title: AC-8 端到端 walkthrough（Playwright · 阻塞点计数）
  ac_refs: [AC-8]
  depends: [T19]
  files:
    - flask-app/_tests/test_arduino_e2e_ac8.py (NEW)
  spec:
    - Playwright 脚本 walkthrough：
        1. 访问 /index → mock poll insert×2 → URL 变为 /index?arduino_inserted=1（无阻塞）
        2. 输入 student 账号登录（阻塞 1：登录）
        3. 落地 IDE，确认工作台可见（无额外阻塞）
        4. dispatch('arduino-device-removed') → lock overlay + save modal（阻塞 2：确认）
        5. 点确认保存 → toast vault_id → 专仓 Tab 打开 → 行出现（无额外阻塞）
    - 记录阻塞点数量：预期 = 2（登录 + 保存确认 Modal）。
    - 断言阻塞点 ≤ 3 → AC-8 ≥ 1 分 → PASS。
  tests:
    - 输出 walkthrough_blocking_points.json = {count: N, list:[...]}。

## ── Summary of AC Coverage ────────────────────────────────────────────
#
#  AC-1 ← T05
#  AC-2 ← T02, T03, T14, T16, T18-a
#  AC-3 ← T03, T18-b/c
#  AC-4 ← T06, T07, T08, T18-e
#  AC-5 ← T09, T10, T11, T18-d
#  AC-6 ← T00, T17
#  AC-7 ← T15, T19
#  AC-8 ← T12, T13, T16, T20
#
## End of tasks.md · v1.0
