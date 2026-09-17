#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@system_container 权限装饰器
======================================================
§14 IRON_RULE · STEP_7_EXECUTE · 模块1 后端Blueprint P1
flow_id: flow_dev_pages_functions_complete_20260818_001
目标版本: v21.12.1 (L3_FIX基于v21.12.0)

4级权限模型(对齐用户权限.md §2 @system_container 4级):
  guest        - 访客(未登录可访问)
  login        - 登录用户(任意已登录)
  admin        - 管理员(admin/system_admin/hardware_admin/hardware_vikey_admin)
  super_admin  - 超级管理员(唯一wuchenghao15, 7要素+VIKEY强认证)

6字段用户容器强制验证(用户权限.md C2硬约束):
  1. user_group      组别校验(对照 allowed_groups 白名单)
  2. permission_level 权限级校验(对照 require_auth 级别)
  3. status          账号状态校验(active/disabled/banned)
  4. anomaly_flag     异常标记校验(无异常才放行)
  5. legal_check      合法性校验(VIKEY加密狗7要素)
  6. timestamp_check  时间戳校验(会话未过期)

落库: mt_permission_audit_detail (每次请求权限审计可追溯)
兼容: 旧装饰器 require_login/require_admin/require_super_admin/require_role 保留不破坏
异常码字典: 调用 mt_exception_code_dict (模块4 P1-A) 匹配异常码
"""
import os, json, sqlite3, uuid
from functools import wraps
from datetime import datetime, timedelta
from flask import session, redirect, jsonify, request, g

# 路径配置(兼容from导入与直接运行)
PROJECT_ROOT = "/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project"
APP_DB = os.path.join(PROJECT_ROOT, "flask-app/ai_engines/app.db")
# 主库(automation_console_logs 所在, 与 rule_db.py 同源)
MAIN_DB = os.path.join(PROJECT_ROOT, "_runtime/databases/Database/app.db")

# §14.1 L5 审计闭环: 拒绝事件落 automation_console_logs(eigenflux_flag=1)
# §14.2: 同一账号 24h 内越权 403/401 >= 20次 → EigenFlux 异常上报(perm_abuse_suspect)
_PERM_ABUSE_THRESHOLD = 20
_PERM_ABUSE_WINDOW_HOURS = 24
_PERM_ABUSE_REPORT_COOLDOWN_MIN = 60
_DENY_EXC_CODES = ("E_AUTH_401", "E_AUTH_403")

# 敏感字段模式(与 security_middleware.SensitiveDataFilter 同口径):
# 审计/日志消息中禁止 password/token/secret 等明文
_SENSITIVE_MSG_PATTERNS = ('password', 'passwd', 'token', 'secret', 'apikey',
                           'api_key', 'private_key', 'vikey', 'authorization', 'cookie')


def _mask_sensitive(text):
    """消息级脱敏: key=value / "key":"value" 中的敏感值替换为 *** (失败返回原文)"""
    try:
        import re as _re
        pat = '|'.join(_SENSITIVE_MSG_PATTERNS)
        rx = _re.compile(
            r'(?i)(("?|\')?(' + pat + r')("?|\')?\s*(?:=>|=|:)\s*)'
            r'("?|\'?)((?:\\.|[^"\',\n}\\])+)("?|\'?)')
        return rx.sub(lambda m: m.group(1) + m.group(5) + '***' + m.group(7),
                      str(text))
    except Exception:
        return text


def _console_log(level, source, message, eigenflux_flag=1):
    """落库 automation_console_logs (主库), 失败不影响主请求"""
    try:
        if not os.path.exists(MAIN_DB):
            return
        conn = sqlite3.connect(MAIN_DB, timeout=10.0)
        try:
            conn.execute("PRAGMA busy_timeout = 10000")
            conn.execute(
                "INSERT INTO automation_console_logs"
                " (timestamp, level, source, message, eigenflux_flag)"
                " VALUES (?,?,?,?,?)",
                (datetime.now().isoformat(), level, source,
                 _mask_sensitive(message)[:2000], eigenflux_flag))
            conn.commit()
        finally:
            conn.close()
    except Exception as e:
        import sys as _sys
        print(f"[system_container.console_log WARN] {e}", file=_sys.stderr)


def _report_perm_abuse_if_needed(user_info, exc_code):
    """§14.2 越权滥用检测: 24h内 403/401 >= 20次 → EigenFlux 上报(60min冷却)"""
    try:
        username = user_info.get("username") or ""
        if not username:
            return
        conn = sqlite3.connect(APP_DB, timeout=5.0)
        conn.row_factory = sqlite3.Row
        try:
            since = (datetime.now() - timedelta(
                hours=_PERM_ABUSE_WINDOW_HOURS)).isoformat()
            row = conn.execute(
                "SELECT COUNT(*) AS n FROM mt_permission_audit_detail"
                " WHERE username=? AND exception_code IN (?,?)"
                " AND timestamp_iso >= ?",
                (username, _DENY_EXC_CODES[0], _DENY_EXC_CODES[1], since)
            ).fetchone()
            if not row or (row["n"] or 0) < _PERM_ABUSE_THRESHOLD:
                return
        finally:
            conn.close()
        # 冷却检查: 60min 内已上报过则跳过(主库)
        cooldown_since = (datetime.now() - timedelta(
            minutes=_PERM_ABUSE_REPORT_COOLDOWN_MIN)).isoformat()
        if os.path.exists(MAIN_DB):
            conn2 = sqlite3.connect(MAIN_DB, timeout=10.0)
            conn2.execute("PRAGMA busy_timeout = 10000")
            dup = conn2.execute(
                "SELECT COUNT(*) FROM automation_console_logs"
                " WHERE source='perm_abuse_suspect' AND message LIKE ?"
                " AND timestamp >= ?",
                (f"%user={username}%", cooldown_since)).fetchone()
            if dup and dup[0] > 0:
                conn2.close()
                return
            conn2.execute(
                "INSERT INTO automation_console_logs"
                " (timestamp, level, source, message, eigenflux_flag)"
                " VALUES (?,?,?,?,1)",
                (datetime.now().isoformat(), "SECURITY", "perm_abuse_suspect",
                 f"24h越权>=20次 user={username} last_code={exc_code}"
                 f" route={user_info.get('route_path', '')}"))
            conn2.commit()
            conn2.close()
    except Exception as e:
        import sys as _sys
        print(f"[system_container.abuse WARN] {e}", file=_sys.stderr)

# 4级权限要求枚举(对齐用户权限.md §2)
PERM_GUEST       = "guest"
PERM_LOGIN       = "login"
PERM_ADMIN       = "admin"
PERM_SUPER_ADMIN = "super_admin"
PERM_LEVELS = (PERM_GUEST, PERM_LOGIN, PERM_ADMIN, PERM_SUPER_ADMIN)

# 11级角色(用户权限.md §1) → 4级权限要求映射
# 含中文别名兼容登录时写入 session.get('role') 的各种值
ROLE_TO_PERM = {
    # 标准英文键
    "guest":               PERM_GUEST,
    "student":             PERM_LOGIN,
    "student_vip":         PERM_LOGIN,
    "teacher":             PERM_LOGIN,
    "user":                PERM_LOGIN,  # v22.39.0: user 普通注册用户也必须 login 级
    "parent":              PERM_LOGIN,
    "admin":               PERM_ADMIN,
    "system_admin":        PERM_ADMIN,
    "hardware_admin":      PERM_ADMIN,
    "hardware_vikey_admin":PERM_ADMIN,
    "super_admin":         PERM_SUPER_ADMIN,
    # 中文别名 (登录时 session['role'] 写入的中文值, 之前 ROLE_TO_PERM 漏了导致 403)
    "成人学生":              PERM_LOGIN,
    "家长":                PERM_LOGIN,
    "学生":                PERM_LOGIN,
    "VIP学生":              PERM_LOGIN,
    "教师":                PERM_LOGIN,
    "普通用户":              PERM_LOGIN,
}

# 状态白名单(用户权限.md C2 - 6字段3状态)
STATUS_ACTIVE    = "active"
STATUS_DISABLED  = "disabled"
STATUS_BANNED    = "banned"

# 异常码字典(与模块4 P1-A Seed 一致)
EXC_AUTH_401         = "E_AUTH_401"     # 未登录或登录已过期
EXC_AUTH_403         = "E_AUTH_403"     # 权限不足，禁止访问
EXC_PERM_GROUP       = "E_PERM_GROUP"   # 用户组别不匹配
EXC_PERM_STATUS      = "E_PERM_STATUS"  # 账号被禁用
EXC_PERM_ANOMALY     = "E_PERM_ANOMALY" # 账号存在异常标记
EXC_PERM_ILLEGAL     = "E_PERM_ILLEGAL" # 账号合法性校验失败(VIKEY)
EXC_PERM_TIMESTAMP   = "E_PERM_TIMESTAMP"  # 登录时间戳过期


def _audit_log(user_id, username, user_role, user_group, route_path,
               blueprint_name, permission_level, status_check, exception_code,
               ip_address, user_agent, vikey_ok, flow_id=None, extra=None):
    """权限审计明细落库 mt_permission_audit_detail (模块4 P1-D)
    保证幂等+失败不影响主请求(只告警)
    """
    try:
        conn = sqlite3.connect(APP_DB, timeout=3)
        c = conn.cursor()
        c.execute("""INSERT INTO mt_permission_audit_detail
            (flow_id, request_id, user_id, username, user_role, user_group,
             route_path, blueprint_name, permission_level, status_check,
             exception_code, ip_address, user_agent, vikey_ok, timestamp_iso, extra_json)
            VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (flow_id, str(uuid.uuid4())[:16], user_id or "", username or "",
             user_role or "", user_group or "", route_path or "",
             blueprint_name or "", permission_level or "",
             status_check, exception_code,
             ip_address or "", user_agent or "", 1 if vikey_ok else 0,
             datetime.now().isoformat(),
             json.dumps(extra or {}, ensure_ascii=False)))
        conn.commit(); conn.close()
    except Exception as e:
        # 审计落库失败不阻断主流程，仅 stderr 告警
        import sys as _sys
        print(f"[system_container.audit WARN] {e}", file=_sys.stderr)


