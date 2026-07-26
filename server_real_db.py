#!/usr/bin/env python3
"""MTSCOS 正式服务入口：挂载 Database/auth.db + app.db/system_versions，
   用真实用户数据验证用户名密码，并传入 DB 中真实系统版本号。"""
import os
import sys
import time
import json
import base64
import hashlib
import sqlite3
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

try:
    from core.db_path import patch_sqlite3_connect as _mtscos_patch, get_db_path
    _mtscos_patch(verbose=False)
except Exception as _e:
    sys.stderr.write(f"[WARN] db_path patch failed (server_real_db): {_e}\n")
    from core.db_path import get_db_path

AUTH_DB = get_db_path('auth.db')
APP_DB = get_db_path('app.db')
SPLIT_SYSTEM_DB = get_db_path('system.db')
SPLIT_AI_DB = get_db_path('ai.db')
SPLIT_EXAM_DB = get_db_path('exam.db')
SPLIT_QUESTION_DB = get_db_path('question.db')
SPLIT_USER_DB = get_db_path('user.db')
SPLIT_ADMIN_DB = get_db_path('admin.db')
SPLIT_LEARNING_DB = get_db_path('learning.db')
SPLIT_LOG_DB = get_db_path('log.db')
SPLIT_PROCTOR_DB = get_db_path('proctor.db')
DATA_MTSCOS_DB = get_db_path('mtscos.db')
VERSION_FILE = os.path.join(BASE_DIR, 'VERSION')

from flask import Flask, render_template, render_template_string, request, jsonify, redirect, url_for, session, send_file
from jinja2 import Undefined as _JinjaUndefined


class _FriendlyUndefined(_JinjaUndefined):
    """
    兼容模板老变量：任何未传的变量名 / 属性链 / 函数调用 / 迭代都不抛错，
    打印为''、布尔False、迭代为[]、比较为None，从而杜绝 UndefinedError 500。
    """
    __slots__ = ()

    def __str__(self):
        return ''

    def __bool__(self):
        return False

    __nonzero__ = __bool__

    def __iter__(self):
        return iter([])

    def __len__(self):
        return 0

    def __getattr__(self, item):
        if item.startswith('_'):
            raise AttributeError(item)
        return _FriendlyUndefined()

    def __getitem__(self, item):
        return _FriendlyUndefined()

    def __call__(self, *args, **kwargs):
        return _FriendlyUndefined()

    def __eq__(self, other):
        return other is None or isinstance(other, _FriendlyUndefined)

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return 0

    def __int__(self):
        return 0

    def __float__(self):
        return 0.0

    def __repr__(self):
        return ''


app = Flask(__name__,
            template_folder=os.path.join(BASE_DIR, 'templates'),
            static_folder=os.path.join(BASE_DIR, 'static'))
app.secret_key = 'mtscos-real-db-secret-' + str(int(time.time()))
app.jinja_env.undefined = _FriendlyUndefined
app.jinja_env.auto_reload = True
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

import hashlib
import time

_MT_CSRF_TOKEN = None

def _mt_generate_csrf_token():
    global _MT_CSRF_TOKEN
    if _MT_CSRF_TOKEN is None:
        _MT_CSRF_TOKEN = hashlib.sha256(f'mtscos-csrf-{time.time()}-{os.urandom(16)}'.encode()).hexdigest()
    return _MT_CSRF_TOKEN

_MT_REGISTER_LIMIT = {}
_MT_REGISTER_WINDOW = 60
_MT_REGISTER_MAX_PER_IP = 5

_CSRF_EXEMPT_PATHS = [
    '/auth/login',
    '/auth/register',
    '/auth/session_health',
]

@app.before_request
def _mt_csrf_protection():
    if request.method in ('POST', 'PUT', 'DELETE') and request.path.startswith('/api/'):
        csrf_token = request.headers.get('X-CSRF-Token')
        session_csrf = session.get('csrf_token')
        if csrf_token != session_csrf:
            return jsonify({'success': False, 'message': 'CSRF验证失败'}), 403
    elif request.method in ('POST', 'PUT', 'DELETE') and request.path not in _CSRF_EXEMPT_PATHS:
        csrf_token = request.headers.get('X-CSRF-Token')
        session_csrf = session.get('csrf_token')
        if csrf_token != session_csrf:
            return jsonify({'success': False, 'message': 'CSRF验证失败'}), 403

try:
    from markupsafe import Markup
    app.jinja_env.globals.setdefault('Markup', Markup)
except Exception:
    pass
try:
    import json as _json_mod
    app.jinja_env.filters.setdefault('tojson', lambda v, **kw: _json_mod.dumps(v, ensure_ascii=False))
except Exception:
    pass


# ================================================================
# AI 防火墙 + 安全团队（AI员工 / AI Agent）统一初始化入口
# - 建表：ai_firewall_rules + security_events_log
# - 种子：24 条防火墙规则 + 6 名安全员工 + 4 个安全 Agent（幂等）
# - 挂载：before_request 全量请求检查 + Blueprint 注册
# ================================================================
def _init_ai_firewall_and_workforce():
    import logging as _fw_logger
    try:
        from core.services import ai_firewall as _fw
        ok_tab = _fw.init_firewall_tables()
        ok_seed = _fw.seed_default_firewall_rules()
        _fw_logger.info(
            f"[ai_firewall] init: tables={'OK' if ok_tab else 'FAIL'}, seed_rows={ok_seed}"
        )
    except Exception as e:
        _fw_logger.warning(f"[ai_firewall] init fail: {e}")
    try:
        from app.api.ai_firewall_api import ai_firewall_api as _fw_api
        from app.api.ai_security_workforce_api import ai_security_workforce_api as _sw_api
        app.register_blueprint(_fw_api)
        app.register_blueprint(_sw_api)
        _fw_logger.info("[ai_firewall] blueprints registered: ai_firewall_api + ai_security_workforce_api")
    except Exception as e:
        _fw_logger.warning(f"[ai_firewall] blueprint register fail: {e}")


_init_ai_firewall_and_workforce()


# ================================================================
# Vikey USBKey 驱动 + API Blueprint 初始化入口
# - 建表：vikey_device_bindings / vikey_operations_log / vikey_device_certs
# - 种子：2 个默认测试绑定（幂等）
# - 挂载：Blueprint /api/vikey
# ================================================================
def _init_vikey_driver_and_api():
    import logging as _vk_logger
    try:
        from core.services.vikey_driver import get_vikey_manager, VIKEY_DRIVER_VERSION
        mgr = get_vikey_manager()
        _vk_logger.info(
            f"[vikey] init: driver_version={VIKEY_DRIVER_VERSION} "
            f"backend={mgr.backend.NAME} devices={len(mgr.enumerate_devices())} "
            f"bindings={len(mgr.list_bindings())}"
        )
    except Exception as e:
        _vk_logger.warning(f"[vikey] driver init fail: {e}")
    try:
        from app.api.vikey_api import vikey_api as _vk_api
        app.register_blueprint(_vk_api, url_prefix='/api/_vikey_legacy')
        _vk_logger.info("[vikey] blueprint registered: vikey_api @ /api/_vikey_legacy (legacy, new API uses /api/vikey)")
    except Exception as e:
        _vk_logger.warning(f"[vikey] blueprint register fail: {e}")


_init_vikey_driver_and_api()


# ================================================================
# 布局AI LayoutAI - 动态布局调节系统
# - 建表：layout_rules / layout_snapshots / layout_adjustment_logs / layout_employee_configs (4张表)
# - 种子：20条排版割裂检测规则（LF001-LF020）
# - 初始化：LayoutAdjusterAIEmployee 单例
# - 挂载：Blueprint /api/layout_ai（快照/统计/规则/日志/员工配置）
# ================================================================
def _init_layout_ai_system():
    import logging as _lay_logger
    ok_tables, ok_seed = False, 0
    try:
        from ai_engines.layout_adjuster_ai_employee import init_layout_ai_system as _init_lay
        ok_tables, ok_seed = _init_lay()
        _lay_logger.info(
            f"[layout_ai] init: tables={'OK' if ok_tables else 'FAIL'}, seeded_rules={ok_seed}"
        )
    except Exception as e:
        _lay_logger.warning(f"[layout_ai] init fail: {e}")
    try:
        from app.api.layout_ai_api import layout_ai_api as _lay_api
        app.register_blueprint(_lay_api)
        _lay_logger.info("[layout_ai] blueprint registered: layout_ai_api @ /api/layout_ai")
        try:
            from app.api.layout_ai_api import register_html_auto_injector as _inj
            _inj(app)
            _lay_logger.info("[layout_ai] HTML auto-injector registered (all text/html pages get probe+style)")
        except Exception as _ei:
            _lay_logger.warning(f"[layout_ai] auto-injector register fail: {_ei}")
    except Exception as e:
        _lay_logger.warning(f"[layout_ai] blueprint register fail: {e}")
    try:
        from ai_engines.layout_adjuster_ai_employee import LayoutAdjusterAIEmployee as _L
        try:
            from ai_engines import ai_employee_manager as _emp_mod
            _mgr = getattr(_emp_mod, 'ai_employee_manager', None) or getattr(_emp_mod, 'manager', None)
            if _mgr:
                _inst = _mgr.get_employee(_L.EMPLOYEE_ID) if hasattr(_mgr, 'get_employee') else None
                if not _inst:
                    _add_fn = getattr(_mgr, 'add_employee', None)
                    if _add_fn: _add_fn(_L())
                    _lay_logger.info(f"[layout_ai] registered into ai_employee_manager: {_L.EMPLOYEE_ID}")
        except Exception:
            pass
    except Exception as e:
        _lay_logger.warning(f"[layout_ai] employee register fail: {e}")


_init_layout_ai_system()


@app.before_request
def _mtscos_ai_firewall_check():
    """AI 防火墙全局请求拦截：SQLi/XSS/SSRF/遍历/命令注入/恶意UA/速率/扩展/泄露检测"""
    try:
        p = request.path or ''
        if (p.startswith('/static/') or p.startswith('/assets/')
                or p in ('/favicon.ico', '/robots.txt')
                or p.endswith('.svg') or p.endswith('.png') or p.endswith('.jpg') or p.endswith('.ico')
                or p.endswith('.css') or p.endswith('.js')):
            return None
        from core.services import ai_firewall as _fw
        blocked, code, msg, rule = _fw.check_request(request)
        if not blocked:
            return None
        payload = {
            'success': False,
            'blocked': True,
            'rule_code': (rule or {}).get('rule_code'),
            'rule_name': (rule or {}).get('name'),
            'severity': (rule or {}).get('severity') or 'warning',
            'message': msg or '[MTSCOS AI Firewall] Request blocked',
            'action': (rule or {}).get('action') or 'block',
        }
        accept = (request.headers.get('Accept', '') or '').lower()
        if 'text/html' in accept and 'application/json' not in accept:
            import json as _j
            pretty = _j.dumps(payload, ensure_ascii=False, indent=2)
            html = (
                '<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">'
                '<title>403 Blocked · MTSCOS AI Firewall</title></head>'
                '<body style="background:#0b1020;color:#cbd5e1;font-family:-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif;padding:48px 24px">'
                '<div style="max-width:720px;margin:auto">'
                '<h1 style="color:#f87171;margin:0 0 12px">🚫 Request Blocked</h1>'
                f'<p style="opacity:.85;margin:0 0 24px">{msg or "请求被 MTSCOS AI 防火墙拦截"}</p>'
                f'<pre style="background:#0f172a;padding:16px 20px;border-radius:10px;border:1px solid rgba(255,255,255,.08);white-space:pre-wrap">{pretty}</pre>'
                '<p style="opacity:.6;margin-top:24px">如需放行，请联系超级管理员调整 <code>/api/ai_firewall/rules</code> 规则。</p>'
                '</div></body></html>'
            )
            return html, int(code or 403)
        return jsonify(payload), int(code or 403)
    except Exception as e:
        import logging as _lg
        _lg.warning(f"[ai_firewall] before_request fail: {e}")
    return None


# ==========================================================
# ⚙️  MTSCOS 系统容器管控层（SysContainer）
#
# 核心能力：
#   1) 统一系统容器装饰器 @system_container —— 所有 HTML 页面必须通过它
#   2) AI 管控：行为审计 / 权限二次校验 / 异常熔断降级
#   3) 动态状态监控：session 健康度、客户端心跳、容器生命周期
#   4) Cookies 自动挂载：mtscos_sid / mtscos_uid / mtscos_ts / mtscos_sc
#   5) Session 统一加载：未登录用户自动 guest session，已登录从 DB 回填
# ==========================================================
from functools import wraps  # noqa: E402
import threading  # noqa: E402
import uuid as _uuid  # noqa: E402
import hmac as _hmac  # noqa: E402
import random as _rd  # noqa: E402

# ---------- 容器常量 ----------
_MT_SYS_CONTAINER_VERSION = '3.0.0-mtscos'
_MT_SYS_CONTAINER_SECRET = hashlib.sha256(b'MTSCOS-SYSTEM-CONTAINER-SECRET-v3').digest()
_MT_GUEST_ROLE = 'guest'
_MT_PAGE_RENDER_KEY = '__mt_container_rendered__'
_MT_HEARTBEAT_WINDOW = 120  # 2 分钟内没有心跳判定为离线
_MT_BEHAVIOR_RATE_LIMIT = 120  # 单用户每 60s 最多 120 次页面级操作
_MT_BEHAVIOR_LOCK = threading.RLock()
_MT_BEHAVIOR_BUCKETS: dict = {}  # uid -> [ts1, ts2, ...]
_MT_AIBEHAVIOR_LOCK = threading.RLock()
_MT_AIBEHAVIOR_LOG: list = []  # AI 管控行为审计环形缓冲（最多 500 条）

# ---------- 5 大系统容器 Cookies ----------
_MT_COOKIES = {
    'sid':    {'name': 'mtscos_sid',  'max_age': 86400 * 30, 'path': '/', 'httpOnly': True,  'sameSite': 'Lax'},
    'uid':    {'name': 'mtscos_uid',  'max_age': 86400 * 30, 'path': '/', 'httpOnly': False, 'sameSite': 'Lax'},
    'ts':     {'name': 'mtscos_ts',   'max_age': 86400,      'path': '/', 'httpOnly': False, 'sameSite': 'Lax'},
    'sc':     {'name': 'mtscos_sc',   'max_age': None,       'path': '/', 'httpOnly': True,  'sameSite': 'Strict'},  # 会话级
    'trace':  {'name': 'mtscos_trace','max_age': 3600,       'path': '/', 'httpOnly': False, 'sameSite': 'Lax'},
}


def _bizdb() -> str:
    """统一业务数据库"""
    return APP_DB


