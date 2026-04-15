#!/usr/bin/env python3
"""
简单的登录测试脚本，用于测试登录功能是否正常工作
"""

import sqlite3
import hashlib
import sys
from app.config import Config

# 数据库路径
DATABASE_PATH = Config.DATABASE_PATH

def create_user_table():
    """创建用户表"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # 创建用户表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS user (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        role TEXT DEFAULT 'user',
        is_active INTEGER DEFAULT 1,
        super_admin_approved INTEGER DEFAULT 1,
        hardware_admin_approved INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        avatar TEXT
    )
    ''')
    
    conn.commit()
    conn.close()
    print("✓ 用户表已创建")

def create_verification_tables():
    """创建验证相关的表"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # 创建verification_codes表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS verification_codes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        code TEXT NOT NULL,
        code_type TEXT NOT NULL,
        user_id INTEGER,
        username TEXT,
        is_used INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        used_at TIMESTAMP,
        expires_at TIMESTAMP NOT NULL
    )
    ''')
    
    # 创建whitelist_tokens表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS whitelist_tokens (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        token TEXT UNIQUE NOT NULL,
        user_id INTEGER,
        username TEXT,
        is_active INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        expires_at TIMESTAMP
    )
    ''')
    
    # 创建login_verification_log表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS login_verification_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        verification_type TEXT NOT NULL,
        verification_value TEXT NOT NULL,
        is_successful INTEGER NOT NULL,
        error_message TEXT,
        ip_address TEXT,
        user_agent TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    conn.commit()
    conn.close()
    print("✓ 验证相关表已创建")

def hash_password(password):
    """简单的密码哈希函数"""
    salt = "mtscos_salt"  # 简单的盐值
    hashed = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000)
    return hashed.hex()

def create_test_user():
    """创建测试用户"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # 测试用户名和密码
    username = "testuser"
    password = "Test123!@#"
    email = "test@example.com"
    
    # 检查用户是否已存在
    cursor.execute('SELECT id FROM user WHERE username = ?', (username,))
    if cursor.fetchone():
        print(f"⚠️ 用户 {username} 已存在")
        conn.close()
        return
    
    # 哈希密码
    hashed_password = hash_password(password)
    
    # 创建用户
    cursor.execute('''
    INSERT INTO user (username, email, password, role, is_active, super_admin_approved, hardware_admin_approved)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (username, email, hashed_password, 'user', 1, 1, 1))
    
    conn.commit()
    conn.close()
    print(f"✓ 测试用户已创建")
    print(f"   用户名: {username}")
    print(f"   密码: {password}")
    print(f"   邮箱: {email}")

def test_login():
    """测试登录功能"""
    from app.models.user import User
    
    # 测试用户名和密码
    username = "testuser"
    password = "Test123!@#"
    
    print("\n🔍 测试登录功能...")
    
    # 使用User类的verify_credentials方法测试登录
    user = User.verify_credentials(username, password)
    
    if user:
        print(f"✅ 登录成功！")
        print(f"   用户ID: {user.user_id}")
        print(f"   用户名: {user.username}")
        print(f"   角色: {user.role}")
        return True
    else:
        print(f"❌ 登录失败！")
        return False

def main():
    """主函数"""
    print("🚀 简单登录测试脚本")
    print(f"📊 数据库路径: {DATABASE_PATH}")
    print("=" * 50)
    
    try:
        # 创建表
        create_user_table()
        create_verification_tables()
        
        # 创建测试用户
        create_test_user()
        
        # 测试登录
        test_login()
        
        print("\n🎉 测试完成！")
    except Exception as e:
        print(f"\n💥 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
