#!/usr/bin/env python3
import sqlite3

# 连接数据库
conn = sqlite3.connect('data/mtscos_ai_project.db')
cursor = conn.cursor()

# 检查用户表的结构
print("检查用户表的结构:")
try:
    cursor.execute('PRAGMA table_info(users)')
    columns = cursor.fetchall()
    for column in columns:
        print(f"- {column[1]}: {column[2]}")
except Exception as e:
    print(f"错误: {e}")

# 检查是否存在项目历史表
print("\n检查是否存在项目历史表:")
try:
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='project_history';")
    result = cursor.fetchone()
    if result:
        print("项目历史表存在")
        # 检查项目历史表的结构
        cursor.execute('PRAGMA table_info(project_history)')
        columns = cursor.fetchall()
        for column in columns:
            print(f"- {column[1]}: {column[2]}")
    else:
        print("项目历史表不存在")
except Exception as e:
    print(f"错误: {e}")

# 关闭连接
conn.close()
