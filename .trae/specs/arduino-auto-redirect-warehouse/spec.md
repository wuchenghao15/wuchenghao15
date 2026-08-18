# Arduino 设备插入自动跳转 + 登录重写路由 + 拔出锁定永久保存 + 管理员录入设置页 + AI/EigenFlux/专家智能介入  (v2.0)

# — Product Requirements / Acceptance Criteria Spec

## Overview

- **Summary**：一旦 Arduino 硬件被系统检测到，前端全局轮询将用户重定向到 `/index`（首页）；完成登录后，系统基于「登录时 Arduino 是否仍保持插入」做**重写路由**判定：普通用户直接跳 `/admin_app/arduino_ide`；管理员（wuchenghao15=super\_admin 以及 admin 级角色）不走 IDE，而是走 Arduino 专用「录入管理员设置」页面 `/admin_app/arduino_admin_setup`（特殊路由规则 — 原 IDE 路由对管理员失效）。设备在从「插入 → 首页 → 登录 → IDE/设置」全程必须保持插入；若任何阶段被拔出，则立即「暂停并锁定界面 + 保存未保存操作/参数提示」。一旦用户点击「确认保存」，系统需要把该次会话中产生的「Arduino 变异动作和参数」**三重永久化**（SQLite 用户专仓行 + 物理 JSON 备份 + Git 仓版本控制），并绑定到用户专有 Arduino 操作仓（`mt_arduino_user_vault`）。

- **AI/EigenFlux/专家智能介入（新增 v2.0）**：AI 员工动态雇佣 + EigenFlux 5 人磋商 + EigenFlux 专家团队介入——必要性新建 AI 员工自动智能调整重写路由逻辑、权限管理白名单、UI/UX 文案与布局复写；独立角色负责 Arduino 设备热插拔实时监测守护；独立角色承担 API 功能完善与回归测试；独立角色承担用户信息深度绑定与数据库建模审查。

- **Purpose**：把现有 §13 规则零散的「插入弹窗 / 临时登录 / 拔出保存」组合，升级为一条**设备驱动 + AI 辅助的端到端闭环链路**，保证：硬件插/拔 → 路由强约束（管理员不进 IDE、普通用户不进设置页）→ 设备拔出即冻结 → 保存即三重永久化 → 用户专属操作仓可回溯 → AI 巡检异常自动派单修复。

- **Target Users**：

  - 普通登录用户（role ∈ {student, teacher, parent, adult\_student, user}）：Arduino 插入 + 登录 → IDE 编程页。

  - 管理员（`role_canonical ∈ {super_admin, admin, hardware_admin}`）：Arduino 插入 + 登录 → **设置页**（板卡注册/端口白名单/编译链路径/用户专仓配额/变异动作模板管理）。

  - 未登录访客：Arduino 插入 → 重定向 `/index` 并触发登录入口；保持设备插入直到登录完成。

