# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
创建新用户并设置密码
"""

import logging
import sqlite3
import os

logger = logging.getLogger(__name__)

try:
    from app.utils.security import security_utils
    from app.utils.logging import logger as app_logger
except ImportError:
    security_utils = None
    app_logger = logger

def create_user(username, password, role='user'):
    """创建新用户"""
    try:
        db_path = os.path.abspath('app.db')
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('SELECT id FROM users WHERE username = ?', (username,))
            if cursor.fetchone():
                print(f"用户 {username} 已存在")
                return False

            if security_utils:
                hashed_password = security_utils.hash_password(password)
            else:
                import hashlib
                hashed_password = hashlib.sha256(password.encode()).hexdigest()
            
            print(f"为用户 {username} 生成哈希密码: {hashed_password}")

            cursor.execute('''
                INSERT INTO users (username, email, password, role, is_active)
                VALUES (?, ?, ?, ?, ?)
            ''', (username, f'{username}@example.com', hashed_password, role, 1))

            conn.commit()
            user_id = cursor.lastrowid
            print(f"用户 {username} 创建成功,ID: {user_id}")
            logger.info(f"创建用户 {username} 成功,ID: {user_id}")
            return True

    except Exception as e:
        logger.error(f"创建用户失败: {str(e)}")
        print(f"创建用户失败: {str(e)}")
        return False

if __name__ == '__main__':
    create_user('designer1', 'designer123', 'user')
