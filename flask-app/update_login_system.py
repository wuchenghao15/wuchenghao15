#!/usr/bin/env python3
import sqlite3

# 连接数据库
conn = sqlite3.connect('data/mtscos_ai_project.db')
cursor = conn.cursor()

# 1. 为用户表添加手机号字段
print("为用户表添加手机号字段...")
try:
    cursor.execute("ALTER TABLE users ADD COLUMN phone TEXT;")
    conn.commit()
    print("用户表添加手机号字段成功")
except Exception as e:
    if "duplicate column name" in str(e):
        print("用户表已经存在手机号字段")
    else:
        print(f"添加手机号字段时出错: {e}")

# 2. 创建操作记录表
print("\n创建操作记录表...")
try:
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS user_operations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        operation_type TEXT,
        operation_description TEXT,
        ip_address TEXT,
        user_agent TEXT,
        device_type TEXT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')
    conn.commit()
    print("操作记录表创建成功")
except Exception as e:
    print(f"创建操作记录表时出错: {e}")

# 3. 检查修改后的用户表结构
print("\n修改后的用户表结构:")
try:
    cursor.execute('PRAGMA table_info(users)')
    columns = cursor.fetchall()
    for column in columns:
        print(f"- {column[1]}: {column[2]}")
except Exception as e:
    print(f"错误: {e}")

# 4. 检查操作记录表结构
print("\n操作记录表结构:")
try:
    cursor.execute('PRAGMA table_info(user_operations)')
    columns = cursor.fetchall()
    for column in columns:
        print(f"- {column[1]}: {column[2]}")
except Exception as e:
    print(f"错误: {e}")

# 关闭连接
conn.close()
