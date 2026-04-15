#!/usr/bin/env python3
"""
设置用户脚本，创建所需的硬件管理员、超级管理员和普通用户
"""

import sys
import os
import hashlib
import hmac
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 导入数据库管理器
from app.utils.db import db_manager

# 密码哈希函数
def hash_password(password, iterations=100000, algorithm='sha256'):
    """生成密码哈希
    
    Args:
        password: 原始密码
        iterations: 迭代次数
        algorithm: 哈希算法
        
    Returns:
        哈希后的密码
    """
    # 使用HMAC-SHA256进行密码哈希
    password_bytes = password.encode('utf-8')
    salt = os.urandom(16)
    
    hasher = hashlib.pbkdf2_hmac(
        algorithm,
        password_bytes,
        salt,
        iterations
    )
    
    # 返回格式：salt$iterations$hash
    return f"{salt.hex()}$${iterations}$${hasher.hex()}"

def setup_users():
    """设置所需的用户"""
    print("开始设置用户...")
    
    # 2. 准备用户数据
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
            'password': 'ppo900lik',
            'email': '2@2.com',
            'role': 'admin',
            'is_active': 1,
            'super_admin_approved': 1,
            'hardware_admin_approved': 1
        },
        {
            'username': 'caopw',
            'password': 'xuxu2pipo',
            'email': '1175061512@qq.com',
            'role': 'user',
            'is_active': 1,
            'super_admin_approved': 1,
            'hardware_admin_approved': 1
        }
    ]
    
    # 3. 插入用户
    for user_data in users:
        # 检查用户是否已存在
        existing_user = db_manager.fetch_one(
            "SELECT id FROM users WHERE username = ? OR email = ?",
            (user_data['username'], user_data['email'])
        )
        
        if existing_user:
            print(f"用户 {user_data['username']} 已存在，更新中...")
            # 更新用户信息
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
        
        # 哈希密码
        hashed_password = hash_password(user_data['password'])
        
        # 准备插入数据
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
        
        # 插入用户
        user_id = db_manager.insert('users', user_insert_data)
        if user_id:
            print(f"成功创建用户：{user_data['username']} (ID: {user_id})")
        else:
            print(f"创建用户失败：{user_data['username']}")
    
    # 4. 验证用户是否创建成功
    print("\n验证用户创建结果：")
    users = db_manager.fetch_all("SELECT id, username, email, role, is_active, super_admin_approved, hardware_admin_approved FROM users")
    for user in users:
        print(f"  - ID: {user['id']}, 用户名: {user['username']}, 邮箱: {user['email']}, 角色: {user['role']}, 已激活: {user['is_active']}, 超级管理员批准: {user['super_admin_approved']}, 硬件管理员批准: {user['hardware_admin_approved']}")
    
    print("\n用户设置完成！")

if __name__ == "__main__":
    setup_users()
