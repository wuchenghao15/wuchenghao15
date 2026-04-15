#!/usr/bin/env python3
"""
日志记录模型
用于处理系统操作日志的记录和查询
"""

import sqlite3
import json
import time
from app.config import Config
from app.utils.logging import logger

class LogEntry:
    """操作日志数据模型"""
    
    def __init__(self, log_id=None, event_type=None, user_id=None, vikey_hardware_id=None, session_id=None, timestamp=None, details=None):
        self.log_id = log_id
        self.event_type = event_type
        self.user_id = user_id
        self.vikey_hardware_id = vikey_hardware_id
        self.session_id = session_id
        self.timestamp = timestamp
        self.details = details or {}
    
    @staticmethod
    def _connect_db():
        """连接数据库"""
        return sqlite3.connect(Config.DATABASE_PATH)
    
    @staticmethod
    def create_table():
        """创建日志表"""
        conn = LogEntry._connect_db()
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT NOT NULL,
                user_id TEXT,
                vikey_hardware_id TEXT,
                session_id TEXT,
                timestamp REAL NOT NULL,
                details TEXT NOT NULL DEFAULT '{}'
            )
        ''')
        conn.commit()
        conn.close()
        logger.info("日志表创建成功")
    
    @staticmethod
    def create(event_type, user_id=None, vikey_hardware_id=None, session_id=None, details=None):
        """创建日志记录"""
        conn = LogEntry._connect_db()
        cursor = conn.cursor()
        
        # 确保details是JSON字符串
        details_json = json.dumps(details or {})
        
        cursor.execute('''
            INSERT INTO logs (event_type, user_id, vikey_hardware_id, session_id, timestamp, details)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (event_type, user_id, vikey_hardware_id, session_id, time.time(), details_json))
        
        log_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        logger.debug(f"创建日志记录成功: {log_id}, 事件类型: {event_type}")
        return LogEntry(log_id, event_type, user_id, vikey_hardware_id, session_id, time.time(), details)
    
    @staticmethod
    def get_by_id(log_id):
        """通过ID获取日志记录"""
        conn = LogEntry._connect_db()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM logs WHERE id=?', (log_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return LogEntry(
                log_id=row[0],
                event_type=row[1],
                user_id=row[2],
                vikey_hardware_id=row[3],
                session_id=row[4],
                timestamp=row[5],
                details=json.loads(row[6]) if row[6] else {}
            )
        return None
    
    @staticmethod
    def get_by_session(session_id):
        """通过会话ID获取日志记录"""
        conn = LogEntry._connect_db()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM logs WHERE session_id=? ORDER BY timestamp DESC', (session_id,))
        rows = cursor.fetchall()
        conn.close()
        
        logs = []
        for row in rows:
            logs.append(LogEntry(
                log_id=row[0],
                event_type=row[1],
                user_id=row[2],
                vikey_hardware_id=row[3],
                session_id=row[4],
                timestamp=row[5],
                details=json.loads(row[6]) if row[6] else {}
            ))
        return logs
    
    @staticmethod
    def get_by_user(user_id):
        """通过用户ID获取日志记录"""
        conn = LogEntry._connect_db()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM logs WHERE user_id=? ORDER BY timestamp DESC LIMIT 100', (user_id,))
        rows = cursor.fetchall()
        conn.close()
        
        logs = []
        for row in rows:
            logs.append(LogEntry(
                log_id=row[0],
                event_type=row[1],
                user_id=row[2],
                vikey_hardware_id=row[3],
                session_id=row[4],
                timestamp=row[5],
                details=json.loads(row[6]) if row[6] else {}
            ))
        return logs
    
    @staticmethod
    def get_by_event_type(event_type):
        """通过事件类型获取日志记录"""
        conn = LogEntry._connect_db()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM logs WHERE event_type=? ORDER BY timestamp DESC LIMIT 100', (event_type,))
        rows = cursor.fetchall()
        conn.close()
        
        logs = []
        for row in rows:
            logs.append(LogEntry(
                log_id=row[0],
                event_type=row[1],
                user_id=row[2],
                vikey_hardware_id=row[3],
                session_id=row[4],
                timestamp=row[5],
                details=json.loads(row[6]) if row[6] else {}
            ))
        return logs
    
    @staticmethod
    def get_latest(limit=50):
        """获取最新的日志记录"""
        conn = LogEntry._connect_db()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM logs ORDER BY timestamp DESC LIMIT ?', (limit,))
        rows = cursor.fetchall()
        conn.close()
        
        logs = []
        for row in rows:
            logs.append(LogEntry(
                log_id=row[0],
                event_type=row[1],
                user_id=row[2],
                vikey_hardware_id=row[3],
                session_id=row[4],
                timestamp=row[5],
                details=json.loads(row[6]) if row[6] else {}
            ))
        return logs
    
    def save(self):
        """保存日志记录"""
        conn = LogEntry._connect_db()
        cursor = conn.cursor()
        
        # 确保details是JSON字符串
        details_json = json.dumps(self.details or {})
        
        if self.log_id:
            # 更新现有记录
            cursor.execute('''
                UPDATE logs SET event_type=?, user_id=?, vikey_hardware_id=?, session_id=?, timestamp=?, details=?
                WHERE id=?
            ''', (self.event_type, self.user_id, self.vikey_hardware_id, self.session_id, self.timestamp, details_json, self.log_id))
        else:
            # 创建新记录
            cursor.execute('''
                INSERT INTO logs (event_type, user_id, vikey_hardware_id, session_id, timestamp, details)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (self.event_type, self.user_id, self.vikey_hardware_id, self.session_id, self.timestamp, details_json))
            self.log_id = cursor.lastrowid
        
        conn.commit()
        conn.close()
        logger.debug(f"保存日志记录成功: {self.log_id}")
        return self
