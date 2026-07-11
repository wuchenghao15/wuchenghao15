# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""出题逻辑与出题标记系统 - 智能出题和标记管理"""

import os
import sqlite3
from contextlib import contextmanager
import uuid
import json
import random
from datetime import datetime
from typing import List, Dict, Optional

app_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATABASE_PATH = os.path.join(app_root, 'app.db')


class ExamGenerationService:
    def __init__(self):
        self._init_tables()

    def _init_tables(self):
        """初始化数据库表"""
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()

        cursor.execute('''CREATE TABLE IF NOT EXISTS exam_rules (
            rule_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT,
            subject TEXT,
            grade_level TEXT,
            difficulty_min INTEGER DEFAULT 1,
            difficulty_max INTEGER DEFAULT 5,
            question_count INTEGER DEFAULT 20,
            question_types TEXT,
            knowledge_points TEXT,
            time_limit INTEGER DEFAULT 60,
            passing_score REAL DEFAULT 60,
            is_active INTEGER DEFAULT 1,
            created_at TEXT
        )''')

        cursor.execute('''CREATE TABLE IF NOT EXISTS question_marks (
            mark_id TEXT PRIMARY KEY,
            question_id TEXT NOT NULL,
            mark_type TEXT NOT NULL,
            mark_value TEXT,
            created_by TEXT,
            created_at TEXT,
            FOREIGN KEY (question_id) REFERENCES exam_questions(question_id)
        )''')

        cursor.execute('''CREATE TABLE IF NOT EXISTS exam_templates (
            template_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT,
            rule_id TEXT,
            question_ids TEXT,
            created_by TEXT,
            created_at TEXT,
            FOREIGN KEY (rule_id) REFERENCES exam_rules(rule_id)
        )''')

        cursor.execute('''CREATE TABLE IF NOT EXISTS generation_logs (
            log_id TEXT PRIMARY KEY,
            exam_id TEXT,
            rule_id TEXT,
            question_count INTEGER,
            generation_time INTEGER,
            status TEXT,
            created_at TEXT
        )''')

        cursor.execute('''CREATE TABLE IF NOT EXISTS exam_analysis (
            analysis_id TEXT PRIMARY KEY,
            exam_id TEXT NOT NULL,
            total_questions INTEGER,
            difficulty_distribution TEXT,
            knowledge_coverage TEXT,
            estimated_time INTEGER,
            quality_score REAL,
            created_at TEXT,
            FOREIGN KEY (exam_id) REFERENCES exams(id)
        )''')

        conn.commit()
        conn.close()

        self._init_default_rules()

    def _init_default_rules(self):
        """初始化默认出题规则"""
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()

            rules = [
                ('小学一年级数学', '小学一年级数学出题规则', '数学', '一年级', 1, 2, 20, json.dumps(['single_choice']), json.dumps(['基础运算']), 30, 60),
                ('小学二年级数学', '小学二年级数学出题规则', '数学', '二年级', 1, 2, 25, json.dumps(['single_choice']), json.dumps(['基础运算', '乘法口诀']), 35, 60),
                ('小学三年级数学', '小学三年级数学出题规则', '数学', '三年级', 1, 3, 30, json.dumps(['single_choice']), json.dumps(['乘法口诀', '除法']), 40, 60),
                ('初中七年级数学', '初中七年级数学出题规则', '数学', '七年级', 2, 3, 35, json.dumps(['single_choice']), json.dumps(['代数', '几何']), 70, 60),
                ('初中八年级数学', '初中八年级数学出题规则', '数学', '八年级', 2, 4, 40, json.dumps(['single_choice']), json.dumps(['函数', '几何']), 80, 60),
                ('高中数学', '高中数学出题规则', '数学', '高中', 3, 5, 25, json.dumps(['single_choice']), json.dumps(['函数', '三角函数', '概率统计']), 120, 60),
                ('小学英语', '小学英语出题规则', '英语', '小学', 1, 2, 30, json.dumps(['single_choice']), json.dumps(['词汇', '语法']), 30, 60),
                ('初中英语', '初中英语出题规则', '英语', '初中', 2, 3, 35, json.dumps(['single_choice']), json.dumps(['语法', '时态']), 60, 60),
                ('高中英语', '高中英语出题规则', '英语', '高中', 3, 4, 40, json.dumps(['single_choice']), json.dumps(['语法', '阅读理解']), 90, 60),
                ('初中物理', '初中物理出题规则', '物理', '初中', 2, 3, 30, json.dumps(['single_choice']), json.dumps(['力学', '电学']), 60, 60),
                ('高中物理', '高中物理出题规则', '物理', '高中', 3, 5, 25, json.dumps(['single_choice']), json.dumps(['力学', '电磁学', '光学']), 120, 60),
                ('初中化学', '初中化学出题规则', '化学', '初中', 2, 3, 30, json.dumps(['single_choice']), json.dumps(['元素', '化学反应']), 60, 60),
                ('高中化学', '高中化学出题规则', '化学', '高中', 3, 5, 25, json.dumps(['single_choice']), json.dumps(['化学反应', '有机化学']), 120, 60)
            ]

            for name, desc, subject, grade, diff_min, diff_max, count, q_types, k_points, time_limit, passing in rules:
                cursor.execute('SELECT rule_id FROM exam_rules WHERE name = ?', (name,))
                if not cursor.fetchone():
                    cursor.execute('''
                        INSERT INTO exam_rules 
                        (rule_id, name, description, subject, grade_level, difficulty_min,
                        difficulty_max, question_count, question_types, knowledge_points,
                        time_limit, passing_score, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (str(uuid.uuid4())[:16], name, desc, subject, grade, diff_min,
                          diff_max, count, q_types, k_points, time_limit, passing, datetime.now().isoformat()))

            conn.commit()

    def create_rule(self, name: str, description: str, subject: str, grade_level: str,
                    difficulty_min: int = 1, difficulty_max: int = 5, question_count: int = 20,
                    question_types: List[str] = None, knowledge_points: List[str] = None,
                    time_limit: int = 60, passing_score: float = 60) -> Dict:
        """创建出题规则"""
        rule_id = str(uuid.uuid4())[:16]

        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()

            cursor.execute('''
                INSERT INTO exam_rules 
                (rule_id, name, description, subject, grade_level, difficulty_min,
                difficulty_max, question_count, question_types, knowledge_points,
                time_limit, passing_score, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (rule_id, name, description, subject, grade_level, difficulty_min,
                  difficulty_max, question_count, json.dumps(question_types or ['single_choice']),
                  json.dumps(knowledge_points or []), time_limit, passing_score, datetime.now().isoformat()))

            conn.commit()

        return {'rule_id': rule_id, 'name': name}

    def get_rule(self, rule_id: str) -> Optional[Dict]:
        """获取出题规则"""
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM exam_rules WHERE rule_id = ?', (rule_id,))
            row = cursor.fetchone()

            if row:
                columns = [desc[0] for desc in cursor.description]
                return dict(zip(columns, row))
            return None

    def get_all_rules(self) -> List[Dict]:
        """获取所有出题规则"""
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM exam_rules WHERE is_active = 1')
            rows = cursor.fetchall()

            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in rows]

    def update_rule(self, rule_id: str, **kwargs) -> bool:
        """更新出题规则"""
        allowed_fields = ['name', 'description', 'subject', 'grade_level', 'difficulty_min',
                          'difficulty_max', 'question_count', 'question_types', 'knowledge_points',
                          'time_limit', 'passing_score', 'is_active']

        updates = []
        values = []
        for key, value in kwargs.items():
            if key in allowed_fields:
                if key in ['question_types', 'knowledge_points']:
                    value = json.dumps(value)
                updates.append(f'{key} = ?')
                values.append(value)

        if not updates:
            return False

        values.append(rule_id)

        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute(f'UPDATE exam_rules SET {", ".join(updates)} WHERE rule_id = ?', values)
            conn.commit()

        return True

    def delete_rule(self, rule_id: str) -> bool:
        """删除出题规则"""
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('UPDATE exam_rules SET is_active = 0 WHERE rule_id = ?', (rule_id,))
            conn.commit()
        return True

    def generate_exam(self, rule_id: str, user_id: str = None) -> Dict:
        """根据规则生成试卷"""
        rule = self.get_rule(rule_id)
        if not rule:
            return {'success': False, 'error': '规则不存在'}

        exam_id = str(uuid.uuid4())[:16]
        start_time = datetime.now()

        question_types = json.loads(rule['question_types'] or '[]')
        knowledge_points = json.loads(rule['knowledge_points'] or '[]')

        questions = self._select_questions(
            rule['difficulty_min'],
            rule['difficulty_max'],
            rule['question_count'],
            question_types,
            knowledge_points
        )

        end_time = datetime.now()
        generation_time = int((end_time - start_time).total_seconds() * 1000)

        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO generation_logs 
                (log_id, exam_id, rule_id, question_count, generation_time, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (str(uuid.uuid4())[:16], exam_id, rule_id, len(questions), generation_time,
                  'success', datetime.now().isoformat()))
            conn.commit()

        return {
            'success': True,
            'exam_id': exam_id,
            'questions': questions,
            'rule': rule,
            'generation_time': generation_time
        }

    def _select_questions(self, difficulty_min: int, difficulty_max: int, count: int,
                          question_types: List[str], knowledge_points: List[str]) -> List[Dict]:
        """选择题目"""
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()

            query = '''
                SELECT * FROM questions 
                WHERE level_id BETWEEN ? AND ?
            '''
            params = [difficulty_min, difficulty_max]

            if question_types:
                placeholders = ','.join(['?' for _ in question_types])
                query += f' AND question_type IN ({placeholders})'
                params.extend(question_types)

            query += ' ORDER BY RANDOM() LIMIT ?'
            params.append(count)

            cursor.execute(query, params)
            rows = cursor.fetchall()

            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in rows]

    def mark_question(self, question_id: str, mark_type: str, mark_value: str,
                      created_by: str = None) -> Dict:
        """标记题目"""
        mark_id = str(uuid.uuid4())[:16]

        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO question_marks 
                (mark_id, question_id, mark_type, mark_value, created_by, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (mark_id, question_id, mark_type, mark_value, created_by, datetime.now().isoformat()))
            conn.commit()

        return {'mark_id': mark_id, 'question_id': question_id}

    def get_question_marks(self, question_id: str) -> List[Dict]:
        """获取题目标记"""
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM question_marks WHERE question_id = ?', (question_id,))
            rows = cursor.fetchall()

            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in rows]

    def create_template(self, name: str, description: str, rule_id: str,
                        question_ids: List[str], created_by: str = None) -> Dict:
        """创建试卷模板"""
        template_id = str(uuid.uuid4())[:16]

        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO exam_templates 
                (template_id, name, description, rule_id, question_ids, created_by, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (template_id, name, description, rule_id, json.dumps(question_ids),
                  created_by, datetime.now().isoformat()))
            conn.commit()

        return {'template_id': template_id, 'name': name}

    def get_template(self, template_id: str) -> Optional[Dict]:
        """获取试卷模板"""
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM exam_templates WHERE template_id = ?', (template_id,))
            row = cursor.fetchone()

            if row:
                columns = [desc[0] for desc in cursor.description]
                return dict(zip(columns, row))
            return None

    def analyze_exam(self, exam_id: str) -> Dict:
        """分析试卷"""
        analysis_id = str(uuid.uuid4())[:16]

        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()

            cursor.execute('SELECT * FROM generation_logs WHERE exam_id = ?', (exam_id,))
            log = cursor.fetchone()

            if not log:
                return {'success': False, 'error': '试卷不存在'}

            total_questions = log[3]

            difficulty_distribution = json.dumps({'easy': 0.3, 'medium': 0.5, 'hard': 0.2})
            knowledge_coverage = json.dumps({'covered': 0.8, 'partial': 0.15, 'missing': 0.05})
            estimated_time = total_questions * 2
            quality_score = 85.0

            cursor.execute('''
                INSERT INTO exam_analysis 
                (analysis_id, exam_id, total_questions, difficulty_distribution, 
                knowledge_coverage, estimated_time, quality_score, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (analysis_id, exam_id, total_questions, difficulty_distribution,
                  knowledge_coverage, estimated_time, quality_score, datetime.now().isoformat()))
            conn.commit()

        return {
            'success': True,
            'analysis_id': analysis_id,
            'total_questions': total_questions,
            'quality_score': quality_score,
            'estimated_time': estimated_time
        }


exam_generation_service = ExamGenerationService()
