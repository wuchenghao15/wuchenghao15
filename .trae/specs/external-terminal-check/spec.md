# Spec: 外部终端访问权限与系统功能全面检查（flow_external_terminal_check）

## 背景
用户报告"外部终端还是打不开系统"。诊断结论：
1. **网络层**：外部终端（mini 设备 192.168.31.242）当前完全离线（ARP 无记录、ping 100% 丢包、
   其轮询脚本 15:58:49 后停止），请求根本未到达主服务器 —— 与拦截无关。
2. **拦截层**：主服务器 HTTP 层局域网可达（模拟外部访问 `/`、`/index` 全 200），防盗链零误拦。
3. **[严重] 检查中发现安全缺陷**：`vikey_enforcement_middleware.py` 正本在 `_output/app/middlewares/`，
   运行位 `flask-app/app/middlewares/` 缺失 → server_real_db.py 3 处 import 全部失败
   （日志 3351 次/日）→ **SA 双钥强制认证（VIKEY+SZU100+插钥终端绑定）整体 fail-open**。

## 需求
1. FIX-1：将中间件正本同步部署至运行位（SHA256 严格一致），恢复 SA 双钥强制认证 fail-closed。
2. CHK：外部终端访问全矩阵检查 —— 防盗链三分类、SA 终端绑定、容器引导、白名单零扰动。
3. Verify：四段式验证脚本（A 部署断言 / B 判定矩阵 / C live HTTP / D 外部 IP 模拟）。

## 防盗链判定语义（已上线 v22.2.0，本 flow 复验）
- 已登录 / OPTIONS / HEAD → 放行
- 外站 Referer：静态/API → 403 HOTLINK_BLOCKED；白名单页（/、/index、auth）→ 放行；其余页面 → 302 `/index?from=hotlink_blocked`
- 无 Referer：白名单 / API / 静态 → 放行；其余页面 → 302 `/index?from=hotlink_blocked`
- 本站 Referer → 放行

## SA 终端绑定语义（v22.1.0，本 flow 恢复其生效）
- 仅信任 TCP 层 remote_addr（不信任 X-Forwarded-For）
- 插钥终端 = loopback(127.0.0.1/::1/localhost) + 本机 hostname 解析 IP + `_config/security/sa_bound_terminals.json` 的 extra_bound_ips
- 空 IP / None / 未知 IP / `::ffff:` 映射外部 IP → NOT_BOUND（fail-closed）
- SA 用户访问需双钥 + 终端绑定 + 网络在线全部通过

## 验收标准（AC-1..AC-8）
见 flow 脚本 STEP_8。

## 网络层结论（落库备查）
mini 设备 242 离线为独立网络事件（设备休眠/关机/断网/IP变更），与防盗链、权限拦截无关。
