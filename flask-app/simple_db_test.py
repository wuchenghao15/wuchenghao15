#!/usr/bin/env python3
"""
简单的数据库测试脚本，用于测试用户表创建和登录验证功能

import sqlite3
import hashlib

# 数据库路径
db_path = 'app.db'

def create_user_table():
    """创建用户表"""
    conn = sqlite3.connect(db_path)
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

def hash_password(password):
    """使用sha256哈希密码，与User.verify_credentials方法兼容"""
    salt = "mtscos_salt"  # 简单的盐值
    hashed = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000)
    return hashed.hex()

def create_test_user():
    """创建测试用户"""
    conn = sqlite3.connect(db_path)

    username = "testuser"
    password = "Test123!@#"
    email = "test@example.com"

    # 检查用户是否已存在
    cursor.execute('SELECT id FROM user WHERE username = ?', (username,))
    if cursor.fetchone():
        print(f"⚠️ 用户 {username} 已存在")
        conn.close()
        return

    hashed_password = hash_password(password)

    # 创建用户
    cursor.execute('''
    INSERT INTO user (username, email, password, role, is_active, super_admin_approved, hardware_admin_approved)
    VALUES (?, ?, ?, ?, ?, ?, ?)

    conn.commit()
    conn.close()
    print(f"✓ 测试用户已创建")
    print(f"   用户名: {username}")
    print(f"   邮箱: {email}")
def verify_password(stored_hash, password):
    """验证密码，与User.verify_credentials方法兼容"""
    salt = "mtscos_salt"  # 简单的盐值
    hashed = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000)
    return hashed.hex() == stored_hash

def test_login():
    """测试登录功能"""
    conn = sqlite3.connect(db_path)
    # 测试用户名和密码

    print("\n🔍 测试登录功能...")

    # 从数据库查询用户
    cursor.execute('SELECT id, username, email, password, role, is_active FROM user WHERE username = ?', (username,))
    user_data = cursor.fetchone()

    if user_data:

        if verify_password(hashed_password, password):
            print(f"   用户ID: {user_id}")
            print(f"   用户名: {username}")
            print(f"   角色: {role}")
            conn.close()
            return True
        else:
            print(f"❌ 密码错误！")
    else:
        print(f"❌ 用户不存在！")

    return False

def main():
    """主函数"""
    print("🚀 简单数据库测试脚本")

    try:
        # 创建表
        create_user_table()

        # 创建测试用户

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
    main()
