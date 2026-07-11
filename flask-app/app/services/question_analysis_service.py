# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""考题分析讲解系统 - 智能分析和讲解题目"""

import os
import sqlite3
from contextlib import contextmanager
import uuid
import json
from datetime import datetime
from typing import List, Dict, Optional

app_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATABASE_PATH = os.path.join(app_root, 'app.db')


class QuestionAnalysisService:
    def __init__(self):
        self._init_tables()

    def _init_tables(self):
        """初始化数据库表"""
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()

        cursor.execute('''CREATE TABLE IF NOT EXISTS question_analysis (
            analysis_id TEXT PRIMARY KEY,
            question_id TEXT NOT NULL,
            difficulty_level INTEGER,
            knowledge_points TEXT,
            common_mistakes TEXT,
            analysis_text TEXT,
            solution_text TEXT,
            related_questions TEXT,
            difficulty_trend TEXT,
            created_at TEXT,
            FOREIGN KEY (question_id) REFERENCES exam_questions(question_id)
        )''')

        cursor.execute('''CREATE TABLE IF NOT EXISTS student_mistakes (
            mistake_id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            question_id TEXT NOT NULL,
            wrong_answer TEXT,
            correct_answer TEXT,
            mistake_type TEXT,
            analysis_note TEXT,
            reviewed INTEGER DEFAULT 0,
            created_at TEXT,
            FOREIGN KEY (question_id) REFERENCES exam_questions(question_id)
        )''')

        cursor.execute('''CREATE TABLE IF NOT EXISTS topic_explanations (
            explanation_id TEXT PRIMARY KEY,
            topic_name TEXT NOT NULL,
            subject TEXT,
            grade_level TEXT,
            explanation_text TEXT,
            examples TEXT,
            key_points TEXT,
            created_at TEXT,
            UNIQUE(topic_name, subject, grade_level)
        )''')

        cursor.execute('''CREATE TABLE IF NOT EXISTS learning_paths (
            path_id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            subject TEXT,
            current_topic TEXT,
            progress REAL DEFAULT 0,
            completed_topics TEXT,
            recommended_topics TEXT,
            created_at TEXT,
            updated_at TEXT
        )''')

        conn.commit()
        conn.close()

    def analyze_question(self, question_id: str) -> Dict:
        """分析题目"""
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()

            cursor.execute('''
                SELECT q.question_text, q.options, q.correct_answer, q.difficulty, q.explanation
                FROM exam_questions q
                WHERE q.question_id = ?
            ''', (question_id,))
            question = cursor.fetchone()

            if not question:
                return {}

            question_text, options, correct_answer, difficulty, explanation = question

            analysis = {
                'question_id': question_id,
                'question_text': question_text,
                'difficulty': difficulty,
                'analysis': self._generate_analysis(question_text, correct_answer, explanation),
                'knowledge_points': self._extract_knowledge_points(question_text),
                'common_mistakes': self._identify_common_mistakes(question_text, correct_answer),
                'solution_steps': self._generate_solution_steps(question_text, correct_answer)
            }

            self._save_analysis(question_id, analysis)

            return analysis

    def _generate_analysis(self, question_text: str, correct_answer: str, explanation: str) -> str:
        """生成题目分析"""
        return f"题目分析: {question_text[:100]}... 正确答案: {correct_answer}. {explanation}"

    def _extract_knowledge_points(self, question_text: str) -> List[str]:
        """提取知识点"""
        return ["知识点1", "知识点2", "知识点3"]

    def _identify_common_mistakes(self, question_text: str, correct_answer: str) -> List[Dict]:
        """识别常见错误"""
        return [
            {"mistake": "常见错误1", "reason": "原因分析1"},
            {"mistake": "常见错误2", "reason": "原因分析2"}
        ]

    def _generate_solution_steps(self, question_text: str, correct_answer: str) -> List[str]:
        """生成解题步骤"""
        return [
            "步骤1: 理解题目要求",
            "步骤2: 分析关键信息",
            "步骤3: 应用相关知识",
            "步骤4: 得出正确答案"
        ]

    def _save_analysis(self, question_id: str, analysis: Dict):
        """保存分析结果"""
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()

            analysis_id = str(uuid.uuid4())[:16]
            cursor.execute('''
                INSERT OR REPLACE INTO question_analysis 
                (analysis_id, question_id, difficulty_level, knowledge_points, common_mistakes, 
                 analysis_text, solution_text, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (analysis_id, question_id, analysis.get('difficulty', 0),
                  json.dumps(analysis.get('knowledge_points', [])),
                  json.dumps(analysis.get('common_mistakes', [])),
                  analysis.get('analysis', ''),
                  json.dumps(analysis.get('solution_steps', [])),
                  datetime.now().isoformat()))
            conn.commit()

    def record_student_mistake(self, user_id: str, question_id: str, wrong_answer: str,
                                correct_answer: str, mistake_type: str = None) -> bool:
        """记录学生错误"""
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()

            mistake_id = str(uuid.uuid4())[:16]
            cursor.execute('''
                INSERT INTO student_mistakes 
                (mistake_id, user_id, question_id, wrong_answer, correct_answer, 
                 mistake_type, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (mistake_id, user_id, question_id, wrong_answer, correct_answer,
                  mistake_type, datetime.now().isoformat()))
            conn.commit()
            return True

    def get_student_mistakes(self, user_id: str, limit: int = 50) -> List[Dict]:
        """获取学生错误记录"""
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()

            cursor.execute('''
                SELECT sm.*, q.question_text, q.subject, q.topic
                FROM student_mistakes sm
                LEFT JOIN exam_questions q ON sm.question_id = q.question_id
                WHERE sm.user_id = ?
                ORDER BY sm.created_at DESC
                LIMIT ?
            ''', (user_id, limit))

            columns = [description[0] for description in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def get_topic_explanation(self, topic_name: str, subject: str = None) -> Optional[Dict]:
        """获取主题讲解"""
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()

            if subject:
                cursor.execute('''
                    SELECT * FROM topic_explanations 
                    WHERE topic_name = ? AND subject = ?
                ''', (topic_name, subject))
            else:
                cursor.execute('''
                    SELECT * FROM topic_explanations WHERE topic_name = ?
                ''', (topic_name,))

            row = cursor.fetchone()
            if row:
                columns = [description[0] for description in cursor.description]
                return dict(zip(columns, row))
            return None

    def create_topic_explanation(self, topic_name: str, subject: str, grade_level: str,
                                  explanation_text: str, examples: List[str] = None,
                                  key_points: List[str] = None) -> bool:
        """创建主题讲解"""
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()

            explanation_id = str(uuid.uuid4())[:16]
            try:
                cursor.execute('''
                    INSERT INTO topic_explanations 
                    (explanation_id, topic_name, subject, grade_level, explanation_text, 
                     examples, key_points, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (explanation_id, topic_name, subject, grade_level, explanation_text,
                      json.dumps(examples or []), json.dumps(key_points or []),
                      datetime.now().isoformat()))
                conn.commit()
                return True
            except sqlite3.IntegrityError:
                return False

    def get_learning_path(self, user_id: str, subject: str) -> Optional[Dict]:
        """获取学习路径"""
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()

            cursor.execute('''
                SELECT * FROM learning_paths WHERE user_id = ? AND subject = ?
            ''', (user_id, subject))

            row = cursor.fetchone()
            if row:
                columns = [description[0] for description in cursor.description]
                return dict(zip(columns, row))
            return None

    def create_learning_path(self, user_id: str, subject: str, current_topic: str = None) -> str:
        """创建学习路径"""
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()

            path_id = str(uuid.uuid4())[:16]
            cursor.execute('''
                INSERT INTO learning_paths 
                (path_id, user_id, subject, current_topic, progress, completed_topics, 
                 recommended_topics, created_at, updated_at)
                VALUES (?, ?, ?, ?, 0, '[]', '[]', ?, ?)
            ''', (path_id, user_id, subject, current_topic,
                  datetime.now().isoformat(), datetime.now().isoformat()))
            conn.commit()
            return path_id

    def update_learning_progress(self, user_id: str, subject: str, topic: str,
                                  progress: float, completed: bool = False) -> bool:
        """更新学习进度"""
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()

            path = self.get_learning_path(user_id, subject)
            if not path:
                return False

            completed_topics = json.loads(path.get('completed_topics', '[]'))
            if completed and topic not in completed_topics:
                completed_topics.append(topic)

            cursor.execute('''
                UPDATE learning_paths 
                SET current_topic = ?, progress = ?, completed_topics = ?, updated_at = ?
                WHERE user_id = AND subject = ?
            ''', (topic, progress, json.dumps(completed_topics),
                  datetime.now().isoformat(), user_id, subject))
            conn.commit()
            return True

    def get_recommended_topics(self, user_id: str, subject: str) -> List[str]:
        """获取推荐学习主题"""
        mistakes = self.get_student_mistakes(user_id, limit=20)

        topic_mistakes = {}
        for mistake in mistakes:
            topic = mistake.get('topic')
            if topic:
                topic_mistakes[topic] = topic_mistakes.get(topic, 0) + 1

        sorted_topics = sorted(topic_mistakes.items(), key=lambda x: x[1], reverse=True)
        return [topic for topic, count in sorted_topics[:5]]

    def generate_practice_questions(self, user_id: str, subject: str, count: int = 10) -> List[Dict]:
        """生成练习题"""
        recommended_topics = self.get_recommended_topics(user_id, subject)

        if not recommended_topics:
            return []

        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()

            placeholders = ','.join(['?' for _ in recommended_topics])
            cursor.execute(f'''
                SELECT * FROM exam_questions 
                WHERE subject = ? AND topic IN ({placeholders})
                ORDER BY RANDOM()
                LIMIT ?
            ''', [subject] + recommended_topics + [count])

            columns = [description[0] for description in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]


question_analysis_service = QuestionAnalysisService()
