#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""数据库绑定模块"""
import logging
import sqlite3
from contextlib import contextmanager
import os
from datetime import datetime
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self):
        self.connection = None
        self.db_path = None
        self.connected = False
        self.db_type = 'sqlite'
        logger.info("数据库管理器初始化完成")

    def connect(self, db_path: str = 'app.db'):
        try:
            self.db_path = db_path
            self.connection = sqlite3.connect(db_path)
            self.connection.row_factory = sqlite3.Row
            self.connected = True
            self._create_tables()
            logger.info(f"数据库连接成功: {db_path}")
            return True
        except Exception as e:
            logger.error(f"数据库连接失败: {str(e)}")
            return False

    def disconnect(self):
        if self.connection:
            self.connection.close()
            self.connected = False
            logger.info("数据库连接已断开")

    def _create_tables(self):
        cursor = self.connection.cursor()
        cursor.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE NOT NULL, password TEXT NOT NULL, email TEXT, role TEXT DEFAULT 'user', active INTEGER DEFAULT 1, created_at TEXT, updated_at TEXT)")
        cursor.execute("CREATE TABLE IF NOT EXISTS sessions (id TEXT PRIMARY KEY, user_id INTEGER, created_at TEXT, expires_at TEXT, last_activity TEXT, FOREIGN KEY (user_id) REFERENCES users(id))")
        cursor.execute("CREATE TABLE IF NOT EXISTS permissions (id INTEGER PRIMARY KEY AUTOINCREMENT, permission_id TEXT UNIQUE NOT NULL, description TEXT, created_at TEXT)")
        cursor.execute("CREATE TABLE IF NOT EXISTS roles (id INTEGER PRIMARY KEY AUTOINCREMENT, role_id TEXT UNIQUE NOT NULL, description TEXT, created_at TEXT)")
        cursor.execute("CREATE TABLE IF NOT EXISTS role_permissions (role_id TEXT, permission_id TEXT, PRIMARY KEY (role_id, permission_id))")
        cursor.execute("CREATE TABLE IF NOT EXISTS audit_logs (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, action TEXT, resource TEXT, details TEXT, timestamp TEXT, ip_address TEXT)")
        self.connection.commit()
        logger.info("数据库表创建完成")

    def execute(self, query: str, params: tuple = None) -> Any:
        if not self.connected:
            raise Exception("数据库未连接")
        cursor = self.connection.cursor()
        try:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            self.connection.commit()
            return cursor
        except Exception as e:
            logger.error(f"执行SQL失败: {str(e)}")
            raise

    def fetch_one(self, query: str, params: tuple = None) -> Optional[Dict[str, Any]]:
        cursor = self.execute(query, params)
        if cursor:
            row = cursor.fetchone()
            if row:
                return dict(row)
        return None

    def fetch_all(self, query: str, params: tuple = None) -> list:
        cursor = self.execute(query, params)
        if cursor:
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        return []

    def insert_user(self, username: str, password: str, email: str = "", role: str = "user"):
        now = datetime.now().isoformat()
        self.execute("INSERT OR IGNORE INTO users (username, password, email, role, active, created_at, updated_at) VALUES (?, ?, ?, ?, 1, ?, ?)", (username, password, email, role, now, now))
        logger.info(f"用户插入成功: {username}")

    def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        return self.fetch_one("SELECT * FROM users WHERE username = ? AND active = 1", (username,))

    def log_action(self, user_id: int, action: str, resource: str, details: Dict[str, Any] = None, ip_address: str = ""):
        now = datetime.now().isoformat()
        details_json = str(details) if details else "{}"
        self.execute("INSERT INTO audit_logs (user_id, action, resource, details, timestamp, ip_address) VALUES (?, ?, ?, ?, ?, ?)", (user_id, action, resource, details_json, now, ip_address))

db_manager = DatabaseManager()

def init_db(db_path: str = 'app.db'):
    logger.info("初始化数据库...")
    success = db_manager.connect(db_path)
    if success:
        import hashlib
        admin_password = hashlib.sha256('admin123'.encode()).hexdigest()
        db_manager.insert_user('admin', admin_password, 'admin@example.com', 'admin')
        logger.info("数据库初始化完成")
    return success
