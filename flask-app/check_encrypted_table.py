#!/usr/bin/env python3
import sqlite3

# 连接数据库
conn = sqlite3.connect('data/mtscos_ai_project.db')
cursor = conn.cursor()

# 检查加密表的结构
encrypted_table_name = 't_de70b7adf040777a'
print(f"加密表 {encrypted_table_name} 的结构:")
cursor.execute(f'PRAGMA table_info({encrypted_table_name})')
columns = cursor.fetchall()
for column in columns:
    print(f"- {column[1]}: {column[2]}")

# 关闭连接
conn.close()
