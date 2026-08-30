"""arduino_session_routes — Arduino 设备热插拔自动行为规范 API

遵循规则: 系统操作规范.md §13 (v1.2.0)
  - §13.1 设备插入自动跳转 (前端轮询 /api/arduino/events/poll 获取 insert 事件)
  - §13.2 临时用户登录弹窗 (前端根据 session 判断是否弹窗, 后端 /api/arduino/session/temp-login 验证)
  - §13.3 设备拔出自动退出 (前端轮询获取 remove 事件)
  - §13.4 未保存工作保存提示 (前端检测变更, POST /api/arduino/session/save)
  - §13.5 用户使用痕迹持久化 (POST /api/arduino/session/trace)
  - §13.6 自动载入继续编译 (GET /api/arduino/session/load)
  - §13.8 引擎事件队列 (GET /api/arduino/events/poll + POST /api/arduino/events/ack)

设计: 采用 SQLite 事件队列替代 WebSocket (与现有架构一致, 零额外依赖)
"""
from __future__ import annotations

import json
import os
import sys
import uuid
from datetime import datetime

from flask import Blueprint, jsonify, render_template, request, session

from ._governance_helpers import (
    _check_login, _current_safe_user, _fail, _get_db_path, _ok, _query, _query_one,
)

# 引擎路径 (用于调用 DAO 函数)
_ENGINE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'engines')
if _ENGINE_DIR not in sys.path:
    sys.path.insert(0, _ENGINE_DIR)

import ai_arduino_detect_engine as _detect  # noqa: E402

arduino_bp = Blueprint('arduino_session', __name__)


def _check_arduino_api_permission():
    """Arduino SA 守卫 · 用户权限.md 硬条款：
    仅 wuchenghao15 (SA) 且 VIKEY + SZU100 双密钥同时在线可访问 /admin_app/arduino_ide 及 /api/arduino/* 。
    返回 (allow: bool, response: Optional[Response])；allow=False 时调用方直接返回 response。
    违反统一 403 + 错误码 ARDUINO_SA_ONLY。"""
    from flask import jsonify, request
    username = (session.get('username') or '').strip()
    role_canonical = (session.get('role_canonical') or '').strip()
    is_sa = (username.lower() == 'wuchenghao15') or (role_canonical.lower() == 'super_admin')
    # ---- 审计落库准备 ----
    extra = {
        'ip': request.remote_addr,
        'ua': request.headers.get('User-Agent','')[:300],
        'session_id': session.sid if getattr(session, 'sid', None) else session.get('_session_id',''),
        'path': request.path,
        'method': request.method,
    }
    def _write_audit(severity, message, **kwargs):
        try:
            from app.middlewares.vikey_enforcement_middleware import VikeyEnforcementMiddleware as V
            V._log_automation_console(
                'arduino_sa_guard', message, severity=severity,
                extra=dict(extra, **kwargs))
        except Exception:
            pass
    if not is_sa:
        _write_audit('warning', 'ARDUINO_SA_ONLY: 非SA角色访问Arduino被拒',
                     username=username, role=role_canonical)
        return False, (jsonify({
            'success': False,
            'error': '仅超级管理员(wuchenghao15)可访问 Arduino 管理接口与页面',
            'error_code': 'ARDUINO_SA_ONLY',
            'status_code': 403,
        }), 403)
    # ---- 双密钥 AND ----
    try:
        from app.middlewares.vikey_enforcement_middleware import vikey_enforcement
        dual = vikey_enforcement.get_dual_hardware_status(
            username=username, role=role_canonical,
            ip=extra.get('ip'), ua=extra.get('ua'), session_id=extra.get('session_id'))
    except Exception as e:
        _write_audit('critical', f'ARDUINO_SA_ONLY: 双密钥检测异常: {e}',
                     username=username, role=role_canonical)
        return False, (jsonify({
            'success': False,
            'error': 'Arduino 访问：双密钥检测异常，请重新插入 VIKEY + SZU100',
            'error_code': 'ARDUINO_SA_ONLY',
            'status_code': 403,
        }), 403)
    if not dual.get('both_authenticated'):
        reason = []
        if not (dual.get('vikey') or {}).get('present'):
            reason.append('未检测到 VIKEY 加密狗')
        elif not (dual.get('vikey') or {}).get('sa_bound_ok'):
            reason.append('VIKEY 未绑定超级管理员')
        if not (dual.get('szu100') or {}).get('present'):
            reason.append('未检测到 SZU100 专用U盘')
        elif not (dual.get('szu100') or {}).get('is_authentic'):
            reason.append('SZU100 正版校验失败（疑似伪造改名U盘）')
        if not reason:
            reason.append('双密钥未同时通过认证')
        _write_audit('critical', 'ARDUINO_SA_ONLY: SA用户双密钥未同时通过',
                     username=username, role=role_canonical, reason='; '.join(reason))
        return False, (jsonify({
            'success': False,
            'error': 'Arduino 需要同时插入 VIKEY 加密狗 和 SZU100 专用U盘：' + '; '.join(reason),
            'error_code': 'ARDUINO_SA_ONLY',
            'reason': '; '.join(reason),
            'vikey_status': (dual.get('vikey') or {}).get('status'),
            'szu100_status': (dual.get('szu100') or {}).get('auth_status'),
            'status_code': 403,
        }), 403)
    _write_audit('info', 'ARDUINO_SA_ONLY: 访问允许 (双密钥)',
                 username=username, role=role_canonical)
    return True, None


