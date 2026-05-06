#!/usr/bin/env python3
"""
创建新用户并设置密码

import sqlite3
import os
from app.utils.security import security_utils
from app.utils.logging import logger

def create_user(username, password, role='user'):
    """创建新用户"""
    try:
        # 连接数据库
        db_path = os.path.abspath('app.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # 检查用户是否已存在
        cursor.execute('SELECT id FROM users WHERE username = ?', (username,))
        if cursor.fetchone():
            print(f"用户 {username} 已存在")
            conn.close()
            return False

        # 生成哈希密码
        hashed_password = security_utils.hash_password(password)
        print(f"为用户 {username} 生成哈希密码: {hashed_password}")

        # 插入新用户
        cursor.execute('''
            INSERT INTO users (username, email, password, role, is_active)
            VALUES (?, ?, ?, ?, ?)
        ''', (username, f'{username}@example.com', hashed_password, role, 1))

        # 提交更改
        conn.commit()
        user_id = cursor.lastrowid
        conn.close()
        print(f"用户 {username} 创建成功，ID: {user_id}")
        logger.info(f"创建用户 {username} 成功，ID: {user_id}")
        return True

    except Exception as e:
        logger.error(f"创建用户失败: {str(e)}")
        print(f"创建用户失败: {str(e)}")
        return False

    # 创建设计师用户，密码为designer123
    create_user('designer1', 'designer123', 'user')
