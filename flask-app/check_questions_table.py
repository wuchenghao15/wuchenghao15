#!/usr/bin/env python3
import sqlite3

# 连接数据库
conn = sqlite3.connect('data/mtscos_ai_project.db')
cursor = conn.cursor()

# 检查questions表的结构
print("检查questions表的结构:")
try:
    cursor.execute('PRAGMA table_info(questions)')
    columns = cursor.fetchall()
    for column in columns:
        print(f"- {column[1]}: {column[2]}")
except Exception as e:
    print(f"错误: {e}")

# 关闭连接
conn.close()
