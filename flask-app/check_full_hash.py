#!/usr/bin/env python3
"""
简单脚本，用于检查数据库中用户表的内容
"""

import sqlite3

try:
    # 直接连接SQLite数据库
    db_path = 'app.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 查询用户表的所有记录
    print("查询用户表内容...")
    cursor.execute('SELECT id, username, email, password, role, is_active FROM user')
    users = cursor.fetchall()
    
    print("\n用户表内容:")
    print(f"{'ID':<5} {'用户名':<20} {'邮箱':<30} {'密码哈希(完整)':<130} {'角色':<15} {'激活状态':<10}")
    print("-" * 210)
    
    for user in users:
        user_id, username, email, password, role, is_active = user
        print(f"{user_id:<5} {username:<20} {email:<30} {password:<130} {role:<15} {is_active:<10}")
        print(f"  密码长度: {len(password)}, 格式: {'hex' if all(c in '0123456789abcdefABCDEF' for c in password) else '其他'}")
    
    # 关闭数据库连接
    conn.close()
    
except Exception as e:
    print(f"错误: {str(e)}")
    import traceback
    traceback.print_exc()