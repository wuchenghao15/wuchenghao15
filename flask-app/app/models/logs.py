# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
日志记录模型
用于处理系统操作日志的记录和查询
"""

import sqlite3
from contextlib import contextmanager
import time
from app.config import Config
from app.utils.logging import logger
import logging
import json
import os

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

    def save(self):
        """保存日志记录"""
        conn = LogEntry._connect_db()
        cursor = conn.cursor()

        details_json = str(self.details or {})

        if self.log_id:
            cursor.execute(
                '''UPDATE logs SET event_type=?, user_id=?, vikey_hardware_id=?, session_id=?, timestamp=?, details=?
                   WHERE log_id=?''',
                (self.event_type, self.user_id, self.vikey_hardware_id, self.session_id, self.timestamp, details_json, self.log_id)
            )
        else:
            cursor.execute(
                '''INSERT INTO logs (event_type, user_id, vikey_hardware_id, session_id, timestamp, details)
                   VALUES (?, ?, ?, ?, ?, ?)''',
                (self.event_type, self.user_id, self.vikey_hardware_id, self.session_id, self.timestamp, details_json)
            )
            self.log_id = cursor.lastrowid

        conn.commit()
        logger.debug(f"保存日志记录成功: {self.log_id}")
        conn.close()
        return self.log_id
