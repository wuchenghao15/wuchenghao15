# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""题库维护与分类系统 - 管理题库分类和标签"""

import sqlite3
from contextlib import contextmanager
import uuid
import json
from datetime import datetime
from typing import List, Dict, Optional
import os

DATABASE_PATH = '/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/flask-app/app.db'


class QuestionBankService:
    def __init__(self):
        self._init_tables()

    def _init_tables(self):
        """初始化数据库表"""
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()

        cursor.execute('''CREATE TABLE IF NOT EXISTS question_categories (
            category_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            parent_id TEXT,
            subject TEXT,
            description TEXT,
            order_num INTEGER DEFAULT 0,
            is_active INTEGER DEFAULT 1,
            created_at TEXT,
            FOREIGN KEY (parent_id) REFERENCES question_categories(category_id)
        )''')

        cursor.execute('''CREATE TABLE IF NOT EXISTS question_tags (
            tag_id TEXT PRIMARY KEY,
            name TEXT NOT NULL UNIQUE,
            color TEXT DEFAULT '#1F2937',
            description TEXT,
            created_at TEXT
        )''')

        cursor.execute('''CREATE TABLE IF NOT EXISTS question_tag_mapping (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question_id TEXT NOT NULL,
            tag_id TEXT NOT NULL,
            FOREIGN KEY (question_id) REFERENCES exam_questions(question_id),
            FOREIGN KEY (tag_id) REFERENCES question_tags(tag_id),
            UNIQUE(question_id, tag_id)
        )''')

        cursor.execute('''CREATE TABLE IF NOT EXISTS question_banks (
            bank_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT,
            category_id TEXT,
            is_public INTEGER DEFAULT 1,
            created_by TEXT,
            created_at TEXT,
            FOREIGN KEY (category_id) REFERENCES question_categories(category_id)
        )''')

        cursor.execute('''CREATE TABLE IF NOT EXISTS bank_question_mapping (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            bank_id TEXT NOT NULL,
            question_id TEXT NOT NULL,
            FOREIGN KEY (bank_id) REFERENCES question_banks(bank_id),
            FOREIGN KEY (question_id) REFERENCES exam_questions(question_id),
            UNIQUE(bank_id, question_id)
        )''')

        cursor.execute('''CREATE TABLE IF NOT EXISTS question_statistics (
            stat_id TEXT PRIMARY KEY,
            question_id TEXT NOT NULL,
            usage_count INTEGER DEFAULT 0,
            correct_rate REAL DEFAULT 0,
            difficulty_avg REAL DEFAULT 0,
            last_used_at TEXT,
            FOREIGN KEY (question_id) REFERENCES exam_questions(question_id)
        )''')

        conn.commit()
        conn.close()

        self._init_default_categories()

    def _init_default_categories(self):
        """初始化默认分类"""
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()

            categories = [
                ('数学', '数学学科题库', None, '数学'),
                ('数学-代数', '代数相关题目', '数学', '数学'),
                ('数学-几何', '几何相关题目', '数学', '数学'),
                ('数学-概率统计', '概率统计题目', '数学', '数学'),
                ('英语', '英语学科题库', None, '英语'),
                ('英语-语法', '语法题目', '英语', '英语'),
                ('英语-词汇', '词汇题目', '英语', '英语'),
                ('英语-听力', '听力题目', '英语', '英语'),
                ('语文', '语文学科题库', None, '语文'),
                ('语文-阅读理解', '阅读理解题目', '语文', '语文'),
                ('语文-写作', '写作题目', '语文', '语文'),
                ('语文-文言文', '文言文题目', '语文', '语文'),
                ('物理', '物理学科题库', None, '物理'),
                ('物理-力学', '力学题目', '物理', '物理'),
                ('物理-电学', '电学题目', '物理', '物理'),
                ('化学', '化学学科题库', None, '化学'),
                ('生物', '生物学科题库', None, '生物'),
                ('历史', '历史学科题库', None, '历史'),
                ('地理', '地理学科题库', None, '地理'),
                ('政治', '政治学科题库', None, '政治')
            ]

            for name, desc, parent_name, subject in categories:
                cursor.execute('SELECT category_id FROM question_categories WHERE name = ?', (name,))
                if not cursor.fetchone():
                    parent_id = None
                    if parent_name:
                        cursor.execute('SELECT category_id FROM question_categories WHERE name = ?', (parent_name,))
                        result = cursor.fetchone()
                        parent_id = result[0] if result else None

                    cursor.execute('''
                        INSERT INTO question_categories 
                        (category_id, name, parent_id, subject, description, created_at)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (str(uuid.uuid4())[:16], name, parent_id, subject, desc, datetime.now().isoformat()))

            conn.commit()

    def create_category(self, name: str, description: str, parent_id: str = None, subject: str = None) -> Dict:
        """创建分类"""
        category_id = str(uuid.uuid4())[:16]

        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()

            cursor.execute('''
                INSERT INTO question_categories 
                (category_id, name, parent_id, subject, description, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (category_id, name, parent_id, subject, description, datetime.now().isoformat()))

            conn.commit()

        return {'category_id': category_id, 'name': name}

    def get_categories(self, parent_id: str = None) -> List[Dict]:
        """获取分类列表"""
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()

            if parent_id:
                cursor.execute('''
                    SELECT * FROM question_categories WHERE parent_id = ? AND is_active = 1
                    ORDER BY order_num
                ''', (parent_id,))
            else:
                cursor.execute('''
                    SELECT * FROM question_categories WHERE parent_id IS NULL AND is_active = 1
                    ORDER BY order_num
                ''')

            columns = [description[0] for description in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def create_tag(self, name: str, color: str = '#1F2937', description: str = None) -> Dict:
        """创建标签"""
        tag_id = str(uuid.uuid4())[:16]

        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()

            try:
                cursor.execute('''
                    INSERT INTO question_tags (tag_id, name, color, description, created_at)
                    VALUES (?, ?, ?, ?, ?)
                ''', (tag_id, name, color, description, datetime.now().isoformat()))
                conn.commit()
                return {'tag_id': tag_id, 'name': name}
            except sqlite3.IntegrityError:
                return None

    def get_tags(self) -> List[Dict]:
        """获取所有标签"""
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()

            cursor.execute('SELECT * FROM question_tags ORDER BY name')
            columns = [description[0] for description in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def add_tag_to_question(self, question_id: str, tag_id: str) -> bool:
        """为题目添加标签"""
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()

            try:
                cursor.execute('''
                    INSERT INTO question_tag_mapping (question_id, tag_id)
                    VALUES (?, ?)
                ''', (question_id, tag_id))
                conn.commit()
                return True
            except sqlite3.IntegrityError:
                return False

    def remove_tag_from_question(self, question_id: str, tag_id: str) -> bool:
        """移除题目标签"""
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()

            cursor.execute('''
                DELETE FROM question_tag_mapping WHERE question_id = ? AND tag_id = ?
            ''', (question_id, tag_id))
            conn.commit()
            return cursor.rowcount > 0

    def get_question_tags(self, question_id: str) -> List[Dict]:
        """获取题目的标签"""
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()

            cursor.execute('''
                SELECT t.* FROM question_tags t
                JOIN question_tag_mapping m ON t.tag_id = m.tag_id
                WHERE m.question_id = ?
            ''', (question_id,))

            columns = [description[0] for description in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def create_bank(self, name: str, description: str, category_id: str = None,
                    is_public: int = 1, created_by: str = None) -> Dict:
        """创建题库"""
        bank_id = str(uuid.uuid4())[:16]

        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()

            cursor.execute('''
                INSERT INTO question_banks 
                (bank_id, name, description, category_id, is_public, created_by, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (bank_id, name, description, category_id, is_public, created_by, datetime.now().isoformat()))
            conn.commit()

        return {'bank_id': bank_id, 'name': name}

    def get_banks(self, category_id: str = None, created_by: str = None) -> List[Dict]:
        """获取题库列表"""
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()

            query = 'SELECT * FROM question_banks WHERE 1=1'
            params = []

            if category_id:
                query += ' AND category_id = ?'
                params.append(category_id)
            if created_by:
                query += ' AND created_by = ?'
                params.append(created_by)

            query += ' ORDER BY created_at DESC'

            cursor.execute(query, params)
            columns = [description[0] for description in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def add_question_to_bank(self, bank_id: str, question_id: str) -> bool:
        """将题目添加到题库"""
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()

            try:
                cursor.execute('''
                    INSERT INTO bank_question_mapping (bank_id, question_id)
                    VALUES (?, ?)
                ''', (bank_id, question_id))
                conn.commit()
                return True
            except sqlite3.IntegrityError:
                return False

    def remove_question_from_bank(self, bank_id: str, question_id: str) -> bool:
        """从题库移除题目"""
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()

            cursor.execute('''
                DELETE FROM bank_question_mapping WHERE bank_id = ? AND question_id = ?
            ''', (bank_id, question_id))
            conn.commit()
            return cursor.rowcount > 0

    def get_bank_questions(self, bank_id: str) -> List[Dict]:
        """获取题库中的题目"""
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()

            cursor.execute('''
                SELECT q.* FROM exam_questions q
                JOIN bank_question_mapping m ON q.question_id = m.question_id
                WHERE m.bank_id = ?
            ''', (bank_id,))

            columns = [description[0] for description in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def update_question_statistics(self, question_id: str, correct: bool = True):
        """更新题目统计信息"""
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()

            cursor.execute('SELECT usage_count, correct_rate FROM question_statistics WHERE question_id = ?',
                          (question_id,))
            row = cursor.fetchone()

            if row:
                usage_count = row[0] + 1
                correct_rate = (row[1] * row[0] + (1 if correct else 0)) / usage_count

                cursor.execute('''
                    UPDATE question_statistics 
                    SET usage_count = ?, correct_rate = ?, last_used_at = ?
                    WHERE question_id = ?
                ''', (usage_count, correct_rate, datetime.now().isoformat(), question_id))
            else:
                cursor.execute('''
                    INSERT INTO question_statistics 
                    (stat_id, question_id, usage_count, correct_rate, last_used_at)
                    VALUES (?, ?, ?, ?, ?)
                ''', (str(uuid.uuid4())[:16], question_id, 1, 1 if correct else 0, datetime.now().isoformat()))

            conn.commit()

    def get_question_statistics(self, question_id: str) -> Optional[Dict]:
        """获取题目统计信息"""
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()

            cursor.execute('SELECT * FROM question_statistics WHERE question_id = ?', (question_id,))
            row = cursor.fetchone()

            if row:
                columns = [description[0] for description in cursor.description]
                return dict(zip(columns, row))
            return None

    def search_questions(self, keyword: str = None, subject: str = None,
                         category_id: str = None, tags: List[str] = None,
                         difficulty_range: tuple = None, limit: int = 50) -> List[Dict]:
        """搜索题目"""
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()

            query = 'SELECT DISTINCT q.* FROM exam_questions q WHERE 1=1'
            params = []

            if keyword:
                query += ' AND (q.question_text LIKE ? OR q.explanation LIKE ?)'
                params.extend([f'%{keyword}%', f'%{keyword}%'])

            if subject:
                query += ' AND q.subject = ?'
                params.append(subject)

            if difficulty_range:
                query += ' AND q.difficulty BETWEEN ? AND ?'
                params.extend(difficulty_range)

            if tags:
                placeholders = ','.join(['?' for _ in tags])
                query += f''' AND q.question_id IN (
                    SELECT m.question_id FROM question_tag_mapping m
                    JOIN question_tags t ON m.tag_id = t.tag_id
                    WHERE t.name IN ({placeholders})
                )'''
                params.extend(tags)

            query += ' ORDER BY q.created_at DESC LIMIT ?'
            params.append(limit)

            cursor.execute(query, params)
            columns = [description[0] for description in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]


question_bank_service = QuestionBankService()
