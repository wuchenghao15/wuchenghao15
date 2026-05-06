#!/usr/bin/env python3
from app.utils.db import db_manager
from app.utils.table_encryption import table_encryption

# 测试表名加密
print("测试表名加密:")
table_name = 'questions'
encrypted_name = table_encryption.encrypt_table_name(table_name)
print(f"原始表名: {table_name}")
print(f"加密表名: {encrypted_name}")

# 检查是否存在加密表
print("\n检查加密表是否存在:")
import sqlite3
conn = sqlite3.connect('data/mtscos_ai_project.db')
cursor = conn.cursor()
cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{encrypted_name}';")
result = cursor.fetchone()
if result:
    print(f"加密表 {encrypted_name} 存在")
else:
    print(f"加密表 {encrypted_name} 不存在")

# 检查加密表的结构
print(f"\n检查加密表 {encrypted_name} 的结构:")
try:
    cursor.execute(f'PRAGMA table_info({encrypted_name})')
    columns = cursor.fetchall()
    for column in columns:
        print(f"- {column[1]}: {column[2]}")
except Exception as e:
    print(f"错误: {e}")

# 检查原始表的结构
print("\n检查原始表 questions 的结构:")
    cursor.execute('PRAGMA table_info(questions)')
    columns = cursor.fetchall()
        print(f"- {column[1]}: {column[2]}")
    print(f"错误: {e}")
# 关闭连接