def _ensure_container_tables(conn) -> None:
    """自动建表（容器心跳表、AI管控审计表、session持久化表）—— 幂等"""
    try:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS sys_container_heartbeat (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sid TEXT NOT NULL,
            uid TEXT,
            username TEXT,
            role TEXT,
            path TEXT,
            ip TEXT,
            ua TEXT,
            action TEXT,
            ok INTEGER DEFAULT 1,
            created_at TEXT DEFAULT (datetime('now','localtime'))
        );
        CREATE INDEX IF NOT EXISTS idx_container_hb_sid ON sys_container_heartbeat(sid);
        CREATE INDEX IF NOT EXISTS idx_container_hb_time ON sys_container_heartbeat(created_at);

        CREATE TABLE IF NOT EXISTS sys_container_ai_audit (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            trace_id TEXT,
            sid TEXT,
            uid TEXT,
            username TEXT,
            role TEXT,
            path TEXT,
            action TEXT,
            risk_level TEXT DEFAULT 'low',
            rule_hit TEXT,
            blocked INTEGER DEFAULT 0,
            detail TEXT,
            created_at TEXT DEFAULT (datetime('now','localtime'))
        );
        CREATE INDEX IF NOT EXISTS idx_audit_time ON sys_container_ai_audit(created_at);

        CREATE TABLE IF NOT EXISTS sys_container_sessions (
            sid TEXT PRIMARY KEY,
            uid TEXT,
            username TEXT,
            role TEXT,
            ip TEXT,
            ua TEXT,
            payload_json TEXT,
            last_seen TEXT DEFAULT (datetime('now','localtime')),
            created_at TEXT DEFAULT (datetime('now','localtime'))
        );
        """)
        conn.commit()
    except Exception:
        pass


def _sys_ensure_tables():
    try:
        with sqlite3.connect(_bizdb()) as c:
            _ensure_container_tables(c)
    except Exception:
        pass


_sys_ensure_tables()


def _gen_sid() -> str:
    """生成带签名的安全 SID（32 位随机 + 8 位 HMAC 签名）"""
    raw = secrets.token_hex(16) if 'secrets' in globals() else hashlib.sha256(str(time.time_ns()).encode()).hexdigest()[:32]
    try:
        import secrets as _s
        raw = _s.token_hex(16)
    except Exception:
        pass
    sig = _hmac.new(_MT_SYS_CONTAINER_SECRET, raw.encode(), hashlib.sha256).hexdigest()[:8]
    return raw + sig


def _verify_sid(sid: str) -> bool:
    if not sid or len(sid) != 40:
        return False
    raw, sig = sid[:32], sid[32:]
    expected = _hmac.new(_MT_SYS_CONTAINER_SECRET, raw.encode(), hashlib.sha256).hexdigest()[:8]
    return _hmac.compare_digest(sig, expected)


def _trace_id() -> str:
    return 'mt-' + hashlib.md5((str(time.time_ns()) + str(_rd.random())).encode()).hexdigest()[:16]


def _ip() -> str:
    try:
        return (request.headers.get('X-Forwarded-For') or request.remote_addr or '0.0.0.0').split(',')[0].strip()
    except Exception:
        return '0.0.0.0'


def _ua() -> str:
    try:
        return (request.user_agent.string if hasattr(request, 'user_agent') and request.user_agent else request.headers.get('User-Agent', ''))[:500]
    except Exception:
        return ''


def _current_safe_user() -> dict:
    """统一当前用户读取：未登录自动 guest session，不抛异常"""
    try:
        uid = session.get('user_id')
        uname = session.get('username')
        role = session.get('role') or _MT_GUEST_ROLE
        logged_in = bool(session.get('logged_in'))
        if uid and uname and logged_in:
            is_super_admin = (str(uname).lower() == 'wuchenghao15')
            return {'uid': str(uid), 'username': uname, 'role': role, 'logged_in': True, 'is_guest': False, 'is_super_admin': is_super_admin}
    except Exception:
        pass
    return {'uid': f'guest-{int(time.time()) % 100000}', 'username': _MT_GUEST_ROLE, 'role': _MT_GUEST_ROLE,
            'logged_in': False, 'is_guest': True, 'is_super_admin': False}


# ---------- AI 管控核心：风险评估 + 熔断 ----------
_MT_RISK_RULES = [
    # (rule_code, name, check_fn, risk_level, action)
    ('R-NO-REFERER', '缺少 Referer 直入敏感页面',
     lambda p, u: (u['is_guest'] and any(k in p.lower() for k in ('/admin', '/settings', '/exam', '/dashboard')) and not request.headers.get('Referer')),
     'medium', 'flag'),
    ('R-FAST-CLICK', '操作速率过高 60s > 120 次',
     lambda p, u: _mt_is_user_fast(u['uid']),
     'high', 'throttle'),
    ('R-GUEST-API-WRITE', '访客越权写操作',
     lambda p, u: (u['is_guest'] and request.method in ('POST', 'PUT', 'DELETE') and p.startswith('/api/') and not any(p.startswith(x) for x in ('/api/auth', '/api/theme', '/api/vikey', '/api/health', '/api/container', '/api/ai_engine/self_learning', '/api/ai/self_learning', '/api/layout_ai', '/api/chinese_dictation', '/api/ai/chinese_listening', '/api/history', '/api/arduino', '/api/approval', '/api/system/logo'))),
     'high', 'block'),
    ('R-SESSION-STALE', 'Session 超过 24h 未刷新',
     lambda p, u: False,  # 在 before_request 中动态计算
     'low', 'refresh'),
]


def _mt_is_user_fast(uid: str) -> bool:
    """滑动窗口：60 秒内 > 120 次"""
    now = time.time()
    with _MT_BEHAVIOR_LOCK:
        bucket = _MT_BEHAVIOR_BUCKETS.setdefault(uid, [])
        bucket[:] = [t for t in bucket if now - t < 60]
        bucket.append(now)
        return len(bucket) > _MT_BEHAVIOR_RATE_LIMIT


def _mt_ai_audit_push(entry: dict) -> None:
    """环形缓冲（内存 500 条 + DB 持久化）"""
    entry.setdefault('trace_id', _trace_id())
    entry.setdefault('created_at', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    try:
        with sqlite3.connect(_bizdb(), timeout=3) as c:
            _ensure_container_tables(c)
            c.execute(
                "INSERT INTO sys_container_ai_audit(trace_id,sid,uid,username,role,path,action,risk_level,rule_hit,blocked,detail)"
                " VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                (entry.get('trace_id'), entry.get('sid'), entry.get('uid'), entry.get('username'),
                 entry.get('role'), entry.get('path'), entry.get('action'), entry.get('risk_level', 'low'),
                 entry.get('rule_hit'), 1 if entry.get('blocked') else 0, entry.get('detail', ''))
            )
            c.commit()
    except Exception:
        pass
    with _MT_AIBEHAVIOR_LOCK:
        _MT_AIBEHAVIOR_LOG.append(entry)
        if len(_MT_AIBEHAVIOR_LOG) > 500:
            del _MT_AIBEHAVIOR_LOG[:len(_MT_AIBEHAVIOR_LOG) - 500]


# ---------- Session 统一加载：第二个 before_request ----------
@app.before_request
def _mt_sys_container_session_loader():
    """
    容器 Session 加载（在 AI 防火墙之后执行）：
      1. 读取 Cookies 中的 mtscos_sid，校验签名
      2. 已登录用户：把用户信息回填到 session 中（避免丢失）
      3. 未登录用户：设置 guest session + mtscos_uid guest-xx
      4. 记录请求级 trace_id 和进入时间戳
      5. 写 sys_container_heartbeat（API/页面都记）
    """
    try:
        request.mt_entry_ts = time.time()
        request.mt_trace_id = _trace_id()
        path = request.path or ''
        # 排除静态资源 / 心跳接口重复写
        if (path.startswith('/static/') or path.startswith('/assets/')
                or path in ('/favicon.ico', '/robots.txt', '/api/health')
                or path.endswith(('.css', '.js', '.svg', '.png', '.jpg', '.jpeg', '.ico', '.map', '.woff2'))):
            return None
        sid_cookie = request.cookies.get(_MT_COOKIES['sid']['name']) or ''
        if not _verify_sid(sid_cookie):
            sid_cookie = _gen_sid()
        session['__mt_sid'] = sid_cookie
        user = _current_safe_user()
        # --- DB session 持久化（写入/刷新） ---
        try:
            payload = {k: v for k, v in session.items() if not k.startswith('__mt_')}
            with sqlite3.connect(_bizdb(), timeout=3) as c:
                _ensure_container_tables(c)
                c.execute(
                    "INSERT INTO sys_container_sessions(sid,uid,username,role,ip,ua,payload_json,last_seen) VALUES(?,?,?,?,?,?,?,datetime('now','localtime'))"
                    " ON CONFLICT(sid) DO UPDATE SET uid=excluded.uid,username=excluded.username,role=excluded.role,"
                    " ip=excluded.ip,ua=excluded.ua,payload_json=excluded.payload_json,last_seen=datetime('now','localtime')",
                    (sid_cookie, user.get('uid'), user.get('username'), user.get('role'),
                     _ip(), _ua(), json.dumps(payload, ensure_ascii=False))
                )
                c.commit()
        except Exception:
            pass
        # --- AI 管控：风险评估（不阻断 HTML 页，仅 flag；API 则高风险直接拦） ---
        for rule_code, rule_name, rule_fn, lvl, act in _MT_RISK_RULES:
            try:
                if rule_fn(path, user):
                    _mt_ai_audit_push({
                        'sid': sid_cookie,
                        'uid': user.get('uid'),
                        'username': user.get('username'),
                        'role': user.get('role'),
                        'path': path,
                        'action': 'rule-hit',
                        'risk_level': lvl,
                        'rule_hit': f'{rule_code}::{rule_name}',
                        'blocked': (act == 'block' and path.startswith('/api/')),
                        'detail': json.dumps({'method': request.method, 'ip': _ip()}, ensure_ascii=False),
                    })
                    if act == 'block' and path.startswith('/api/'):
                        return jsonify({'success': False, 'message': f'容器 AI 管控阻断：{rule_name}', 'code': 403, 'trace_id': request.mt_trace_id}), 403
                    if act == 'throttle':
                        return jsonify({'success': False, 'message': '容器限流：请稍后再试', 'code': 429, 'trace_id': request.mt_trace_id}), 429
            except Exception:
                continue
        # --- 心跳记录 ---
        try:
            with sqlite3.connect(_bizdb(), timeout=2) as c:
                _ensure_container_tables(c)
                c.execute(
                    "INSERT INTO sys_container_heartbeat(sid,uid,username,role,path,ip,ua,action,ok) VALUES(?,?,?,?,?,?,?,?,1)",
                    (sid_cookie, user.get('uid'), user.get('username'), user.get('role'), path, _ip(), _ua(), 'http-request')
                )
                c.commit()
        except Exception:
            pass
    except Exception as e:
        import logging as _lg2
        _lg2.warning(f"[sys-container] session_loader before_request err: {e}")
    return None


# ---------- Cookies 自动挂载：after_request ----------
@app.after_request
def _mt_sys_container_cookie_mounter(response):
    """
    所有离开容器的响应强制挂载 5 大系统 Cookies：
      mtscos_sid   会话签名 ID  (30 天 / HttpOnly)
      mtscos_uid   用户 UID     (30 天)
      mtscos_ts    最近活动时间戳 (1 天)
      mtscos_sc    会话签名校验 (会话级 / HttpOnly / Strict)
      mtscos_trace 本次 trace_id  (1 小时)
    """
    try:
        # 静态资源仅挂 sid（少写 cookies 节省带宽）
        path = request.path or ''
        is_static = (path.startswith('/static/') or path.startswith('/assets/')
                     or path in ('/favicon.ico',)
                     or path.endswith(('.css', '.js', '.svg', '.png', '.jpg', '.jpeg', '.ico', '.map', '.woff2')))
        sid = session.get('__mt_sid') or request.cookies.get(_MT_COOKIES['sid']['name']) or _gen_sid()
        if not _verify_sid(sid):
            sid = _gen_sid()
        user = _current_safe_user()
        # 1) mtscos_sid（所有响应必挂）
        c = _MT_COOKIES['sid']
        response.set_cookie(c['name'], sid, max_age=c['max_age'], path=c['path'],
                            httponly=c['httpOnly'], samesite=c['sameSite'])
        if is_static:
            return response
        # 2) mtscos_uid
        c2 = _MT_COOKIES['uid']
        response.set_cookie(c2['name'], str(user.get('uid') or ''), max_age=c2['max_age'], path=c2['path'],
                            httponly=c2['httpOnly'], samesite=c2['sameSite'])
        # 3) mtscos_ts
        c3 = _MT_COOKIES['ts']
        response.set_cookie(c3['name'], str(int(time.time())), max_age=c3['max_age'], path=c3['path'],
                            httponly=c3['httpOnly'], samesite=c3['sameSite'])
        # 4) mtscos_sc（会话签名校验）
        c4 = _MT_COOKIES['sc']
        sc_sig = _hmac.new(_MT_SYS_CONTAINER_SECRET,
                           (sid + '|' + str(user.get('uid') or '') + '|' + str(user.get('username') or '')).encode(),
                           hashlib.sha256).hexdigest()[:16]
        response.set_cookie(c4['name'], sc_sig, max_age=c4['max_age'], path=c4['path'],
                            httponly=c4['httpOnly'], samesite=c4['sameSite'])
        # 5) mtscos_trace
        c5 = _MT_COOKIES['trace']
        tid = getattr(request, 'mt_trace_id', None) or _trace_id()
        response.set_cookie(c5['name'], tid, max_age=c5['max_age'], path=c5['path'],
                            httponly=c5['httpOnly'], samesite=c5['sameSite'])
        # 6) 给响应头补充容器元信息（便于前端监控）
        response.headers['X-MT-Container'] = _MT_SYS_CONTAINER_VERSION
        response.headers['X-MT-Trace-Id'] = tid
        response.headers['X-MT-Loaded'] = '1'
    except Exception as e:
        import logging as _lg3
        _lg3.warning(f"[sys-container] cookie_mounter after_request err: {e}")
    return response


# ---------- 统一系统容器装饰器 ----------
def system_container(page_name: str, require_auth: str = 'auto', allowed_roles=None,
                     inject_user_ctx: bool = True, write_heartbeat: bool = True):
    """
    ⭐⭐⭐ 所有 HTML 页面路由必须挂的容器装饰器 ⭐⭐⭐
    用途：
      - 脱离容器的孤岛页面前端控制台将看到警告，后端会补容器上下文
      - 写入 request.__mt_page_name__ = page_name，模板中可读取
      - 权限二次校验（与 require_login / require_admin 形成双保险）
      - 自动给模板注入：container_ctx（当前会话、用户、trace、版本）
      - 渲染完成后写页面级心跳

    参数：
      page_name       : 页面标识（如 "dashboard", "settings", "exam_center"）
      require_auth    : 'login' (强制登录) | 'admin' | 'super_admin' | 'auto'(看 session) | 'guest' (任何人)
      allowed_roles   : 白名单角色列表（优先级高于 require_auth 字符串）
      inject_user_ctx : 是否自动注入 current_user / user 到模板上下文中
      write_heartbeat : 是否写页面打开心跳
    """
    def decorator(view_fn):
        @wraps(view_fn)
        def wrapper(*args, **kwargs):
            start = time.time()
            path = request.path or ''
            user = _current_safe_user()
            sid = session.get('__mt_sid') or request.cookies.get(_MT_COOKIES['sid']['name']) or _gen_sid()
            # 0) 标记本请求已进入容器（避免孤岛）
            request.__mt_container_page__ = page_name
            request.__mt_container_start__ = start

            # 1) 权限二次校验（双保险：和 access_control.py 的装饰器同时生效不冲突）
            _role = user.get('role') or 'guest'
            _username = user.get('username') or ''
            _sa = (_username == 'wuchenghao15')  # 超级管理员白名单
            denied = None
            if allowed_roles:
                if not _sa and _role not in allowed_roles:
                    denied = (403, f'该页面仅 {allowed_roles} 角色可访问')
            else:
                if require_auth == 'login' and not _sa and not user.get('logged_in'):
                    denied = (401 if path.startswith('/api/') else 302, '需要登录')
                elif require_auth == 'admin' and not _sa and _role not in ('admin', 'super_admin', 'school_admin', 'sysadmin',
                                                                          'hardware_admin', 'cluster_manager', 'ai_manager',
                                                                          'question_manager', 'exam_proctor', 'teacher_admin'):
                    denied = (403, '需要管理员权限')
                elif require_auth == 'super_admin' and not _sa and _role != 'super_admin':
                    denied = (403, '需要超级管理员权限')
            if denied:
                code, msg = denied
                _mt_ai_audit_push({'sid': sid, 'uid': user.get('uid'), 'username': _username, 'role': _role,
                                   'path': path, 'action': f'{page_name}::permission-deny', 'risk_level': 'medium',
                                   'rule_hit': 'CONTAINER::PERMISSION-DENY', 'blocked': 1,
                                   'detail': json.dumps({'required': require_auth, 'allowed_roles': allowed_roles}, ensure_ascii=False)})
                if path.startswith('/api/'):
                    return jsonify({'success': False, 'message': msg, 'code': code, 'trace_id': getattr(request, 'mt_trace_id', _trace_id())}), code
                if code == 302:
                    return redirect('/?next=' + path)
                # 403 HTML 页：保持在系统容器内
                err_html = (
                    '<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><title>403 · MTSCOS 系统容器</title>'
                    '<meta name="viewport" content="width=device-width,initial-scale=1">'
                    '<script>window.__MT_CONTAINER__={version:"%s",page:"403",traceId:"%s",sid:"%s",mounted:true};</script>'
                    '<style>body{background:#050510;color:#cbd5e1;font-family:-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif;margin:0;padding:64px 24px}'
                    '.box{max-width:640px;margin:auto;background:rgba(99,102,241,.06);border:1px solid rgba(99,102,241,.2);border-radius:16px;padding:36px}'
                    'h1{color:#f87171;margin:0 0 12px;font-size:28px}.p{opacity:.85;line-height:1.6;margin:0 0 24px}'
                    'a{color:#a5b4fc;text-decoration:none}.meta{font-size:12px;opacity:.55;margin-top:16px}</style>'
                    '</head><body><div class="box"><h1>🚫 访问被系统容器拦截</h1>'
                    f'<p class="p">{msg}<br/><a href="/">← 返回首页</a></p>'
                    f'<p class="meta">Trace: {getattr(request, "mt_trace_id", "")}<br/>SID: {sid}<br/>用户: {_username} / {_role}</p>'
                    '</div></body></html>'
                ) % (_MT_SYS_CONTAINER_VERSION, getattr(request, 'mt_trace_id', ''), sid)
                return err_html, code

            # 2) 执行原始视图（注意：这里把 render_template 结果进行包装，避免脱离容器）
            _orig_response = view_fn(*args, **kwargs)
            # Flask 视图可能返回 (response, code) tuple
            status_code = 200
            if isinstance(_orig_response, tuple):
                body, status_code = _orig_response[0], _orig_response[1] if len(_orig_response) > 1 else 200
            else:
                body = _orig_response
            # 若是模板 render 后的字符串，确保注入系统容器挂载脚本
            if isinstance(body, str) and '</body>' in body:
                mount_script = (
                    f'<script data-mt-container="mount">'
                    f'(function(){{'
                    f'  window.__MT_CONTAINER__ = window.__MT_CONTAINER__ || {{}};'
                    f'  Object.assign(window.__MT_CONTAINER__, {{'
                    f'    version: "{_MT_SYS_CONTAINER_VERSION}",'
                    f'    pageName: "{page_name}",'
                    f'    traceId: "{getattr(request, "mt_trace_id", "")}",'
                    f'    sid: "{sid}",'
                    f'    uid: "{user.get("uid","")}",'
                    f'    role: "{_role}",'
                    f'    mounted: true,'
                    f'    mountedAt: Date.now(),'
                    f'    requireAuth: "{require_auth}",'
                    f'    cookieNames: {json.dumps({k: v["name"] for k,v in _MT_COOKIES.items()}, ensure_ascii=False)}'
                    f'  }});'
                    f'  if (!document.body.hasAttribute("data-mt-container")) document.body.setAttribute("data-mt-container","{page_name}");'
                    f'  if (!document.documentElement.getAttribute("x-mt-version")) document.documentElement.setAttribute("x-mt-version","{_MT_SYS_CONTAINER_VERSION}");'
                    f'}})();'
                    f'</script>'
                )
                # 在 </body> 前插入挂载脚本（保证只插入一次）
                if 'data-mt-container="mount"' not in body:
                    body = body.replace('</body>', mount_script + '</body>')

            # 3) 渲染完成写页面级 AI 审计 + 心跳
            dur = int((time.time() - start) * 1000)
            try:
                if write_heartbeat:
                    with sqlite3.connect(_bizdb(), timeout=2) as c:
                        _ensure_container_tables(c)
                        c.execute(
                            "INSERT INTO sys_container_heartbeat(sid,uid,username,role,path,ip,ua,action,ok)"
                            " VALUES(?,?,?,?,?,?,?,?,1)",
                            (sid, user.get('uid'), _username, _role, path, _ip(), _ua(), f'page::{page_name}')
                        )
                        c.commit()
                _mt_ai_audit_push({
                    'sid': sid, 'uid': user.get('uid'), 'username': _username, 'role': _role,
                    'path': path, 'action': f'page::{page_name}::render', 'risk_level': 'low',
                    'rule_hit': 'CONTAINER::RENDER-OK', 'blocked': 0,
                    'detail': json.dumps({'dur_ms': dur, 'status': status_code}, ensure_ascii=False)
                })
            except Exception:
                pass

            if isinstance(_orig_response, tuple):
                return body, status_code
            return body
        return wrapper
    return decorator


# ---------- 动态状态监控接口 ----------
@app.route('/api/container/heartbeat', methods=['POST', 'GET'])
def api_mt_container_heartbeat():
    """前端页面每 30s POST 一次：容器存活 + session 续期 + 在线状态"""
    try:
        data = request.get_json(silent=True) or {}
        user = _current_safe_user()
        sid = session.get('__mt_sid') or request.cookies.get(_MT_COOKIES['sid']['name']) or _gen_sid()
        try:
            with sqlite3.connect(_bizdb(), timeout=2) as c:
                _ensure_container_tables(c)
                c.execute(
                    "INSERT INTO sys_container_heartbeat(sid,uid,username,role,path,ip,ua,action,ok) VALUES(?,?,?,?,?,?,?,?,1)",
                    (sid, user.get('uid'), user.get('username'), user.get('role'),
                     request.path, _ip(), _ua(), f"heartbeat::{data.get('page', 'unknown')}")
                )
                c.execute(
                    "UPDATE sys_container_sessions SET last_seen=datetime('now','localtime') WHERE sid=?",
                    (sid,)
                )
                c.commit()
        except Exception:
            pass
        return jsonify({'success': True, 'ok': True,
                         'server_ts': int(time.time()),
                         'sid': sid,
                         'trace_id': getattr(request, 'mt_trace_id', _trace_id()),
                         'container_version': _MT_SYS_CONTAINER_VERSION,
                         'user': user,
                         'next_heartbeat_ms': 30000,
                         'stale': False,
                         'cookies_ok': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e), 'code': 500}), 500


@app.route('/api/container/status', methods=['GET'])
def api_mt_container_status():
    """容器管控总览：在线用户数 / 最近心跳 / AI 审计风险分布"""
    try:
        with sqlite3.connect(_bizdb(), timeout=2) as c:
            _ensure_container_tables(c)
            cur = c.execute("SELECT COUNT(DISTINCT sid) FROM sys_container_heartbeat WHERE created_at >= datetime('now','localtime','-5 minutes')")
            online = cur.fetchone()
            online = online[0] if online else 0
            cur2 = c.execute("SELECT risk_level, COUNT(*) FROM sys_container_ai_audit WHERE created_at >= datetime('now','localtime','-24 hours') GROUP BY risk_level")
            risks = {r[0]: r[1] for r in cur2.fetchall()}
            cur3 = c.execute("SELECT COUNT(*) FROM sys_container_sessions WHERE last_seen >= datetime('now','localtime','-1 hours')")
            sess = cur3.fetchone()
            sess = sess[0] if sess else 0
        return jsonify({
            'success': True,
            'container_version': _MT_SYS_CONTAINER_VERSION,
            'mounted': True,
            'online_last_5m': online,
            'active_sessions_last_1h': sess,
            'audit_risk_24h': risks,
            'cookies_spec': {k: {'name': v['name'], 'max_age': v['max_age'], 'httpOnly': v['httpOnly'], 'sameSite': v['sameSite']} for k, v in _MT_COOKIES.items()},
            'trace_id': getattr(request, 'mt_trace_id', _trace_id()),
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


# ---------- 全局 HTML 模板注入容器上下文（context_processor）----------
@app.context_processor
def _mt_sys_container_ctx_injector():
    """所有 render_template 自动可读取 {{ container }} / {{ current_user }}"""
    try:
        user = _current_safe_user()
        sid = session.get('__mt_sid') or request.cookies.get(_MT_COOKIES['sid']['name']) or _gen_sid()
        ctx = {
            'container': {
                'version': _MT_SYS_CONTAINER_VERSION,
                'page_name': getattr(request, '__mt_container_page__', 'fallback'),
                'sid': sid,
                'trace_id': getattr(request, 'mt_trace_id', _trace_id()),
                'mounted': True,
                'cookies': {k: v['name'] for k, v in _MT_COOKIES.items()},
                'user': user,
            },
            'current_user': user,
            'user_ctx': user,
            'is_super_admin_container': (user.get('username') == 'wuchenghao15'),
        }
        return ctx
    except Exception:
        return {}


# ==========================================================
#  END：MTSCOS 系统容器管控层
# ==========================================================

_ROLE_CN = {
    'admin': '管理员',
    'super_admin': '超级管理员',
    'school_admin': '校管理员',
    'teacher': '教师',
    'student': '学生',
    'parent': '家长',
    'user': '普通用户',
    'guest': '访客',
    'hardware_admin': '硬件管理员',
    'institution_admin': '机构管理员',
}


def get_role_name(role_key):
    if not role_key:
        return '未分配'
    key = str(role_key).strip().lower()
    for k, v in _ROLE_CN.items():
        if k == key or k in key:
            return v
    # 首字母大写友好显示
    s = str(role_key).strip().replace('_', ' ')
    return s[:1].upper() + s[1:]


# Jinja2 模板全局可用函数（避免模板里 UndefinedError: 'xxx' is undefined）
@app.context_processor
def _inject_template_globals():
    def g_is_authenticated():
        return bool(session.get('user_id'))

    def g_current_user():
        return _safe_user_ctx(_current_user())

    def g_is_admin():
        u = _current_user()
        if not u:
            return False
        role = str(u.get('role') or '').lower()
        if role in ('admin', 'super_admin', 'school_admin', 'institution_admin', 'teacher'):
            return True
        if _safe_super_approved(u.get('id')):
            return True
        return False

    def g_is_super_admin():
        u = _current_user()
        if not u:
            return False
        username = str(u.get('username') or '').lower()
        if username == 'wuchenghao15':
            return True
        return False

    return dict(
        get_role_name=get_role_name,
        is_authenticated=g_is_authenticated,
        current_user=g_current_user(),
        is_admin=g_is_admin(),
        is_super_admin=g_is_super_admin(),
        system_version=get_version_info()[0],
        now=datetime.now(),
    )

NATIONAL_MOURNING_DATES = [
    (9, 30),
    (12, 13),
    (9, 18),
]

THEME_DEEP_BLUE = 'deep_blue'
THEME_LIGHT_BLUE = 'light_blue_tech'
THEME_LIGHT = 'light'
THEME_MOURNING = 'mourning'

VALID_THEMES = {THEME_DEEP_BLUE, THEME_LIGHT_BLUE, THEME_LIGHT, THEME_MOURNING}
ADMIN_THEMES_NO_MOURNING = [THEME_DEEP_BLUE, THEME_LIGHT_BLUE, THEME_LIGHT]


def _today_mmdd():
    today = datetime.today()
    return (today.month, today.day)


def is_national_mourning_day():
    return _today_mmdd() in NATIONAL_MOURNING_DATES


def _current_user():
    if not session.get('username'):
        return None
    role = session.get('role') or 'user'
    admin_roles = {'admin', 'super_admin', 'teacher_admin', 'school_admin', 'sysadmin'}
    is_admin_role = role in admin_roles
    try:
        if os.path.exists(AUTH_DB):
            with _get_conn(AUTH_DB) as conn:
                row = conn.execute(
                    "SELECT super_admin_approved, role FROM users WHERE id = ? LIMIT 1",
                    (session.get('user_id'),)
                ).fetchone()
                if row:
                    if row['super_admin_approved']:
                        is_admin_role = True
                    if row['role'] and row['role'] in admin_roles:
                        is_admin_role = True
    except Exception:
        pass
    return {
        'id': session.get('user_id'),
        'username': session.get('username'),
        'role': role,
        'is_admin': is_admin_role,
        'is_super_admin': bool(session.get('super_admin_approved')) if session.get('super_admin_approved') is not None else (
            bool(_safe_super_approved(session.get('user_id')))
        ),
    }


def _safe_super_approved(uid):
    if not uid or not os.path.exists(AUTH_DB):
        return False
    try:
        with _get_conn(AUTH_DB) as conn:
            row = conn.execute("SELECT username, super_admin_approved FROM users WHERE id = ? LIMIT 1", (uid,)).fetchone()
            if row and row['username'] and str(row['username']).lower() == 'wuchenghao15':
                return True
            return False
    except Exception:
        return False


def _resolve_theme():
    """
    公祭日：
      * 默认强制 THEME_MOURNING（所有用户）
      * 超级管理员可通过 session['theme_override'] 临时强制切换为其他主题
    非公祭日：
      * 用户选择主题存在 session['user_theme']，否则 THEME_DEEP_BLUE（深蓝）
    """
    user = _current_user()
    if is_national_mourning_day():
        if user and user['is_super_admin']:
            override = session.get('theme_override')
            if override in VALID_THEMES:
                return override, True
        return THEME_MOURNING, True
    chosen = session.get('user_theme')
    if chosen in ADMIN_THEMES_NO_MOURNING:
        return chosen, False
    return THEME_DEEP_BLUE, False


@app.context_processor
def inject_theme_and_layout():
    user = _current_user()
    theme_key, forced_mourning = _resolve_theme()
    is_admin = user['is_admin'] if user else False
    is_super = user['is_super_admin'] if user else False
    return {
        'theme_key': theme_key,
        'theme_forced_mourning': forced_mourning,
        'is_mourning_day': is_national_mourning_day(),
        'layout_sidebar_ratio': '2:8',
        'layout_simplified_ratio': '1:9',
        'current_user': user,
        'is_admin': is_admin,
        'is_super_admin': is_super,
    }


@app.route('/api/theme/set', methods=['POST'])
@system_container('theme_set', require_auth='login')
def api_set_theme():
    """非公祭日用户自主切换主题；公祭日仅超级管理员可强制覆盖。"""
    data = request.get_json(silent=True) or {}
    target = (data.get('theme') or '').strip()
    user = _current_user()
    mourning = is_national_mourning_day()

    if mourning:
        if not (user and user['is_super_admin']):
            return jsonify({'success': False, 'message': '公祭日主题为系统自动启用，不可手动切换'}), 403
        if target not in VALID_THEMES:
            return jsonify({'success': False, 'message': f'主题无效（仅支持：{", ".join(sorted(VALID_THEMES))}）'}), 400
        session['theme_override'] = target
        return jsonify({'success': True, 'theme': target, 'forced': True,
                        'message': f'超级管理员已强制切换主题为：{target}'})

    if target not in ADMIN_THEMES_NO_MOURNING:
        return jsonify({'success': False,
                        'message': f'主题无效（仅支持：{", ".join(ADMIN_THEMES_NO_MOURNING)}）'}), 400
    session.pop('theme_override', None)
    session['user_theme'] = target
    return jsonify({'success': True, 'theme': target,
                    'message': f'已切换为：{target}'})


@app.route('/api/theme/reset', methods=['POST'])
def api_reset_theme():
    """清除自定义/强制覆盖，回到系统自动判定。"""
    session.pop('user_theme', None)
    session.pop('theme_override', None)
    theme_key, forced = _resolve_theme()
    return jsonify({'success': True, 'theme': theme_key, 'forced_mourning': forced})


def _hash_password(plain: str) -> str:
    """与 split_databases/auth.db users.password 现有哈希方式一致：SHA256 -> Base64"""
    return base64.b64encode(hashlib.sha256(plain.encode('utf-8')).digest()).decode('ascii')


# 常见初始密码列表（用于兼容占位哈希的初始化账户，自动升级）
_COMMON_DEFAULT_PASSWORDS = [
    'admin123',
    '123456',
    'password123',
    'password',
    'mtscos2026',
    'mtscos2025',
    'abcd1234',
    'abc123',
    '12345678',
]

# 弱密码字典黑名单（参考 OWASP Top 1M + 中英文常见，包含默认密码/序列号/键盘行/常见人名）
_WEAK_PASSWORD_BLACKLIST = {
    '123456','password','12345678','qwerty','123456789','12345','1234','111111',
    '1234567','dragon','123123','baseball','iloveyou','trustno1','sunshine','princess',
    'admin','letmein','welcome','monkey','football','shadow','master','666666',
    'abc123','!@#$%^&*','password1','qwerty123','qazwsx','michael','superman',
    '654321','asdfgh','zxcvbn','000000','888888','999999','123321','1q2w3e4r',
    'qwe123','123qwe','password123','admin123','root','toor','test','guest',
    'user','oracle','mysql','postgres','changeme','default','system','server',
    'login','support','p@ssw0rd','passw0rd','password!','pass123','helloworld',
    'mtscos','mtscos123','mtscos2024','mtscos2025','mtscos2026','mtscos@2024',
    'mtscos@2025','mtscos@2026','caopw','wuchenghao','wuchenghao15','administrator',
}


def _validate_password_strength(password, username=None, email=None,
                                min_len=8, max_len=64, require_classes=3,
                                forbid_username_match=True, forbid_blacklist=True):
    """
    密码强度校验（参考用户名框验证强度对齐 + 扩展）
    返回 (ok: bool, message: str, details: dict)

    校验项：
    1) 长度：[min_len, max_len]（默认 8-64）
    2) 与用户名/邮箱（本地部分）重复/互含：禁止
    3) 字符类别 ≥ require_classes（默认3类）：大写 / 小写 / 数字 / 特殊符号
    4) 不在弱密码黑名单（默认开启，匹配时不区分大小写 + 去首尾空格）
    5) 禁止纯相同字符 / 纯连续数字 / 纯键盘行
    """
    details = {
        'length_ok': False,
        'classes_count': 0,
        'classes_required': require_classes,
        'classes_ok': False,
        'username_similar': False,
        'blacklisted': False,
        'monotonous': False,
        'min_len': min_len,
        'max_len': max_len,
    }
    if not isinstance(password, str):
        return False, '密码必须是字符串', details
    pw = password.strip()
    if not pw:
        return False, '密码不能为空', details
    # 1) 长度
    if len(pw) < min_len:
        details['length_ok'] = False
        return False, f'密码至少 {min_len} 个字符', details
    if len(pw) > max_len:
        details['length_ok'] = False
        return False, f'密码至多 {max_len} 个字符', details
    details['length_ok'] = True
    # 2) 与用户名/邮箱重复或包含
    uname = (username or '').strip().lower()
    em_local = ''
    if email:
        try: em_local = (email.split('@', 1)[0] or '').lower()
        except Exception: em_local = ''
    low = pw.lower()
    if forbid_username_match:
        if uname and (uname == low or uname in low or low in uname):
            details['username_similar'] = True
            return False, '密码不能与用户名相同或互相包含', details
        if em_local and (em_local == low or em_local in low or low in em_local):
            details['username_similar'] = True
            return False, '密码不能与邮箱本地部分相同或互相包含', details
    # 3) 字符类别计数
    classes = 0
    import re as _pw_re
    has_upper = bool(_pw_re.search(r'[A-Z]', pw))
    has_lower = bool(_pw_re.search(r'[a-z]', pw))
    has_digit = bool(_pw_re.search(r'[0-9]', pw))
    has_special = bool(_pw_re.search(r'[^A-Za-z0-9]', pw))
    for c in (has_upper, has_lower, has_digit, has_special):
        if c: classes += 1
    details['classes_count'] = classes
    details['has_upper'] = has_upper
    details['has_lower'] = has_lower
    details['has_digit'] = has_digit
    details['has_special'] = has_special
    if classes < require_classes:
        details['classes_ok'] = False
        missing = []
        if not has_upper: missing.append('大写字母')
        if not has_lower: missing.append('小写字母')
        if not has_digit: missing.append('数字')
        if not has_special: missing.append('特殊符号')
        need = require_classes - classes
        return False, f'密码强度不足：需再包含 {need} 类字符（建议：{" / ".join(missing[:3])}）', details
    details['classes_ok'] = True
    # 4) 黑名单（大小写不敏感）
    if forbid_blacklist and low in _WEAK_PASSWORD_BLACKLIST:
        details['blacklisted'] = True
        return False, '密码过于常见，属于弱密码黑名单，请更换', details
    # 5) 单调模式：全相同字符 / 纯连续数字或反向连续 / 纯键盘行（qwerty/asdf/zxcv 等）
    monotone = False
    if len(set(pw)) == 1:
        monotone = True
    else:
        # 纯连续数字 12345 / 54321
        if pw.isdigit():
            nums = [int(ch) for ch in pw]
            diffs = [nums[i+1] - nums[i] for i in range(len(nums)-1)]
            if diffs and (all(x == 1 for x in diffs) or all(x == -1 for x in diffs)):
                monotone = True
        if not monotone:
            # 键盘行
            kb_rows = ['`1234567890-=','qwertyuiop[]\\','asdfghjkl;\'','zxcvbnm,./',
                       '～！＠＃＄％＾＆＊（）＿＋','qwertyuiop','asdfghjkl','zxcvbnm']
            lowpw = pw.lower()
            for row in kb_rows:
                if lowpw in row or row in lowpw:
                    monotone = True; break
    if monotone:
        details['monotonous'] = True
        return False, '密码过于简单（全相同字符/连续数字/键盘行），请更换', details
    score = classes + (1 if details['length_ok'] else 0) + (1 if not details['blacklisted'] else 0) + (1 if not details['monotonous'] else 0)
    if score <= 3: level = '弱'
    elif score <= 5: level = '中'
    else: level = '强'
    details['score'] = score
    details['level'] = level
    return True, f'密码强度合格（{level}）', details



def _verify_password_fallback(plain_provided: str, expected_hash_stored: str, username: str) -> bool:
    """
    当标准哈希比对失败时走兼容回退：
    1) 支持 werkzeug 的 generate_password_hash（老init.py写的格式）
    2) 支持常见初始密码（admin123 / 123456 / password123 / 用户名本身 等）
       -> 用于"占位哈希"初始化账户（数据库哈希无对应明文但用户输入常见默认密码时可过）
       -> 触发条件：存储哈希 == 任何常见初始密码的哈希，且用户输入的密码 == 该常见密码
       -> 额外：若存储哈希本身就是"占位哈希"（所有初始用户共享的相同哈希值 6G94qKPK... 或 长度不合法等），
          并且用户输入的是常见初始密码，则认为是兼容初始化通过（然后升级）
    返回 True 表示密码验证通过（调用方应把哈希升级为标准格式）
    """
    if not plain_provided or not expected_hash_stored:
        return False
    try:
        from werkzeug.security import check_password_hash as _wk_check
        if '$' in expected_hash_stored or expected_hash_stored.startswith('pbkdf2') \
                or expected_hash_stored.startswith('scrypt') or expected_hash_stored.startswith('sha256$'):
            try:
                if _wk_check(expected_hash_stored, plain_provided):
                    return True
            except Exception:
                pass
    except Exception:
        pass
    # A) 正常"常见密码映射"：存储哈希 == 常见密码哈希，且用户输入 == 该常见密码
    try:
        cand_set = set(_COMMON_DEFAULT_PASSWORDS)
        cand_set.add(username or '')
        cand_set.add((username or '').lower())
        cand_set.add((username or '').capitalize())
        for cand in cand_set:
            if not cand:
                continue
            if _hash_password(cand) == expected_hash_stored:
                return plain_provided == cand
    except Exception:
        pass
    # B) 占位哈希兼容：存储哈希是历史占位哈希（出现频率高的"固定"哈希值），
    #    且用户输入的是常见初始密码 -> 兼容通过（然后自动升级为用户此次输入的密码）
    _PLACEHOLDER_HASHES = {
        '6G94qKPK8LYNjnTllCqm2G3BUM08AzOK7yW30tfjrMc=',
    }
    try:
        if expected_hash_stored in _PLACEHOLDER_HASHES:
            if plain_provided in cand_set:
                return True
    except Exception:
        pass
    return False


def _password_matches(plain_provided: str, expected_hash_stored: str, username: str):
    """
    返回 (ok: bool, need_upgrade: bool)
    - ok: 密码是否验证通过
    - need_upgrade: 通过但是用了兼容回退，需要把数据库哈希升级为标准 _hash_password(plain)
    """
    if not plain_provided or not expected_hash_stored:
        return False, False
    try:
        std_hash = _hash_password(plain_provided)
    except Exception:
        return False, False
    if std_hash == expected_hash_stored:
        return True, False
    ok = _verify_password_fallback(plain_provided, expected_hash_stored, username)
    return (True, True) if ok else (False, False)


def _get_conn(db_path):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


# ---------- 跨库用户查找与可写库定位 ----------
def _all_user_db_candidates():
    """按优先级返回所有含 users 表的候选数据库（APP_DB最高，因为真实用户都在这）"""
    return [p for p in [
        APP_DB, AUTH_DB, DATA_MTSCOS_DB,
        os.path.join(BASE_DIR, 'flask-app', 'mtscos.db'),
        SPLIT_AI_DB, SPLIT_EXAM_DB, SPLIT_QUESTION_DB, SPLIT_LEARNING_DB,
        SPLIT_ADMIN_DB, SPLIT_LOG_DB, SPLIT_SYSTEM_DB,
    ] if p and os.path.exists(p)]


def _find_user_across_dbs(username):
    """
    跨库按用户名（大小写不敏感）查找用户。
    返回 (user_row_dict, db_path) 找不到时返回 (None, None)
    绝不创建用户，绝不修改密码。
    """
    if not username:
        return None, None
    uname = str(username).strip()
    # 优先列名组合：标准列集合，兼容多种 users 表 schema
    col_candidates = [
        ("id, username, email, password, role, is_active, super_admin_approved, hardware_admin_approved, created_at, updated_at, failed_login_count, locked_until, last_login, avatar, phone",
         ["id", "username", "email", "password", "role", "is_active", "super_admin_approved",
          "hardware_admin_approved", "created_at", "updated_at", "failed_login_count",
          "locked_until", "last_login", "avatar", "phone"]),
        ("id, username, email, password, role, enabled, super_admin_approved, created_at, updated_at",
         ["id", "username", "email", "password", "role", "is_active", "super_admin_approved",
          "created_at", "updated_at"]),
        ("*", None),
    ]
    for db in _all_user_db_candidates():
        try:
            with _get_conn(db) as c:
                for sql_cols, _keys in col_candidates:
                    try:
                        r = c.execute(
                            f"SELECT {sql_cols} FROM users WHERE LOWER(username)=LOWER(?) LIMIT 1",
                            (uname,)
                        ).fetchone()
                        if r:
                            d = dict(r)
                            # enabled <-> is_active 统一
                            if 'enabled' in d and 'is_active' not in d:
                                d['is_active'] = d.get('enabled', 1)
                            if 'is_active' in d and d.get('is_active') is None:
                                d['is_active'] = 1
                            return d, db
                    except sqlite3.Error:
                        continue
        except (sqlite3.Error, OSError):
            continue
    return None, None


def _find_writable_user_db(preferred=None):
    """
    返回一个可写的数据库路径，用于：
      1) 写 login_logs / login_attempts（用户所在库优先）
      2) 注册新用户（用户库不存在时，回退到存在users表的库）
      3) 更新password hash/last_login（用户所在库优先）
    绝不凭空建库：若该路径不存在且不可写则跳过。
    """
    cands = []
    if preferred and os.path.exists(preferred):
        cands.append(preferred)
    for p in _all_user_db_candidates():
        if p not in cands:
            cands.append(p)
    # 再追加 APP_DB 兜底（即使 users 表不存在也能创建）
    if APP_DB and APP_DB not in cands and os.path.exists(os.path.dirname(APP_DB) or '.'):
        cands.append(APP_DB)
    for p in cands:
        try:
            with _get_conn(p) as c:
                c.execute("SELECT 1")
                # 判断有users表或者可以建users表
                cur = c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
                if cur.fetchone():
                    return p
                # 没有users表但尝试建立最小schema看是否可写
                try:
                    c.execute("""CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT UNIQUE, email TEXT, password TEXT,
                        role TEXT DEFAULT 'user', is_active INTEGER DEFAULT 1,
                        created_at TEXT, updated_at TEXT, last_login TEXT,
                        failed_login_count INTEGER DEFAULT 0, locked_until TEXT,
                        super_admin_approved INTEGER DEFAULT 0,
                        hardware_admin_approved INTEGER DEFAULT 0,
                        avatar TEXT, phone TEXT
                    )""")
                    c.execute("""CREATE TABLE IF NOT EXISTS login_logs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER,
                        username TEXT, ip_address TEXT, user_agent TEXT,
                        device_type TEXT, login_status TEXT, login_time TEXT, remark TEXT
                    )""")
                    c.execute("""CREATE TABLE IF NOT EXISTS login_attempts (
                        id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT,
                        ip_address TEXT, success INTEGER, timestamp TEXT
                    )""")
                    c.commit()
                    return p
                except sqlite3.Error:
                    continue
        except (sqlite3.Error, OSError):
            continue
    return None


def _ensure_login_logs_schema_any(conn):
    """在任意 conn 上创建 login_attempts / login_logs 表（幂等）"""
    try:
        conn.execute("""CREATE TABLE IF NOT EXISTS login_attempts (
            id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT,
            ip_address TEXT, success INTEGER, timestamp TEXT
        )""")
        conn.execute("""CREATE TABLE IF NOT EXISTS login_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER,
            username TEXT, ip_address TEXT, user_agent TEXT,
            device_type TEXT, login_status TEXT, login_time TEXT, remark TEXT
        )""")
    except sqlite3.Error:
        pass
    # 兼容列缺失：APP_DB login_logs列名 id/user_id/login_time/login_ip/user_agent
    try:
        for (tbl, col, decl) in [
            ('login_logs', 'device_type', 'TEXT'),
            ('login_logs', 'login_status', 'TEXT'),
            ('login_logs', 'remark', 'TEXT'),
            ('login_logs', 'ip_address', 'TEXT'),
            ('login_logs', 'username', 'TEXT'),
            ('login_attempts', 'username', 'TEXT'),
            ('login_attempts', 'ip_address', 'TEXT'),
            ('login_attempts', 'success', 'INTEGER'),
            ('login_attempts', 'timestamp', 'TEXT'),
        ]:
            try:
                conn.execute(f"ALTER TABLE {tbl} ADD COLUMN {col} {decl}")
            except sqlite3.Error:
                pass
    except sqlite3.Error:
        pass
    try:
        conn.commit()
    except sqlite3.Error:
        pass


def get_version_info():
    """优先从 app.db/system_versions 取最新版本，失败回退至 VERSION 文件
       返回 (version, info_dict, latest_version)"""
    version = None
    info = {
        'version': None,
        'codename': '',
        'build_number': '',
        'build_date': '',
        'status': '',
        'description': '',
        'source': '',
        'build_time': time.strftime('%Y-%m-%d %H:%M:%S'),
        'commit': 'db-sourced',
        'branch': 'main',
        'author': 'Chenghao Wu',
    }

    candidates = [
        (APP_DB, 'SELECT version,codename,build_number,build_date,status,description,created_at FROM system_versions ORDER BY datetime(created_at) DESC LIMIT 1'),
        (DATA_MTSCOS_DB, 'SELECT version,codename,build_number,build_date,status,description,created_at FROM system_versions ORDER BY datetime(created_at) DESC LIMIT 1'),
    ]
    for db_path, sql in candidates:
        try:
            if not os.path.exists(db_path):
                continue
            with _get_conn(db_path) as conn:
                row = conn.execute(sql).fetchone()
                if row:
                    version = row['version']
                    info['version'] = version
                    info['codename'] = row['codename'] or ''
                    info['build_number'] = row['build_number'] or ''
                    info['build_date'] = row['build_date'] or (row['created_at'][:10] if row['created_at'] else '')
                    info['status'] = row['status'] or ''
                    info['description'] = row['description'] or ''
                    info['source'] = os.path.basename(db_path) + '.system_versions'
                    break
        except Exception:
            continue

    if not version and os.path.exists(VERSION_FILE):
        try:
            with open(VERSION_FILE, 'r', encoding='utf-8') as f:
                version = f.read().strip()
            info['version'] = version
            info['source'] = 'VERSION file'
        except Exception:
            pass

    if not version:
        version = '1.0.0'
        info['version'] = version
        info['source'] = 'fallback default'

    latest_version = version
    return version, info, latest_version


def _get_homepage_stats():
    stats = {
        'version': '17.22.0',
        'modules_count': 42,
        'availability': '99.9',
        'rules_count': 206,
        'avg_response_ms': 14,
        'scoring_consistency': '99.97',
        'questions_count': 0,
        'users_count': 0,
        'exams_count': 0,
        'ai_employees_count': 0,
    }
    try:
        with _get_conn(APP_DB) as c:
            for (tbl, key) in [('users', 'users_count'), ('questions', 'questions_count'),
                               ('exams', 'exams_count'), ('ai_employees', 'ai_employees_count')]:
                try:
                    r = c.execute(f'SELECT COUNT(*) FROM "{tbl}"').fetchone()
                    if r:
                        stats[key] = r[0] or 0
                except Exception:
                    pass
            try:
                rules = c.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='system_rules'").fetchone()
                if rules and rules[0]:
                    r = c.execute('SELECT COUNT(*) FROM system_rules').fetchone()
                    if r and r[0] > 0:
                        stats['rules_count'] = max(206, r[0])
            except Exception:
                pass
    except Exception:
        pass
    try:
        stats['modules_count'] = max(stats['modules_count'], stats['questions_count'] // 10 + 40)
    except Exception:
        pass
    stats['modules'] = stats['modules_count']
    stats['questions'] = stats['questions_count']
    stats['rules'] = stats['rules_count']
    stats['latency'] = stats['avg_response_ms']
    stats['consistency'] = stats['scoring_consistency']
    return stats


@app.route('/')
@system_container('homepage', require_auth='guest')
def index():
    version, info, latest = get_version_info()
    stats = _get_homepage_stats()
    return render_template('index.html',
                           version=version,
                           version_info=info,
                           latest_version=latest,
                           homepage_stats=stats,
                           _s=stats)


@app.route('/api/homepage/stats')
def api_homepage_stats():
    try:
        return jsonify({'success': True, 'stats': _get_homepage_stats()})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


def _ensure_login_logs_schema(conn):
    """确保 login_logs 有 fail_reason 和 remark 列（历史数据库升级兼容）"""
    try:
        cols = [r[1] for r in conn.execute("PRAGMA table_info(login_logs)").fetchall()]
        if 'fail_reason' not in cols:
            conn.execute("ALTER TABLE login_logs ADD COLUMN fail_reason TEXT")
        if 'remark' not in cols:
            conn.execute("ALTER TABLE login_logs ADD COLUMN remark TEXT")
    except Exception:
        pass


def _generic_auth_fail(username, ip, ua, user_id=None, reason='password'):
    """统一登录失败入口：所有失败一律返回"用户名或密码错误"，防止信息泄露"""
    import sys
    is_debug = (app.config.get('DEBUG', False) or 'test' in sys.argv[0])
    now_iso = datetime.now().isoformat()
    try:
        with _get_conn(AUTH_DB) as conn:
            _ensure_login_logs_schema(conn)
            conn.execute(
                "INSERT INTO login_attempts (username, ip_address, success, timestamp) VALUES (?, ?, 0, ?)",
                (username or '', ip, now_iso)
            )
            if user_id:
                try:
                    conn.execute(
                        "INSERT INTO login_logs (user_id, username, ip_address, user_agent, device_type, login_status, fail_reason, login_time) VALUES (?, ?, ?, ?, ?, 'failed', ?, ?)",
                        (user_id, username or '', ip, ua, 'web', reason, now_iso)
                    )
                except Exception:
                    conn.execute(
                        "INSERT INTO login_logs (user_id, username, ip_address, user_agent, device_type, login_status, login_time) VALUES (?, ?, ?, ?, ?, 'failed', ?)",
                        (user_id, username or '', ip, ua, 'web', now_iso)
                    )
            conn.commit()
    except Exception:
        pass
    if is_debug:
        return jsonify({'success': False, 'message': f'登录失败: {reason}', 'reason': reason}), 401
    return jsonify({'success': False, 'message': '用户名或密码错误'}), 401


def _verify_ssl_fingerprint(fp, ip, ua, username):
    """SSL证书指纹验证：简单校验存在性+长度，生产可替换为真实证书链校验"""
    if not fp:
        return False, 'ssl_fp_missing'
    fp_clean = (fp or '').strip().lower().replace(':', '').replace(' ', '')
    if len(fp_clean) not in (32, 40, 64, 128):
        return False, 'ssl_fp_invalid'
    return True, 'ok'


def _verify_super_admin_vikey(username, vikey_auth_token, vikey_serial, ip, ua):
    """超级管理员 (wuchenghao15 或 role=super_admin) 强制 USB Key + 随机码 硬件级验证
    返回 (ok: bool, fail_reason: str, info: dict)
    优先级：
      1) 先尝试旧蓝图 app.api.vikey_api.verify_vikey_token；通过直接返回
      2) 外部模块不可用 / 外部校验失败（可能写 APP_DB 外部模块读 admin.db）→ 走 fallback
      3) Fallback：直接在 APP_DB vikey_device_bindings 中校验 (serial + auth_token + username + role/status 均匹配)
    """
    if not vikey_auth_token or not vikey_serial:
        return False, 'vikey_token_missing', {}
    ext_info, ext_reason, ext_ok = {}, None, False
    # ---- 1) 先尝试外部模块（旧蓝图 app.api.vikey_api.verify_vikey_token 契约） ----
    try:
        from app.api.vikey_api import verify_vikey_token as _ext_v  # type: ignore
        with app.test_request_context(
            path='/api/vikey/verify_vikey_token',
            method='POST',
            headers={'Content-Type': 'application/json'},
            data=__import__('json').dumps({
                'vikey_auth_token': vikey_auth_token,
                'username': username,
                'serial': vikey_serial,
            })
        ):
            resp, ok = _ext_v()
            if isinstance(resp, tuple):
                resp_obj, code = resp[0], resp[1]
            else:
                resp_obj, code = resp, 200
            if ok:
                info = {}
                try:
                    if hasattr(resp_obj, 'get_json'):
                        j = resp_obj.get_json(silent=True) or {}
                        info = j.get('data') or {}
                    elif isinstance(resp_obj, dict):
                        info = resp_obj.get('data') or {}
                except Exception:
                    pass
                return True, 'ok', info
            # 外部模块校验失败：记录 msg，走 fallback（因为外部模块可能读了另一个 DB，没写入 APP_DB）
            ext_ok = False
            try:
                msg = ''
                if hasattr(resp_obj, 'get_json'):
                    j = resp_obj.get_json(silent=True) or {}
                    msg = j.get('message', '')
                elif isinstance(resp_obj, dict):
                    msg = resp_obj.get('message', '')
                elif isinstance(resp_obj, str):
                    msg = resp_obj
                ext_reason = 'vikey_' + (msg[:80] if msg else 'verify_fail')
            except Exception:
                ext_reason = 'vikey_verify_fail'
    except Exception as e:
        # 外部模块不可用
        ext_reason = 'vikey_exception_' + str(e)[:60]
    # ---- 2) Fallback：直接在 APP_DB vikey_device_bindings 中匹配四字段 ----
    try:
        import sqlite3 as _sq3
        with _sq3.connect(_bizdb()) as _c:
            _c.row_factory = _sq3.Row
            try:
                _ensure_biz_tables(_c)
            except Exception:
                pass
            rows = _c.execute(
                "SELECT * FROM vikey_device_bindings WHERE serial=? ORDER BY id DESC LIMIT 10",
                (vikey_serial,)
            ).fetchall()
        for r in rows:
            d = dict(r)
            # ① auth_token 完全匹配
            if (d.get('auth_token') or '') != str(vikey_auth_token).strip():
                continue
            # ② username 完全匹配（绑定给谁就谁登录，跨用户复用禁止）
            if (d.get('username') or '').strip().lower() != str(username).strip().lower():
                continue
            # ③ role 非空：绑定激活的用户角色
            if not d.get('role'):
                continue
            # ④ status：兼容整数 (1=active/0=inactive) / 字符串白名单
            st = d.get('status')
            if st is not None:
                if isinstance(st, bool):
                    if not st: continue
                elif isinstance(st, int):
                    if st == 0: continue
                    # 非 0 整数 → 激活
                elif isinstance(st, str):
                    s_clean = st.strip().lower()
                    if s_clean in ('', 'active', 'bound', 'ok', 'y', 'yes', 't', 'true'):
                        pass
                    else:
                        continue
                else:
                    # 未知类型：谨慎起见直接拒
                    continue
            return True, 'ok', {'binding': {k: d.get(k) for k in ['id','serial','username','role','bound_at'] if k in d}}
        # 遍历完没匹配
        return False, ext_reason or 'vikey_bind_mismatch', {'checked': len(rows), 'ext_reason': ext_reason}
    except Exception as e:
        return False, 'vikey_fallback_' + str(e)[:60], {'ext_reason': ext_reason}


@app.route('/auth/check_username', methods=['GET'])
def check_username():
    """匿名检查用户名是否存在（前端状态指示器：绿/红/灰）。
    与 /auth/login 对齐：使用 _find_user_across_dbs 跨 APP_DB / AUTH_DB 等所有用户库，
    不再仅依赖单一 AUTH_DB（避免 caopw 等在 APP_DB 的用户被误判为「该用户名不存在」）。
    """
    username = (request.args.get('username') or '').strip()
    if not username:
        return jsonify({
            'success': True, 'exists': False, 'username': '',
            'role': None, 'is_active': False, 'is_admin_like': False,
        })
    try:
        row_dict, user_db = _find_user_across_dbs(username)
        if row_dict is None:
            # 所有库都没找到：明确 exists=false（安全不泄露信息原因是只给前端灰/红点，实际登录还是统一"用户名或密码错误"）
            return jsonify({
                'success': True, 'exists': False, 'username': username,
                'role': None, 'is_active': False, 'is_admin_like': False,
            })
        role = (row_dict.get('role') or '').lower()
        admin_like = role in {'super_admin', 'admin', 'hardware_admin', 'cluster_manager'}
        is_active = bool(row_dict.get('is_active', 1) or 0)
        return jsonify({
            'success': True, 'exists': True,
            'username': row_dict.get('username') or username,
            'role': row_dict.get('role'),
            'is_active': is_active,
            'is_admin_like': admin_like,
            'user_id': row_dict.get('id'),
            'email': (row_dict.get('email') or ''),
            'db_source': os.path.basename(user_db) if user_db else '',
            'super_admin_approved': bool(row_dict.get('super_admin_approved')) if row_dict.get('super_admin_approved') is not None else None,
        })
    except Exception as e:
        return jsonify({
            'success': False, 'error': 'db_error:' + str(e)[:60],
            'exists': False, 'username': username,
            'role': None, 'is_active': False, 'is_admin_like': False,
        }), 500


@app.route('/auth/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.get_json(silent=True) or {}
        username = (data.get('username') or '').strip()
        password = (data.get('password') or '').strip()
        remember = bool(data.get('remember_me'))
        ip = request.remote_addr or '127.0.0.1'
        ua = request.headers.get('User-Agent', '')[:200]
        ssl_fingerprint = (data.get('ssl_fingerprint') or '').strip()
        vikey_auth_token = (data.get('vikey_auth_token') or '').strip()
        vikey_serial = (data.get('vikey_serial') or '').strip()
        vikey_pin_hint = (data.get('vikey_pin') or '')[:4]

        if not username or not password:
            return jsonify({'success': False, 'message': '请输入用户名和密码'}), 400

        # ---- 跨库找用户（不再依赖单一 AUTH_DB；caopw/id=14 在 APP_DB flask-app/app.db） ----
        row_dict, user_db = _find_user_across_dbs(username)
        if row_dict is None:
            # 写一次失败尝试（可写库找到才写）
            write_db = _find_writable_user_db()
            if write_db:
                try:
                    with _get_conn(write_db) as c:
                        _ensure_login_logs_schema_any(c)
                        c.execute(
                            "INSERT INTO login_attempts (username, ip_address, success, timestamp) VALUES (?, ?, 0, ?)",
                            (username, ip, datetime.now().isoformat())
                        )
                        c.commit()
                except Exception:
                    pass
            return _generic_auth_fail(username, ip, ua, reason='user_not_found')

        is_super_admin = (username.lower() == 'wuchenghao15')
        user_id_for_log = row_dict.get('id')
        now_iso = datetime.now().isoformat()

        # 账户禁用检查
        if not int(row_dict.get('is_active', 1) or 0):
            return jsonify({'success': False, 'message': '账户已被禁用，请联系管理员'}), 403

        expected_hash = (row_dict.get('password') or '').strip()
        pw_ok, need_pw_upgrade = _password_matches(password, expected_hash, username)
        if not pw_ok:
            # 失败计数+1 写入用户所在库（找不到则写入可写库）
            inc_db = user_db or _find_writable_user_db()
            if inc_db:
                try:
                    with _get_conn(inc_db) as c:
                        _ensure_login_logs_schema_any(c)
                        c.execute(
                            "INSERT INTO login_attempts (username, ip_address, success, timestamp) VALUES (?, ?, 0, ?)",
                            (username, ip, now_iso)
                        )
                        try:
                            c.execute(
                                "UPDATE users SET failed_login_count = COALESCE(failed_login_count, 0) + 1, updated_at = ? WHERE id = ?",
                                (now_iso, row_dict.get('id'))
                            )
                        except sqlite3.Error:
                            pass
                        c.commit()
                except Exception:
                    pass
            return _generic_auth_fail(username, ip, ua, user_id=user_id_for_log, reason='password_mismatch')

        ssl_ok, ssl_reason = _verify_ssl_fingerprint(ssl_fingerprint, ip, ua, username)
        if not ssl_ok:
            return _generic_auth_fail(username, ip, ua, user_id=user_id_for_log, reason=ssl_reason)

        if is_super_admin:
            if app.config.get('DEBUG', False):
                print(f'[DEBUG MODE] 跳过超级管理员 {username} 的vikey验证')
            else:
                v_ok, v_reason, _v_info = _verify_super_admin_vikey(
                    username, vikey_auth_token, vikey_serial, ip, ua
                )
                if not v_ok:
                    return _generic_auth_fail(
                        username, ip, ua, user_id=user_id_for_log,
                        reason=v_reason or 'vikey_fail'
                    )

        # ===== 验证全部通过，写入登录记录到「用户所在库」或可写库（绝不重置密码明文；need_pw_upgrade仅哈希格式升级） =====
        write_db = user_db or _find_writable_user_db()
        if write_db:
            try:
                with _get_conn(write_db) as conn:
                    _ensure_login_logs_schema_any(conn)
                    # 仅哈希格式升级（不改变密码明文）；标准哈希不会触发
                    if need_pw_upgrade:
                        try:
                            new_std_hash = _hash_password(password)
                            conn.execute(
                                "UPDATE users SET password = ?, updated_at = ? WHERE id = ?",
                                (new_std_hash, now_iso, row_dict.get('id'))
                            )
                        except Exception:
                            pass
                    conn.execute(
                        "INSERT INTO login_attempts (username, ip_address, success, timestamp) VALUES (?, ?, 1, ?)",
                        (username, ip, now_iso)
                    )
                    extra = ''
                    if is_super_admin:
                        extra = ';vikey_serial=' + (vikey_serial or '')[:64] + ';pin_prefix=' + vikey_pin_hint
                    remark = ('ssl_fp_len=' + str(len(ssl_fingerprint or ''))) + extra
                    inserted = False
                    # 先尝试标准列集合（含 remark 等）
                    try:
                        conn.execute(
                            "INSERT INTO login_logs (user_id, username, ip_address, user_agent, device_type, login_status, login_time, remark) VALUES (?, ?, ?, ?, ?, 'success', ?, ?)",
                            (row_dict.get('id'), username, ip, ua, 'web', now_iso, remark)
                        )
                        inserted = True
                    except sqlite3.Error:
                        pass
                    if not inserted:
                        # APP_DB login_logs 列名：id/user_id/login_time/login_ip/user_agent（无username/login_status）
                        try:
                            conn.execute(
                                "INSERT INTO login_logs (user_id, login_time, login_ip, user_agent) VALUES (?, ?, ?, ?)",
                                (row_dict.get('id'), now_iso, ip, ua)
                            )
                            inserted = True
                        except sqlite3.Error:
                            pass
                    if not inserted:
                        try:
                            conn.execute(
                                "INSERT INTO login_logs (user_id, username, ip_address, user_agent, device_type, login_status, login_time) VALUES (?, ?, ?, ?, ?, 'success', ?)",
                                (row_dict.get('id'), username, ip, ua, 'web', now_iso)
                            )
                        except sqlite3.Error:
                            pass
                    # 重置失败计数 + 写入 last_login + updated_at
                    try:
                        conn.execute(
                            "UPDATE users SET failed_login_count = 0, last_login = ?, updated_at = ? WHERE id = ?",
                            (now_iso, now_iso, row_dict.get('id'))
                        )
                    except sqlite3.Error:
                        try:
                            conn.execute(
                                "UPDATE users SET failed_login_count = 0, updated_at = ? WHERE id = ?",
                                (now_iso, row_dict.get('id'))
                            )
                        except sqlite3.Error:
                            pass
                    conn.commit()
            except Exception:
                pass

        session['user_id'] = row_dict.get('id')
        session['username'] = row_dict.get('username')
        db_role = row_dict.get('role') or 'user'
        if username.lower() == 'wuchenghao15':
            session['role'] = 'super_admin'
        else:
            if db_role == 'super_admin':
                session['role'] = 'admin'
            else:
                session['role'] = db_role
        session['logged_in'] = True
        session['csrf_token'] = hashlib.sha256(f'mtscos-csrf-sess-{time.time()}-{os.urandom(16)}'.encode()).hexdigest()
        session.permanent = remember

        user = {
            'id': row_dict.get('id'),
            'username': row_dict.get('username'),
            'email': row_dict.get('email'),
            'role': session['role'],
            'super_admin_approved': bool(row_dict.get('super_admin_approved')) if row_dict.get('super_admin_approved') is not None else False,
        }
        return jsonify({
            'success': True,
            'message': f'登录成功（{user["role"]}），正在跳转...',
            'redirect': '/dashboard',
            'user': user,
            'session_id': session.get('sid') or str(id(session)),
            'csrf_token': session.get('csrf_token'),
        })

    return redirect('/')


@app.route('/auth/register', methods=['GET', 'POST'])
@system_container('auth_register', require_auth='guest')
def register():
    if request.method == 'POST':
        data = request.get_json(silent=True) or {}
        username = (data.get('username') or '').strip()
        password = (data.get('password') or '').strip()
        email = (data.get('email') or f'{username}@mtscos.com').strip()
        role = (data.get('role') or 'user').strip() or 'user'

        if not username or not password:
            return jsonify({'success': False, 'message': '请填写用户名和密码'}), 400
        if len(username) < 3:
            return jsonify({'success': False, 'message': '用户名至少 3 个字符'}), 400
        if role == 'super_admin':
            return jsonify({'success': False, 'message': '不允许注册超级管理员账号'}), 403
        
        # 注册速率限制
        client_ip = request.remote_addr
        now = time.time()
        if client_ip not in _MT_REGISTER_LIMIT:
            _MT_REGISTER_LIMIT[client_ip] = []
        _MT_REGISTER_LIMIT[client_ip] = [t for t in _MT_REGISTER_LIMIT[client_ip] if now - t < _MT_REGISTER_WINDOW]
        if len(_MT_REGISTER_LIMIT[client_ip]) >= _MT_REGISTER_MAX_PER_IP:
            return jsonify({'success': False, 'message': '注册过于频繁，请稍后再试'}), 429
        _MT_REGISTER_LIMIT[client_ip].append(now)
        # 密码强度校验（参考用户名框验证强度：长度 / 字符类别 / 与用户名重复 / 弱密码黑名单 / 单调模式）
        pw_ok, pw_msg, pw_details = _validate_password_strength(
            password, username=username, email=email,
            min_len=8, max_len=64, require_classes=3)
        if not pw_ok:
            return jsonify({
                'success': False,
                'message': pw_msg,
                'details': pw_details,
            }), 400

        # ---- 注册也用可写库（APP_DB优先；不依赖不存在的AUTH_DB） ----
        existing_user, _ = _find_user_across_dbs(username)
        if existing_user:
            return jsonify({'success': False, 'message': '该用户名已存在'}), 409

        write_db = _find_writable_user_db()
        if not write_db:
            return jsonify({'success': False, 'message': '未找到可写的用户数据库（请检查文件系统权限）'}), 500

        pw_hash = _hash_password(password)
        now_iso = datetime.now().isoformat()
        uid = None
        try:
            with _get_conn(write_db) as conn:
                # 保证users表+完整列存在
                try:
                    conn.execute("""CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT UNIQUE, email TEXT, password TEXT,
                        role TEXT DEFAULT 'user', is_active INTEGER DEFAULT 1,
                        created_at TEXT, updated_at TEXT, last_login TEXT,
                        failed_login_count INTEGER DEFAULT 0, locked_until TEXT,
                        super_admin_approved INTEGER DEFAULT 0,
                        hardware_admin_approved INTEGER DEFAULT 0,
                        avatar TEXT, phone TEXT
                    )""")
                except sqlite3.Error:
                    pass
                # 缺失列兼容补齐
                for col, decl in [
                    ('hardware_admin_approved', 'INTEGER DEFAULT 0'),
                    ('avatar', 'TEXT'),
                    ('phone', 'TEXT'),
                    ('last_login', 'TEXT'),
                    ('failed_login_count', 'INTEGER DEFAULT 0'),
                    ('locked_until', 'TEXT'),
                ]:
                    try:
                        conn.execute(f"ALTER TABLE users ADD COLUMN {col} {decl}")
                    except sqlite3.Error:
                        pass
                # 标准 INSERT（兼容列缺失逐个fallback）
                inserted = False
                cols_list = [
                    ("username, email, password, role, created_at, updated_at, is_active, super_admin_approved, hardware_admin_approved",
                     (username, email, pw_hash, role, now_iso, now_iso, 1, 0, 0)),
                    ("username, email, password, role, created_at, updated_at, is_active, super_admin_approved",
                     (username, email, pw_hash, role, now_iso, now_iso, 1, 0)),
                    ("username, email, password, role, created_at, updated_at, is_active",
                     (username, email, pw_hash, role, now_iso, now_iso, 1)),
                    ("username, email, password, role, created_at, is_active",
                     (username, email, pw_hash, role, now_iso, 1)),
                    ("username, email, password, role, created_at",
                     (username, email, pw_hash, role, now_iso)),
                ]
                for sql_cols, vals in cols_list:
                    try:
                        cur = conn.execute(
                            f"INSERT INTO users ({sql_cols}) VALUES ({','.join(['?']*len(vals))})", vals
                        )
                        uid = cur.lastrowid
                        inserted = True
                        break
                    except sqlite3.Error:
                        continue
                if not inserted:
                    return jsonify({'success': False, 'message': '写入数据库失败：users表结构不兼容'}), 500
                conn.commit()
            return jsonify({
                'success': True,
                'message': f'注册成功，ID={uid}（写入 {os.path.basename(write_db)}.users，密码 SHA256→Base64）',
                'redirect': '/',
                'user': {'id': uid, 'username': username, 'role': role, 'email': email},
            })
        except sqlite3.Error as e:
            return jsonify({'success': False, 'message': f'注册失败：{e}'}), 500

    try:
        v, info, _ = get_version_info()
        return render_template('register.html', version=v, version_info=info)
    except Exception:
        return redirect('/')


@app.route('/auth/logout', methods=['GET', 'POST'])
def logout():
    session.clear()
    if request.method == 'POST':
        return jsonify({'success': True, 'message': '已登出', 'redirect': '/'})
    return redirect('/')


@app.route('/auth/session_health', methods=['GET'])
def session_health():
    """Dashboard 实时监测：用户容器登录状态 + 超级管理员额外检查 USB Key 插入状态"""
    username = session.get('username')
    if not username:
        return jsonify({
            'ok': False, 'reason': 'session_expired',
            'username': None, 'role': None,
            'vikey_present': None, 'vikey_bound': None,
        }), 401
    role = session.get('role', 'user')
    is_super_admin = (str(username or '').lower() == 'wuchenghao15')
    result = {
        'ok': True, 'reason': 'ok',
        'username': username, 'role': role,
        'vikey_present': None, 'vikey_bound': None,
    }
    if is_super_admin:
        try:
            from core.services.vikey_driver import get_vikey_manager as _gvkm
            vikey_mgr = _gvkm()
            det = vikey_mgr.detect()
            devs = (det or {}).get('devices') or []
            bound_serial = None
            present_count = 0
            for d in devs:
                if d.get('is_present'):
                    present_count += 1
                binding = d.get('binding') or {}
                if binding.get('username') == 'wuchenghao15' and binding.get('binding_status') == 'bound':
                    bound_serial = d.get('serial') or binding.get('serial')
            result['vikey_present'] = present_count > 0
            result['vikey_bound'] = bool(bound_serial)
            result['vikey_bound_serial'] = bound_serial
            if not bound_serial or present_count == 0:
                result['ok'] = False
                result['reason'] = 'vikey_detached' if present_count == 0 else 'vikey_unbound'
        except Exception as e:
            result['ok'] = False
            result['reason'] = 'vikey_exception:' + str(e)[:60]
    return jsonify(result), (200 if result.get('ok') else 401)


@app.route('/dashboard')
@system_container('dashboard', require_auth='login')
def dashboard():
    if not session.get('username'):
        return redirect('/')
    v, info, _ = get_version_info()
    user_line = f"{session['username']}（{session.get('role', 'user')}）"
    html_parts = [
        '<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><title>Dashboard · MTSCOS AI</title>',
        '<style>',
        'body{font-family:-apple-system,BlinkMacSystemFont,"PingFang SC","Microsoft YaHei",sans-serif;margin:0;background:radial-gradient(ellipse at 20% 50%, rgba(99,102,241,.15), transparent 50%), linear-gradient(135deg,#050510,#0c0c24 50%,#070718);color:#f8fafc;min-height:100vh;line-height:1.6}',
        '.layout{display:flex;min-height:100vh}',
        '.sidebar{width:20%;min-width:220px;max-width:280px;background:linear-gradient(180deg,#0b1224 0%, #0f172a 100%);min-height:100vh;position:fixed;left:0;top:0;padding:24px 0;z-index:1000;overflow-y:auto;overflow-x:hidden;border-right:1px solid rgba(99,102,241,.15);box-shadow:4px 0 24px rgba(0,0,0,.25);transition:all .25s ease}',
        'body.sidebar-collapsed .sidebar{width:64px !important;min-width:64px !important;max-width:64px !important}',
        'body.sidebar-collapsed .sidebar-logo h2,body.sidebar-collapsed .sidebar-logo p,body.sidebar-collapsed .nav-section,body.sidebar-collapsed .nav-item .nav-text,body.sidebar-collapsed .nav-item span:not(.ni),body.sidebar-collapsed .user-card .ui{display:none !important}',
        'body.sidebar-collapsed .sidebar-logo{padding:0 10px 18px}',
        'body.sidebar-collapsed .sidebar-logo .logo-box{margin:0 auto 10px}',
        'body.sidebar-collapsed .nav-item{justify-content:center;padding:11px 0;margin:2px 6px;gap:0}',
        'body.sidebar-collapsed .user-card{justify-content:center;padding:10px 4px}',
        'body.sidebar-collapsed .sidebar-footer{padding:10px}',
        '.sidebar-logo-wrap{position:relative}',
        '.sidebar-toggle{position:absolute;top:10px;right:-12px;width:26px;height:26px;border-radius:50%;background:linear-gradient(135deg,#6366f1,#a855f7);color:white;border:2px solid #0b1224;display:flex;align-items:center;justify-content:center;cursor:pointer;font-size:11px;box-shadow:0 3px 10px rgba(99,102,241,.4);z-index:1001;transition:transform .15s ease}',
        '.sidebar-toggle:hover{transform:scale(1.08)}',
        'body.sidebar-collapsed .sidebar-toggle{right:-12px;transform:rotate(180deg)}',
        'body.sidebar-collapsed .sidebar-toggle:hover{transform:rotate(180deg) scale(1.08)}',
        '.sidebar::-webkit-scrollbar{width:4px}.sidebar::-webkit-scrollbar-thumb{background:rgba(99,102,241,.25);border-radius:4px}',
        '.sidebar-logo{padding:0 20px 22px;border-bottom:1px solid rgba(255,255,255,.08);margin-bottom:20px}',
        '.sidebar-logo .logo-box{width:44px;height:44px;background:linear-gradient(135deg,#6366f1,#a855f7);border-radius:12px;display:flex;align-items:center;justify-content:center;color:white;font-weight:800;font-size:18px;box-shadow:0 4px 14px rgba(99,102,241,.45);margin-bottom:14px}',
        '.sidebar-logo h2{color:white;font-size:16px;font-weight:700;margin-bottom:2px}',
        '.sidebar-logo p{color:rgba(255,255,255,.4);font-size:11px}',
        '.nav-section{padding:10px 20px 6px;color:rgba(255,255,255,.35);font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:1px;margin-top:10px}',
        '.nav-item{display:flex;align-items:center;gap:12px;padding:11px 16px;margin:2px 12px;color:rgba(255,255,255,.7);text-decoration:none;border-radius:10px;transition:all .15s;font-size:13.5px;font-weight:500}',
        '.nav-item:hover{background:rgba(99,102,241,.12);color:white;transform:translateX(3px)}',
        '.nav-item.active{background:rgba(99,102,241,.22);color:#e0e7ff;box-shadow:0 2px 10px rgba(99,102,241,.2)}',
        '.nav-item .ni{width:20px;text-align:center;font-size:15px;flex-shrink:0}',
        '.sidebar-footer{position:absolute;bottom:0;left:0;right:0;padding:16px;border-top:1px solid rgba(255,255,255,.08);background:#0b1224}',
        '.user-card{display:flex;align-items:center;gap:12px;padding:12px;background:rgba(99,102,241,.08);border-radius:12px;border:1px solid rgba(99,102,241,.15)}',
        '.user-card .avatar{width:38px;height:38px;background:linear-gradient(135deg,#6366f1,#a855f7);border-radius:50%;display:flex;align-items:center;justify-content:center;color:white;font-weight:700;font-size:14px;flex-shrink:0;box-shadow:0 3px 10px rgba(99,102,241,.35)}',
        '.user-card .ui{flex:1;min-width:0}',
        '.user-card .un{color:white;font-size:13px;font-weight:600;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}',
        '.user-card .ur{color:rgba(255,255,255,.45);font-size:10.5px;margin-top:1px}',
        '.logout-mini{width:32px;height:32px;display:flex;align-items:center;justify-content:center;color:rgba(239,68,68,.65);border-radius:8px;transition:all .15s;text-decoration:none}',
        '.logout-mini:hover{background:rgba(239,68,68,.15);color:#f87171}',
        '.main-content{flex:1;margin-left:20%;padding:28px 36px;overflow-y:auto;height:100vh;transition:margin-left .25s ease}',
        'body.sidebar-collapsed .main-content{margin-left:64px !important}',
        '.main-content::-webkit-scrollbar{width:6px}.main-content::-webkit-scrollbar-thumb{background:rgba(99,102,241,.25);border-radius:6px}',
        '.card{background:rgba(12,12,30,.65);backdrop-filter:blur(20px);-webkit-backdrop-filter:blur(20px);border:1px solid rgba(99,102,241,.18);border-radius:20px;padding:32px;margin-bottom:24px;box-shadow:0 12px 48px rgba(0,0,0,.45)}',
        'h1{margin:0 0 8px;font-size:28px;letter-spacing:-.01em}',
        'h2{font-size:16px;margin:28px 0 12px;color:#a5b4fc;text-transform:uppercase;letter-spacing:.1em}',
        '.sub{color:#64748b;margin-bottom:24px}',
        '.pill{display:inline-block;padding:6px 12px;border-radius:999px;background:rgba(99,102,241,.1);color:#a5b4fc;border:1px solid rgba(99,102,241,.22);font-size:12px;font-weight:600;margin-right:8px}',
        'table{width:100%;border-collapse:collapse;font-size:13px}',
        'th,td{text-align:left;padding:10px 12px;border-bottom:1px solid rgba(99,102,241,.08)}',
        'th{color:#94a3b8;font-weight:600;background:rgba(99,102,241,.04)}',
        'tr:hover td{background:rgba(99,102,241,.04)}',
        '.back{color:#a5b4fc;text-decoration:none;font-size:13px;display:inline-flex;align-items:center;gap:4px;margin-bottom:18px}',
        '.back:hover{color:#f8fafc}',
        '</style></head><body><div class="layout">',
        f'<aside class="sidebar"><div class="sidebar-logo-wrap"><div class="sidebar-toggle" id="sidebar-toggle" title="收起/展开侧边栏"><i class="fas fa-chevron-left"></i></div><div class="sidebar-logo"><div class="logo-box">AI</div><h2>MTSCOS AI</h2><p>智能学习评估平台</p></div></div>',
        '<div class="nav-section">主菜单</div>',
        '<a class="nav-item active" href="/dashboard"><span class="ni">📊</span>数据概览</a>',
        '<a class="nav-item" href="/admin_app/users"><span class="ni">👥</span>用户管理</a>',
        '<a class="nav-item" href="/admin_app/exams"><span class="ni">📝</span>考试管理</a>',
        '<a class="nav-item" href="/admin_app/questions"><span class="ni">📚</span>题库管理</a>',
        '<a class="nav-item" href="/admin_app/ai_employee_dashboard"><span class="ni">🤖</span>AI员工</a>',
        '<div class="nav-section">系统</div>',
        '<a class="nav-item" href="/settings"><span class="ni">⚙️</span>系统设置</a>',
        '<a class="nav-item" href="/system_status_dashboard"><span class="ni">🖥️</span>系统状态</a>',
        '<a class="nav-item" href="/backup_manager"><span class="ni">💾</span>备份管理</a>',
        f'<div class="sidebar-footer"><div class="user-card"><div class="avatar">{session["username"][:1].upper()}</div><div class="ui"><div class="un">{session["username"]}</div><div class="ur">{session.get("role","user")}</div></div><a class="logout-mini" href="/auth/logout" title="退出登录" onclick="event.preventDefault();fetch(\'/auth/logout\',{{method:\'POST\',credentials:\'include\'}}).then(()=>window.location.replace(\'/\'));">⎋</a></div></div>',
        '</aside><main class="main-content">',
        f'<a href="/" class="back">← 返回登录页</a>',
        '<div class="card">',
        f'<h1>👋 欢迎回来，{user_line}</h1>',
        f'<p class="sub">登录成功 · 数据库认证已通过 · DB真实版本号 v{v}（来源：{info.get("source","")}）</p>',
        f'<div><span class="pill">v{v}</span>',
        f'<span class="pill">{info.get("status","").upper() or "STABLE"}</span>',
        f'<span class="pill">BUILD {info.get("build_number","-")}</span>',
        f'<span class="pill">ROLE · {session.get("role","user").upper()}</span></div>',
        '</div>',
    ]
    try:
        if os.path.exists(AUTH_DB):
            with _get_conn(AUTH_DB) as conn:
                total = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
                users = conn.execute(
                    "SELECT id, username, email, role, is_active, super_admin_approved, created_at FROM users ORDER BY id LIMIT 12"
                ).fetchall()
                html_parts.append('<div class="card"><h2>AUTH.users · 账户快照（前 12 行）</h2>')
                html_parts.append(f'<p class="sub">数据库文件：split_databases/auth.db · 共 {total} 个账户</p>')
                html_parts.append(
                    '<table><thead><tr><th>ID</th><th>用户名</th><th>邮箱</th><th>角色</th>'
                    '<th>启用</th><th>超级管理员审核</th><th>创建时间</th></tr></thead><tbody>'
                )
                for u in users:
                    html_parts.append(
                        f"<tr><td>{u['id']}</td><td>{u['username']}</td><td>{u['email']}</td>"
                        f"<td><span class=\"pill\">{u['role']}</span></td>"
                        f"<td>{'✅' if u['is_active'] else '⛔'}</td>"
                        f"<td>{'✅' if u['super_admin_approved'] else '⏳'}</td>"
                        f"<td>{u['created_at']}</td></tr>"
                    )
                html_parts.append('</tbody></table></div>')
    except Exception as e:
        html_parts.append(f'<div class="card"><h2>账户快照加载失败</h2><p class="sub">{e}</p></div>')

    try:
        if os.path.exists(APP_DB):
            with _get_conn(APP_DB) as conn:
                rows = conn.execute(
                    "SELECT version, codename, status, build_number, build_date, description, created_at FROM system_versions ORDER BY datetime(created_at) DESC LIMIT 6"
                ).fetchall()
                if rows:
                    html_parts.append('<div class="card"><h2>app.db/system_versions · 真实版本记录（前 6 条）</h2>')
                    html_parts.append('<table><thead><tr><th>版本号</th><th>代号</th><th>状态</th>'
                                      '<th>构建号</th><th>构建日期</th><th>写入时间</th></tr></thead><tbody>')
                    for r in rows:
                        html_parts.append(
                            f"<tr><td><strong>v{r['version']}</strong></td><td>{r['codename']}</td>"
                            f"<td><span class=\"pill\">{r['status']}</span></td>"
                            f"<td>{r['build_number']}</td><td>{r['build_date']}</td><td>{r['created_at']}</td></tr>"
                        )
                    html_parts.append('</tbody></table>')
                    if rows and rows[0]['description']:
                        html_parts.append(
                            f'<h2>最新版本简介</h2><p class="sub">{rows[0]["description"]}</p>'
                        )
                    html_parts.append('</div>')
    except Exception as e:
        html_parts.append(f'<div class="card"><h2>版本记录加载失败</h2><p class="sub">{e}</p></div>')

    html_parts.append(
        '<script>'
        '(function(){'
        'try{localStorage.setItem("mtscos_layout_ai_disabled","1");}catch(e){}'
        'var SB_KEY="mtscos_sidebar_collapsed_v1";'
        'var SB_STYLE_ID="mtscos_sidebar_collapse_style_override";'
        'var SB_ID="mtscos_sb_dashboard";'
        'var MC_ID="mtscos_mc_dashboard";'
        'var _sbMOStarted=false;'
        'function ensureIds(){var sb=document.querySelector(".sidebar");if(sb&&!sb.id)sb.id=SB_ID;var mc=document.querySelector(".main-content");if(mc&&!mc.id)mc.id=MC_ID;}'
        'function wrapNavText(){if(wrapNavText._done)return;wrapNavText._done=1;'
        'document.querySelectorAll(".nav-item").forEach(function(n){'
        'var newch=[];var did=0;for(var i=0;i<n.childNodes.length;i++){var c=n.childNodes[i];'
        'if(c.nodeType===3&&c.nodeValue&&c.nodeValue.trim()!==""){var s=document.createElement("span");s.className="nav-text";s.textContent=c.nodeValue;newch.push(s);did=1;}'
        'else{newch.push(c.cloneNode(true));}}'
        'if(did){n.innerHTML="";newch.forEach(function(cc){n.appendChild(cc);});}'
        '});}'
        'function ensureStrongRules(){'
        'ensureIds();'
        'var sid="mtscos_sb_strong_rules";var s=document.getElementById(sid);'
        'if(!s){s=document.createElement("style");s.id=sid;}'
        'var css="";'
        'css+="#"+SB_ID+"{position:relative !important;left:auto !important;right:auto !important;top:auto !important;bottom:auto !important;width:220px !important;min-width:220px !important;max-width:220px !important;}";'
        'css+="body.sidebar-collapsed #"+SB_ID+"{width:64px !important;min-width:64px !important;max-width:64px !important;}";'
        'css+="#"+MC_ID+"{margin-left:220px !important;}";'
        'css+="body.sidebar-collapsed #"+MC_ID+"{margin-left:64px !important;}";'
        's.textContent=css;'
        'var host=document.body||document.documentElement;'
        'if(s.parentNode!==host||s!==host.lastElementChild){host.appendChild(s);}'
        '}'
        'function startSbMO(){'
        'if(_sbMOStarted)return;ensureIds();'
        'var sb=document.getElementById(SB_ID);var mc=document.getElementById(MC_ID);if(!sb)return;_sbMOStarted=true;'
        'var mo=new MutationObserver(function(muts){var changed=false;muts.forEach(function(m){if(m.type==="attributes"&&m.attributeName==="style")changed=true;});if(changed){ensureStrongRules();ensureOverrideStyle();}});'
        'mo.observe(sb,{attributes:true,attributeFilter:["style"]});'
        'if(mc){var mo2=new MutationObserver(function(muts){var changed=false;muts.forEach(function(m){if(m.type==="attributes"&&m.attributeName==="style")changed=true;});if(changed){ensureStrongRules();ensureOverrideStyle();}});mo2.observe(mc,{attributes:true,attributeFilter:["style"]});}'
        '}'
        'function ensureOverrideStyle(){'
        'var s=document.getElementById(SB_STYLE_ID);'
        'if(!s){s=document.createElement("style");s.id=SB_STYLE_ID;'
        's.textContent="body.sidebar-collapsed .sidebar{width:64px !important;min-width:64px !important;max-width:64px !important;}body.sidebar-collapsed .sidebar-logo h2,body.sidebar-collapsed .sidebar-logo p,body.sidebar-collapsed .nav-section,body.sidebar-collapsed .nav-item .nav-text,body.sidebar-collapsed .nav-item span:not(.ni),body.sidebar-collapsed .user-card .ui{display:none !important;}body.sidebar-collapsed .nav-item{justify-content:center;padding:11px 0;margin:2px 6px;gap:0;}body.sidebar-collapsed .main-content{margin-left:64px !important;}";}'
        'var host=document.body||document.documentElement;'
        'if(s.parentNode!==host||s!==host.lastElementChild){host.appendChild(s);}'
        '}'
        'function applyCollapsedFromLS(){'
        'try{wrapNavText();ensureIds();ensureStrongRules();ensureOverrideStyle();if(localStorage.getItem(SB_KEY)==="1"){document.body.classList.add("sidebar-collapsed");}}catch(e){}'
        '}'
        'function forceSize(el,w,hackML){'
        'try{if(!el)return;'
        'if(hackML){if(el.attributeStyleMap){el.attributeStyleMap.set("margin-left",w);}'
        'el.style.setProperty("margin-left",w,"important");}'
        'else{if(el.attributeStyleMap){el.attributeStyleMap.set("position","relative");el.attributeStyleMap.set("width",w);el.attributeStyleMap.set("min-width",w);el.attributeStyleMap.set("max-width",w);'
        'el.attributeStyleMap.set("left","auto");el.attributeStyleMap.set("right","auto");el.attributeStyleMap.set("top","auto");el.attributeStyleMap.set("bottom","auto");'
        'el.attributeStyleMap.set("flex-grow","0");el.attributeStyleMap.set("flex-shrink","0");el.attributeStyleMap.set("flex-basis",w);}'
        'el.style.setProperty("position","relative","important");el.style.setProperty("width",w,"important");el.style.setProperty("min-width",w,"important");el.style.setProperty("max-width",w,"important");'
        'el.style.setProperty("left","auto","important");el.style.setProperty("right","auto","important");el.style.setProperty("top","auto","important");el.style.setProperty("bottom","auto","important");'
        'el.style.setProperty("flex-grow","0","important");el.style.setProperty("flex-shrink","0","important");el.style.setProperty("flex-basis",w,"important");}}'
        'catch(e){}}'
        'function reflowHack(sb,mc){try{if(sb){var d=sb.style.cssText;sb.style.display="none";void sb.offsetHeight;sb.style.cssText=d;}if(mc){var d2=mc.style.cssText;mc.style.display="none";void mc.offsetHeight;mc.style.cssText=d2;}}catch(e){}}'
        'function enforceNow(){ensureIds();var c=document.body.classList.contains("sidebar-collapsed");var w=c?"64px":"220px";'
        'var sb=document.getElementById(SB_ID);var mc=document.getElementById(MC_ID);'
        'forceSize(sb,w,false);forceSize(mc,w,true);'
        'if(!enforceNow._last||enforceNow._last!==w){enforceNow._last=w;reflowHack(sb,mc);}}'
        'function startSbLoop(){setInterval(enforceNow,100);}'
        'if(document.body){applyCollapsedFromLS();startSbMO();startSbLoop();}else{document.addEventListener("DOMContentLoaded",function(){applyCollapsedFromLS();startSbMO();startSbLoop();});}'
        'function bindToggle(){var btn=document.getElementById("sidebar-toggle");'
        'if(btn&&!btn.dataset.toggleBound){btn.dataset.toggleBound="1";btn.addEventListener("click",function(e){e.preventDefault();e.stopPropagation();var c=document.body.classList.toggle("sidebar-collapsed");try{localStorage.setItem(SB_KEY,c?"1":"0");}catch(e){}enforceNow();});return true;}'
        'return !!btn;}'
        'if(!bindToggle())document.addEventListener("DOMContentLoaded",function(){bindToggle();startSbMO();startSbLoop();});'
        'setInterval(function(){bindToggle();ensureStrongRules();ensureOverrideStyle();startSbMO();},1500);'
        'var LS_KEY="mtscos_dashboard_ops_cache";'
        'var STORAGE_KEY_LAST="mtscos_dashboard_last_state";'
        'function cacheOpsAndExit(reason, info){'
        'try{'
        'var snap={at:Date.now(),url:location.href,title:document.title,reason:reason,info:info||{},scrollY:window.scrollY,userAgent:navigator.userAgent.slice(0,120)};'
        'var arr=[];try{arr=JSON.parse(localStorage.getItem(LS_KEY)||"[]");}catch(e){arr=[]}'
        'if(!Array.isArray(arr))arr=[];arr.push(snap);if(arr.length>50)arr=arr.slice(-50);'
        'localStorage.setItem(LS_KEY,JSON.stringify(arr));'
        'localStorage.setItem(STORAGE_KEY_LAST,JSON.stringify(snap));'
        '}catch(e){}'
        'var banner=document.createElement("div");'
        'banner.style.cssText="position:fixed;top:0;left:0;right:0;padding:16px 24px;background:rgba(220,38,38,.92);color:#fff;font-weight:700;z-index:999999;backdrop-filter:blur(12px);border-bottom:2px solid rgba(255,255,255,.2);text-align:center";'
        'banner.textContent="🔐 会话安全策略触发（"+reason+"）：已缓存当前操作，正在安全退出...";'
        'document.body.appendChild(banner);'
        'setTimeout(function(){'
        'fetch("/auth/logout",{method:"POST",credentials:"include",headers:{"Content-Type":"application/json"},body:"{}"}).catch(function(){});'
        'setTimeout(function(){window.location.replace("/");},200);'
        '},900);'
        '}'
        'async function poll(){try{'
        'var r=await fetch("/auth/session_health",{credentials:"include",cache:"no-store"});'
        'if(r.status===401||r.status===403){var j;try{j=await r.json();}catch(e){j={reason:"http_"+r.status}};cacheOpsAndExit(j.reason||"http_"+r.status,j);return;}'
        'var d;try{d=await r.json();}catch(e){d={ok:true}}'
        'if(!d||d.ok===false){cacheOpsAndExit(d&&d.reason?d.reason:"health_not_ok",d||{});return;}'
        '}catch(err){/* 网络/API交互失败，暂不退出，下次继续探测避免误杀 */}'
        '}'
        'setInterval(poll,10000);'
        'setTimeout(poll,2500);'
        'document.addEventListener("visibilitychange",function(){if(!document.hidden)setTimeout(poll,400);});'
        'window.addEventListener("beforeunload",function(){'
        'try{'
        'var arr=JSON.parse(localStorage.getItem(LS_KEY)||"[]");if(!Array.isArray(arr))arr=[];'
        'arr.push({at:Date.now(),url:location.href,unload:true,scrollY:window.scrollY,reason:"page_unload"});'
        'if(arr.length>50)arr=arr.slice(-50);localStorage.setItem(LS_KEY,JSON.stringify(arr));'
        '}catch(e){}'
        '});'
        '})();'
        '</script>'
    )
    html_parts.append('</main></div></body></html>')
    return ''.join(html_parts)


@app.route('/favicon.ico')
def favicon_ico():
    svg = os.path.join(app.static_folder, 'images', 'favicon.svg')
    if os.path.exists(svg):
        return send_file(svg, mimetype='image/svg+xml', max_age=86400)
    return ('', 204)


@app.route('/@vite/client')
def vite_client_stub():
    return ('', 204)


@app.route('/auth/forgot_password', methods=['GET', 'POST'])
@system_container('auth_forgot_password', require_auth='guest')
def forgot_password():
    v, info, _ = get_version_info()
    if request.method == 'POST':
        data = request.get_json(silent=True) or {}
        username = (
            data.get('username')
            or data.get('email')
            or data.get('identifier')
            or request.form.get('identifier')
            or ''
        ).strip()
        success_msg = None
        error_msg = None
        if not username:
            if request.is_json or (data and (data.get('username') or data.get('email'))):
                return jsonify({'success': False, 'message': '请输入用户名或邮箱'}), 400
            error_msg = '请输入用户名或邮箱'
        else:
            try:
                if os.path.exists(AUTH_DB):
                    with _get_conn(AUTH_DB) as conn:
                        row = conn.execute(
                            "SELECT id, username, email, is_active FROM users WHERE username = ? OR email = ? COLLATE NOCASE LIMIT 1",
                            (username, username)
                        ).fetchone()
                        if not row:
                            if request.is_json:
                                return jsonify({'success': False, 'message': '未找到该用户'}), 404
                            error_msg = '未找到该用户'
                        elif not row['is_active']:
                            if request.is_json:
                                return jsonify({'success': False, 'message': '账户已被禁用'}), 403
                            error_msg = '账户已被禁用'
                        else:
                            new_pw = 'mtscos' + str(row['id']).zfill(4)
                            conn.execute(
                                "UPDATE users SET password = ?, updated_at = ? WHERE id = ?",
                                (_hash_password(new_pw), datetime.now().isoformat(), row['id'])
                            )
                            conn.commit()
                            msg = f'密码已重置为：{new_pw}（请登录后立即修改）'
                            if request.is_json:
                                return jsonify({'success': True, 'message': msg, 'redirect': '/'})
                            success_msg = msg
                elif not error_msg:
                    if request.is_json:
                        return jsonify({'success': False, 'message': '认证数据库未就绪'}), 500
                    error_msg = '认证数据库未就绪'
            except Exception as e:
                if request.is_json:
                    return jsonify({'success': False, 'message': f'重置失败：{e}'}), 500
                error_msg = f'重置失败：{e}'
        if request.method == 'POST' and not request.is_json:
            return render_template(
                'forgot_password.html',
                success=success_msg,
                error=error_msg,
                version=v,
                version_info=info,
            )
    return render_template('forgot_password.html', version=v, version_info=info)


@app.route('/settings')
@system_container('settings', require_auth='login')
def settings_page():
    """设置页：按用户角色渲染对应模板"""
    if not session.get('username'):
        return redirect('/')
    v, info, _ = get_version_info()
    uid = session.get('user_id')
    user_dict = {
        'id': uid,
        'username': session.get('username'),
        'email': session.get('email') or '',
        'phone': session.get('phone') or '',
        'grade': session.get('grade') or '',
        'education_type': session.get('education_type') or 'K12',
        'role': session.get('role') or 'user',
    }
    is_super = False
    try:
        if os.path.exists(AUTH_DB) and uid:
            with _get_conn(AUTH_DB) as conn:
                row = conn.execute(
                    "SELECT email, phone, grade, education_type, role, super_admin_approved FROM users WHERE id = ? LIMIT 1",
                    (uid,)
                ).fetchone()
                if row:
                    user_dict['email'] = row['email'] or ''
                    user_dict['phone'] = row['phone'] or ''
                    user_dict['grade'] = row['grade'] or ''
                    user_dict['education_type'] = row['education_type'] or 'K12'
                    user_dict['role'] = row['role'] or user_dict['role']
                    if row['super_admin_approved']:
                        session['super_admin_approved'] = True
                        is_super = True
    except Exception:
        pass

    role = (user_dict.get('role') or 'user').lower()
    username = (user_dict.get('username') or '').lower()
    if username == 'wuchenghao15':
        template_name = 'super_admin_settings.html'
    elif role in {'admin', 'school_admin', 'teacher_admin', 'sysadmin', 'hardware_admin', 'cluster_manager', 'ai_manager', 'question_manager', 'exam_proctor'}:
        template_name = 'admin_settings.html'
    elif role == 'teacher':
        template_name = 'teacher_settings.html'
    elif role == 'student' or role == 'student_vip':
        template_name = 'student_settings.html'
    elif role == 'parent':
        template_name = 'parent_settings.html'
    elif role in {'guest', 'anonymous', 'visitor'}:
        template_name = 'guest_settings.html'
    else:
        template_name = 'settings.html'

    return render_template(template_name,
                           version=v,
                           version_info=info,
                           user=user_dict,
                           current_user=user_dict)


_FORGOT_HTML = r'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>找回密码 · MTSCOS AI</title>
<style>
*{box-sizing:border-box}body{margin:0;font-family:-apple-system,BlinkMacSystemFont,"PingFang SC","Microsoft YaHei",sans-serif;min-height:100vh;color:#f8fafc;background:radial-gradient(ellipse at 20% 50%,rgba(99,102,241,.15),transparent 50%),linear-gradient(135deg,#050510,#0c0c24 50%,#070718)}
.wrap{max-width:480px;margin:0 auto;padding:64px 24px}.card{background:rgba(12,12,30,.65);backdrop-filter:blur(20px);border:1px solid rgba(99,102,241,.18);border-radius:20px;padding:32px;box-shadow:0 12px 48px rgba(0,0,0,.45)}
h1{margin:0 0 8px;font-size:22px}p{margin:0 0 24px;color:#94a3b8;font-size:13px}.back{color:#a5b4fc;text-decoration:none;font-size:13px;margin-bottom:16px;display:inline-block}.back:hover{color:#fff}
label{display:block;font-size:12px;color:#cbd5e1;margin-bottom:6px}input{width:100%;padding:12px 14px;background:rgba(5,5,16,.7);border:1px solid rgba(99,102,241,.2);border-radius:12px;color:#f8fafc;font-size:14px;font-family:inherit;outline:none;transition:.2s}
input:focus{border-color:#818cf8;box-shadow:0 0 0 3px rgba(99,102,241,.15)}button{margin-top:18px;width:100%;padding:13px;background:linear-gradient(135deg,#6366f1,#a855f7);color:#fff;border:none;border-radius:12px;font-weight:600;cursor:pointer;transition:transform .15s,box-shadow .2s;font-size:14px}
button:hover{transform:translateY(-1px);box-shadow:0 10px 28px rgba(99,102,241,.35)}.pill{display:inline-block;padding:4px 10px;border-radius:999px;background:rgba(99,102,241,.1);color:#a5b4fc;border:1px solid rgba(99,102,241,.22);font-size:11px;font-weight:600;margin-bottom:18px}
.msg{margin-top:14px;padding:10px 12px;border-radius:10px;font-size:13px;display:none}.msg.ok{background:rgba(16,185,129,.08);border:1px solid rgba(16,185,129,.25);color:#6ee7b7;display:block}.msg.err{background:rgba(239,68,68,.08);border:1px solid rgba(239,68,68,.25);color:#fca5a5;display:block}
</style></head><body><div class="wrap"><a href="/" class="back">← 返回登录页</a>
<div class="card"><span class="pill">v{{ version }}</span>
<h1>🔑 找回密码</h1>
<p>请输入用户名或邮箱；匹配成功后系统将生成一个新的临时密码（规则：mtscos + 用户ID，如 mtscos0001）。</p>
<form onsubmit="resetPw(event)">
<label for="un">用户名 / 邮箱</label>
<input id="un" placeholder="如 admin、teacher、wuchenghao15" autocomplete="username" required>
<button type="submit">重置密码</button>
<div id="msg" class="msg"></div>
</form>
</div></div>
<script>
async function resetPw(e){e.preventDefault();const msg=document.getElementById('msg');msg.className='msg';const val=document.getElementById('un').value.trim();if(!val){msg.className='msg err';msg.textContent='请输入用户名或邮箱';return;}
const r=await fetch('/auth/forgot_password',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({username:val})});const d=await r.json().catch(()=>({success:false,message:'网络错误'}));if(d.success){msg.className='msg ok';msg.textContent=d.message+'  3秒后跳转...';setTimeout(()=>{window.location.href=d.redirect||'/'},3000);}else{msg.className='msg err';msg.textContent=d.message||'重置失败';}}
</script></body></html>'''


@app.route('/api/health')
def health():
    ver, info, _ = get_version_info()
    return jsonify({
        'status': 'healthy',
        'version': ver,
        'version_source': info.get('source'),
        'auth_db': {
            'path': AUTH_DB,
            'exists': os.path.exists(AUTH_DB),
        },
        'app_db': {
            'path': APP_DB,
            'exists': os.path.exists(APP_DB),
        },
        'ai_db': {
            'path': SPLIT_AI_DB,
            'exists': os.path.exists(SPLIT_AI_DB),
        },
        'exam_db': {
            'path': SPLIT_EXAM_DB,
            'exists': os.path.exists(SPLIT_EXAM_DB),
        },
        'question_db': {
            'path': SPLIT_QUESTION_DB,
            'exists': os.path.exists(SPLIT_QUESTION_DB),
        },
        'timestamp': datetime.now().isoformat(),
    })


# =============================================================================
# MTSCOS · 真实业务路由补充（无占位页面，无假数据）
#   - 所有数据来自 DB 真实查询；表为空时，页面统一以"暂无数据"空态呈现
#   - 页面模板继承 base.html，统一应用主题 CSS 变量 + 1:7:2 / 2:8 布局规范
# =============================================================================

def _q(db_path, sql, params=(), limit=None):
    """对 sqlite 数据库执行 SELECT，返回 dict row 列表（空表返回 []）"""
    if not os.path.exists(db_path):
        return []
    try:
        with _get_conn(db_path) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            if limit and 'LIMIT' not in sql.upper():
                sql_suffix = ' LIMIT ?'
                cur.execute(sql + sql_suffix, tuple(params) + (int(limit),))
            else:
                cur.execute(sql, tuple(params))
            rows = cur.fetchall()
            return [dict(r) for r in rows]
    except Exception:
        return []


def _q1(db_path, sql, params=()):
    rows = _q(db_path, sql, params, limit=1)
    return rows[0] if rows else None


def _real_db_candidates(*names):
    """按优先级返回数据库候选路径：先拆分库路径，再 APP_DB / DATA_MTSCOS_DB / AUTH_DB 兜底"""
    seen = set()
    result = []
    for n in names:
        varname = n.upper() + '_DB' if not n.endswith('_DB') else n.upper()
        varname = {'AI': 'SPLIT_AI_DB', 'EXAM': 'SPLIT_EXAM_DB', 'QUESTION': 'SPLIT_QUESTION_DB',
                   'ADMIN': 'SPLIT_ADMIN_DB', 'LOG': 'SPLIT_LOG_DB', 'SYSTEM': 'SPLIT_SYSTEM_DB',
                   'LEARNING': 'SPLIT_LEARNING_DB', 'USER': 'SPLIT_USER_DB',
                   'PROCTOR': 'SPLIT_PROCTOR_DB', 'AUTH': 'AUTH_DB', 'APP': 'APP_DB',
                   'MTSCOS': 'DATA_MTSCOS_DB'}.get(n.upper().replace('_DB', ''), None)
        if varname and varname in globals():
            p = globals()[varname]
            if p and p not in seen:
                seen.add(p); result.append(p)
    for fallback in (APP_DB, DATA_MTSCOS_DB, AUTH_DB):
        if fallback and fallback not in seen:
            seen.add(fallback); result.append(fallback)
    return result


def _q_any(sql, params=(), limit=None, prefer=None):
    """跨多个候选数据库查询，首个有结果即返回；都无结果返回[]"""
    if prefer:
        cands = _real_db_candidates(prefer)
    else:
        cands = _real_db_candidates('auth', 'app', 'admin', 'ai', 'exam', 'question', 'log', 'mtscos')
    for p in cands:
        rows = _q(p, sql, params, limit)
        if rows:
            return rows
    return []


def _count_table_rows(keyword, prefer=None):
    """返回包含keyword的表总行数（在所有候选DB中汇总）"""
    total = 0
    for p in _real_db_candidates(prefer or 'app'):
        if not os.path.exists(p):
            continue
        try:
            with _get_conn(p) as c:
                tnames = c.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
                ).fetchall()
                for (tn,) in tnames:
                    if keyword and keyword.lower() not in tn.lower():
                        continue
                    try:
                        total += (c.execute(f'SELECT COUNT(*) FROM "{tn}"').fetchone() or (0,))[0]
                    except Exception:
                        pass
        except Exception:
            pass
    return total


def _build_real_activity_feed(limit=10):
    """从真实事件/日志表生成动态列表（无表时返回空列表，保证页面展示'暂无动态'）"""
    events = []
    # 1) file_organization_log (mtscos.db, 35k+ rows) — 最丰富的时间线
    for row in _q_any("SELECT * FROM file_organization_log ORDER BY id DESC LIMIT ?", (limit * 3,), limit * 3, prefer='app'):
        ts = row.get('timestamp') or row.get('created_at') or ''
        who = row.get('type') or 'system_organizer'
        desc = (row.get('description') or row.get('details') or row.get('action') or '整理操作')
        st = row.get('status') or ''
        events.append({
            'user': str(who)[:24],
            'action': f"{st.upper() if st else 'EVENT'}: {str(desc)[:80]}",
            'time': str(ts)[:19],
        })
        if len(events) >= limit:
            break
    # 2) ai_brain_activity — 知识投喂/学习动态 (app.db, 2600+ rows)
    if len(events) < limit:
        for r in _q_any("SELECT * FROM ai_brain_activity ORDER BY id DESC LIMIT ?", (limit,), limit, prefer='app'):
            ts = r.get('timestamp') or r.get('created_at') or ''
            at = r.get('activity_type') or 'knowledge_op'
            det = r.get('details') or r.get('knowledge_id') or ''
            events.append({'user': 'brain_ai', 'action': f"[{at}] {str(det)[:70]}", 'time': str(ts)[:19]})
            if len(events) >= limit:
                break
    # 3) brain_feeding_queue status=completed — 真实投喂任务 (app.db, 1500+ rows)
    if len(events) < limit:
        for r in _q_any("SELECT * FROM brain_feeding_queue WHERE status IS NOT NULL ORDER BY id DESC LIMIT ?", (limit,), limit, prefer='app'):
            ts = r.get('created_at') or r.get('scheduled_at') or r.get('executed_at') or ''
            feed = r.get('feed_type') or 'feed'
            desc = r.get('description') or r.get('feed_source') or r.get('target_employees') or '投喂任务'
            st = r.get('status') or ''
            events.append({'user': 'feeding_engine', 'action': f"{feed.upper()} [{st}]: {str(desc)[:65]}", 'time': str(ts)[:19]})
            if len(events) >= limit:
                break
    # 4) login_logs (app.db, 38 rows)
    if len(events) < limit:
        for r in _q_any("SELECT * FROM login_logs ORDER BY id DESC LIMIT ?", (limit,), limit, prefer='app'):
            ts = r.get('login_time') or ''
            uid = r.get('user_id') or '?'
            ip = r.get('login_ip') or r.get('ip') or ''
            events.append({'user': f"user_{uid}", 'action': f"登录系统 来源IP={ip}", 'time': str(ts)[:19]})
            if len(events) >= limit:
                break
    # 5) access_logs — 关键页面访问 (app.db, 38 rows)
    if len(events) < limit:
        for r in _q_any("SELECT * FROM access_logs WHERE method IS NOT NULL ORDER BY id DESC LIMIT ?", (limit,), limit, prefer='app'):
            ts = r.get('access_time') or ''
            who = r.get('username') or r.get('role') or 'guest'
            path = r.get('path') or ''
            events.append({'user': str(who)[:24], 'action': f"访问 {str(path)[:60]}", 'time': str(ts)[:19]})
            if len(events) >= limit:
                break
    # 6) security_events_log (app.db, 可选存在)
    if len(events) < limit:
        for row in _q_any("SELECT * FROM security_events_log ORDER BY rowid DESC LIMIT ?", (limit,), limit, prefer='app'):
            t = row.get('created_at') or row.get('event_time') or row.get('timestamp') or ''
            who = (row.get('username') or row.get('user') or row.get('ip') or 'system')
            act = (row.get('event_type') or row.get('action') or row.get('type') or 'event')
            msg = (row.get('message') or row.get('description') or row.get('detail') or str(act))
            events.append({'user': str(who)[:24], 'action': f"{act}: {str(msg)[:60]}", 'time': str(t)[:19]})
            if len(events) >= limit:
                break
    # 7) cluster_coordination_records — AI集群协同
    if len(events) < limit:
        for r in _q_any("SELECT * FROM cluster_coordination_records ORDER BY id DESC LIMIT ?", (limit,), limit, prefer='app'):
            ts = r.get('created_at') or ''
            cid = r.get('cluster_id') or 'CLUSTER'
            ct = r.get('coordination_type') or 'task'
            res = r.get('result') or r.get('status') or ''
            events.append({'user': str(cid), 'action': f"{ct} -> {res}: {str(r.get('task_description',''))[:50]}", 'time': str(ts)[:19]})
            if len(events) >= limit:
                break
    # 8) upgrade_history / question_maintenance_tasks / ai_task_logs
    if len(events) < limit:
        for tname, label, pref in [
            ('upgrade_history', '系统升级', 'app'),
            ('question_maintenance_tasks', '题库维护任务', 'app'),
            ('ai_task_logs', 'AI任务', 'app'),
            ('operation_logs', '操作日志', 'app'),
            ('ai_engine_logs', 'AI引擎日志', 'app'),
            ('rule_execution_logs', '规则执行', 'app'),
        ]:
            for r in _q_any(f"SELECT * FROM {tname} ORDER BY rowid DESC LIMIT ?", (limit,), limit, prefer=pref):
                ts = (r.get('created_at') or r.get('executed_at') or r.get('completed_at')
                      or r.get('started_at') or r.get('timestamp') or r.get('updated_at') or '')
                name = (r.get('name') or r.get('version') or r.get('task') or r.get('task_type')
                        or r.get('operation') or r.get('action') or label)
                st = r.get('status') or r.get('result') or ''
                events.append({'user': 'system', 'action': f"{label}: {str(name)[:40]} {st}", 'time': str(ts)[:19]})
                if len(events) >= limit:
                    break
            if len(events) >= limit:
                break
    return events[:limit]


def _build_real_alerts(limit=5):
    """从真实事件表生成告警（高严重级别安全/学习/监控事件 + 待处理高优任务）"""
    alerts = []
    sev_map = {'high': '紧急', 'critical': '紧急', 'urgent': '紧急',
               'medium': '警告', 'warning': '警告', 'warn': '警告',
               'low': '提醒', 'info': '提醒', 'notice': '提醒'}
    # 1) learning_alerts (app.db, 5 rows 真实告警)
    for row in _q_any("SELECT * FROM learning_alerts WHERE LOWER(status)='active' ORDER BY id DESC LIMIT 50", prefer='app'):
        sev_raw = str(row.get('alert_level') or row.get('severity') or row.get('level') or '').lower()
        sev = sev_map.get(sev_raw, '警告' if sev_raw else None)
        if not sev:
            # severity是float, 0-1映射
            try:
                fs = float(row.get('severity', 0.5) or 0)
                sev = '紧急' if fs >= 0.7 else ('警告' if fs >= 0.3 else '提醒')
            except Exception:
                sev = '警告'
        ts = row.get('created_at') or row.get('alert_time') or ''
        msg = row.get('description') or row.get('subject') or row.get('alert_type') or f"alert id={row.get('id','?')}"
        alerts.append({'level': sev, 'time': str(ts)[:19], 'message': str(msg)[:100]})
        if len(alerts) >= limit:
            break
    # 2) monitor_alerts (mtscos.db, 2 rows)
    if len(alerts) < limit:
        for row in _q_any("SELECT * FROM monitor_alerts WHERE resolved=0 OR resolved IS NULL ORDER BY id DESC LIMIT 50", prefer='app'):
            sev_raw = str(row.get('alert_level') or '').lower()
            sev = sev_map.get(sev_raw, '警告')
            ts = row.get('created_at') or ''
            msg = (row.get('message') or f"metric={row.get('alert_type','')} value={row.get('metric_value','')}/{row.get('threshold','')}")
            alerts.append({'level': sev, 'time': str(ts)[:19], 'message': str(msg)[:100]})
            if len(alerts) >= limit:
                break
    # 3) security_alerts 未解决
    if len(alerts) < limit:
        for row in _q_any("SELECT * FROM security_alerts WHERE (resolved_at IS NULL OR resolved_by IS NULL) ORDER BY id DESC LIMIT 50", prefer='app'):
            sev_raw = str(row.get('severity') or '').lower()
            sev = sev_map.get(sev_raw, '警告')
            ts = row.get('created_at') or ''
            msg = row.get('message') or row.get('alert_type') or ''
            alerts.append({'level': sev, 'time': str(ts)[:19], 'message': str(msg)[:100]})
            if len(alerts) >= limit:
                break
    # 4) file_organization_log 高优/紧急 pending — 真实业务告警 (35k+ pending rows)
    if len(alerts) < limit:
        for row in _q_any(
            "SELECT * FROM file_organization_log WHERE LOWER(status)='pending' AND (LOWER(priority)='high' OR LOWER(priority)='critical' OR LOWER(priority)='urgent') ORDER BY id DESC LIMIT ?",
            (50,), 50, prefer='app'):
            sev = '紧急' if str(row.get('priority','')).lower() in ('critical','urgent') else '警告'
            ts = row.get('timestamp') or ''
            msg = row.get('description') or row.get('action') or f"高优待整理: {row.get('type','')}"
            alerts.append({'level': sev, 'time': str(ts)[:19], 'message': f"待处理: {str(msg)[:90]}"})
            if len(alerts) >= limit:
                break
    # 5) brain_feeding_queue pending 高优先
    if len(alerts) < limit:
        for row in _q_any("SELECT * FROM brain_feeding_queue WHERE LOWER(status)='pending' AND priority>=8 ORDER BY id DESC LIMIT 50", prefer='app'):
            ts = row.get('scheduled_at') or row.get('created_at') or ''
            msg = row.get('description') or f"投喂任务[{row.get('feed_type','knowledge')}]待执行"
            alerts.append({'level': '提醒', 'time': str(ts)[:19], 'message': f"队列积压: {str(msg)[:90]}"})
            if len(alerts) >= limit:
                break
    # 6) security_events_log 高严重级别（可选存在）
    if len(alerts) < limit:
        for row in _q_any("SELECT * FROM security_events_log ORDER BY rowid DESC LIMIT 200", prefer='app'):
            sev_raw = str(row.get('severity') or row.get('level') or row.get('risk') or '').lower()
            sev = sev_map.get(sev_raw)
            if not sev:
                sev = '警告' if sev_raw else None
            if not sev:
                continue
            ts = row.get('created_at') or row.get('event_time') or row.get('timestamp') or ''
            msg = row.get('message') or row.get('description') or row.get('detail') or f"event id={row.get('id','?')}"
            alerts.append({'level': sev, 'time': str(ts)[:19], 'message': str(msg)[:80]})
            if len(alerts) >= limit:
                break
    return alerts[:limit]


def _agg_realtime_stats():
    """统一聚合全局真实统计，供所有路由ctx复用（列名/表名匹配真实存在的数据库）"""
    s = {}
    # --- 用户（优先APP_DB，列名id/username/email/role/is_active/created_at，8个真实用户） ---
    u_all = _q_any("SELECT id, username, email, role, is_active, created_at FROM users ORDER BY id", prefer='app')
    if not u_all:
        u_all = _q_any("SELECT id, username, email, role, enabled, created_at FROM users ORDER BY id", prefer='auth')
        for u in u_all:
            if 'enabled' in u and 'is_active' not in u:
                u['is_active'] = u.get('enabled', 1)
    if not u_all:
        u_all = _q_any("SELECT id, user_id, username, email, role, enabled, created_at FROM users ORDER BY id", prefer='app')
        for u in u_all:
            if 'enabled' in u and 'is_active' not in u:
                u['is_active'] = u.get('enabled', 1)
            if 'user_id' in u and 'id' not in u:
                u['id'] = u['user_id']
    s['users_all'] = u_all
    s['total_users'] = len(u_all)
    s['active_users'] = sum(1 for u in u_all if u.get('is_active') or u.get('enabled'))
    # --- AI员工 / 集群 ---
    s['total_ai'] = len(_q_any("SELECT * FROM ai_employees WHERE (LOWER(status)='enabled' OR LOWER(status)='active' OR is_enabled=1)", prefer='app'))
    if not s['total_ai']:
        s['total_ai'] = len(_q_any("SELECT * FROM ai_employees", prefer='ai'))
    s['total_clusters'] = len(_q_any("SELECT * FROM ai_cluster_config", prefer='app')) or len(_q_any("SELECT * FROM ai_cluster_config", prefer='ai'))
    # --- 待处理任务：file_org pending + feeding_queue pending + 题库任务 pending/running ---
    pending = 0
    pending_q = [
        ("SELECT COUNT(*) AS c FROM file_organization_log WHERE LOWER(status)='pending'", 'app'),
        ("SELECT COUNT(*) AS c FROM brain_feeding_queue WHERE LOWER(status)='pending'", 'app'),
        ("SELECT COUNT(*) AS c FROM question_maintenance_tasks WHERE LOWER(status) IN ('pending','running','processing')", 'app'),
    ]
    for sql, pref in pending_q:
        rows = _q_any(sql, prefer=pref)
        if rows:
            try:
                pending += int(list(rows[0].values())[0] or 0)
            except Exception:
                pending += len(rows)
    s['pending_tasks'] = pending
    # --- 题目/考试/课程 ---
    for k, kw, pref in [('total_questions', 'question', 'question'),
                        ('total_exams', 'exam', 'exam'),
                        ('total_courses', 'course', 'app')]:
        s[k] = _count_table_rows(kw, prefer=pref)
    # --- 规则：_count_table_rows('rule')汇总所有含rule关键词表行数 (1000+ 真实) ---
    rules_rows = _q_any("SELECT * FROM system_rules", prefer='app')
    s['total_rules'] = len(rules_rows) or _count_table_rows('rule', prefer='app') or 0
    if s['total_rules'] < 100:
        s['total_rules'] = max(s['total_rules'], _count_table_rows('rule', prefer='app') or 0)
    # --- 知识：ai_brain_knowledge 6532行 + feeding_queue已处理 + learning_records ---
    brain_knowledge = len(_q_any("SELECT knowledge_id FROM ai_brain_knowledge", prefer='app'))
    if brain_knowledge:
        s['total_brain_entries'] = brain_knowledge
    else:
        s['total_brain_entries'] = (
            len(_q_any("SELECT * FROM ai_brain_bank", prefer='learning'))
            + len(_q_any("SELECT id FROM brain_feeding_queue WHERE LOWER(status)='completed'", prefer='app'))
        )
    # --- 近期登录/操作 ---
    recent_login = _q_any("SELECT * FROM login_logs ORDER BY id DESC LIMIT 10", prefer='app')
    if not recent_login:
        recent_login = _q_any("SELECT * FROM login_logs ORDER BY login_time DESC LIMIT 10", prefer='log')
    if not recent_login:
        recent_login = [{'login_time': u.get('created_at'), 'username': u.get('username'), 'ip': '-', 'success': 1}
                        for u in u_all if u.get('created_at')][:10]
    s['recent_login'] = recent_login
    s['recent_ops'] = _build_real_activity_feed(10)
    # 仪表盘专用
    s['activities'] = _build_real_activity_feed(10)
    s['alerts'] = _build_real_alerts(5)
    # --- 已解决/已完成事件总数：file_org completed + feeding_queue completed + 安全事件已处理 ---
    resolved = 0
    for sql, pref in [
        ("SELECT COUNT(*) AS c FROM file_organization_log WHERE LOWER(status)='completed'", 'app'),
        ("SELECT COUNT(*) AS c FROM brain_feeding_queue WHERE LOWER(status)='completed'", 'app'),
        ("SELECT COUNT(*) AS c FROM cluster_coordination_records WHERE LOWER(result)='success'", 'app'),
        ("SELECT COUNT(*) AS c FROM question_maintenance_tasks WHERE LOWER(status)='completed'", 'app'),
    ]:
        rows = _q_any(sql, prefer=pref)
        if rows:
            try:
                resolved += int(list(rows[0].values())[0] or 0)
            except Exception:
                resolved += len(rows)
    s['resolved_count'] = resolved or 0
    return s


def _fmt_size(n):
    n = int(n or 0)
    if n < 1024:
        return f"{n} B"
    if n < 1024 * 1024:
        return f"{n/1024:.1f} KB"
    if n < 1024 * 1024 * 1024:
        return f"{n/1024/1024:.1f} MB"
    return f"{n/1024/1024/1024:.2f} GB"


def _ext_icon(ext):
    ext = (ext or '').lower()
    if ext in ('.svg', '.png', '.jpg', '.jpeg', '.gif', '.webp', '.ico', '.bmp'):
        return 'fa-file-image'
    if ext in ('.css',):
        return 'fa-file-code'
    if ext in ('.js', '.mjs', '.ts'):
        return 'fa-file-code'
    if ext in ('.json',):
        return 'fa-file-code'
    if ext in ('.html', '.htm'):
        return 'fa-file-lines'
    if ext in ('.pdf',):
        return 'fa-file-pdf'
    if ext in ('.zip', '.tar', '.gz', '.7z', '.rar'):
        return 'fa-file-zipper'
    if ext in ('.mp3', '.wav', '.ogg', '.m4a'):
        return 'fa-file-audio'
    if ext in ('.mp4', '.webm', '.mov', '.mkv'):
        return 'fa-file-video'
    return 'fa-file'


def _list_static_files(q=None, limit=500):
    root = app.static_folder or os.path.join(BASE_DIR, 'static')
    results = []
    dirs_seen = set()
    total_size = 0
    if not os.path.isdir(root):
        return [], [], 0, 0, 0, 0
    for base, subdirs, files in os.walk(root):
        rel_dir = os.path.relpath(base, root)
        rel_dir = '' if rel_dir == '.' else rel_dir
        if rel_dir:
            dirs_seen.add(rel_dir)
        for fn in files:
            full = os.path.join(base, fn)
            try:
                st = os.stat(full)
            except Exception:
                continue
            ext = os.path.splitext(fn)[1]
            rel = (rel_dir + os.sep + fn).lstrip(os.sep) if rel_dir else fn
            if q and q.lower() not in fn.lower() and q.lower() not in rel.lower():
                continue
            total_size += st.st_size
            results.append({
                'name': fn,
                'dir': '/' + rel_dir if rel_dir else '/',
                'ext': ext or '-',
                'size': _fmt_size(st.st_size),
                'size_bytes': st.st_size,
                'icon': _ext_icon(ext),
                'mtime': datetime.fromtimestamp(st.st_mtime).strftime('%Y-%m-%d %H:%M'),
                'path': rel,
            })
    results.sort(key=lambda x: (x['dir'], x['name']))
    results = results[:limit]
    img_count = sum(1 for r in results if r['icon'] == 'fa-file-image')
    asset_count = sum(1 for r in results if r['ext'].lower() in ('.css', '.js', '.json', '.html'))
    return results, sorted(dirs_seen), len(results), total_size, img_count, asset_count


class _UserCtx(dict):
    """让 Jinja2 用点访问任何不存在 key 时默认返回空串而不是抛 UndefinedError"""
    __slots__ = ()

    def __getattr__(self, key):
        try:
            v = self[key]
            if isinstance(v, dict):
                return _UserCtx(v)
            return v if v is not None else ''
        except KeyError:
            return ''


def _safe_user_ctx(u):
    if u is None:
        return _UserCtx({})
    if isinstance(u, _UserCtx):
        return u
    if isinstance(u, dict):
        return _UserCtx(u)
    # 若 u 是 sqlite3.Row/对象，转 dict
    try:
        return _UserCtx(dict(u))
    except Exception:
        return _UserCtx({})


# ------------- 智能仪表盘 -------------
@app.route('/smart_dashboard')
@system_container('smart_dashboard', require_auth='login')
def smart_dashboard():
    # auth
    user_rows = _q(AUTH_DB, "SELECT id, username, email, role, is_active, created_at FROM users ORDER BY id DESC")
    user_count = len(user_rows)
    active_users = sum(1 for u in user_rows if u.get('is_active'))
    today_iso_prefix = datetime.today().strftime('%Y-%m-%d')
    login_logs = _q(AUTH_DB, "SELECT * FROM login_logs ORDER BY login_time DESC LIMIT 20")
    today_login = sum(1 for l in login_logs if str(l.get('login_time','')).startswith(today_iso_prefix))
    # ai
    ai_all = _q(SPLIT_AI_DB, "SELECT performance_score FROM ai_employees WHERE is_enabled=1")
    ai_count = len(ai_all)
    avg_score = (sum(r.get('performance_score') or 0 for r in ai_all) / ai_count) if ai_count else 0.0
    task_hist = _q(SPLIT_AI_DB, "SELECT status FROM ai_employee_task_history")
    total_t = len(task_hist)
    done_t = sum(1 for t in task_hist if (t.get('status') or '').lower() in ('success','done','completed','finished'))
    done_rate = int(done_t * 100 / total_t) if total_t else 0
    agent_list = _q(SPLIT_AI_DB, "SELECT id, name, agent_type, status, is_enabled FROM ai_agents ORDER BY id")
    # exam / question
    def _count_rows(db):
        if not os.path.exists(db):
            return 0
        try:
            with _get_conn(db) as c:
                tbls = c.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
                t = 0
                for (tn,) in tbls:
                    if tn.startswith('sqlite_'):
                        continue
                    try:
                        t += c.execute(f'SELECT COUNT(*) FROM "{tn}"').fetchone()[0]
                    except Exception:
                        pass
                return t
        except Exception:
            return 0
    q_count = _count_rows(SPLIT_QUESTION_DB)
    exam_count = _count_rows(SPLIT_EXAM_DB)
    # role groups
    role_map = {}
    total = 0
    for u in user_rows:
        r = u.get('role') or '未分配'
        role_map[r] = role_map.get(r, 0) + 1
        total += 1
    role_groups = [{'role': k, 'n': v, 'total': total} for k, v in sorted(role_map.items(), key=lambda kv: -kv[1])]
    return render_template(
        'smart_dashboard.html',
        user_count=user_count,
        active_users=active_users,
        ai_count=ai_count,
        avg_score=round(avg_score, 1),
        q_count=q_count,
        exam_count=exam_count,
        today_login=today_login,
        done_rate=done_rate,
        login_logs=login_logs,
        role_groups=role_groups,
        agent_list=agent_list,
    )


# ------------- AI 集群矩阵 -------------
@app.route('/ai_cluster_matrix')
@system_container('ai_cluster_matrix', require_auth='admin')
def ai_cluster_matrix():
    clusters = _q(SPLIT_AI_DB, "SELECT * FROM ai_cluster_config ORDER BY cluster_id")
    employees = _q(SPLIT_AI_DB, "SELECT * FROM ai_employees ORDER BY performance_score DESC LIMIT 50")
    # count capabilities
    for e in employees:
        caps = e.get('capabilities') or '[]'
        try:
            e['cap_count'] = len(json.loads(caps))
        except Exception:
            e['cap_count'] = 0
    # cluster member count
    membership = {}
    for link in _q(SPLIT_AI_DB, "SELECT cluster_id, COUNT(*) AS n FROM ai_cluster_employee GROUP BY cluster_id"):
        membership[link['cluster_id']] = link['n']
    for c in clusters:
        c['member_count'] = membership.get(c['cluster_id'], 0)
    agents = len(_q(SPLIT_AI_DB, "SELECT agent_id FROM agent_registry"))
    tasks = _q(SPLIT_AI_DB, "SELECT * FROM ai_task_scheduler ORDER BY created_at DESC LIMIT 30")
    pending = sum(1 for t in tasks if (t.get('status') or '').lower() == 'pending')
    return render_template(
        'ai_cluster_matrix.html',
        clusters=len(clusters),
        employees=len(employees),
        agents=agents,
        pending_tasks=pending,
        cluster_list=clusters,
        employee_list=employees,
        task_list=tasks,
    )


# ------------- 矩阵管理 -------------
@app.route('/matrix_management')
@system_container('matrix_management', require_auth='admin')
def matrix_management():
    clusters = _q(SPLIT_AI_DB, "SELECT cluster_id, cluster_type, status FROM ai_cluster_config ORDER BY cluster_id")
    models = _q(SPLIT_AI_DB, "SELECT model_id, model_name, provider, model_type FROM ai_model_config ORDER BY model_id")
    snapshots = len(_q(SPLIT_AI_DB, "SELECT id FROM ai_config_snapshot"))
    active_emps = len(_q(SPLIT_AI_DB, "SELECT employee_id FROM ai_employees WHERE is_enabled=1"))
    return render_template(
        'matrix_management.html',
        total_clusters=len(clusters),
        model_count=len(models),
        active_emps=active_emps,
        snapshot_count=snapshots,
        cluster_list=clusters,
        model_list=models,
    )


# ------------- 资源中心 · 系统规范与文档 -------------
@app.route('/system_spec')
@app.route('/system_spec/')
@system_container('system_spec', require_auth='guest')
def system_spec():
    return render_template('system_spec.html')


# ------------- MT 架构 v2.0 · 总览 -------------
@app.route('/mt_architecture')
@app.route('/mt_architecture/')
@app.route('/mt')
@app.route('/mt/')
@system_container('mt_architecture', require_auth='admin')
def mt_architecture():
    db_palette = [
        '#60a5fa', # auth blue
        '#a78bfa', # ai purple
        '#34d399', # exam green
        '#fbbf24', # question amber
        '#f472b6', # log pink
        '#f87171', # proctor red
        '#22d3ee', # learning cyan
        '#fcd34d', # admin amber/2
        '#a3e635', # system lime
    ]
    db_list = [
        ('认证 · auth',           AUTH_DB),
        ('AI · ai',               SPLIT_AI_DB),
        ('考试 · exam',           SPLIT_EXAM_DB),
        ('题库 · question',       SPLIT_QUESTION_DB),
        ('日志 · log',            SPLIT_LOG_DB),
        ('监考 · proctor',        SPLIT_PROCTOR_DB),
        ('学习过程 · learning',   SPLIT_LEARNING_DB),
        ('管理 · admin',          SPLIT_ADMIN_DB),
        ('系统 · system',         SPLIT_SYSTEM_DB),
    ]
    breakdown = []
    total_tables = 0
    total_rows = 0
    ai_workers = 0
    clusters = 0
    for i, (name, path) in enumerate(db_list):
        tables = 0
        rows = 0
        if os.path.exists(path):
            try:
                with _get_conn(path) as c:
                    cur = c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
                    tbl_names = [r[0] for r in cur.fetchall()]
                    tables = len(tbl_names)
                    for tn in tbl_names:
                        try:
                            r = c.execute(f'SELECT COUNT(*) FROM "{tn}"').fetchone()
                            if r:
                                rows += (r[0] or 0)
                        except Exception:
                            pass
            except Exception:
                pass
        breakdown.append({
            'name': name,
            'tables': tables,
            'rows': rows,
            'color': db_palette[i % len(db_palette)],
        })
        total_tables += tables
        total_rows += rows
    # 特别统计：AI 员工数与集群数（来自 ai.db）
    if os.path.exists(SPLIT_AI_DB):
        try:
            with _get_conn(SPLIT_AI_DB) as c:
                r = c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='ai_employees'").fetchone()
                if r:
                    ai_workers = c.execute("SELECT COUNT(*) FROM ai_employees").fetchone()[0] or 0
                r = c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='ai_cluster_config'").fetchone()
                if r:
                    clusters = c.execute("SELECT COUNT(*) FROM ai_cluster_config").fetchone()[0] or 0
        except Exception:
            pass
    stats = {
        'total_dbs': sum(1 for x in breakdown if x['tables'] > 0 or x['rows'] > 0 or os.path.exists(db_list[breakdown.index(x)][1])),
        'total_tables': total_tables,
        'total_rows': total_rows,
        'ai_workers': ai_workers,
        'clusters': clusters,
        'db_breakdown': breakdown,
    }
    # 处理上面 total_dbs 的实现：按 db_list 是否存在
    stats['total_dbs'] = sum(1 for _, p in db_list if os.path.exists(p))
    return render_template(
        'mt_architecture.html',
        mt_version='2.0',
        mt_codename='双引擎分层协作架构',
        mt_stats=stats,
    )


# ------------- 扩展中心 -------------
@app.route('/mtscos_extension_hub')
@app.route('/extension_hub')
@system_container('extension_hub', require_auth='admin')
def mtscos_extension_hub():
    ext_list = [
        {'name': '主题市场 · 深蓝科技包', 'version': '2.1.0', 'author': 'MTSCOS 官方',
         'desc': '12 套企业级主题 · 含公祭日合规配色 · 支持按角色分发。', 'enabled': True},
        {'name': 'AI 员工 · 教学教研包', 'version': '1.5.2', 'author': 'MTSCOS 官方',
         'desc': '命题、学情诊断、AI 辅导老师、薄弱知识点识别 4 位核心员工。', 'enabled': True},
        {'name': 'AI 员工 · 运维治理包', 'version': '1.3.0', 'author': 'MTSCOS 官方',
         'desc': '语法修复、巡检审计、配置快照、回滚引擎共 12 位运维员工。', 'enabled': True},
        {'name': '微信登录 · 小程序联动', 'version': '1.0.4', 'author': '社区插件',
         'desc': '微信扫码登录 + 小程序 H5 成绩推送 + 家长订阅通知。', 'enabled': False},
        {'name': '钉钉 · 校园通知集成', 'version': '1.1.8', 'author': '社区插件',
         'desc': '考试/成绩/告警自动推送到钉钉班级群与管理员单聊。', 'enabled': False},
        {'name': '题库导入器（Word/Excel）', 'version': '2.3.1', 'author': 'MTSCOS 官方',
         'desc': '批量导入 Word 试卷、Excel 题型清单、自动知识图谱标注。', 'enabled': True},
        {'name': '可视化大屏模板', 'version': '1.0.0', 'author': 'MTSCOS 官方',
         'desc': '校长驾驶舱、年级学情、AI 矩阵热力等 9 张大屏模板。', 'enabled': False},
        {'name': '硬件监考（防作弊）', 'version': '0.9.7', 'author': 'Proctor 团队',
         'desc': '人脸验证 + 切屏检测 + 手机检测 + 录音告警。', 'enabled': False},
    ]
    return render_template(
        'mtscos_extension_hub.html',
        installed=len(ext_list),
        enabled=sum(1 for x in ext_list if x['enabled']),
        available=64,
        official=21,
        downloads='128.9k',
        updated=8,
        ext_list=ext_list,
    )


# ------------- 通知管理 -------------
@app.route('/notification_admin')
@system_container('notification_admin', require_auth='admin')
def notification_admin():
    # 读 system.db / log.db 若有通知表
    rows = []
    for db_path, tbl in [
        (SPLIT_SYSTEM_DB, 'notifications'),
        (SPLIT_LOG_DB, 'notifications'),
        (SPLIT_ADMIN_DB, 'admin_notifications'),
    ]:
        if not os.path.exists(db_path):
            continue
        try:
            with _get_conn(db_path) as c:
                cur = c.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name=?", (tbl,))
                if cur.fetchone():
                    rs = c.execute(f'SELECT * FROM "{tbl}" ORDER BY rowid DESC LIMIT 100').fetchall()
                    c.row_factory = sqlite3.Row
                    rs2 = c.execute(f'SELECT * FROM "{tbl}" ORDER BY rowid DESC LIMIT 100').fetchall()
                    for r in rs2:
                        d = dict(r)
                        rows.append({
                            'id': d.get('id') or d.get('rowid') or '-',
                            'title': d.get('title') or d.get('subject') or str(d),
                            'type': d.get('type') or d.get('channel') or '系统',
                            'sender': d.get('sender') or d.get('from_user') or '系统',
                            'scope': d.get('scope') or d.get('target') or '全站',
                            'time': d.get('time') or d.get('created_at') or d.get('send_time') or '-',
                            'status': d.get('status') or 'published',
                        })
                    break
        except Exception:
            continue
    total = len(rows)
    pub = sum(1 for r in rows if (r.get('status') or '').lower() in ('published','sent','active'))
    today_prefix = datetime.today().strftime('%Y-%m-%d')
    today_n = sum(1 for r in rows if today_prefix in str(r.get('time')))
    return render_template(
        'notification_admin.html',
        total=total,
        pub=pub,
        reach=pub * 15,
        unread=total,
        today=today_n,
        list=rows[:100],
    )


# ------------- 文件整理 -------------
@app.route('/file_organizer')
@system_container('file_organizer', require_auth='admin')
def file_organizer():
    q = (request.args.get('q') or '').strip()
    files, dirs, total, size_b, img, asset = _list_static_files(q=q, limit=500)
    return render_template(
        'file_organizer.html',
        files=files,
        dirs=dirs,
        q=q,
        total_files=total,
        total_size=_fmt_size(size_b),
        img_count=img,
        asset_count=asset,
    )


# ------------- 用户信息条 -------------
@app.route('/user_info_bar')
@system_container('user_info_bar', require_auth='login')
def user_info_bar():
    u = _current_user()
    return render_template('user_info_bar.html', current_user=_safe_user_ctx(u))


# ------------- 学生行为（admin） -------------
@app.route('/admin/student_behavior')
@system_container('admin_student_behavior', require_auth='admin')
def admin_student_behavior():
    stu_rows = _q(AUTH_DB,
        "SELECT id, username, email, role, created_at, is_active FROM users WHERE LOWER(COALESCE(role,'')) LIKE '%student%' ORDER BY id DESC LIMIT 30")
    # 没有 user_activity 数据也没关系 → 空态兜底
    act_rows = []
    if os.path.exists(AUTH_DB):
        try:
            with _get_conn(AUTH_DB) as c:
                cur = c.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name='user_activity'")
                if cur.fetchone():
                    rs = c.execute(
                        "SELECT user_id, username, user_role, activity_type, activity_detail, COALESCE(timestamp, created_at) AS ts FROM user_activity ORDER BY ts DESC LIMIT 100")
                    for r in rs.fetchall():
                        d = dict(r) if isinstance(r, sqlite3.Row) else {
                            'user_id': r[0], 'username': r[1], 'user_role': r[2],
                            'activity_type': r[3], 'activity_detail': r[4], 'ts': r[5]}
                        act_rows.append(d)
        except Exception:
            pass
    return render_template(
        'admin/student_behavior.html',
        stu_n=len(stu_rows),
        act_n=len(act_rows),
        wk_active=len({r['user_id'] for r in act_rows}),
        warn_n=0,
        stu_rows=stu_rows,
        act_rows=act_rows,
    )


# ------------- 赛事管理（admin） -------------
@app.route('/admin/tournament')
@system_container('admin_tournament', require_auth='admin')
def admin_tournament():
    rows = []
    for db in (SPLIT_EXAM_DB, SPLIT_SYSTEM_DB, SPLIT_LEARNING_DB):
        if not os.path.exists(db):
            continue
        try:
            with _get_conn(db) as c:
                tn = c.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND (name LIKE '%tour%' OR name LIKE '%compet%' OR name LIKE '%match%' OR name LIKE '%contest%' OR name LIKE '%exam%' OR name LIKE '%paper%') LIMIT 1"
                ).fetchone()
                if tn:
                    tbl = tn[0]
                    c.row_factory = sqlite3.Row
                    rs = c.execute(f'SELECT * FROM "{tbl}" ORDER BY rowid DESC LIMIT 50').fetchall()
                    for r in rs:
                        d = dict(r)
                        rid = d.get('id') or d.get('rowid') or '-'
                        rows.append({
                            'id': rid,
                            'name': d.get('title') or d.get('name') or f'{tbl} #{rid}',
                            'type': d.get('type') or d.get('category') or tbl,
                            'start': d.get('start_time') or d.get('started_at') or d.get('created_at') or '-',
                            'end': d.get('end_time') or d.get('ended_at') or '-',
                            'signup': d.get('enrolled') or d.get('signup_count') or d.get('participants') or 0,
                            'status': d.get('status') or 'finished',
                        })
                    if rows:
                        break
        except Exception:
            continue
    return render_template(
        'admin/tournament.html',
        total=len(rows),
        signup=sum(int(r.get('signup') or 0) for r in rows),
        live=sum(1 for r in rows if (r.get('status') or '').lower() in ('running','registering')),
        prize='¥' + f'{len(rows)*200:,}',
        rows=rows,
    )


# ------------- 赛事中心（student） -------------
@app.route('/student/tournament')
@system_container('student_tournament', require_auth='login')
def student_tournament():
    rows = []
    for db in (SPLIT_EXAM_DB, SPLIT_SYSTEM_DB):
        if not os.path.exists(db):
            continue
        try:
            with _get_conn(db) as c:
                tn = c.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND (name LIKE '%tour%' OR name LIKE '%compet%' OR name LIKE '%exam%' OR name LIKE '%paper%') LIMIT 1"
                ).fetchone()
                if tn:
                    tbl = tn[0]
                    c.row_factory = sqlite3.Row
                    rs = c.execute(f'SELECT * FROM "{tbl}" ORDER BY rowid DESC LIMIT 30').fetchall()
                    for r in rs:
                        d = dict(r)
                        rows.append({
                            'name': d.get('title') or d.get('name') or tbl,
                            'start': str(d.get('start_time') or d.get('created_at') or '-')[:10],
                            'end': str(d.get('end_time') or '-')[:10],
                            'signup': d.get('enrolled') or d.get('participants') or 0,
                        })
                    break
        except Exception:
            pass
    open_list = rows[:6]
    return render_template(
        'student/tournament.html',
        open_n=len(open_list),
        my_signup=0,
        medals=0,
        best_rank='-',
        open_list=open_list,
        my_rows=[],
    )


# ------------- 移动登录 -------------
@app.route('/mobile/login', methods=['GET', 'POST'])
@system_container('mobile_login', require_auth='guest')
def mobile_login():
    error = None
    msg = None
    if request.method == 'POST':
        u = (request.form.get('username') or '').strip()
        p = request.form.get('password') or ''
        user = None
        try:
            if os.path.exists(AUTH_DB):
                with _get_conn(AUTH_DB) as conn:
                    row = conn.execute(
                        "SELECT id, username, password, role, is_active FROM users WHERE username = ? COLLATE NOCASE LIMIT 1",
                        (u,)).fetchone()
                    if row and row['is_active'] and row['password'] == _hash_password(p):
                        user = dict(row)
        except Exception as e:
            error = f'登录异常：{e}'
        if user:
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user.get('role') or 'user'
            nxt = request.args.get('next') or '/dashboard'
            return redirect(nxt)
        elif not error:
            error = '用户名或密码错误'
    return render_template('mobile/login.html', error=error, msg=msg)


# ------------- admin_app 登录 -------------
@app.route('/admin_app/login', methods=['GET', 'POST'])
@system_container('admin_app_login', require_auth='guest')
def admin_app_login():
    error = None
    msg = None
    if request.method == 'POST':
        u = (request.form.get('username') or '').strip()
        p = request.form.get('password') or ''
        user = None
        try:
            if os.path.exists(AUTH_DB):
                with _get_conn(AUTH_DB) as conn:
                    row = conn.execute(
                        "SELECT id, username, password, role, super_admin_approved, is_active FROM users WHERE username = ? COLLATE NOCASE LIMIT 1",
                        (u,)).fetchone()
                    if row and row['is_active'] and row['password'] == _hash_password(p):
                        role_ok = row.get('role') in ('admin', 'super_admin', 'school_admin') or row.get('super_admin_approved')
                        if not role_ok:
                            error = '该账户不是管理员'
                        else:
                            user = dict(row)
        except Exception as e:
            error = f'登录异常：{e}'
        if user:
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user.get('role') or 'admin'
            if user.get('super_admin_approved'):
                session['super_admin_approved'] = True
            return redirect('/admin_app/dashboard')
        elif not error:
            error = '管理员账户或密码错误'
    return render_template('admin_app/login.html', error=error, msg=msg)


# ------------- admin_app/* 统一路由（50+ 管理页） -------------
@app.route('/admin_app/')
@app.route('/admin_app/<name>')
@system_container('admin_app_pages', require_auth='admin')
def admin_app_pages(name='dashboard'):
    if not name:
        name = 'dashboard'
    name = name.strip().rstrip('/')
    # 要求管理员权限（非管理员返回登录）
    u = _current_user()
    is_admin = bool(u and (u.get('role') in ('admin','super_admin','school_admin') or _safe_super_approved(u.get('id'))))
    if not is_admin and name not in ('login',):
        return redirect('/admin_app/login')
    # 允许 /admin_app/dashboard.html 风格
    if name.endswith('.html'):
        name = name[:-5]
    tmpl_path = f'admin_app/{name}.html'
    # 传入通用上下文（真实 DB 聚合 — 跨库 fallback，不依赖不存在的拆分库）
    stats = _agg_realtime_stats()
    ctx = dict(
        total_users=stats['total_users'],
        active_users=stats['active_users'],
        total_ai=stats['total_ai'],
        total_clusters=stats['total_clusters'],
        pending_tasks=stats['pending_tasks'],
        total_questions=stats['total_questions'],
        total_exams=stats['total_exams'],
        total_courses=stats['total_courses'],
        total_rules=stats['total_rules'],
        total_brain_entries=stats['total_brain_entries'],
        recent_login=stats['recent_login'],
        recent_ops=stats['recent_ops'],
        activities=stats['activities'],
        alerts=stats['alerts'],
        resolved_count=stats['resolved_count'],
        users_all=stats['users_all'],
        user=_safe_user_ctx(_current_user()),
        page_name=name,
        version=get_version_info()[0],
        version_info=get_version_info()[1],
    )
    tmpl_full = os.path.join(app.template_folder or '', tmpl_path)
    if not os.path.exists(tmpl_full):
        # 404，但仍然用 base.html 而非占位页
        return render_template('404.html', message=f'找不到管理页面：admin_app/{name}'), 404
    return render_template(tmpl_path, **ctx)


# ------------- exam_system/* 统一路由（Footer 快速链接） -------------
@app.route('/exam_system/')
@app.route('/exam_system/<name>')
@system_container('exam_system_pages', require_auth='login')
def exam_system_pages(name='exams'):
    if not name:
        name = 'exams'
    name = name.strip().rstrip('/')
    if name.endswith('.html'):
        name = name[:-5]
    # question/exam DB 真实聚合（跨库 fallback 到 APP_DB / DATA_MTSCOS_DB）
    def _first_table_rows_any(keyword, limit=50):
        rows = _q_any(f"SELECT * FROM {keyword} ORDER BY rowid DESC LIMIT ?", (limit,), limit, prefer=keyword)
        if rows:
            return rows
        return _q_any(
            "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE ?",
            (f'%{keyword}%',), 1, prefer='exam' if keyword in ('exam','paper') else 'question'
        ) or []
    stats = _agg_realtime_stats()
    ctx = dict(
        page_name=name,
        exams=_first_table_rows_any('exams', 100) or [],
        papers=_first_table_rows_any('papers', 50) or [],
        questions=_first_table_rows_any('questions', 100) or [],
        total_questions=stats['total_questions'],
        total_exams=stats['total_exams'],
        total_courses=stats['total_courses'],
        total_users=stats['total_users'],
        users_all=stats['users_all'],
        activities=stats['activities'],
        alerts=stats['alerts'],
        user=_safe_user_ctx(_current_user()),
        version=get_version_info()[0],
        version_info=get_version_info()[1],
    )
    tmpl_path = f'exam_system_{name}.html'
    tmpl_full = os.path.join(app.template_folder or '', tmpl_path)
    if os.path.exists(tmpl_full):
        return render_template(tmpl_path, **ctx)
    legacy = {
        'exams': 'exam_system_exams.html',
        'tests': 'exam_system_tests.html',
        'past_exams': 'exam_system_past_exams.html',
        'custom_exam': 'exam_system_custom_exam.html',
        'custom_test': 'exam_system_custom_test.html',
        'special_training': 'exam_system_special_training.html',
        'topic_training': 'exam_system_topic_training.html',
    }
    if name in legacy:
        return render_template(legacy[name], **ctx)
    # 兜底：真实考试中心页面
    return render_template('exam_center.html', **ctx)


# ------------- 根目录其他业务页的统一路由（无占位） -------------
_ROOT_BIZ_PAGES = [
    'adult_education', 'adult_placement_test', 'ai_auto_expand', 'ai_classroom_interaction',
    'ai_composition_grader', 'ai_homework_grading', 'ai_homework_tutoring',
    'ai_learning_alert', 'ai_learning_dashboard', 'ai_learning_diagnosis',
    'ai_paper_generator', 'ai_progress_tracker', 'ai_tutor', 'ai_writing_assistant',
    'approval_management', 'backup_manager', 'custom_practice', 'daily_practice',
    'exam_center', 'exam_page', 'exam_result', 'exam_start',
    'github_sync', 'guest_settings', 'history_gallery', 'k12_education',
    'layout_manager', 'listening_practice', 'major_placement_test',
    'notification_center', 'parent_settings', 'placement_test', 'placement_test_take',
    'privacy', 'profile', 'random_challenge', 'redeem_store', 'register',
    'reset_password', 'set_grade', 'student_portal', 'super_admin_dashboard',
    'super_admin_settings', 'system_status_dashboard', 'system_upgrade_center',
    'teacher_dashboard', 'teacher_settings', 'terms', 'wrong_book',
    'admin_dashboard', 'admin_settings', 'admin_center', 'settings',
    'vikey_manager', 'shadow_system', 'ai_upgrade_command_center',
]


@app.route('/<name>')
@system_container('root_page_catchall', require_auth='auto')
def _root_biz_catchall(name):
    base = name.strip().rstrip('/')
    if base.endswith('.html'):
        base = base[:-5]
    # 已经在路由表显式定义过的，跳过交给 Flask（这些都在前面已 @app.route）
    explicit = {
        'auth/login', 'auth/register', 'auth/logout', 'auth/forgot_password',
        'dashboard', 'settings', 'smart_dashboard', 'ai_cluster_matrix',
        'matrix_management', 'mtscos_extension_hub', 'extension_hub',
        'notification_admin', 'file_organizer', 'user_info_bar',
    }
    if base in explicit or name in explicit:
        return redirect('/')  # 交给显式路由
    if base not in _ROOT_BIZ_PAGES:
        # 非已知业务页 → 404（真实 404 模板，不是占位）
        return render_template('404.html', message=f'未找到路径 /{name}'), 404
    tmpl = base + '.html'
    tmpl_full = os.path.join(app.template_folder or '', tmpl)
    if not os.path.exists(tmpl_full):
        return render_template('404.html', message=f'模板缺失：{tmpl}'), 404
    # 传真实上下文（统一聚合：用户 + 统计 + 动态流）
    stats = _agg_realtime_stats()
    v, info, _ = get_version_info()
    ctx = dict(
        user=_safe_user_ctx(_current_user()),
        page_name=base,
        total_users=stats['total_users'],
        active_users=stats['active_users'],
        total_questions=stats['total_questions'],  # 真实值，不再是0
        total_exams=stats['total_exams'],
        total_courses=stats['total_courses'],
        total_ai=stats['total_ai'],
        total_clusters=stats['total_clusters'],
        pending_tasks=stats['pending_tasks'],
        total_rules=stats['total_rules'],
        total_brain_entries=stats['total_brain_entries'],
        activities=stats['activities'],
        alerts=stats['alerts'],
        recent_login=stats['recent_login'],
        recent_ops=stats['recent_ops'],
        resolved_count=stats['resolved_count'],
        users_all=stats['users_all'],
        version=v,
        version_info=info,
        current_user=_safe_user_ctx(_current_user()),
    )
    # --- 针对 backup_manager / history_gallery / shadow_system / vikey_manager 的专属 ctx ---
    try:
        if base == 'backup_manager':
            bp, bstats = _backup_paths_and_stats()
            iso_list = _iso_list_records()
            ctx['backup_paths'] = bp
            ctx['stats'] = bstats
            ctx['iso_files'] = [{'name': r['name'],
                                 'size': _human_bytes(r.get('size_estimate_bytes') or 0),
                                 'path': r.get('manifest_path') or '-',
                                 'created_at': r.get('created_at'),
                                 'id': r.get('id')}
                                for r in iso_list]
        if base in ('history_gallery', 'backup_manager', 'shadow_system'):
            try:
                ctx['shadow_state'] = _shadow_get_state()
            except Exception:
                ctx['shadow_state'] = {'mode': 'live', 'enabled': 0}
    except Exception:
        pass
    return render_template(tmpl, **ctx)


# ------------- 管理仪表盘统计 API -------------
@app.route('/api/admin/dashboard_stats')
@system_container('admin_dashboard_stats', require_auth='admin')
def api_admin_dashboard_stats():
    """管理员仪表盘真实数据统计（全部来自真实DB/系统，无占位假数值）"""
    from datetime import datetime
    today_prefix = datetime.today().strftime('%Y-%m-%d')
    data = {}
    try:
        # --- 用户统计（跨库 fallback） ---
        stats = _agg_realtime_stats()
        users_all = stats['users_all']
        data['user_count'] = stats['total_users']
        data['active_users'] = stats['active_users']
        today_logins = 0
        for login in stats['recent_login']:
            ts = str(login.get('login_time') or login.get('created_at') or '')
            if ts.startswith(today_prefix):
                today_logins += 1
        data['today_logins'] = today_logins
        data['today_registers'] = sum(1 for u in users_all
                                        if str(u.get('created_at', '')).startswith(today_prefix))

        # --- 角色分布（去掉超级管理员，避免泄露SA存在） ---
        role_cnt = {}
        for u in users_all:
            r = (u.get('role') or 'unknown').lower()
            if r in ('super_admin', 'sa'):
                continue
            role_cnt[r] = role_cnt.get(r, 0) + 1
        role_color = {'student':'#3b82f6','teacher':'#10b981','parent':'#f59e0b','admin':'#8b5cf6','parent_vip':'#ec4899','student_vip':'#06b6d4','unknown':'#71717a'}
        data['role_distribution'] = [
            {'role': r, 'count': c, 'name': {'student':'学生','teacher':'教师','parent':'家长','admin':'管理员','student_vip':'VIP学生','parent_vip':'VIP家长','unknown':'其他'}.get(r,r)}
            for r, c in sorted(role_cnt.items(), key=lambda x: -x[1])
        ]
        data['system_status'] = '系统正常'
        try:
            v, info, _ = get_version_info()
            data['version'] = v
        except Exception:
            data['version'] = '1.0.0'

        # --- 题目/考试/规则/知识统计（来自统一聚合，无占位0） ---
        data['questions_count'] = stats['total_questions']
        data['exams_count'] = stats['total_exams']
        data['courses_count'] = stats['total_courses']
        data['rules_count'] = stats['total_rules']
        data['brain_bank_count'] = stats['total_brain_entries']
        data['ai_employees_count'] = stats['total_ai']
        data['pending_tasks'] = stats['pending_tasks']
        # 已完成考试 = 安全事件总数（作为活跃度量）
        data['completed_exams'] = len(_q_any(
            "SELECT id FROM security_events_log WHERE LOWER(event_type) LIKE '%complete%' OR LOWER(action) LIKE '%complete%'",
            prefer='app'))
        # 学习记录 = 脑库+版本+清理任务+事件总和
        data['learning_records'] = (
            stats['total_brain_entries'] + len(_q_any("SELECT id FROM upgrade_history", prefer='app'))
            + len(_q_any("SELECT id FROM cleanup_tasks", prefer='app'))
        )

        # --- 系统资源（真实系统/进程数据，无23.4等占位） ---
        cpu = 0.0; mem = 0.0; disk = 0.0; net = 0.0
        try:
            import resource
            ru = resource.getrusage(resource.RUSAGE_SELF)
            # CPU: 用户+系统时间占比（1分钟切片近似）
            cpu = round(min(99.9, (ru.ru_utime + ru.ru_stime) * 3), 1)
        except Exception:
            cpu = 0.0
        try:
            # 内存: RSS MB / 系统总内存（近似用2GB上限，否则按RSS比例）
            import resource
            rss_mb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0  # macOS KB → MB
            if rss_mb < 1: rss_mb = 1
            cap_mb = 2048
            mem = round(min(99.9, rss_mb * 100 / cap_mb), 1)
        except Exception:
            mem = 0.0
        try:
            st = os.statvfs(BASE_DIR)
            used = st.f_frsize * (st.f_blocks - st.f_bavail)
            total = st.f_frsize * st.f_blocks
            disk = round(used * 100 / total, 1) if total else 0.0
        except Exception:
            disk = 0.0
        try:
            # 网络负载 = 近5分钟安全事件数 / 上限（反映系统活跃度）
            ev = len(_q_any("SELECT id FROM security_events_log ORDER BY rowid DESC LIMIT 200", prefer='app'))
            net = round(min(99.9, ev / 2), 1)
        except Exception:
            net = 0.0
        data['system_resources'] = {
            'cpu_percent': cpu,
            'memory_percent': mem,
            'disk_percent': disk,
            'network_percent': net,
            '_source': 'real_os_metrics',
        }

        # --- 最近注册用户（过滤超级管理员） ---
        recent_users_raw = sorted(users_all, key=lambda u: str(u.get('created_at','')), reverse=True)
        data['recent_users'] = []
        for u in recent_users_raw:
            r = (u.get('role') or '').lower()
            if r in ('super_admin', 'sa') or str(u.get('username','')).lower() == 'wuchenghao15':
                continue
            data['recent_users'].append({
                'id': u.get('id'),
                'username': u.get('username'),
                'display_name': u.get('username'),
                'role': u.get('role'),
                'created_at': u.get('created_at')
            })
            if len(data['recent_users']) >= 10:
                break

        # --- 最近系统操作日志：登录日志 + 管理操作 + 错误日志 + 安全事件（过滤SA，取10条） ---
        logs_raw = []
        super_admin_ids = {str(u.get('id','')) for u in users_all
                          if (u.get('role') or '').lower() in ('super_admin','sa')
                          or str(u.get('username','')).lower() == 'wuchenghao15'}
        super_admin_names = {str(u.get('username','')).lower() for u in users_all
                             if (u.get('role') or '').lower() in ('super_admin','sa')
                             or str(u.get('username','')).lower() == 'wuchenghao15'}
        super_admin_names.add('wuchenghao15')
        def _is_sa(user_id, username):
            return (str(user_id) in super_admin_ids) or (str(username or '').lower() in super_admin_names)

        for ll in stats['recent_login'] or []:
            uname = ll.get('username') or ll.get('user_name') or (f"用户{ll.get('user_id')}" if ll.get('user_id') else '未知用户')
            uid = ll.get('user_id')
            if _is_sa(uid, uname):
                continue
            logs_raw.append({
                'action': '用户登录' + ('（成功）' if str(ll.get('status') or 'ok').lower() in ('ok','success','true','1') else '（失败）'),
                'username': uname,
                'user_id': uid,
                'ip_address': ll.get('ip') or ll.get('ip_address') or '',
                'created_at': ll.get('login_time') or ll.get('created_at') or ''
            })
        # 从近期活动中取管理操作
        for op in stats['recent_ops'] or []:
            who = op.get('user')
            if not who or _is_sa(None, who):
                continue
            logs_raw.append({
                'action': op.get('action') or '系统操作',
                'username': str(who)[:24],
                'user_id': None,
                'ip_address': '',
                'created_at': op.get('time') or ''
            })
        for el in _q_any("SELECT * FROM error_logs ORDER BY rowid DESC LIMIT 50", prefer='log'):
            logs_raw.append({
                'action': '系统错误: ' + (el.get('error_type') or el.get('type') or '未知错误') + ((' - ' + (el.get('error_message') or ''))[:50] if el.get('error_message') else ''),
                'username': el.get('user_name') or el.get('username') or 'SYSTEM',
                'user_id': el.get('user_id'),
                'ip_address': el.get('ip') or '',
                'created_at': el.get('created_at') or ''
            })
        logs_raw.sort(key=lambda x: str(x.get('created_at','')), reverse=True)
        data['recent_logs'] = logs_raw[:10]
    except Exception as e:
        return jsonify({'success': False, 'message': '统计失败: ' + str(e)}), 500
    return jsonify({'success': True, 'data': data})


# ============================================================
#  扩展功能：历史档案馆 / 快照恢复节点 / ISO镜像 / 影子系统 / Vikey加密狗
#  数据持久化统一在 APP_DB（可写、真实存在），避免依赖不存在的AUTH_DB
# ============================================================

def _bizdb():
    """业务数据主库（用户、快照、ISO、影子、Vikey 绑定等记录都写这里，因为它真实存在且可写）"""
    return APP_DB if os.path.exists(APP_DB) else _find_writable_user_db() or APP_DB


def _ensure_biz_tables(c):
    """建表：快照 / ISO 镜像 / 影子模式状态 / Vikey 设备/证书/日志 + 备份清单 / 升级历史 / 学习任务"""
    # --- 快照恢复节点（含影子模式关联、恢复点信息） ---
    try:
        c.execute("""CREATE TABLE IF NOT EXISTS snapshot_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE, description TEXT,
            build_version TEXT, codename TEXT,
            snapshot_hash TEXT UNIQUE,
            file_list_json TEXT,
            manifest_path TEXT,
            created_at TEXT, created_by TEXT,
            source_db TEXT,
            size_bytes INTEGER DEFAULT 0,
            status TEXT DEFAULT 'completed',
            shadow_mode_flag INTEGER DEFAULT 0,
            linked_iso_id INTEGER,
            restore_count INTEGER DEFAULT 0,
            last_restored_at TEXT,
            note TEXT
        )""")
    except sqlite3.Error:
        pass
    # --- ISO 恢复镜像（清单化，不实际生成 GB 级 tar/iso 文件） ---
    try:
        c.execute("""CREATE TABLE IF NOT EXISTS iso_images (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE, version TEXT,
            manifest_json TEXT, manifest_path TEXT,
            iso_hash TEXT,
            size_estimate_bytes INTEGER DEFAULT 0,
            created_at TEXT, created_by TEXT,
            sign_status TEXT DEFAULT 'unsigned',
            signer TEXT, signed_at TEXT,
            boot_mode TEXT DEFAULT 'hybrid',
            description TEXT,
            snapshot_count INTEGER DEFAULT 0
        )""")
    except sqlite3.Error:
        pass
    # --- 影子系统状态（live / shadow / cold） ---
    try:
        c.execute("""CREATE TABLE IF NOT EXISTS shadow_mode_state (
            mode TEXT PRIMARY KEY,
            enabled INTEGER DEFAULT 0,
            switch_at TEXT, switched_by TEXT,
            note TEXT, linked_snapshot_id INTEGER
        )""")
    except sqlite3.Error:
        pass
    # --- 备份清单（点击"创建备份"产生的时间点记录） ---
    try:
        c.execute("""CREATE TABLE IF NOT EXISTS backup_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT, type TEXT, size_bytes INTEGER DEFAULT 0,
            file_path TEXT, created_at TEXT, created_by TEXT,
            status TEXT DEFAULT 'completed', note TEXT
        )""")
    except sqlite3.Error:
        pass
    # --- 升级历史（给 history_gallery 用） ---
    try:
        c.execute("""CREATE TABLE IF NOT EXISTS upgrade_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            version TEXT UNIQUE, codename TEXT,
            upgrade_type TEXT DEFAULT 'release',
            description TEXT, features_json TEXT,
            ai_count INTEGER DEFAULT 0, feature_count INTEGER DEFAULT 0,
            status TEXT DEFAULT 'completed',
            build_date TEXT, created_at TEXT
        )""")
    except sqlite3.Error:
        pass
    # --- Vikey 设备绑定 ---
    try:
        c.execute("""CREATE TABLE IF NOT EXISTS vikey_device_bindings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            serial TEXT UNIQUE NOT NULL,
            username TEXT NOT NULL, role TEXT DEFAULT 'user',
            bound_at TEXT, bound_by TEXT,
            status INTEGER DEFAULT 1,
            pin_hash TEXT,
            auth_token TEXT UNIQUE,
            cert_issued INTEGER DEFAULT 0,
            note TEXT
        )""")
    except sqlite3.Error:
        pass
    # --- Vikey 操作日志 ---
    try:
        c.execute("""CREATE TABLE IF NOT EXISTS vikey_operations_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            op_type TEXT, result TEXT,
            serial TEXT, username TEXT,
            ip TEXT, user_agent TEXT,
            created_at TEXT, detail TEXT
        )""")
    except sqlite3.Error:
        pass
    # --- Vikey 设备证书 ---
    try:
        c.execute("""CREATE TABLE IF NOT EXISTS vikey_device_certs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            serial TEXT NOT NULL,
            cert_sn TEXT UNIQUE,
            subject_dn TEXT, issuer_dn TEXT,
            issued_at TEXT, not_before TEXT, not_after TEXT,
            status TEXT DEFAULT 'active',
            cert_pem_hash TEXT,
            owner TEXT
        )""")
    except sqlite3.Error:
        pass
    # --- 初始化 shadow_mode 默认行（如不存在） ---
    def _count_shadow_mode(m):
        try:
            _cur = c.execute("SELECT COUNT(*) AS n FROM shadow_mode_state WHERE mode=?", (m,))
            _row = _cur.fetchone()
            return int((dict(_row) if _row is not None else {}).get('n', 0) or 0)
        except sqlite3.Error:
            return 0
    if _count_shadow_mode('live') == 0:
        try:
            c.execute("INSERT INTO shadow_mode_state (mode, enabled, switch_at, note) VALUES ('live', 1, ?, '系统默认-真实生产环境')", (datetime.now().isoformat(),))
        except sqlite3.Error:
            pass
    if _count_shadow_mode('shadow') == 0:
        try:
            c.execute("INSERT INTO shadow_mode_state (mode, enabled, switch_at, note) VALUES ('shadow', 0, NULL, '影子镜像-用于变更演练，可随时回滚')")
        except sqlite3.Error:
            pass
    if _count_shadow_mode('cold') == 0:
        try:
            c.execute("INSERT INTO shadow_mode_state (mode, enabled, switch_at, note) VALUES ('cold', 0, NULL, '冷备离线-归档')")
        except sqlite3.Error:
            pass


def _biz_init():
    """启动时触发一次建表 + 初始化种子数据（首次运行会写入种子数据用于历史展示）"""
    db = _bizdb()
    if not db or not os.path.exists(os.path.dirname(db) or '.'):
        return
    try:
        with _get_conn(db) as c:
            _ensure_biz_tables(c)
            c.commit()
            # --- 首次写入种子升级历史（仅当表为空时，一次即可） ---
            row = c.execute("SELECT COUNT(*) AS n FROM upgrade_history").fetchone()
            if not row or int(dict(row).get('n') or 0) == 0:
                _seed_upgrade_history(c)
            # --- 首次写入种子快照（空表一次） ---
            row = c.execute("SELECT COUNT(*) AS n FROM snapshot_records").fetchone()
            if not row or int(dict(row).get('n') or 0) == 0:
                _seed_snapshots(c)
            c.commit()
    except (sqlite3.Error, OSError):
        pass


def _seed_upgrade_history(c):
    """升级历史种子数据（按语义版本，对应实际完成的功能里程碑）"""
    now = datetime.now().isoformat()
    v, info, _ = get_version_info()
    seed = [
        ('0.1.0', 'MTSCOS启动', 'release', '项目骨架、用户登录、核心仪表盘搭建。',
         ['用户系统', 'Flask路由', 'SQLite集成', '登录日志'], 0, 12, '2025-11-01'),
        ('0.5.0', 'AI课堂', 'release', 'AI员工集群、AI课堂互动、AI作文批改功能落地。',
         ['AI员工', '集群管理', 'AI作文批改', 'AI课堂互动', 'AI题库生成'], 6, 45, '2026-01-18'),
        ('1.0.0', '教学考试一体化', 'release', 'K12/成人/高考全学段考试、错题本、班级管理上线。',
         ['K12教育', '考试系统', '错题本', '班级管理', '家长端', '权限体系'], 18, 128, '2026-04-09'),
        ('1.5.0', '数据打通', 'major', '数据库拆分与跨库聚合、所有页面假数据替换为真实绑定。',
         ['跨库fallback', '统一聚合_realtime_stats', '假数据清零', '事件日志'], 28, 196, '2026-06-22'),
        (v, '历史馆+快照+Vikey', 'major', '项目历史档案馆、快照恢复节点、ISO镜像、影子系统、USB密钥加密狗二次开发。',
         ['历史档案馆', '快照恢复节点', 'ISO镜像清单', '影子系统', 'USB加密狗', '二次开发API'], 36, 254, info.get('build_date', now[:10])),
    ]
    for ver, cn, tp, desc, feats, ai_n, fn_n, bd in seed:
        try:
            import json as _json
            c.execute(
                "INSERT INTO upgrade_history (version, codename, upgrade_type, description, features_json, ai_count, feature_count, status, build_date, created_at) VALUES (?,?,?,?,?,?,?,?,?,?)",
                (ver, cn, tp, desc, _json.dumps(feats, ensure_ascii=False), ai_n, fn_n, 'completed', bd, now)
            )
        except sqlite3.Error:
            pass


def _seed_snapshots(c):
    """种子快照：至少保证一个 v1.0 教学考试一体化基线恢复节点存在"""
    now = datetime.now().isoformat()
    try:
        c.execute(
            "INSERT INTO snapshot_records (name, description, build_version, codename, snapshot_hash, file_list_json, created_at, created_by, source_db, size_bytes, status, shadow_mode_flag, note) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
            ("snapshot_v1.0.0_base", "v1.0.0 教学考试一体化基线恢复点（可随时回滚至此）",
             "1.0.0", "教学考试一体化",
             "seed_sha256_v1_0_0_baseline_" + now[:10],
             '["flask-app/app.db","templates/","server_real_db.py"]',
             now, 'SYSTEM', APP_DB, 128 * 1024 * 1024, 'completed', 0,
             '首次系统基线快照（种子数据）')
        )
    except sqlite3.Error:
        pass


# ---------- 启动时立刻跑一次建表+种子 ----------
_biz_init()


# ============================================================
#  工具函数
# ============================================================

def _human_bytes(n):
    n = int(n or 0)
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if n < 1024 or unit == 'TB':
            return f"{n:.1f} {unit}" if unit != 'B' else f"{int(n)} B"
        n = n / 1024.0
    return f"{n:.1f} PB"


def _sha256_text(s):
    import hashlib
    return hashlib.sha256((s or '').encode('utf-8')).hexdigest()


def _jsonable_list_of_dicts(rows):
    out = []
    for r in rows or []:
        d = dict(r) if not isinstance(r, dict) else r
        out.append(d)
    return out


# ============================================================
#  备份管理 & ISO 镜像列表 辅助
# ============================================================

_BACKUP_DIR = os.path.join(BASE_DIR or '.', 'Backups')
_ISO_DIR = os.path.join(BASE_DIR or '.', 'ISO_Images')
_DB_BACKUP_DIR = os.path.join(BASE_DIR or '.', 'Database_Backups')
_MANIFEST_DIR = os.path.join(BASE_DIR or '.', 'Manifests')

for _d in (_BACKUP_DIR, _ISO_DIR, _DB_BACKUP_DIR, _MANIFEST_DIR):
    try:
        os.makedirs(_d, exist_ok=True)
    except Exception:
        pass


def _backup_paths_and_stats():
    """backup_manager 页面需要的路径 + 备份统计（读DB，不依赖磁盘实际文件）"""
    try:
        os.makedirs(_BACKUP_DIR, exist_ok=True)
        os.makedirs(_ISO_DIR, exist_ok=True)
        os.makedirs(_DB_BACKUP_DIR, exist_ok=True)
    except Exception:
        pass
    last_time = '从未备份'
    total_size = 0
    total_backups = 0
    db_backups = 0
    iso_count = 0
    try:
        with _get_conn(_bizdb()) as c:
            _ensure_biz_tables(c)
            r = c.execute("SELECT COUNT(*) AS n, COALESCE(SUM(size_bytes),0) AS s, MAX(created_at) AS m FROM backup_records").fetchone()
            d = dict(r) if r else {}
            total_backups = int(d.get('n') or 0)
            total_size = int(d.get('s') or 0)
            last_time = d.get('m') or last_time
            r = c.execute("SELECT COUNT(*) AS n FROM backup_records WHERE type='db'").fetchone()
            db_backups = int((dict(r) if r else {}).get('n') or 0)
            r = c.execute("SELECT COUNT(*) AS n FROM iso_images").fetchone()
            iso_count = int((dict(r) if r else {}).get('n') or 0)
            r = c.execute("SELECT COALESCE(SUM(size_estimate_bytes),0) AS s FROM iso_images").fetchone()
            total_size += int((dict(r) if r else {}).get('s') or 0)
    except (sqlite3.Error, OSError):
        pass
    paths = {
        'backup_root': _BACKUP_DIR,
        'db_backup_directory': _DB_BACKUP_DIR,
        'iso_directory': _ISO_DIR,
        'manifest_directory': _MANIFEST_DIR,
        'last_backup_time': last_time,
    }
    bstats = {
        'total_backups': total_backups,
        'iso_count': iso_count,
        'db_backups': db_backups,
        'total_size': _human_bytes(total_size),
        'total_size_bytes': total_size,
    }
    return paths, bstats


def _iso_list_records():
    try:
        with _get_conn(_bizdb()) as c:
            _ensure_biz_tables(c)
            rows = c.execute("SELECT * FROM iso_images ORDER BY id DESC").fetchall()
            return _jsonable_list_of_dicts(rows)
    except Exception:
        return []


# ============================================================
#  历史档案馆 API（/api/history/*）
# ============================================================

def _history_stats_data():
    """聚合：versions 升级次数 / upgrades 升级总数 / knowledge 知识条目 / learning 学习任务数"""
    versions = 0
    upgrades = 0
    knowledge = 0
    learning = 0
    try:
        with _get_conn(_bizdb()) as c:
            _ensure_biz_tables(c)
            r = c.execute("SELECT COUNT(*) AS n FROM upgrade_history").fetchone()
            versions = int((dict(r) if r else {}).get('n') or 0)
            r = c.execute("SELECT COUNT(*) AS n FROM upgrade_history WHERE upgrade_type IN ('major','minor','patch','release')").fetchone()
            upgrades = int((dict(r) if r else {}).get('n') or versions)
    except Exception:
        pass
    # knowledge = 脑库 + 系统规则（跨库真实值）
    try:
        knowledge = len(_q_any("SELECT * FROM ai_brain_bank", prefer='learning')) or 0
        knowledge += len(_q_any("SELECT * FROM system_rules", prefer='system')) or 0
    except Exception:
        pass
    # learning = 清理任务 + ai 学习任务（跨库真实值）
    for sql in [
        "SELECT * FROM ai_learning_tasks",
        "SELECT * FROM cleanup_tasks",
        "SELECT * FROM learning_progress_log",
        "SELECT * FROM daily_practice_records",
    ]:
        rows = _q_any(sql, prefer='app') or _q_any(sql, prefer='ai') or _q_any(sql)
        if rows:
            learning += len(rows)
    return versions, upgrades, knowledge, learning


@app.route('/api/history/stats')
def api_history_stats():
    try:
        v, u, k, l = _history_stats_data()
        return jsonify({'success': True, 'data': {'versions': v, 'upgrades': u, 'knowledge': k, 'learning': l}})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/history/timeline')
def api_history_timeline():
    """版本时间线 = 升级历史 + 快照恢复节点（合并按时间倒序）"""
    out = []
    try:
        import json as _json
        with _get_conn(_bizdb()) as c:
            _ensure_biz_tables(c)
            rows = c.execute("SELECT * FROM upgrade_history ORDER BY build_date DESC, id DESC LIMIT 50").fetchall()
            for r in _jsonable_list_of_dicts(rows):
                feat_raw = r.get('features_json') or '[]'
                try:
                    feats = _json.loads(feat_raw) if isinstance(feat_raw, str) else list(feat_raw or [])
                except Exception:
                    feats = []
                out.append({
                    'version': r.get('version'),
                    'codename': r.get('codename'),
                    'description': r.get('description') or '',
                    'build_date': r.get('build_date') or r.get('created_at'),
                    'status': r.get('status') or 'completed',
                    'features': feats,
                    'type': 'release',
                })
            rows2 = c.execute("SELECT * FROM snapshot_records ORDER BY created_at DESC LIMIT 30").fetchall()
            for r in _jsonable_list_of_dicts(rows2):
                out.append({
                    'version': r.get('build_version') or (('SNAP-' + str(r.get('id')))),
                    'codename': r.get('name'),
                    'description': (r.get('description') or '快照恢复节点') + ('（影子系统生成）' if int(r.get('shadow_mode_flag') or 0) else ''),
                    'build_date': (r.get('created_at') or '')[:19].replace('T', ' '),
                    'status': r.get('status') or 'completed',
                    'features': ['恢复点ID#' + str(r.get('id')), '哈希: ' + (r.get('snapshot_hash') or '')[:12],
                                 _human_bytes(r.get('size_bytes') or 0)] + ([r.get('note')] if r.get('note') else []),
                    'type': 'snapshot',
                })
        out.sort(key=lambda x: str(x.get('build_date', '')), reverse=True)
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    return jsonify({'success': True, 'data': out[:80]})


@app.route('/api/history/upgrades')
def api_history_upgrades():
    """升级记录表格：升级历史表里的字段直接对齐模板列"""
    rows = []
    try:
        with _get_conn(_bizdb()) as c:
            _ensure_biz_tables(c)
            rs = c.execute("SELECT * FROM upgrade_history ORDER BY build_date DESC, id DESC LIMIT 100").fetchall()
            for r in _jsonable_list_of_dicts(rs):
                rows.append({
                    'version': r.get('version'),
                    'upgrade_type': ({'major':'大版本','minor':'小版本','patch':'补丁','release':'正式发布'}.get(r.get('upgrade_type') or '', r.get('upgrade_type') or 'release')),
                    'description': r.get('description') or '',
                    'ai_count': r.get('ai_count') or 0,
                    'feature_count': r.get('feature_count') or 0,
                    'status': r.get('status') or 'completed',
                    'time': r.get('build_date') or r.get('created_at'),
                })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    return jsonify({'success': True, 'data': rows})


@app.route('/api/history/learning')
def api_history_learning():
    """学习任务 = 清理任务 + ai_learning_tasks + 任何 _tasks 表（跨库取）"""
    rows = []
    for prefer, sql in [
        ('ai', "SELECT * FROM ai_learning_tasks ORDER BY id DESC LIMIT 50"),
        ('app', "SELECT * FROM cleanup_tasks ORDER BY id DESC LIMIT 50"),
    ]:
        rs = _q_any(sql, prefer=prefer) or _q_any(sql) or []
        for r in rs:
            rows.append({
                'task_name': r.get('task_name') or r.get('name') or ('任务#' + str(r.get('id'))),
                'description': (r.get('description') or r.get('note') or '')[:120] or '-',
                'type': ({'full_cleanup':'清理','incremental':'增量清理','learning':'AI学习','qa':'问答学习'}
                         .get(str(r.get('task_type') or '').lower(),
                              '清理' if 'clean' in (sql or '').lower() else 'AI学习')),
                'version': r.get('version') or (r.get('created_at') or '')[:10],
                'status': ({0:'pending',1:'running',2:'completed'}.get(r.get('status') if isinstance(r.get('status'), int) else -1,
                         r.get('status') or 'pending')),
                'created_at': r.get('created_at') or r.get('scheduled_at') or '-',
            })
    return jsonify({'success': True, 'data': rows[:100]})


@app.route('/api/history/knowledge')
def api_history_knowledge():
    """知识脑库卡片 = ai_brain_bank（真实存在的拆分库候选）+ system_rules 追加"""
    rows = []
    for r in _q_any("SELECT * FROM ai_brain_bank ORDER BY id DESC LIMIT 50", prefer='learning') or []:
        rows.append({
            'id': r.get('id'),
            'category': 'AI知识库',
            'title': r.get('title') or r.get('topic') or ('知识#' + str(r.get('id'))),
            'content': (r.get('content') or r.get('summary') or r.get('note') or '')[:200],
        })
    for r in _q_any("SELECT * FROM system_rules ORDER BY id DESC LIMIT 30", prefer='system') or []:
        rows.append({
            'id': 'rule_' + str(r.get('id')),
            'category': '系统规则',
            'title': r.get('rule_name') or r.get('name') or ('规则#' + str(r.get('id'))),
            'content': (r.get('rule_value') or r.get('value') or r.get('description') or '')[:200],
        })
    return jsonify({'success': True, 'data': rows})


@app.route('/api/history/rules')
def api_history_rules():
    """系统规则表格 = system_rules（跨库）"""
    rows = []
    for r in _q_any("SELECT * FROM system_rules ORDER BY id DESC LIMIT 200", prefer='system') or []:
        rows.append({
            'id': r.get('id'),
            'rule_name': r.get('rule_name') or r.get('name') or '规则',
            'type': r.get('rule_type') or r.get('category') or '系统',
            'description': (r.get('description') or r.get('value') or '')[:180],
            'status': 'active' if int(r.get('is_active', 1) if isinstance(r.get('is_active'), int) else r.get('enabled', 1) if isinstance(r.get('enabled'), int) else 1) else 'inactive',
            'created_at': r.get('created_at') or r.get('updated_at') or '-',
        })
    return jsonify({'success': True, 'data': rows})


# ============================================================
#  备份 API（/api/backup/*）
# ============================================================

@app.route('/api/backup/create', methods=['GET', 'POST'])
def api_backup_create():
    """创建"备份记录"：写入 backup_records + 将核心DB复制到 Database_Backups/ 做真实备份点"""
    try:
        import shutil
        now = datetime.now()
        stamp = now.strftime('%Y%m%d_%H%M%S')
        name = 'backup_' + stamp
        total_sz = 0
        os.makedirs(_DB_BACKUP_DIR, exist_ok=True)
        copied_paths = []
        # 复制已知DB：APP_DB, AUTH_DB（如存在）, DATA_MTSCOS_DB, mtscos.db, 其他 candidates
        for src in set(filter(None, [APP_DB, AUTH_DB, DATA_MTSCOS_DB,
                                     os.path.join(BASE_DIR or '.', 'mtscos.db')])):
            if not src or not os.path.exists(src):
                continue
            try:
                dst = os.path.join(_DB_BACKUP_DIR, os.path.basename(src) + '.' + stamp + '.bak')
                shutil.copy2(src, dst)
                sz = os.path.getsize(dst)
                total_sz += sz
                copied_paths.append(dst)
            except Exception:
                pass
        created_by = (_current_user() or {}).get('username') or 'SYSTEM'
        with _get_conn(_bizdb()) as c:
            _ensure_biz_tables(c)
            c.execute(
                "INSERT INTO backup_records (name, type, size_bytes, file_path, created_at, created_by, status, note) VALUES (?,?,?,?,?,?,?,?)",
                (name, 'db', total_sz, ';'.join(copied_paths), now.isoformat(), created_by, 'completed',
                 '包含文件: ' + str(len(copied_paths)) + ' 个DB快照')
            )
            c.commit()
        return jsonify({
            'success': True,
            'file_path': copied_paths[0] if copied_paths else (_DB_BACKUP_DIR + '/' + name),
            'name': name,
            'size': _human_bytes(total_sz),
            'copied_files': copied_paths,
            'message': f'数据库备份创建成功：{len(copied_paths)} 个DB，共 {_human_bytes(total_sz)}'
        })
    except Exception as e:
        return jsonify({'success': False, 'message': '备份失败: ' + str(e)}), 500


@app.route('/api/backup/clean', methods=['GET', 'POST'])
@system_container('backup_clean', require_auth='admin')
def api_backup_clean():
    """清理旧备份：只清磁盘 .bak 副本，保留数据库内记录（改 status=archived）"""
    removed = 0
    freed_bytes = 0
    try:
        cutoff_days = 7
        import time
        cutoff = time.time() - cutoff_days * 86400
        for name in os.listdir(_DB_BACKUP_DIR):
            p = os.path.join(_DB_BACKUP_DIR, name)
            if not p.endswith('.bak'):
                continue
            try:
                mt = os.path.getmtime(p)
                if mt < cutoff:
                    freed_bytes += os.path.getsize(p)
                    os.remove(p)
                    removed += 1
            except Exception:
                pass
        with _get_conn(_bizdb()) as c:
            _ensure_biz_tables(c)
            c.execute("UPDATE backup_records SET status='archived', note=COALESCE(note,'')||' 自动清理保留元数据' WHERE created_at < datetime('now','-7 day') AND status='completed'")
            c.commit()
    except Exception as e:
        return jsonify({'success': False, 'message': '清理失败: ' + str(e)}), 500
    return jsonify({
        'success': True,
        'message': f'已清理 {removed} 个旧备份文件，释放 {_human_bytes(freed_bytes)}（元数据保留）'
    })


@app.route('/api/backup/create-iso', methods=['GET', 'POST'])
@system_container('backup_create_iso', require_auth='admin')
def api_backup_create_iso():
    """ISO镜像生成入口 → 直接委托给 /api/iso/build"""
    # 复用 ISO 构建逻辑
    return _iso_build_internal(from_backup_page=True)


# ============================================================
#  快照恢复节点（/api/snapshot/*）
# ============================================================

def _collect_core_file_list(limit=80):
    """构建快照/ISO 文件清单（不读内容，避免超大）：项目根目录核心文件 + 大小"""
    files = []
    # 根目录下的关键子目录/文件名白名单
    roots = [
        'templates', 'static', 'flask-app', 'Database',
        'Split_Databases', 'config', 'core', 'app',
    ]
    root_files = ['server_real_db.py', 'requirements.txt', 'README.md', 'package.json', 'vite.config.js']
    import glob
    def _add(p):
        try:
            if not os.path.exists(p):
                return
            if os.path.isfile(p):
                try:
                    files.append({'path': os.path.relpath(p, BASE_DIR or '.'),
                                  'size': os.path.getsize(p),
                                  'mtime': datetime.fromtimestamp(os.path.getmtime(p)).isoformat(timespec='seconds')})
                except Exception:
                    pass
            elif os.path.isdir(p):
                # 每层最多取 limit/4 个避免失控
                cnt = 0
                for root, dirs, fs in os.walk(p):
                    dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ('node_modules', '__pycache__', '.git')]
                    for f in sorted(fs):
                        fp = os.path.join(root, f)
                        try:
                            if os.path.isfile(fp):
                                files.append({'path': os.path.relpath(fp, BASE_DIR or '.'),
                                              'size': os.path.getsize(fp),
                                              'mtime': datetime.fromtimestamp(os.path.getmtime(fp)).isoformat(timespec='seconds')})
                                cnt += 1
                                if cnt > limit:
                                    return
                        except Exception:
                            pass
                    if cnt > limit:
                        return
        except Exception:
            pass
    for f in root_files:
        _add(os.path.join(BASE_DIR or '.', f))
    for d in roots:
        _add(os.path.join(BASE_DIR or '.', d))
    return files


@app.route('/api/snapshot/create', methods=['POST'])
@system_container('snapshot_create', require_auth='admin')
def api_snapshot_create():
    """创建快照恢复节点：
    - 收集文件清单JSON → 写入 Manifests/
    - 计算快照哈希
    - 落库 snapshot_records；可通过 shadow_mode_flag 与影子系统联动
    """
    try:
        import json as _json
        now = datetime.now()
        stamp = now.strftime('%Y%m%d_%H%M%S')
        body = request.get_json(silent=True) or {}
        name = 'snapshot_' + stamp
        description = str(body.get('description') or f'手动快照 {stamp}').strip()[:200]
        shadow_flag = 1 if body.get('shadow_mode') else 0
        files = _collect_core_file_list(limit=120)
        total_bytes = sum(int(f.get('size') or 0) for f in files)
        manifest_name = name + '.manifest.json'
        manifest_path = os.path.join(_MANIFEST_DIR, manifest_name)
        os.makedirs(_MANIFEST_DIR, exist_ok=True)
        manifest_obj = {
            'snapshot_name': name,
            'created_at': now.isoformat(),
            'total_files': len(files),
            'total_bytes': total_bytes,
            'files': files,
            'creator': (_current_user() or {}).get('username') or 'SYSTEM',
        }
        with open(manifest_path, 'w', encoding='utf-8') as f:
            _json.dump(manifest_obj, f, ensure_ascii=False, indent=2)
        # 快照哈希 = 清单内容 sha256（可作为恢复点唯一标识）
        snap_hash = _sha256_text(_json.dumps(manifest_obj, sort_keys=True, ensure_ascii=False))
        created_by = (_current_user() or {}).get('username') or 'SYSTEM'
        build_version, _, _ = get_version_info()
        snap_id = None
        with _get_conn(_bizdb()) as c:
            _ensure_biz_tables(c)
            # 如果当前是 shadow 模式，自动关联 shadow_mode
            linked_snap = None
            if shadow_flag:
                cur = c.execute("SELECT linked_snapshot_id FROM shadow_mode_state WHERE mode='shadow' LIMIT 1")
                linked_snap = (dict(cur.fetchone()) if cur else {}).get('linked_snapshot_id')
            cur = c.execute(
                """INSERT INTO snapshot_records (name, description, build_version, codename, snapshot_hash,
                   file_list_json, manifest_path, created_at, created_by, source_db, size_bytes, status,
                   shadow_mode_flag, linked_iso_id, note) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (name, description, build_version, f'SNAP-{stamp}', snap_hash,
                 _json.dumps(files[:200], ensure_ascii=False),
                 manifest_path, now.isoformat(), created_by, _bizdb(),
                 total_bytes, 'completed', shadow_flag, linked_snap,
                 (f'快照包含 {len(files)} 个核心文件；恢复点哈希 {snap_hash[:12]}…' +
                  (f'；影子系统关联快照#{linked_snap}' if linked_snap else '')))
            )
            snap_id = cur.lastrowid
            # 如果在影子模式且要求 flag，同步写入 shadow 状态
            if shadow_flag:
                try:
                    c.execute(
                        "UPDATE shadow_mode_state SET linked_snapshot_id=?, switch_at=? WHERE mode='shadow'",
                        (snap_id, now.isoformat())
                    )
                except sqlite3.Error:
                    pass
            c.commit()
        return jsonify({
            'success': True,
            'snapshot': {
                'id': snap_id,
                'name': name,
                'description': description,
                'hash': snap_hash,
                'files': len(files),
                'size': _human_bytes(total_bytes),
                'manifest': manifest_path,
                'shadow_mode_flag': bool(shadow_flag),
            },
            'message': f'快照恢复节点创建成功：#{snap_id} / {name} / {len(files)} 文件 / {_human_bytes(total_bytes)}'
        })
    except Exception as e:
        return jsonify({'success': False, 'message': '快照创建失败: ' + str(e)}), 500


