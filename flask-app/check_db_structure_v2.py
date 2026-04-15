#!/usr/bin/env python3
import sqlite3

# 连接数据库
conn = sqlite3.connect('data/mtscos_ai_project.db')
cursor = conn.cursor()

# 检查所有表
print("所有表:")
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()
for table in tables:
    print(f"- {table[0]}")

# 检查加密表的结构
print("\n检查加密表 t_de70b7adf040777a 的结构:")
try:
    cursor.execute('PRAGMA table_info(t_de70b7adf040777a)')
    columns = cursor.fetchall()
    for column in columns:
        print(f"- {column[1]}: {column[2]}")
except Exception as e:
    print(f"错误: {e}")

# 关闭连接
conn.close()
