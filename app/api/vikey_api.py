#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Vikey USBKey 二次开发 REST API - Blueprint
============================================
鉴权模式：
  - 只读 / 检测类 (detect/list_bindings/certs/hash/random)：登录用户即可
  - 写操作 (bind/unbind/update_binding/import_cert)：super_admin 或 hardware_vikey_admin 角色
  - 密码运算 (login/sign/verify/encrypt/decrypt/hmac/logout)：登录 + 会话 token
  - 操作日志 (logs/stats)：管理员可读
"""
import os
import sys
import json
import time
import traceback
from datetime import datetime
from flask import Blueprint, request, jsonify, session

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PROJECT_ROOT = os.path.dirname(BASE_DIR)
sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, os.path.join(PROJECT_ROOT, 'core', 'services'))

vikey_api = Blueprint('vikey_api', __name__, url_prefix='/api/vikey')

from core.services.vikey_driver import (  # noqa: E402
    get_vikey_manager, VikeyError, VIKEY_DRIVER_VERSION, VIKEY_SUPPORT_ALGOS,
    _base64url_encode, _base64url_decode,
)

AUTH_DB = os.path.join(PROJECT_ROOT, 'split_databases', 'auth.db')


def _conn_auth():
    import sqlite3
    c = sqlite3.connect(AUTH_DB)
    c.row_factory = sqlite3.Row
    return c


def _current_user():
    if not session.get('username'):
        return None
    uid = session.get('user_id')
    user = {
        'id': uid,
        'username': session.get('username'),
        'role': session.get('role'),
        'is_admin': False,
        'is_super_admin': False,
        'is_hw_vikey_admin': False,
    }
    uname = str(session.get('username') or '').strip()
    if uname == 'wuchenghao15':
        user['is_super_admin'] = True
        user['is_admin'] = True
        user['is_hw_vikey_admin'] = True
        return user
    try:
        if uid and os.path.exists(AUTH_DB):
            with _conn_auth() as c:
                row = c.execute(
                    "SELECT super_admin_approved, role FROM users WHERE id=? LIMIT 1", (uid,)
                ).fetchone()
                if row:
                    if row['super_admin_approved']:
                        user['is_super_admin'] = True
                        user['is_admin'] = True
                    role = (row['role'] or '').lower()
                    admin_roles = {'admin', 'super_admin', 'school_admin', 'institution_admin',
                                   'teacher_admin', 'sysadmin', 'hardware_vikey_admin'}
                    if role in admin_roles:
                        user['is_admin'] = True
                        if role == 'super_admin':
                            user['is_super_admin'] = True
                        if role in ('hardware_vikey_admin', 'super_admin', 'sysadmin'):
                            user['is_hw_vikey_admin'] = True
    except Exception:
        pass
    if str(session.get('role') or '').lower() in {'admin', 'super_admin', 'hardware_vikey_admin'}:
        user['is_admin'] = True
    if str(session.get('role') or '').lower() in {'super_admin', 'hardware_vikey_admin'}:
        user['is_hw_vikey_admin'] = True
    if session.get('super_admin_approved') is True:
        user['is_super_admin'] = True
        user['is_hw_vikey_admin'] = True
    return user


def _client_ip():
    return (
        request.headers.get('X-Forwarded-For', '').split(',')[0].strip()
        or request.headers.get('X-Real-IP', '').strip()
        or (request.remote_addr or '')
    )


def _ua():
    return (request.headers.get('User-Agent') or '')[:255]


def _ok(data=None, **kw):
    payload = {'success': True, 'server_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
    if data is not None:
        payload['data'] = data
    payload.update(kw)
    return jsonify(payload)


def _fail(msg, code=400, **kw):
    payload = {'success': False, 'message': msg,
               'server_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
    payload.update(kw)
    return jsonify(payload), code


def _auth_required(need_admin=False, need_hw_admin=False, need_super=False):
    def decorator(fn):
        import functools

        @functools.wraps(fn)
        def wrap(*args, **kwargs):
            u = _current_user()
            if not u:
                return _fail('需要登录', 401)
            if need_super and not u['is_super_admin']:
                return _fail('需要超级管理员权限', 403)
            if need_hw_admin and not (u['is_hw_vikey_admin'] or u['is_super_admin']):
                return _fail('需要硬件密钥管理员权限', 403)
            if need_admin and not u['is_admin']:
                return _fail('需要管理员权限', 403)
            return fn(*args, **kwargs)
        return wrap
    return decorator


def _meta(**extra):
    u = _current_user() or {}
    m = {
        'user_id': u.get('id'),
        'username': u.get('username'),
        'client_ip': _client_ip(),
        'user_agent': _ua(),
    }
    m.update(extra)
    return m


# ==========================================================
#  元信息 / 驱动状态
# ==========================================================
@vikey_api.route('/version', methods=['GET'])
def version():
    return _ok({
        'driver_version': VIKEY_DRIVER_VERSION,
        'support_algos': VIKEY_SUPPORT_ALGOS,
        'manufacturer': 'MTSCOS Vikey Security',
    })


@vikey_api.route('/detect', methods=['GET'])
def detect():
    """设备探测：允许匿名访问（登录前探测超级管理员是否插入 UKey）"""
    mgr = get_vikey_manager()
    return _ok(mgr.detect())


@vikey_api.route('/status', methods=['GET'])
def status():
    """获取VIKEY设备状态（轻量级，用于前端实时监控）"""
    from core.services.vikey_driver import VikeyGetStatus
    result = VikeyGetStatus()
    return _ok(result)


@vikey_api.route('/simulate_plug', methods=['POST'])
def simulate_plug():
    """
    模拟设备插拔（仅模拟模式下有效）
    Body: { serial, present }
    """
    body = request.get_json(silent=True) or {}
    serial = (body.get('serial') or '').strip()
    present = bool(body.get('present', True))
    
    if not serial:
        return _fail('缺少 serial', 400)
    
    try:
        from core.services.vikey_driver import _SIM_DEVICES, _SIM_DEVICES_LOCK
        with _SIM_DEVICES_LOCK:
            if serial in _SIM_DEVICES:
                _SIM_DEVICES[serial]['present'] = present
                return _ok({'serial': serial, 'present': present, 'message': '模拟插拔成功'})
            else:
                return _fail(f'设备不存在: {serial}', 404)
    except Exception as e:
        return _fail(f'模拟插拔失败: {e}', 500)


@vikey_api.route('/challenge', methods=['GET'])
def challenge():
    """生成随机挑战串 + 6位数字随机码（登录前匿名获取即可）。挑战码 60 秒后自动过期，每 1 分钟自动刷新。"""
    import secrets as _s
    raw = _s.token_bytes(32)
    code6 = "".join([str(_s.randbelow(10)) for _ in range(6)])
    chal_id = "chal_" + _s.token_hex(6)
    try:
        from flask import current_app
        cache_key = 'vikey_challenge_' + chal_id
        storage = getattr(current_app, '_vikey_challenge_cache', None)
        if storage is None:
            storage = {}
            setattr(current_app, '_vikey_challenge_cache', storage)
        storage[chal_id] = {
            'challenge_hex': raw.hex(),
            'challenge_b64': _base64url_encode(raw),
            'random_code': code6,
            'expires_at_ts': int(time.time()) + 60,
            'used': False,
        }
    except Exception:
        pass
    return _ok({
        'challenge_id': chal_id,
        'challenge_hex': raw.hex(),
        'challenge_b64': _base64url_encode(raw),
        'random_code': code6,
        'expires_at': datetime.fromtimestamp(time.time() + 60).strftime("%Y-%m-%d %H:%M:%S"),
        'expires_in': 60,
        'algo_hint': 'SM2withSM3',
    })


@vikey_api.route('/hardware_anonymous_auth', methods=['POST'])
def hardware_anonymous_auth():
    """
    登录前匿名验证 UKey：超级管理员登录必须先走这一步。
    输入：{ serial, pin?, challenge_id, random_code, signature_b64? }
      - pin 可选：未传 pin 时将自动读取 USB Key 内部存储的 PIN 完成验证（用户无需手动输入 PIN）
    输出：{ success, vikey_auth_token, binding_info }
    """
    body = request.get_json(silent=True) or {}
    serial = (body.get('serial') or '').strip()
    pin = body.get('pin') or ''
    challenge_id = (body.get('challenge_id') or '').strip()
    random_code_input = str(body.get('random_code') or '').strip()
    signature_b64 = (body.get('signature_b64') or '').strip()
    auto_pin = not bool(pin)

    if not serial:
        return _fail('缺少 serial', 400)
    if not challenge_id or not random_code_input:
        return _fail('缺少随机码挑战信息', 400)

    try:
        from flask import current_app
        storage = getattr(current_app, '_vikey_challenge_cache', None) or {}
        chal = storage.get(challenge_id)
        if not chal:
            return _fail('随机码挑战不存在或已过期', 401)
        if chal.get('used'):
            return _fail('随机码挑战已被使用', 401)
        if int(time.time()) > int(chal.get('expires_at_ts', 0)):
            storage.pop(challenge_id, None)
            return _fail('随机码挑战已过期，请重新获取', 401)
        if str(chal.get('random_code', '')) != random_code_input:
            return _fail('随机码错误', 401)
    except Exception as e:
        return _fail(f'随机码校验失败: {e}', 401)

    mgr = get_vikey_manager()
    try:
        binding = mgr.get_binding(serial) or {}
        if auto_pin:
            result = mgr.login_with_internal_pin(serial, 'user', meta={
                'username': binding.get('username'),
                'user_id': binding.get('user_id'),
                'client_ip': _client_ip(),
                'user_agent': _ua(),
                'operation': 'hardware_anonymous_auth_auto_pin',
            })
        else:
            result = mgr.login(serial, pin, 'user', meta={
                'username': binding.get('username'),
                'user_id': binding.get('user_id'),
                'client_ip': _client_ip(),
                'user_agent': _ua(),
                'operation': 'hardware_anonymous_auth',
            })
        try:
            storage = getattr(current_app, '_vikey_challenge_cache', None) or {}
            storage[challenge_id]['used'] = True
        except Exception:
            pass
        token = 'vat_' + __import__('secrets').token_urlsafe(32)
        try:
            token_store = getattr(current_app, '_vikey_auth_token_cache', None)
            if token_store is None:
                token_store = {}
                setattr(current_app, '_vikey_auth_token_cache', token_store)
            token_store[token] = {
                'serial': serial,
                'binding': binding,
                'session_token': result.get('session_token'),
                'issued_at': int(time.time()),
                'expires_at': int(time.time()) + 300,
            }
        except Exception:
            pass
        return _ok({
            'vikey_auth_token': token,
            'serial': serial,
            'binding': binding,
            'device_info': result.get('device_info'),
            'expires_in': 300,
            'auto_pin': auto_pin,
        }, message='USB 密钥硬件认证通过' + ('（自动验证密钥内部 PIN）' if auto_pin else ''))
    except VikeyError as e:
        return _fail(str(e), 401, error_code=hex(e.code))
    except Exception as e:
        return _fail(f'USB 密钥认证失败: {e}', 401)


@vikey_api.route('/verify_vikey_token', methods=['POST'])
def verify_vikey_token():
    """后端 /auth/login 使用：验证 vikey_auth_token 与对应用户名、serial 是否匹配"""
    body = request.get_json(silent=True) or {}
    token = (body.get('vikey_auth_token') or '').strip()
    expect_username = (body.get('username') or '').strip()
    expect_serial = (body.get('serial') or '').strip()
    if not token:
        return _fail('缺少 vikey_auth_token', 400), False
    try:
        from flask import current_app
        token_store = getattr(current_app, '_vikey_auth_token_cache', None) or {}
        rec = token_store.get(token)
        if not rec:
            return _fail('USB 密钥认证令牌无效', 401), False
        if int(time.time()) > int(rec.get('expires_at', 0)):
            token_store.pop(token, None)
            return _fail('USB 密钥认证令牌已过期', 401), False
        if expect_serial and rec.get('serial') != expect_serial:
            return _fail('USB 密钥序列号不匹配', 401), False
        binding = rec.get('binding') or {}
        bound_username = str(binding.get('username') or '').strip().lower()
        if expect_username and bound_username and bound_username != expect_username.lower():
            return _fail('USB 密钥未绑定到该用户', 401), False
        token_store.pop(token, None)
        return _ok({
            'serial': rec.get('serial'),
            'binding': binding,
            'session_token': rec.get('session_token'),
        }, message='USB 密钥令牌校验通过'), True
    except Exception as e:
        return _fail(f'USB 密钥令牌校验异常: {e}', 401), False


# ==========================================================
#  登录 / 会话
# ==========================================================
@vikey_api.route('/login', methods=['POST'])
@_auth_required(need_admin=False)
def login():
    """
    UKey PIN 登录，返回会话 token。
    Body JSON: { serial, pin, user_type?: "user"|"so"|"admin" }
    """
    body = request.get_json(silent=True) or {}
    serial = (body.get('serial') or '').strip()
    pin = (body.get('pin') or '')
    user_type = (body.get('user_type') or 'user').lower()
    if not serial:
        return _fail('缺少 serial', 400)
    if not pin:
        return _fail('缺少 pin', 400)
    if user_type not in ('user', 'so', 'admin'):
        user_type = 'user'
    mgr = get_vikey_manager()
    try:
        result = mgr.login(serial, pin, user_type, meta=_meta())
        return _ok(result, message='登录成功')
    except VikeyError as e:
        return _fail(str(e), 401, error_code=hex(e.code))
    except Exception as e:
        return _fail(f'登录失败: {e}', 500, trace=traceback.format_exc()[:300])


@vikey_api.route('/session', methods=['GET'])
@_auth_required(need_admin=False)
def session_status():
    """查询登录会话状态 ?token=xxx"""
    token = (request.args.get('token') or request.headers.get('X-Vikey-Token') or '').strip()
    if not token:
        return _fail('缺少 token', 400)
    mgr = get_vikey_manager()
    return _ok(mgr.session_status(token))


@vikey_api.route('/logout', methods=['POST'])
@_auth_required(need_admin=False)
def logout():
    """登出会话：{ token }"""
    body = request.get_json(silent=True) or {}
    token = (body.get('token') or request.headers.get('X-Vikey-Token') or '').strip()
    if not token:
        return _fail('缺少 token', 400)
    mgr = get_vikey_manager()
    ok = mgr.logout_token(token)
    return _ok({'logged_out': ok})


# ==========================================================
#  密码运算接口
# ==========================================================
@vikey_api.route('/sign', methods=['POST'])
@_auth_required(need_admin=False)
def sign():
    """
    签名接口：需要先登录拿到 session_token。
    Body: { token, key_id="SM2_SIG_01", data_b64, hash_algo?="SM3"|"SHA256" }
    """
    body = request.get_json(silent=True) or {}
    token = (body.get('token') or request.headers.get('X-Vikey-Token') or '').strip()
    key_id = (body.get('key_id') or 'SM2_SIG_01').strip()
    data_b64 = (body.get('data_b64') or body.get('data') or '').strip()
    hash_algo = (body.get('hash_algo') or 'SM3').upper()
    if not token:
        return _fail('缺少 token，请先登录 UKey', 400)
    if not data_b64:
        return _fail('缺少 data_b64', 400)
    if hash_algo not in VIKEY_SUPPORT_ALGOS and hash_algo not in ('SM3', 'SHA256', 'SHA384', 'SHA512'):
        return _fail(f'不支持的 hash_algo: {hash_algo}', 400)
    mgr = get_vikey_manager()
    try:
        res = mgr.sign(token, key_id, data_b64, hash_algo, meta=_meta())
        return _ok(res)
    except VikeyError as e:
        return _fail(str(e), 400, error_code=hex(e.code))
    except Exception as e:
        return _fail(f'sign fail: {e}', 500)


@vikey_api.route('/verify', methods=['POST'])
@_auth_required(need_admin=False)
def verify():
    """
    验签接口（允许匿名，只要能找到设备即可）。
    Body: { token?, key_id, data_b64, signature_b64, hash_algo? }
    """
    body = request.get_json(silent=True) or {}
    token = (body.get('token') or request.headers.get('X-Vikey-Token') or '').strip()
    key_id = (body.get('key_id') or 'SM2_SIG_01').strip()
    data_b64 = (body.get('data_b64') or body.get('data') or '').strip()
    sig = (body.get('signature_b64') or body.get('signature') or '').strip()
    hash_algo = (body.get('hash_algo') or 'SM3').upper()
    if not data_b64 or not sig:
        return _fail('缺少 data_b64 或 signature_b64', 400)
    mgr = get_vikey_manager()
    try:
        res = mgr.verify(token, key_id, data_b64, sig, hash_algo, meta=_meta())
        return _ok(res)
    except VikeyError as e:
        return _fail(str(e), 400, error_code=hex(e.code))
    except Exception as e:
        return _fail(f'verify fail: {e}', 500)


@vikey_api.route('/encrypt', methods=['POST'])
@_auth_required(need_admin=False)
def encrypt():
    body = request.get_json(silent=True) or {}
    token = (body.get('token') or request.headers.get('X-Vikey-Token') or '').strip()
    key_id = (body.get('key_id') or 'SM4_SES_01').strip()
    pt = (body.get('plaintext_b64') or body.get('data_b64') or '').strip()
    if not token or not pt:
        return _fail('缺少 token 或 plaintext_b64', 400)
    mgr = get_vikey_manager()
    try:
        return _ok(mgr.encrypt(token, key_id, pt, meta=_meta()))
    except VikeyError as e:
        return _fail(str(e), 400, error_code=hex(e.code))
    except Exception as e:
        return _fail(f'encrypt fail: {e}', 500)


@vikey_api.route('/decrypt', methods=['POST'])
@_auth_required(need_admin=False)
def decrypt():
    body = request.get_json(silent=True) or {}
    token = (body.get('token') or request.headers.get('X-Vikey-Token') or '').strip()
    key_id = (body.get('key_id') or 'SM4_SES_01').strip()
    nonce = (body.get('nonce_b64') or '').strip()
    ct = (body.get('ciphertext_b64') or '').strip()
    if not token or not nonce or not ct:
        return _fail('缺少 token/nonce_b64/ciphertext_b64', 400)
    mgr = get_vikey_manager()
    try:
        return _ok(mgr.decrypt(token, key_id, nonce, ct, meta=_meta()))
    except VikeyError as e:
        return _fail(str(e), 400, error_code=hex(e.code))
    except Exception as e:
        return _fail(f'decrypt fail: {e}', 500)


@vikey_api.route('/hmac', methods=['POST'])
@_auth_required(need_admin=False)
def hmac():
    body = request.get_json(silent=True) or {}
    token = (body.get('token') or request.headers.get('X-Vikey-Token') or '').strip()
    key_id = (body.get('key_id') or 'HMAC_KEY_01').strip()
    data_b64 = (body.get('data_b64') or '').strip()
    hash_algo = (body.get('hash_algo') or 'SHA256').upper()
    if not token or not data_b64:
        return _fail('缺少 token 或 data_b64', 400)
    mgr = get_vikey_manager()
    try:
        return _ok(mgr.hmac(token, key_id, data_b64, hash_algo, meta=_meta()))
    except VikeyError as e:
        return _fail(str(e), 400, error_code=hex(e.code))
    except Exception as e:
        return _fail(f'hmac fail: {e}', 500)


@vikey_api.route('/hash', methods=['POST'])
@_auth_required(need_admin=False)
def hash_data():
    """纯哈希，不需要登录 UKey（驱动层本地实现）"""
    body = request.get_json(silent=True) or {}
    data_b64 = (body.get('data_b64') or '').strip()
    algo = (body.get('algo') or 'SM3').upper()
    if not data_b64:
        return _fail('缺少 data_b64', 400)
    mgr = get_vikey_manager()
    try:
        return _ok(mgr.hash_data(data_b64, algo))
    except VikeyError as e:
        return _fail(str(e), 400, error_code=hex(e.code))
    except Exception as e:
        return _fail(f'hash fail: {e}', 500)


@vikey_api.route('/random', methods=['GET'])
@_auth_required(need_admin=False)
def random_bytes():
    """硬件真随机数 ?serial=xxx&length=32"""
    serial = (request.args.get('serial') or '').strip()
    length = int(request.args.get('length') or 32)
    length = max(1, min(length, 1024))
    if not serial:
        devs = get_vikey_manager().enumerate_devices()
        if not devs:
            return _fail('无可用 UKey', 404)
        serial = devs[0]['serial']
    mgr = get_vikey_manager()
    try:
        return _ok(mgr.random(serial, length, meta=_meta()))
    except VikeyError as e:
        return _fail(str(e), 400, error_code=hex(e.code))


# ==========================================================
#  密钥 / 证书
# ==========================================================
@vikey_api.route('/keys', methods=['GET'])
@_auth_required(need_admin=False)
def list_keys():
    serial = (request.args.get('serial') or '').strip()
    if not serial:
        return _fail('缺少 serial', 400)
    mgr = get_vikey_manager()
    return _ok({'serial': serial, 'keys': mgr.list_keys(serial)})


@vikey_api.route('/certs', methods=['GET'])
@_auth_required(need_admin=False)
def list_certs():
    serial = (request.args.get('serial') or '').strip()
    if not serial:
        return _fail('缺少 serial', 400)
    mgr = get_vikey_manager()
    return _ok({'serial': serial, 'certs': mgr.list_certificates(serial)})


@vikey_api.route('/certs/export', methods=['POST'])
@_auth_required(need_hw_admin=False, need_admin=False)
def export_cert():
    body = request.get_json(silent=True) or {}
    serial = (body.get('serial') or '').strip()
    cert_id = (body.get('cert_id') or 'CERT_01').strip()
    if not serial:
        return _fail('缺少 serial', 400)
    mgr = get_vikey_manager()
    try:
        return _ok(mgr.export_cert(serial, cert_id, meta=_meta()))
    except VikeyError as e:
        return _fail(str(e), 400, error_code=hex(e.code))


# ==========================================================
#  绑定管理 (管理员级别)
# ==========================================================
@vikey_api.route('/bindings', methods=['GET'])
@_auth_required(need_admin=True)
def list_bindings():
    """列出所有 UKey 绑定关系（仅管理员）"""
    mgr = get_vikey_manager()
    return _ok({'items': mgr.list_bindings()})


@vikey_api.route('/bindings/<serial>', methods=['GET'])
@_auth_required(need_admin=True)
def get_binding(serial):
    mgr = get_vikey_manager()
    b = mgr.get_binding(serial)
    if not b:
        return _fail(f'未找到 serial={serial} 的绑定', 404)
    return _ok(b)


@vikey_api.route('/bindings', methods=['POST'])
@_auth_required(need_hw_admin=True)
def create_or_update_binding():
    """
    绑定/更新 UKey 到用户。
    Body: { serial, user_id, username, role_hint, label, allowed_operations?: ["sign","login",...] }
    """
    body = request.get_json(silent=True) or {}
    serial = (body.get('serial') or '').strip()
    if not serial:
        return _fail('缺少 serial', 400)
    fields = {}
    for k in ('user_id', 'username', 'role_hint', 'label', 'allowed_operations', 'remark'):
        if k in body:
            fields[k] = body[k] if k != 'allowed_operations' else json.dumps(
                body[k], ensure_ascii=False
            ) if not isinstance(body[k], str) else body[k]
    if not fields:
        return _fail('没有可更新的字段', 400)
    fields['binding_status'] = 'bound'
    mgr = get_vikey_manager()
    b = mgr.update_binding(serial, **fields)
    return _ok(b, message='绑定已更新')


@vikey_api.route('/bindings/<serial>/unbind', methods=['POST'])
@_auth_required(need_hw_admin=True)
def unbind(serial):
    """吊销/解绑 UKey"""
    mgr = get_vikey_manager()
    b = mgr.update_binding(
        serial,
        binding_status='revoked',
        user_id=None,
        username=None,
        unbound_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    )
    return _ok(b, message='已吊销')


# ==========================================================
#  硬件前端上报校验（对接 mechanism_ai 的硬件身份验证）
# ==========================================================
@vikey_api.route('/verify_hardware', methods=['POST'])
@_auth_required(need_admin=False)
def verify_hardware():
    """
    前端/插件通过这个接口上报 UKey 信息，服务端校验真伪与绑定。
    Body: { hardwareId, session_token?, signature?, challenge? }
    """
    info = request.get_json(silent=True) or {}
    mgr = get_vikey_manager()
    return _ok(mgr.verify_vikey_hardware(info))


# ==========================================================
#  操作日志 / 统计
# ==========================================================
@vikey_api.route('/logs', methods=['GET'])
@_auth_required(need_admin=True)
def list_logs():
    """
    操作日志：?limit=100&serial=xxx&operation=login
    """
    limit = int(request.args.get('limit') or 100)
    limit = max(1, min(limit, 5000))
    serial = (request.args.get('serial') or None) or None
    operation = (request.args.get('operation') or None) or None
    mgr = get_vikey_manager()
    rows = mgr.list_operations(limit=limit, serial=serial, operation=operation)
    return _ok({'count': len(rows), 'items': rows})


@vikey_api.route('/stats', methods=['GET'])
@_auth_required(need_admin=True)
def stats():
    mgr = get_vikey_manager()
    bindings = mgr.list_bindings()
    bound = sum(1 for b in bindings if b.get('binding_status') == 'bound')
    revoked = sum(1 for b in bindings if b.get('binding_status') == 'revoked')
    recent = mgr.list_operations(1000)
    ok = sum(1 for r in recent if r.get('success'))
    op_counts = {}
    for r in recent:
        op_counts[r.get('operation') or 'unknown'] = op_counts.get(r.get('operation') or 'unknown', 0) + 1
    return _ok({
        'binding_total': len(bindings),
        'binding_bound': bound,
        'binding_revoked': revoked,
        'binding_unbound': len(bindings) - bound - revoked,
        'device_online_count': len(mgr.enumerate_devices()),
        'recent_ops_count': len(recent),
        'recent_ops_success': ok,
        'recent_ops_fail': len(recent) - ok,
        'recent_ops_by_type': op_counts,
        'driver_version': VIKEY_DRIVER_VERSION,
    })


# ==========================================================
#  AI增强接口 - VIKEY安全专家
# ==========================================================
@vikey_api.route('/ai/health_check', methods=['GET'])
@_auth_required(need_admin=False)
def ai_health_check():
    """
    AI增强：VIKEY设备健康检查
    返回所有设备的健康状态、存储使用、PIN重试次数等信息
    """
    try:
        from ai_engines.ai_vikey_security_employee import AI_VIKEY_Security_Employee
        
        employee = AI_VIKEY_Security_Employee("api_health_check", "API健康检查员工")
        result = employee.process({'type': 'health_check'})
        
        if result.get('success'):
            return _ok(result.get('data', {}), message=result.get('message', ''))
        else:
            return _fail(result.get('message', '健康检查失败'), 500)
    except Exception as e:
        return _fail(f'AI健康检查失败: {e}', 500)


@vikey_api.route('/ai/security_audit', methods=['GET'])
@_auth_required(need_admin=True)
def ai_security_audit():
    """
    AI增强：VIKEY安全审计
    分析认证日志，检测异常行为模式
    """
    serial = (request.args.get('serial') or '').strip()
    time_range = (request.args.get('time_range') or '24h').strip()
    
    try:
        from ai_engines.ai_vikey_security_employee import AI_VIKEY_Security_Employee
        
        employee = AI_VIKEY_Security_Employee("api_security_audit", "API安全审计员工")
        result = employee.process({
            'type': 'audit_logs',
            'serial': serial,
            'time_range': time_range,
        })
        
        if result.get('success'):
            return _ok(result, message=result.get('message', ''))
        else:
            return _fail(result.get('message', '安全审计失败'), 500)
    except Exception as e:
        return _fail(f'AI安全审计失败: {e}', 500)


@vikey_api.route('/ai/anomaly_detection', methods=['GET'])
@_auth_required(need_admin=True)
def ai_anomaly_detection():
    """
    AI增强：VIKEY异常检测
    实时检测安全威胁并预警（暴力破解、设备缺失、PIN重试不足等）
    """
    try:
        from ai_engines.ai_vikey_security_employee import AI_VIKEY_Security_Employee
        
        employee = AI_VIKEY_Security_Employee("api_anomaly_detection", "API异常检测员工")
        result = employee.process({'type': 'anomaly_detection'})
        
        if result.get('success'):
            return _ok(result, message=result.get('message', ''))
        else:
            return _fail(result.get('message', '异常检测失败'), 500)
    except Exception as e:
        return _fail(f'AI异常检测失败: {e}', 500)


@vikey_api.route('/ai/key_rotation', methods=['POST'])
@_auth_required(need_hw_admin=True)
def ai_key_rotation():
    """
    AI增强：VIKEY密钥轮换
    自动生成新密钥，支持单密钥轮换和批量轮换
    Body: { serial, key_id?, algo?="SM2" }
    """
    body = request.get_json(silent=True) or {}
    serial = (body.get('serial') or '').strip()
    key_id = (body.get('key_id') or '').strip()
    algo = (body.get('algo') or 'SM2').upper()
    
    if not serial:
        return _fail('缺少设备序列号', 400)
    
    try:
        from ai_engines.ai_vikey_security_employee import AI_VIKEY_Security_Employee
        
        employee = AI_VIKEY_Security_Employee("api_key_rotation", "API密钥轮换员工")
        result = employee.process({
            'type': 'key_rotation',
            'serial': serial,
            'key_id': key_id,
            'algo': algo,
        })
        
        if result.get('success'):
            return _ok(result, message=result.get('message', ''))
        else:
            return _fail(result.get('message', '密钥轮换失败'), 500)
    except Exception as e:
        return _fail(f'AI密钥轮换失败: {e}', 500)


@vikey_api.route('/ai/generate_report', methods=['GET'])
@_auth_required(need_admin=True)
def ai_generate_report():
    """
    AI增强：生成VIKEY安全报告
    包含设备概览、绑定管理、操作统计、安全策略、安全预警等完整报告
    """
    report_type = (request.args.get('report_type') or 'daily').strip()
    
    try:
        from ai_engines.ai_vikey_security_employee import AI_VIKEY_Security_Employee
        
        employee = AI_VIKEY_Security_Employee("api_report_generator", "API报告生成员工")
        result = employee.process({'type': 'generate_report', 'report_type': report_type})
        
        if result.get('success'):
            return _ok(result.get('report', {}), message=result.get('message', ''))
        else:
            return _fail(result.get('message', '生成报告失败'), 500)
    except Exception as e:
        return _fail(f'AI生成报告失败: {e}', 500)


@vikey_api.route('/ai/policy', methods=['GET'])
@_auth_required(need_admin=True)
def ai_get_policy():
    """
    AI增强：获取VIKEY安全策略
    返回当前生效的所有安全策略配置
    """
    try:
        from ai_engines.ai_vikey_security_employee import AI_VIKEY_Security_Employee
        
        employee = AI_VIKEY_Security_Employee("api_policy_get", "API策略查询员工")
        result = employee.process({'type': 'get_policy'})
        
        if result.get('success'):
            return _ok(result.get('policy', {}), message=result.get('message', ''))
        else:
            return _fail(result.get('message', '获取策略失败'), 500)
    except Exception as e:
        return _fail(f'AI获取策略失败: {e}', 500)


@vikey_api.route('/ai/policy', methods=['PUT'])
@_auth_required(need_hw_admin=True)
def ai_update_policy():
    """
    AI增强：更新VIKEY安全策略
    Body: { policy: { key: value, ... } }
    """
    body = request.get_json(silent=True) or {}
    policy_updates = body.get('policy', {})
    
    if not policy_updates:
        return _fail('缺少策略更新内容', 400)
    
    try:
        from ai_engines.ai_vikey_security_employee import AI_VIKEY_Security_Employee
        
        employee = AI_VIKEY_Security_Employee("api_policy_update", "API策略更新员工")
        result = employee.process({'type': 'update_policy', 'policy': policy_updates})
        
        if result.get('success'):
            return _ok(result.get('policy', {}), message=result.get('message', ''))
        else:
            return _fail(result.get('message', '更新策略失败'), 500)
    except Exception as e:
        return _fail(f'AI更新策略失败: {e}', 500)


@vikey_api.route('/ai/certificate_check', methods=['GET'])
@_auth_required(need_admin=False)
def ai_certificate_check():
    """
    AI增强：VIKEY证书检查
    返回所有设备的证书信息、过期状态检查
    """
    serial = (request.args.get('serial') or '').strip()
    
    try:
        from ai_engines.ai_vikey_security_employee import AI_VIKEY_Security_Employee
        
        employee = AI_VIKEY_Security_Employee("api_cert_check", "API证书检查员工")
        result = employee.process({'type': 'certificate_check', 'serial': serial})
        
        if result.get('success'):
            return _ok(result, message=result.get('message', ''))
        else:
            return _fail(result.get('message', '证书检查失败'), 500)
    except Exception as e:
        return _fail(f'AI证书检查失败: {e}', 500)


@vikey_api.route('/ai/binding_audit', methods=['GET'])
@_auth_required(need_admin=True)
def ai_binding_audit():
    """
    AI增强：VIKEY绑定审计
    检查用户绑定数量是否符合策略限制
    """
    try:
        from ai_engines.ai_vikey_security_employee import AI_VIKEY_Security_Employee
        
        employee = AI_VIKEY_Security_Employee("api_binding_audit", "API绑定审计员工")
        result = employee.process({'type': 'binding_audit'})
        
        if result.get('success'):
            return _ok(result.get('audit', {}), message=result.get('message', ''))
        else:
            return _fail(result.get('message', '绑定审计失败'), 500)
    except Exception as e:
        return _fail(f'AI绑定审计失败: {e}', 500)


@vikey_api.route('/ai/auto_repair', methods=['POST'])
@_auth_required(need_hw_admin=True)
def ai_auto_repair():
    """
    AI增强：VIKEY自动修复
    自动检测并修复设备问题（重置状态、检查密钥等）
    Body: { serial?, repair_type?="all" }
    """
    body = request.get_json(silent=True) or {}
    serial = (body.get('serial') or '').strip()
    repair_type = (body.get('repair_type') or 'all').strip()
    
    try:
        from ai_engines.ai_vikey_security_employee import AI_VIKEY_Security_Employee
        
        employee = AI_VIKEY_Security_Employee("api_auto_repair", "API自动修复员工")
        result = employee.process({'type': 'auto_repair', 'serial': serial, 'repair_type': repair_type})
        
        if result.get('success'):
            return _ok(result, message=result.get('message', ''))
        else:
            return _fail(result.get('message', '自动修复失败'), 500)
    except Exception as e:
        return _fail(f'AI自动修复失败: {e}', 500)


@vikey_api.route('/ai/alerts', methods=['GET'])
@_auth_required(need_admin=True)
def ai_get_alerts():
    """
    AI增强：获取VIKEY安全预警列表
    ?limit=20&level=critical|warning
    """
    limit = int(request.args.get('limit') or 20)
    level = (request.args.get('level') or '').strip()
    
    try:
        from ai_engines.ai_vikey_security_employee import AI_VIKEY_Security_Employee
        
        employee = AI_VIKEY_Security_Employee("api_alerts", "API预警查询员工")
        result = employee.process({'type': 'get_alerts', 'limit': limit, 'level': level})
        
        if result.get('success'):
            return _ok(result, message=result.get('message', ''))
        else:
            return _fail(result.get('message', '获取预警失败'), 500)
    except Exception as e:
        return _fail(f'AI获取预警失败: {e}', 500)