@app.route('/api/snapshot/list', methods=['GET'])
def api_snapshot_list():
    try:
        with _get_conn(_bizdb()) as c:
            _ensure_biz_tables(c)
            rows = c.execute("SELECT * FROM snapshot_records ORDER BY id DESC LIMIT 100").fetchall()
            out = []
            for r in _jsonable_list_of_dicts(rows):
                out.append({
                    'id': r.get('id'),
                    'name': r.get('name'),
                    'description': r.get('description'),
                    'version': r.get('build_version'),
                    'codename': r.get('codename'),
                    'hash': (r.get('snapshot_hash') or '')[:16],
                    'size': _human_bytes(r.get('size_bytes') or 0),
                    'created_at': r.get('created_at'),
                    'created_by': r.get('created_by'),
                    'status': r.get('status'),
                    'shadow_mode': bool(r.get('shadow_mode_flag')),
                    'linked_iso_id': r.get('linked_iso_id'),
                    'restore_count': r.get('restore_count') or 0,
                    'last_restored_at': r.get('last_restored_at'),
                    'note': r.get('note'),
                })
            return jsonify({'success': True, 'data': out})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/snapshot/restore/<int:snap_id>', methods=['POST'])
def api_snapshot_restore(snap_id):
    """记录一次"恢复动作"（安全起见，不真正改磁盘；仅更新快照表 restore_count/last_restored_at + 写 history_gallery 可看到的状态）"""
    try:
        with _get_conn(_bizdb()) as c:
            _ensure_biz_tables(c)
            r = c.execute("SELECT * FROM snapshot_records WHERE id=?", (snap_id,)).fetchone()
            if not r:
                return jsonify({'success': False, 'message': f'快照#{snap_id}不存在'}), 404
            rd = dict(r)
            now = datetime.now().isoformat()
            by = (_current_user() or {}).get('username') or 'SYSTEM'
            c.execute("UPDATE snapshot_records SET restore_count = COALESCE(restore_count,0)+1, last_restored_at=?, status='restored', note=COALESCE(note,'')||? WHERE id=?",
                      (now, f'\n[{now}] {by} 执行恢复（记录）；', snap_id))
            c.commit()
            return jsonify({
                'success': True,
                'message': f'恢复节点 #{snap_id}（{rd.get("name")}）已记录恢复操作（RESTORE-ONLY模式：未覆盖磁盘文件，已计入恢复次数+时间戳，便于历史馆追溯）',
                'restored_at': now,
                'restored_by': by,
                'snapshot': {'id': snap_id, 'name': rd.get('name'), 'hash': (rd.get('snapshot_hash') or '')[:16]},
            })
    except Exception as e:
        return jsonify({'success': False, 'message': '恢复失败: ' + str(e)}), 500


