# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
AI修复方案知识库管理器
用于存储和管理代码修复思路和解决方案
"""

import logging
logger = logging.getLogger(__name__)
import sqlite3
from contextlib import contextmanager
import json
from datetime import datetime
from typing import Dict, List, Optional
import os

DATABASE_PATH = '/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/flask-app/app.db'


def init_fix_knowledge_base():
    """初始化修复方案知识库表"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ai_fix_knowledge (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fix_id TEXT UNIQUE NOT NULL,
            fix_type TEXT NOT NULL,
            file_path TEXT NOT NULL,
            error_type TEXT,
            error_message TEXT,
            problem_description TEXT,
            root_cause TEXT,
            solution_approach TEXT,
            solution_code TEXT,
            best_practices TEXT,
            prevention_measures TEXT,
            related_patterns TEXT,
            ai_suggestions TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            verified INTEGER DEFAULT 0,
            success_count INTEGER DEFAULT 0,
            fail_count INTEGER DEFAULT 0
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ai_fix_steps (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fix_id TEXT NOT NULL,
            step_number INTEGER NOT NULL,
            step_description TEXT NOT NULL,
            step_code TEXT,
            expected_result TEXT,
            actual_result TEXT,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (fix_id) REFERENCES ai_fix_knowledge(fix_id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ai_fix_patterns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pattern_name TEXT UNIQUE NOT NULL,
            pattern_type TEXT NOT NULL,
            pattern_description TEXT NOT NULL,
            detection_rules TEXT,
            solution_template TEXT,
            examples TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    conn.commit()
    conn.close()

    print("修复方案知识库表初始化完成")


def upload_fix_knowledge(fix_data: Dict) -> bool:
    """上传修复方案到知识库"""
    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()

            cursor.execute('''
                INSERT OR REPLACE INTO ai_fix_knowledge
                (fix_id, fix_type, file_path, error_type, error_message, problem_description,
                root_cause, solution_approach, solution_code, best_practices,
                prevention_measures, related_patterns, ai_suggestions)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                fix_data.get('fix_id'),
                fix_data.get('fix_type'),
                fix_data.get('file_path'),
                fix_data.get('error_type'),
                fix_data.get('error_message'),
                fix_data.get('problem_description'),
                fix_data.get('root_cause'),
                fix_data.get('solution_approach'),
                fix_data.get('solution_code'),
                fix_data.get('best_practices'),
                fix_data.get('prevention_measures'),
                json.dumps(fix_data.get('related_patterns', []), ensure_ascii=False),
                fix_data.get('ai_suggestions')
            ))

            conn.commit()
        return True
    except Exception as e:
        logger.error(f"上传修复方案失败: {str(e)}")
        return False


def get_fix_knowledge(fix_id: str) -> Optional[Dict]:
    """获取修复方案"""
    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM ai_fix_knowledge WHERE fix_id = ?
            ''', (fix_id,))
            row = cursor.fetchone()

            if row:
                columns = [description[0] for description in cursor.description]
                return dict(zip(columns, row))
            return None
    except Exception as e:
        logger.error(f"获取修复方案失败: {str(e)}")
        return None


def get_all_fix_knowledge() -> List[Dict]:
    """获取所有修复方案"""
    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM ai_fix_knowledge')
            rows = cursor.fetchall()

            columns = [description[0] for description in cursor.description]
            return [dict(zip(columns, row)) for row in rows]
    except Exception as e:
        logger.error(f"获取所有修复方案失败: {str(e)}")
        return []


def delete_fix_knowledge(fix_id: str) -> bool:
    """删除修复方案"""
    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM ai_fix_knowledge WHERE fix_id = ?', (fix_id,))
            conn.commit()
        return True
    except Exception as e:
        logger.error(f"删除修复方案失败: {str(e)}")
        return False
