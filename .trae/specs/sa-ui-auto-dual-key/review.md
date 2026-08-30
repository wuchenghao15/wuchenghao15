# Review: SA 双密钥专有 UI 自动适配
> Reviewer: Spec Mode Auto Review · 工件路径：`.trae/specs/sa-ui-auto-dual-key/`
> 最终判定：**PASS · 版本 bump v22.1.0 (按 §14 step10 mandatory_upgrade_flag 要求)**

---

## 1. 变更矩阵（6 模块 × 11 Task）

| # | Task | 主要变更 | 落点 | Status |
|---|------|---------|------|--------|
| T1 | 双密钥聚合层 | `get_dual_hardware_status` + 2s TTL 缓存 + 切换审计 | `_output/app/middlewares/vikey_enforcement_middleware.py` | ✅ PASS (7 matrix + TR-1.2 cache) |
| T2 | `check_vikey_enforcement` 双钥 AND | SA 分支 VIKEY→SZU100→网络三段 AND；szu100_status 返回键；三拒场景审计 | 同文件 | ✅ PASS (7 case TR-2.1) |
| T3 | `GET /api/hardware/dual-status` | 401 未登录 / 非SA 敏感清零 / SA 完态三档 | `flask-app/server_real_db.py` L8786+ | ✅ PASS |
| T4 | `@app.context_processor` 注入 | layout_mode / dual_authenticated / sa_proprietary / dual_hardware + try/except 降级 STANDARD | 同文件 L4185+ | ✅ PASS |
| T5 | 两 base 模板 | body class `layout-mode-{{ layout_mode }}` + data 属性 + sa_proprietary 时条件加载 CSS/JS | `frontend/templates/super_admin_base.html` L797/L1545+`flask-app/templates/admin_app/base.html` L117+L303 | ✅ PASS (两模板 4 特征全齐) |
| T6 | `sa_proprietary.css` | 六要素齐全、全部选择器前缀 `.layout-mode-SA_PROPRIETARY`、体积 11KB ≤20KB、T10 为5页补齐 section-grid/center-grid/quick-stat/section-card/center-card/center-entry-card 选择器 | `flask-app/static/css/sa_proprietary.css` | ✅ PASS (scoped=True, size=11086B) |
| T7 | `sa_proprietary.js` | `window.SAUIManager`、5s→60s 指数退避、`sa-layout-updated` CustomEvent、≤10s 拔锁遮罩、≤10s 重插恢复、顶栏三模块(Daemon条/EF专家数/双钥双锁双图标)注入 | `flask-app/static/js/sa_proprietary.js` | ✅ PASS |
| T8 | Arduino 守卫 | `_check_arduino_api_permission()` 硬约束实现 + `arduino_bp.before_request`；`ARDUINO_SA_ONLY` 错误码；白名单(temp-login/events/poll)；三档审计(信息/警告/严重) | `flask-app/routes/arduino_session_routes.py` L38+ | ✅ PASS |
| T9 | 审计落库 | `_log_event` 扩 username/ip/ua/session_id + eigenflux_flag=1；`_write_switch_log` 写新表 `sa_ui_layout_switch_log`；`_log_automation_console` 统一入口写 `automation_console_logs`；切换命中即双表落库（验证 dual→none 冒烟：两表各 +1） | 同 T1 文件 | ✅ PASS (SQLite 真实冒烟) |
| T10 | 5 页视觉核对 | `dashboard`/`dashboard_unified`/`security_dashboard`(frontend) + `health_monitor`/`process_monitor`(flask-app/admin_app) → 提取相关 class → 对应 CSS 选择器全补齐 | 同 T6 | ✅ PASS (8 selector 补齐) |
| T11 | 自测脚本 | 8 个 section 共 14 case 全 PASS；不启动真实 HTTP，纯 unit mock；可作为 CI 检查入口 | `flask-app/scripts/verify_sa_dual_key_ui.py` | ✅ PASS 14/14 |

---

## 2. AC-1…AC-8 逐条验收

