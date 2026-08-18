# Arduino 设备插入自动跳转 + 重写路由 + 拔出锁定三重永久化 + AI/EigenFlux/专家介入
# — 原子任务清单 v2.0（10 条 AC → 31 条原子任务）
#
# 执行总顺序：
#   Phase 0  DB 基座      (T00a → T00b → T00c → T00d → T00e)
#   Phase 1  权限&路由     (T01a → T01b → T02a → T02b → T02c → T03a → T03b → T03c)
#   Phase 2  管理员设置页   (T04a → T04b → T04c)
#   Phase 3  前端全局热插拔 (T05a → T05b → T05c)
#   Phase 4  拔出锁定      (T06a → T06b → T06c → T07 → T08a → T08b)
#   Phase 5  专仓 commit   (T09a → T09b → T10a → T10b → T10c → T10d → T11a → T11b)
#   Phase 6  专仓 UI       (T12a → T12b → T13a → T13b → T14)
#   Phase 7  设置页模板    (T15a → T15b → T16)
#   Phase 8  AI 介入      (T21 → T22 → T23a → T23b → T24 → T25 → T26)
#   Phase 9  测试验证      (T17 → T18 → T19 → T20 → T27 → T28)
#
# 依赖声明：每任务 depends 字段显式列出前驱；DONE 写入 §14 flow session nodes。
# ============================================================================

## ── Phase 0：数据库基座（AC-6, AC-10） ──────────────────────────────────

- id: T00a
  title: 建表 mt_arduino_user_vault（用户专仓主表）
  ac_refs: [AC-6]
  depends: []
  files: [flask-app/engines/ai_arduino_detect_engine.py]
  spec:
    - ensure_detect_tables() 内：
        CREATE TABLE IF NOT EXISTS mt_arduino_user_vault (
          vault_id TEXT PRIMARY KEY,
          bound_user_id INTEGER NOT NULL,
          session_id TEXT,
          snapshot_version INTEGER NOT NULL DEFAULT 1,
          label TEXT DEFAULT '拔出自动保存',
          payload_json TEXT NOT NULL,
          acl_json TEXT NOT NULL DEFAULT '{"owner":0,"readers":[]}',
          size_bytes INTEGER NOT NULL DEFAULT 0,
          committed_at TEXT NOT NULL,
          json_backup_path TEXT,
          git_tag TEXT,
          git_commit_sha TEXT
        );
        CREATE INDEX IF NOT EXISTS idx_arduino_vault_user
            ON mt_arduino_user_vault(bound_user_id, committed_at DESC);
        CREATE INDEX IF NOT EXISTS idx_arduino_vault_created_at_desc
            ON mt_arduino_user_vault(committed_at DESC);
  tests:
    - sqlite_master 查询 name + index_list 断言表与 2 条索引存在。

- id: T00b
  title: 建表 mt_arduino_admin_settings（管理员设置 key-value 多版）
  ac_refs: [AC-6]
  depends: []
  files: [flask-app/engines/ai_arduino_detect_engine.py]
  spec:
    - CREATE TABLE IF NOT EXISTS mt_arduino_admin_settings (
        setting_version TEXT PRIMARY KEY,
        scope TEXT NOT NULL DEFAULT 'global',
        key_name TEXT NOT NULL,
        value_json TEXT NOT NULL,
        changed_by INTEGER NOT NULL,
        changed_at TEXT NOT NULL,
        active_flag INTEGER NOT NULL DEFAULT 1,
        ai_suggestion_ref TEXT
      );
    - CREATE INDEX IF NOT EXISTS idx_arduino_settings_active
          ON mt_arduino_admin_settings(key_name, active_flag DESC);
    - CREATE INDEX IF NOT EXISTS idx_arduino_settings_created_at_desc
          ON mt_arduino_admin_settings(changed_at DESC);
  tests: [PRAGMA index_list 断言 2 索引]

- id: T00c
  title: 建表 mt_arduino_lock_log（锁定/解锁审计）
  ac_refs: [AC-6]
  depends: []
  files: [flask-app/engines/ai_arduino_detect_engine.py]
  spec:
    - CREATE TABLE IF NOT EXISTS mt_arduino_lock_log (
        lock_id TEXT PRIMARY KEY,
        user_id INTEGER NOT NULL,
        session_id TEXT,
        lock_trigger TEXT NOT NULL,
        lock_reason TEXT,
        released_by TEXT,
        released_at TEXT,
        committed_vault_id TEXT,
        eigenflux_panel_ref TEXT
      );
    - CREATE INDEX IF NOT EXISTS idx_arduino_lock_user
          ON mt_arduino_lock_log(user_id, released_at DESC);
    - CREATE INDEX IF NOT EXISTS idx_arduino_lock_created_at_desc
          ON mt_arduino_lock_log(COALESCE(released_at, substr(lock_id,8,8)) DESC);
  tests: [PRAGMA 索引断言]

- id: T00d
  title: 建表 mt_arduino_ai_intervention_log（AI 介入审计）
  ac_refs: [AC-6, AC-9]
  depends: []
  files: [flask-app/engines/ai_arduino_detect_engine.py]
  spec:
    - CREATE TABLE IF NOT EXISTS mt_arduino_ai_intervention_log (
        intervention_id TEXT PRIMARY KEY,
        ai_group_type TEXT NOT NULL,
        ai_employee_id TEXT,
        action_type TEXT NOT NULL,
        action_detail TEXT,
        ai_confidence REAL DEFAULT 0,
        eigenflux_consensus REAL,
        expert_reviewer_list TEXT,
        created_at TEXT NOT NULL,
        applied_flag INTEGER NOT NULL DEFAULT 0
      );
    - CREATE INDEX IF NOT EXISTS idx_arduino_aiinter_group
          ON mt_arduino_ai_intervention_log(ai_group_type, created_at DESC);
  tests: [索引断言]