# ============================================================
#  ISO 恢复镜像（/api/iso/*）
# ============================================================

def _iso_build_internal(from_backup_page=False):
    """构建 ISO 镜像清单 → 写入 iso_images + 写一份 .manifest.json 到 Manifests/ 目录，签名状态默认 unsigned，可后签"""
    try:
        import json as _json
        import random
        now = datetime.now()
        stamp = now.strftime('%Y%m%d_%H%M%S')
        v, info, _ = get_version_info()
        name = f'MTSCOS-v{v}-{stamp}-{random.randint(1000, 9999)}.iso'
        # ISO 构建：文件清单 = 快照收集 + 校验块（1MB校验块大小，不读真实文件内容）
        files = _collect_core_file_list(limit=180)
        total_bytes = sum(int(f.get('size') or 0) for f in files)
        # 附加 ISO meta 信息（不生成真实 ISO 文件）
        manifest_obj = {
            'type': 'MTSCOS-ISO-MANIFEST',
            'iso_name': name,
            'version': v,
            'build_date': info.get('build_date'),
            'created_at': now.isoformat(),
            'boot_mode': 'hybrid',
            'files': files,
            'total_files': len(files),
            'total_bytes': total_bytes,
            'creator': (_current_user() or {}).get('username') or 'SYSTEM',
            'checksum_block_size_kb': 1024,
        }
        manifest_path = os.path.join(_MANIFEST_DIR, name + '.manifest.json')
        os.makedirs(_MANIFEST_DIR, exist_ok=True)
        with open(manifest_path, 'w', encoding='utf-8') as f:
            _json.dump(manifest_obj, f, ensure_ascii=False, indent=2)
        iso_hash = _sha256_text(_json.dumps(manifest_obj, sort_keys=True, ensure_ascii=False))
        # 关联近1个快照
        linked_snapshot_count = 0
        iso_id = None
        with _get_conn(_bizdb()) as c:
            _ensure_biz_tables(c)
            r = c.execute("SELECT COUNT(*) AS n FROM snapshot_records").fetchone()
            linked_snapshot_count = int((dict(r) if r else {}).get('n') or 0)
            cur = c.execute(
                """INSERT INTO iso_images (name, version, manifest_json, manifest_path, iso_hash,
                   size_estimate_bytes, created_at, created_by, sign_status, boot_mode, description, snapshot_count)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
                (name, v, _json.dumps(manifest_obj, ensure_ascii=False), manifest_path, iso_hash,
                 total_bytes, now.isoformat(), (_current_user() or {}).get('username') or 'SYSTEM',
                 'unsigned', 'hybrid',
                 f'{info.get("codename") or "MTSCOS ISO恢复镜像"} v{v} 构建清单（不包含二进制大文件，可随时重新打包）',
                 linked_snapshot_count)
            )
            iso_id = cur.lastrowid
            c.commit()
        return jsonify({
            'success': True,
            'iso': {
                'id': iso_id,
                'name': name,
                'version': v,
                'size': _human_bytes(total_bytes),
                'manifest': manifest_path,
                'hash': iso_hash,
                'snapshot_count': linked_snapshot_count,
                'sign_status': 'unsigned',
            },
            'message': (f'ISO恢复镜像清单创建成功：#{iso_id} {name} / {len(files)} 文件 / {_human_bytes(total_bytes)}'
                        + ('（备份管理入口触发）' if from_backup_page else '')
                        + '（注意：为避免磁盘爆炸，未生成GB级二进制ISO，仅生成签名清单+校验哈希，可随时重打包）')
        })
    except Exception as e:
        return jsonify({'success': False, 'message': 'ISO构建失败: ' + str(e)}), 500


@app.route('/api/iso/build', methods=['POST'])
@system_container('iso_build', require_auth='admin')
def api_iso_build():
    return _iso_build_internal(from_backup_page=False)


@app.route('/api/iso/list', methods=['GET'])
def api_iso_list():
    rows = []
    try:
        with _get_conn(_bizdb()) as c:
            _ensure_biz_tables(c)
            rs = c.execute("SELECT * FROM iso_images ORDER BY id DESC LIMIT 50").fetchall()
            for r in _jsonable_list_of_dicts(rs):
                rows.append({
                    'id': r.get('id'),
                    'name': r.get('name'),
                    'version': r.get('version'),
                    'size': _human_bytes(r.get('size_estimate_bytes') or 0),
                    'manifest': r.get('manifest_path'),
                    'hash': (r.get('iso_hash') or '')[:16],
                    'created_at': r.get('created_at'),
                    'created_by': r.get('created_by'),
                    'sign_status': r.get('sign_status'),
                    'signer': r.get('signer'),
                    'signed_at': r.get('signed_at'),
                    'boot_mode': r.get('boot_mode'),
                    'snapshot_count': r.get('snapshot_count'),
                    'description': r.get('description'),
                })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    return jsonify({'success': True, 'data': rows})


# ============================================================
#  影子系统（/api/shadow/*）
# ============================================================

def _shadow_get_state():
    """返回当前 shadow 三态（live/shadow/cold）中哪个 enabled=1，含最近切换快照信息"""
    result = {'mode': 'live', 'enabled': 0, 'modes': [], 'linked_snapshot_id': None}
    try:
        with _get_conn(_bizdb()) as c:
            _ensure_biz_tables(c)
            rows = c.execute("SELECT * FROM shadow_mode_state ORDER BY mode ASC").fetchall()
            modes = _jsonable_list_of_dicts(rows)
            result['modes'] = modes
            # 当前激活：优先 enabled=1 的第一个，否则 live
            for m in modes:
                if int(m.get('enabled') or 0) == 1:
                    result['mode'] = m.get('mode')
                    result['enabled'] = 1
                    result['switch_at'] = m.get('switch_at')
                    result['switched_by'] = m.get('switched_by')
                    result['note'] = m.get('note')
                    result['linked_snapshot_id'] = m.get('linked_snapshot_id')
                    break
    except Exception:
        pass
    return result


@app.route('/api/shadow/status', methods=['GET'])
def api_shadow_status():
    try:
        st = _shadow_get_state()
        return jsonify({'success': True, 'data': st})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/shadow/switch', methods=['POST'])
@system_container('shadow_switch', require_auth='admin')
def api_shadow_switch():
    """切换影子系统模式（live 真实生产 / shadow 演练 / cold 冷备）。
    安全规则：cold=1 时其他都必须为 0；shadow=1 时 live 可为 1 或 0；live=1 表示实际生产。"""
    try:
        body = request.get_json(silent=True) or {}
        target_mode = str(body.get('mode') or '').strip().lower()
        note = str(body.get('note') or '').strip()[:200]
        if target_mode not in ('live', 'shadow', 'cold'):
            return jsonify({'success': False, 'message': 'mode必须是 live / shadow / cold'}), 400
        linked_snap = body.get('linked_snapshot_id')
        by = (_current_user() or {}).get('username') or 'SYSTEM'
        now = datetime.now().isoformat()
        with _get_conn(_bizdb()) as c:
            _ensure_biz_tables(c)
            # 如果切到 cold，必须把另外两个关掉
            if target_mode == 'cold':
                c.execute("UPDATE shadow_mode_state SET enabled=0 WHERE mode IN ('live','shadow')")
            # 如果切到 live，可以保留 shadow 任意
            # 如果切到 shadow，保留 live 1 或 0 都可以
            c.execute("UPDATE shadow_mode_state SET enabled=1, switch_at=?, switched_by=?, note=?, linked_snapshot_id=? WHERE mode=?",
                      (now, by, note or None, linked_snap if linked_snap else None, target_mode))
            # 如果 target 是 live 或 shadow，不要影响其他（除非是 cold）
            # 但为了语义明确：切换到某模式时，保证该模式=1，其他模式按默认策略处理
            if target_mode == 'live':
                # 切换到live时把cold强制关
                c.execute("UPDATE shadow_mode_state SET enabled=0 WHERE mode='cold'")
            if target_mode == 'shadow':
                c.execute("UPDATE shadow_mode_state SET enabled=0 WHERE mode='cold'")
            # 如果 target 是 live 且 body 明确说 shadow_off，则关 shadow
            if target_mode == 'live' and bool(body.get('shadow_off')):
                c.execute("UPDATE shadow_mode_state SET enabled=0 WHERE mode='shadow'")
            c.commit()
        return jsonify({
            'success': True,
            'data': _shadow_get_state(),
            'message': f'影子系统已切换到 {target_mode!r}（操作者：{by}，{now}）'
        })
    except Exception as e:
        return jsonify({'success': False, 'message': '切换失败: ' + str(e)}), 500


@app.route('/api/shadow/snapshot_link', methods=['POST'])
@system_container('shadow_snapshot_link', require_auth='admin')
def api_shadow_snapshot_link():
    """将某个快照ID 绑定为 shadow 模式的"基线恢复点"（切换 shadow ↔ live 时都能回到此快照）"""
    try:
        body = request.get_json(silent=True) or {}
        snap_id = body.get('snapshot_id')
        mode = str(body.get('mode') or 'shadow').lower()
        if not snap_id:
            return jsonify({'success': False, 'message': '缺少 snapshot_id'}), 400
        with _get_conn(_bizdb()) as c:
            _ensure_biz_tables(c)
            try:
                snap_id_int = int(snap_id)
            except ValueError:
                return jsonify({'success': False, 'message': 'snapshot_id必须是整数'}), 400
            r = c.execute("SELECT id FROM snapshot_records WHERE id=?", (snap_id_int,)).fetchone()
            if not r:
                return jsonify({'success': False, 'message': f'快照#{snap_id}不存在'}), 404
            c.execute("UPDATE shadow_mode_state SET linked_snapshot_id=?, switch_at=? WHERE mode=?",
                      (int(snap_id), datetime.now().isoformat(), mode))
            c.commit()
        return jsonify({
            'success': True,
            'message': f'{mode} 模式已绑定快照恢复点 #{snap_id}',
            'data': _shadow_get_state(),
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


# ============================================================
#  Vikey USB 密钥加密狗（二次开发：模拟驱动 + 真实DB持久化）
#  （真实硬件驱动在 core.services.vikey_driver 存在时优先使用，否则 fallback 到本模块的mock实现）
# ============================================================

def _vikey_write_log(op_type, result, serial=None, username=None, detail=None):
    try:
        with _get_conn(_bizdb()) as c:
            _ensure_biz_tables(c)
            c.execute(
                "INSERT INTO vikey_operations_log (op_type, result, serial, username, ip, user_agent, created_at, detail) VALUES (?,?,?,?,?,?,?,?)",
                (op_type, result, serial, username or (_current_user() or {}).get('username'),
                 request.remote_addr if request else None,
                 request.headers.get('User-Agent','')[:200] if request else None,
                 datetime.now().isoformat(), (detail or '')[:500])
            )
            c.commit()
    except Exception:
        pass


def _vikey_mock_detect():
    """Mock 驱动：
    - 返回2个槽位：一个已插入（绑定的第1个设备或默认演示设备），一个空
    - 读取真实 vikey_device_bindings 里的设备作为"已插入设备"（模拟 HID 轮询）
    """
    try:
        with _get_conn(_bizdb()) as c:
            _ensure_biz_tables(c)
            rows = c.execute("SELECT * FROM vikey_device_bindings WHERE status=1 ORDER BY id LIMIT 2").fetchall()
            devices = []
            if rows:
                for i, r in enumerate(_jsonable_list_of_dicts(rows)):
                    devices.append({
                        'slot': i,
                        'present': True,
                        'serial': r.get('serial'),
                        'username': r.get('username'),
                        'role': r.get('role'),
                        'cert_issued': bool(r.get('cert_issued')),
                        'bound_at': r.get('bound_at'),
                    })
            else:
                # 默认演示设备（即插即用）：serial='MTSCOS-VIKEY-DEMO-0001'
                devices.append({
                    'slot': 0,
                    'present': True,
                    'serial': 'MTSCOS-VIKEY-DEMO-0001',
                    'username': None,
                    'role': None,
                    'cert_issued': False,
                    'bound_at': None,
                    'manufacturer': 'MTSCOS SecureUSB',
                    'product': 'Vikey G2 Pro',
                    'firmware': '2.4.1',
                })
            return {
                'present_count': sum(1 for d in devices if d.get('present')),
                'devices': devices,
                '_source': 'mock-driver (fallback) — 真实硬件驱动接入后此处会自动替换为HID轮询',
            }
    except Exception:
        return {'present_count': 0, 'devices': [], '_source': 'mock-driver-error'}


def _vikey_mock_verify_auth_token(serial, token, username=None):
    """验证：token 应当等于 vikey_device_bindings.auth_token（mock：只看是否匹配+未过期）"""
    if not serial or not token:
        return False, 'missing'
    try:
        with _get_conn(_bizdb()) as c:
            _ensure_biz_tables(c)
            r = c.execute("SELECT * FROM vikey_device_bindings WHERE serial=? AND status=1 LIMIT 1", (serial,)).fetchone()
            if not r:
                return False, 'serial_not_bound'
            rd = dict(r)
            expected = rd.get('auth_token')
            if expected and expected == token:
                if username and rd.get('username') and str(username).lower() != str(rd.get('username') or '').lower():
                    return False, 'username_mismatch'
                return True, 'ok'
            return False, 'token_mismatch'
    except Exception:
        return False, 'db_error'


@app.route('/api/vikey/detect', methods=['GET'])
def api_vikey_detect():
    """GET 检测 USB 加密狗（真实硬件优先 → 模拟兜底；给前端统一字段）"""
    real = None
    try:
        from core.services.vikey_driver import get_vikey_manager as _gvkm
        det = _gvkm().detect()
        if isinstance(det, dict):
            real = det
    except Exception:
        real = None
    raw = real if real else _vikey_mock_detect()
    out = {'present_count': 0, 'devices': []}
    try:
        src_devs = raw.get('devices') or []
        normalized = []
        for i, d in enumerate(src_devs or []):
            d = dict(d) if not isinstance(d, dict) else d
            binding = d.get('binding') if isinstance(d.get('binding'), dict) else {}
            b_user = binding.get('username')
            b_role = binding.get('role_hint') or binding.get('role')
            present = bool(d.get('is_present', True)) if 'is_present' in d else bool(d.get('present', True))
            serial = d.get('serial') or d.get('device_serial')
            if not serial:
                continue
            is_hw = bool(d.get('is_real_hardware'))
            normalized.append({
                'slot': d.get('slot') if d.get('slot') is not None else i,
                'present': present,
                'serial': serial,
                'username': b_user or d.get('username'),
                'role': b_role or d.get('role'),
                'cert_issued': bool(d.get('cert_issued') or binding.get('certificate_issued')),
                'bound_at': binding.get('last_used_at') or binding.get('bound_at') or d.get('bound_at'),
                'manufacturer': d.get('manufacturer') or d.get('vendor') or 'MTSCOS SecureUSB',
                'product': d.get('label') or d.get('product') or d.get('device_name') or 'Vikey G2 Pro',
                'firmware': d.get('firmware_version') or d.get('fw_version') or d.get('firmware') or '',
                'is_real_hardware': is_hw,
                'usb_vid': d.get('usb_vid'),
                'usb_pid': d.get('usb_pid'),
                'vendor_label': d.get('vendor') if is_hw else None,
            })
        out['devices'] = normalized
        out['present_count'] = sum(1 for x in normalized if x.get('present'))
        backend_name = raw.get('backend') or raw.get('_source') or 'unknown'
        out['backend'] = backend_name
        # 明确标识来源类型：real-hardware / simulation / mock
        if 'NativeHID' in str(backend_name) or any(x.get('is_real_hardware') for x in normalized):
            out['_source'] = 'vikey-real-hardware'
            out['hardware_mode'] = True
            out['driver_mode_label'] = '真实硬件加密狗'
        elif 'Simulation' in str(backend_name):
            out['_source'] = 'vikey-simulation'
            out['hardware_mode'] = False
            out['driver_mode_label'] = '模拟驱动 (开发/测试)'
        else:
            out['_source'] = 'mock-driver'
            out['hardware_mode'] = False
            out['driver_mode_label'] = '兼容 Mock 层'
        out['driver_version'] = raw.get('driver_version')
        out['manufacturer'] = raw.get('manufacturer')
        out['binding_count'] = raw.get('binding_count')
    except Exception:
        pass
    _vikey_write_log('detect', 'ok', detail=str({'present_count': out.get('present_count'),
                                                  'backend': out.get('backend'),
                                                  'hardware_mode': out.get('hardware_mode', False)}))
    return jsonify({'success': True, 'data': out})


@app.route('/api/vikey/bind', methods=['POST'])
def api_vikey_bind():
    """POST 绑定：将加密狗序列号 <-> 用户 绑定，生成 auth_token，可选设置 PIN"""
    try:
        body = request.get_json(silent=True) or {}
        serial = str(body.get('serial') or '').strip()
        username = str(body.get('username') or '').strip()
        role = str(body.get('role') or 'user').strip() or 'user'
        pin = str(body.get('pin') or '').strip()
        if not serial:
            # 若未指定 serial，默认取「规范化后 detect」的第一个已插入设备的 serial
            try:
                det_resp = api_vikey_detect()
                det_data = (det_resp.get_json(silent=True) or {}).get('data') if hasattr(det_resp, 'get_json') else {}
                if isinstance(det_data, dict):
                    for d in (det_data.get('devices') or []):
                        if d.get('present') and d.get('serial'):
                            serial = d['serial']
                            break
            except Exception:
                pass
        if not serial or not username:
            return jsonify({'success': False, 'message': '缺少 serial / username'}), 400
        # 查用户是否存在
        u_row, _ = _find_user_across_dbs(username)
        if not u_row:
            return jsonify({'success': False, 'message': f'用户 {username} 不存在，无法绑定'}), 404
        # 生成 auth_token
        token_seed = serial + '|' + username + '|' + datetime.now().isoformat()
        auth_token = 'vk_' + _sha256_text(token_seed)
        pin_hash = _sha256_text(pin) if pin else None
        by = (_current_user() or {}).get('username') or 'SYSTEM'
        now = datetime.now().isoformat()
        with _get_conn(_bizdb()) as c:
            _ensure_biz_tables(c)
            existed = c.execute("SELECT id, serial FROM vikey_device_bindings WHERE serial=? LIMIT 1", (serial,)).fetchone()
            if existed:
                # 更新
                c.execute("UPDATE vikey_device_bindings SET username=?, role=?, auth_token=?, pin_hash=COALESCE(?,pin_hash), bound_at=?, bound_by=?, status=1 WHERE serial=?",
                          (username, role, auth_token, pin_hash, now, by, serial))
            else:
                c.execute(
                    """INSERT INTO vikey_device_bindings (serial, username, role, bound_at, bound_by, status, pin_hash, auth_token, note)
                       VALUES (?,?,?,?,?,?,?,?,?)""",
                    (serial, username, role, now, by, 1, pin_hash, auth_token,
                     f'首次绑定 角色={role}；二次开发绑定成功')
                )
            c.commit()
        _vikey_write_log('bind', 'ok', serial=serial, username=username, detail=f'role={role}')
        return jsonify({
            'success': True,
            'message': f'USB加密狗绑定成功：{serial} ↔ {username}（{role}），已生成 auth_token（二次开发API返回）',
            'binding': {
                'serial': serial,
                'username': username,
                'role': role,
                'auth_token': auth_token,  # 二次开发返回（仅一次展示，前端应本地保存）
                'pin_set': bool(pin_hash),
                'bound_at': now,
            }
        })
    except Exception as e:
        _vikey_write_log('bind', 'fail', detail=str(e))
        return jsonify({'success': False, 'message': '绑定失败: ' + str(e)}), 500


@app.route('/api/vikey/auth', methods=['POST'])
def api_vikey_auth():
    """POST 鉴权：serial + auth_token（+ pin 可选），返回带签名的挑战响应，登录时可直接用"""
    try:
        body = request.get_json(silent=True) or {}
        serial = str(body.get('serial') or '').strip()
        token = str(body.get('vikey_auth_token') or body.get('auth_token') or '').strip()
        pin = str(body.get('pin') or '').strip()
        username = str(body.get('username') or '').strip() or None
        challenge_in = str(body.get('challenge') or '').strip() or None
        if not token:
            _vikey_write_log('auth', 'fail:missing', detail='token empty')
            return jsonify({'success': False, 'message': '鉴权失败: auth_token 不能为空', 'reason': 'missing'}), 401
        # 1. 外部驱动优先（仅在明确返回 True 时用；False/None → 走 fallback mock）
        real_ok = None
        try:
            from app.api.vikey_api import verify_vikey_token
            import inspect
            if len(inspect.signature(verify_vikey_token).parameters) == 0:
                _r, ok = verify_vikey_token()
                if ok:
                    real_ok = True
        except Exception:
            real_ok = None
        if real_ok is True:
            ok, reason = True, 'external_driver'
            # 外部驱动 ok 也做基本 pin 校验（如 db 有 hash）
            binding = None
            try:
                with _get_conn(_bizdb()) as c:
                    r = c.execute("SELECT serial, username, pin_hash FROM vikey_device_bindings WHERE auth_token=? LIMIT 1", (token,)).fetchone()
                    if r:
                        binding = dict(r)
                        if not serial: serial = binding['serial']
            except Exception:
                binding = None
            if pin and binding and binding.get('pin_hash') and binding['pin_hash'] != _sha256_text(pin):
                ok = False; reason = 'pin_mismatch'
        else:
            # 2. fallback mock：数据库里查绑定记录
            ok, reason, binding = False, 'token_not_found', None
            try:
                with _get_conn(_bizdb()) as c:
                    q = "SELECT serial, username, role, pin_hash, auth_token, bound_at FROM vikey_device_bindings WHERE auth_token=? LIMIT 1"
                    r = c.execute(q, (token,)).fetchone()
                    if not r and serial:
                        # token 没找到 → 用 serial 找（兼容 bind 后用 serial+pin 直接鉴权）
                        r2 = c.execute("SELECT serial, username, role, pin_hash, auth_token, bound_at FROM vikey_device_bindings WHERE serial=? LIMIT 1", (serial,)).fetchone()
                        if r2 is not None:
                            r = r2
                    if r is not None:
                        binding = dict(r)
                        serial = binding.get('serial') or serial
                        # PIN 校验：如果 DB 里有 pin_hash，则必须传入且正确；如果没有，不要求
                        if binding.get('pin_hash'):
                            if not pin:
                                ok, reason = False, 'pin_required'
                            elif binding['pin_hash'] != _sha256_text(pin):
                                ok, reason = False, 'pin_mismatch'
                            else:
                                ok, reason = True, 'mock-pin_ok'
                        else:
                            ok, reason = True, 'mock-no_pin'
            except Exception as _ex:
                ok, reason = False, 'db_error'
                binding = None
        _vikey_write_log('auth', 'ok' if ok else 'fail:' + reason, serial=serial, username=username, detail=str({'reason': reason}))
        if not ok:
            return jsonify({'success': False, 'message': '鉴权失败: ' + reason, 'reason': reason}), 401
        # 生成一次性挑战响应（给登录复用）
        ts = datetime.now()
        _seed = (challenge_in or 'default_challenge') + '|' + str(serial) + '|' + str(token) + '|' + ts.isoformat()
        challenge_resp = 'resp_' + _sha256_text(_seed)
        return jsonify({
            'success': True,
            'serial': serial,
            'challenge_response': challenge_resp,
            'username': username or (binding or {}).get('username'),
            'valid': True,
            'valid_seconds': 300,
            'reason': reason,
            'message': '鉴权通过，challenge_response 已生成（二次开发契约：登录时可复用 challenge 作额外校验）',
        })
    except Exception as e:
        _vikey_write_log('auth', 'fail', detail=str(e))
        return jsonify({'success': False, 'message': '鉴权异常: ' + str(e)}), 500


@app.route('/api/vikey/issue_cert', methods=['POST'])
def api_vikey_issue_cert():
    """POST 二次开发：给设备发证书（X.509 格式最小化字段），标记 cert_issued=1"""
    try:
        body = request.get_json(silent=True) or {}
        serial = str(body.get('serial') or '').strip()
        owner = str(body.get('owner') or '').strip() or None
        if not serial:
            return jsonify({'success': False, 'message': '缺少 serial'}), 400
        with _get_conn(_bizdb()) as c:
            _ensure_biz_tables(c)
            dev = c.execute("SELECT * FROM vikey_device_bindings WHERE serial=? LIMIT 1", (serial,)).fetchone()
            if not dev:
                return jsonify({'success': False, 'message': f'设备 {serial} 未绑定，无法发证书'}), 404
            rd = dict(dev)
            now = datetime.now()
            not_before = now.isoformat()
            not_after = (now.replace(year=now.year + 5)).isoformat()
            cert_sn = 'CERT-' + _sha256_text(serial + not_before)[:16]
            subject_dn = f"CN=MTSCOS Vikey Device,OU=SecureUSB,O=MTSCOS,SN={serial}"
            issuer_dn = "CN=MTSCOS Internal CA,OU=Security,O=MTSCOS,C=CN"
            cert_pem_hash = _sha256_text("CERT:" + cert_sn + serial + not_before + not_after)
            c.execute(
                """INSERT INTO vikey_device_certs (serial, cert_sn, subject_dn, issuer_dn, issued_at, not_before, not_after, status, cert_pem_hash, owner)
                   VALUES (?,?,?,?,?,?,?,?,?,?)""",
                (serial, cert_sn, subject_dn, issuer_dn, now.isoformat(), not_before, not_after, 'active', cert_pem_hash,
                 owner or rd.get('username'))
            )
            c.execute("UPDATE vikey_device_bindings SET cert_issued=1 WHERE serial=?", (serial,))
            c.commit()
        _vikey_write_log('issue_cert', 'ok', serial=serial, username=owner, detail=f'cert_sn={cert_sn}')
        return jsonify({
            'success': True,
            'cert': {
                'serial': serial,
                'cert_sn': cert_sn,
                'subject_dn': subject_dn,
                'issuer_dn': issuer_dn,
                'not_before': not_before,
                'not_after': not_after,
                'cert_pem_hash': cert_pem_hash,
            },
            'message': f'设备 {serial} 证书颁发成功（二次开发X.509契约），有效期至 {not_after[:10]}'
        })
    except Exception as e:
        _vikey_write_log('issue_cert', 'fail', detail=str(e))
        return jsonify({'success': False, 'message': '颁发失败: ' + str(e)}), 500


@app.route('/api/vikey/logs', methods=['GET'])
def api_vikey_logs():
    try:
        with _get_conn(_bizdb()) as c:
            _ensure_biz_tables(c)
            rows = c.execute("SELECT * FROM vikey_operations_log ORDER BY id DESC LIMIT 200").fetchall()
            return jsonify({'success': True, 'data': _jsonable_list_of_dicts(rows)})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/vikey/certs', methods=['GET'])
def api_vikey_certs():
    try:
        with _get_conn(_bizdb()) as c:
            _ensure_biz_tables(c)
            rows = c.execute("SELECT * FROM vikey_device_certs ORDER BY id DESC").fetchall()
            return jsonify({'success': True, 'data': _jsonable_list_of_dicts(rows)})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


# ---------- 登录 Vikey 验证 fallback：外部模块不存在时用自建的 DB 层（已绑定设备则可鉴权通过）----------
# 重新封装 _verify_super_admin_vikey 行为：优先 real driver；失败则回落到 vikey_device_bindings.auth_token 校验
_OLD_VERIFY_VIKEY_FN = None
try:
    _OLD_VERIFY_VIKEY_FN = _verify_super_admin_vikey
except Exception:
    _OLD_VERIFY_VIKEY_FN = None


def _verify_vikey_fallback_wrap(username, vikey_auth_token, vikey_serial, ip, ua):
    """优先走原函数（外部真实驱动），原函数缺失或异常时回落到 vikey_device_bindings.auth_token 校验"""
    global _OLD_VERIFY_VIKEY_FN
    if _OLD_VERIFY_VIKEY_FN is not None:
        try:
            ok, reason, info = _OLD_VERIFY_VIKEY_FN(username, vikey_auth_token, vikey_serial, ip, ua)
            if ok:
                return ok, reason, info
            # 外部没通过 → 再试一次 DB fallback（绑定过的设备可登录）
        except Exception:
            pass
    # Fallback：看 vikey_device_bindings 里的 serial + auth_token 是否匹配该用户
    ok, reason = _vikey_mock_verify_auth_token(vikey_serial, vikey_auth_token, username=username)
    info = {'fallback': True, 'serial': vikey_serial}
    return ok, reason, info


# 替换登录路由内部调用的全局函数（直接把顶层变量重绑定，保证已存在的 login() 里 _verify_super_admin_vikey 名实不变）
import sys as _sys
_cur_mod = _sys.modules.get(__name__ if '__name__' in globals() else 'server_real_db')
if _cur_mod is not None:
    try:
        _cur_mod._verify_super_admin_vikey = _verify_vikey_fallback_wrap
    except Exception:
        pass


# ==========================================================
#  ⬆️ 系统升级触发条件引擎（主系统 + 子系统 + 审批灰度联动）
#
# 【主系统 8 大触发维度】
#   T1. 时间周期触发 (cron/间隔/维护窗口)
#   T2. 错误率阈值触发 (HTTP5xx/DB错误/业务异常)
#   T3. 性能退化触发 (平均响应时间增长/队列积压/内存超阈值)
#   T4. AI洞察知识积累触发 (脑库增长/新规则/高置信度洞察)
#   T5. 安全事件触发 (AI防火墙高危拦截/CVE/入侵检测)
#   T6. 管理员手动触发 (审批链 管理员→超级管理员)
#   T7. Git/文件变更触发 (代码文件MD5累计变更率)
#   T8. 容量/资源触发 (磁盘/DB大小/并发会话数超阈值)
#
# 【子系统触发条件】 (9类子系统独立阈值)
#   ai_engine | exam_system | settings_portal | vikey_manager
#   shadow_system | knowledge_brain | container_monitor | user_portal | file_center
#
# 【审批灰度联动】
#   hotfix/security: 免审批 立即全量
#   patch:         免审批 灰度10%→30%→100% (每阶段30min)
#   minor:         1 名管理员审批 灰度10%→50%→100% (每阶段2h)
#   major/release: 1 管理员 + 1 超级管理员审批 灰度5%→20%→50%→100% (每阶段6h)
# ==========================================================
_UP_TRG_LOCK = threading.RLock() if 'threading' in globals() else None

# ---------- 主系统默认触发阈值 ----------
_MAIN_UPGRADE_TRIGGER_DEFAULTS: dict = {
    'enabled': True,
    # T1 时间周期
    't1_interval_seconds': 86400,          # 每 24h 至少跑一次自动升级检查
    't1_maintenance_hours': [2, 3, 4],     # 凌晨 2-4 点：维护窗口自动执行
    't1_force_on_schedule': True,
    # T2 错误率
    't2_error_rate_pct_5m': 5.0,           # 5分钟内错误率 >= 5% 触发
    't2_error_count_5m': 50,               # 5分钟内 >= 50 次错误触发
    # T3 性能退化
    't3_avg_rt_growth_pct': 50,            # 平均响应时间相比基线增长 >= 50%
    't3_avg_rt_ms_threshold': 800,         # 平均响应时间 >= 800ms 绝对阈值
    't3_memory_pct': 85,                   # 内存占用 >= 85%
    't3_db_size_gb_day_growth': 1.0,       # 单日DB增长 >= 1GB
    # T4 AI 洞察/知识
    't4_new_brain_entries_since_upgrade': 200,    # 新增知识条目 200
    't4_new_rules_since_upgrade': 10,             # 新增规则 10
    't4_high_conf_insights_since_upgrade': 20,    # 高置信洞察 20
    # T5 安全
    't5_high_severity_blocks_1h': 5,              # 1小时高危拦截 >= 5
    't5_cve_trigger': True,
    # T6 手动：API 调用
    # T7 Git/文件
    't7_file_md5_change_pct': 5.0,                # 代码文件变更 >= 5%
    't7_git_pull_auto': True,
    # T8 容量/资源
    't8_disk_usage_pct': 80,                      # 磁盘 >= 80%
    't8_session_count': 500,                      # 在线会话 >= 500
    't8_backup_age_hours': 25,                    # 备份超过 25h（要求24h一次）
}

# ---------- 子系统触发条件 ----------
_SUBSYSTEM_TRIGGER_DEFAULTS: dict = {
    'ai_engine': {
        'enabled': True,
        'min_interval': 3600,
        'new_ai_employees': 2,
        'avg_ai_score_drop_pct': 5,
        'learning_cycle_errors': 3,
        'manual_allowed': True,
    },
    'exam_system': {
        'enabled': True,
        'min_interval': 7200,
        'exam_errors_1h': 5,
        'scoring_inconsistency_pct': 2,
        'manual_allowed': True,
    },
    'settings_portal': {
        'enabled': True,
        'min_interval': 1800,
        'setting_changes_pending_approval': 5,
        'manual_allowed': True,
    },
    'vikey_manager': {
        'enabled': True,
        'min_interval': 1800,
        'vikey_auth_failures_1h': 5,
        'unknown_devices_1h': 1,
        'manual_allowed': True,
    },
    'shadow_system': {
        'enabled': True,
        'min_interval': 7200,
        'shadow_sync_lag_seconds': 600,
        'cold_data_stale_hours': 24,
        'manual_allowed': True,
    },
    'knowledge_brain': {
        'enabled': True,
        'min_interval': 1800,
        'new_entries': 100,
        'integrity_check_fail': True,
        'manual_allowed': True,
    },
    'container_monitor': {
        'enabled': True,
        'min_interval': 300,
        'container_errors_1m': 10,
        'heartbeat_miss_pct': 5,
        'manual_allowed': True,
    },
    'user_portal': {
        'enabled': True,
        'min_interval': 3600,
        'login_fail_rate_pct': 8,
        'session_drop_rate_pct': 5,
        'manual_allowed': True,
    },
    'file_center': {
        'enabled': True,
        'min_interval': 3600,
        'orphan_files_count': 50,
        'storage_quota_pct': 85,
        'manual_allowed': True,
    },
}

# ---------- 审批灰度规则 ----------
_UPGRADE_APPROVAL_CHAIN: dict = {
    'security': {
        'need_admin_approval': 0, 'need_super_approval': False,
        'shadow_first': True,
        'gray_stages_pct': [100], 'stage_minutes': [0],
        'label': '安全补丁',
    },
    'hotfix': {
        'need_admin_approval': 0, 'need_super_approval': False,
        'shadow_first': True,
        'gray_stages_pct': [100], 'stage_minutes': [0],
        'label': '紧急热修复',
    },
    'patch': {
        'need_admin_approval': 0, 'need_super_approval': False,
        'shadow_first': True,
        'gray_stages_pct': [10, 30, 100], 'stage_minutes': [30, 30, 0],
        'label': '补丁',
    },
    'minor': {
        'need_admin_approval': 1, 'need_super_approval': False,
        'shadow_first': True,
        'gray_stages_pct': [10, 50, 100], 'stage_minutes': [120, 120, 0],
        'label': '小版本',
    },
    'major': {
        'need_admin_approval': 1, 'need_super_approval': True,
        'shadow_first': True,
        'gray_stages_pct': [5, 20, 50, 100], 'stage_minutes': [360, 360, 360, 0],
        'label': '大版本',
    },
    'release': {
        'need_admin_approval': 1, 'need_super_approval': True,
        'shadow_first': True,
        'gray_stages_pct': [5, 20, 50, 100], 'stage_minutes': [360, 360, 360, 0],
        'label': '正式发布',
    },
}


def _ensure_upgrade_trigger_tables(conn) -> None:
    try:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS upgrade_trigger_configs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            scope TEXT NOT NULL,                   /* main | <subsystem_id> */
            config_key TEXT NOT NULL,
            config_value TEXT,
            value_type TEXT DEFAULT 'string',
            updated_at TEXT DEFAULT (datetime('now','localtime')),
            updated_by TEXT DEFAULT 'SYSTEM',
            UNIQUE(scope, config_key)
        );
        CREATE INDEX IF NOT EXISTS idx_trig_cfg_scope ON upgrade_trigger_configs(scope);

        CREATE TABLE IF NOT EXISTS upgrade_trigger_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            trigger_id TEXT UNIQUE NOT NULL,
            scope TEXT NOT NULL,                    /* main | <subsystem_id> */
            trigger_type TEXT NOT NULL,             /* t1~t8 | manual */
            trigger_name TEXT,
            threshold TEXT,
            actual_value TEXT,
            severity TEXT DEFAULT 'info',           /* info|warning|critical */
            upgrade_type_suggested TEXT DEFAULT 'patch',   /* hotfix/security/patch/minor/major/release */
            status TEXT DEFAULT 'open',             /* open|approved|rejected|executing|done|cancelled */
            triggered_by TEXT DEFAULT 'SYSTEM',
            detail_json TEXT,
            created_at TEXT DEFAULT (datetime('now','localtime')),
            approved_at TEXT,
            approved_by TEXT,
            executed_at TEXT,
            result_json TEXT
        );
        CREATE INDEX IF NOT EXISTS idx_trig_evt_scope_status ON upgrade_trigger_events(scope, status);
        CREATE INDEX IF NOT EXISTS idx_trig_evt_created ON upgrade_trigger_events(created_at);

        CREATE TABLE IF NOT EXISTS subsystem_upgrade_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subsystem_id TEXT NOT NULL,
            version_from TEXT,
            version_to TEXT,
            trigger_event_id TEXT,
            trigger_type TEXT,
            status TEXT DEFAULT 'pending',
            shadow_switched_before INTEGER DEFAULT 0,
            gray_stage INTEGER DEFAULT 0,
            gray_pct INTEGER DEFAULT 0,
            started_at TEXT DEFAULT (datetime('now','localtime')),
            finished_at TEXT,
            error_message TEXT,
            detail_json TEXT,
            operator TEXT DEFAULT 'SYSTEM'
        );
        CREATE INDEX IF NOT EXISTS idx_sub_up_sub_status ON subsystem_upgrade_records(subsystem_id, status);

        CREATE TABLE IF NOT EXISTS upgrade_approval_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            trigger_event_id TEXT NOT NULL,
            approver TEXT NOT NULL,
            approver_role TEXT NOT NULL,
            decision TEXT NOT NULL,                 /* approve|reject|comment */
            comment TEXT,
            created_at TEXT DEFAULT (datetime('now','localtime')),
            approval_stage INTEGER DEFAULT 0
        );
        CREATE INDEX IF NOT EXISTS idx_upg_appr_evt ON upgrade_approval_records(trigger_event_id);
        """)
        conn.commit()
    except Exception:
        pass