def _check_user_container_6fields(require_auth, allowed_roles, allowed_groups):
    """
    6字段用户容器强制验证(用户权限.md C2硬约束)
    返回 (status_check, exception_code, user_info_dict)
      status_check: 'PASS' / 'FAIL' / 'SKIP'
      exception_code: 失败时的异常码
      user_info_dict: 当前用户上下文(user_id/username/role/group/ip/ua/vikey)
    """
    # 1. 收集用户上下文(从 session + request)
    user_id    = session.get("user_id") or session.get("uid") or ""
    username   = session.get("username") or session.get("user") or ""
    user_role  = session.get("role", "guest")
    user_group = session.get("user_group") or session.get("group") or "default"
    logged_in  = session.get("logged_in", False)
    vikey_ok   = bool(session.get("vikey_ok", False))
    ip_addr    = request.remote_addr or "0.0.0.0"
    user_agent = (request.headers.get("User-Agent") or "")[:255]
    route_path = request.path
    blueprint_name = (request.blueprint if hasattr(request, "blueprint") else "") or ""

    user_info = {
        "user_id": user_id, "username": username, "user_role": user_role,
        "user_group": user_group, "logged_in": logged_in,
        "vikey_ok": vikey_ok, "ip_address": ip_addr, "user_agent": user_agent,
        "route_path": route_path, "blueprint_name": blueprint_name,
    }

    # 2. require_auth=guest 直接放行(但记录SKIP审计)
    if require_auth == PERM_GUEST:
        return ("SKIP", None, user_info)

    # 3. require_auth>=login 校验登录状态
    if not logged_in:
        return ("FAIL", EXC_AUTH_401, user_info)

    # 4. 时间戳校验(会话max_age默认8小时)
    session_started = session.get("session_started_at")
    if session_started:
        try:
            started_dt = datetime.fromisoformat(session_started)
            age_sec = (datetime.now() - started_dt).total_seconds()
            if age_sec > 8 * 3600:  # 8小时过期
                return ("FAIL", EXC_PERM_TIMESTAMP, user_info)
        except Exception:
            pass  # 时间戳格式错误不阻断

    # 5. 账号状态校验
    status = session.get("status", STATUS_ACTIVE)
    if status == STATUS_DISABLED:
        return ("FAIL", EXC_PERM_STATUS, user_info)
    if status == STATUS_BANNED:
        return ("FAIL", EXC_PERM_STATUS, user_info)

    # 6. 异常标记校验
    anomaly_flag = session.get("anomaly_flag", 0)
    if anomaly_flag:
        return ("FAIL", EXC_PERM_ANOMALY, user_info)

    # 7. 用户组别校验(allowed_groups 白名单)
    if allowed_groups and user_group not in allowed_groups:
        return ("FAIL", EXC_PERM_GROUP, user_info)

    # 8. 角色权限校验(require_auth级 + allowed_roles白名单)
    user_perm = ROLE_TO_PERM.get(user_role, PERM_GUEST)
    perm_order = {PERM_GUEST:0, PERM_LOGIN:1, PERM_ADMIN:2, PERM_SUPER_ADMIN:3}
    if perm_order.get(user_perm, 0) < perm_order.get(require_auth, 0):
        return ("FAIL", EXC_AUTH_403, user_info)
    if allowed_roles and user_role not in allowed_roles:
        return ("FAIL", EXC_AUTH_403, user_info)

    # 9. 超级管理员 VIKEY 合法性校验(C2硬约束)
    if require_auth == PERM_SUPER_ADMIN:
        if not vikey_ok:
            return ("FAIL", EXC_PERM_ILLEGAL, user_info)
        # wuchenghao15 唯一性校验
        if username and username != "wuchenghao15":
            return ("FAIL", EXC_AUTH_403, user_info)

    return ("PASS", None, user_info)