- id: T00e
  title: 建表 mt_arduino_route_override_log（重写路由建议审计）
  ac_refs: [AC-6, AC-9]
  depends: []
  files: [flask-app/engines/ai_arduino_detect_engine.py]
  spec:
    - CREATE TABLE IF NOT EXISTS mt_arduino_route_override_log (
        override_id TEXT PRIMARY KEY,
        user_role TEXT NOT NULL,
        source_path TEXT NOT NULL,
        rewritten_path TEXT NOT NULL,
        rule_reason TEXT,
        ai_agent_id TEXT,
        eigenflux_panel_ref TEXT,
        created_at TEXT NOT NULL
      );
    - CREATE INDEX IF NOT EXISTS idx_arduino_route_role_created
          ON mt_arduino_route_override_log(user_role, created_at DESC);
  tests: [索引断言]

## ── Phase 1：后端权限守卫 & 重写路由（AC-2, AC-3, AC-9） ───────────────

- id: T01a
  title: 扩展守卫函数 _check_arduino_api_permission 支持 scope=ide|setup|vault
  ac_refs: [AC-3, NFR-2]
  depends: [T00a, T00b, T00c, T00d, T00e]
  files: [flask-app/routes/arduino_session_routes.py]
  spec:
    - 原函数改为 _check_arduino_api_permission(scope='ide')：
        scope='ide'   → username == 'wuchenghao15' + 双密钥（不变）
        scope='setup' → role_canonical ∈ {super_admin, admin, hardware_admin}；
                        super_admin 双密钥；admin/hardware_admin 只需合法登录 session
        scope='vault' → 任意已登录用户（行级 ACL 由 DAO 负责）
    - 返回 (allowed, resp_or_None, role_canonical) 三元组。
  tests:
    - flask test client 4 角色 × 3 scope = 12 次请求，断言 HTTP 状态与响应体。

- id: T01b
  title: 新增 _ensure_device_present(bound_vid_pid)（后端写操作 fail-closed 通用守卫）
  ac_refs: [AC-4]
  depends: [T01a]
  files: [flask-app/routes/arduino_session_routes.py]
  spec:
    - 内部调用 engine.get_status()：
        connected=0 → return (False, 423 JSON {device_status:"removed", lock_id}, None)
        connected>0 且 bound_vid_pid 不在 connected_vid_pids → return (False, 409 JSON {...}, None)
        否则 → return (True, None, status)
  tests:
    - mock get_status() 三种返回 + 3 次写接口断言 423/409/200。

- id: T02a
  title: 新增 bind API：GET /api/arduino/session/bind（标记 arduino_bound session）
  ac_refs: [AC-1]
  depends: [T01a]
  files: [flask-app/routes/arduino_session_routes.py]
  spec:
    - 要求已登录；调 engine.get_status()；connected>0：
        session['arduino_bound'] = True
        session['bound_vid_pid'] = status.connected_vid_pids[0]
        session['bound_at'] = iso_now()
        → return {"bound": True, vid_pid, bound_at}
      else → return {"bound": False, reason: "device not found"}
  tests:
    - flask test client：login + bind → session dict 断言 3 字段存在。

- id: T02b
  title: 新增 redirect_target API：GET /api/arduino/session/redirect_target
  ac_refs: [AC-2, FR-2]
  depends: [T02a]
  files: [flask-app/routes/arduino_session_routes.py]
  spec:
    - 算法：
        if not session.get('arduino_bound') → return {'redirect': None}
        status = engine.get_status()
        if status.connected == 0 → return {'redirect': None, reason: 'removed'}
        role = get_current_role_canonical()
        if role ∈ admin-like → redirect = '/admin_app/arduino_admin_setup'
        else → redirect = '/admin_app/arduino_ide'
        → 写入 mt_arduino_route_override_log 一行记录决策
        → return {redirect, bound_vid_pid, role}
  tests:
    - 3 角色 × [bound=True/False] × [connected=0/>0] → 断言 redirect 值。

- id: T02c
  title: 修改 auth_routes.py /auth/login 重写路由 override
  ac_refs: [AC-2]
  depends: [T02a]
  files: [flask-app/routes/auth_routes.py]
  spec:
    - 写 session 后追加：
        is_bound = session.get('arduino_bound') or request_json.get('arduino_bound')
        if is_bound:
            status = ai_arduino_detect_engine.get_status()
            if status.connected > 0:
                if user.role_canonical in {super_admin, admin, hardware_admin}:
                    redirect = '/admin_app/arduino_admin_setup'
                else:
                    redirect = '/admin_app/arduino_ide'
                session['bound_vid_pid'] = status.connected_vid_pids[0]
                session['bound_at'] = iso_now()
    - 写 mt_arduino_route_override_log 审计行（rule_reason='login_rewrite'）。
  tests:
    - flask test client 3 角色 login 带 arduino_bound=1 + mock connected → 断言 redirect。

- id: T03a
  title: _arduino_sa_only_guard 角色分流：管理员 GET IDE → 302 SETUP
  ac_refs: [AC-3]
  depends: [T01a]
  files: [flask-app/routes/arduino_session_routes.py]
  spec:
    - 守卫命中 /admin_app/arduino_ide：
        role ∈ admin → 写 ARD_ROLE_REDIRECT_SETUP 审计（detect_log + route_override_log）
                        → return redirect('/admin_app/arduino_admin_setup', code=302)
  tests:
    - admin session GET IDE → 响应 302 且 Location 包含 arduino_admin_setup。

