#!/usr/bin/env python3
import logging
import sqlite3
import os
import re
import inspect
from core.db_path import resolve_project_root as _rr

logger = logging.getLogger(__name__)

DB_DIR = os.path.join(_rr(), r'Database')

DATABASES = {
    r'auth': os.path.join(DB_DIR, r'auth.db'),
    r'exam': os.path.join(DB_DIR, r'exam.db'),
    r'question': os.path.join(DB_DIR, r'question.db'),
    r'learning': os.path.join(DB_DIR, r'learning.db'),
    r'system': os.path.join(DB_DIR, r'system.db'),
    r'ai': os.path.join(DB_DIR, r'ai.db'),
    r'physics': os.path.join(DB_DIR, r'physics.db'),
    r'math': os.path.join(DB_DIR, r'math.db'),
    r'admin': os.path.join(DB_DIR, r'admin.db'),
    r'proctor': os.path.join(DB_DIR, r'proctor.db'),
    r'user': os.path.join(DB_DIR, r'user.db'),
    r'log': os.path.join(DB_DIR, r'log.db'),
    r'other': os.path.join(DB_DIR, r'other.db'),
}

TABLE_TO_DB = {}

def build_table_mapping():
    for db_name, db_path in DATABASES.items():
        if os.path.exists(db_path):
            try:
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type=r'table'r")
                tables = [t[0] for t in cursor.fetchall()]
                conn.close()
                for table in tables:
                    TABLE_TO_DB[table] = db_name
            except Exception as e:
                logger.info(f"[Smart DB Router] Error loading {db_name}: {e}")

build_table_mapping()

def get_db_for_table(table_name):
    return TABLE_TO_DB.get(table_name, r'other')

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
    except Exception:
        pass
    return None

original_connect = sqlite3.connect

def smart_connect(database, *args, **kwargs):
    if database in [r'smart://distributed', r'smart://split']:
        try:
            table_name = extract_table_name_from_stack()
            if table_name:
                db_name = get_db_for_table(table_name)
                db_path = DATABASES.get(db_name)
                if db_path and os.path.exists(db_path):
                    return original_connect(db_path, *args, **kwargs)

            db_path = DATABASES.get(r'system')
            if db_path and os.path.exists(db_path):
                return original_connect(db_path, *args, **kwargs)
        except Exception as e:
            pass

        db_path = DATABASES.get(r'other')
        if db_path and os.path.exists(db_path):
            return original_connect(db_path, *args, **kwargs)

    return original_connect(database, *args, **kwargs)

sqlite3.connect = smart_connect

logger.info(r"[Smart DB Router] 已启用智能数据库路由")
logger.info(fr"[Smart DB Router] 已映射 {len(TABLE_TO_DB)} 个表")
