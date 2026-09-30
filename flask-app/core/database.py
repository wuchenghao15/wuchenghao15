# -*- coding: utf-8 -*-
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Database management module
"""

import sqlite3
import os
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from .config import config

class DatabaseManager:
    """SQLite database manager with connection pooling"""
    
    def __init__(self):
        self.db_path = config.get("database.path", "app.db")
        self.conn = None
        self._ensure_connection()
    
    def _ensure_connection(self):
        """Ensure database connection is established"""
        if self.conn is None:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row
    
    def execute(self, query: str, params: tuple = ()) -> sqlite3.Cursor:
        """Execute SQL query"""
        self._ensure_connection()
        cursor = self.conn.cursor()
        cursor.execute(query, params)
        return cursor
    
    def fetch_one(self, query: str, params: tuple = ()) -> Optional[Dict[str, Any]]:
        """Fetch single row"""
        cursor = self.execute(query, params)
        row = cursor.fetchone()
        if row:
            return dict(row)
        return None
    
    def fetch_all(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """Fetch all rows"""
        cursor = self.execute(query, params)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    
    def commit(self):
        """Commit transaction"""
        if self.conn:
            self.conn.commit()
    
    def rollback(self):
        """Rollback transaction"""
        if self.conn:
            self.conn.rollback()
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            self.conn = None
    
    def backup(self, backup_path: str = None) -> str:
        """Create database backup"""
        if backup_path is None:
            backup_path = config.get("database.backup_path", "backups/")
        
        os.makedirs(backup_path, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = f"{backup_path}backup_{timestamp}.db"
        
        try:
            backup_conn = sqlite3.connect(backup_file)
            self.conn.backup(backup_conn)
            backup_conn.close()
            return backup_file
        except Exception as e:
            print(f"Backup failed: {e}")
            return ""
    
    def restore(self, backup_file: str) -> bool:
        """Restore database from backup"""
        try:
            self.close()
            os.remove(self.db_path)
            with open(backup_file, 'rb') as src, open(self.db_path, 'wb') as dst:
                dst.write(src.read())
            self._ensure_connection()
            return True
        except Exception as e:
            print(f"Restore failed: {e}")
            return False
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.rollback()
        else:
            self.commit()
        self.close()

# Global database instance
db = DatabaseManager()