- id: T03b
  title: _arduino_sa_only_guard 普通用户：未 bound → 302 /index
  ac_refs: [AC-3]
  depends: [T03a]
  files: [flask-app/routes/arduino_session_routes.py]
  spec:
    - 守卫命中 /admin_app/arduino_ide，非管理员：
        若 not session.arduino_bound OR engine 未连接 → 302 /index
  tests:
    - student 无 bound → GET IDE → 302 /index。

- id: T03c
  title: 新增路由 GET /admin_app/arduino_admin_setup 渲染设置页模板
  ac_refs: [AC-3, FR-3]
  depends: [T03b]
  files: [flask-app/routes/arduino_session_routes.py]
  spec:
    - @arduino_bp.route('/admin_app/arduino_admin_setup')
      scope='setup' 守卫通过后，load_active_settings_dict() 注入模板。
    - 模板渲染：render_template('admin_app/arduino_admin_setup.html',
                                 page_type='form', settings_dict=...)
  tests:
    - admin session GET → 200 + 响应体含「Arduino 管理员录入设置」文案。

## ── Phase 2：管理员设置页 CRUD（FR-3） ─────────────────────────────────

- id: T04a
  title: DAO save_admin_setting + load_active_settings_dict
  ac_refs: [FR-3]
  depends: [T00b]
  files: [flask-app/engines/ai_arduino_detect_engine.py]
  spec:
    - save_admin_setting(key_name, value_json, changed_by, ai_suggestion_ref=None)
        → UPDATE 旧行 active_flag=0 WHERE key_name=? AND active_flag=1
        → INSERT 新 setting_version（ARD-SET-<ts>-<uuid>）
    - load_active_settings_dict()
        → SELECT key_name, value_json WHERE active_flag=1
        → 返回 {key: parsed_value_dict}
  tests:
    - save 3 次不同 key → load → 3 key dict 断言 + version 递增。

- id: T04b
  title: GET /api/arduino/admin/setup → 返回当前激活设置字典
  ac_refs: [FR-3]
  depends: [T04a, T03c]
  files: [flask-app/routes/arduino_session_routes.py]
  spec:
    - scope='setup' 守卫通过 → return jsonify(load_active_settings_dict())
  tests:
    - admin login → GET → 响应体含 10 个顶层键（board_whitelist / toolchain_path / ...）。

- id: T04c
  title: POST /api/arduino/admin/setup → 批量保存设置（设备拔出 423）
  ac_refs: [FR-3, AC-4]
  depends: [T04b, T01b]
  files: [flask-app/routes/arduino_session_routes.py]
  spec:
    - 首行调 _ensure_device_present；参数为 10 键 body；
      逐 key 调 save_admin_setting；返回 {saved_keys:[...], latest_version}。
  tests:
    - admin + connected → POST 3 键 → saved_keys 3。
    - admin + removed → 423 LOCKED。

## ── Phase 3：前端全局热插拔（FR-1, AC-1） ──────────────────────────────

- id: T05a
  title: 新建 arduino_global_hotplug.js（全局 2s 轮询 + insert 双轮确认跳转）
  ac_refs: [AC-1, FR-1]
  depends: [T02a, T02b]
  files:
    - flask-app/static/js/arduino_global_hotplug.js (NEW)
  spec:
    - 常量：POLL_MS=2000, EXCLUDE_PATHS=[/admin_app/arduino_ide$, /admin_app/arduino_admin_setup$]
    - ARDUINO_GLOBAL.pendingInsert = false
    - pollOnce():
        fetch /api/arduino/events/poll?global=1 → 解析 events[]
        命中 insert 且不在 EXCLUDE_PATHS：
          if pendingInsert === true → 第二轮确认，执行跳转
          else pendingInsert = true → 下一轮验证
        命中 remove：
          pendingInsert = false
          localStorage.removeItem('ARDUINO_BOUND_VIDPID')
          if 当前页为 IDE/SETUP → dispatchEvent(new CustomEvent('arduino-device-removed', {...}))
        其他事件 → pendingInsert = false
    - doInsertJump(vid_pid, model):
        if notLoggedIn → location = `/index?arduino_inserted=1&vid_pid=${vid}&model=${m}`
                         localStorage.ARDUINO_BOUND_VIDPID = vid_pid
        else loggedIn:
          fetch('/api/arduino/session/bind')
            .then(r=>r.json()).then(d=>{
              if (d.bound)
                fetch('/api/arduino/session/redirect_target')
                  .then(rd=>rd.json()).then(rd=>{ if(rd.redirect) location=rd.redirect })
            })
  tests:
    - 静态文件 grep：assert 无 style= 字符串、无 "--[a-z]" 裸 BEM 类。

- id: T05b
  title: 在 admin_app/base.html 注入 arduino_global_hotplug.js
  ac_refs: [AC-1]
  depends: [T05a]
  files: [flask-app/templates/admin_app/base.html]
  spec:
    - </body> 前一行插入：
        <script src="{{ url_for('static', filename='js/arduino_global_hotplug.js') }}" defer></script>
  tests:
    - Playwright: 访问 /admin → 断言 <script src=...arduino_global_hotplug.js> 存在。

- id: T05c
  title: 在 index.html 注入 arduino_global_hotplug.js（未登录态）
  ac_refs: [AC-1]
  depends: [T05a]
  files: [flask-app/templates/index.html]
  spec:
    - 同 T05b；确保 defer 且在其他业务 script 之后。
  tests:
    - Playwright: 访问 /index → 断言 script 标签存在；localStorage mock poll 后 URL 变更。

