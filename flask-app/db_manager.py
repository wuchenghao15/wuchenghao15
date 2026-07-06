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
                print(f"[DB Manager] Error loading {db_name}: {e}")

build_table_mapping()

def get_db_for_table(table_name):
    return TABLE_TO_DB.get(table_name, 'other')

def get_db_path(db_name):
    return DATABASES.get(db_name)

def get_db_path_for_table(table_name):
    db_name = get_db_for_table(table_name)
    return get_db_path(db_name)

def connect(db_name):
    db_path = DATABASES.get(db_name)
    if not db_path or not os.path.exists(db_path):
        return None
    return sqlite3.connect(db_path, timeout=10)

def connect_for_table(table_name):
    db_name = get_db_for_table(table_name)
    return connect(db_name)

class SmartConnection:
    def __init__(self):
        self.connections = {}
        
    def get_connection(self, db_name):
        if db_name not in self.connections:
            db_path = DATABASES.get(db_name)
            if db_path and os.path.exists(db_path):
                self.connections[db_name] = sqlite3.connect(db_path, timeout=10)
                self.connections[db_name].row_factory = sqlite3.Row
        return self.connections.get(db_name)
    
    def execute(self, sql, params=None):
        table_name = extract_table_name(sql)
        db_name = get_db_for_table(table_name)
        conn = self.get_connection(db_name)
        
        if conn:
            cursor = conn.cursor()
            if params:
                result = cursor.execute(sql, params)
            else:
                result = cursor.execute(sql)
            conn.commit()
            return result
        return None
    
    def fetchone(self, sql, params=None):
        table_name = extract_table_name(sql)
        db_name = get_db_for_table(table_name)
        conn = self.get_connection(db_name)
        
        if conn:
            cursor = conn.cursor()
            if params:
                cursor.execute(sql, params)
            else:
                cursor.execute(sql)
            return cursor.fetchone()
        return None
    
    def fetchall(self, sql, params=None):
        table_name = extract_table_name(sql)
        db_name = get_db_for_table(table_name)
        conn = self.get_connection(db_name)
        
        if conn:
            cursor = conn.cursor()
            if params:
                cursor.execute(sql, params)
            else:
                cursor.execute(sql)
            return cursor.fetchall()
        return []
    
    def close(self):
        for conn in self.connections.values():
            conn.close()
        self.connections = {}

def extract_table_name(sql):
    import re
    sql = sql.strip().upper()
    
    patterns = [
        r'FROM\s+(\w+)',
        r'INSERT\s+INTO\s+(\w+)',
        r'UPDATE\s+(\w+)',
        r'DELETE\s+FROM\s+(\w+)',
        r'CREATE\s+TABLE\s+(\w+)',
        r'ALTER\s+TABLE\s+(\w+)',
        r'DROP\s+TABLE\s+(\w+)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, sql)
        if match:
            return match.group(1).lower()
    
    return 'other'

smart_conn = SmartConnection()

def get_db_connection():
    return smart_conn