# -*- coding: utf-8 -*-
#!/usr/bin/env python3
import sqlite3

DATABASE_PATH = '/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/flask-app/app.db'

with sqlite3.connect(DATABASE_PATH) as conn:
    cursor = conn.cursor()
    cursor.execute('SELECT username, password, role FROM users WHERE username = ?', ('admin',))
    admin_user = cursor.fetchone()
    if admin_user:
        print('用户名:', admin_user[0])
        print('密码哈希:', admin_user[1])
        print('角色:', admin_user[2])
        print('密码哈希长度:', len(admin_user[1]))
