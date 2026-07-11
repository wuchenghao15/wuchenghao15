# -*- coding: utf-8 -*-
"""
用户个人中心服务
提供用户资料管理、密码修改、头像上传等功能
"""

import logging
import sqlite3
import os
import hashlib
import time
from datetime import datetime
from typing import Dict, List, Optional
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class UserProfileService:
    """用户个人中心服务"""

    _instance = None

    def __new__(cls, db_path: str = None):
        if not cls._instance:
            cls._instance = super(UserProfileService, cls).__new__(cls)
            cls._instance._initialize(db_path)
        return cls._instance

    def _initialize(self, db_path: str = None):
        if db_path:
            self.db_path = db_path
        else:
            self.db_path = os.path.join(
                os.path.dirname(__file__), '..', '..', 'app.db'
            )
        self._init_tables()
        logger.info("用户个人中心服务初始化完成")

    @contextmanager
    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def _init_tables(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_profile_info (
                user_id INTEGER PRIMARY KEY,
                nickname TEXT,
                avatar TEXT,
                bio TEXT,
                phone TEXT,
                email TEXT,
                gender TEXT,
                birthday TEXT,
                location TEXT,
                company TEXT,
                position TEXT,
                website TEXT,
                language TEXT DEFAULT 'zh',
                theme TEXT DEFAULT 'light',
                notification_enabled INTEGER DEFAULT 1,
                email_notification INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')

            cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_login_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                login_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                logout_time TIMESTAMP,
                ip_address TEXT,
                user_agent TEXT,
                device TEXT,
                location TEXT,
                status TEXT DEFAULT 'success',
                session_id TEXT
            )
            ''')

            cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_activity_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                activity_type TEXT NOT NULL,
                activity_detail TEXT,
                ip_address TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')

            cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_login_logs_user ON user_login_logs(user_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_activity_logs_user ON user_activity_logs(user_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_activity_logs_type ON user_activity_logs(activity_type)')

            conn.commit()

    def get_profile(self, user_id: int) -> Optional[Dict]:
        """获取用户资料"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
            user = cursor.fetchone()
            if not user:
                return None

            cursor.execute('SELECT * FROM user_profile_info WHERE user_id = ?', (user_id,))
            profile = cursor.fetchone()

            user_dict = dict(user)
            profile_dict = dict(profile) if profile else {}

            if not profile:
                cursor.execute(
                    'INSERT INTO user_profile_info (user_id, nickname) VALUES (?, ?)',
                    (user_id, user_dict.get('username', ''))
                )
                conn.commit()
                profile_dict = {'user_id': user_id, 'nickname': user_dict.get('username', '')}

            result = {
                'id': user_dict['id'],
                'username': user_dict['username'],
                'role': user_dict.get('role', ''),
                'nickname': profile_dict.get('nickname', user_dict.get('username', '')),
                'avatar': profile_dict.get('avatar', ''),
                'bio': profile_dict.get('bio', ''),
                'phone': profile_dict.get('phone', ''),
                'email': profile_dict.get('email', ''),
                'gender': profile_dict.get('gender', ''),
                'birthday': profile_dict.get('birthday', ''),
                'location': profile_dict.get('location', ''),
                'company': profile_dict.get('company', ''),
                'position': profile_dict.get('position', ''),
                'website': profile_dict.get('website', ''),
                'language': profile_dict.get('language', 'zh'),
                'theme': profile_dict.get('theme', 'light'),
                'notification_enabled': profile_dict.get('notification_enabled', 1),
                'email_notification': profile_dict.get('email_notification', 1),
                'created_at': user_dict.get('created_at', ''),
                'updated_at': profile_dict.get('updated_at', '')
            }

            return result

    def update_profile(self, user_id: int, data: Dict) -> Dict:
        """更新用户资料"""
        allowed_fields = [
            'nickname', 'bio', 'phone', 'email', 'gender',
            'birthday', 'location', 'company', 'position', 'website'
        ]

        fields_to_update = {}
        for field in allowed_fields:
            if field in data:
                fields_to_update[field] = data[field]

        if not fields_to_update:
            return self.get_profile(user_id)

        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute('SELECT user_id FROM user_profile_info WHERE user_id = ?', (user_id,))
            exists = cursor.fetchone()

            if exists:
                set_clause = ', '.join([f'{k} = ?' for k in fields_to_update.keys()])
                values = list(fields_to_update.values()) + [datetime.now().isoformat(), user_id]
                cursor.execute(
                    f'UPDATE user_profile_info SET {set_clause}, updated_at = ? WHERE user_id = ?',
                    values
                )
            else:
                fields = list(fields_to_update.keys()) + ['user_id']
                placeholders = ', '.join(['?' for _ in fields])
                values = list(fields_to_update.values()) + [user_id]
                cursor.execute(
                    f'INSERT INTO user_profile_info ({", ".join(fields)}) VALUES ({placeholders})',
                    values
                )

            conn.commit()

        self.log_activity(user_id, 'update_profile', '更新个人资料')

        return self.get_profile(user_id)

    def change_password(self, user_id: int, old_password: str, new_password: str) -> Dict:
        """修改密码"""
        if not new_password or len(new_password) < 6:
            return {'success': False, 'error': '新密码长度不能少于6位'}

        if old_password == new_password:
            return {'success': False, 'error': '新密码不能与旧密码相同'}

        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute('SELECT password FROM users WHERE id = ?', (user_id,))
            row = cursor.fetchone()
            if not row:
                return {'success': False, 'error': '用户不存在'}

            stored_password = row['password']

            if len(stored_password) == 32:
                old_hash = hashlib.md5(old_password.encode()).hexdigest()
            else:
                from werkzeug.security import check_password_hash
                if not check_password_hash(stored_password, old_password):
                    return {'success': False, 'error': '原密码错误'}
                old_hash = None

            if old_hash and old_hash != stored_password:
                return {'success': False, 'error': '原密码错误'}

            from werkzeug.security import generate_password_hash
            new_hash = generate_password_hash(new_password)

            cursor.execute(
                'UPDATE users SET password = ?, updated_at = ? WHERE id = ?',
                (new_hash, datetime.now().isoformat(), user_id)
            )
            conn.commit()

        self.log_activity(user_id, 'change_password', '修改密码')

        return {'success': True, 'message': '密码修改成功'}

    def update_avatar(self, user_id: int, avatar_url: str) -> Dict:
        """更新头像"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute('SELECT user_id FROM user_profile_info WHERE user_id = ?', (user_id,))
            exists = cursor.fetchone()

            if exists:
                cursor.execute(
                    'UPDATE user_profile_info SET avatar = ?, updated_at = ? WHERE user_id = ?',
                    (avatar_url, datetime.now().isoformat(), user_id)
                )
            else:
                cursor.execute(
                    'INSERT INTO user_profile_info (user_id, avatar) VALUES (?, ?)',
                    (user_id, avatar_url)
                )

            conn.commit()

        self.log_activity(user_id, 'update_avatar', '更新头像')

        return {'success': True, 'avatar': avatar_url}

    def update_settings(self, user_id: int, settings: Dict) -> Dict:
        """更新用户设置"""
        allowed_fields = ['language', 'theme', 'notification_enabled', 'email_notification']

        fields_to_update = {}
        for field in allowed_fields:
            if field in settings:
                fields_to_update[field] = settings[field]

        if not fields_to_update:
            return {'success': True}

        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute('SELECT user_id FROM user_profile_info WHERE user_id = ?', (user_id,))
            exists = cursor.fetchone()

            if exists:
                set_clause = ', '.join([f'{k} = ?' for k in fields_to_update.keys()])
                values = list(fields_to_update.values()) + [datetime.now().isoformat(), user_id]
                cursor.execute(
                    f'UPDATE user_profile_info SET {set_clause}, updated_at = ? WHERE user_id = ?',
                    values
                )
            else:
                fields = list(fields_to_update.keys()) + ['user_id']
                placeholders = ', '.join(['?' for _ in fields])
                values = list(fields_to_update.values()) + [user_id]
                cursor.execute(
                    f'INSERT INTO user_profile_info ({", ".join(fields)}) VALUES ({placeholders})',
                    values
                )

            conn.commit()

        self.log_activity(user_id, 'update_settings', '更新个人设置')

        return {'success': True, 'settings': fields_to_update}

    def log_login(self, user_id: int, ip_address: str = None, user_agent: str = None, session_id: str = None) -> int:
        """记录登录日志"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                '''INSERT INTO user_login_logs 
                   (user_id, ip_address, user_agent, session_id, status)
                   VALUES (?, ?, ?, ?, 'success')''',
                (user_id, ip_address, user_agent, session_id)
            )
            conn.commit()
            return cursor.lastrowid

    def log_logout(self, user_id: int, session_id: str = None):
        """记录登出"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if session_id:
                cursor.execute(
                    '''UPDATE user_login_logs SET logout_time = ? 
                       WHERE user_id = ? AND session_id = ? AND logout_time IS NULL
                       ORDER BY login_time DESC LIMIT 1''',
                    (datetime.now().isoformat(), user_id, session_id)
                )
            else:
                cursor.execute(
                    '''UPDATE user_login_logs SET logout_time = ? 
                       WHERE user_id = ? AND logout_time IS NULL
                       ORDER BY login_time DESC LIMIT 1''',
                    (datetime.now().isoformat(), user_id)
                )
            conn.commit()

    def log_activity(self, user_id: int, activity_type: str, activity_detail: str = None, ip_address: str = None):
        """记录用户活动"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                '''INSERT INTO user_activity_logs 
                   (user_id, activity_type, activity_detail, ip_address)
                   VALUES (?, ?, ?, ?)''',
                (user_id, activity_type, activity_detail, ip_address)
            )
            conn.commit()

    def get_login_history(self, user_id: int, limit: int = 20) -> List[Dict]:
        """获取登录历史"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                '''SELECT * FROM user_login_logs 
                   WHERE user_id = ? ORDER BY login_time DESC LIMIT ?''',
                (user_id, limit)
            )
            return [dict(row) for row in cursor.fetchall()]

    def get_activity_logs(self, user_id: int, limit: int = 50, activity_type: str = None) -> List[Dict]:
        """获取活动日志"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if activity_type:
                cursor.execute(
                    '''SELECT * FROM user_activity_logs 
                       WHERE user_id = ? AND activity_type = ?
                       ORDER BY created_at DESC LIMIT ?''',
                    (user_id, activity_type, limit)
                )
            else:
                cursor.execute(
                    '''SELECT * FROM user_activity_logs 
                       WHERE user_id = ? ORDER BY created_at DESC LIMIT ?''',
                    (user_id, limit)
                )
            return [dict(row) for row in cursor.fetchall()]

    def get_stats(self, user_id: int) -> Dict:
        """获取用户统计信息"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute(
                'SELECT COUNT(*) as count FROM user_login_logs WHERE user_id = ?',
                (user_id,)
            )
            login_count = cursor.fetchone()['count']

            cursor.execute(
                'SELECT COUNT(*) as count FROM user_activity_logs WHERE user_id = ?',
                (user_id,)
            )
            activity_count = cursor.fetchone()['count']

            cursor.execute(
                '''SELECT COUNT(DISTINCT DATE(login_time)) as days 
                   FROM user_login_logs WHERE user_id = ?''',
                (user_id,)
            )
            active_days = cursor.fetchone()['days']

        return {
            'login_count': login_count,
            'activity_count': activity_count,
            'active_days': active_days
        }
