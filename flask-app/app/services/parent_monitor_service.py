import os
import logging
logger = logging.getLogger(__name__)

# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""家长监控服务 - 家长查看孩子学习情况"""

import sqlite3
from contextlib import contextmanager
import uuid
import json
from datetime import datetime
from typing import List, Dict, Optional

app_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATABASE_PATH = os.path.join(app_root, 'app.db')


class ParentMonitorService:
    def __init__(self):
        self._init_tables()

    def _init_tables(self):
        """初始化数据库表"""
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()

            cursor.execute('''CREATE TABLE IF NOT EXISTS parent_child_relations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            parent_id TEXT NOT NULL,
            child_id TEXT NOT NULL,
            relation_type TEXT DEFAULT 'parent',
            is_active INTEGER DEFAULT 1,
            created_at TEXT,
            UNIQUE(parent_id, child_id)
            )''')

            cursor.execute('''CREATE TABLE IF NOT EXISTS parent_permissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            parent_id TEXT NOT NULL,
            child_id TEXT NOT NULL,
            can_view_progress INTEGER DEFAULT 1,
            can_view_exam_history INTEGER DEFAULT 1,
            can_view_learning_time INTEGER DEFAULT 1,
            can_set_goals INTEGER DEFAULT 0,
            can_receive_alerts INTEGER DEFAULT 1,
            updated_at TEXT,
            UNIQUE(parent_id, child_id)
            )''')

            cursor.execute('''CREATE TABLE IF NOT EXISTS child_learning_stats (
            stat_id TEXT PRIMARY KEY,
            child_id TEXT NOT NULL,
            date TEXT NOT NULL,
            total_learning_time INTEGER DEFAULT 0,
            completed_exams INTEGER DEFAULT 0,
            average_score REAL DEFAULT 0,
            topics_studied TEXT,
            created_at TEXT,
            UNIQUE(child_id, date)
            )''')

            cursor.execute('''CREATE TABLE IF NOT EXISTS parent_alerts (
            alert_id TEXT PRIMARY KEY,
            parent_id TEXT NOT NULL,
            child_id TEXT NOT NULL,
            alert_type TEXT NOT NULL,
            message TEXT,
            is_read INTEGER DEFAULT 0,
            created_at TEXT
            )''')

            conn.commit()

    def add_parent_child_relation(self, parent_id: str, child_id: str, relation_type: str = 'parent') -> bool:
        """添加家长-孩子关系"""
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            try:
                cursor.execute('''
                INSERT INTO parent_child_relations 
                (parent_id, child_id, relation_type, created_at)
                VALUES (?, ?, ?, ?)
                ''', (parent_id, child_id, relation_type, datetime.now().isoformat()))

                cursor.execute('''
                INSERT INTO parent_permissions 
                (parent_id, child_id, updated_at)
                VALUES (?, ?, ?)
                ''', (parent_id, child_id, datetime.now().isoformat()))

                conn.commit()
                return True
            except Exception as e:
                print(f"添加关系失败: {str(e)}")
                return False

    def get_children_by_parent(self, parent_id: str) -> List[Dict]:
        """获取家长关联的所有孩子"""
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('''
            SELECT child_id, relation_type, is_active, created_at 
            FROM parent_child_relations 
            WHERE parent_id = ? AND is_active = 1
            ''', (parent_id,))
            return [{'child_id': row[0], 'relation_type': row[1], 'is_active': row[2], 'created_at': row[3]} for row in cursor.fetchall()]

    def get_child_learning_stats(self, child_id: str, days: int = 30) -> List[Dict]:
        """获取孩子学习统计"""
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('''
            SELECT date, total_learning_time, completed_exams, average_score, topics_studied
            FROM child_learning_stats
            WHERE child_id = ?
            ORDER BY date DESC
            LIMIT ?
            ''', (child_id, days))
            return [{'date': row[0], 'learning_time': row[1], 'exams': row[2], 'score': row[3], 'topics': row[4]} for row in cursor.fetchall()]

    def get_parent_permissions(self, parent_id: str, child_id: str) -> Optional[Dict]:
        """获取家长对孩子的权限"""
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('''
            SELECT can_view_progress, can_view_exam_history, can_view_learning_time, can_set_goals, can_receive_alerts
            FROM parent_permissions
            WHERE parent_id = ? AND child_id = ?
            ''', (parent_id, child_id))
            row = cursor.fetchone()
            if row:
                return {
                    'view_progress': bool(row[0]),
                    'view_exam_history': bool(row[1]),
                    'view_learning_time': bool(row[2]),
                    'set_goals': bool(row[3]),
                    'receive_alerts': bool(row[4])
                }
            return None

    def create_alert(self, parent_id: str, child_id: str, alert_type: str, message: str) -> bool:
        """创建家长提醒"""
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            try:
                alert_id = str(uuid.uuid4())
                cursor.execute('''
                INSERT INTO parent_alerts (alert_id, parent_id, child_id, alert_type, message, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                ''', (alert_id, parent_id, child_id, alert_type, message, datetime.now().isoformat()))
                conn.commit()
                return True
            except Exception as e:
                print(f"创建提醒失败: {str(e)}")
                return False

    def get_unread_alerts(self, parent_id: str) -> List[Dict]:
        """获取未读提醒"""
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('''
            SELECT alert_id, child_id, alert_type, message, created_at
            FROM parent_alerts
            WHERE parent_id = ? AND is_read = 0
            ORDER BY created_at DESC
            ''', (parent_id,))
            return [{'alert_id': row[0], 'child_id': row[1], 'type': row[2], 'message': row[3], 'created_at': row[4]} for row in cursor.fetchall()]

    def mark_alert_read(self, alert_id: str) -> bool:
        """标记提醒为已读"""
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            try:
                cursor.execute('UPDATE parent_alerts SET is_read = 1 WHERE alert_id = ?', (alert_id,))
                conn.commit()
                return True
            except Exception as e:
                logger.info(f"标记已读失败: {str(e)}")
                return False