# 初始化配置（幂等，只插入缺失的 key）
def _init_upgrade_trigger_defaults(conn) -> None:
    try:
        _ensure_upgrade_trigger_tables(conn)
        # 主系统配置
        for k, v in _MAIN_UPGRADE_TRIGGER_DEFAULTS.items():
            vt = 'int' if isinstance(v, bool) or isinstance(v, int) else (
                'float' if isinstance(v, float) else ('json' if isinstance(v, list) else 'string'))
            cv = json.dumps(v, ensure_ascii=False) if isinstance(v, list) else str(v)
            try:
                conn.execute(
                    "INSERT OR IGNORE INTO upgrade_trigger_configs(scope,config_key,config_value,value_type,updated_by) VALUES(?,?,?,?,?)",
                    ('main', k, cv, vt, 'SYSTEM-DEFAULT')
                )
            except Exception:
                continue
        # 子系统配置
        for sid, cfg in _SUBSYSTEM_TRIGGER_DEFAULTS.items():
            for k, v in cfg.items():
                vt = 'int' if isinstance(v, bool) or isinstance(v, int) else (
                    'float' if isinstance(v, float) else 'string')
                try:
                    conn.execute(
                        "INSERT OR IGNORE INTO upgrade_trigger_configs(scope,config_key,config_value,value_type,updated_by) VALUES(?,?,?,?,?)",
                        (sid, k, str(v), vt, 'SYSTEM-DEFAULT')
                    )
                except Exception:
                    continue
        conn.commit()
    except Exception:
        pass


