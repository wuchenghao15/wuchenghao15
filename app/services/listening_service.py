#!/usr/bin/env python3
"""
听力题服务
=============
提供听力题的生成、管理、训练和统计功能。
支持多种语言的听力练习，包含音频生成、播放控制和进度跟踪。
"""
import os
import sqlite3
import json
import random
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

DATABASE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'app.db')

logger = logging.getLogger('ListeningService')


class ListeningService:
    """听力题服务"""

    def __init__(self):
        self._init_db()
        logger.info("[ListeningService] 听力题服务初始化成功")

    def _init_db(self):
        """初始化数据库表"""
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS listening_questions (
                    id TEXT PRIMARY KEY,
                    subject TEXT NOT NULL,
                    level TEXT DEFAULT 'beginner',
                    dialogue TEXT NOT NULL,
                    question TEXT NOT NULL,
                    options TEXT NOT NULL,
                    correct_answer TEXT NOT NULL,
                    explanation TEXT,
                    audio_url TEXT,
                    language TEXT DEFAULT 'english',
                    voice_type TEXT DEFAULT 'standard',
                    duration REAL DEFAULT 0,
                    difficulty INTEGER DEFAULT 1,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS listening_progress (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    question_id TEXT NOT NULL,
                    answered_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    user_answer TEXT,
                    is_correct INTEGER DEFAULT 0,
                    listen_count INTEGER DEFAULT 1,
                    time_spent REAL DEFAULT 0,
                    accuracy REAL DEFAULT 0,
                    FOREIGN KEY (question_id) REFERENCES listening_questions(id)
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS listening_stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    subject TEXT NOT NULL,
                    total_questions INTEGER DEFAULT 0,
                    correct_count INTEGER DEFAULT 0,
                    wrong_count INTEGER DEFAULT 0,
                    total_listen_count INTEGER DEFAULT 0,
                    avg_time_spent REAL DEFAULT 0,
                    accuracy REAL DEFAULT 0,
                    last_practice_at TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_id, subject)
                )
            ''')
            
            conn.commit()

    def add_listening_question(self, data: Dict[str, Any]) -> bool:
        """添加听力题目"""
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()
                
                question_id = f"listen_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{random.randint(1000, 9999)}"
                
                cursor.execute('''
                    INSERT INTO listening_questions (
                        id, subject, level, dialogue, question, options, 
                        correct_answer, explanation, audio_url, language, 
                        voice_type, duration, difficulty
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    question_id,
                    data.get('subject', 'english'),
                    data.get('level', 'beginner'),
                    data.get('dialogue', ''),
                    data.get('question', ''),
                    json.dumps(data.get('options', [])),
                    data.get('correct_answer', ''),
                    data.get('explanation', ''),
                    data.get('audio_url', ''),
                    data.get('language', 'english'),
                    data.get('voice_type', 'standard'),
                    data.get('duration', 0),
                    data.get('difficulty', 1)
                ))
                
                conn.commit()
                logger.info(f"添加听力题目: {question_id}")
                return True
        except Exception as e:
            logger.error(f"添加听力题目失败: {e}")
            return False

    def get_listening_question(self, question_id: str) -> Optional[Dict[str, Any]]:
        """获取单个听力题目"""
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute('SELECT * FROM listening_questions WHERE id = ?', (question_id,))
                row = cursor.fetchone()
                
                if row:
                    result = dict(row)
                    result['options'] = json.loads(result['options'])
                    return result
                return None
        except Exception as e:
            logger.error(f"获取听力题目失败: {e}")
            return None

    def get_listening_questions(self, subject: str = '', level: str = '', 
                                limit: int = 10, randomize: bool = True) -> List[Dict[str, Any]]:
        """获取听力题目列表"""
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                query = 'SELECT * FROM listening_questions WHERE 1=1'
                params = []
                
                if subject:
                    query += ' AND subject = ?'
                    params.append(subject)
                
                if level:
                    query += ' AND level = ?'
                    params.append(level)
                
                if randomize:
                    query += ' ORDER BY RANDOM()'
                else:
                    query += ' ORDER BY difficulty ASC'
                
                query += ' LIMIT ?'
                params.append(limit)
                
                cursor.execute(query, params)
                rows = cursor.fetchall()
                
                results = []
                for row in rows:
                    result = dict(row)
                    result['options'] = json.loads(result['options'])
                    results.append(result)
                
                return results
        except Exception as e:
            logger.error(f"获取听力题目列表失败: {e}")
            return []

    def get_random_question(self, subject: str = '', user_id: str = '') -> Optional[Dict[str, Any]]:
        """获取随机听力题目（优先推荐未做过或错误率高的题目）"""
        try:
            questions = self.get_listening_questions(subject=subject, limit=50)
            
            if not questions:
                return None
            
            if user_id:
                wrong_questions = self.get_user_wrong_questions(user_id, subject=subject)
                if wrong_questions:
                    return random.choice(wrong_questions)
            
            return random.choice(questions)
        except Exception as e:
            logger.error(f"获取随机听力题目失败: {e}")
            return None

    def get_user_wrong_questions(self, user_id: str, subject: str = '', limit: int = 10) -> List[Dict[str, Any]]:
        """获取用户错误的听力题目"""
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                query = '''
                    SELECT q.* FROM listening_questions q
                    JOIN listening_progress p ON q.id = p.question_id
                    WHERE p.user_id = ? AND p.is_correct = 0
                '''
                params = [user_id]
                
                if subject:
                    query += ' AND q.subject = ?'
                    params.append(subject)
                
                query += ' GROUP BY q.id ORDER BY COUNT(p.id) DESC LIMIT ?'
                params.append(limit)
                
                cursor.execute(query, params)
                rows = cursor.fetchall()
                
                results = []
                for row in rows:
                    result = dict(row)
                    result['options'] = json.loads(result['options'])
                    results.append(result)
                
                return results
        except Exception as e:
            logger.error(f"获取用户错误听力题目失败: {e}")
            return []

    def record_progress(self, user_id: str, question_id: str, user_answer: str, 
                        is_correct: bool, listen_count: int = 1, time_spent: float = 0) -> bool:
        """记录听力练习进度"""
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO listening_progress 
                    (user_id, question_id, user_answer, is_correct, listen_count, time_spent)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (user_id, question_id, user_answer, 1 if is_correct else 0, listen_count, time_spent))
                
                self._update_user_stats(user_id, question_id, is_correct, listen_count, time_spent)
                
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"记录听力练习进度失败: {e}")
            return False

    def _update_user_stats(self, user_id: str, question_id: str, is_correct: bool, 
                           listen_count: int, time_spent: float):
        """更新用户统计数据"""
        try:
            question = self.get_listening_question(question_id)
            if not question:
                return
            
            subject = question['subject']
            
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT * FROM listening_stats WHERE user_id = ? AND subject = ?
                ''', (user_id, subject))
                row = cursor.fetchone()
                
                if row:
                    total = row['total_questions'] + 1
                    correct = row['correct_count'] + (1 if is_correct else 0)
                    wrong = row['wrong_count'] + (0 if is_correct else 1)
                    listens = row['total_listen_count'] + listen_count
                    avg_time = (row['avg_time_spent'] * row['total_questions'] + time_spent) / total
                    accuracy = correct / total * 100 if total > 0 else 0
                    
                    cursor.execute('''
                        UPDATE listening_stats 
                        SET total_questions = ?, correct_count = ?, wrong_count = ?,
                            total_listen_count = ?, avg_time_spent = ?, accuracy = ?,
                            last_practice_at = ?, updated_at = ?
                        WHERE user_id = ? AND subject = ?
                    ''', (total, correct, wrong, listens, avg_time, accuracy, 
                          datetime.now().isoformat(), datetime.now().isoformat(), user_id, subject))
                else:
                    cursor.execute('''
                        INSERT INTO listening_stats 
                        (user_id, subject, total_questions, correct_count, wrong_count,
                         total_listen_count, avg_time_spent, accuracy, last_practice_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (user_id, subject, 1, 1 if is_correct else 0, 0 if is_correct else 1,
                          listen_count, time_spent, 100 if is_correct else 0, datetime.now().isoformat()))
                
                conn.commit()
        except Exception as e:
            logger.error(f"更新用户统计数据失败: {e}")

    def get_user_stats(self, user_id: str, subject: str = '') -> Dict[str, Any]:
        """获取用户听力统计数据"""
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                if subject:
                    cursor.execute('''
                        SELECT * FROM listening_stats WHERE user_id = ? AND subject = ?
                    ''', (user_id, subject))
                    row = cursor.fetchone()
                    if row:
                        return dict(row)
                    return {'user_id': user_id, 'subject': subject, 'total_questions': 0, 
                            'correct_count': 0, 'wrong_count': 0, 'accuracy': 0}
                else:
                    cursor.execute('''
                        SELECT * FROM listening_stats WHERE user_id = ?
                    ''', (user_id,))
                    rows = cursor.fetchall()
                    return {'total': len(rows), 'subjects': [dict(row) for row in rows]}
        except Exception as e:
            logger.error(f"获取用户听力统计数据失败: {e}")
            return {}

    def generate_practice_session(self, user_id: str, subject: str = '', 
                                  question_count: int = 5, mode: str = 'random') -> List[Dict[str, Any]]:
        """生成听力练习会话"""
        try:
            questions = []
            
            if mode == 'review':
                wrong_questions = self.get_user_wrong_questions(user_id, subject=subject, limit=question_count)
                questions.extend(wrong_questions)
            
            remaining = question_count - len(questions)
            if remaining > 0:
                new_questions = self.get_listening_questions(subject=subject, limit=remaining)
                questions.extend(new_questions)
            
            for q in questions:
                q['audio_url'] = self._generate_audio_url(q)
            
            logger.info(f"生成听力练习会话: {len(questions)}题")
            return questions
        except Exception as e:
            logger.error(f"生成听力练习会话失败: {e}")
            return []

    def _generate_audio_url(self, question: Dict[str, Any]) -> str:
        """生成音频URL"""
        try:
            if question.get('audio_url'):
                return question['audio_url']
            
            dialogue = question.get('dialogue', '')
            language = question.get('language', 'english')
            
            if dialogue:
                from ai_engines.audio_manager import audio_manager
                audio_result = audio_manager.text_to_speech(
                    text=dialogue,
                    language=language,
                    voice_type=question.get('voice_type', 'standard'),
                    speed=question.get('speed', 1.0)
                )
                if audio_result.get('success'):
                    return audio_result['audio_url']
            
            return ''
        except Exception as e:
            logger.error(f"生成音频URL失败: {e}")
            return ''

    def get_difficulty_levels(self) -> List[str]:
        """获取难度级别列表"""
        return ['beginner', 'intermediate', 'advanced', 'expert']

    def get_supported_subjects(self) -> List[str]:
        """获取支持的科目列表"""
        return ['english', 'japanese', 'chinese', 'korean', 'french', 'german', 'spanish']


listening_service = ListeningService()