- **Notable Design Decisions**（记录在此以避免后续返工）：

  1. **双路由形态**：同一 URL `/admin_app/arduino_ide` 对管理员返回 302 到 `/admin_app/arduino_admin_setup`，对普通用户返回 IDE 模板。即「管理员特殊路由规则生效」= 管理员访问 IDE 路由被静默拦截改派。
  2. **全程设备绑定语义**：`arduino_bound=1` 写入 session，表示「本次登录流是 Arduino 插入驱动、后续必须保持设备在线」。该 session 字段为整个链路的唯一凭证。
  3. **设备拔出锁定 = fail-closed**：一旦 poll 到 remove 事件，**立即**用全屏遮罩冻结 IDE/设置页（停止所有编译/上传/写入设置表单的提交），并展示三按钮 Modal：确认保存 / 放弃 / 我已重新插入设备（关闭锁定）。
  4. **变异动作和参数永久化**：不只是「代码保存」，还捕获所有会导致硬件输出差异的要素（板卡/端口/波特率/库引用/编译标志/上传速度/变异宏定义/自定义接线 JSON/串口监视器输出采样率等），统一打包为 `variant_actions_json` + `variant_params_json`。
  5. **用户专仓三重永久化**：SQLite 行 `mt_arduino_user_vault` + 物理 JSON（`_runtime/arduino_vault/<uid>/<vault_id>.json`）+ Git 仓版本控制（`_runtime/arduino_vault_repo` 自动 commit + tag `vault/<vault_id>`）。vault 与 `mt_arduino_user_sessions` 解耦；sessions 是"一次工作"，vault 是"永久归档 + 版本追溯 + 标签 + ACL（仅用户本人 + SA 可看）"。
  6. **登录重写路由**：`/auth/login` 返回 JSON 的 `redirect` 字段对「刚完成 login + session.arduino\_bound=1」的用户覆盖默认 `/admin` 或 `/student_portal`，改为「角色判断 → IDE 或 设置」。所有文档、代码注释、日志统一使用「重写路由」术语。
  7. **AI 员工 & EigenFlux 5 人磋商 & 专家团队介入模型**：

     - 路由权限组 AI 员工（3 人）—— 自动学习角色-路由-设备绑定关系；异常时自动派 EigenFlux 5 人磋商

     - UI/UX 组 AI 员工（2 人）—— 智能调整文案、标签页布局、锁定遮罩措辞、toast 提示内容

     - 热插拔守护组 AI 员工（2 人）—— 深度扫描 VID:PID / ioreg / dev 路径；发现异常自动工单

     - API 功能完善组 AI 员工（2 人）—— 参数验证、边缘 case 覆盖、API 契约文档自动回写

     - 用户绑定 & DB 建模组 AI 员工（2 人）—— vault 版本冲突处理、schema 迁移审查、跨用户隔离审计

     - 以上注册进 `ai_employees` 表，并邀请 EigenFlux 5 人磋商 + 领域专家（架构/安全/DBA/IoT/前端 5 人）作为 reviewer

## Non-Goals

- 不做硬件底层新驱动：不新增 Arduino 芯片级驱动、不修改 `ai_arduino_detect_engine.py` 中的 VID/PID 表（但允许新增表/索引和"当前设备插入"查询函数）。

- 不引入 WebSocket：沿用现有「轮询 + SQLite 事件队列」架构（降低全局侵入）。

- 不修改学生/家长/老师默认首页、默认 dashboard 路由的非 Arduino 分支。

- 不构建移动端专用 UI；响应式宽度与现有 Art Design Pro 一致即可。

- 不改变 SA 双密钥守卫：Arduino 管理 API（含设置页保存）仍需 SA/管理员权限；但**本 spec 把 admin/hardware\_admin 也提升为可访问设置页**（IDE 仍是仅 SA），因此要在 `_check_arduino_api_permission()` 加一个"设置页权限"分支。

## Background & Context

### 代码现状审计 (2026-09-01)

1. **路由与权限**：

   - `routes/arduino_session_routes.py` 已存在：`arduino_bp = Blueprint('arduino_session', __name__)`，注册在 `routes/__init__.py`（url\_prefix=None）。

   - 现有守卫 `_check_arduino_api_permission()`：仅允许 username==wuchenghao15 且双密钥，其他一律 ARDUINO\_SA\_ONLY 403。此守卫会拦截 `/api/arduino/*` 和 `/admin_app/arduino_ide`。**新需求**：设置页 `/admin_app/arduino_admin_setup` 应对 admin/hardware\_admin 开放（需双密钥则仅 SA）。

   - 登录路由 `auth_routes.py` L382：`/auth/login` POST 成功后 `redirect = next_url or (/admin if is_admin_like else /student_portal)`。没有 Arduino 绑定后的 override 逻辑。

   - 根路由 `routes/__init__.py`：`/` → 登录或学生门户；`/index` → 登录或 hotlink 模板。
2. **设备检测 / 事件**：

   - `engines/ai_arduino_detect_engine.py`：daemon `sys_arduino_detect` 每 30s 扫描。函数：`scan_devices / get_status / get_pending_events / ack_event`。

   - `mt_arduino_device_events` 表：存储 insert/remove 事件（前端 `/api/arduino/events/poll` 每次取 10 条）。

   - 前端轮询仅在 `arduino_ide.html` 页面存在。**当前非 IDE 页（首页/登录页/其他后台页）不轮询，检测不到 Arduino 插入也不会跳转**。
3. **前端**：

   - `arduino_ide.html`：JS 中 `ARDUINO_STATE.deviceInsertedJump = '/admin_app/arduino_ide'`；插入后不在 IDE 页则 100ms 后跳转；未登录则 `needs_login=true` 显示 Modal。

   - Modal 中 `temp-login` 走 `/api/arduino/session/temp-login`（与主 `/auth/login` 完全解耦，session 字段最小集）。
