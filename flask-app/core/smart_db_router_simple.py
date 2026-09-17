#!/usr/bin/env python3
import sqlite3
import os

DB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'split_databases')

DATABASES = {
    'auth': os.path.join(DB_DIR, 'auth.db'),
    'exam': os.path.join(DB_DIR, 'exam.db'),
    'question': os.path.join(DB_DIR, 'question.db'),
    'learning': os.path.join(DB_DIR, 'learning.db'),
    'system': os.path.join(DB_DIR, 'system.db'),
    'ai': os.path.join(DB_DIR, 'ai.db'),
    'physics': os.path.join(DB_DIR, 'physics.db'),
    'math': os.path.join(DB_DIR, 'math.db'),
    'admin': os.path.join(DB_DIR, 'admin.db'),
    'proctor': os.path.join(DB_DIR, 'proctor.db'),
    'user': os.path.join(DB_DIR, 'user.db'),
    'log': os.path.join(DB_DIR, 'log.db'),
    'other': os.path.join(DB_DIR, 'other.db'),
}

TABLE_TO_DB = {}

def build_table_mapping():
    for db_name, db_path in DATABASES.items():
        if os.path.exists(db_path):
            try:
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [t[0] for t in cursor.fetchall()]
                conn.close()
                for table in tables:
                    TABLE_TO_DB[table] = db_name
            except Exception as e:
                print(f"[Smart DB Router] Error loading {db_name}: {e}")

build_table_mapping()

original_connect = sqlite3.connect

def smart_connect(database, *args, **kwargs):
    if database in ['smart://distributed', 'smart://split']:
        db_path = DATABASES.get('system')
        if db_path and os.path.exists(db_path):
            return original_connect(db_path, *args, **kwargs)
        
        db_path = DATABASES.get('other')
        if db_path and os.path.exists(db_path):
            return original_connect(db_path, *args, **kwargs)
    
    return original_connect(database, *args, **kwargs)

sqlite3.connect = smart_connect

print("[Smart DB Router Simple] 已启用智能数据库路由")
print(f"[Smart DB Router Simple] 已映射 {len(TABLE_TO_DB)} 个表")