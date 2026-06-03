# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
设置用户脚本,创建所需的硬件管理员、超级管理员和普通用户
"""
import logging
logger = logging.getLogger(__name__)
import sys
import os
import hashlib
import hmac
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.utils.db import db_manager

def hash_password(password, iterations=100000, algorithm='sha256'):
    """生成密码哈希
    
    Args:
        password: 原始密码
        iterations: 迭代次数
        algorithm: 哈希算法
    
    Returns:
        哈希后的密码
    """
    password_bytes = password.encode('utf-8')
    salt = os.urandom(16)

    hasher = hashlib.pbkdf2_hmac(
        algorithm,
        password_bytes,
        salt,
        iterations
    )

    return f"{salt.hex()}$${iterations}$${hasher.hex()}"

def setup_users():
    """设置所需的用户"""
    print("开始设置用户...")

    users = [
        {
            'username': 'wuchenghao15',
            'password': 'LoginMe.1988',
            'email': 'wuchenghao_15@163.com',
            'role': 'hardware_vikey_admin',
            'is_active': 1,
            'super_admin_approved': 1,
            'hardware_admin_approved': 1
        },
        {
            'username': 'wuchenghao16',
            'password': 'LoginMe.1988',
            'email': '2@2.com',
            'role': 'admin',
            'is_active': 1,
            'super_admin_approved': 1,
            'hardware_admin_approved': 1
        },
        {
            'username': 'wuchenghao17',
            'password': 'LoginMe.1988',
            'email': '1175061512@qq.com',
            'role': 'user',
            'is_active': 1,
            'super_admin_approved': 1,
            'hardware_admin_approved': 1
        }
    ]

    for user_data in users:
        existing_user = db_manager.fetch_one(
            "SELECT id FROM users WHERE username = ? OR email = ?",
            (user_data['username'], user_data['email'])
        )

        if existing_user:
            print(f"用户 {user_data['username']} 已存在,更新中...")
            hashed_password = hash_password(user_data['password'])
            update_data = {
                'password': hashed_password,
                'email': user_data['email'],
                'role': user_data['role'],
                'is_active': user_data['is_active'],
                'super_admin_approved': user_data['super_admin_approved'],
                'hardware_admin_approved': user_data['hardware_admin_approved'],
                'updated_at': datetime.now().isoformat()
            }
            db_manager.update('users', update_data, "username = ?", (user_data['username'],))
            print(f"用户 {user_data['username']} 更新成功")
            continue

        hashed_password = hash_password(user_data['password'])

        user_insert_data = {
            'username': user_data['username'],
            'password': hashed_password,
            'email': user_data['email'],
            'role': user_data['role'],
            'is_active': user_data['is_active'],
            'super_admin_approved': user_data['super_admin_approved'],
            'hardware_admin_approved': user_data['hardware_admin_approved'],
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }

        user_id = db_manager.insert('users', user_insert_data)
        if user_id:
            print(f"成功创建用户:{user_data['username']} (ID: {user_id})")
        else:
            print(f"创建用户失败:{user_data['username']}")

    users = db_manager.fetch_all("SELECT id, username, email, role, is_active, super_admin_approved, hardware_admin_approved FROM users")
    print(f"\n当前用户总数: {len(users)}")
    for user in users:
        print(f"  - {user['username']} ({user['role']})")

if __name__ == "__main__":
    setup_users()
