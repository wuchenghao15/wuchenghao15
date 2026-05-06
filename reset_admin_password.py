#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
重置admin用户密码

import sqlite3
from werkzeug.security import generate_password_hash

# 数据库连接
conn = sqlite3.connect('/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/flask-app/app.db')
cursor = conn.cursor()

# 新密码
new_password = "admin123"
# 生成scrypt哈希
hashed_password = generate_password_hash(new_password)

# 更新admin用户密码
cursor.execute('''
    UPDATE user SET password = ? WHERE username = 'admin'
''', (hashed_password,))

# 提交更改
conn.commit()

# 验证更新
cursor.execute('''
''')
user = cursor.fetchone()

if user:
    print(f"成功更新admin用户密码！")
    print(f"用户名: {user[0]}")
    print(f"新密码: {new_password}")
    print(f"哈希密码: {user[1]}")
else:
    print("更新失败，未找到admin用户！")

# 关闭连接
conn.close()

"""