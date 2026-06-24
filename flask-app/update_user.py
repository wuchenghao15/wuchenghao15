#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sqlite3
import os
import hashlib
import base64

db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app.db')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

password = 'LoginMe.1988$'
salt = os.urandom(16)
hashed = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 100000)
stored_password = base64.b64encode(salt + hashed).decode('utf-8')

cursor.execute('''
    UPDATE users 
    SET role='hardware_vikey_admin', 
        password=?, 
        super_admin_approved=1, 
        hardware_admin_approved=1,
        is_active=1,
        updated_at=CURRENT_TIMESTAMP
    WHERE username='wuchenghao15'
''', (stored_password,))
conn.commit()

cursor.execute('SELECT id, username, role, super_admin_approved, hardware_admin_approved, is_active, password FROM users WHERE username = ?', ('wuchenghao15',))
row = cursor.fetchone()
print('更新成功:')
print(f'  用户ID: {row[0]}')
print(f'  用户名: {row[1]}')
print(f'  角色: {row[2]}')
print(f'  超级管理员批准: {row[3]}')
print(f'  硬件管理员批准: {row[4]}')
print(f'  激活状态: {row[5]}')
print(f'  密码哈希格式: PBKDF2 (base64编码)')
conn.close()