@arduino_bp.before_request
def _arduino_sa_only_guard():
    """路由级 before_request 守卫：/admin_app/arduino_ide + /api/arduino/* 统一走 _check_arduino_api_permission
    仅 temp-login (§13.2 临时登录弹窗) 放行 login_required 级别。"""
    path = (request.path or '').lower()
    is_arduino_route = (
        path.startswith('/api/arduino/')
        or path == '/api/arduino'
        or '/admin_app/arduino_ide' in path
    )
    if not is_arduino_route:
        return None
    if path.endswith('/session/temp-login') or path.endswith('/events/poll'):
        # §13.1 登录弹窗 + 轮询公共接口：保持 _check_login 原先未登录即可访问
        return None
    allowed, resp = _check_arduino_api_permission()
    if not allowed:
        return resp
    return None


# ============================================================
# §13.2 临时用户登录验证 (无 session 时弹窗登录走此 API)
# ============================================================
@arduino_bp.route('/api/arduino/session/temp-login', methods=['POST'])
def arduino_temp_login():
    """Arduino 临时登录验证 (走 @system_container 等价校验, 禁止绕过)

    前端弹窗提交用户名+密码, 后端验证后写入 session, 并触发设备载入流程
    """
    data = request.get_json(silent=True) or {}
    username = (data.get('username') or '').strip()
    password = (data.get('password') or '').strip()
    if not username or not password:
        return _fail('用户名和密码不能为空', 400)

    # 复用 server_real_db 的登录校验逻辑 (禁止绕过 @system_container)
    try:
        import server_real_db as _srd
        ok = _srd._verify_user_credentials(username, password)  # type: ignore[attr-defined]
    except AttributeError:
        # 回退: 直接查 users 表
        ok = _verify_user_fallback(username, password)
    except Exception:
        ok = _verify_user_fallback(username, password)

    if not ok:
        return _fail('用户名或密码错误', 401)

    # 写入 session (与主登录流程一致的最小字段集)
    user = _query_one("SELECT id, username, role_canonical FROM users WHERE username=?", (username,))
    if not user:
        return _fail('用户不存在', 404)
    session['logged_in'] = True
    session['username'] = user.get('username', username)
    session['user_id'] = user.get('id')
    session['role_canonical'] = user.get('role_canonical', 'user')
    session.permanent = False  # 临时会话, 浏览器关闭即失效

    return _ok({
        'username': user.get('username', username),
        'user_id': user.get('id'),
        'role': user.get('role_canonical', 'user'),
        'message': '临时登录成功, 即将进入 Arduino 编译系统',
    })


def _verify_user_fallback(username: str, password: str) -> bool:
    """回退密码校验 (pbkdf2/简单hash, 与 users 表一致)"""
    import hashlib
    import hmac
    row = _query_one("SELECT password_hash FROM users WHERE username=?", (username,))
    if not row:
        return False
    stored = row.get('password_hash', '') or ''
    # 兼容 pbkdf2_sha256$... 格式
    if stored.startswith('pbkdf2_sha256$'):
        parts = stored.split('$')
        if len(parts) == 4:
            _, salt, iterations, h = parts
            try:
                dk = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), int(iterations))
                return hmac.compare_digest(dk.hex(), h)
            except Exception:
                return False
    # 兼容裸 sha256
    return hmac.compare_digest(hashlib.sha256(password.encode()).hexdigest(), stored)


# ============================================================
# §13.1/§13.3 设备事件轮询 (前端每 2s 调用一次)
# ============================================================
@arduino_bp.route('/api/arduino/events/poll')
def arduino_events_poll():
    """轮询设备插入/拔出事件 (替代 WebSocket, 零依赖)

    返回: { events: [{ event_id, event_type, device_vid_pid, board_model, serial_port, payload }] }
    """
    ok, u, err = _check_login()
    if not ok:
        # 未登录时也允许轮询 (用于触发登录弹窗), 但不返回敏感数据
        events = _detect.get_pending_events(limit=5)
        return jsonify({'success': True, 'logged_in': False, 'events': events})
    events = _detect.get_pending_events(limit=10)
    return _ok({'events': events, 'logged_in': True})


@arduino_bp.route('/api/arduino/events/ack', methods=['POST'])
def arduino_events_ack():
    """确认事件已处理 (前端跳转/退出完成后调用)"""
    data = request.get_json(silent=True) or {}
    event_id = (data.get('event_id') or '').strip()
    if not event_id:
        return _fail('event_id 不能为空', 400)
    ok = _detect.ack_event(event_id)
    return _ok({'acked': ok})