4. **数据表现状**：

   - `mt_arduino_user_sessions`：保存 code/config/edit\_history 等；无「变异动作/参数」/「绑定 vault\_id」/「锁定原因」字段。

   - 不存在 `mt_arduino_user_vault`（用户专仓表）。**需要新建**。

   - 不存在保存确认日志。
5. **已注册类名差集已通过**：上一轮修复 `ai_team_hub.html` 后，AI 员工模块的 V1/V2/V3 千轮 8/8 PASS。

### 硬约束 / 规则文档来源

- **用户权限.md**：仅 wuchenghao15 可访问 Arduino IDE；其他角色访问 Arduino 相关路由需在本 spec 定义明确例外（设置页对 admin 开放），并仍走守卫。

- **用户权限.md · SA 双密钥**：Arduino IDE 相关 API / 会话 API 在 SA 账号下必须双密钥同时在线。

- **§14 IRON\_RULE 步骤 10 版本强制评估 / 步骤 12 千轮测试**：完成后必须跑千轮 V1\~V4，Arduino 新页面不能有内联 style、不能有 BEM `--` 裸类。

- **设计规范.md / Art Design Pro 视觉融合**：新设置页必须通过 `page_type` 声明，沿用 `mtscos-action-bar / mtscos-table-wrapper / mtscos-form / mtscos-dialog` 类。

- **开发规则.md · 数据库唯一数据源**：插入/拔出/锁定/保存确认/归档均实时落库 SQLite；禁止前端内存态替代。

## Open Questions → 澄清后已解答

| #  | 问题                          | 用户表达要点（原文推断）                                                    | 本 Spec 采纳解释                                                                                           |
| -- | --------------------------- | --------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------- |
| Q1 | 「完成登陆后重写路由」含义               | 登录 redirect 不再按旧规则 /admin 或 /student\_portal，而是依据角色 → IDE 或 设置页 | ✔️ session.arduino\_bound + 登录响应 redirect 覆盖                                                          |
| Q2 | 「变异动作和参数」的定义                | 硬件输出发生差异化的所有操作/参数：板卡、端口、波特率、宏、编译标志、上传速率、接线 JSON、监视器采样率等         | ✔️ `variant_actions_json`（操作序列） + `variant_params_json`（静态配置）                                         |
| Q3 | 「绑定用户专有 Arduino 操作仓库」 撞人 专仓 | 绑定=user\_id 关联；撞人=写入用户 vault；专仓=该 user 只能读自己的 vault             | ✔️ 新建 `mt_arduino_user_vault` + 普通用户仅可 CRUD 本人的行                                                      |
| Q4 | 「首页用户是管理员」范围                | 用户权限.md 中 SA(wuchenghao15) + admin/hardware\_admin 三种角色         | ✔️ 三者都算管理员；其中进入设置页仅 SA/硬管需双密钥                                                                         |
| Q5 | 「Arduino 特殊路由规则失效」指向        | 管理员访问 IDE 路由 → 被静默拦截到设置页；IDE 这条路由对管理员相当于"不生效"                   | ✔️ `_arduino_sa_only_guard`：is\_admin → 访问 IDE 时 302 → 设置页；非 admin → 正常返回 IDE                         |
| Q6 | 全程必须保持插入状态的**检测粒度**         | IDE 打开 → 任何用户操作（编译/保存/设置保存）前再验一次                                | ✔️ 前端 2s poll + 后端所有写操作（save/save\_vault/update\_setting）前查 `get_status().connected > 0`，未连接直接 reject |

***

## Functional Requirements (功能需求)

### FR-1 全局 Arduino 插入检测与首页跳转（跨页面）

在前端全局（所有页面均加载）启动 Arduino 事件轮询：

- 当事件 `event_type === 'insert'` 发生且当前用户**未处于 IDE 或 设置页**：

  - **未登录**：跳转 `/index?arduino_inserted=1&vid_pid=<vid_pid>&model=<board_model>`，并写入 `localStorage.ARDUINO_BOUND_VIDPID`。

  - **已登录但未标记** **`arduino_bound`**：跳转前先调新增 API `GET /api/arduino/session/bind`，后端将 session 打上 `arduino_bound=True + bound_vid_pid + bound_at`，然后按 FR-2 重写路由判定结果直接跳转。

