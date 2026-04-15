#!/usr/bin/env python3
import sqlite3
import os

# 获取数据库路径
db_path = os.path.join(os.getcwd(), 'app.db')

if not os.path.exists(db_path):
    print(f"Database file not found at: {db_path}")
    exit(1)

print(f"Checking database integrity at: {db_path}")

# 连接到数据库
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 执行完整性检查
print("Running integrity check...")
cursor.execute('PRAGMA integrity_check;')
result = cursor.fetchone()[0]
print(f"Integrity check result: {result}")

# 执行优化
if result == 'ok':
    print("Running database vacuum...")
    cursor.execute('VACUUM;')
    conn.commit()
    print("Database vacuum completed successfully.")
else:
    print("Database integrity check failed. Skipping vacuum.")

# 关闭连接
cursor.close()
conn.close()

print("Database maintenance completed.")