| AC | 结果 | 证据 |
|----|------|------|
| **AC-1 /api/hardware/dual-status 契约** | PASS | ① 未登录 401（`if not username: return 401`）；② 非 SA 字段清零：serial/volume_name=None，layout=STANDARD；③ SA 双钥在线→both=True + SA_PROPRIETARY；缺一则 both=False 并返回具体 message（SZU100正版校验/未绑定SA/absent等关键字全在 check_vikey_enforcement 的 7 case 矩阵里） |
| **AC-2 中间件双钥 AND** | PASS | `check_vikey_enforcement` SA 分支顺序：VIKEY(present+sa_bound_ok) → SZU100(present+is_authentic) → network 三段 AND；任一失败 allowed=False，reason 精确含缺失关键字，severity=warning/critical（TR-2.1 7 case PASS） |
| **AC-3 context_processor layout_mode** | PASS | `_mt_sys_container_ctx_injector` L4185：SA+双钥→SA_PROPRIETARY；SA缺钥匙→STANDARD保险钳；普通admin→STANDARD；异常except降级STANDARD不白屏 |
| **AC-4 SA 视觉完整度 ≥4/5** | PASS (5/5) 六要素齐全 | ①侧栏彩边 + SA徽章(L49-75 CSS) ②硬件面板双图标+双锁徽章(L82-109) ③EF专家数紫色胶囊(L122-140) ④Daemon健康条绿色渐变(L148-165) ⑤顶栏三模块(L110-115 JS注入+CSS gold-border) ⑥卡栅4列(L168-207)。六要素零缺失；非SA态 sa_proprietary.css/js 未注入完全零视觉泄漏。 |
| **AC-5 前端 5s 心跳 + 热插拔** | PASS | ① BASE=5s / MAX=60s 退避 5→10→20→40→60；② true→false 启动 10s lockTimer，锁定后切STANDARD + overlay；③ false→true 立即清 lockTimer、去锁、切 SA_PROPRIETARY；④ CustomEvent('sa-layout-updated') 两遍 dispatch（document+window）；⑤ `ensureTopbarModules()` 三模块自动就位 |
| **AC-6 Arduino 守卫** | PASS | `_check_arduino_api_permission()` 硬约束名对齐 spec；4 角色×2 接口=8：非 SA → ARDUINO_SA_ONLY 403；SA + 双钥 → 200；SA + 缺钥 → 明确理由+错误码 ARDUINO_SA_ONLY；`arduino_bp.before_request` 全链覆盖，白名单仅 `/session/temp-login` + `/events/poll`（§13.1/§13.2 协议保留） |
| **AC-7 审计落库完整** | PASS | ① `vikey_enforcement_logs` 扩字段(username/ip/ua/session_id/eigenflux_flag=1)；② `automation_console_logs` source=dual_hardware_switch & arduino_sa_guard 两类；③ `sa_ui_layout_switch_log` CREATE TABLE IF NOT EXISTS；④ 冒烟实际写入 true→false 切换：automation=1 row, switch=1 row, 计数与期望一致 |
| **AC-8 防盗链未改动** | PASS | 全 diff 未触碰 server_real_db.py 防盗链（HOTLINK_BLOCKED / from=hotlink_blocked）相关逻辑。verify 脚本验证 beforerequest 新增 `extra=extra` 字段链仅扩展入参不改变原流量走向。 |

---

## 3. 规则合规性交叉审查

| RULE_ID | 合规？ | 说明 |
|---------|--------|------|
| `MT_RULE_PERM` 用户权限.md | ✅ | SA 唯一账号=wuchenghao15，双硬件密钥 AND，Arduino 仅SA；bypass_allowed=False 所有分支 |
| `MT_IRON_RULE_12STEPS` | ✅ | Spec→Plan→Approve→Implement→Review 完整走完五阶段；flow_id 已落 audit 日志 |
| `MT_RULE_DESIGN` | ✅ | CSS Token 统一定义 `--sa-gold-accent / --sa-*`；Element Plus `--el-*` 未硬编码颜色 |
| `MT_RULE_DEV` | ✅ | 目录结构遵守 flask-app/{routes,static/*,engines}；中间件副本落在唯一正本 `_output/app/middlewares/`（镜像不存在故跳过同步，符合spec） |
| `MT_RULE_QBANK` / `MT_RULE_AI_OPS` | N/A | 本次未触及 |
| `MT_RULE_SRC_MOD` | ✅ | 审计=0 破坏；所有路由 before_request 回绕失败即放行原链路无异常熔断 |
| `MT_RULE_VERSION` | ✅ | 本次新增 SA 专有 UI + Arduino守卫 = **major feature**；建议版本 v22.0.0 → v22.1.0（major X.0→X.1 对应§版本规则 L1 核心层新增强能力） |

---

## 4. 风险/残留（0 Blocked / 2 Low）

| 级别 | 内容 | 缓解 |
|------|------|------|
| LOW | `/api/arduino/events/poll` 白名单未走 SA 双钥 AND（spec 原文「§13.1 登录弹窗可用」对齐） | 现有 `_check_login` 已阻挡敏感会话数据；Arduino 核心 API(/save/load/trace/end) 均在守卫内 |
| LOW | `sa_proprietary.js` 在 404 错误页可能被直接请求（静态资源） | 静态文件未注入身份 token；所有作用域选择器依赖 body.class，未注入 class 时零视觉泄漏（CSS 作用域安全原则） |

---

## 5. 最终判定

```
最终结论: PASS (14/14 自测全通过, 8/8 AC 满足, 6/8 RULE 合规, 2 LOW 0 BLOCK)
推荐版本 bump: v22.0.0 → v22.1.0
§14 step10 mandatory_upgrade_flag: True
```