- 跳转条件**必须**在下一次 poll 返回「当前设备仍插入」时执行；避免一瞬间的假插入事件导致用户被强制来回跳。

- 全局脚本放在 `admin_app/base.html`（所有后台页继承）和 `templates/index.html`（首页）同时注入；脚本 URL `/static/js/arduino_global_hotplug.js`。

### FR-2 登录成功后的重写路由判定（后端 + 前端双保险）

- 后端：`auth_routes.py::login()` 在写 session 完成后，若（`session.arduino_bound` 为真 OR request JSON 中 `arduino_bound=1`），额外执行：

  1. 实时调 `ai_arduino_detect_engine.get_status()` 检查当前 vid\_pid 是否仍连接；若不连接 → **不做重写路由覆盖**，保留原 `redirect`。
  2. 仍连接时：若 `role_canonical ∈ {super_admin, admin, hardware_admin}` → `redirect = '/admin_app/arduino_admin_setup'`；其他用户 → `redirect = '/admin_app/arduino_ide'`。

- 前端保险：`login` 页面 JS 收到登录成功 JSON 后，若 `localStorage.ARDUINO_BOUND_VIDPID` 存在：

  1. 等落地重定向页面后，后台再向 `GET /api/arduino/session/redirect_target` 发请求拿最终 redirect。
  2. 若返回的 redirect 与当前 location 不一致，再次跳转（处理后端不支持 JSON redirect 覆盖的老版本客户端或 cookie 未同步时）。

### FR-3 角色路由分流：管理员走设置页，普通用户走 IDE

- 后端 `_arduino_sa_only_guard()` 中新增**特殊路由规则**（替换"普通用户无法使用 Arduino"的旧行为）：

  - 路径命中 `/admin_app/arduino_ide`：

    - 若 `role_canonical ∈ {super_admin, admin, hardware_admin}` → 不返回 IDE，返回 `302 Location: /admin_app/arduino_admin_setup`，并写审计日志 `ARD_ROLE_REDIRECT_SETUP`。

    - 否则（普通用户）：保持 IDE 渲染，但仍必须 **session.arduino\_bound=True 且设备当前连接** → 否则返回 302 至 `/index`（设备未绑定 → 不允许直接输入 URL 进 IDE）。

- 新增页面路由 `/admin_app/arduino_admin_setup`：

  - 权限：{super\_admin, admin, hardware\_admin}；SA 双密钥；admin/hardware\_admin 仅 VIKEY 在线或密码登录均允许（通过新增参数 `scope=setup` 调守卫）。

  - 渲染 `admin_app/arduino_admin_setup.html`，表单含：板卡白名单、编译链路径、端口白名单、库镜像源 URL、用户专仓空间配额(MB)、变异动作模板 JSON、允许保存的动作类型列表、是否启用"拔出立即自动保存"开关、默认 IDE 主题/字号。

  - 保存 API：`POST /api/arduino/admin/setup`，写入 `mt_arduino_admin_settings`（key-value 表，可多版本），并返回成功+版本号。

### FR-4 全程设备保持 + 拔出锁定（fail-closed）

- 前端：`arduino_ide.html` 与 `arduino_admin_setup.html` 收到 `remove` 事件后，**立即**：

  1. 显示全屏锁定遮罩 `arduino-lock-overlay`（禁止任何输入/点击）。
  2. 停止轮询自动保存、停止编译/上传队列、暂停设置表单提交按钮 disabled。
  3. 展示 Modal「检测到 Arduino 设备被拔出」，三按钮：

     - 「确认保存并写入专仓」 → 调 `POST /api/arduino/session/commit`（触发 FR-5）。

     - 「放弃」→ 关闭 Modal 并跳转 `/index`；不写入 vault。

     - 「我已重新插入设备」 → 先调 `GET /api/arduino/events/repoll_now`，若后端返回 connected=True 且 vid\_pid 匹配 → 解除遮罩、恢复轮询、恢复按钮；否则保持锁定并提示「仍未检测到匹配设备」。