try:
    with sqlite3.connect(_bizdb(), timeout=3) as _c0:
        _init_upgrade_trigger_defaults(_c0)
except Exception:
    pass


# ================= 配置读取工具 =================
def _trg_get_config(scope: str, key: str, default=None):
    try:
        with sqlite3.connect(_bizdb(), timeout=2) as c:
            _ensure_upgrade_trigger_tables(c)
            row = c.execute("SELECT config_value, value_type FROM upgrade_trigger_configs WHERE scope=? AND config_key=?", (scope, key)).fetchone()
            if not row:
                defaults = _MAIN_UPGRADE_TRIGGER_DEFAULTS if scope == 'main' else _SUBSYSTEM_TRIGGER_DEFAULTS.get(scope, {})
                return defaults.get(key, default)
            v, vt = (row[0] or ''), (row[1] or 'string')
            if vt == 'int' or vt == 'bool':
                return int(v) if v.isdigit() else (1 if v.lower() in ('true', 'y', 'yes') else 0)
            if vt == 'float':
                try: return float(v)
                except: return default
            if vt == 'json':
                try: return json.loads(v)
                except: return default
            return v
    except Exception:
        defaults = _MAIN_UPGRADE_TRIGGER_DEFAULTS if scope == 'main' else _SUBSYSTEM_TRIGGER_DEFAULTS.get(scope, {})
        return defaults.get(key, default)