## ── Phase 4：拔出锁定 fail-closed（FR-4, AC-4） ───────────────────────

- id: T06a
  title: arduino_ide.html：arduino-device-removed 监听 + 生成 lock_id
  ac_refs: [AC-4]
  depends: [T05a]
  files: [flask-app/templates/admin_app/arduino_ide.html]
  spec:
    - 插入 window.addEventListener('arduino-device-removed', (e)=>{
        const lockId = 'ARD-LCK-' + crypto.randomUUID().slice(0,8);
        // 写入 lock_trigger = e.detail.reason || 'device_removed'
        lockOverlayShow(lockId, e.detail || {});
      });
    - lockOverlayShow 入口函数：
        1. 停止 autosave 计时器
        2. compile/upload 相关按钮 disabled = true
        3. 追加全屏 div → 显示遮罩 + 三按钮 Modal
  tests:
    - Playwright: 页加载 → dispatch 事件 → 500ms 内遮罩 DOM 存在。

- id: T06b
  title: ide 锁定遮罩 CSS 类族（复用 mtscos-dialog）
  ac_refs: [NFR-4, AC-4]
  depends: [T06a]
  files: [flask-app/static/css/mtscos_pages.css §12]
  spec:
    - .mtscos-ide-page .arduino-lock-overlay--visible
        { position:fixed; inset:0; background:var(--adp-overlay-bg, rgba(0,0,0,.72));
          display:flex; align-items:center; justify-content:center; z-index:9999 }
    - .mtscos-ide-page .arduino-lock-modal
        @extend 规则复用 mtscos-dialog（宽度/圆角/阴影）
  tests:
    - CSS 语法校验 + grep 断言没有 BEM -- 裸类。

- id: T06c
  title: ide 三按钮 Modal 动作回调（commit / 放弃 / 重新插入）
  ac_refs: [AC-4, FR-4]
  depends: [T06b]
  files: [flask-app/templates/admin_app/arduino_ide.html]
  spec:
    - 确认保存并写入专仓 → commitToVault({confirm_reason:'device_removed', lock_id})
    - 放弃 → fetch POST /api/arduino/lock/release（released_by='discard'）
              + location = '/index'
    - 我已重新插入 → fetch GET /api/arduino/events/repoll_now
                      → connected && vid_pid match → hideOverlay + 恢复按钮
                      → toast 仍未检测到匹配设备
  tests:
    - mock fetch 返回 → 3 种点击断言 location / toast / 遮罩显隐。

- id: T07
  title: arduino_admin_setup.html：拔出锁定（与 ide 对称，放弃跳 /admin）
  ac_refs: [AC-4]
  depends: [T06a, T06b, T06c]
  files: [flask-app/templates/admin_app/arduino_admin_setup.html]
  spec:
    - 同 T06a 结构；放弃按钮跳 /admin；确认保存按钮调 POST /api/arduino/admin/setup（保存当前表单）后隐藏遮罩。
  tests:
    - 与 T06a 对称。

- id: T08a
  title: 后端 4 个写接口挂 _ensure_device_present（save/save_vault/setup/compile_upload）
  ac_refs: [AC-4]
  depends: [T01b, T04c]
  files: [flask-app/routes/arduino_session_routes.py]
  spec:
    - POST /api/arduino/session/save
    - POST /api/arduino/session/commit （例外：reason=device_removed 时跳过设备检查）
    - POST /api/arduino/admin/setup
    - POST /api/arduino/session/compile_upload
  tests:
    - mock removed → 4 POST → 断言 status=423（commit 例外走 200）。

- id: T08b
  title: 新增 GET /api/arduino/events/repoll_now + 新增 POST /api/arduino/lock/release
  ac_refs: [FR-4]
  depends: [T08a]
  files: [flask-app/routes/arduino_session_routes.py]
  spec:
    - /events/repoll_now → engine.scan_devices() 同步扫一次 → return engine.get_status()
    - /lock/release（POST body: {lock_id, released_by}）
        → UPDATE mt_arduino_lock_log SET released_by=?, released_at=? WHERE lock_id=?
  tests:
    - 两个接口单独 flask test client 断言返回字段。

## ── Phase 5：变异采集 + 专仓 commit 三重永久化（FR-5, AC-5） ──────────

- id: T09a
  title: IDE 页 VARIANT_ACTIONS / VARIANT_PARAMS 双对象采集
  ac_refs: [FR-5]
  depends: [T06a]
  files: [flask-app/templates/admin_app/arduino_ide.html]
  spec:
    - 初始化：window.VARIANT_ACTIONS = []; window.VARIANT_PARAMS = {}
    - 事件钩子：
        onCompile → push {ts, type:'compile', detail: {flags, board}}
        onUpload  → push {ts, type:'upload',  detail: {port, speed, board}}
        onChangeBoard → VARIANT_PARAMS.board = ...
        onChangePort  → VARIANT_PARAMS.port  = ...
        onChangeBaud  → VARIANT_PARAMS.baud  = ...
        onLibToggle    → VARIANT_PARAMS.libs = [...libs]
        onSave        → push {ts, type:'save', detail: {size_bytes}}
  tests:
    - Playwright: 依次触发 onCompile + onUpload + onChangeBoard
                → VARIANT_ACTIONS.length≥2, VARIANT_PARAMS.board 非空。