- 后端：所有写操作（session/save / vault/commit / admin/setup / compile\_upload 等模拟硬件写接口）在进入业务前调用 `_ensure_device_present(session['bound_vid_pid'])`：

  - 未连接 → 423 LOCKED，响应含 `{"device_status": "removed", "lock_id": "..."}`；前端按 FR-4.3 展示锁定。

  - 连接但 vid\_pid 不匹配 session.bound → 409 CONFLICT，拒绝跨设备操作。

### FR-5 「确认保存」永久化 Arduino 变异动作和参数并绑定用户专仓

- 新增**变异动作 & 参数**采集：

  - 前端在 IDE 页将编译/上传/切换板卡/改波特率/保存等操作序列追加到 `VARIANT_ACTIONS` 数组；设置页表单任何改动映射为 `VARIANT_PARAMS`（键值对）。

- 新增 API `POST /api/arduino/session/commit`：

  - 参数：`session_id, code_content, variant_actions_json, variant_params_json, confirm_reason ("device_removed"|"user_save"), pin_reinserted_if_any`。

  - 后端：

    1. 先更新 `mt_arduino_user_sessions` 行，写入 `variant_actions_json / variant_params_json / locked_reason / committed=1 / committed_at`。
    2. 调用 `commit_to_user_vault(user_id, username, session_row)` 写入 `mt_arduino_user_vault`：每个提交生成一条 vault 记录，`vault_id = ARD-VLT-<user_id_hash>-<短uuid>`，含 `snapshot_version`、标签（默认"拔出自动保存"）、session\_id（外键）、`payload_json`（完整打包：code+variant\_actions+variant\_params+usage\_trace+edit\_history+device\_snapshot）、`bound_user_id`、`acl_json={"owner":user_id,"readers":[]}`。
    3. **三重永久化并行写入**：
       a) **SQLite 行**：mt\_arduino\_user\_vault 行完成提交（事务内）
       b) **物理 JSON 备份**：`_runtime/arduino_vault/<uid>/<vault_id>.json` 写入 payload\_json；目录不存在自动 mkdir
       c) **Git 仓版本控制**：`_runtime/arduino_vault_repo` 作为 Git 仓，首次 init；将 JSON 文件复制进仓；执行 git add + commit（message = `vault: <vault_id> by <username>`）+ git tag `vault/<vault_id>`；Git 失败降级为 SQLite+JSON，不阻塞 commit API 返回
    4. 返回 `{vault_id, snapshot_version, vault_size_bytes, committed_at, json_backup_path, git_tag}`。

- 新增读 API `GET /api/arduino/vault/list?page=&size=` 和 `GET /api/arduino/vault/<vault_id>`：

  - 普通用户仅能 list/get 本人 vault 行；SA 可通过 `?as_user=<uid>` 查看所有。

### FR-6 用户专仓查询 UI（IDE 页 → 左侧抽屉）

- IDE 左侧新增「用户专仓」Tab（在 editor header 之上，用 mtscos-ide 风格），展示本人最近 10 次 commit 列表，点击 → 确认后载入代码 + variant\_params，并恢复到板卡/端口选择器。

- 设置页「用户专仓配额」Tab 供管理员查看：每个用户占用 MB 数 / 提交次数 / 最近一次提交时间 / 超限状态。

### FR-7 数据表与审计

- 新增 3 张 Arduino 业务表 + 2 张 AI 介入审计表：

  1. `mt_arduino_user_vault`（vault\_id 主键, bound\_user\_id, session\_id FK, snapshot\_version INT, label, payload\_json, acl\_json, size\_bytes, committed\_at, json\_backup\_path, git\_tag, git\_commit\_sha）
  2. `mt_arduino_admin_settings`（setting\_version 主键, scope, key\_name, value\_json, changed\_by, changed\_at, active\_flag, ai\_suggestion\_ref）
  3. `mt_arduino_lock_log`（lock\_id 主键, user\_id, session\_id, lock\_trigger, lock\_reason, released\_by, released\_at, committed\_vault\_id, eigenflux\_panel\_ref）
  4. `mt_arduino_ai_intervention_log`（intervention\_id 主键, ai\_group\_type, ai\_employee\_id, action\_type, action\_detail, ai\_confidence, eigenflux\_consensus, expert\_reviewer\_list, created\_at, applied\_flag）
  5. `mt_arduino_route_override_log`（override\_id 主键, user\_role, source\_path, rewritten\_path, rule\_reason, ai\_agent\_id, eigenflux\_panel\_ref, created\_at）

