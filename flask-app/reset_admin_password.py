#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
重置admin用户密码脚本

import sqlite3
import os
import sys
import hashlib
import base64

# 获取数据库路径
DATABASE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app.db')

# 安全工具类 - 使用PBKDF2算法
class SecurityUtils:
    """安全工具类，用于密码哈希"""

    @staticmethod
    def hash_password(password):
        """使用PBKDF2算法进行密码哈希"""
        # 模拟原始应用的配置
        HASH_ALGORITHM = 'sha256'
        HASH_ITERATIONS = 100000

        # 生成32字节的随机盐
        salt = os.urandom(32)
        hashed = hashlib.pbkdf2_hmac(
            HASH_ALGORITHM,
            password.encode('utf-8'),
            salt,
            HASH_ITERATIONS
        )
        # 将盐和哈希值连接起来，然后进行base64编码
        return base64.b64encode(salt + hashed).decode('utf-8')

security_utils = SecurityUtils()

def connect_db():
    """连接数据库"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        return conn
    except sqlite3.Error as e:
        print(f"数据库连接错误: {e}")
        sys.exit(1)

def reset_admin_password():
    """重置admin用户密码"""
    conn = connect_db()
    cursor = conn.cursor()

    # 管理员数据
    admin_user = {
        'username': 'admin',
        'password': 'ppo900lik',  # 用户要求的密码
        'email': '2@2.com',
        'role': 'admin',
        'is_active': 1,
        'super_admin_approved': 1,
        'hardware_admin_approved': 1
    }

    # 哈希密码
    hashed_password = security_utils.hash_password(admin_user['password'])

    # 更新admin用户
    try:
            UPDATE users
            SET password = ?, email = ?, role = ?, is_active = ?,
                super_admin_approved = ?, hardware_admin_approved = ?
            WHERE username = ?
        ''', (
            hashed_password,
            admin_user['email'],
            admin_user['role'],
            admin_user['is_active'],
            admin_user['super_admin_approved'],
            admin_user['hardware_admin_approved'],
            admin_user['username']
        ))

        if cursor.rowcount > 0:
            print(f"✅ 成功更新admin用户密码")
        else:
            # 如果admin用户不存在，则创建
            cursor.execute('''
                INSERT INTO users (username, email, password, role, is_active, super_admin_approved, hardware_admin_approved)
            ''', (
                admin_user['username'],
                admin_user['email'],
                admin_user['role'],
                admin_user['is_active'],
            ))
            print(f"✅ 成功创建admin用户")
        conn.commit()
        print(f"❌ 操作失败: {e}")

def verify_admin_password():
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute('SELECT username, password FROM users WHERE username = ?', ('admin',))

    if user:
        print(f"找到admin用户: {user[0]}")
        # 验证密码
        password_to_test = 'ppo900lik'
        hashed_test = security_utils.hash_password(password_to_test)
        print(f"测试密码的哈希: {hashed_test}")
        print(f"数据库中的哈希: {user[1]}")

    conn.close()

if __name__ == '__main__':
    print("开始重置admin用户密码...")
    reset_admin_password()
    print("\n验证admin用户密码...")
    verify_admin_password()
    print("\n操作完成！")