- id: T09b
  title: 设置页 VARIANT_PARAMS 表单实时采集
  ac_refs: [FR-5]
  depends: [T07]
  files: [flask-app/templates/admin_app/arduino_admin_setup.html]
  spec:
    - form 每一个 input/textarea/select oninput 都把键值同步到 window.VARIANT_PARAMS。
  tests:
    - Playwright: 填入 5 个字段 → VARIANT_PARAMS 5 键值全匹配。

- id: T10a
  title: 引擎 DAO commit_to_user_vault（含 sqlite 行 + 物理 JSON 备份）
  ac_refs: [AC-5]
  depends: [T00a]
  files: [flask-app/engines/ai_arduino_detect_engine.py]
  spec:
    - 生成 vault_id = f"ARD-VLT-{sha1(str(user_id)).hexdigest()[:8]}-{uuid8()}"
    - payload = {code_content, variant_actions, variant_params,
                 usage_trace, edit_history, device_snapshot: get_status()}
    - 写入 mt_arduino_user_vault 行；size_bytes = len(payload_json.encode('utf-8'))
    - 写物理 JSON：
        dir = f"_runtime/arduino_vault/{user_id}" → mkdir -p
        path = f"{dir}/{vault_id}.json"
        with open(path, 'w', encoding='utf-8') as f: f.write(payload_json)
    - 返回 vault_row + json_backup_path
  tests:
    - python 单元：调 DAO → SELECT vault + 读 JSON 文件断言匹配。

- id: T10b
  title: 引擎 Git 仓归档 _git_tag_vault(vault_id, username, json_path)
  ac_refs: [AC-5]
  depends: [T10a]
  files: [flask-app/engines/ai_arduino_detect_engine.py]
  spec:
    - repo_dir = '_runtime/arduino_vault_repo'
    - 首次：os.system(f'git init {repo_dir}') → 写 .gitignore 忽略临时文件
    - 复制 json_path → {repo_dir}/users/{uid}/{vault_id}.json
    - 在 repo_dir 执行：git add → git commit -m "vault: <vault_id> by <username>"
                      → git tag "vault/<vault_id>"
    - 失败异常捕获 → 返回 ('FAILED_DEGRADED', None)；成功 → (tag, commit_sha)
  tests:
    - 调 1 次后 git tag 查 tag 存在；或 git 不存在时返回 FAILED_DEGRADED。

- id: T10c
  title: 更新 mt_arduino_user_sessions 会话行（variant_* + committed + lock_ref）
  ac_refs: [FR-5]
  depends: [T10a]
  files: [flask-app/engines/ai_arduino_detect_engine.py]
  spec:
    - UPDATE mt_arduino_user_sessions SET
        variant_actions_json = ?, variant_params_json = ?,
        locked_reason = ?, committed = 1, committed_at = ?,
        vault_id = ?
      WHERE session_id = ?
  tests:
    - 提交后 SELECT sessions → committed == 1。

- id: T10d
  title: 新增 API POST /api/arduino/session/commit（挂接三重永久化）
  ac_refs: [AC-5]
  depends: [T01b, T10b, T10c]
  files: [flask-app/routes/arduino_session_routes.py]
  spec:
    - body：{session_id, code_content, variant_actions_json, variant_params_json,
             confirm_reason, pin_reinserted_if_any, lock_id}
    - 若 confirm_reason != 'device_removed' → 走 _ensure_device_present
    - 顺序执行：
        1) 校验 session 存在且属于 current_user
        2) T10c UPDATE sessions
        3) T10a commit_to_user_vault → 行 + json_path
        4) T10b _git_tag_vault → (tag, sha)
        5) UPDATE mt_arduino_user_vault SET git_tag=?, git_commit_sha=?, json_backup_path=?
        6) UPDATE mt_arduino_lock_log SET committed_vault_id=?, released_by='commit'
    - 返回 200 {vault_id, snapshot_version, size_bytes, committed_at, json_backup_path, git_tag}
  tests:
    - student commit → SELECT vault + 文件存在 + git tag（或降级）。

- id: T11a
  title: 引擎 DAO list_user_vault（本人 / SA as_user 过滤）
  ac_refs: [AC-5]
  depends: [T10a]
  files: [flask-app/engines/ai_arduino_detect_engine.py]
  spec:
    - WHERE bound_user_id = (as_user if (is_sa and as_user) else user_id)
    - ORDER committed_at DESC LIMIT size OFFSET (page-1)*size
  tests:
    - user1 与 user2 各 2 行 → user1 list → 2 行；SA as_user=2 → 2 行。

- id: T11b
  title: 路由 GET /api/arduino/vault/list + GET /api/arduino/vault/<vault_id>
  ac_refs: [AC-5, NFR-2]
  depends: [T11a]
  files: [flask-app/routes/arduino_session_routes.py]
  spec:
    - scope='vault' 守卫
    - get_vault_by_id 行级检查：非 SA 且 row.bound_user_id != session.user_id → 403
  tests:
    - user2 list/get user1 的 vault → 403。

## ── Phase 6：用户专仓 UI + 重写路由前端保险（FR-6, AC-2, AC-8） ───────

- id: T12a
  title: IDE 左侧「用户专仓」Tab 列表渲染
  ac_refs: [FR-6, AC-8]
  depends: [T11b]
  files: [flask-app/templates/admin_app/arduino_ide.html]
  spec:
    - Tab 按钮与 Tab Panel 使用 mtscos-underline-tabs 家族（mtscos_pages.css 已提供）
    - 激活：fetch /api/arduino/vault/list?size=10
      → 渲染卡片（vault_id 尾 6 位 + committed_at + label + size_kb）
  tests:
    - Playwright: 点 Tab → 列表项 ≤ 10。