- 所有 5 表创建在 `ai_arduino_detect_engine.ensure_detect_tables()` 内，保证 daemon 启动时自动建表 + 索引。

### FR-8 AI 员工 & EigenFlux 5 人磋商 & 专家团队智能介入（v2.0 新增）

- **T1 路由权限组（3 名 AI 员工，注册工种：arduino\_route\_permissions\_specialist）**：

  - 职责：扫描 `mt_arduino_route_override_log`，当 redirect 异常率超过 5% 或 30 分钟内相同角色 20 次命中不同路径时，自动提出"角色-路径-设备绑定白名单"优化建议。

  - 触发：每次 `_ensure_device_present` 失败 423/409 超过阈值 → 调 `sys_auto_hire` 雇佣（不足 3 人时补编）→ 生成建议 → 写入 EigenFlux 5 人磋商队列。

- **T2 UI/UX 组（2 名 AI 员工，arduino\_uiux\_specialist）**：

  - 职责：根据 `mt_arduino_lock_log.released_by=discard` 的比例（>20% 时），自动建议优化保存 Modal 文案、遮罩视觉层级、toast 提示措辞；建议通过 EigenFlux 前端专家 review 后自动写入对应 HTML/CSS。

- **T3 热插拔守护组（2 名 AI 员工，arduino\_hotplug\_watcher）**：

  - 职责：每 30s 深度扫描 `ls /dev/cu.* + system_profiler + ioreg`（与现有 sys\_arduino\_detect 并行但独立），发现 VID:PID 识别率异常或 session.bound 与实际连接不一致时，自动写热插拔工单到 `mt_ai_auto_hire_log` + 派发 EigenFlux IoT 专家会诊。

- **T4 API 功能完善组（2 名 AI 员工，arduino\_api\_contract\_specialist）**：

  - 职责：扫描所有新 Arduino API 的参数分布、异常返回率（>5% 时），自动补充 Pydantic 式校验、文档回写 OpenAPI JSON（保存至 `_runtime/arduino_api_contract.json`）。

- **T5 用户绑定 & DB 建模组（2 名 AI 员工，arduino\_db\_model\_specialist）**：

  - 职责：vault 版本冲突（同一 user\_id 短时间重复 commit 3 次及以上）触发 schema 审查 + 跨用户隔离审计，建议加索引/加字段；通过 EigenFlux DBA 专家 review 后落库执行 `ALTER TABLE`。

- **EigenFlux 5 人磋商**：

  - 角色组：{架构 1 + 安全 1 + DBA 1 + IoT 1 + 前端 1} = 5 人。

  - 表决规则：≥4/5 通过 → applied\_flag=1 立即执行；3/5 → SA 审核；<3 → 驳回并记录原因。

- **专家团队 reviewer**：

  - 领域：架构/安全/DBA/IoT/前端 5 名 EigenFlux 注册专家。任何 schema 变更、权限白名单变更必须至少 1 名对应领域专家电子签章（写入 applied\_by 字段）。

## Non-Functional Requirements

### NFR-1 性能

- 全局 2s 轮询：单个 `GET /api/arduino/events/poll` DB 查询 ≤ 50ms（30k 事件行场景下），现有索引要包含：`idx_arduino_events_pending(delivered, acked, created_at)` 已存在，新增 `idx_arduino_vault_user(bound_user_id, committed_at DESC)`。

- `POST /api/arduino/session/commit` 在 payload ≤ 5MB 时 ≤ 400ms（SQLite WAL 模式 + `busy_timeout=10`）。

### NFR-2 安全 / 权限

- `_check_arduino_api_permission(scope="ide"|"setup"|"vault")`：scope 参数决定哪些角色放行，不得裸返回 True。

- 所有 Arduino 写入 API 必须加 CSRF token（复用现有 session.sid 校验或 `X-Arduino-Request: 1` 头，与轮询 fetch 一致）。

- vault 行的 ACL：owner 以外任何人（包括 admin）读需走 SA `as_user` 参数；hardware\_admin 不可跨用户读。

### NFR-3 可维护 / 可追踪

