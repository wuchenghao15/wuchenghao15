#!/usr/bin/env python3
import sqlite3
import logging
import os

logger = logging.getLogger(__name__)

DATABASE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'app.db')

class UserContainer:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def get_user(self, username):
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
                user = cursor.fetchone()
                if user:
                    return dict(user)
                return None
        except Exception as e:
            logger.error(f"获取用户失败: {e}")
            return None

    def get_user_by_id(self, user_id):
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
                user = cursor.fetchone()
                if user:
                    return dict(user)
                return None
        except Exception as e:
            logger.error(f"获取用户失败: {e}")
            return None

    def get_all_users(self):
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT id, username, email, role, created_at FROM users')
                users = cursor.fetchall()
                return [dict(u) for u in users]
        except Exception as e:
            logger.error(f"获取所有用户失败: {e}")
            return []

    def get_user_count(self):
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT COUNT(*) FROM users')
                return cursor.fetchone()[0]
        except Exception as e:
            logger.error(f"获取用户数量失败: {e}")
            return 0
