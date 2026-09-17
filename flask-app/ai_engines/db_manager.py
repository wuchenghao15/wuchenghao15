"""db_manager 兼容模块 (SYS-NORM修复)."""
import sqlite3, os
_DB = os.environ.get("MT_MAIN_DB_PATH", os.path.join(os.path.dirname(__file__), "app.db"))
class db_manager:
    @staticmethod
    def get_connection():
        return sqlite3.connect(_DB, timeout=15)
    @staticmethod
    def execute(sql, args=()):
        c = sqlite3.connect(_DB, timeout=15)
        try:
            cur = c.execute(sql, args); c.commit(); return cur.fetchall()
        finally:
            c.close()
    @staticmethod
    def query(sql, args=()):
        return db_manager.execute(sql, args)

DATABASES = {"default": {"ENGINE": "sqlite3", "NAME": _DB}}

import os as _os
DB_DIR = _os.path.dirname(_DB)

def build_table_mapping(*a, **kw):
    return {}

def get_db_for_table(table_name=None):
    return db_manager()

def connect(*a, **kw):
    import sqlite3, os
    return sqlite3.connect(os.environ.get('MT_MAIN_DB_PATH', ''), timeout=15)
