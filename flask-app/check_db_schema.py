# -*- coding: utf-8 -*-
#!/usr/bin/env python3
import sqlite3
import os

DATABASE_PATH = '/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/flask-app/app.db'

with sqlite3.connect(DATABASE_PATH) as conn:
    cursor = conn.cursor()
    
    # 获取所有表名
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    
    print("数据库表:")
    for table in tables:
        print(f"  - {table[0]}")
    
    # 检查users表结构
    print("\nusers表结构:")
    cursor.execute("PRAGMA table_info(users)")
    columns = cursor.fetchall()
    for col in columns:
        print(f"  {col[1]} ({col[2]}) - {'PRIMARY KEY' if col[5] else ''}")
    
    # 查看一些用户数据
    print("\n用户数据示例:")
    cursor.execute("SELECT id, username, role, email FROM users LIMIT 10")
    users = cursor.fetchall()
    for user in users:
        print(f"  {user}")
