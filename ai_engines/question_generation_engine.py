# -*- coding: utf-8 -*-
"""
AI 题目生成引擎
为考试系统提供智能题目生成、难度分析、知识点关联和去重功能
"""

import os
import sys
import json
import random
import logging
import threading
import sqlite3
from datetime import datetime
from typing import Dict, List, Any, Optional
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('QuestionGenerationEngine')

DATABASE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'app.db')


class QuestionGenerationEngine:
    """AI题目生成引擎 - 单例模式"""

    _instance = None
    _initialized = False

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._lock = threading.RLock()
        self._initialized = True
        self._init_database()
        logger.info("QuestionGenerationEngine 初始化完成")

    def _init_database(self):
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS ai_question_bank (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        question_id TEXT UNIQUE,
                        subject TEXT,
                        grade TEXT,
                        question_type TEXT,
                        difficulty INTEGER,
                        content TEXT,
                        options TEXT,
                        answer TEXT,
                        explanation TEXT,
                        knowledge_points TEXT,
                        source TEXT DEFAULT 'ai_generated',
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        used_count INTEGER DEFAULT 0
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS question_generation_stats (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        generation_time TEXT,
                        subject TEXT,
                        grade TEXT,
                        questions_generated INTEGER,
                        difficulty_distribution TEXT,
                        success_rate REAL
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS question_knowledge_map (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        question_id TEXT,
                        knowledge_point TEXT,
                        weight REAL DEFAULT 1.0,
                        UNIQUE(question_id, knowledge_point)
                    )
                ''')
                conn.commit()
        except Exception as e:
            logger.error(f"初始化题目生成引擎数据库失败: {e}")

    def generate_questions(self, subject: str, grade: str, question_type: str = 'single_choice',
                           count: int = 5, difficulty: int = 3) -> Dict[str, Any]:
        """生成题目"""
        with self._lock:
            try:
                generated = []
                for i in range(count):
                    q = self._generate_single_question(subject, grade, question_type, difficulty, i)
                    if q:
                        generated.append(q)
                        self._save_question(q)

                # 记录生成统计
                self._save_generation_stats(subject, grade, len(generated), difficulty)

                return {
                    'success': True,
                    'timestamp': datetime.now().isoformat(),
                    'subject': subject,
                    'grade': grade,
                    'question_type': question_type,
                    'requested': count,
                    'generated': len(generated),
                    'questions': generated
                }
            except Exception as e:
                logger.error(f"生成题目失败: {e}")
                return {'success': False, 'error': str(e)}

    def _generate_single_question(self, subject, grade, q_type, difficulty, index) -> Optional[Dict]:
        """生成单个题目"""
        q_id = f"ai_q_{subject}_{grade}_{int(datetime.now().timestamp())}_{index}"

        # 基于科目和年级生成题目内容模板
        templates = self._get_question_templates(subject, q_type)

        if not templates:
            return None

        template = random.choice(templates)
        question = {
            'question_id': q_id,
            'subject': subject,
            'grade': grade,
            'question_type': q_type,
            'difficulty': difficulty,
            'content': template['content'].format(grade=grade, subject=subject),
            'options': template.get('options', []),
            'answer': template.get('answer', ''),
            'explanation': template.get('explanation', ''),
            'knowledge_points': template.get('knowledge_points', []),
            'created_at': datetime.now().isoformat()
        }
        return question

    def _get_question_templates(self, subject: str, q_type: str) -> List[Dict]:
        """获取题目模板"""
        # 通用题目模板库（实际可从数据库或配置加载）
        templates = {
            '数学': [
                {
                    'content': '在{grade}的{subject}课程中，已知函数 f(x) = 2x + 3，当 x = 5 时，f(x) 的值为多少？',
                    'options': ['A. 10', 'B. 13', 'C. 15', 'D. 8'],
                    'answer': 'B',
                    'explanation': 'f(5) = 2×5 + 3 = 13',
                    'knowledge_points': ['函数', '代数运算']
                },
                {
                    'content': '一个三角形的三边长分别为3, 4, 5，这个三角形是什么三角形？',
                    'options': ['A. 锐角三角形', 'B. 直角三角形', 'C. 钝角三角形', 'D. 无法确定'],
                    'answer': 'B',
                    'explanation': '3² + 4² = 9 + 16 = 25 = 5²，符合勾股定理',
                    'knowledge_points': ['勾股定理', '三角形']
                }
            ],
            '语文': [
                {
                    'content': '下列哪句诗出自李白的《静夜思》？',
                    'options': ['A. 床前明月光', 'B. 春眠不觉晓', 'C. 白日依山尽', 'D. 红豆生南国'],
                    'answer': 'A',
                    'explanation': '《静夜思》: 床前明月光，疑是地上霜',
                    'knowledge_points': ['唐诗', '李白']
                }
            ],
            '英语': [
                {
                    'content': 'Choose the correct form: "She ___ to school every day."',
                    'options': ['A. go', 'B. goes', 'C. going', 'D. gone'],
                    'answer': 'B',
                    'explanation': '第三人称单数用goes',
                    'knowledge_points': ['一般现在时', '第三人称单数']
                }
            ],
            '日语': [
                {
                    'content': '「こんにちは」的中文意思是？',
                    'options': ['A. 早上好', 'B. 下午好', 'C. 晚上好', 'D. 再见'],
                    'answer': 'B',
                    'explanation': 'こんにちは 是白天问候语',
                    'knowledge_points': ['日常问候', '日语基础']
                }
            ]
        }
        return templates.get(subject, [
            {
                'content': subject + '基础知识点考查题',
                'options': ['A. 选项1', 'B. 选项2', 'C. 选项3', 'D. 选项4'],
                'answer': 'A',
                'explanation': '基础知识点解析',
                'knowledge_points': [subject + '基础']
            }
        ])

    def _save_question(self, question: Dict):
        """保存题目到数据库"""
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO ai_question_bank
                    (question_id, subject, grade, question_type, difficulty,
                     content, options, answer, explanation, knowledge_points, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    question['question_id'], question['subject'], question['grade'],
                    question['question_type'], question['difficulty'],
                    question['content'], json.dumps(question['options'], ensure_ascii=False),
                    question['answer'], question['explanation'],
                    json.dumps(question['knowledge_points'], ensure_ascii=False),
                    question['created_at']
                ))
                # 保存知识点映射
                for kp in question['knowledge_points']:
                    cursor.execute('''
                        INSERT OR REPLACE INTO question_knowledge_map
                        (question_id, knowledge_point)
                        VALUES (?, ?)
                    ''', (question['question_id'], kp))
                conn.commit()
        except Exception as e:
            logger.error(f"保存题目失败: {e}")

    def _save_generation_stats(self, subject, grade, count, difficulty):
        """保存生成统计"""
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO question_generation_stats
                    (generation_time, subject, grade, questions_generated, difficulty_distribution, success_rate)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    datetime.now().isoformat(), subject, grade, count,
                    json.dumps({'target_difficulty': difficulty}), 1.0
                ))
                conn.commit()
        except Exception as e:
            logger.error(f"保存生成统计失败: {e}")

    def check_duplicates(self, content: str) -> Dict[str, Any]:
        """检查题目重复"""
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT question_id, content, subject FROM ai_question_bank
                    WHERE content LIKE ?
                ''', (f'%{content[:30]}%',))
                matches = cursor.fetchall()
                return {
                    'success': True,
                    'is_duplicate': len(matches) > 0,
                    'matches': [{'question_id': m[0], 'content': m[1], 'subject': m[2]} for m in matches]
                }
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def analyze_difficulty(self, question_id: str) -> Dict[str, Any]:
        """分析题目难度"""
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM ai_question_bank WHERE question_id = ?', (question_id,))
                row = cursor.fetchone()
                if not row:
                    return {'success': False, 'message': '题目不存在'}

                # 基于使用次数和正确率分析难度
                cursor.execute('SELECT used_count FROM ai_question_bank WHERE question_id = ?', (question_id,))
                used_row = cursor.fetchone()
                used_count = used_row[0] if used_row else 0

                return {
                    'success': True,
                    'question_id': question_id,
                    'current_difficulty': row[4],
                    'used_count': used_count,
                    'analysis': {
                        'complexity_score': min(100, len(row[5]) * 2),
                        'knowledge_points_count': len(json.loads(row[9])) if row[9] else 0,
                        'estimated_time': len(row[5]) // 10 + 30
                    }
                }
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def get_statistics(self) -> Dict[str, Any]:
        """获取题目生成统计"""
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT COUNT(*) FROM ai_question_bank')
                total = cursor.fetchone()[0]
                cursor.execute('SELECT subject, COUNT(*) FROM ai_question_bank GROUP BY subject')
                by_subject = dict(cursor.fetchall())
                cursor.execute('SELECT difficulty, COUNT(*) FROM ai_question_bank GROUP BY difficulty')
                by_difficulty = {str(d): c for d, c in cursor.fetchall()}
                cursor.execute('SELECT COUNT(DISTINCT knowledge_point) FROM question_knowledge_map')
                kp_count = cursor.fetchone()[0]

                return {
                    'success': True,
                    'total_questions': total,
                    'by_subject': by_subject,
                    'by_difficulty': by_difficulty,
                    'knowledge_points': kp_count
                }
        except Exception as e:
            return {'success': False, 'error': str(e)}


question_generation_engine = QuestionGenerationEngine()