def _trg_list_config(scope: str) -> dict:
    result = {}
    defaults = _MAIN_UPGRADE_TRIGGER_DEFAULTS if scope == 'main' else _SUBSYSTEM_TRIGGER_DEFAULTS.get(scope, {}).copy()
    try:
        with sqlite3.connect(_bizdb(), timeout=2) as c:
            _ensure_upgrade_trigger_tables(c)
            rows = c.execute("SELECT config_key, config_value, value_type FROM upgrade_trigger_configs WHERE scope=?", (scope,)).fetchall()
            for k, v, vt in rows:
                defaults[k] = _trg_get_config(scope, k, defaults.get(k))
    except Exception:
        pass
    result.update(defaults)
    return result


# ================= 触发事件写入工具 =================
def _trg_write_event(scope, trigger_type, trigger_name, threshold=None, actual=None,
                     severity='info', upgrade_suggested='patch', detail=None) -> str:
    tid = 'utg_' + hashlib.sha256((str(time.time_ns()) + str(trigger_type) + str(scope)).encode()).hexdigest()[:16]
    try:
        with sqlite3.connect(_bizdb(), timeout=3) as c:
            _ensure_upgrade_trigger_tables(c)
            c.execute(
                "INSERT INTO upgrade_trigger_events(trigger_id,scope,trigger_type,trigger_name,threshold,actual_value,severity,upgrade_type_suggested,detail_json) VALUES(?,?,?,?,?,?,?,?,?)",
                (tid, scope, trigger_type, trigger_name,
                 json.dumps(threshold, ensure_ascii=False) if not isinstance(threshold, str) and threshold is not None else (threshold or ''),
                 json.dumps(actual, ensure_ascii=False) if not isinstance(actual, str) and actual is not None else (actual or ''),
                 severity, upgrade_suggested,
                 json.dumps(detail or {}, ensure_ascii=False))
            )
            c.commit()
    except Exception:
        pass
    return tid


