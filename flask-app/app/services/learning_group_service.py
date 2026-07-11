# -*- coding: utf-8 -*-
import os
from flask import Blueprint, jsonify, request
#!/usr/bin/env python3
"""学习小组服务 - 支持多人协作学习"""

import sqlite3
from contextlib import contextmanager
import uuid
import json
from datetime import datetime
from typing import List, Dict, Optional

app_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATABASE_PATH = os.path.join(app_root, 'app.db')

class LearningGroupService:
    def __init__(self):
        self._init_tables()
    
    def _init_tables(self):
        """初始化数据库表"""
        with sqlite3.connect(DATABASE_PATH) as conn:
            conn_cursor = conn.cursor()
            cursor = conn.cursor()
            
            cursor.execute('''CREATE TABLE IF NOT EXISTS learning_groups (
            group_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT,
            creator_id TEXT NOT NULL,
            max_members INTEGER DEFAULT 10,
            is_active INTEGER DEFAULT 1,
            created_at TEXT,
            updated_at TEXT
            )''')
            
            cursor.execute('''CREATE TABLE IF NOT EXISTS group_members (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            group_id TEXT NOT NULL,
            user_id TEXT NOT NULL,
            role TEXT DEFAULT 'member',
            joined_at TEXT,
            FOREIGN KEY (group_id) REFERENCES learning_groups(group_id),
            UNIQUE(group_id, user_id)
            )''')
            
            cursor.execute('''CREATE TABLE IF NOT EXISTS group_activities (
            activity_id TEXT PRIMARY KEY,
            group_id TEXT NOT NULL,
            activity_type TEXT NOT NULL,
            content TEXT,
            created_by TEXT,
            created_at TEXT,
            FOREIGN KEY (group_id) REFERENCES learning_groups(group_id)
            )''')
            
            cursor.execute('''CREATE TABLE IF NOT EXISTS group_progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            group_id TEXT NOT NULL,
            user_id TEXT NOT NULL,
            exam_id TEXT,
            score REAL,
            completed_at TEXT,
            FOREIGN KEY (group_id) REFERENCES learning_groups(group_id),
            UNIQUE(group_id, user_id, exam_id)
            )''')
            
            conn.commit()
    
    def create_group(self, name: str, description: str, creator_id: str, max_members: int = 10) -> Dict:
        """创建学习小组"""
        group_id = str(uuid.uuid4())[:16]
        now = datetime.now().isoformat()
        
        with sqlite3.connect(DATABASE_PATH) as conn:
            conn_cursor = conn.cursor()
            cursor = conn.cursor()
            
            cursor.execute('''
            INSERT INTO learning_groups 
            (group_id, name, description, creator_id, max_members, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (group_id, name, description, creator_id, max_members, now, now))
            
            cursor.execute('''
            INSERT INTO group_members (group_id, user_id, role, joined_at)
            VALUES (?, ?, 'admin', ?)
            ''', (group_id, creator_id, now))
            
            conn.commit()
        
        return {'group_id': group_id, 'name': name, 'description': description}