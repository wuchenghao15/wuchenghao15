#!/usr/bin/env python3
"""
测试登录功能，创建用户表和测试用户
"""

import os
import sys

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.utils.db import db_manager
from app.utils.security import security_utils

# 创建用户表
def create_user_table():
    """创建用户表"""
    table_name = "user"
    columns = {
        "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
        "username": "VARCHAR(50) NOT NULL UNIQUE",
        "email": "VARCHAR(100) NOT NULL UNIQUE",
        "password": "VARCHAR(255) NOT NULL",
        "role": "VARCHAR(20) NOT NULL DEFAULT 'user'",
        "is_active": "INTEGER NOT NULL DEFAULT 1",
        "super_admin_approved": "INTEGER NOT NULL DEFAULT 0",
        "hardware_admin_approved": "INTEGER NOT NULL DEFAULT 0",
        "created_at": "DATETIME DEFAULT CURRENT_TIMESTAMP",
        "updated_at": "DATETIME DEFAULT CURRENT_TIMESTAMP"
    }
    
    success = db_manager.create_table(table_name, columns)
    if success:
        print("✅ 用户表创建成功")
    else:
        print("❌ 用户表创建失败")

# 创建测试用户
def create_test_user():
    """创建测试用户"""
    username = "testuser"
    email = "test@example.com"
    password = "Test1234!"
    
    # 检查用户是否已存在
    query = "SELECT id FROM user WHERE username = ?"
    user = db_manager.fetch_one(query, (username,))
    
    if user:
        print("ℹ️  测试用户已存在")
        return
    
    # 哈希密码
    hashed_password = security_utils.hash_password(password)
    
    # 插入用户
    user_data = {
        "username": username,
        "email": email,
        "password": hashed_password,
        "role": "user",
        "is_active": 1,
        "super_admin_approved": 1,
        "hardware_admin_approved": 1
    }
    
    user_id = db_manager.insert("user", user_data)
    if user_id:
        print(f"✅ 测试用户创建成功，ID: {user_id}")
        print(f"   用户名: {username}")
        print(f"   密码: {password}")
    else:
        print("❌ 测试用户创建失败")

# 创建验证码表
def create_verification_tables():
    """创建验证相关的表"""
    # 创建verification_codes表
    verification_codes_columns = {
        "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
        "code": "VARCHAR(50) NOT NULL",
        "code_type": "VARCHAR(20) NOT NULL",
        "user_id": "INTEGER",
        "username": "VARCHAR(50)",
        "is_used": "INTEGER NOT NULL DEFAULT 0",
        "used_at": "DATETIME",
        "expires_at": "DATETIME NOT NULL",
        "created_at": "DATETIME DEFAULT CURRENT_TIMESTAMP"
    }
    
    success = db_manager.create_table("verification_codes", verification_codes_columns)
    if success:
        print("✅ 验证码表创建成功")
    else:
        print("❌ 验证码表创建失败")
    
    # 创建whitelist_tokens表
    whitelist_tokens_columns = {
        "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
        "token": "VARCHAR(255) NOT NULL UNIQUE",
        "user_id": "INTEGER",
        "username": "VARCHAR(50)",
        "is_active": "INTEGER NOT NULL DEFAULT 1",
        "expires_at": "DATETIME",
        "description": "TEXT",
        "created_at": "DATETIME DEFAULT CURRENT_TIMESTAMP",
        "updated_at": "DATETIME DEFAULT CURRENT_TIMESTAMP"
    }
    
    success = db_manager.create_table("whitelist_tokens", whitelist_tokens_columns)
    if success:
        print("✅ 白名单token表创建成功")
    else:
        print("❌ 白名单token表创建失败")
    
    # 创建login_verification_log表
    login_verification_log_columns = {
        "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
        "username": "VARCHAR(50) NOT NULL",
        "verification_type": "VARCHAR(20) NOT NULL",
        "verification_value": "TEXT NOT NULL",
        "is_successful": "INTEGER NOT NULL",
        "error_message": "TEXT",
        "ip_address": "VARCHAR(50)",
        "user_agent": "TEXT",
        "created_at": "DATETIME DEFAULT CURRENT_TIMESTAMP"
    }
    
    success = db_manager.create_table("login_verification_log", login_verification_log_columns)
    if success:
        print("✅ 登录验证日志表创建成功")
    else:
        print("❌ 登录验证日志表创建失败")

# 运行测试
def main():
    """主函数"""
    print("🚀 开始测试登录功能...")
    print("=" * 50)
    
    # 创建用户表
    create_user_table()
    
    # 创建验证相关的表
    create_verification_tables()
    
    # 创建测试用户
    create_test_user()
    
    print("=" * 50)
    print("🎉 测试完成！")
    print("\n使用以下信息登录:")
    print("用户名: testuser")
    print("密码: Test1234!")

if __name__ == "__main__":
    main()