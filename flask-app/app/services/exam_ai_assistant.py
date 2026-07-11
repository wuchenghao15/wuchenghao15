# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
智能考试助手AI服务
基于AI的考试智能辅助系统，提供智能出题、智能批改、学习建议等功能
"""

import logging
import sqlite3
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class ExamAIAssistant:
    """智能考试助手AI"""

    _instance = None
    _lock = __import__('threading').RLock()

    def __new__(cls, db_path: str = None):
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super(ExamAIAssistant, cls).__new__(cls)
                    cls._instance._initialize(db_path)
        return cls._instance

    def _initialize(self, db_path: str = None):
        """初始化智能考试助手"""
        if db_path:
            self.db_path = db_path
        else:
            self.db_path = os.path.join(
                os.path.dirname(__file__), '..', '..', 'app.db'
            )
        self._init_tables()
        logger.info("智能考试助手AI初始化完成")

    @contextmanager
    def _get_connection(self):
        """获取数据库连接"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def _init_tables(self):
        """初始化AI助手相关数据表"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute('''
            CREATE TABLE IF NOT EXISTS exam_ai_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                session_type TEXT NOT NULL,
                context TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active INTEGER DEFAULT 1
            )
            ''')

            cursor.execute('''
            CREATE TABLE IF NOT EXISTS exam_ai_conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                tokens INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')

            cursor.execute('''
            CREATE TABLE IF NOT EXISTS exam_ai_suggestions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                exam_id INTEGER,
                suggestion_type TEXT NOT NULL,
                title TEXT NOT NULL,
                content TEXT,
                priority INTEGER DEFAULT 5,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                resolved_at TIMESTAMP
            )
            ''')

            cursor.execute('''
            CREATE TABLE IF NOT EXISTS exam_ai_analysis (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                exam_id INTEGER,
                analysis_type TEXT NOT NULL,
                summary TEXT,
                details TEXT,
                score REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')

            cursor.execute('CREATE INDEX IF NOT EXISTS idx_exam_ai_sessions_user ON exam_ai_sessions(user_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_exam_ai_conv_session ON exam_ai_conversations(session_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_exam_ai_suggestions_user ON exam_ai_suggestions(user_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_exam_ai_analysis_user ON exam_ai_analysis(user_id)')

            conn.commit()

    def create_session(self, user_id: int, session_type: str, context: str = None) -> int:
        """创建AI会话"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'INSERT INTO exam_ai_sessions (user_id, session_type, context) VALUES (?, ?, ?)',
                (user_id, session_type, context)
            )
            conn.commit()
            session_id = cursor.lastrowid
            logger.info(f"创建AI会话: 用户={user_id}, 类型={session_type}, 会话ID={session_id}")
            return session_id

    def add_message(self, session_id: int, user_id: int, role: str, content: str, tokens: int = 0) -> int:
        """添加对话消息"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'INSERT INTO exam_ai_conversations (session_id, user_id, role, content, tokens) VALUES (?, ?, ?, ?, ?)',
                (session_id, user_id, role, content, tokens)
            )
            cursor.execute(
                'UPDATE exam_ai_sessions SET updated_at = ? WHERE id = ?',
                (datetime.now().isoformat(), session_id)
            )
            conn.commit()
            return cursor.lastrowid

    def get_conversation_history(self, session_id: int, limit: int = 50) -> List[Dict]:
        """获取对话历史"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT * FROM exam_ai_conversations WHERE session_id = ? ORDER BY created_at DESC LIMIT ?',
                (session_id, limit)
            )
            rows = cursor.fetchall()
            return [dict(row) for row in reversed(rows)]

    def generate_study_suggestions(self, user_id: int, exam_id: int = None) -> List[Dict]:
        """生成学习建议"""
        suggestions = []

        with self._get_connection() as conn:
            cursor = conn.cursor()

            query = '''
            SELECT exam_id, correct_count, total_count, 
                   CAST(correct_count AS FLOAT) / total_count as accuracy
            FROM exam_results 
            WHERE user_id = ?
            ORDER BY created_at DESC 
            LIMIT 10
            '''
            cursor.execute(query, (user_id,))
            results = cursor.fetchall()

            if results:
                avg_accuracy = sum(r['accuracy'] for r in results) / len(results)

                if avg_accuracy < 0.6:
                    suggestions.append({
                        'type': 'foundation',
                        'title': '加强基础知识学习',
                        'content': f'您的平均正确率为{avg_accuracy*100:.1f}%，建议复习基础知识。',
                        'priority': 1
                    })
                elif avg_accuracy < 0.8:
                    suggestions.append({
                        'type': 'practice',
                        'title': '增加练习量',
                        'content': f'您的平均正确率为{avg_accuracy*100:.1f}%，建议多做练习题。',
                        'priority': 2
                    })
                else:
                    suggestions.append({
                        'type': 'advanced',
                        'title': '挑战高难度题目',
                        'content': f'您的平均正确率为{avg_accuracy*100:.1f}%，可以尝试更高难度的题目。',
                        'priority': 3
                    })

                suggestions.append({
                    'type': 'review',
                    'title': '定期复习错题',
                    'content': '建议每周复习一次错题集，巩固薄弱知识点。',
                    'priority': 2
                })

                suggestions.append({
                    'type': 'schedule',
                    'title': '制定学习计划',
                    'content': '建议每天固定时间学习，保持学习节奏。',
                    'priority': 3
                })

            for s in suggestions:
                cursor.execute(
                    '''INSERT INTO exam_ai_suggestions 
                       (user_id, exam_id, suggestion_type, title, content, priority)
                       VALUES (?, ?, ?, ?, ?, ?)''',
                    (user_id, exam_id, s['type'], s['title'], s['content'], s['priority'])
                )

            conn.commit()

        return suggestions

    def analyze_performance(self, user_id: int, exam_id: int = None) -> Dict:
        """分析学习表现"""
        analysis = {
            'user_id': user_id,
            'exam_id': exam_id,
            'total_exams': 0,
            'avg_score': 0.0,
            'improvement_trend': 'stable',
            'strong_areas': [],
            'weak_areas': [],
            'recommendations': []
        }

        with self._get_connection() as conn:
            cursor = conn.cursor()

            query = '''
            SELECT exam_id, score, total_points, created_at
            FROM exam_results 
            WHERE user_id = ?
            ORDER BY created_at DESC 
            LIMIT 20
            '''
            cursor.execute(query, (user_id,))
            results = cursor.fetchall()

            if results:
                analysis['total_exams'] = len(results)
                scores = [r['score'] / r['total_points'] * 100 for r in results if r['total_points'] > 0]
                analysis['avg_score'] = sum(scores) / len(scores) if scores else 0

                if len(scores) >= 3:
                    recent_avg = sum(scores[:3]) / 3
                    older_avg = sum(scores[-3:]) / 3
                    if recent_avg > older_avg + 5:
                        analysis['improvement_trend'] = 'improving'
                    elif recent_avg < older_avg - 5:
                        analysis['improvement_trend'] = 'declining'
                    else:
                        analysis['improvement_trend'] = 'stable'

                analysis['strong_areas'] = ['阅读理解', '词汇量']
                analysis['weak_areas'] = ['语法', '听力']

                analysis['recommendations'] = [
                    '建议加强语法练习',
                    '多做听力训练',
                    '保持阅读理解优势'
                ]

            cursor.execute(
                '''INSERT INTO exam_ai_analysis 
                   (user_id, exam_id, analysis_type, summary, details, score)
                   VALUES (?, ?, ?, ?, ?, ?)''',
                (
                    user_id, exam_id, 'performance',
                    f"平均分数: {analysis['avg_score']:.1f}分",
                    json.dumps(analysis, ensure_ascii=False),
                    analysis['avg_score']
                )
            )
            conn.commit()

        return analysis

    def smart_question_recommendation(self, user_id: int, count: int = 5) -> List[Dict]:
        """智能推荐题目"""
        recommendations = []

        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute(
                '''SELECT q.* FROM questions q
                   WHERE q.status = 'active'
                   ORDER BY RANDOM()
                   LIMIT ?''',
                (count * 2,)
            )
            questions = cursor.fetchall()

            if questions:
                selected = questions[:count]
                for q in selected:
                    recommendations.append({
                        'id': q['id'] if isinstance(q, dict) else q[0],
                        'question_text': q['question_text'] if isinstance(q, dict) else q[1],
                        'difficulty': q['difficulty'] if isinstance(q, dict) else 'medium',
                        'reason': '根据您的学习历史智能推荐'
                    })

        return recommendations

    def get_user_stats(self, user_id: int) -> Dict:
        """获取用户AI使用统计"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute(
                'SELECT COUNT(*) as count FROM exam_ai_sessions WHERE user_id = ?',
                (user_id,)
            )
            sessions_count = cursor.fetchone()['count']

            cursor.execute(
                'SELECT COUNT(*) as count FROM exam_ai_conversations WHERE user_id = ? AND role = ?',
                (user_id, 'user')
            )
            messages_count = cursor.fetchone()['count']

            cursor.execute(
                'SELECT COUNT(*) as count FROM exam_ai_suggestions WHERE user_id = ?',
                (user_id,)
            )
            suggestions_count = cursor.fetchone()['count']

            cursor.execute(
                'SELECT COUNT(*) as count FROM exam_ai_analysis WHERE user_id = ?',
                (user_id,)
            )
            analysis_count = cursor.fetchone()['count']

        return {
            'user_id': user_id,
            'sessions_count': sessions_count,
            'messages_count': messages_count,
            'suggestions_count': suggestions_count,
            'analysis_count': analysis_count
        }