- 每一次 redirect/锁定/解锁/保存 commit 都写入对应审计表：`mt_arduino_lock_log` + 现有 `mt_arduino_detect_log` + 新增 `mt_rule_violation_alert` 若角色越权。

- 前端全局脚本错误 → catch → console.warn，不中断其他页面 JS。

### NFR-4 视觉 / §14 千轮 V2

- 新页面 `arduino_admin_setup.html` 不得有内联 `<style>` 或内联 `style=` 属性（进度条动态百分比除外，使用 `data-fill` + JS 赋值模式，如 AI 员工模块修复后一致）。

- 锁定遮罩、对话框复用 `mtscos-dialog-overlay / mtscos-dialog` 类，不新增重复 CSS 组件族。

## Dependencies, Assumptions, Risks

- **依赖**：admin\_app/base.html 已注入统一 Token；`arduino_session_routes.py` 已有 Blueprint；`ai_arduino_detect_engine.ensure_detect_tables()` 可扩展。

- **假设**：登录完成后 session 仍带 `arduino_bound`（永久=False → 浏览器 tab 不关即可）。

- **风险**：用户插入设备后立刻拔出，首页 redirect 到设置页时已无设备 → 会被 `_ensure_device_present` 打回 /index（可接受，fail-closed 原则）。

- **风险**：管理员"设置页不是 IDE"可能让用户困惑 → 页面顶部 Hero 标题明确写「Arduino 管理员录入设置」并放置跳转普通用户 IDE 的链接（仅 SA 可见）。

***

## Acceptance Criteria（仅 rule 或 rubric 二选一）

### rule AC-1 跨页面插入→首页跳转链路

- rule：在任意未登录页面（/index）启动 2 轮 poll，注入一个 `insert` 事件后，最多 3 秒内浏览器地址变为 `/index?arduino_inserted=1`（前端测试：通过 `localStorage.ARDUINO_BOUND_VIDPID` 断言非空）。

- 证据来源：浏览器 Playwright 集成（或静态脚本）访问 index → 调用 poll mock → 断言 URL & localStorage。

### rule AC-2 登录重写路由分流

- rule：对普通用户账号（student）POST `/auth/login`，携带 `arduino_bound=1` 且后端 `get_status().connected > 0`，返回 JSON 中 `redirect == '/admin_app/arduino_ide'`。

- rule：对 admin 账号 POST `/auth/login`，同样条件，返回 JSON 中 `redirect == '/admin_app/arduino_admin_setup'`。

- rule：对 SA 账号（wuchenghao15）POST `/auth/login`，同条件，返回 redirect 必须为 `/admin_app/arduino_admin_setup`（不是 IDE）。

- 证据来源：Python 测试脚本用 `flask test client` 调 3 条请求 + 断言 redirect。

### rule AC-3 管理员特殊路由规则：IDE 路由对管理员失效

- rule：管理员 session 访问 GET `/admin_app/arduino_ide` → 返回 302 Location 包含 `arduino_admin_setup`。

- rule：普通用户 session + `arduino_bound=1 + device_connected` 访问同 URL → 返回 200，响应体含字符串 `mtscos-canvas-stage`（IDE 工作台 div）。

- 证据来源：flask test client。

### rule AC-4 拔出锁定 fail-closed

- rule：IDE 页面渲染完成后，前端 mock 一个 remove 事件，**在 500ms 内** DOM 中 `classList.contains('arduino-lock-overlay--visible')` 为 True；且 `arduinoSaveSession(false)` 被调用按钮 disabled。

- rule：随后调用 `POST /api/arduino/session/save`（后端）在 remove 状态下返回 423 `device_status=removed`。

- 证据来源：前端 JS 单元（Node/playwright）+ 后端 Python 脚本。

### rule AC-5 确认保存永久化 + 绑定用户专仓

- rule：`POST /api/arduino/session/commit` 成功响应包含非空 `vault_id` 且 `mt_arduino_user_vault` 新增一行 `bound_user_id == user_id`、`size_bytes > 0`、`payload_json` 含 code\_content + variant\_actions + variant\_params 三个 top key。

- rule：物理 JSON 备份文件存在 — `_runtime/arduino_vault/<uid>/<vault_id>.json` 文件 read 返回 JSON 顶层与 payload\_json 一致。

