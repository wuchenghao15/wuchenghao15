#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
注册用户脚本，用于批量注册不同角色的用户
"""

import sqlite3
import os
import sys
import hashlib

# 获取数据库路径
DATABASE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app.db')

# 安全工具类
class SecurityUtils:
    """安全工具类，用于密码哈希"""
    
    @staticmethod
    def hash_password(password):
        """密码哈希"""
        return hashlib.sha256(password.encode()).hexdigest()

security_utils = SecurityUtils()

# 用户数据
USERS = [
    # 硬件管理员
    {
        'username': 'wuchenghao15',
        'password': 'LoginMe.1988',
        'email': '1@1.com',
        'role': 'hardware_vikey_admin',
        'is_active': 1,
        'super_admin_approved': 1,
        'hardware_admin_approved': 1
    },
    # 管理员
    {
        'username': 'admin',
        'password': 'ppo900lik',
        'email': '2@2.com',
        'role': 'admin',
        'is_active': 1,
        'super_admin_approved': 1,
        'hardware_admin_approved': 1
    },
    # 普通用户
    {
        'username': 'caopw',
        'password': 'xuxu2pipo',
        'email': '3@3.com',
        'role': 'user',
        'is_active': 1,
        'super_admin_approved': 1,
        'hardware_admin_approved': 1
    }
]

def connect_db():
    """连接数据库"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        return conn
    except sqlite3.Error as e:
        print(f"数据库连接错误: {e}")
        sys.exit(1)

def create_users_table():
    """创建用户表（如果不存在）"""
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'user',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            is_active INTEGER DEFAULT 1,
            super_admin_approved INTEGER DEFAULT 0,
            hardware_admin_approved INTEGER DEFAULT 0,
            avatar TEXT DEFAULT NULL
        )
    ''')
    conn.commit()
    conn.close()
    print("用户表已创建或已存在")

def register_users():
    """注册用户"""
    conn = connect_db()
    cursor = conn.cursor()
    
    for user_data in USERS:
        # 检查用户是否已存在
        cursor.execute('SELECT id FROM users WHERE username=?', (user_data['username'],))
        if cursor.fetchone():
            print(f"用户 {user_data['username']} 已存在")
            continue
        
        # 哈希密码
        hashed_password = security_utils.hash_password(user_data['password'])
        
        # 插入用户
        cursor.execute('''
            INSERT INTO users (username, email, password, role, is_active, super_admin_approved, hardware_admin_approved)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            user_data['username'],
            user_data['email'],
            hashed_password,
            user_data['role'],
            user_data['is_active'],
            user_data['super_admin_approved'],
            user_data['hardware_admin_approved']
        ))
        
        print(f"用户 {user_data['username']} 注册成功")
    
    conn.commit()
    conn.close()

def verify_users():
    """验证用户是否注册成功"""
    conn = connect_db()
    cursor = conn.cursor()
    
    for user_data in USERS:
        cursor.execute('SELECT username, role, is_active FROM users WHERE username=?', (user_data['username'],))
        user = cursor.fetchone()
        if user:
            print(f"验证通过：用户 {user[0]}，角色 {user[1]}，状态 {'已激活' if user[2] == 1 else '未激活'}")
        else:
            print(f"验证失败：用户 {user_data['username']} 不存在")
    
    conn.close()

if __name__ == '__main__':
    print("开始注册用户...")
    create_users_table()
    register_users()
    print("\n验证用户注册结果...")
    verify_users()
    print("\n用户注册完成！")