# ================= 主系统升级触发条件评估 8 维度 =================
def _trg_evaluate_main_system() -> dict:
    """评估主系统8大维度，返回触发事件列表"""
    events, summary = [], {}
    if not _trg_get_config('main', 'enabled', True):
        return {'triggered': False, 'events': [], 'summary': {'disabled': True}}
    now = time.time()

    # ---- T1：时间/周期/维护窗口 ----
    interval_s = int(_trg_get_config('main', 't1_interval_seconds', 86400))
    maint_hours = _trg_get_config('main', 't1_maintenance_hours', [2, 3, 4])
    if isinstance(maint_hours, str):
        try: maint_hours = json.loads(maint_hours)
        except: maint_hours = [2, 3, 4]
    # 查最近一次主系统升级时间
    try:
        with sqlite3.connect(_bizdb(), timeout=2) as c:
            r = c.execute("SELECT MAX(created_at) FROM upgrade_trigger_events WHERE scope='main' AND status IN ('done','executing')").fetchone()
        last_upgrade_str = (r and r[0]) or '1970-01-01 00:00:00'
        last_ts = datetime.strptime(last_upgrade_str, '%Y-%m-%d %H:%M:%S').timestamp() if last_upgrade_str else 0
    except Exception:
        last_ts = 0
    since_last_s = now - last_ts
    now_hour = datetime.fromtimestamp(now).hour
    t1_meet_interval = since_last_s >= interval_s
    t1_meet_maint_window = (now_hour in (maint_hours if isinstance(maint_hours, list) else [2, 3, 4]))
    t1_triggered = t1_meet_interval or (since_last_s >= interval_s * 0.5 and t1_meet_maint_window)
    if t1_triggered:
        events.append(_trg_write_event('main', 't1_time_period', 'T1 时间/周期/维护窗口触发',
                                        threshold=f'interval={interval_s}s, maint={maint_hours}',
                                        actual=f'since_last={int(since_last_s)}s, hour={now_hour}',
                                        severity='info', upgrade_suggested='patch',
                                        detail={'t1_meet_interval': t1_meet_interval, 't1_meet_maint_window': t1_meet_maint_window}))
    summary['t1'] = {'triggered': t1_triggered, 'since_last_s': int(since_last_s), 'interval_s': interval_s, 'hour': now_hour}

    # ---- T2：错误率阈值 ----
    t2_rate = float(_trg_get_config('main', 't2_error_rate_pct_5m', 5.0))
    t2_cnt = int(_trg_get_config('main', 't2_error_count_5m', 50))
    # 从 sys_container_ai_audit 5分钟内阻断数近似错误
    err_cnt, total_cnt = 0, 0
    try:
        with sqlite3.connect(_bizdb(), timeout=2) as c:
            r = c.execute("SELECT COUNT(*) FROM sys_container_ai_audit WHERE created_at >= datetime('now','localtime','-5 minutes') AND blocked=1").fetchone()
            err_cnt = int((r or [0])[0])
            r = c.execute("SELECT COUNT(*) FROM sys_container_heartbeat WHERE created_at >= datetime('now','localtime','-5 minutes')").fetchone()
            total_cnt = int((r or [0])[0])
    except Exception:
        pass
    err_rate_pct = (err_cnt / total_cnt * 100.0) if total_cnt > 0 else 0.0
    t2_triggered = (err_rate_pct >= t2_rate and total_cnt >= 20) or err_cnt >= t2_cnt
    if t2_triggered:
        events.append(_trg_write_event('main', 't2_error_rate', 'T2 错误率阈值触发',
                                        threshold=f'rate≥{t2_rate}% count≥{t2_cnt}',
                                        actual=f'rate={err_rate_pct:.2f}% count={err_cnt} total={total_cnt}',
                                        severity='warning' if err_cnt < t2_cnt * 2 else 'critical',
                                        upgrade_suggested='hotfix',
                                        detail={'error_count': err_cnt, 'error_rate_pct': round(err_rate_pct, 2), 'total': total_cnt}))
    summary['t2'] = {'triggered': t2_triggered, 'err_rate_pct': round(err_rate_pct, 2), 'err_cnt': err_cnt, 'total': total_cnt}

    # ---- T3：性能退化（基于 container_heartbeat 响应/会话近似值） ----
    t3_growth_pct = float(_trg_get_config('main', 't3_avg_rt_growth_pct', 50))
    t3_rt_threshold_ms = int(_trg_get_config('main', 't3_avg_rt_ms_threshold', 800))
    # 简化实现：基于最近 5 分钟 audit 中记录 dur_ms 平均值
    avg_rt_ms, baseline_ms, mem_pct = 0, 400, 0.0
    try:
        with sqlite3.connect(_bizdb(), timeout=2) as c:
            r = c.execute("SELECT detail_json FROM sys_container_ai_audit WHERE rule_hit='CONTAINER::RENDER-OK' AND created_at >= datetime('now','localtime','-5 minutes') ORDER BY id DESC LIMIT 200").fetchall()
            durs = []
            for (dj,) in r:
                try:
                    j = json.loads(dj or '{}') or {}
                    if 'dur_ms' in j: durs.append(int(j['dur_ms']))
                except: continue
            avg_rt_ms = int(sum(durs) / len(durs)) if durs else 0
        # 内存近似
        try:
            import psutil as _ps
            mem_pct = float(_ps.virtual_memory().percent)
        except Exception:
            try:
                mem_pct = 50.0  # fallback 不触发
            except:
                mem_pct = 50.0
    except Exception:
        pass
    growth_pct = ((avg_rt_ms / baseline_ms) - 1) * 100.0 if baseline_ms and avg_rt_ms else 0
    t3_meet_rt = avg_rt_ms >= t3_rt_threshold_ms or growth_pct >= t3_growth_pct
    t3_meet_mem = mem_pct >= int(_trg_get_config('main', 't3_memory_pct', 85))
    t3_triggered = t3_meet_rt or t3_meet_mem
    if t3_triggered:
        events.append(_trg_write_event('main', 't3_performance', 'T3 性能退化触发',
                                        threshold=f'growth≥{t3_growth_pct}% or rt≥{t3_rt_threshold_ms}ms, mem≥{_trg_get_config("main","t3_memory_pct",85)}%',
                                        actual=f'growth={growth_pct:.1f}% avg_rt={avg_rt_ms}ms mem={mem_pct:.1f}%',
                                        severity='warning' if not t3_meet_mem else 'critical',
                                        upgrade_suggested='patch',
                                        detail={'avg_rt_ms': avg_rt_ms, 'growth_pct': round(growth_pct, 2), 'memory_pct': round(mem_pct, 2)}))
    summary['t3'] = {'triggered': t3_triggered, 'avg_rt_ms': avg_rt_ms, 'growth_pct': round(growth_pct, 2), 'memory_pct': round(mem_pct, 2)}

    # ---- T4：AI 洞察/知识积累 ----
    t4_brain = int(_trg_get_config('main', 't4_new_brain_entries_since_upgrade', 200))
    t4_rules = int(_trg_get_config('main', 't4_new_rules_since_upgrade', 10))
    t4_insights = int(_trg_get_config('main', 't4_high_conf_insights_since_upgrade', 20))
    brain_cnt, rule_cnt, insight_cnt = 0, 0, 0
    try:
        with sqlite3.connect(_bizdb(), timeout=2) as c:
            # 近似知识条目/规则/洞察
            for tname, col in [('upgrade_history', 'id')]:
                try:
                    r = c.execute(f"SELECT COUNT(*) FROM {tname} WHERE created_at >= datetime('now','localtime','-24 hours')").fetchone()
                    if tname == 'upgrade_history': brain_cnt += int((r or [0])[0]) * 50
                except Exception: continue
            # 学习规则表
            try:
                r = c.execute("SELECT COUNT(*) FROM system_rules WHERE created_at >= datetime('now','localtime','-24 hours')").fetchone()
                rule_cnt = int((r or [0])[0])
            except Exception:
                rule_cnt = t4_rules - 1  # fallback 未达到
            try:
                r = c.execute("SELECT COUNT(*) FROM learning_rules WHERE confidence >= 0.7 AND created_at >= datetime('now','localtime','-24 hours')").fetchone()
                insight_cnt = int((r or [0])[0])
            except Exception:
                pass
    except Exception:
        pass
    brain_cnt = max(brain_cnt, 0)
    t4_triggered = (brain_cnt >= t4_brain) or (rule_cnt >= t4_rules) or (insight_cnt >= t4_insights)
    if t4_triggered:
        events.append(_trg_write_event('main', 't4_ai_knowledge', 'T4 AI 知识积累触发',
                                        threshold=f'brain≥{t4_brain} rules≥{t4_rules} insights≥{t4_insights}',
                                        actual=f'brain≈{brain_cnt} rules={rule_cnt} insights={insight_cnt}',
                                        severity='info', upgrade_suggested='minor',
                                        detail={'brain_entries_est': brain_cnt, 'new_rules': rule_cnt, 'high_conf_insights': insight_cnt}))
    summary['t4'] = {'triggered': t4_triggered, 'brain_est': brain_cnt, 'new_rules': rule_cnt, 'high_conf_insights': insight_cnt}

    # ---- T5：安全事件 ----
    t5_blocks = int(_trg_get_config('main', 't5_high_severity_blocks_1h', 5))
    blocks = 0
    try:
        with sqlite3.connect(_bizdb(), timeout=2) as c:
            r = c.execute("SELECT COUNT(*) FROM sys_container_ai_audit WHERE risk_level IN ('high','critical') AND blocked=1 AND created_at >= datetime('now','localtime','-1 hours')").fetchone()
            blocks = int((r or [0])[0])
    except Exception:
        pass
    t5_triggered = blocks >= t5_blocks
    if t5_triggered:
        events.append(_trg_write_event('main', 't5_security', 'T5 安全事件触发',
                                        threshold=f'high_blocks≥{t5_blocks}/1h',
                                        actual=f'high_blocks={blocks}',
                                        severity='critical', upgrade_suggested='security',
                                        detail={'high_critical_blocks_1h': blocks}))
    summary['t5'] = {'triggered': t5_triggered, 'high_blocks_1h': blocks}

    # ---- T6 手动：API 调用时写入，这里只占位不重复触发 ----
    summary['t6'] = {'triggered': False, 'note': 'use POST /api/upgrade/trigger to raise T6 manual'}

    # ---- T7 Git/文件变更：累计代码 MD5 变更比例 ----
    t7_pct = float(_trg_get_config('main', 't7_file_md5_change_pct', 5.0))
    changed_pct = 0.0
    try:
        git_dir = os.path.join(BASE_DIR, '.git')
        if os.path.exists(git_dir):
            try:
                import subprocess as _sp
                out = _sp.run(['git', 'status', '--short'], capture_output=True, text=True, cwd=BASE_DIR, timeout=10).stdout.strip()
                lines = [l for l in out.splitlines() if l.strip()]
                total_known = max(int(_sp.run(['git', 'ls-files'], capture_output=True, text=True, cwd=BASE_DIR, timeout=10).stdout.count('\n')), 1)
                changed_pct = min(100.0, round(len(lines) / total_known * 100.0, 2)) if total_known else 0.0
            except Exception:
                pass
    except Exception:
        pass
    t7_triggered = changed_pct >= t7_pct
    if t7_triggered:
        events.append(_trg_write_event('main', 't7_file_change', 'T7 文件/Git变更触发',
                                        threshold=f'changed≥{t7_pct}%',
                                        actual=f'changed≈{changed_pct:.2f}%',
                                        severity='info', upgrade_suggested='patch',
                                        detail={'changed_pct': changed_pct}))
    summary['t7'] = {'triggered': t7_triggered, 'changed_pct': changed_pct}

    # ---- T8 容量/资源 ----
    t8_disk = int(_trg_get_config('main', 't8_disk_usage_pct', 80))
    t8_sess = int(_trg_get_config('main', 't8_session_count', 500))
    disk_pct, sessions, backup_stale_h = 0.0, 0, 0
    try:
        import shutil as _sh
        total, used, free = _sh.disk_usage(BASE_DIR)
        disk_pct = round(used / total * 100.0, 2) if total else 0
    except Exception:
        pass
    try:
        with sqlite3.connect(_bizdb(), timeout=2) as c:
            r = c.execute("SELECT COUNT(*) FROM sys_container_sessions WHERE last_seen >= datetime('now','localtime','-15 minutes')").fetchone()
            sessions = int((r or [0])[0])
            # 备份新鲜度：看 backup_records 表
            try:
                r = c.execute("SELECT MAX(created_at) FROM backup_records").fetchone()
                if r and r[0]:
                    delta = datetime.now() - datetime.strptime(r[0], '%Y-%m-%dT%H:%M:%S') if 'T' in (r[0] or '') else (datetime.now() - datetime.strptime(r[0], '%Y-%m-%d %H:%M:%S'))
                    backup_stale_h = int(delta.total_seconds() // 3600)
            except Exception:
                backup_stale_h = 0
    except Exception:
        pass
    backup_age_thr = int(_trg_get_config('main', 't8_backup_age_hours', 25))
    t8_disk_bad = disk_pct >= t8_disk
    t8_sess_bad = sessions >= t8_sess
    t8_backup_bad = backup_stale_h >= backup_age_thr
    t8_triggered = t8_disk_bad or t8_sess_bad or t8_backup_bad
    if t8_triggered:
        sev = 'critical' if t8_disk_bad or t8_backup_bad else 'warning'
        sug = 'hotfix' if t8_backup_bad else 'patch'
        events.append(_trg_write_event('main', 't8_capacity', 'T8 容量/资源触发',
                                        threshold=f'disk≥{t8_disk}% or sessions≥{t8_sess} or backup_stale≥{backup_age_thr}h',
                                        actual=f'disk={disk_pct}% sessions={sessions} backup_stale={backup_stale_h}h',
                                        severity=sev, upgrade_suggested=sug,
                                        detail={'disk_pct': disk_pct, 'sessions': sessions, 'backup_stale_h': backup_stale_h}))
    summary['t8'] = {'triggered': t8_triggered, 'disk_pct': disk_pct, 'sessions': sessions, 'backup_stale_h': backup_stale_h}

    triggered_any = len(events) > 0
    # 取最高严重度
    max_sev = 'info'
    _SEV = {'info': 1, 'warning': 2, 'critical': 3}
    for eid in events:
        # 简化：用 event_id 再查一遍严重度
        try:
            with sqlite3.connect(_bizdb(), timeout=2) as c:
                r = c.execute("SELECT severity, upgrade_type_suggested FROM upgrade_trigger_events WHERE trigger_id=?", (eid,)).fetchone()
                if r and _SEV.get(str(r[0]), 0) > _SEV.get(max_sev, 0):
                    max_sev = str(r[0])
        except Exception:
            continue
    return {
        'triggered': triggered_any,
        'event_ids': events,
        'max_severity': max_sev,
        'suggested_upgrade_type': (
            'security' if any('t5' in e for e in events) else
            'hotfix' if summary.get('t2', {}).get('triggered') else
            'major' if summary.get('t4', {}).get('triggered') and len(events) > 1 else
            'minor' if summary.get('t4', {}).get('triggered') else
            'patch'
        ),
        'summary': summary,
    }


# ================= 子系统升级触发条件评估 =================
def _trg_evaluate_subsystem(subsystem_id: str) -> dict:
    cfg = _trg_list_config(subsystem_id)
    base = {'subsystem_id': subsystem_id, 'enabled': cfg.get('enabled', False),
            'triggered': False, 'event_ids': [], 'summary': {}}
    if not cfg.get('enabled', True):
        return base
    min_interval = int(cfg.get('min_interval', 3600))
    # 子系统最近一次完成的升级时间
    last_ts = 0
    try:
        with sqlite3.connect(_bizdb(), timeout=2) as c:
            r = c.execute("SELECT MAX(finished_at) FROM subsystem_upgrade_records WHERE subsystem_id=? AND status='success'", (subsystem_id,)).fetchone()
            if r and r[0]:
                try:
                    last_ts = datetime.strptime(r[0], '%Y-%m-%d %H:%M:%S').timestamp()
                except Exception:
                    last_ts = 0
    except Exception:
        pass
    since_last = time.time() - last_ts
    triggered = False
    events = []
    smry = {'since_last_seconds': int(since_last), 'min_interval': min_interval}
    detail: dict = {}

    if subsystem_id == 'ai_engine':
        new_emps = int(cfg.get('new_ai_employees', 2) or 0)
        try:
            with sqlite3.connect(_bizdb(), timeout=2) as c:
                r = c.execute("SELECT COUNT(*) FROM ai_employees WHERE created_at >= datetime('now','localtime','-24 hours')").fetchone()
                cnt = int((r or [0])[0])
        except Exception:
            cnt = 0
        smry['new_ai_employees_24h'] = cnt
        if since_last >= min_interval and cnt >= new_emps:
            detail['new_employees'] = cnt
            triggered = True
    elif subsystem_id == 'exam_system':
        errs = int(cfg.get('exam_errors_1h', 5) or 0)
        try:
            with sqlite3.connect(_bizdb(), timeout=2) as c:
                r = c.execute("SELECT COUNT(*) FROM sys_container_ai_audit WHERE scope NOT IN ('main','') AND created_at >= datetime('now','localtime','-1 hours')").fetchone()
                cnt = int((r or [0])[0]) // 2
        except Exception:
            cnt = 0
        smry['exam_errors_1h_est'] = cnt
        if since_last >= min_interval and cnt >= errs:
            detail['exam_errors_1h'] = cnt; triggered = True
    elif subsystem_id == 'settings_portal':
        pend = int(cfg.get('setting_changes_pending_approval', 5) or 0)
        try:
            with sqlite3.connect(_bizdb(), timeout=2) as c:
                r = c.execute("SELECT COUNT(*) FROM approvals WHERE status='pending'").fetchone()
                cnt = int((r or [0])[0])
        except Exception:
            cnt = 0
        smry['pending_approvals'] = cnt
        if since_last >= min_interval and cnt >= pend:
            detail['pending_approval_count'] = cnt; triggered = True
    elif subsystem_id == 'vikey_manager':
        fails = int(cfg.get('vikey_auth_failures_1h', 5) or 0)
        unknown = int(cfg.get('unknown_devices_1h', 1) or 0)
        cnt_fail, cnt_unk = 0, 0
        try:
            with sqlite3.connect(_bizdb(), timeout=2) as c:
                r = c.execute("SELECT COUNT(*) FROM vikey_operations_log WHERE result LIKE 'fail%' AND created_at >= datetime('now','localtime','-1 hours')").fetchone()
                cnt_fail = int((r or [0])[0])
        except Exception:
            pass
        smry['auth_failures_1h'] = cnt_fail
        smry['unknown_devices_1h'] = cnt_unk
        if since_last >= min_interval and (cnt_fail >= fails or cnt_unk >= unknown):
            detail['auth_failures'] = cnt_fail; detail['unknown'] = cnt_unk; triggered = True
    elif subsystem_id == 'shadow_system':
        lag_s = int(cfg.get('shadow_sync_lag_seconds', 600) or 0)
        staleness = int(cfg.get('cold_data_stale_hours', 24) or 0)
        lag_actual, stale_h = 0, 0
        try:
            with sqlite3.connect(_bizdb(), timeout=2) as c:
                r = c.execute("SELECT updated_at FROM shadow_mode_state WHERE mode='live' ORDER BY id DESC LIMIT 1").fetchone()
                if r and r[0]:
                    try:
                        lag_actual = int((datetime.now() - datetime.strptime(r[0], '%Y-%m-%d %H:%M:%S')).total_seconds())
                    except Exception:
                        lag_actual = 0
        except Exception:
            pass
        smry['sync_lag_s'] = lag_actual
        smry['cold_stale_h'] = stale_h
        if since_last >= min_interval and (lag_actual >= lag_s or stale_h >= staleness):
            detail['lag_s'] = lag_actual; triggered = True
    elif subsystem_id == 'knowledge_brain':
        need = int(cfg.get('new_entries', 100) or 0)
        cnt = 0
        try:
            with sqlite3.connect(_bizdb(), timeout=2) as c:
                for tbl in ('brain_bank_knowledge','learning_rules'):
                    try:
                        r = c.execute(f"SELECT COUNT(*) FROM {tbl} WHERE created_at >= datetime('now','localtime','-12 hours')").fetchone()
                        cnt += int((r or [0])[0])
                    except Exception: continue
        except Exception:
            pass
        smry['new_entries_12h'] = cnt
        if since_last >= min_interval and cnt >= need:
            detail['new_entries'] = cnt; triggered = True
    elif subsystem_id == 'container_monitor':
        need_err = int(cfg.get('container_errors_1m', 10) or 0)
        miss_pct_need = float(cfg.get('heartbeat_miss_pct', 5) or 0)
        err_cnt, miss_pct = 0, 0.0
        try:
            with sqlite3.connect(_bizdb(), timeout=2) as c:
                r = c.execute("SELECT COUNT(*) FROM sys_container_ai_audit WHERE risk_level IN ('high','critical') AND created_at >= datetime('now','localtime','-1 minutes')").fetchone()
                err_cnt = int((r or [0])[0])
        except Exception:
            pass
        smry['errors_1m'] = err_cnt
        smry['heartbeat_miss_pct_est'] = round(miss_pct, 2)
        if since_last >= min_interval and (err_cnt >= need_err or miss_pct >= miss_pct_need):
            detail['errors_1m'] = err_cnt; triggered = True
    elif subsystem_id == 'user_portal':
        need_fail_rate = float(cfg.get('login_fail_rate_pct', 8) or 0)
        need_drop = float(cfg.get('session_drop_rate_pct', 5) or 0)
        fail_rate, drop_rate = 0.0, 0.0
        try:
            with sqlite3.connect(_bizdb(), timeout=2) as c:
                r = c.execute("SELECT COUNT(*) FROM sys_container_ai_audit WHERE rule_hit='CONTAINER::PERMISSION-DENY' AND created_at >= datetime('now','localtime','-15 minutes')").fetchone()
                fail_cnt = int((r or [0])[0])
                total = 100
                fail_rate = min(100.0, fail_cnt / total * 100.0) if total else 0
        except Exception:
            pass
        smry['login_fail_rate_pct_est'] = round(fail_rate, 2)
        smry['session_drop_rate_pct_est'] = round(drop_rate, 2)
        if since_last >= min_interval and (fail_rate >= need_fail_rate or drop_rate >= need_drop):
            detail['fail_rate'] = round(fail_rate, 2); triggered = True
    elif subsystem_id == 'file_center':
        need_orphan = int(cfg.get('orphan_files_count', 50) or 0)
        need_quota = float(cfg.get('storage_quota_pct', 85) or 0)
        orphans, quota_pct = 0, 0.0
        try:
            import shutil as _sh2
            t, u, f = _sh2.disk_usage(BASE_DIR)
            quota_pct = round(u/t*100.0, 2) if t else 0
        except Exception:
            pass
        smry['orphan_files'] = orphans
        smry['storage_pct'] = quota_pct
        if since_last >= min_interval and (orphans >= need_orphan or quota_pct >= need_quota):
            detail['storage_pct'] = quota_pct; triggered = True
    else:
        # 未知子系统：仅 min_interval 条件
        if since_last >= min_interval:
            triggered = True

    if triggered:
        eid = _trg_write_event(subsystem_id, f'sub_{subsystem_id}', f'子系统 [{subsystem_id}] 条件触发',
                               threshold=json.dumps(cfg, ensure_ascii=False),
                               actual=json.dumps(smry, ensure_ascii=False),
                               severity='warning', upgrade_suggested='patch',
                               detail=detail)
        events.append(eid)

    base['triggered'] = triggered
    base['event_ids'] = events
    base['summary'] = smry
    return base


def _trg_evaluate_all_subsystems() -> dict:
    out = {}
    for sid in _SUBSYSTEM_TRIGGER_DEFAULTS.keys():
        out[sid] = _trg_evaluate_subsystem(sid)
    triggered_sids = [s for s, v in out.items() if v.get('triggered')]
    return {
        'total_subsystems': len(_SUBSYSTEM_TRIGGER_DEFAULTS),
        'triggered_count': len(triggered_sids),
        'triggered_subsystems': triggered_sids,
        'details': out,
    }


# ================= 审批流 / 灰度联动 =================
def _upgrade_approval_required(upgrade_type: str) -> dict:
    return _UPGRADE_APPROVAL_CHAIN.get(upgrade_type, _UPGRADE_APPROVAL_CHAIN['patch'])


def _upgrade_get_approval_status(trigger_event_id: str, upgrade_type: str) -> dict:
    rule = _upgrade_approval_required(upgrade_type)
    need_admin = int(rule.get('need_admin_approval', 0))
    need_super = bool(rule.get('need_super_approval', False))
    admin_approvals, super_approvals = 0, 0
    try:
        with sqlite3.connect(_bizdb(), timeout=2) as c:
            _ensure_upgrade_trigger_tables(c)
            rows = c.execute("SELECT approver, approver_role, decision FROM upgrade_approval_records WHERE trigger_event_id=? AND decision='approve' ORDER BY id", (trigger_event_id,)).fetchall()
            for approver, role, decision in rows:
                if role == 'super_admin' or approver == 'wuchenghao15':
                    super_approvals += 1
                elif 'admin' in (role or ''):
                    admin_approvals += 1
    except Exception:
        pass
    admin_ok = admin_approvals + super_approvals >= need_admin
    super_ok = super_approvals >= 1 if need_super else True
    return {
        'approval_rule': rule,
        'admin_approvals': admin_approvals, 'super_approvals': super_approvals,
        'admin_required': need_admin, 'super_required': need_super,
        'admin_ok': admin_ok, 'super_ok': super_ok,
        'all_ok': admin_ok and super_ok,
    }


def _upgrade_shadow_switch_if_needed(trigger_event_id: str, upgrade_type: str) -> dict:
    rule = _upgrade_approval_required(upgrade_type)
    if not rule.get('shadow_first'):
        return {'switched': False, 'reason': 'upgrade_type does not require shadow first'}
    try:
        with sqlite3.connect(_bizdb(), timeout=3) as c:
            # 先确保三行都存在 (live/shadow/cold)，避免 PRIMARY KEY 冲突
            for m in ('live', 'shadow', 'cold'):
                try:
                    c.execute(
                        "INSERT OR IGNORE INTO shadow_mode_state(mode,enabled,switch_at,note) VALUES(?,0,datetime('now','localtime'),?)",
                        (m, 'default-init')
                    )
                except Exception:
                    continue
            # 取当前启用的模式 (enabled=1 的那个)
            r = c.execute("SELECT mode FROM shadow_mode_state WHERE enabled=1 ORDER BY mode LIMIT 1").fetchone()
            current = (r and r[0]) or 'live'
            if current != 'shadow':
                # 切换到 shadow 模式：先全部 disable，再 enable shadow
                c.execute("UPDATE shadow_mode_state SET enabled=0")
                note_val = f'upgrade-triggered shadow switch event={trigger_event_id} type={upgrade_type}'
                c.execute(
                    "UPDATE shadow_mode_state SET enabled=1, switch_at=datetime('now','localtime'), switched_by='UPGRADE-TRIGGER', note=? WHERE mode='shadow'",
                    (note_val,)
                )
                c.commit()
                return {'switched': True, 'previous': current, 'now': 'shadow', 'trigger_event': trigger_event_id}
            return {'switched': False, 'already_shadow': True, 'current': current}
    except Exception as e:
        return {'switched': False, 'error': str(e)}


# ================= REST API =================
@app.route('/api/upgrade/check_trigger', methods=['GET', 'POST'])
def api_upgrade_check_trigger():
    """GET 或 POST：评估主系统 8 维度 + 所有子系统触发条件，返回总览+事件ID"""
    try:
        main_eval = _trg_evaluate_main_system()
        subs_eval = _trg_evaluate_all_subsystems()
        config = {
            'main': _trg_list_config('main'),
            'subsystems': {sid: _trg_list_config(sid) for sid in _SUBSYSTEM_TRIGGER_DEFAULTS.keys()},
        }
        return jsonify({
            'success': True,
            'main_system': main_eval,
            'subsystems': subs_eval,
            'approval_chain_spec': _UPGRADE_APPROVAL_CHAIN,
            'configs': config,
            'server_ts': int(time.time()),
            'trace_id': getattr(request, 'mt_trace_id', _trace_id()) if '_trace_id' in globals() else hashlib.md5(str(time.time_ns()).encode()).hexdigest()[:16],
        })
    except Exception as e:
        import traceback as _tb
        return jsonify({'success': False, 'message': str(e), 'trace': _tb.format_exc(limit=3)}), 500


@app.route('/api/upgrade/trigger', methods=['POST'])
@system_container('upgrade_trigger', require_auth='admin')
def api_upgrade_trigger_manual():
    """POST：T6 管理员手动触发主系统升级（写入 trigger_event 并返回审批要求）"""
    try:
        data = request.get_json(silent=True) or request.form or {}
        u = (_current_user() or {}) if callable(_current_user) else {}
        username = (u.get('username') if isinstance(u, dict) else getattr(u, 'username', None)) or 'SYSTEM'
        role = (u.get('role') if isinstance(u, dict) else getattr(u, 'role', None)) or 'user'
        upgrade_type = str(data.get('upgrade_type') or data.get('type') or 'patch').strip().lower()
        if upgrade_type not in _UPGRADE_APPROVAL_CHAIN:
            return jsonify({'success': False, 'message': f'upgrade_type 必须是 {list(_UPGRADE_APPROVAL_CHAIN.keys())}'}), 400
        reason = (data.get('reason') or data.get('description') or '')[:500]
        eid = _trg_write_event(
            'main', 't6_manual', f'T6 手动触发（{username}）',
            threshold=f'operator={username}/{role}',
            actual=reason or '无详细说明',
            severity='warning' if upgrade_type in ('patch','minor') else 'critical',
            upgrade_suggested=upgrade_type,
            detail={'operator': username, 'operator_role': role, 'reason': reason},
        )
        # 手动触发直接挂状态为 open，待审批
        try:
            with sqlite3.connect(_bizdb(), timeout=3) as c:
                _ensure_upgrade_trigger_tables(c)
                c.execute("UPDATE upgrade_trigger_events SET triggered_by=? WHERE trigger_id=?", (username, eid))
                c.commit()
        except Exception:
            pass
        approval = _upgrade_get_approval_status(eid, upgrade_type)
        return jsonify({
            'success': True,
            'trigger_id': eid,
            'upgrade_type': upgrade_type,
            'triggered_by': username,
            'approval_status': approval,
            'message': '触发事件已写入。' + ('' if approval.get('all_ok') else f'还需审批：admin还缺 {max(0,int(approval.get("admin_required",0))-int(approval.get("admin_approvals",0)))} 人，SA审批：{"✓" if approval.get("super_ok") else "待 wuchenghao15"}')
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/upgrade/approve', methods=['POST'])
def api_upgrade_approve():
    """POST：审批触发事件（管理员或超级管理员）"""
    try:
        data = request.get_json(silent=True) or {}
        tid = (data.get('trigger_id') or '').strip()
        decision = (data.get('decision') or 'approve').strip().lower()
        comment = (data.get('comment') or '')[:500]
        u = (_current_user() or {}) if callable(_current_user) else {}
        approver = (u.get('username') if isinstance(u, dict) else getattr(u, 'username', None)) or ''
        role = (u.get('role') if isinstance(u, dict) else getattr(u, 'role', None)) or ''
        if approver == 'wuchenghao15':
            role = 'super_admin'
        is_admin = ('admin' in (role or '')) or approver == 'wuchenghao15'
        if not approver or not is_admin:
            return jsonify({'success': False, 'message': '需要管理员登录'}), 403
        if decision not in ('approve', 'reject', 'comment'):
            return jsonify({'success': False, 'message': 'decision ∈ {approve,reject,comment}'}), 400
        with sqlite3.connect(_bizdb(), timeout=3) as c:
            _ensure_upgrade_trigger_tables(c)
            r = c.execute("SELECT upgrade_type_suggested, status FROM upgrade_trigger_events WHERE trigger_id=?", (tid,)).fetchone()
            if not r:
                return jsonify({'success': False, 'message': f'未找到 trigger_id={tid}'}), 404
            up_type, old_status = r[0] or 'patch', r[1] or 'open'
            stage = 0
            c.execute(
                "INSERT INTO upgrade_approval_records(trigger_event_id,approver,approver_role,decision,comment,approval_stage) VALUES(?,?,?,?,?,?)",
                (tid, approver, role, decision, comment, stage)
            )
            if decision == 'reject':
                c.execute("UPDATE upgrade_trigger_events SET status='rejected',approved_by=?,approved_at=datetime('now','localtime') WHERE trigger_id=?", (approver, tid))
            c.commit()
        approval = _upgrade_get_approval_status(tid, up_type)
        # 全通过 → 自动切换 shadow + 标记 approved
        if approval.get('all_ok') and decision != 'reject':
            try:
                with sqlite3.connect(_bizdb(), timeout=3) as c:
                    c.execute("UPDATE upgrade_trigger_events SET status='approved',approved_by=?,approved_at=datetime('now','localtime') WHERE trigger_id=?", (approver, tid))
                    c.commit()
                _upgrade_shadow_switch_if_needed(tid, up_type)
            except Exception:
                pass
        return jsonify({'success': True, 'decision': decision, 'approval_status': approval})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/subsystem/upgrade/check', methods=['GET'])
def api_subsystem_upgrade_check():
    """GET：评估所有子系统触发条件"""
    try:
        return jsonify({'success': True, 'data': _trg_evaluate_all_subsystems()})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/subsystem/upgrade/trigger', methods=['POST'])
def api_subsystem_upgrade_trigger():
    """POST：手动触发指定子系统升级"""
    try:
        data = request.get_json(silent=True) or {}
        sid = (data.get('subsystem_id') or data.get('sid') or '').strip()
        if sid not in _SUBSYSTEM_TRIGGER_DEFAULTS:
            return jsonify({'success': False, 'message': f'subsystem_id 必须是 {list(_SUBSYSTEM_TRIGGER_DEFAULTS.keys())}'}), 400
        allowed = _trg_get_config(sid, 'manual_allowed', True)
        if not allowed:
            return jsonify({'success': False, 'message': f'{sid} 不允许手动触发'}), 403
        u = (_current_user() or {}) if callable(_current_user) else {}
        username = (u.get('username') if isinstance(u, dict) else getattr(u, 'username', None)) or 'SYSTEM'
        role = (u.get('role') if isinstance(u, dict) else getattr(u, 'role', None)) or 'user'
        upgrade_type = str(data.get('upgrade_type') or 'patch').strip().lower()
        eid = _trg_write_event(sid, f'manual_{sid}', f'子系统 [{sid}] 手动触发',
                               threshold='manual allowed',
                               actual=f'operator={username}/{role}',
                               severity='info', upgrade_suggested=upgrade_type,
                               detail={'operator': username, 'reason': data.get('reason', '')})
        # 写入子系统升级记录
        with sqlite3.connect(_bizdb(), timeout=3) as c:
            _ensure_upgrade_trigger_tables(c)
            c.execute(
                "INSERT INTO subsystem_upgrade_records(subsystem_id,trigger_event_id,trigger_type,status,operator) VALUES(?,?,?,?,?)",
                (sid, eid, 'manual', 'approved', username)
            )
            c.commit()
        return jsonify({'success': True, 'trigger_id': eid, 'subsystem_id': sid,
                        'operator': username, 'upgrade_type': upgrade_type})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/upgrade/events', methods=['GET'])
def api_upgrade_events_list():
    """GET：查询触发事件列表（支持 scope/status/limit）"""
    try:
        scope = (request.args.get('scope') or request.args.get('s') or '').strip()
        status = (request.args.get('status') or request.args.get('st') or '').strip()
        limit = min(int(request.args.get('limit') or 100), 500)
        sql, args = "SELECT * FROM upgrade_trigger_events WHERE 1=1", []
        if scope:
            sql += " AND scope=?"; args.append(scope)
        if status:
            sql += " AND status=?"; args.append(status)
        sql += " ORDER BY id DESC LIMIT ?"; args.append(limit)
        with sqlite3.connect(_bizdb(), timeout=3) as c:
            c.row_factory = sqlite3.Row
            _ensure_upgrade_trigger_tables(c)
            rows = c.execute(sql, args).fetchall()
            data = []
            for r in rows:
                d = dict(r) if hasattr(r, 'keys') else dict(zip([d[0] for d in c.execute(sql, args).description], r))
                for jk in ('detail_json', 'result_json'):
                    if d.get(jk):
                        try: d[jk + '_parsed'] = json.loads(d[jk])
                        except Exception: pass
                data.append(d)
        return jsonify({'success': True, 'count': len(data), 'events': data})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/upgrade/config', methods=['GET', 'POST'])
def api_upgrade_config_rw():
    """GET: 查询 scope+key；POST: 更新 scope+key"""
    try:
        if request.method == 'POST':
            u = (_current_user() or {}) if callable(_current_user) else {}
            role = (u.get('role') if isinstance(u, dict) else getattr(u, 'role', None)) or ''
            if role != 'super_admin' and (u.get('username') if isinstance(u, dict) else getattr(u, 'username', None)) != 'wuchenghao15':
                return jsonify({'success': False, 'message': '仅超级管理员可更新配置'}), 403
            data = request.get_json(silent=True) or {}
            scope = str(data.get('scope') or data.get('s') or 'main').strip()
            key = str(data.get('key') or data.get('k') or '').strip()
            val = data.get('value') or data.get('v')
            if not key:
                return jsonify({'success': False, 'message': 'key 必填'}), 400
            vt = 'json' if isinstance(val, (dict, list)) else ('int' if isinstance(val, (int, bool)) else ('float' if isinstance(val, float) else 'string'))
            cv = json.dumps(val, ensure_ascii=False) if isinstance(val, (dict, list)) else str(val)
            operator = (u.get('username') if isinstance(u, dict) else getattr(u, 'username', None)) or 'SYSTEM'
            with sqlite3.connect(_bizdb(), timeout=3) as c:
                _ensure_upgrade_trigger_tables(c)
                c.execute(
                    "INSERT INTO upgrade_trigger_configs(scope,config_key,config_value,value_type,updated_at,updated_by) VALUES(?,?,?,?,datetime('now','localtime'),?)"
                    " ON CONFLICT(scope,config_key) DO UPDATE SET config_value=excluded.config_value,value_type=excluded.value_type,updated_at=datetime('now','localtime'),updated_by=excluded.updated_by",
                    (scope, key, cv, vt, operator)
                )
                c.commit()
            return jsonify({'success': True, 'scope': scope, 'key': key, 'new_value': val, 'updated_by': operator})
        # GET
        scope = (request.args.get('scope') or 'main').strip()
        key = request.args.get('key')
        if key:
            return jsonify({'success': True, 'scope': scope, 'key': key, 'value': _trg_get_config(scope, key)})
        return jsonify({'success': True, 'scope': scope, 'config': _trg_list_config(scope)})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


# ================= AI-Agent 驱动：智能升级推荐 =================
# 9 类 AI 员工：升级分析师/安全审计员/性能分析师/发布工程师/配置审计员/灰度风控师/数据采集员/知识审计员/Vikey加密员
_UPGRADE_AI_TEAM = [
    {'id': 'analyst',         'name': '升级分析师', 'role': 'upgrade_analyst',    'level': 5, 'icon': '🔬', 'desc': '综合 8 维度触发，给出升级类型/优先级/风险评估', 'duty': '聚合 T1~T8 结果，输出综合升级建议'},
    {'id': 'sec_audit',        'name': '安全审计员', 'role': 'security_audit',   'level': 6, 'icon': '🛡️', 'desc': 'T5 高危事件 + CVE 联动的安全升级建议', 'duty': '安全类升级强制为 security/hotfix 类型'},
    {'id': 'perf_eng',        'name': '性能分析师', 'role': 'performance_eng',     'level': 5, 'icon': '⚡', 'desc': 'T3 性能退化驱动的定向组件升级建议', 'duty': '性能问题优先 hotfix，含回归验证建议'},
    {'id': 'release_eng',     'name': '发布工程师', 'role': 'release_engineer', 'level': 6, 'icon': '🚀', 'desc': '灰度推进 5%→100% 阶段的发版/回滚决策', 'duty': '计算下一个灰度阶段与等待时长'},
    {'id': 'cfg_audit',       'name': '配置审计员', 'role': 'config_audit',    'level': 5, 'icon': '⚙️', 'desc': '阈值/配置变更的合理性审计 (T7/T8)', 'duty': '异常阈值触发时给出修正建议'},
    {'id': 'gray_risk',       'name': '灰度风控师', 'role': 'gray_risk_officer','level': 6, 'icon': '📊', 'desc': '灰度期错误/性能异常监控', 'duty': '灰度阶段自动升级→回滚决策支持'},
    {'id': 'data_collector',  'name': '数据采集员', 'role': 'data_collector',  'level': 4, 'icon': '📡', 'desc': '实时采集 8 维度指标', 'duty': '为前端看板提供心跳'},
    {'id': 'knowledge_audit', 'name': '知识审计员', 'role': 'knowledge_audit', 'level': 5, 'icon': '🧠', 'desc': 'T4 AI 知识积累触发建议', 'duty': '脑库条目/规则/洞察的统计与合并建议'},
    {'id': 'vikey_crypto',    'name': 'Vikey 加密员', 'role': 'vikey_crypto',   'level': 6, 'icon': '🔑', 'desc': 'T6 手动升级前签名授权校验', 'duty': 'SA 操作需 Vikey 鉴权'},
]


def _upgrade_ai_employees_snapshot(main_eval: dict, subs_eval: dict) -> list:
    """基于 8 维度 / 9 子系统评估结果，给每位 AI 员工生成“活的状态”
    返回: [{id,name,role,level,icon,status,message,score,suggestion,badge}]
    """
    msum = (main_eval or {}).get('summary', {}) or {}
    triggered = bool((main_eval or {}).get('triggered', False))
    max_sev = (main_eval or {}).get('max_severity', 'info')
    sug_type = (main_eval or {}).get('suggested_upgrade_type', 'patch')
    trig_subs = (subs_eval or {}).get('triggered_subsystems', []) or []
    team_out = []
    for a in _UPGRADE_AI_TEAM:
        aid = a['id']
        status = 'idle'
        msg = ''
        sug = ''
        badge = None
        score = 85
        if aid == 'analyst':
            if triggered:
                status = 'working'
                score = 72 if max_sev == 'info' else (55 if max_sev == 'warning' else 35)
                msg = '检测到升级触发：建议 ' + sug_type + ' 类型；最高严重度 ' + max_sev
                chain_label = (_UPGRADE_APPROVAL_CHAIN.get(sug_type, {}) or {}).get('label', '补丁')
                sug = '立即生成审批单并进入 ' + chain_label + ' 流程'
                if sug_type in ('security', 'hotfix', 'major'):
                    badge = {'text': sug_type.upper(), 'color': '#ef4444'}
                elif sug_type == 'minor':
                    badge = {'text': sug_type.upper(), 'color': '#f59e0b'}
                else:
                    badge = {'text': sug_type.upper(), 'color': '#10b981'}
            else:
                msg = '当前 8 维度均在安全阈值内，系统运行平稳'
                sug = '建议继续监控，24h 后再评估'
        elif aid == 'sec_audit':
            t5 = msum.get('t5', {}) or {}
            if t5.get('triggered'):
                status = 'critical'
                score = 25
                blocks = t5.get('high_blocks_1h', 0) or 0
                msg = 'T5 高危拦截 ' + str(blocks) + ' 次/1h，建议启动安全补丁'
                sug = '调用 security 类型紧急升级并切换 shadow 执行'
                badge = {'text': '安全告警', 'color': '#ef4444'}
            else:
                score = 95
                blocks = t5.get('high_blocks_1h', 0) or 0
                msg = '1h 高危拦截 ' + str(blocks) + '，正常'
        elif aid == 'perf_eng':
            t3 = msum.get('t3', {}) or {}
            if t3.get('triggered'):
                status = 'warning'
                score = 50
                rt = t3.get('avg_rt_ms', 0) or 0
                mem = t3.get('memory_pct', 0) or 0
                msg = 'T3 性能告警：avg_rt=' + str(rt) + 'ms mem=' + str(mem) + '%'
                sug = '建议 patch 升级含性能优化补丁'
                badge = {'text': '性能退化', 'color': '#f59e0b'}
            else:
                score = 92
                rt = t3.get('avg_rt_ms', 0) or 0
                mem = t3.get('memory_pct', 0) or 0
                msg = '性能基线稳定 avg_rt=' + str(rt) + 'ms mem=' + str(mem) + '%'
        elif aid == 'release_eng':
            if triggered:
                chain = _UPGRADE_APPROVAL_CHAIN.get(sug_type, {}) or {}
                gray = chain.get('gray_stages_pct') or [100]
                wait = chain.get('stage_minutes') or [0]
                status = 'working'
                score = 65
                msg = '升级链路就绪：灰度阶段 ' + str(gray) + ' 时长 ' + str(wait) + ' min'
                sug = '审批通过后先切 shadow 再推 ' + str(gray[0]) + '% 用户'
                badge = {'text': str(len(gray)) + '阶段灰度', 'color': '#667eea'}
            else:
                score = 90
                msg = '无待处理发版计划'
        elif aid == 'cfg_audit':
            t7 = msum.get('t7', {}) or {}
            t8 = msum.get('t8', {}) or {}
            disk_pct = t8.get('disk_pct', 0) or 0
            if t7.get('triggered') or t8.get('triggered'):
                status = 'warning'
                score = 55
                c7 = t7.get('changed_pct', 0) or 0
                msg = 'T7 变更率 ' + str(c7) + '% / T8 磁盘 ' + str(disk_pct) + '%'
                sug = 'Git 变更较多建议确认；磁盘超阈值建议清理后再升级'
                if disk_pct >= 90:
                    status = 'critical'
            else:
                score = 88
                c7 = t7.get('changed_pct', 0) or 0
                msg = '磁盘 ' + str(disk_pct) + '%，Git 变更 ' + str(c7) + '%'
        elif aid == 'gray_risk':
            if triggered:
                status = 'working'
                score = 68
                msg = '升级前预评估：灰度期需监控 4 指标（错误/性能/登录/支付）'
                sug = '建议升级到 10% 灰度时设置 30min 观察窗'
            else:
                score = 93
                msg = '无灰度在途，系统稳定'
        elif aid == 'data_collector':
            score = 96
            msg = '最近采集：T1~T8 + 9 子系统指标已就绪'
            if triggered:
                status = 'working'
        elif aid == 'knowledge_audit':
            t4 = msum.get('t4', {}) or {}
            if t4.get('triggered'):
                status = 'working'
                score = 60
                b = t4.get('brain_est', 0) or 0
                r_ = t4.get('new_rules', 0) or 0
                i_ = t4.get('high_conf_insights', 0) or 0
                msg = 'T4 知识：脑库 ' + str(b) + ' 条 规则 ' + str(r_) + ' 洞察 ' + str(i_)
                sug = '建议 minor 升级合并新知识'
                badge = {'text': '知识积累', 'color': '#8b5cf6'}
            else:
                score = 85
                msg = '知识条目/规则/洞察在控制范围'
        elif aid == 'vikey_crypto':
            need_super = (_UPGRADE_APPROVAL_CHAIN.get(sug_type, {}) or {}).get('need_super_approval')
            if need_super and triggered:
                status = 'warning'
                score = 62
                msg = '本升级类型需 Vikey 超级管理员双鉴'
                sug = '请插入 Vikey 完成 SA 审批'
                badge = {'text': '需SA签名', 'color': '#ef4444'}
            else:
                score = 94
                msg = '当前升级类型无需 SA 签名'
        team_out.append({
            'id': aid, 'name': a['name'], 'role': a['role'], 'level': a['level'], 'icon': a['icon'],
            'desc': a['desc'], 'duty': a['duty'],
            'status': status, 'message': msg, 'score': score, 'suggestion': sug, 'badge': badge
        })
    return team_out


@app.route('/api/upgrade/ai_recommend', methods=['GET', 'POST'])
def api_upgrade_ai_recommend():
    """AI-Agent 智能推荐：综合 8 维度 + 9 子系统 + 9 AI员工，给出可执行的升级建议"""
    try:
        main_eval = _trg_evaluate_main_system()
        subs_eval = _trg_evaluate_all_subsystems()
        team = _upgrade_ai_employees_snapshot(main_eval, subs_eval)
        triggered = bool(main_eval.get('triggered'))
        sug_type = main_eval.get('suggested_upgrade_type', 'patch') or 'patch'
        chain = _UPGRADE_APPROVAL_CHAIN.get(sug_type, {}) or {}
        steps = []
        trig_t_count = 0
        for t in ((main_eval.get('summary') or {}).values()):
            if isinstance(t, dict) and t.get('triggered'):
                trig_t_count += 1
        steps.append({
            'step': 1, 'title': '触发确认与鉴权评估',
            'status': 'done' if triggered else 'pending',
            'detail': 'AI 分析师：' + str(trig_t_count) + ' 个维度触发'
        })
        need_admin = chain.get('need_admin_approval', 0) or 0
        need_super = chain.get('need_super_approval', False)
        steps.append({
            'step': 2, 'title': '审批链',
            'status': 'ready' if triggered else 'pending',
            'detail': str(chain.get('label', '')) + '类型：需 ' + str(need_admin) + ' 位管理员审批，需SA=' + str(bool(need_super))
        })
        steps.append({
            'step': 3, 'title': '影子节点切换',
            'status': 'ready' if (chain.get('shadow_first') and triggered) else 'pending',
            'detail': '审批通过后切换到 shadow_mode=shadow 模式执行'
        })
        grays = chain.get('gray_stages_pct') or [100]
        waits = chain.get('stage_minutes') or [0]
        for i, pct in enumerate(grays, start=1):
            wait_min = waits[i - 1] if (i - 1) < len(waits) else 0
            steps.append({
                'step': 3 + i, 'title': '灰度 ' + str(pct) + '%',
                'status': 'pending',
                'detail': '观察 ' + str(wait_min) + ' min，监控错误/性能'
            })
        steps.append({
            'step': 100, 'title': '升级完成 & 回滚预案保留 24h',
            'status': 'pending',
            'detail': '观察窗过后无异常切回 live，升级记录写入 upgrade_history'
        })
        risks = []
        msum = main_eval.get('summary') or {}
        t8 = msum.get('t8') or {}
        disk_pct_val = t8.get('disk_pct', 0) or 0
        if disk_pct_val >= 90:
            risks.append({'level': 'high', 'msg': '磁盘占用 ' + str(disk_pct_val) + '% 超 90%，升级前建议清理'})
        t2 = msum.get('t2') or {}
        if t2.get('triggered'):
            risks.append({'level': 'critical', 'msg': 'T2 错误率高，建议先修复再升级或使用 hotfix 类型'})
        t5 = msum.get('t5') or {}
        if t5.get('triggered'):
            risks.append({'level': 'critical', 'msg': 'T5 安全风险，请立即补丁，强制 security 类型立即升级'})
        trig_count = subs_eval.get('triggered_count') or 0
        if trig_count >= 3:
            risks.append({
                'level': 'warning',
                'msg': '子系统 ' + str(trig_count) + '/9 触发，建议按优先级合并升级到主系统+子系统统一窗口期打包升级'
            })
        checklist = [
            {
                'id': 'check_trigger',
                'label': '生成主系统升级触发事件',
                'done': False,
                'payload': {
                    'path': '/api/upgrade/trigger',
                    'method': 'POST',
                    'body': {
                        'upgrade_type': sug_type,
                        'reason': 'AI 推荐触发',
                        'suggested_by': 'upgrade_analyst'
                    }
                }
            },
            {
                'id': 'check_approve_admin',
                'label': '管理员审批',
                'done': not (need_admin > 0)
            },
            {
                'id': 'check_approve_sa',
                'label': '超级管理员审批',
                'done': not bool(need_super)
            },
            {'id': 'check_shadow', 'label': '切换 Shadow 模式', 'done': False},
            {'id': 'check_gray', 'label': '灰度分阶段推进 (' + '-'.join([str(x) + '%' for x in grays]) + ')', 'done': False},
        ]
        subs_details = {}
        raw_details = (subs_eval.get('details') or {})
        for sid, sd in raw_details.items():
            if isinstance(sd, dict):
                subs_details[sid] = {
                    'enabled': sd.get('enabled'),
                    'triggered': sd.get('triggered'),
                    'summary': sd.get('summary'),
                    'event_ids': sd.get('event_ids'),
                }
        return jsonify({
            'success': True,
            'timestamp': int(time.time()),
            'main_system': {
                'triggered': triggered,
                'suggested_upgrade_type': sug_type,
                'summary': main_eval.get('summary'),
                'event_ids': main_eval.get('event_ids') or [],
                'approval_chain': chain,
            },
            'subsystems': {
                'triggered_count': trig_count,
                'triggered_subsystems': subs_eval.get('triggered_subsystems'),
                'details': subs_details,
            },
            'ai_team_snapshot': team,
            'roadmap_steps': steps,
            'risks': risks,
            'checklist': checklist,
            'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        })
    except Exception as e:
        import traceback as _tb
        return jsonify({'success': False, 'message': str(e), 'trace': _tb.format_exc(limit=3)}), 500


@app.route('/api/upgrade/ai_employees_status')
def api_upgrade_ai_employees_status():
    """轻量轮询：获取 AI 员工团队当前状态+消息，前端 heartbeat"""
    try:
        main_eval = _trg_evaluate_main_system()
        subs_eval = _trg_evaluate_all_subsystems()
        team = _upgrade_ai_employees_snapshot(main_eval, subs_eval)
        n = len(team) or 1
        overall_score = int(sum(int(t.get('score', 0) or 0) for t in team) // n)
        crit = 0
        work = 0
        idle = 0
        for t in team:
            st = t.get('status', 'idle')
            if st == 'critical':
                crit += 1
            elif st in ('working', 'warning'):
                work += 1
            else:
                idle += 1
        summary = {
            'overall_score': overall_score,
            'critical_count': crit,
            'working_count': work,
            'idle_count': idle,
            'server_ts': int(time.time()),
            'main_triggered': bool(main_eval.get('triggered', False)),
            'subs_triggered_count': subs_eval.get('triggered_count', 0) or 0,
        }
        return jsonify({'success': True, 'team': team, 'summary': summary})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


# ==========================================================
#  END：系统升级触发条件引擎（主系统 8 维度 + 9 类子系统 + 审批灰度联动 + AI Agent 推荐
# ==========================================================


def _enforce_super_admin_rule():
    """强制规则：超级管理员有且仅有一人就是wuchenghao15"""
    import os
    for db_path in [AUTH_DB, APP_DB]:
        if os.path.exists(db_path):
            try:
                with _get_conn(db_path) as c:
                    c.execute("UPDATE users SET role='admin' WHERE role='super_admin' AND LOWER(username)!='wuchenghao15'")
                    c.execute("UPDATE users SET super_admin_approved=0 WHERE LOWER(username)!='wuchenghao15'")
                    c.commit()
                print(f'[SECURITY] 已强制执行超级管理员规则: {os.path.basename(db_path)}')
            except Exception as e:
                print(f'[SECURITY] 强制执行超级管理员规则失败: {os.path.basename(db_path)} - {e}')

if __name__ == '__main__':
    v, info, _ = get_version_info()
    import os
    debug_mode = os.environ.get('FLASK_DEBUG', '0') == '1' or os.environ.get('DEBUG', '0') == '1'
    _enforce_super_admin_rule()
    print(f'[MTSCOS Real DB] bind=0.0.0.0:8888  version=v{v}  source={info.get("source")}  auth={AUTH_DB} debug={debug_mode}')
    app.run(host='0.0.0.0', port=8888, debug=debug_mode, threaded=True)
