# Tasks: 全站防盗链拦截 + /index 路由

| # | 任务 | 产物 | 状态 |
|---|------|------|------|
| T1 | 判定核心纯函数 `_mt_hotlink_decision`（三分支优先级） | server_real_db.py | done |
| T2 | 防伪造 Referer 解析 `_mt_hotlink_parse_netloc` | server_real_db.py | done |
| T3 | before_request 守卫 `_mt_hotlink_guard`（302/403 双处置） | server_real_db.py | done |
| T4 | 限频审计 `_mt_hotlink_audit` → automation_console_logs | server_real_db.py | done |
| T5 | `/index` 双路由 + system_container 容器 | server_real_db.py | done |
| T6 | verify_hotlink_index.py（A/B/C 三段自测） | scripts/verify_hotlink_index.py | done |

## 测试矩阵（§14 STEP_12 千轮）
- NORMAL 400 = 8 场景 × 50（白名单/本站Referer/无Referer API与静态/已登录/OPTIONS）
- ABNORMAL 300 = 6 场景 × 50（guest 无Referer页面 / 外站Referer页面 redirect）
- HACKER 300 = 6 攻击 × 50（后缀主机/userinfo/畸形端口/异端口/静态盗链/非回环IPv6）
