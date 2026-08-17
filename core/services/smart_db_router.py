#!/usr/bin/env python3
import sqlite3
import os
import re
import inspect
from core.db_path import resolve_project_root as _rr

DB_DIR = os.path.join(_rr(), 'Database')

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
                logger.info(f"[Smart DB Router] Error loading {db_name}: {e}")

build_table_mapping()

def get_db_for_table(table_name):
    return TABLE_TO_DB.get(table_name, 'other')

def extract_table_name_from_sql(sql):
    sql_upper = sql.strip().upper()
    
    patterns = [
        r'FROM\s+(\w+)',
        r'INSERT\s+INTO\s+(\w+)',
        r'UPDATE\s+(\w+)',
        r'DELETE\s+FROM\s+(\w+)',
        r'CREATE\s+TABLE\s+(\w+)',
        r'ALTER\s+TABLE\s+(\w+)',
        r'DROP\s+TABLE\s+(\w+)',
        r'PRAGMA\s+table_info\((\w+)\)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, sql_upper)
        if match:
            return match.group(1).lower()
    return None

def extract_table_name_from_stack():
    try:
        stack = inspect.stack()
        for frame in stack[3:8]:
            source = frame.code_context
            if source:
                line = source[0].strip()
                table_name = extract_table_name_from_sql(line)
                if table_name:
                    return table_name
    except:
        pass
    return None

original_connect = sqlite3.connect

def smart_connect(database, *args, **kwargs):
    if database in ['smart://distributed', 'smart://split']:
        try:
            table_name = extract_table_name_from_stack()
            if table_name:
                db_name = get_db_for_table(table_name)
                db_path = DATABASES.get(db_name)
                if db_path and os.path.exists(db_path):
                    return original_connect(db_path, *args, **kwargs)
            
            db_path = DATABASES.get('system')
            if db_path and os.path.exists(db_path):
                return original_connect(db_path, *args, **kwargs)
        except Exception as e:
            pass
        
        db_path = DATABASES.get('other')
        if db_path and os.path.exists(db_path):
            return original_connect(db_path, *args, **kwargs)
    
    return original_connect(database, *args, **kwargs)

sqlite3.connect = smart_connect

logger.info("[Smart DB Router] 已启用智能数据库路由")
logger.info(f"[Smart DB Router] 已映射 {len(TABLE_TO_DB)} 个表")