#!/usr/bin/env python3
import sqlite3
import os
import sys

db_path = None

# 搜索数据库文件
search_paths = [
    os.path.join(os.path.dirname(__file__), 'instance', 'mtscos.db'),
    os.path.join(os.path.dirname(__file__), 'data', 'mtscos.db'),
    os.path.join(os.path.dirname(__file__), 'app.db'),
]

for p in search_paths:
    if os.path.exists(p):
        db_path = p
        break

if not db_path:
    for root, dirs, files in os.walk('.'):
        for f in files:
            if f.endswith('.db') and 'mtscos' in f.lower():
                db_path = os.path.join(root, f)
                break
        if db_path:
            break

print('DB path:', db_path)
if not db_path:
    print('No database found!')
    sys.exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 检查表是否存在
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%layout%'")
tables = cursor.fetchall()
print('Layout tables:', tables)

# 查询方案数
if tables:
    cursor.execute('SELECT COUNT(*) FROM layout_adjustment_plans')
    count = cursor.fetchone()[0]
    print('Total plans:', count)
    
    cursor.execute('SELECT plan_id, name, total_pages, total_issues, average_score, created_at FROM layout_adjustment_plans ORDER BY created_at DESC LIMIT 3')
    for row in cursor.fetchall():
        print(f'  Plan: {row[0][:8]}... | {row[1]} | {row[2]}页 | {row[3]}问题 | {row[4]}分')
    
    # 页面分析记录
    cursor.execute('SELECT COUNT(*) FROM layout_page_analyses')
    analysis_count = cursor.fetchone()[0]
    print('Total page analyses:', analysis_count)
    
    # 应用记录
    cursor.execute('SELECT COUNT(*) FROM layout_application_records')
    app_count = cursor.fetchone()[0]
    print('Total application records:', app_count)

conn.close()
