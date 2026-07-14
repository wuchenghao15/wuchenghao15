# -*- coding: utf-8 -*-
"""
用户认证增强API - 多因素认证、权限矩阵管理、用户分组管理
"""

from flask import Blueprint, jsonify, request, session
from app.middlewares.permission_decorators import require_login, require_admin
import sqlite3
import logging
import os
import json
import hashlib
import random
import string
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

user_auth_enhanced_api = Blueprint('user_auth_enhanced_api', __name__)

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'app.db')


def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def create_response(code=200, message='success', data=None):
    return jsonify({
        'code': code,
        'message': message,
        'data': data,
        'timestamp': datetime.now().isoformat()
    })


def create_tables():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_groups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                group_name TEXT UNIQUE NOT NULL,
                description TEXT,
                permissions TEXT DEFAULT '[]',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_group_members (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                group_id INTEGER NOT NULL,
                joined_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (group_id) REFERENCES user_groups(id),
                UNIQUE(user_id, group_id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS mfa_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER UNIQUE NOT NULL,
                mfa_enabled INTEGER DEFAULT 0,
                mfa_secret TEXT,
                backup_codes TEXT,
                last_used TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS permission_matrix (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                role TEXT NOT NULL,
                resource TEXT NOT NULL,
                action TEXT NOT NULL,
                allowed INTEGER DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(role, resource, action)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS login_attempts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                username TEXT,
                ip_address TEXT,
                attempt_time TEXT DEFAULT CURRENT_TIMESTAMP,
                success INTEGER DEFAULT 0,
                failure_reason TEXT
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS session_tokens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                token TEXT UNIQUE NOT NULL,
                device_info TEXT,
                ip_address TEXT,
                expires_at TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')

        conn.commit()
        conn.close()
        logger.info("✓ 用户认证增强表创建完成")
    except Exception as e:
        logger.error(f"✗ 创建用户认证增强表失败: {e}")


create_tables()


@user_auth_enhanced_api.route('/api/auth/enhanced/login', methods=['POST'])
def enhanced_login():
    try:
        data = request.get_json() or {}
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()
        mfa_code = data.get('mfa_code', '')

        if not username or not password:
            return create_response(400, '请输入用户名和密码')

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
        user = cursor.fetchone()

        if not user:
            cursor.execute('INSERT INTO login_attempts (username, ip_address, success, failure_reason) VALUES (?, ?, ?, ?)',
                         (username, request.remote_addr, 0, '用户不存在'))
            conn.commit()
            conn.close()
            return create_response(401, '用户名或密码错误')

        from app import verify_password
        if not verify_password(user['password'], password):
            cursor.execute('INSERT INTO login_attempts (user_id, username, ip_address, success, failure_reason) VALUES (?, ?, ?, ?, ?)',
                         (user['id'], username, request.remote_addr, 0, '密码错误'))
            conn.commit()
            conn.close()
            return create_response(401, '用户名或密码错误')

        cursor.execute('SELECT mfa_enabled FROM mfa_settings WHERE user_id = ?', (user['id'],))
        mfa_row = cursor.fetchone()
        mfa_enabled = mfa_row['mfa_enabled'] if mfa_row else 0

        if mfa_enabled and not mfa_code:
            conn.close()
            return create_response(200, '需要多因素认证', {'requires_mfa': True, 'user_id': user['id']})

        if mfa_enabled and mfa_code:
            cursor.execute('SELECT mfa_secret FROM mfa_settings WHERE user_id = ?', (user['id'],))
            mfa_secret_row = cursor.fetchone()
            if mfa_secret_row:
                import pyotp
                totp = pyotp.TOTP(mfa_secret_row['mfa_secret'])
                if not totp.verify(mfa_code):
                    cursor.execute('INSERT INTO login_attempts (user_id, username, ip_address, success, failure_reason) VALUES (?, ?, ?, ?, ?)',
                                 (user['id'], username, request.remote_addr, 0, 'MFA验证码错误'))
                    conn.commit()
                    conn.close()
                    return create_response(401, 'MFA验证码错误')

        session['user_id'] = user['id']
        session['username'] = user['username']
        session['role'] = user['role']

        token = ''.join(random.choices(string.ascii_letters + string.digits, k=64))
        expires_at = (datetime.now() + timedelta(hours=24)).isoformat()
        cursor.execute('INSERT INTO session_tokens (user_id, token, device_info, ip_address, expires_at) VALUES (?, ?, ?, ?, ?)',
                     (user['id'], token, request.headers.get('User-Agent', ''), request.remote_addr, expires_at))

        cursor.execute('INSERT INTO login_attempts (user_id, username, ip_address, success) VALUES (?, ?, ?, ?)',
                     (user['id'], username, request.remote_addr, 1))
        conn.commit()
        conn.close()

        return create_response(200, '登录成功', {
            'user_id': user['id'],
            'username': user['username'],
            'role': user['role'],
            'token': token,
            'expires_at': expires_at
        })

    except Exception as e:
        logger.error(f"增强登录失败: {e}")
        return create_response(500, '登录失败')


@user_auth_enhanced_api.route('/api/auth/mfa/enable', methods=['POST'])
@require_login
def enable_mfa():
    try:
        user_id = session.get('user_id')
        conn = get_db_connection()
        cursor = conn.cursor()

        import pyotp
        secret = pyotp.random_base32()
        totp = pyotp.TOTP(secret)
        provisioning_url = totp.provisioning_uri(session.get('username'), issuer_name='MTSCOS')

        backup_codes = [''.join(random.choices(string.digits, k=8)) for _ in range(5)]
        backup_codes_json = json.dumps(backup_codes)

        cursor.execute('''
            INSERT OR REPLACE INTO mfa_settings (user_id, mfa_enabled, mfa_secret, backup_codes, updated_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, 0, secret, backup_codes_json, datetime.now().isoformat()))
        conn.commit()
        conn.close()

        return create_response(200, 'MFA配置生成成功', {
            'secret': secret,
            'provisioning_url': provisioning_url,
            'backup_codes': backup_codes,
            'qr_code_url': f'otpauth://totp/MTSCOS:{session.get("username")}?secret={secret}&issuer=MTSCOS'
        })

    except Exception as e:
        logger.error(f"启用MFA失败: {e}")
        return create_response(500, '启用MFA失败')


@user_auth_enhanced_api.route('/api/auth/mfa/verify', methods=['POST'])
@require_login
def verify_mfa():
    try:
        user_id = session.get('user_id')
        data = request.get_json() or {}
        mfa_code = data.get('mfa_code', '')

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT mfa_secret FROM mfa_settings WHERE user_id = ?', (user_id,))
        row = cursor.fetchone()

        if not row:
            conn.close()
            return create_response(400, 'MFA未配置')

        import pyotp
        totp = pyotp.TOTP(row['mfa_secret'])
        if not totp.verify(mfa_code):
            conn.close()
            return create_response(400, 'MFA验证码无效')

        cursor.execute('UPDATE mfa_settings SET mfa_enabled = 1, updated_at = ? WHERE user_id = ?',
                     (datetime.now().isoformat(), user_id))
        conn.commit()
        conn.close()

        return create_response(200, 'MFA验证成功，已启用多因素认证')

    except Exception as e:
        logger.error(f"验证MFA失败: {e}")
        return create_response(500, '验证MFA失败')


@user_auth_enhanced_api.route('/api/auth/mfa/disable', methods=['POST'])
@require_login
def disable_mfa():
    try:
        user_id = session.get('user_id')
        data = request.get_json() or {}
        mfa_code = data.get('mfa_code', '')

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT mfa_secret FROM mfa_settings WHERE user_id = ?', (user_id,))
        row = cursor.fetchone()

        if not row:
            conn.close()
            return create_response(400, 'MFA未配置')

        import pyotp
        totp = pyotp.TOTP(row['mfa_secret'])
        if not totp.verify(mfa_code):
            conn.close()
            return create_response(400, 'MFA验证码无效')

        cursor.execute('UPDATE mfa_settings SET mfa_enabled = 0, updated_at = ? WHERE user_id = ?',
                     (datetime.now().isoformat(), user_id))
        conn.commit()
        conn.close()

        return create_response(200, 'MFA已禁用')

    except Exception as e:
        logger.error(f"禁用MFA失败: {e}")
        return create_response(500, '禁用MFA失败')


@user_auth_enhanced_api.route('/api/groups', methods=['GET'])
@require_admin
def get_groups():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT id, group_name, description, created_at FROM user_groups ORDER BY created_at DESC')
        groups = []
        for row in cursor.fetchall():
            cursor.execute('SELECT COUNT(*) FROM user_group_members WHERE group_id = ?', (row['id'],))
            member_count = cursor.fetchone()[0] or 0
            groups.append({
                'id': row['id'],
                'group_name': row['group_name'],
                'description': row['description'] or '',
                'member_count': member_count,
                'created_at': row['created_at'] or ''
            })
        conn.close()
        return create_response(200, 'success', {'groups': groups})

    except Exception as e:
        logger.error(f"获取用户组列表失败: {e}")
        return create_response(500, '获取用户组列表失败')


@user_auth_enhanced_api.route('/api/groups', methods=['POST'])
@require_admin
def create_group():
    try:
        data = request.get_json() or {}
        group_name = data.get('group_name', '').strip()
        description = data.get('description', '')
        permissions = data.get('permissions', [])

        if not group_name:
            return create_response(400, '组名称不能为空')

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM user_groups WHERE group_name = ?', (group_name,))
        if cursor.fetchone():
            conn.close()
            return create_response(400, '组名称已存在')

        cursor.execute('INSERT INTO user_groups (group_name, description, permissions, created_at) VALUES (?, ?, ?, ?)',
                     (group_name, description, json.dumps(permissions), datetime.now().isoformat()))
        group_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return create_response(201, '用户组创建成功', {'group_id': group_id, 'group_name': group_name})

    except Exception as e:
        logger.error(f"创建用户组失败: {e}")
        return create_response(500, '创建用户组失败')


@user_auth_enhanced_api.route('/api/groups/<int:group_id>', methods=['GET', 'PUT', 'DELETE'])
@require_admin
def group_detail(group_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        if request.method == 'GET':
            cursor.execute('SELECT id, group_name, description, permissions, created_at FROM user_groups WHERE id = ?', (group_id,))
            row = cursor.fetchone()
            if not row:
                conn.close()
                return create_response(404, '用户组不存在')

            cursor.execute('SELECT user_id FROM user_group_members WHERE group_id = ?', (group_id,))
            member_ids = [r['user_id'] for r in cursor.fetchall()]

            conn.close()
            return create_response(200, 'success', {
                'id': row['id'],
                'group_name': row['group_name'],
                'description': row['description'] or '',
                'permissions': json.loads(row['permissions'] or '[]'),
                'member_ids': member_ids,
                'created_at': row['created_at'] or ''
            })

        elif request.method == 'PUT':
            data = request.get_json() or {}
            updates = []
            params = []

            if 'group_name' in data:
                updates.append('group_name = ?')
                params.append(data['group_name'])
            if 'description' in data:
                updates.append('description = ?')
                params.append(data['description'])
            if 'permissions' in data:
                updates.append('permissions = ?')
                params.append(json.dumps(data['permissions']))

            if not updates:
                conn.close()
                return create_response(400, '没有可更新的字段')

            updates.append('updated_at = ?')
            params.append(datetime.now().isoformat())
            params.append(group_id)

            cursor.execute(f'UPDATE user_groups SET {", ".join(updates)} WHERE id = ?', params)
            conn.commit()
            affected = cursor.rowcount
            conn.close()

            if affected == 0:
                return create_response(404, '用户组不存在')
            return create_response(200, '用户组更新成功')

        elif request.method == 'DELETE':
            cursor.execute('DELETE FROM user_group_members WHERE group_id = ?', (group_id,))
            cursor.execute('DELETE FROM user_groups WHERE id = ?', (group_id,))
            conn.commit()
            affected = cursor.rowcount
            conn.close()

            if affected == 0:
                return create_response(404, '用户组不存在')
            return create_response(200, '用户组删除成功')

    except Exception as e:
        logger.error(f"用户组操作失败: {e}")
        return create_response(500, '用户组操作失败')


@user_auth_enhanced_api.route('/api/groups/<int:group_id>/members', methods=['GET', 'POST', 'DELETE'])
@require_admin
def group_members(group_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        if request.method == 'GET':
            cursor.execute('''
                SELECT u.id, u.username, u.email, u.role, ugm.joined_at 
                FROM user_group_members ugm 
                JOIN users u ON ugm.user_id = u.id 
                WHERE ugm.group_id = ?
            ''', (group_id,))
            members = []
            for row in cursor.fetchall():
                members.append({
                    'user_id': row['id'],
                    'username': row['username'],
                    'email': row['email'],
                    'role': row['role'],
                    'joined_at': row['joined_at'] or ''
                })
            conn.close()
            return create_response(200, 'success', {'members': members})

        elif request.method == 'POST':
            data = request.get_json() or {}
            user_id = data.get('user_id')

            cursor.execute('SELECT id FROM users WHERE id = ?', (user_id,))
            if not cursor.fetchone():
                conn.close()
                return create_response(404, '用户不存在')

            cursor.execute('INSERT OR IGNORE INTO user_group_members (user_id, group_id, joined_at) VALUES (?, ?, ?)',
                         (user_id, group_id, datetime.now().isoformat()))
            conn.commit()
            conn.close()
            return create_response(200, '用户已加入用户组')

        elif request.method == 'DELETE':
            data = request.get_json() or {}
            user_id = data.get('user_id')

            cursor.execute('DELETE FROM user_group_members WHERE user_id = ? AND group_id = ?', (user_id, group_id))
            conn.commit()
            affected = cursor.rowcount
            conn.close()

            if affected == 0:
                return create_response(404, '用户不在该组中')
            return create_response(200, '用户已移出用户组')

    except Exception as e:
        logger.error(f"用户组成员操作失败: {e}")
        return create_response(500, '用户组成员操作失败')


@user_auth_enhanced_api.route('/api/permissions/matrix', methods=['GET'])
@require_admin
def get_permission_matrix():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT role, resource, action, allowed FROM permission_matrix')
        matrix = []
        for row in cursor.fetchall():
            matrix.append({
                'role': row['role'],
                'resource': row['resource'],
                'action': row['action'],
                'allowed': row['allowed'] == 1
            })
        conn.close()
        return create_response(200, 'success', {'matrix': matrix})

    except Exception as e:
        logger.error(f"获取权限矩阵失败: {e}")
        return create_response(500, '获取权限矩阵失败')


@user_auth_enhanced_api.route('/api/permissions/matrix', methods=['POST'])
@require_admin
def update_permission_matrix():
    try:
        data = request.get_json() or {}
        role = data.get('role')
        resource = data.get('resource')
        action = data.get('action')
        allowed = data.get('allowed', True)

        if not role or not resource or not action:
            return create_response(400, '缺少必要参数')

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('''
            INSERT OR REPLACE INTO permission_matrix (role, resource, action, allowed)
            VALUES (?, ?, ?, ?)
        ''', (role, resource, action, 1 if allowed else 0))
        conn.commit()
        conn.close()

        return create_response(200, '权限矩阵更新成功')

    except Exception as e:
        logger.error(f"更新权限矩阵失败: {e}")
        return create_response(500, '更新权限矩阵失败')


@user_auth_enhanced_api.route('/api/permissions/check', methods=['POST'])
@require_login
def check_permission():
    try:
        data = request.get_json() or {}
        resource = data.get('resource')
        action = data.get('action')
        user_role = session.get('role', 'user')

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT allowed FROM permission_matrix WHERE role = ? AND resource = ? AND action = ?',
                     (user_role, resource, action))
        row = cursor.fetchone()

        if row:
            has_permission = row['allowed'] == 1
        else:
            default_permissions = {
                'super_admin': True,
                'admin': True,
                'teacher': resource in ['exam', 'question', 'student'] and action in ['view', 'edit'],
                'student': resource in ['exam', 'learning'] and action in ['view']
            }
            has_permission = default_permissions.get(user_role, False)

        conn.close()
        return create_response(200, 'success', {'has_permission': has_permission})

    except Exception as e:
        logger.error(f"权限检查失败: {e}")
        return create_response(500, '权限检查失败')


@user_auth_enhanced_api.route('/api/auth/sessions', methods=['GET'])
@require_admin
def get_sessions():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT st.id, st.user_id, u.username, st.device_info, st.ip_address, st.expires_at, st.created_at
            FROM session_tokens st
            JOIN users u ON st.user_id = u.id
            WHERE st.expires_at > ?
            ORDER BY st.created_at DESC
        ''', (datetime.now().isoformat(),))

        sessions = []
        for row in cursor.fetchall():
            is_current = session.get('user_id') == row['user_id']
            sessions.append({
                'id': row['id'],
                'user_id': row['user_id'],
                'username': row['username'],
                'device_info': row['device_info'] or '',
                'ip_address': row['ip_address'] or '',
                'expires_at': row['expires_at'] or '',
                'created_at': row['created_at'] or '',
                'is_current': is_current
            })
        conn.close()
        return create_response(200, 'success', {'sessions': sessions})

    except Exception as e:
        logger.error(f"获取会话列表失败: {e}")
        return create_response(500, '获取会话列表失败')


@user_auth_enhanced_api.route('/api/auth/sessions/<int:session_id>', methods=['DELETE'])
@require_admin
def revoke_session(session_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('DELETE FROM session_tokens WHERE id = ?', (session_id,))
        conn.commit()
        affected = cursor.rowcount
        conn.close()

        if affected == 0:
            return create_response(404, '会话不存在')
        return create_response(200, '会话已吊销')

    except Exception as e:
        logger.error(f"吊销会话失败: {e}")
        return create_response(500, '吊销会话失败')


@user_auth_enhanced_api.route('/api/auth/login_attempts', methods=['GET'])
@require_admin
def get_login_attempts():
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        keyword = request.args.get('keyword', '')

        conn = get_db_connection()
        cursor = conn.cursor()

        where_clauses = []
        params = []

        if keyword:
            where_clauses.append('(username LIKE ?)')
            params.append(f'%{keyword}%')

        where_sql = 'WHERE ' + ' AND '.join(where_clauses) if where_clauses else ''

        cursor.execute(f'SELECT COUNT(*) FROM login_attempts {where_sql}', params)
        total = cursor.fetchone()[0] or 0

        offset = (page - 1) * per_page
        cursor.execute(f'''
            SELECT id, user_id, username, ip_address, attempt_time, success, failure_reason
            FROM login_attempts
            {where_sql}
            ORDER BY attempt_time DESC
            LIMIT ? OFFSET ?
        ''', params + [per_page, offset])

        attempts = []
        for row in cursor.fetchall():
            attempts.append({
                'id': row['id'],
                'user_id': row['user_id'],
                'username': row['username'] or '',
                'ip_address': row['ip_address'] or '',
                'attempt_time': row['attempt_time'] or '',
                'success': row['success'] == 1,
                'failure_reason': row['failure_reason'] or ''
            })
        conn.close()

        return create_response(200, 'success', {
            'attempts': attempts,
            'total': total,
            'page': page,
            'per_page': per_page
        })

    except Exception as e:
        logger.error(f"获取登录尝试记录失败: {e}")
        return create_response(500, '获取登录尝试记录失败')