- id: T12b
  title: 专仓条目点击 → 确认对话框 → 载入代码 + 回填板卡端口参数
  ac_refs: [FR-6]
  depends: [T12a]
  files: [flask-app/templates/admin_app/arduino_ide.html]
  spec:
    - confirm「载入此专仓快照？当前未保存代码将被覆盖」
    - 确认 → fetch GET /api/arduino/vault/<id> → payload = JSON.parse(row.payload_json)
        editor.setValue(payload.code_content)
        boardSelector.value = payload.variant_params.board ?? ''
        portSelector.value  = payload.variant_params.port  ?? ''
        baudSelector.value  = payload.variant_params.baud  ?? ''
  tests:
    - 点行 → 选确认 → editor 文本变更 + select 选择器变值。

- id: T13a
  title: 新增 DAO + API：GET /api/arduino/admin/vault_usage（管理员配额 Tab）
  ac_refs: [FR-6]
  depends: [T11a, T04b]
  files:
    - flask-app/engines/ai_arduino_detect_engine.py
    - flask-app/routes/arduino_session_routes.py
  spec:
    - GROUP BY bound_user_id → COUNT(*) commit_count, SUM(size_bytes) total_bytes,
      MAX(committed_at) last_commit_at
    - JOIN users 拿 username；对比 settings.vault_quota_mb → over_quota=total_mb > quota
  tests:
    - 造 3 组用户数据 → 返回 3 行，每行含 5 字段。

- id: T13b
  title: 设置页「全局设置 / 专仓配额」双 Tab 模板
  ac_refs: [FR-6]
  depends: [T13a, T07]
  files: [flask-app/templates/admin_app/arduino_admin_setup.html]
  spec:
    - 两个 Tab：全局设置（表单） + 专仓配额（mtscos-table-wrapper 表格）
    - 配额表格列：用户名 / 已用 MB / 提交数 / 最近提交 / 超限状态
    - over_quota 行 → tr class=is-danger-row（mtscos_pages.css 加色）
  tests:
    - Playwright: 点 Tab 切换 → 表格出现且行数正确；超限行红底。

- id: T14
  title: 登录落地后 localStorage 双保险重写路由校验
  ac_refs: [AC-2]
  depends: [T05c, T02b]
  files: [flask-app/templates/index.html]
  spec:
    - 登录 submit 成功 → 落地页 window.onload 追加：
        if (localStorage.ARDUINO_BOUND_VIDPID) {
          fetch('/api/arduino/session/redirect_target', {credentials:'include'})
            .then(r=>r.json()).then(d=>{
              if (d.redirect && location.pathname !== new URL(d.redirect,location).pathname)
                location.replace(d.redirect);
            });
        }
  tests:
    - Playwright: login + 设置 localStorage → 断言最终 URL pathname 为 IDE 或 SETUP。

## ── Phase 7：设置页模板 FORM 类型 + 头部角色回显（AC-7, AC-2） ────────

- id: T15a
  title: arduino_admin_setup.html 骨架（extends base + page_type=form + action bar）
  ac_refs: [AC-7]
  depends: [T03c]
  files: [flask-app/templates/admin_app/arduino_admin_setup.html]
  spec:
    - {% extends 'admin_app/base.html' %}
      {% set page_type = 'form' %}
      {% block content %}
        <div class="mtscos-action-bar adp-slide-up">
          <div class="mtscos-action-bar-title">⚙️ Arduino 管理员录入设置
            <span class="mtscos-action-bar-subtitle">板卡白名单 · 编译链 · 端口 · 专仓配额 · 变异模板 · 自动保存</span>
          </div>
          <div class="mtscos-action-bar-actions">
            <button class="mtscos-btn is-secondary is-sm" data-role="sa-only" ...>切换 IDE</button>
            <button class="mtscos-btn is-primary is-sm" id="btn-save-setup">保存设置</button>
          </div>
        </div>
        <!-- 双 Tab 容器 + form + table -->
      {% endblock %}
    - 零内联 style；data-role=sa-only 在非 SA 时由 base.html 自动 display:none。
  tests:
    - 千轮子集 V2/V3：0 违规。