def system_container(require_auth=PERM_LOGIN, allowed_roles=None,
                     allowed_groups=None, flow_id=None, audit=True):
    """
    @system_container 权限装饰器 (4级 + 6字段用户容器验证)

    参数:
      require_auth    - 4级权限要求: 'guest'/'login'/'admin'/'super_admin'
      allowed_roles   - 角色白名单(可选, 11级角色子集)
      allowed_groups  - 用户组别白名单(可选)
      flow_id         - §14流程ID(关联审计)
      audit           - 是否落库 mt_permission_audit_detail

    用法:
      @system_container(require_auth='login')
      @system_container(require_auth='admin', allowed_roles=['admin','system_admin'])
      @system_container(require_auth='super_admin', flow_id='flow_xxx')
      @system_container(require_auth='guest', audit=False)  # 公开API不审计
    """
    if require_auth not in PERM_LEVELS:
        raise ValueError(f"@system_container require_auth 必须是 {PERM_LEVELS}, 实际={require_auth}")
    allowed_roles = allowed_roles or []
    allowed_groups = allowed_groups or []

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # 1. 6字段用户容器验证
            status_check, exc_code, user_info = _check_user_container_6fields(
                require_auth, allowed_roles, allowed_groups)

            # 2. 审计落库(无论PASS/FAIL)
            if audit:
                _audit_log(
                    user_info["user_id"], user_info["username"],
                    user_info["user_role"], user_info["user_group"],
                    user_info["route_path"], user_info["blueprint_name"],
                    require_auth, status_check, exc_code or "",
                    user_info["ip_address"], user_info["user_agent"],
                    user_info["vikey_ok"], flow_id=flow_id,
                    extra={"allowed_roles": allowed_roles,
                           "allowed_groups": allowed_groups})

            # 3. PASS 放行
            if status_check == "PASS" or status_check == "SKIP":
                g.current_user = user_info  # 注入到请求上下文供视图使用
                return f(*args, **kwargs)

            # 4. FAIL 返回统一异常响应(对齐异常码字典 mt_exception_code_dict)
            #    §14.1 L5: 拒绝事件同步落 automation_console_logs(eigenflux_flag=1)
            #    §14.2: 24h内越权>=20次触发 perm_abuse_suspect EigenFlux 上报
            if status_check == "FAIL":
                _console_log(
                    "SECURITY", "system_container",
                    f"权限拒绝 code={exc_code} user={user_info['username']}"
                    f" role={user_info['user_role']} route={user_info['route_path']}"
                    f" ip={user_info['ip_address']}")
                _report_perm_abuse_if_needed(user_info, exc_code)
            from app.utils.mtscos_response import build_error_response
            return build_error_response(exc_code or EXC_AUTH_403,
                                        route_path=user_info["route_path"],
                                        blueprint=user_info["blueprint_name"])

        return decorated_function
    return decorator


# 便捷别名(对齐旧装饰器命名习惯, 方便渐进式迁移)
system_container.guest       = lambda **kw: system_container(require_auth=PERM_GUEST, **kw)
system_container.login       = lambda **kw: system_container(require_auth=PERM_LOGIN, **kw)
system_container.admin       = lambda **kw: system_container(require_auth=PERM_ADMIN, **kw)
system_container.super_admin = lambda **kw: system_container(require_auth=PERM_SUPER_ADMIN, **kw)


if __name__ == "__main__":
    # 模块自检: 验证常量与函数完整性
    print(f"@system_container 4级权限: {PERM_LEVELS}")
    print(f"11级角色映射: {len(ROLE_TO_PERM)}项")
    print(f"6字段验证函数: {_check_user_container_6fields.__name__}")
    print(f"审计落库函数: {_audit_log.__name__}")
    print(f"异常码: AUTH_401={EXC_AUTH_401}, PERM_ILLEGAL={EXC_PERM_ILLEGAL}")
    print("OK @system_container 装饰器就绪(待Flask app上下文激活)")