# ============================================================
# §13.6 载入用户上次会话
# ============================================================
@arduino_bp.route('/api/arduino/session/load')
def arduino_session_load():
    """载入用户上次 Arduino 编译会话 (按 device_vid_pid 精确匹配)"""
    ok, u, err = _check_login()
    if not ok:
        return _fail('未登录', 401)
    user_id = str(u.get('user_id') or u.get('username') or '')
    device_vid_pid = request.args.get('device_vid_pid', '').strip() or None
    sess = _detect.load_user_session(user_id, device_vid_pid)
    if not sess:
        return _ok({'session': None, 'message': '无历史会话, 开始新编译'})
    # 解析 JSON 字段
    try:
        sess['config'] = json.loads(sess.get('config_json') or '{}')
    except Exception:
        sess['config'] = {}
    try:
        sess['usage_trace'] = json.loads(sess.get('usage_trace_json') or '[]')
    except Exception:
        sess['usage_trace'] = []
    try:
        sess['edit_history'] = json.loads(sess.get('edit_history_json') or '[]')
    except Exception:
        sess['edit_history'] = []
    return _ok({'session': sess, 'message': '已恢复上次工作, 继续编译'})


# ============================================================
# §13.4/§13.5 保存用户会话 (手动保存 + 自动保存)
# ============================================================
@arduino_bp.route('/api/arduino/session/save', methods=['POST'])
def arduino_session_save():
    """保存用户 Arduino 编译会话 (代码/配置/痕迹/编辑历史)

    前端调用场景:
      - 用户点击保存按钮 (auto_saved=0)
      - 每60秒自动保存 (auto_saved=1)
      - 设备拔出提示保存 (auto_saved=0)
    """
    ok, u, err = _check_login()
    if not ok:
        return _fail('未登录', 401)
    data = request.get_json(silent=True) or {}
    user_id = str(u.get('user_id') or u.get('username') or '')
    username = u.get('username') or 'unknown'
    device_vid_pid = (data.get('device_vid_pid') or '').strip()
    board_model = (data.get('board_model') or '').strip()
    code_content = data.get('code_content', '')
    code_language = data.get('code_language', 'cpp')
    config_json = data.get('config_json', '{}')
    usage_trace_json = data.get('usage_trace_json', '[]')
    edit_history_json = data.get('edit_history_json', '[]')
    auto_saved = int(data.get('auto_saved', 0))
    session_id = data.get('session_id')  # 可选, 有则更新

    if not device_vid_pid:
        return _fail('device_vid_pid 不能为空', 400)

    sid = _detect.save_user_session(
        user_id=user_id, username=username, device_vid_pid=device_vid_pid,
        board_model=board_model, code_content=code_content,
        code_language=code_language, config_json=config_json,
        usage_trace_json=usage_trace_json, edit_history_json=edit_history_json,
        auto_saved=auto_saved, session_id=session_id,
    )
    return _ok({'session_id': sid, 'message': '保存成功'})


# ============================================================
# §13.5 追加使用痕迹记录
# ============================================================
@arduino_bp.route('/api/arduino/session/trace', methods=['POST'])
def arduino_session_trace():
    """追加使用痕迹记录 (编译/上传/调试/清除等操作序列)"""
    ok, u, err = _check_login()
    if not ok:
        return _fail('未登录', 401)
    data = request.get_json(silent=True) or {}
    session_id = (data.get('session_id') or '').strip()
    if not session_id:
        return _fail('session_id 不能为空', 400)
    trace_entry = {
        'action': data.get('action', 'unknown'),
        'timestamp': datetime.now().isoformat(),
        'details': data.get('details', {}),
    }
    success = _detect.append_usage_trace(session_id, trace_entry)
    return _ok({'appended': success})


# ============================================================
# §13.3 结束会话 (设备拔出时前端调用)
# ============================================================
@arduino_bp.route('/api/arduino/session/end', methods=['POST'])
def arduino_session_end():
    """结束 Arduino 编译会话 (设备拔出时调用)"""
    ok, u, err = _check_login()
    if not ok:
        return _fail('未登录', 401)
    data = request.get_json(silent=True) or {}
    session_id = (data.get('session_id') or '').strip()
    if not session_id:
        return _fail('session_id 不能为空', 400)
    success = _detect.end_user_session(session_id)
    return _ok({'ended': success})


# ============================================================
# §13.1 Arduino IDE 页面 (登录可访问, 权限遵循 用户权限.md)
# ============================================================
@arduino_bp.route('/admin_app/arduino_ide')
def arduino_ide_page():
    """Arduino IDE 编译页面

    权限规则 (用户权限.md):
      - 管理页面 (/admin_app/arduino_ide 管理) 仅 wuchenghao15
      - 临时登录用户可访问编译功能 (本页面渲染编译器, 不含管理功能)
    """
    ok, u, err = _check_login()
    if not ok:
        # 前端检测到无 session, 弹出临时登录框 (§13.2)
        return render_template(
            'admin_app/arduino_ide.html',
            needs_login=True,
            user=None,
        )

    # 检测当前已连接设备 (用于页面初始展示)
    status = _detect.get_status()
    connected_devices = status.get('devices', [])

    return render_template(
        'admin_app/arduino_ide.html',
        needs_login=False,
        user=u,
        connected_devices=connected_devices,
    )