- id: T15b
  title: mtscos_pages.css §13 arduino-setup 族（最小作用域限定 FORM page_type）
  ac_refs: [AC-7, NFR-4]
  depends: [T15a]
  files: [flask-app/static/css/mtscos_pages.css]
  spec:
    - 作用域：
        .mtscos-content[data-page-type="form"] .arduino-setup-tabs {...}
        .mtscos-content[data-page-type="form"] .arduino-setup-form .mtscos-form-group {...}
        .mtscos-content[data-page-type="form"] .arduino-quota-table .is-danger-row { background:var(--mtscos-danger-bg, #fff1f0); }
  tests:
    - CSS 语法校验；无 BEM -- 裸类。

- id: T16
  title: IDE / SETUP 头部角色 + 设备绑定状态 chip 标签
  ac_refs: [AC-2, AC-8]
  depends: [T12b, T13b]
  files:
    - flask-app/templates/admin_app/arduino_ide.html
    - flask-app/templates/admin_app/arduino_admin_setup.html
  spec:
    - IDE 页 action bar 右侧追加：
        <span class="mtscos-underline-chip" id="device-status-chip">🔌 设备检测中…</span>
        JS poll 后 chip.innerText = 已绑定 {model} {vid_pid} / 未检测到设备
    - SETUP 页追加：
        <span class="mtscos-underline-chip" id="role-chip">管理员录入模式</span>
        <span class="mtscos-underline-chip" id="device-status-chip">🔌 设备检测中…</span>
  tests:
    - Playwright: 插/拔模拟 → 标签文本变更。

## ── Phase 8：AI 员工 & EigenFlux 5 人磋商 & 专家团队介入（FR-8, AC-9） ──

- id: T21
  title: 注册 11 名 Arduino 专项 AI 员工进 ai_employees（5 工种）
  ac_refs: [AC-9]
  depends: [T00d]
  files: [flask-app/engines/ai_arduino_intervention_engine.py (NEW)]
  spec:
    - 新建 ai_arduino_intervention_engine.py，函数 ensure_ai_arduino_workers_registered():
        工种与名额：
          arduino_route_permissions_specialist × 3  （T1 路由权限）
          arduino_uiux_specialist                 × 2  （T2 UI/UX）
          arduino_hotplug_watcher                 × 2  （T3 热插拔深度守护）
          arduino_api_contract_specialist         × 2  （T4 API 契约）
          arduino_db_model_specialist             × 2  （T5 用户绑定 & DB）
        - 注册前查 ai_employees 表是否已存在同名 specialization + 同状态
          不足则 INSERT（调用 ai_auto_hire_engine 相同注册逻辑）
        - 注册成功后写 eigenflux_registrations → EigenFlux 平台可见
  tests:
    - 调函数后 SELECT ai_employees WHERE specialization IN (...) → 数量 11。

- id: T22
  title: EigenFlux 5 人磋商接口 dispatch_eigenflux_5panel(topic, proposal)
  ac_refs: [AC-9]
  depends: [T21]
  files: [flask-app/engines/ai_arduino_intervention_engine.py]
  spec:
    - 5 领域专家固定列表 = ['架构','安全','DBA','IoT','前端']，从 eigenflux_registrations 随机/按权重挑选。
    - 模拟投票：每位专家返回同意/反对 + 置信度；consensus = 赞成/5。
    - 写入 mt_arduino_ai_intervention_log.eigenflux_consensus + expert_reviewer_list=JSON
    - 返回 {consensus, votes: [...], panel_ref}
  tests:
    - 调用 10 次 → 断言 panel_ref 非空 + 专家列表 5 人齐全无重复。

- id: T23a
  title: T1 路由权限组：异常率扫描触发器
  ac_refs: [AC-9, FR-8]
  depends: [T22]
  files: [flask-app/engines/ai_arduino_intervention_engine.py]
  spec:
    - 函数 t1_scan_route_anomalies()：
        - 统计 mt_arduino_route_override_log 近 30 分钟：
          · redirect 异常率 > 5% 或 同一角色 20 次命中不同 rewritten_path
          → 生成建议：角色-路径-设备绑定白名单 JSON
          → 派 T22 dispatch_eigenflux_5panel → 写入 intervention_log
          → ≥4/5 或 3/5 后 SA 手动 applied → 生效
  tests:
    - 注入 30 条 423 + route_override 日志 → t1_scan 后 intervention_log 至少 1 行 t1。

- id: T23b
  title: 在所有 _ensure_device_present 失败时累计阈值回调
  ac_refs: [AC-9]
  depends: [T23a, T01b]
  files: [flask-app/routes/arduino_session_routes.py]
  spec:
    - _ensure_device_present 返回 False 时，本地 cache 累加失败计数；
      每累计 30 次 → 后台线程异步调 t1_scan_route_anomalies()
  tests:
    - mock 30 次失败 → intervention_log 出现 t1 新行。

- id: T24
  title: T2 UI/UX 组：discard 比例 > 20% → 文案优化建议
  ac_refs: [FR-8]
  depends: [T22]
  files: [flask-app/engines/ai_arduino_intervention_engine.py]
  spec:
    - t2_scan_discard_ratio()：mt_arduino_lock_log 最近 7 天 released_by='discard' / total > 20%
      → 生成文案建议（Modal 标题 / 副标题 / 按钮 label）+ 派 EigenFlux 前端专家 1 人 review
      → ≥4/5 通过 → 自动 patch arduino_ide.html 的 Modal 文案文本节点
  tests:
    - 注入 100 条 lock_log 其中 25 discard → 触发文案建议。

- id: T25
  title: T3 热插拔深度守护（独立 30s 循环）
  ac_refs: [FR-8]
  depends: [T22]
  files: [flask-app/engines/ai_arduino_intervention_engine.py]
  spec:
    - t3_deep_hotplug_watch(): 三重扫（ls /dev/cu.*, system_profiler SPUSBDataType, ioreg -p IOUSB）
      - 识别率异常（VID:PID 未在已知表 but dev 存在）→ 写 mt_ai_auto_hire_log 工单
        + 派 EigenFlux IoT 专家会诊（panel_ref）+ 干预日志 t3
  tests:
    - mock ioreg 注入未知 VID:PID → 工单与干预日志各 1 行。

- id: T26
  title: T4 API 契约完善 + T5 DB 建模审查
  ac_refs: [FR-8, AC-10]
  depends: [T22]
  files: [flask-app/engines/ai_arduino_intervention_engine.py]
  spec:
    - t4_api_contract_audit():
        · 扫描 /api/arduino/* 5xx / 4xx 异常率 >5%
        · 自动追加 Pydantic 式校验（参数必填、类型范围）
        · 汇总 OpenAPI JSON → 保存 _runtime/arduino_api_contract.json
    - t5_db_model_audit():
        · 同一 user_id 短时间重复 commit ≥ 3 次 → 跨用户隔离审计
        · 建议加索引/加字段 → EigenFlux DBA 专家 1 人 review → ≥4/5
          → 自动执行 ALTER TABLE（PRAGMA 表结构备份先行）
        · 验证 bound_user_id ↔ users.id FK 一致性断言写入 mt_arduino_ai_intervention_log
  tests:
    - 造数据：commit 5 次冲突 → t5 触发；FK 一致写入 applied_flag=1。

## ── Phase 9：测试验证（AC-1~AC-10 全部覆盖） ──────────────────────────

- id: T17
  title: AC-6 / AC-10 建表 + 索引自动测试脚本
  ac_refs: [AC-6, AC-10]
  depends: [T00a, T00b, T00c, T00d, T00e]
  files: [flask-app/_tests/test_arduino_tables_auto.py (NEW)]
  spec:
    - 删 5 表 → import 引擎 → get_status() → SELECT 5 表名齐全
    - 索引总数 ≥ 6；每个表至少 1 条 created_at 索引。
  tests:
    - python3 运行 → PASS/FAIL 写入 _runtime/test_report/arduino_ac6.json。

- id: T18
  title: 后端 9 条断言（AC-2 / AC-3 / AC-4 / AC-5）
  ac_refs: [AC-2, AC-3, AC-4, AC-5]
  depends: [T10d, T11b]
  files: [flask-app/_tests/test_arduino_backend_ac.py (NEW)]
  spec:
    1) student login arduino_bound → redirect=IDE
    2) admin   login arduino_bound → redirect=SETUP
    3) SA      login arduino_bound → redirect=SETUP
    4) admin   GET /admin_app/arduino_ide → 302 → SETUP
    5) student bound+connected GET IDE → 200 含 mtscos-canvas-stage
    6) commit vault → SELECT bound_user_id==uid 且 size_bytes>0
    7) 跨用户 list vault → 0 行交叉
    8) remove → POST save → 423
    9) conflict bound_vid → POST save → 409
  tests:
    - 9/9 PASS → 报告 arduino_backend.json。

- id: T19
  title: AC-7 千轮子集 V1~V4 扫 2 个页面
  ac_refs: [AC-7]
  depends: [T15a, T15b, T16]
  files: [使用既有 §14_scan.py]
  spec:
    - 目标：admin_app/arduino_admin_setup.html + admin_app/arduino_ide.html
    - 维度：V1 未定义类引用（0 或 ≤白名单）/ V2 内联 style=（≤1 且为进度条）
          / V3 BEM -- 裸类（0）/ V4 绕过标记（0）
  tests:
    - 4 维度各 ≤ 1 → 总分 ≥ 4 → PASS；报告 arduino_ac7.json。

- id: T20
  title: AC-1 Playwright /index 插入→跳转
  ac_refs: [AC-1]
  depends: [T05a, T05b, T05c]
  files: [flask-app/_tests/test_arduino_e2e_ac1.py (NEW)]
  spec:
    - 访问 /index → poll mock 注入 insert 事件 ×2 次 → 3s 内
      断言 URL 含 arduino_inserted=1 且 localStorage.ARDUINO_BOUND_VIDPID 非空。
  tests:
    - Playwright 执行 → 记录 timing。

- id: T27
  title: AC-9 AI 介入注册 + 触发 + EigenFlux 5 专家
  ac_refs: [AC-9]
  depends: [T23b, T24, T25, T26]
  files: [flask-app/_tests/test_arduino_ai_intervention_ac9.py (NEW)]
  spec:
    1) ensure_ai_arduino_workers_registered() → ai_employees 5 工种齐全 ≥ 11 行。
    2) 模拟 30 次 423/409 → intervention_log t1 行 + eigenflux_consensus 0~1。
    3) route_override_log 新增 1 行建议。
    4) dispatch_eigenflux_5panel 专家 5 领域齐全无重复。
  tests:
    - 4 子项全部 True → AC-9 PASS。

- id: T28
  title: AC-10 用户 FK 绑定 + 索引扫描
  ac_refs: [AC-10]
  depends: [T17, T27]
  files: [flask-app/_tests/test_arduino_db_user_binding_ac10.py (NEW)]
  spec:
    - commit 3 次不同用户 → 取 vault 行 → SELECT users WHERE id=bound_user_id
      → 3 行全部命中且 username 匹配。
    - 5 张表 idx 扫描 → 每张都有 created_at 索引。
  tests:
    - 3/3 FK OK + 5/5 索引 → PASS。

## ── AC → Task 映射总表 ────────────────────────────────────────────────
#
#  AC-1  跨页面插入→首页跳转       ← T02a T02b T05a T05b T05c T20
#  AC-2  登录重写路由分流          ← T02c T03c T14 T16 T18(1,2,3)
#  AC-3  管理员 IDE→SETUP 失效     ← T01a T03a T03b T03c T18(4,5)
#  AC-4  拔出锁定 fail-closed     ← T01b T06a T06b T06c T07 T08a T08b T18(8,9)
#  AC-5  三重永久化+用户专仓       ← T09a T09b T10a T10b T10c T10d T11a T11b T18(6,7)
#  AC-6  5 表自动建表+索引         ← T00a T00b T00c T00d T00e T17
#  AC-7  前端 V1~V4 质量          ← T15a T15b T16 T19
#  AC-8  体验阻塞点               ← T12a T12b T13a T13b T16 T20 (walkthrough)
#  AC-9  AI 员工+EigenFlux+专家   ← T21 T22 T23a T23b T24 T25 T26 T27
#  AC-10 用户 DB 深度绑定+索引     ← T00a T00b T00c T00d T00e T26 T28
#
## End of tasks_v2.md v2.0
