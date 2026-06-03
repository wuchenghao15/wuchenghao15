# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
修复测试脚本 - 使用正确的密码哈希
"""

import os
import sys
import sqlite3
import hashlib
import base64
from datetime import datetime

# 路径
DATABASE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'app.db')


def fix_test_users():
    """修复测试用户密码"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    users = [
        ('testStu', 'Stu0123', 'user'),
        ('testAmd', 'testAmd', 'admin')
    ]
    
    for username, password, role in users:
        print(f"处理用户: {username}")
        
        # 使用简单的SHA-256哈希(与verify_password兼容)
        hashed_pw = hashlib.sha256(password.encode()).digest()
        hashed_pw_b64 = base64.b64encode(hashed_pw).decode()
        
        cursor.execute('''
            UPDATE users SET password = ? WHERE username = ?
        ''', (hashed_pw_b64, username))
        
        if cursor.rowcount == 0:
            cursor.execute('''
                INSERT INTO users (username, password, role, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
            ''', (username, hashed_pw_b64, role, 
                  datetime.now().isoformat(), datetime.now().isoformat()))
            print(f"  创建用户: {username}")
        else:
            print(f"  更新密码: {username}")
    
    conn.commit()
    conn.close()
    print("\n✅ 用户密码修复完成!")


if __name__ == '__main__':
    fix_test_users()
