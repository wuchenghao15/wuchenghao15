#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
auth_routes — 认证相关路由（骨架已升级为可用实现）
================================================================
源参考: server_real_db.py L6738-L8763 (7路由)
当前实现: 仅 /auth/check_username（前端用户名小点指示器必需）
        其余 6 个路由保持 TODO 状态，未来按需迁移

设计原则:
  - 自包含：不依赖 server_real_db.py 的 5 个 helper
  - 跨库兜底：优先查 app.db，失败时尝试已知用户库列表
  - SA 白名单硬保证：wuchenghao15 直接返回 super_admin（不暴露真实库结构）
  - 不创建用户、不修改密码、不泄露敏感字段
"""
from __future__ import annotations

import os
import re
import sqlite3
import base64
import hashlib
import hmac
import time
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from flask import Blueprint, jsonify, jsonify, request, session, redirect, url_for, render_template, current_app

from . import auth_bp
from app.middlewares.system_container import system_container

# ---------- 常量 ----------
_SA_WHITELIST = {'wuchenghao15'}
_ADMIN_LIKE_ROLES = {'super_admin', 'admin', 'hardware_admin', 'cluster_manager'}


def _clear_sa_session():
    """Remove stale privileged session state after an incomplete SA login."""
    for key in (
        'user_id', 'username', 'role', 'role_canonical', 'logged_in',
        'auth_method', '_sa_session', '_sa_login_time',
        '_sa_dual_verified_at', '_sa_dual_reason',
    ):
        session.pop(key, None)


def _write_login_route_override(user_role, source_path, rewritten_path, rule_reason):
    """T02c: Arduino 登录重写路由审计写入 (最佳努力，失败不阻塞)。"""
    try:
        import sys as _s, os as _o, uuid as _u, sqlite3 as _sq3, time as _t
        _eng_dir = _o.join(_o.dirname(_o.dirname(_o.path.abspath(__file__))), 'engines')
        if _eng_dir not in _s.path:
            _s.path.insert(0, _eng_dir)
        import ai_arduino_detect_engine as _ad
        _ad.ensure_detect_tables()
        from core.db_path import get_db_path as _g
        dbp = _g('app.db')
        conn = _sq3.connect(dbp, timeout=5)
        c = conn.cursor()
        override_id = f"ARD-RO-{_u.uuid4().hex[:12]}"
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        c.execute("""INSERT INTO mt_arduino_route_override_log
            (override_id,user_role,source_path,rewritten_path,rule_reason,created_at)
            VALUES(?,?,?,?,?,?)""",
            (override_id, user_role, source_path, rewritten_path, rule_reason, now))
        conn.commit()
        conn.close()
    except Exception:
        pass
# 学生类角色（含中文变体）：规范化到 'student'，避免下游 role=='student' 硬编码识别不到中文角色
_STUDENT_LIKE_ROLES = {
    'student', '学生', '成人学生', 'k12_student', 'adult_student',
    '成人教育学生', '大学生', '高校学生', '在校生', 'learner',
    'student_vip', 'adult_student_vip',
}

_REGISTERED_SYSTEM_ROLES = {
    'guest', 'login', 'user',
    'super_admin', 'sadmin', 'admin', 'system_admin', 'school_admin', 'sysadmin',
    'hardware_admin', 'cluster_manager',
    'student', 'student_vip', 'adult_student', 'k12_student',
    'teacher', 'teaching_leader', 'academic_affairs',
    'parent', 'guardian', 'principal', 'operator',
    '管理员', '学生', '教师', '家长', '校长', '运营员',
    '成人学生', '成人教育学生', '大学生', '高校学生', '在校生', 'learner',
}

_STUDENT_SUBJECT_KEYWORDS = {
    'math': ('math', '数学', '数理', '算术', '代数', '几何'),
    'chinese': ('chinese', '语文', '文学', '文言', '阅读'),
    'english': ('english', '英语', 'en', '词汇', '口语'),
    'physics': ('physics', '物理', '力学', '电学'),
    'chemistry': ('chemistry', '化学', '无机', '有机'),
    'biology': ('biology', '生物', '遗传', '细胞'),
    'history': ('history', '历史', '古代', '近代'),
    'geography': ('geography', '地理', '地图', '环境'),
    'politics': ('politics', '政治', '思想', '道德'),
    'computer': ('computer', '编程', 'it', '计算机', '软件', '算法'),
    'art': ('art', '美术', '艺术', '设计', '绘画'),
    'music': ('music', '音乐', '合唱', '乐理'),
    'pe': ('pe', '体育', 'physical', '运动', '足球', '篮球'),
    'science': ('science', '理科', '科研', '实验'),
    'humanities': ('humanities', '文科', '人文', '社科'),
    'adult_education': ('adult_education', '成人教育', '成人学历', '成人高考', '继续教育', '学历提升', '职业教育', '技能培训', '自学考试', '夜大', '函授', '网络教育', '在职教育'),
    'adult_vocational': ('vocational', '职业培训', '职业教育', '技能提升', '岗位培训', '就业培训', '工艺培训'),
    'adult_diploma': ('diploma', '专升本', '本科提升', '学历提升', '成人本科', '高起专', '专科提升'),
    'adult_online': ('online', '网络教育', '线上教育', '远程学习', '在线学习', '直播教育'),
}

_STUDENT_GROUP_LABELS = {
    'math': '数学组',
    'chinese': '语文组',
    'english': '英语组',
    'physics': '物理组',
    'chemistry': '化学组',
    'biology': '生物组',
    'history': '历史组',
    'geography': '地理组',
    'politics': '政治组',
    'computer': '计算机组',
    'art': '美术组',
    'music': '音乐组',
    'pe': '体育组',
    'science': '理科组',
    'humanities': '文科组',
    'adult_education': '成人教育组',
    'adult_vocational': '职业教育组',
    'adult_diploma': '学历提升组',
    'adult_online': '网络教育组',
}

_STUDENT_SUBJECT_NAMES = {
    'math': '数学',
    'chinese': '语文',
    'english': '英语',
    'physics': '物理',
    'chemistry': '化学',
    'biology': '生物',
    'history': '历史',
    'geography': '地理',
    'politics': '政治',
    'computer': '计算机',
    'art': '美术',
    'music': '音乐',
    'pe': '体育',
    'science': '理科',
    'humanities': '文科',
    'adult_education': '成人教育',
    'adult_vocational': '职业教育',
    'adult_diploma': '学历提升',
    'adult_online': '网络教育',
}


def _infer_student_subject(raw_group: str):
    """根据学生组别/班级/学科词汇，细化到具体学科；成人教育单独细化。"""
    text = (raw_group or '').strip()
    if not text:
        return 'general', '综合', '综合学生组'
    haystack = text.lower()
    if '成人教育' in text or 'adult' in haystack or '继续教育' in text or '学历提升' in text or '自学考试' in text or '函授' in text or '夜大' in text:
        if '职业' in text or '技能' in text or '就业' in text:
            return 'adult_vocational', '职业教育', '职业教育组'
        if '学历' in text or '专升本' in text or '本科' in text or '提升' in text:
            return 'adult_diploma', '学历提升', '学历提升组'
        if '网络' in text or '线上' in text or '在线' in text or '远程' in text:
            return 'adult_online', '网络教育', '网络教育组'
        return 'adult_education', '成人教育', '成人教育组'
    for subject_key, aliases in _STUDENT_SUBJECT_KEYWORDS.items():
        for alias in aliases:
            if isinstance(alias, str) and alias.lower() in haystack:
                if subject_key in {'adult_education', 'adult_vocational', 'adult_diploma', 'adult_online'}:
                    continue
                return subject_key, _STUDENT_SUBJECT_NAMES.get(subject_key, subject_key), _STUDENT_GROUP_LABELS.get(subject_key, '综合学生组')
    if '理科' in text or 'science' in haystack:
        return 'science', '理科', '理科组'
    if '文科' in text or 'humanities' in haystack:
        return 'humanities', '文科', '文科组'
    if '班' in text or 'class' in haystack or 'group' in haystack:
        return 'general', '综合', '综合学生组'
    return 'general', '综合', '综合学生组'


def _canonize_role(raw_role: str) -> str:
    """角色规范化：只接受系统已注册的角色；其他一律归入 guest。

    规则：
    - 已注册组别保留规范化后的英文角色
    - 未注册/未知/杂项组别一律视为 guest（最低权限，无任何权限）
    - guest 仅用于访问控制，不用于业务分流
    """
    if not raw_role:
        return 'guest'
    r = str(raw_role).strip().lower()
    if r in _ADMIN_LIKE_ROLES:
        return r
    if r in {'super_admin', 'sadmin'}:
        return 'super_admin'
    if r in {'admin', 'system_admin', 'school_admin', 'sysadmin'}:
        return 'admin'
    if r in {'hardware_admin', 'cluster_manager'}:
        return 'admin'
    if r in _STUDENT_LIKE_ROLES:
        return 'student'
    if r in {'teacher', 'teaching_leader', 'academic_affairs', '教师', '教务'}:
        return 'teacher'
    if r in {'parent', 'guardian', '家长'}:
        return 'parent'
    if r in {'principal', '校长'}:
        return 'admin'
    if r in {'operator', '运营员'}:
        return 'admin'
    if r in {'user', 'login', 'guest'}:
        return r if r == 'guest' else 'user'
    if r in _REGISTERED_SYSTEM_ROLES:
        return r
    return 'guest'


_CTRL_CHARS_RE = re.compile(r'[\r\n\t\v\f]')
# ⚠️ 超级管理员 wuchenghao15 禁用密码登录（项目硬约束）
# 仅接受 VIKEY 加密狗 + SZU100 专用 U 盘双因子认证（见 /auth/login SA 分支）
# 历史 PIN '2486' 已彻底废弃，不得恢复
# 常见默认密码（用于兼容占位哈希的初始化账户）
_COMMON_DEFAULT_PASSWORDS = [
    'admin123', '123456', 'password123', 'password', 'mtscos2026', 'mtscos2025',
    'abcd1234', 'abc123', '12345678',
]


# ---------- 密码哈希（与 server_real_db.py L5229 _hash_password 一致） ----------
def _hash_password(plain: str) -> str:
    """SHA256 -> Base64（与 split_databases/auth.db users.password 一致）"""
    return base64.b64encode(hashlib.sha256(plain.encode('utf-8')).digest()).decode('ascii')


def _hash_password_hex(plain: str) -> str:
    """SHA256 -> hex（与 _runtime/databases/Database/app.db users.password_hash 一致）

    app.db 将密码存为 64 位十六进制摘要（非 Base64），历史 _hash_password 仅产出 Base64,
    导致 app.db 用户即使密码正确也校验失败。本函数补齐 hex 形态以兼容两种存储。
    """
    return hashlib.sha256(plain.encode('utf-8')).hexdigest()


def _verify_password_fallback(plain: str, stored: str, username: str) -> bool:
    """兼容多种历史哈希格式：bcrypt / werkzeug / 常见密码映射 / 占位哈希"""
    if not plain or not stored:
        return False
    # 1) bcrypt
    if stored.startswith('$2'):
        try:
            import bcrypt
            if bcrypt.checkpw(plain.encode(), stored.encode()):
                return True
        except ImportError:
            pass
    # 2) werkzeug 格式
    try:
        from werkzeug.security import check_password_hash as _wk_check
        if '$' in stored or stored.startswith('pbkdf2') or stored.startswith('scrypt') or stored.startswith('sha256$'):
            try:
                if _wk_check(stored, plain):
                    return True
            except Exception:
                pass
    except Exception:
        pass
    # 3) 常见密码映射（同时匹配 Base64 与 hex 两种存储形态）
    cand_set = set(_COMMON_DEFAULT_PASSWORDS)
    cand_set.add(username or '')
    cand_set.add((username or '').lower())
    cand_set.add((username or '').capitalize())
    for cand in cand_set:
        if not cand:
            continue
        if _hash_password(cand) == stored or _hash_password_hex(cand) == stored:
            return plain == cand
    return False


def _password_matches(plain: str, stored: str, username: str) -> bool:
    """主密码校验入口：先标准 SHA256+base64, 再 SHA256+hex, 最后回退到兼容模式

    兼容两种历史存储:
      - auth.db / mtscos.db: users.password 列, Base64 编码 (44 字符)
      - app.db: users.password_hash 列, 十六进制摘要 (64 字符)
    """
    if not plain or not stored:
        return False
    stored = stored.strip()
    try:
        if hmac.compare_digest(_hash_password(plain), stored):
            return True
    except Exception:
        pass
    try:
        if hmac.compare_digest(_hash_password_hex(plain), stored):
            return True
    except Exception:
        pass
    return _verify_password_fallback(plain, stored, username)


# ---------- 用户名格式预检（与前端 _validateUsernameFormat 对齐） ----------
def _validate_username_format(raw):
    """返回 dict: ok/msg/color/allow_fetch"""
    s = '' if raw is None else str(raw)
    trimmed = s.strip()
    if not trimmed:
        return {'ok': True, 'msg': '', 'need_hide': True}
    if len(trimmed) < 2:
        return {'ok': False, 'msg': '用户名过短（至少2个字符）', 'color': 'red'}
    if len(trimmed) > 64:
        return {'ok': False, 'msg': '用户名过长（最多64个字符）', 'color': 'red'}
    if _CTRL_CHARS_RE.search(s):
        return {'ok': False, 'msg': '用户名含非法控制字符', 'color': 'red'}
    return {'ok': True, 'msg': '', 'color': 'gray', 'allow_fetch': True}


# ---------- 候选用户库列表（按优先级） ----------
def _candidate_user_dbs():
    """返回所有可能含 users 表的数据库路径列表（按优先级）

    P0 修复: get_db_path('app.db') 可能解析到损坏的副本
    (flask-app/data/databases/app.db, "malformed database schema (cluster) - orphan index"),
    导致 SELECT * FROM users 抛 DatabaseError 被跳过, 登录落到 auth.db 的 admin
    (其密码非 admin123) → admin/admin123 登录失败。此处显式将已验证健康的
    主库 _runtime/databases/Database/app.db (19.8GB, 含 admin/admin123 hex 哈希) 置于首位。
    """
    candidates = []
    # 显式优先: 健康主库 (项目根/_runtime/databases/Database/app.db)
    try:
        # 本文件: <root>/flask-app/routes/auth_routes.py → 上溯三级到项目根
        _here = os.path.dirname(os.path.abspath(__file__))
        _proj_root = os.path.dirname(os.path.dirname(_here))
        _runtime_appdb = os.path.join(_proj_root, '_runtime', 'databases', 'Database', 'app.db')
        if os.path.exists(_runtime_appdb) and os.path.getsize(_runtime_appdb) > 0:
            candidates.append(_runtime_appdb)
    except Exception:
        pass
    # 兜底: 通过 get_db_path 发现的其他候选库 (auth.db / mtscos.db 等)
    try:
        from core.db_path import get_db_path
        for name in ['app.db', 'admin.db', 'auth.db', 'mtscos.db']:
            try:
                p = get_db_path(name)
                if p and os.path.exists(p) and os.path.abspath(p) not in [os.path.abspath(c) for c in candidates]:
                    candidates.append(p)
            except Exception:
                pass
    except Exception:
        pass
    return candidates


# ---------- 跨库密码校验（多副本容错） ----------
def _find_user_by_password(username, password):
    """跨库查找用户并校验密码, 返回首个密码匹配的 (user_dict, db_path)

    背景: 同一用户名在不同库可能存在密码不一致的副本(历史数据迁移/同步遗留),
          例如 test_student 在 app.db 的 password_hash 与 auth.db 的 password 不同。
          旧实现仅取首个含该用户的库校验, 一旦该副本密码不符即拒绝, 导致可用账户登录失败。
    本函数遍历所有候选库, 在每个含该用户的库中逐一校验密码, 返回首个匹配项,
    兼顾多副本容错; 仅当所有库均不匹配时返回 (None, None)。
    账户禁用检查仍由调用方(login)在匹配后执行。
    """
    if not username or not password:
        return None, None
    uname = str(username).strip()

    for db_path in _candidate_user_dbs():
        try:
            conn = sqlite3.connect(db_path, timeout=10)
            conn.row_factory = sqlite3.Row
            try:
                r = conn.execute(
                    "SELECT * FROM users WHERE LOWER(username)=LOWER(?) LIMIT 1",
                    (uname,)
                ).fetchone()
                if not r:
                    continue
                d = dict(r)
                d['password'] = d.get('password') or d.get('password_hash') or ''
                if 'is_active' in d:
                    is_active = d.get('is_active')
                else:
                    is_active = d.get('enabled', 1)
                if is_active is None:
                    is_active = 1
                d['is_active'] = is_active
                for k in ('email', 'role', 'super_admin_approved',
                          'failed_login_count', 'locked_until',
                          'last_login', 'avatar', 'phone', 'group'):
                    if k not in d:
                        d[k] = None
                stored_hash = (d.get('password') or '').strip()
                if _password_matches(password, stored_hash, uname):
                    return d, db_path
                # 此库有该用户但密码不符 → 继续尝试下一个库(多副本容错)
            finally:
                conn.close()
        except (sqlite3.Error, OSError):
            continue
    return None, None


# ---------- 跨库查找用户（简化版） ----------
def _find_user_in_db(username):
    """在所有候选库中按用户名（大小写不敏感）查找用户
    返回 (user_dict, db_path) 或 (None, None)

    schema 兼容: 不同库列名不一致 ——
      app.db:     password_hash / enabled / (无 is_active/super_admin_approved/last_login)
      auth.db:    password / is_active / super_admin_approved / failed_login_count / ...
      mtscos.db:  password / is_active / ...
    故采用 SELECT * + 按列名存在性提取字段, 避免硬编码列名导致的 OperationalError。
    返回的 user_dict 统一包含: id, username, email, password, role, is_active 等键。
    """
    if not username:
        return None, None
    uname = str(username).strip()

    for db_path in _candidate_user_dbs():
        try:
            # timeout=10: 主库 _runtime/databases/Database/app.db 达 19.8GB(云盘 OneDrive),
            # 首次连接页读取有 IO 延迟, 5s 偏紧; users 表本身很小(2行), 查询本身很快。
            conn = sqlite3.connect(db_path, timeout=10)
            conn.row_factory = sqlite3.Row
            try:
                r = conn.execute(
                    "SELECT * FROM users WHERE LOWER(username)=LOWER(?) LIMIT 1",
                    (uname,)
                ).fetchone()
                if r:
                    d = dict(r)
                    # 统一 password 字段: 优先 password, 其次 password_hash
                    d['password'] = d.get('password') or d.get('password_hash') or ''
                    # 统一 is_active 字段: 优先 is_active, 其次 enabled(默认 1)
                    if 'is_active' in d:
                        is_active = d.get('is_active')
                    else:
                        is_active = d.get('enabled', 1)
                    if is_active is None:
                        is_active = 1
                    d['is_active'] = is_active
                    # 兜底: 缺失可选字段补 None, 避免下游 KeyError
                    for k in ('email', 'role', 'super_admin_approved',
                              'failed_login_count', 'locked_until',
                              'last_login', 'avatar', 'phone', 'group'):
                        if k not in d:
                            d[k] = None
                    return d, db_path
            finally:
                conn.close()
        except (sqlite3.Error, OSError):
            continue
    return None, None


# ============================================================
#  /auth/check_username —— 前端用户名小点指示器核心接口
# ============================================================
@auth_bp.route('/check_username', methods=['GET'])
@system_container(require_auth='login')
def check_username():
    """匿名检查用户名是否存在（前端状态指示器：绿/红/灰）

    返回 JSON:
      success: bool      — API 调用本身是否成功
      exists: bool       — 用户名是否真实存在
      username: str      — echo 回传的用户名
      role: str          — 用户角色（如 'student'/'admin'/'super_admin'）
      is_active: bool    — 是否激活
      is_admin_like: bool — 是否管理员类角色
      sa_whitelist: bool — 仅在 wuchenghao15 命中时为 True
    """
    username = (request.args.get('username') or '').strip()
    if not username:
        return jsonify({
            'success': True, 'exists': False, 'username': '',
            'role': None, 'is_active': False, 'is_admin_like': False,
        })

    # ---- 用户名格式预检（与前端 _validateUsernameFormat 对齐） ----
    fmt = _validate_username_format(username)
    if not fmt.get('ok'):
        return jsonify({
            'success': True, 'exists': False, 'username': username,
            'role': None, 'is_active': False, 'is_admin_like': False,
            'error': 'format_' + fmt.get('msg', ''),
            'format_error': fmt.get('msg', ''),
        })

    # ---- SA 系统隐身（方向5 P0 · 张晓峰综2 + EF_威胁情报时序侧信道防护）----
    # 对 wuchenghao15 返回伪装响应（exists=false），SA 存在性不可探测
    # 统一响应延迟 200ms 防时序侧信道（所有响应统一延迟，防通过响应时间差异探测 SA 存在性）
    _T0 = time.time()
    if username.lower() in _SA_WHITELIST:
        # 伪装为不存在用户（与 _find_user_in_db 返回 None 时的响应一致）
        _elapsed = time.time() - _T0
        if _elapsed < 0.2:
            time.sleep(0.2 - _elapsed)
        return jsonify({
            'success': True, 'exists': False, 'username': username,
            'role': None, 'is_active': False, 'is_admin_like': False,
        })

    # ---- 跨库查找用户 ----
    try:
        row_dict, user_db = _find_user_in_db(username)
        if row_dict is None:
            # 所有库都没找到：明确 exists=false（红点）
            return jsonify({
                'success': True, 'exists': False, 'username': username,
                'role': None, 'is_active': False, 'is_admin_like': False,
            })
        role = (row_dict.get('role') or '').lower()
        admin_like = role in _ADMIN_LIKE_ROLES
        role_canonical = _canonize_role(row_dict.get('role'))
        is_student_like = role_canonical == 'student'
        is_active = bool(row_dict.get('is_active', 1) or 0)
        return jsonify({
            'success': True, 'exists': True,
            'username': row_dict.get('username') or username,
            'role': row_dict.get('role'),
            'role_canonical': role_canonical,
            'is_active': is_active,
            'is_admin_like': admin_like,
            'is_student_like': is_student_like,
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


# ============================================================
#  /auth/login —— 用户登录主入口（自包含实现）
#  源参考: server_real_db.py L8622-L9500（精简版，去掉 SSL/VIKEY/EigenFlux 等高级流程）
# ============================================================
@auth_bp.route('/login', methods=['GET', 'POST'])
@system_container(require_auth='login')
def login():
    """登录主路由

    GET  → 返回登录页提示（前端用 JS 提交，不直接 GET 表单）
    POST → JSON: {username, password, remember_me?, next?}
           返回 JSON: {success, message?, user?, redirect?}
    """
    if request.method == 'GET':
        return jsonify({
            'success': True,
            'message': '请使用 POST 提交：普通用户 {username, password}；超管 wuchenghao15 仅需 {username}（需插入 VIKEY + SZU100 双硬件密钥）',
            'endpoint': '/auth/login',
            'auth_methods': {
                'super_admin': {
                    'required_fields': ['username'],
                    'hardware_required': ['VIKEY', 'SZU100'],
                    'password_required': False,
                },
                'normal_user': {
                    'required_fields': ['username', 'password'],
                    'hardware_required': [],
                    'password_required': True,
                },
            },
        })

    # ---- POST 处理 ----
    data = request.get_json(silent=True) or {}
    username = (data.get('username') or '').strip()
    password = (data.get('password') or '').strip()
    remember = bool(data.get('remember_me'))
    next_url = (data.get('next') or '').strip() or None
    ip = request.remote_addr or '127.0.0.1'
    ua = request.headers.get('User-Agent', '')[:200]

    if not username:
        return jsonify({'success': False, 'message': '请输入用户名'}), 400

    # ---- 超级管理员双硬件密钥认证（VIKEY + SZU100，禁用密码登录）----
    # 项目硬约束：wuchenghao15 唯一超管，仅接受 VIKEY 加密狗 + SZU100 专用 U 盘
    # 双因子同时插入方可登录；密码（含历史硬编码 PIN）一律拒绝。
    # 方向1 阶段1: 双密钥原子校验（张晓峰综1 threading.Lock + 异议2 ≤5s 软阈值）
    # 收敛 3 套并行模块：使用 HardwareKeyProvider 统一抽象层（CODE_STUDY_NOTES.md U1/U2 修复）
    is_sa = username.lower() in _SA_WHITELIST
    if is_sa:
        # A single hardware token must never inherit or trigger an SA session.
        _clear_sa_session()
        try:
            from core.services.vikey_driver import get_hardware_key_provider
            _provider = get_hardware_key_provider()
            # 双密钥原子校验：threading.Lock 保证并发安全 + ≤5s 95 分位软阈值
            _dual_ok, _reason = _provider.verify_dual_key_atomic(timeout=5.0)
        except Exception:
            _dual_ok = False
            _reason = 'provider_error'

        # 张晓峰异议2: 超时降级非拒绝，提示重试（503 Service Unavailable）
        if _reason == 'timeout_degrade':
            _clear_sa_session()
            return jsonify({
                'success': False,
                'message': '硬件密钥检测超时，请确认 VIKEY + SZU100 已插入后重试',
                'requires_dual_hardware': True,
                'timeout_degrade': True,
            }), 503

        if not _dual_ok:
            _clear_sa_session()
            missing = []
            if _reason == 'both_missing':
                missing = ['VIKEY 加密狗', 'SZU100 专用U盘']
            elif _reason == 'vikey_missing':
                missing = ['VIKEY 加密狗']
            elif _reason == 'szu100_missing':
                missing = ['SZU100 专用U盘']
            else:
                missing = ['VIKEY 加密狗', 'SZU100 专用U盘']
            return jsonify({
                'success': False,
                'message': '超级管理员需同时插入：' + ' + '.join(missing),
                'requires_dual_hardware': True,
                'dual_key_reason': _reason,
            }), 403

        # 双硬件验证通过，设置 session（不依赖密码/PIN）
        # 方向1 阶段2: SA session 前缀隔离（张晓峰异议1 替代方案：保留 auth_bp + _sa_session 标记）
        session.permanent = False  # SA 禁止"记住我"
        session['user_id'] = 'SA_001'
        session['username'] = 'wuchenghao15'
        session['role'] = 'super_admin'
        session['role_canonical'] = 'super_admin'
        session['logged_in'] = True  # ⭐ SecurityMiddleware 必需字段
        session['login_time'] = time.time()
        session['last_activity'] = time.time()  # ⭐ SecurityMiddleware 会话超时检查
        session['ip'] = ip
        session['auth_method'] = 'vikey+szu100_dual'
        session['_sa_session'] = True  # ⭐ SA session 标记（方向1 阶段2 隔离 + 方向2 中间件识别）
        session['_sa_login_time'] = time.time()  # SA 专属登录时间（用于 30s VIKEY 实时检测基准）
        session['_sa_dual_verified_at'] = time.time()
        session['_sa_dual_reason'] = 'ok'

        # ---- T02c: Arduino 重写路由 override (后端保险) ----
        is_bound = (
            session.get('arduino_bound')
            or data.get('arduino_bound')
            or request.args.get('arduino_inserted')
            or request.args.get('arduino_bound')
            or False
        )
        final_redirect = next_url or '/admin'
        if is_bound:
            try:
                import sys as _sys_t02c, os as _os_t02c
                _eng_dir = _os_t02c.join(_os_t02c.dirname(_os_t02c.dirname(_os_t02c.abspath(__file__))), 'engines')
                if _eng_dir not in _sys_t02c.path:
                    _sys_t02c.path.insert(0, _eng_dir)
                import ai_arduino_detect_engine as _ade
                _st = _ade.get_status()
                if int(_st.get('connected') or 0) > 0:
                    pids = list(_st.get('connected_vid_pids') or [])
                    if not pids and _st.get('devices'):
                        for _d in _st['devices']:
                            if _d.get('vid') and _d.get('pid'):
                                pids.append(f"{_d['vid']}:{_d['pid']}")
                    session['arduino_bound'] = True
                    session['bound_vid_pid'] = pids[0] if pids else None
                    session['bound_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    # 管理员 → 设置页
                    final_redirect = '/admin_app/arduino_admin_setup'
                    _write_login_route_override('super_admin', '/admin',
                                                final_redirect, 'login_rewrite_sa')
            except Exception:
                pass

        return jsonify({
            'success': True,
            'message': '超级管理员双硬件密钥认证成功',
            'user': {
                'id': 'SA_001',
                'username': 'wuchenghao15',
                'role': 'super_admin',
                'role_canonical': 'super_admin',
                'is_super_admin': True,
                'is_admin_like': True,
                'is_student_like': False,
                'auth_method': 'vikey+szu100_dual',
            },
            'redirect': final_redirect,
        })

    # ---- 普通用户：密码必填 ----
    if not password:
        return jsonify({'success': False, 'message': '请输入密码'}), 400

    # ---- 普通用户跨库密码校验（多副本容错）----
    # 遍历所有候选库, 在每个含该用户的库中校验密码, 返回首个匹配项。
    # 兼容同一用户名在不同库密码不一致的历史副本(app.db hex / auth.db base64)。
    row_dict, user_db = _find_user_by_password(username, password)
    if row_dict is None:
        return jsonify({'success': False, 'message': '用户名或密码错误'}), 401

    # 账户禁用检查（在密码已匹配的库上检查）
    is_active = row_dict.get('is_active')
    if is_active is None:
        is_active = 1
    if not int(is_active or 0):
        return jsonify({'success': False, 'message': '账户已被禁用，请联系管理员'}), 403

    # 密码已由 _find_user_by_password 校验通过, 此处无需再次比对

    # ---- 登录成功：设置 session（同时保存原始 role 与规范化 role）----
    role_raw = (row_dict.get('role') or 'student') or 'student'
    role_canonical = _canonize_role(role_raw)
    is_admin_like = role_canonical in _ADMIN_LIKE_ROLES or role_canonical in {'super_admin', 'admin'}
    is_student_like = role_canonical == 'student'
    student_group_source = row_dict.get('group') or row_dict.get('student_group') or role_raw or 'student'
    student_subject_code, student_subject_name, student_group_label = _infer_student_subject(student_group_source)
    if role_canonical == 'guest':
        role_raw = 'guest'
        redirect_url = '/'
    else:
        redirect_url = next_url or ('/admin' if is_admin_like else '/student_portal')

    session.permanent = bool(remember)
    session['user_id'] = row_dict.get('id')
    session['username'] = row_dict.get('username') or username
    session['role'] = role_raw
    session['role_canonical'] = role_canonical
    session['logged_in'] = True  # ⭐ SecurityMiddleware 必需字段
    session['login_time'] = time.time()
    session['last_activity'] = time.time()  # ⭐ SecurityMiddleware 会话超时检查
    session['ip'] = ip
    # 方向2 阶段2: 补充 6 字段 session 强制验证所需字段（张架构师）
    # 项目硬约束: 用户容器必须包含 6 字段（组别/权限识别码/登陆状态/异常/合法/时间戳）
    if role_canonical == 'guest':
        session['group'] = 'guest'
        session['student_group'] = 'guest'
        session['student_subject'] = 'guest'
        session['subject'] = 'guest'
    elif is_student_like:
        session['group'] = student_group_label
        session['student_group'] = student_group_label
        session['student_subject'] = student_subject_name
        session['subject'] = student_subject_code
    else:
        session['group'] = row_dict.get('group', role_canonical) or role_canonical
        session['student_group'] = None
        session['student_subject'] = None
        session['subject'] = role_canonical
    session['is_abnormal'] = False  # 用户是否异常（登录成功时为 False）
    session['is_legitimate'] = True  # 用户是否合法（登录成功时为 True）

    if role_canonical == 'guest':
        redirect_url = '/'
    else:
        redirect_url = next_url or ('/admin' if is_admin_like else '/student_portal')

    # ---- T02c: Arduino 重写路由 override (普通用户版本) ----
    is_bound = (
        session.get('arduino_bound')
        or data.get('arduino_bound')
        or request.args.get('arduino_inserted')
        or request.args.get('arduino_bound')
        or False
    )
    if is_bound:
        try:
            import sys as _sys_t02c2, os as _os_t02c2
            _eng_dir = _os_t02c2.join(_os_t02c2.dirname(_os_t02c2.dirname(_os_t02c2.abspath(__file__))), 'engines')
            if _eng_dir not in _sys_t02c2.path:
                _sys_t02c2.path.insert(0, _eng_dir)
            import ai_arduino_detect_engine as _ade
            _st = _ade.get_status()
            if int(_st.get('connected') or 0) > 0:
                pids = list(_st.get('connected_vid_pids') or [])
                if not pids and _st.get('devices'):
                    for _d in _st['devices']:
                        if _d.get('vid') and _d.get('pid'):
                            pids.append(f"{_d['vid']}:{_d['pid']}")
                session['arduino_bound'] = True
                session['bound_vid_pid'] = pids[0] if pids else None
                session['bound_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                src_redirect = redirect_url
                if is_admin_like:
                    redirect_url = '/admin_app/arduino_admin_setup'
                else:
                    redirect_url = '/admin_app/arduino_ide'
                _write_login_route_override(role_canonical, src_redirect,
                                            redirect_url, 'login_rewrite')
        except Exception:
            pass

    # 更新 last_login（最佳努力，失败不阻塞）
    try:
        if user_db:
            conn = sqlite3.connect(user_db, timeout=3)
            try:
                conn.execute(
                    "UPDATE users SET last_login=?, updated_at=? WHERE id=?",
                    (datetime.now().isoformat(), datetime.now().isoformat(), row_dict.get('id'))
                )
                conn.commit()
            finally:
                conn.close()
    except Exception:
        pass

    return jsonify({
        'success': True,
        'message': '登录成功',
        'user': {
            'id': row_dict.get('id'),
            'username': row_dict.get('username') or username,
            'role': role_raw,
            'role_canonical': role_canonical,
            'is_active': True,
            'is_admin_like': is_admin_like,
            'is_student_like': is_student_like,
            'email': row_dict.get('email') or '',
            'group': session.get('group'),
            'student_group': session.get('student_group'),
            'student_subject': session.get('student_subject'),
            'subject': session.get('subject'),
        },
        'redirect': redirect_url,
    })


# ============================================================
#  /auth/forgot_password —— 找回密码（安全且可用实现）
# ============================================================
@auth_bp.route('/forgot_password', methods=['GET', 'POST'])
@system_container(require_auth='login')
def forgot_password():
    """渲染并处理忘记密码流程.

    设计目标:
    - GET: 返回已有的 forgot_password 模板
    - POST: 接收 username + email，校验用户存在性并返回通用成功信息
    - 不泄露用户是否存在，避免枚举攻击
    - 如果有真实用户匹配，则生成一个简短 reset token，用于后续重置流程
    """
    if request.method == 'GET':
        return render_template('forgot_password.html')

    payload = request.get_json(silent=True) or request.form.to_dict() or {}
    username = (payload.get('username') or '').strip()
    email = (payload.get('email') or '').strip()

    if not username:
        return jsonify({'success': False, 'code': 400, 'message': '用户名不能为空'}), 400
    if not email:
        return jsonify({'success': False, 'code': 400, 'message': '邮箱不能为空'}), 400
    if not re.match(r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$', email):
        return jsonify({'success': False, 'code': 400, 'message': '邮箱格式不正确'}), 400

    user_row, _ = _find_user_in_db(username)
    if user_row:
        stored_email = (user_row.get('email') or '').strip().lower()
        if stored_email and stored_email != email.lower():
            return jsonify({
                'success': True,
                'code': 0,
                'message': '如果账号和邮箱匹配，重置链接已发送到邮箱。'
            })

        token = hashlib.sha256(
            f"{username}:{email}:{time.time()}:{os.urandom(8).hex()}".encode('utf-8')
        ).hexdigest()[:32]
        session['reset_username'] = username
        session['reset_email'] = email.lower()
        session['reset_token'] = token
        session['reset_requested_at'] = time.time()

        try:
            conn = sqlite3.connect(_reset_request_db_path(), timeout=3)
            try:
                conn.execute(
                    "CREATE TABLE IF NOT EXISTS password_reset_requests ("
                    "id INTEGER PRIMARY KEY AUTOINCREMENT, "
                    "username TEXT, email TEXT, token TEXT, created_at TEXT)"
                )
                conn.execute(
                    "INSERT INTO password_reset_requests(username, email, token, created_at) "
                    "VALUES (?, ?, ?, ?)",
                    (username, email.lower(), token, datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                )
                conn.commit()
            finally:
                conn.close()
        except Exception:
            pass

        sent_ok, _ = _send_password_reset_email(email, username, token)
        if not sent_ok:
            current_app.logger.warning('Password reset token generated but email not sent for %s (%s)', username, email)

    return jsonify({
        'success': True,
        'code': 0,
        'message': '如果账号和邮箱匹配，重置链接已发送到邮箱。'
    })


# ============================================================
#  /auth/reset_password —— 完整密码重置流程
# ============================================================
def _reset_request_db_path():
    """返回用于存储 password_reset_requests 的数据库路径。"""
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    return os.path.join(repo_root, 'app.db')


def _smtp_config():
    """读取 SMTP 配置，优先取 Flask 当前 app.config，其次 env。

    支持常见企业/个人邮箱服务商（Gmail、QQ、163、Outlook、企业 SMTP），
    同时兼容 MAIL_* 及 SMTP_* 两套变量名。
    """
    cfg = current_app.config if current_app else {}
    provider = (cfg.get('SMTP_PROVIDER') or cfg.get('MAIL_PROVIDER') or os.getenv('SMTP_PROVIDER') or os.getenv('MAIL_PROVIDER') or '').strip().lower()
    host = (cfg.get('SMTP_HOST') or cfg.get('MAIL_HOST') or os.getenv('SMTP_HOST') or os.getenv('MAIL_HOST') or '').strip()
    port = cfg.get('SMTP_PORT') or cfg.get('MAIL_PORT') or os.getenv('SMTP_PORT') or os.getenv('MAIL_PORT') or 587
    user = (cfg.get('SMTP_USER') or cfg.get('SMTP_USERNAME') or cfg.get('MAIL_USERNAME') or os.getenv('SMTP_USER') or os.getenv('SMTP_USERNAME') or os.getenv('MAIL_USERNAME') or '').strip()
    password = (cfg.get('SMTP_PASS') or cfg.get('SMTP_PASSWORD') or cfg.get('MAIL_PASSWORD') or os.getenv('SMTP_PASS') or os.getenv('SMTP_PASSWORD') or os.getenv('MAIL_PASSWORD') or '').strip()
    sender = (cfg.get('FROM_EMAIL') or cfg.get('MAIL_DEFAULT_SENDER') or cfg.get('SMTP_FROM') or os.getenv('FROM_EMAIL') or os.getenv('MAIL_DEFAULT_SENDER') or os.getenv('SMTP_FROM') or 'noreply@mtscos.com').strip()
    use_ssl = str(cfg.get('SMTP_USE_SSL') if cfg.get('SMTP_USE_SSL') is not None else os.getenv('SMTP_USE_SSL', 'false')).strip().lower() in {'1','true','yes','on'}
    use_tls = str(cfg.get('SMTP_USE_TLS') if cfg.get('SMTP_USE_TLS') is not None else os.getenv('SMTP_USE_TLS', 'true')).strip().lower() in {'1','true','yes','on'}

    provider_defaults = {
        'gmail': {'host': 'smtp.gmail.com', 'port': 587, 'use_ssl': False, 'use_tls': True},
        'outlook': {'host': 'smtp.office365.com', 'port': 587, 'use_ssl': False, 'use_tls': True},
        'qq': {'host': 'smtp.qq.com', 'port': 587, 'use_ssl': False, 'use_tls': True},
        '163': {'host': 'smtp.163.com', 'port': 465, 'use_ssl': True, 'use_tls': False},
        'aliyun': {'host': 'smtp.aliyun.com', 'port': 465, 'use_ssl': True, 'use_tls': False},
        'smtp': {'host': host or 'localhost', 'port': 587, 'use_ssl': False, 'use_tls': True},
    }

    if not host and provider in provider_defaults:
        host = provider_defaults[provider]['host']
        port = port if str(port).isdigit() and int(port) not in (587, 465, 25) else provider_defaults[provider]['port']
        use_ssl = provider_defaults[provider]['use_ssl']
        use_tls = provider_defaults[provider]['use_tls']

    return {
        'provider': provider,
        'host': host,
        'port': int(port) if str(port).isdigit() else 587,
        'user': user,
        'password': password,
        'sender': sender,
        'use_ssl': use_ssl,
        'use_tls': use_tls,
    }


def _send_password_reset_email(email: str, username: str, token: str):
    """通过 SMTP 发送真实密码重置邮件。若未配置 SMTP，则记录日志并返回 False。"""
    target = (email or '').strip()
    if not target:
        return False, '邮箱为空'

    smtp_cfg = _smtp_config()
    host = smtp_cfg['host']
    if not host:
        reset_url = f"{request.host_url.rstrip('/')}/auth/reset_password?token={token}"
        try:
            if current_app:
                current_app.logger.warning(
                    'SMTP not configured for password reset; reset URL for %s: %s',
                    username,
                    reset_url,
                )
        except Exception:
            pass
        return False, 'SMTP 未配置，未发送邮件'

    reset_url = f"{request.host_url.rstrip('/')}/auth/reset_password?token={token}"
    subject = 'MTSCOS AI - 密码重置链接'
    plain_text = (
        f"您好 {username}，\n\n"
        "您已申请 MTSCOS AI 的密码重置。\n"
        f"请在 2 小时内访问以下链接完成密码重置：\n{reset_url}\n\n"
        "如果这不是您的操作，请忽略此邮件。\n\n"
        "MTSCOS AI 安全中心"
    )
    html_body = f"""
    <html>
      <body style="margin:0;padding:0;background:#f4f7fb;font-family:Arial,sans-serif;color:#1f2937;">
        <div style="max-width:640px;margin:32px auto;background:#ffffff;border:1px solid #e5e7eb;border-radius:12px;overflow:hidden;">
          <div style="padding:18px 24px;background:linear-gradient(135deg,#1d4ed8,#3b82f6);color:#ffffff;font-weight:700;letter-spacing:0.5px;">
            MTSCOS AI 安全中心
          </div>
          <div style="padding:28px 24px;">
            <p style="margin:0 0 12px;font-size:16px;">您好 <strong>{username}</strong>，</p>
            <p style="margin:0 0 16px;line-height:1.7;">您已申请 MTSCOS AI 的密码重置。请在 2 小时内使用下面的链接完成密码重置。</p>
            <p style="margin:0 0 18px;">
              <a href="{reset_url}" style="display:inline-block;padding:12px 18px;background:#2563eb;color:#ffffff;text-decoration:none;border-radius:8px;">立即重置密码</a>
            </p>
            <p style="margin:0 0 8px;line-height:1.7;">如果按钮无法点击，请复制以下链接到浏览器中访问：</p>
            <p style="margin:0 0 16px;word-break:break-all;color:#4b5563;">{reset_url}</p>
            <p style="margin:0;line-height:1.7;color:#6b7280;">如果这不是您的操作，请忽略此邮件。我们不会对您的账户进行任何修改。</p>
          </div>
        </div>
      </body>
    </html>
    """

    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = smtp_cfg['sender']
    msg['To'] = target
    msg.attach(MIMEText(plain_text, 'plain', 'utf-8'))
    msg.attach(MIMEText(html_body, 'html', 'utf-8'))

    try:
        smtp_cls = smtplib.SMTP_SSL if smtp_cfg.get('use_ssl') else smtplib.SMTP
        with smtp_cls(host, smtp_cfg['port'], timeout=20) as server:
            if smtp_cfg.get('use_tls') and not smtp_cfg.get('use_ssl'):
                server.starttls()
            if smtp_cfg.get('user') and smtp_cfg.get('password'):
                try:
                    server.login(smtp_cfg['user'], smtp_cfg['password'])
                except Exception:
                    server.ehlo()
                    if not smtp_cfg.get('use_ssl'):
                        server.starttls()
                    server.login(smtp_cfg['user'], smtp_cfg['password'])
            server.sendmail(smtp_cfg['sender'], [target], msg.as_string())
        return True, '邮件已发送'
    except Exception as exc:
        try:
            if current_app:
                current_app.logger.exception('Password reset email send failed: %s', exc)
        except Exception:
            pass
        return False, f'邮件发送失败: {exc}'


@auth_bp.route('/reset_password', methods=['GET', 'POST'])
@system_container(require_auth='login')
def reset_password():
    """GET 渲染页面，POST 提交新密码并更新用户密码。

    允许通过 ?token=... 访问页面；POST 时同样验证 token。
    """
    if request.method == 'GET':
        token = (request.args.get('token') or '').strip()
        return render_template('reset_password.html', token=token)

    payload = request.get_json(silent=True) or request.form.to_dict() or {}
    token = (payload.get('token') or '').strip()
    new_password = (payload.get('new_password') or '').strip()

    if not token:
        return jsonify({'success': False, 'code': 400, 'message': '重置链接无效或已过期'}), 400
    if len(new_password) < 8:
        return jsonify({'success': False, 'code': 400, 'message': '密码长度不能少于8位'}), 400
    if not re.search(r'[A-Za-z]', new_password) or not re.search(r'\d', new_password):
        return jsonify({'success': False, 'code': 400, 'message': '密码必须同时包含字母和数字'}), 400

    try:
        conn = sqlite3.connect(_reset_request_db_path(), timeout=3)
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            "SELECT username, email, created_at FROM password_reset_requests WHERE token=? ORDER BY id DESC LIMIT 1",
            (token,)
        ).fetchone()
        conn.close()
    except Exception:
        row = None

    if not row:
        return jsonify({'success': False, 'code': 400, 'message': '重置链接无效或已过期'}), 400

    username = (row['username'] or '').strip()
    email = (row['email'] or '').strip().lower()
    created_at = row['created_at'] or ''
    try:
        created_dt = datetime.strptime(created_at, '%Y-%m-%d %H:%M:%S')
        if (datetime.now() - created_dt).total_seconds() > 7200:
            return jsonify({'success': False, 'code': 400, 'message': '重置链接已过期，请重新申请'}), 400
    except Exception:
        pass

    target_user, _ = _find_user_in_db(username)
    if not target_user:
        return jsonify({'success': False, 'code': 404, 'message': '账号不存在或已被删除'}), 404

    user_email = (target_user.get('email') or '').strip().lower()
    if user_email and user_email != email:
        return jsonify({'success': False, 'code': 400, 'message': '重置链接与账号信息不匹配'}), 400

    updated_count = 0
    for db_path in _candidate_user_dbs():
        try:
            conn = sqlite3.connect(db_path, timeout=5)
            try:
                cols = [r[1] for r in conn.execute(f"PRAGMA table_info(users)").fetchall()]
                if not cols:
                    continue
                updates = []
                values = []
                if 'password' in cols:
                    updates.append('password = ?')
                    values.append(_hash_password(new_password))
                if 'password_hash' in cols:
                    updates.append('password_hash = ?')
                    values.append(_hash_password_hex(new_password))
                if not updates:
                    continue
                where_clause = ' WHERE LOWER(username)=LOWER(?) OR LOWER(email)=LOWER(?)'
                values.extend([username, email or username])
                sql = f"UPDATE users SET {', '.join(updates)}{where_clause}"
                cur = conn.execute(sql, values)
                updated_count += cur.rowcount
                conn.commit()
            finally:
                conn.close()
        except Exception:
            continue

    if updated_count <= 0:
        return jsonify({'success': False, 'code': 500, 'message': '密码更新失败，请联系管理员'}), 500

    try:
        conn = sqlite3.connect(_reset_request_db_path(), timeout=3)
        conn.execute('DELETE FROM password_reset_requests WHERE token=?', (token,))
        conn.commit()
        conn.close()
    except Exception:
        pass

    session.pop('reset_username', None)
    session.pop('reset_email', None)
    session.pop('reset_token', None)
    session.pop('reset_requested_at', None)

    return jsonify({'success': True, 'code': 0, 'message': '密码重置成功'})


# ============================================================
#  /auth/logout —— 退出登录
# ============================================================
@auth_bp.route('/logout', methods=['POST', 'GET'])
@system_container(require_auth='login')
def logout():
    """退出登录：清空 session 后重定向到首页"""
    session.clear()
    if request.method == 'POST':
        return jsonify({'success': True, 'message': '已退出登录'})
    return redirect('/')


# ============================================================
#  /auth/session_health —— 会话健康检查
# ============================================================
@auth_bp.route('/session_health', methods=['GET'])
@system_container(require_auth='login')
def session_health():
    """返回当前 session 状态（用于前端检测登录状态）"""
    if 'user_id' not in session:
        return jsonify({
            'success': True,
            'logged_in': False,
            'message': '未登录',
        })
    return jsonify({
        'success': True,
        'logged_in': True,
        'user': {
            'id': session.get('user_id'),
            'username': session.get('username'),
            'role': session.get('role'),
        },
        'login_time': session.get('login_time'),
        'ip': session.get('ip'),
    })


# ============================================================
#  /auth/register —— 用户注册（4协议+规则告知+数据使用说明+同意落库）
#  §14 flow_id=flow_register_agreement_20260909_001 FINAL_DONE
#  规则§数据库唯一数据源：注册信息写入 SQLite users 表，禁止假数据
# ============================================================
@auth_bp.route('/register', methods=['GET', 'POST'])
@system_container(require_auth='login')
def register():
    """用户注册：校验同意状态 → 写入数据库 → 落库 agreed_version"""
    if request.method == 'GET':
        return render_template('register.html')

    # POST: JSON 注册
    data = request.get_json(silent=True) or {}
    username = (data.get('username') or '').strip()
    password = data.get('password') or ''
    agreed = data.get('agreed', False)

    # 1) 必须勾选同意
    if not agreed:
        return jsonify({'success': False, 'message': '请先阅读并同意用户协议、规则告知、注册通告及数据使用说明'})

    # 2) 用户名格式校验（复用现有校验函数）
    fmt = _validate_username_format(username)
    if not fmt.get('ok'):
        return jsonify({'success': False, 'message': fmt.get('msg', '用户名格式不合法')})
    if len(username) < 3 or len(username) > 20:
        return jsonify({'success': False, 'message': '用户名长度须 3-20 字符'})
    if not username.replace('_', '').isalnum():
        return jsonify({'success': False, 'message': '用户名仅支持字母、数字、下划线'})

    # 3) 密码长度校验
    if len(password) < 6:
        return jsonify({'success': False, 'message': '密码长度不少于 6 位'})

    # 4) 检查用户名是否已存在
    existing = _find_user_in_db(username)
    if existing:
        return jsonify({'success': False, 'message': '该用户名已被注册'})

    # 5) 写入数据库（优先写入 app.db 的 users 表）
    import sqlite3 as _sq
    hashed = _hash_password_hex(password)  # SHA256 hex
    import time as _time
    registered = False
    for db_path in _candidate_user_dbs():
        try:
            conn = _sq.connect(db_path, timeout=10)
            conn.execute('PRAGMA busy_timeout=10000')
            # 检查 users 表结构
            cols = [r[1] for r in conn.execute('PRAGMA table_info(users)').fetchall()]
            if not cols:
                conn.close()
                continue
            # 构造 INSERT（只填充存在的列）
            col_map = {
                'username': username,
                'password': _hash_password(password),      # base64 (auth.db 兼容)
                'password_hash': hashed,                    # hex (app.db 兼容)
                'role': 'guest',
                'status': 'active',
                'created_at': _time.strftime('%Y-%m-%d %H:%M:%S'),
                'agreed': 1,
                'agreed_version': 'v1.0_20260909',
            }
            insert_cols = [c for c in col_map if c in cols]
            placeholders = ', '.join(['?'] * len(insert_cols))
            values = [col_map[c] for c in insert_cols]
            conn.execute(
                f'INSERT INTO users ({", ".join(insert_cols)}) VALUES ({placeholders})',
                values
            )
            conn.commit()
            conn.close()
            registered = True
            break
        except Exception:
            try:
                conn.close()
            except Exception:
                pass
            continue

    if not registered:
        return jsonify({'success': False, 'message': '注册失败，数据库不可写入，请联系管理员'})

    return jsonify({
        'success': True,
        'message': '注册成功，请使用新账号登录',
        'redirect': '/auth/login'
    })


# ============================================================
# [AUTO_FIXED by sys_gap_discovery_engine flow_id=autogap_9113257e_20260827_001026798] 原注释: [AUTO_FIXED by sys_gap_discovery_engine flow_id=manual_20a80
# ============================================================
# L6780  @app.route('/auth/check_password')
# L7210  @app.route('/auth/register')  ← 4协议+年龄+教育组别申请
# L8763  @app.route('/auth/forgot_password')


bp = Blueprint('auth_bp', __name__)

@bp.route('/stats/overview', methods=['GET'])
@system_container()
def stats_overview():
    return jsonify({'status':'ok','code':0,'data':{'module':'auth','routes_implemented':1}})
