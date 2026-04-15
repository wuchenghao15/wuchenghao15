#!/usr/bin/env python3
"""
使用系统相同的哈希算法创建测试用户
"""

import sqlite3
from app.utils.security import security_utils
from app.config import Config

# 数据库路径
db_path = Config.DATABASE_PATH

def create_test_user():
    """使用系统相同的哈希算法创建测试用户"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 测试用户名和密码
    username = "testuser"
    password = "Test123!@#"
    email = "test@example.com"
    
    print(f"\n🚀 创建测试用户")
    print(f"   用户名: {username}")
    print(f"   密码: {password}")
    print(f"   邮箱: {email}")
    
    # 使用系统相同的哈希算法
    hashed_password = security_utils.hash_password(password)
    print(f"   哈希密码: {hashed_password}")
    
    # 检查用户是否已存在
    cursor.execute('SELECT id FROM user WHERE username = ?', (username,))
    if cursor.fetchone():
        print(f"\n⚠️ 用户 {username} 已存在，将更新密码")
        # 更新用户密码
        cursor.execute('''
        UPDATE user SET password = ?, updated_at = CURRENT_TIMESTAMP WHERE username = ?
        ''', (hashed_password, username))
    else:
        # 创建用户
        cursor.execute('''
        INSERT INTO user (username, email, password, role, is_active, super_admin_approved, hardware_admin_approved)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (username, email, hashed_password, 'user', 1, 1, 1))
    
    conn.commit()
    conn.close()
    print(f"\n✅ 测试用户已创建/更新")

def main():
    """主函数"""
    print("🚀 创建测试用户脚本")
    print("=" * 50)
    
    # 创建测试用户
    create_test_user()
    
    print("\n🎉 完成！")

if __name__ == "__main__":
    main()
