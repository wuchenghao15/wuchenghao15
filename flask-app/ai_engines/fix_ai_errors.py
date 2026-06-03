# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
修复AI模块启动错误,确保应用能正常运行

import sqlite3
from contextlib import contextmanager

# 获取数据库路径
db_path = '/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/flask-app/app.db'

# 连接到数据库
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 创建ai_instances表
print("创建ai_instances表...")
cursor.execute('''
CREATE TABLE IF NOT EXISTS ai_instances (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ai_name TEXT UNIQUE NOT NULL,
    ai_type TEXT NOT NULL,
    description TEXT DEFAULT '',
    status TEXT DEFAULT 'active',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
)
''')

# 创建ai_collections表
print("创建ai_collections表...")
cursor.execute('''
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    collection_name TEXT UNIQUE NOT NULL,
    status TEXT DEFAULT 'active',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
)

conn.commit()


"""