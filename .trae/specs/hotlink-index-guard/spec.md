# Spec: 全站防盗链拦截 + /index 统一首页路由

- **flow_id 前缀**: `flow_hotlink_index_`
- **日期**: 2026-08-30
- **规则来源**: 用户权限.md 硬条款「所有页面禁止盗链，未授权且Referer非法的请求返回403 HOTLINK_BLOCKED并重定向到首页 /index?from=hotlink_blocked」

## 背景
规则文档中防盗链重定向目标 `/index` 长期不存在（404），且防盗链拦截在代码层未落地（flask-app 无 hotlink 实现）。

## 方案
1. `/index` 与 `/` 同视图双路由（`@system_container('homepage', require_auth='guest')`）。
2. `_mt_hotlink_guard` before_request（注册于 session_loader 之后、VIKEY 锁之前）：
   - 外站 Referer：静态 403 / API 403(HOTLINK_BLOCKED) / 白名单页放行 / 其余页面 302 `/index?from=hotlink_blocked`
   - 无 Referer：guest 非白名单页面 302 `/index`（先经首页）；API/静态放行
   - 本站 Referer / 已登录 / OPTIONS/HEAD：放行
3. `_mt_hotlink_parse_netloc` 防伪造解析：端口非纯数字、userinfo(@)、主机名后缀、异端口、非回环 IPv6 全判外站。
4. `_mt_hotlink_audit` 限频落库 `automation_console_logs`（forbid 60s / redirect 10s，eigenflux_flag=1）。

## AC（8条）
AC-1 /index 路由；AC-2 外站Referer页面302；AC-3 外站Referer API 403；AC-4 静态外站盗链403；
AC-5 伪造Referer全拦截；AC-6 已登录/白名单/OPTIONS零扰动；AC-7 阻断审计落库；AC-8 守卫位次与异常兜底。

## 验证
`flask-app/scripts/verify_hotlink_index.py`（A 源码断言 + B 纯函数三矩阵 + C live HTTP）。