- rule：Git 仓版本控制 tag 存在 — `git -C _runtime/arduino_vault_repo tag | grep vault/<vault_id>` 非空；或 git 不可用时 commit API 返回 `git_tag=FAILED_DEGRADED` 且不影响 HTTP 200。

- rule：`GET /api/arduino/vault/list` 在另一普通用户 session 下**不返回**本次提交的 vault\_id（跨用户隔离）。

- 证据来源：SQLite SELECT + 文件存在性检查 + git tag 检查 + 不同 session 的 flask test client。

### rule AC-6 数据表/索引自动建表（5 张 Arduino 表 + 对应索引）

- rule：删除 `mt_arduino_user_vault/mt_arduino_admin_settings/mt_arduino_lock_log/mt_arduino_ai_intervention_log/mt_arduino_route_override_log` 共 5 张表后，import `ai_arduino_detect_engine` 并调用任意 DAO（如 `get_status()`）后，SQL 查询 `SELECT name FROM sqlite_master WHERE type='table' AND name IN (...)` 返回 5 个表名齐全；对应索引 ≥ 6 条（3 业务表索引 + AI 介入表 2 索引 + route\_override 1 索引）存在。

- 证据来源：python 脚本。

### rubric AC-7 前端代码质量（§14 千轮 V1\~V4）

- rubric：对 `arduino_admin_setup.html` + `arduino_ide.html` 做 V1\~V4 千轮子集扫描，维度 = (缺失类数, 内联 style 数, BEM `--` 裸类数, 绕过标记数)，每维最高 1 分，总分 ≥ 4 才 PASS。

  - 0 分 (严重)：任一维 ≥ 10 违规。

  - 1 分 (通过)：0 违规 或 进度条百分比 style.width ≤ 1 处且对应 `data-fill` 存在。

- 证据来源：本次 spec 前序修复中相同的 `python3 §14_scan.py` 脚本。

### rubric AC-8 用户体验

- rubric：从设备插入 → 跳转首页 → 登录 → 到达 IDE/设置 → 模拟拔出 → 弹出保存确认 → 确认保存 → 看到 vault 列表，端到端链路的**明确阻塞点**仅 2 处（登录 + 保存确认 Modal）。额外阻塞 < 1 得 2 分；2\~3 处 得 1 分；>3 处得 0 分；通过阈值 ≥ 1。

- 证据来源：手动 Playwright 脚本 walkthrough 记录阻塞位置数。

### rule AC-9 AI 员工 & EigenFlux & 专家介入注册与触发（v2.0 新增）

- rule：执行 `ensure_ai_arduino_workers_registered()` 后，`ai_employees` 表至少新增 11 条 Arduino 工种行（3 路由权限 + 2 UI/UX + 2 热插拔 + 2 API + 2 DB），且 `specialization` 字段分别为 `arduino_route_permissions_specialist / arduino_uiux_specialist / arduino_hotplug_watcher / arduino_api_contract_specialist / arduino_db_model_specialist`。

- rule：模拟触发 423/409 阈值（30 次失败）后，`mt_arduino_ai_intervention_log` 至少新增 1 条 `ai_group_type='t1_route_permissions'` 且 `eigenflux_consensus` 为 0\~1 数字；`mt_arduino_route_override_log` 同步新增建议行。

- rule：EigenFlux 5 人磋商接口被调用时，5 名领域专家列表 = {架构, 安全, DBA, IoT, 前端} 齐全无重复。

- 证据来源：SQLite SELECT × ai\_employees / mt\_arduino\_ai\_intervention\_log / mt\_arduino\_route\_override\_log + eigenflux\_registrations 断言。

### rule AC-10 用户信息深度绑定 & DB 隔离（v2.0 新增）

- rule：`vault.bound_user_id` 在同一 user\_id 下的所有 vault 行与 `users.id` FK 约束（或等价业务约束）保持正确 — 任意 commit 后取 vault 行 SELECT users WHERE id=bound\_user\_id → 命中且 username == commit 入参 username。

- rule：5 张新增表均含 `idx_*_created_at_desc` 或同效创建时间倒序索引，保证 admin 控制台列表页 100ms 内首屏。

- 证据来源：SQLite SELECT + FK 一致性脚本。

***

End of `spec.md` v2.0. 等待 §14 Plan（tasks\_v2.md）与 Approve。
