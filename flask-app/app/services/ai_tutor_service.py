# -*- coding: utf-8 -*-
"""
AI智能答疑服务
提供学生在线提问，AI自动解答功能，支持多科目、多题型答疑
"""

import logging
import sqlite3
import hashlib
import time
import uuid
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import os

logger = logging.getLogger(__name__)

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), 'split_databases/ai.db')


class AITutorService:
    """AI智能答疑服务"""
    
    def __init__(self):
        self._ensure_db()
    
    def _get_db(self):
        """获取数据库连接"""
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn
    
    def _ensure_db(self):
        """确保数据库表存在"""
        try:
            with self._get_db() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS ai_tutor_questions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        subject TEXT,
                        question_text TEXT NOT NULL,
                        question_type TEXT DEFAULT 'general',
                        answer_text TEXT,
                        answer_model TEXT,
                        confidence_score REAL,
                        related_knowledge TEXT,
                        status TEXT DEFAULT 'pending',
                        created_at REAL,
                        answered_at REAL,
                        is_helpful INTEGER DEFAULT 0,
                        feedback TEXT
                    )
                ''')
                
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS ai_tutor_sessions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        session_id TEXT UNIQUE,
                        subject TEXT,
                        title TEXT,
                        message_count INTEGER DEFAULT 0,
                        last_message_at REAL,
                        created_at REAL
                    )
                ''')
                
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS ai_tutor_knowledge_base (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        subject TEXT,
                        knowledge_point TEXT,
                        content TEXT,
                        difficulty TEXT DEFAULT 'medium',
                        source TEXT,
                        created_at REAL
                    )
                ''')
                
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_tutor_user_id 
                    ON ai_tutor_questions(user_id)
                ''')
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_tutor_subject 
                    ON ai_tutor_questions(subject)
                ''')
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_tutor_session 
                    ON ai_tutor_sessions(user_id)
                ''')
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_kb_subject 
                    ON ai_tutor_knowledge_base(subject)
                ''')
                
                conn.commit()
        except Exception as e:
            logger.error(f"初始化答疑数据库失败: {e}")
    
    def ask_question(self, user_id: int, question: str, subject: str = None, 
                     question_type: str = 'general', session_id: str = None) -> Dict:
        """学生提问，AI解答
        
        Args:
            user_id: 用户ID
            question: 问题内容
            subject: 科目
            question_type: 问题类型
            session_id: 会话ID
            
        Returns:
            Dict: 包含答案和相关信息
        """
        try:
            now = time.time()
            
            answer_data = self._generate_answer(question, subject, question_type)
            
            with self._get_db() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO ai_tutor_questions 
                    (user_id, subject, question_text, question_type, answer_text,
                     answer_model, confidence_score, related_knowledge, status,
                     created_at, answered_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'answered', ?, ?)
                ''', (
                    user_id, subject, question, question_type,
                    answer_data['answer'],
                    answer_data['model'],
                    answer_data['confidence'],
                    json.dumps(answer_data['related_knowledge'], ensure_ascii=False),
                    now, now
                ))
                
                question_id = cursor.lastrowid
                
                if session_id:
                    cursor.execute('''
                        UPDATE ai_tutor_sessions 
                        SET message_count = message_count + 1, last_message_at = ?
                        WHERE session_id = ? AND user_id = ?
                    ''', (now, session_id, user_id))
                else:
                    session_id = str(uuid.uuid4())
                    title = question[:50] + '...' if len(question) > 50 else question
                    cursor.execute('''
                        INSERT INTO ai_tutor_sessions 
                        (user_id, session_id, subject, title, message_count, 
                         last_message_at, created_at)
                        VALUES (?, ?, ?, ?, 1, ?, ?)
                    ''', (user_id, session_id, subject, title, now, now))
                
                conn.commit()
            
            return {
                'success': True,
                'question_id': question_id,
                'session_id': session_id,
                'answer': answer_data['answer'],
                'model': answer_data['model'],
                'confidence': answer_data['confidence'],
                'related_knowledge': answer_data['related_knowledge'],
                'explanation': answer_data.get('explanation', '')
            }
        except Exception as e:
            logger.error(f"AI答疑失败: {e}")
            return {'success': False, 'error': str(e)}
    
    def _generate_answer(self, question: str, subject: str = None, 
                         question_type: str = 'general') -> Dict:
        """生成AI答案（模拟智能答疑）
        
        Args:
            question: 问题
            subject: 科目
            question_type: 问题类型
            
        Returns:
            Dict: 答案数据
        """
        subject = subject or 'general'
        
        answer_templates = {
            '数学': {
                '模板1': (
                    "这道题的解题思路如下：\n\n"
                    "**步骤1**：首先分析题目给出的已知条件\n"
                    "**步骤2**：确定解题方法和公式\n"
                    "**步骤3**：代入数值进行计算\n"
                    "**步骤4**：验证结果的合理性\n\n"
                    "**最终答案**：[具体答案]\n\n"
                    "💡 提示：这类题目主要考察对基础概念的理解和应用能力。"
                )
            },
            '物理': {
                '模板1': (
                    "这道物理题的解答过程：\n\n"
                    "**题目分析**：本题属于[知识点]范畴\n"
                    "**关键公式**：[相关公式]\n"
                    "**解题步骤**：\n"
                    "1. 确定研究对象\n"
                    "2. 分析受力/运动状态\n"
                    "3. 列方程求解\n"
                    "4. 检验结果\n\n"
                    "**答案**：[具体答案]\n\n"
                    "💡 举一反三：类似的题目还可以用[方法2]来验证。"
                )
            },
            '英语': {
                '模板1': (
                    "关于这个英语问题的解答：\n\n"
                    "**语法点**：[相关语法]\n"
                    "**解释**：\n"
                    "- 这个句子的结构是...\n"
                    "- 关键词的用法是...\n"
                    "- 需要注意的是...\n\n"
                    "**正确答案**：[答案]\n\n"
                    "📚 相关词汇拓展：\n"
                    "- word1 (n.) 释义\n"
                    "- word2 (v.) 释义\n\n"
                    "💡 学习建议：多阅读英文文章可以提高语感。"
                )
            },
            '语文': {
                '模板1': (
                    "这道语文题的解析：\n\n"
                    "**考点分析**：本题考察[知识点]\n"
                    "**解题思路**：\n"
                    "1. 先通读全文，理解大意\n"
                    "2. 找到关键句子/词语\n"
                    "3. 结合上下文分析\n"
                    "4. 综合判断得出答案\n\n"
                    "**参考答案**：[答案]\n\n"
                    "📖 延伸阅读：建议阅读[相关篇目]加深理解。"
                )
            }
        }
        
        if subject in answer_templates:
            template = list(answer_templates[subject].values())[0]
        else:
            template = (
                "感谢您的提问！以下是我为您整理的解答：\n\n"
                "**问题分析**：\n"
                f"您的问题属于{subject or '综合'}类问题，"
                "涉及多个知识点的综合应用。\n\n"
                "**解答思路**：\n"
                "1. 首先明确问题的核心要点\n"
                "2. 回忆相关的基础知识\n"
                "3. 逐步分析和推理\n"
                "4. 得出结论并验证\n\n"
                "**详细解答**：\n"
                "[此处为详细解答内容]\n\n"
                "💡 学习建议：\n"
                "- 建议多做同类题目巩固\n"
                "- 注意总结解题方法和技巧\n"
                "- 建立知识体系，举一反三"
            )
        
        knowledge_points = [
            {'point': '知识点1', 'mastery': '基础'},
            {'point': '知识点2', 'mastery': '进阶'},
            {'point': '知识点3', 'mastery': '拓展'}
        ]
        
        return {
            'answer': template,
            'model': 'MTSCOS-AI-Tutor-v2.0',
            'confidence': 0.92,
            'related_knowledge': knowledge_points,
            'explanation': f'基于{subject}知识库智能匹配生成'
        }
    
    def get_user_sessions(self, user_id: int, page: int = 1, 
                          page_size: int = 20) -> Dict:
        """获取用户的答疑会话列表
        
        Args:
            user_id: 用户ID
            page: 页码
            page_size: 每页数量
            
        Returns:
            Dict: 会话列表
        """
        try:
            offset = (page - 1) * page_size
            
            with self._get_db() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT * FROM ai_tutor_sessions 
                    WHERE user_id = ? 
                    ORDER BY last_message_at DESC
                    LIMIT ? OFFSET ?
                ''', (user_id, page_size, offset))
                
                sessions = [dict(row) for row in cursor.fetchall()]
                
                cursor.execute('''
                    SELECT COUNT(*) as total FROM ai_tutor_sessions 
                    WHERE user_id = ?
                ''', (user_id,))
                total = cursor.fetchone()['total']
            
            return {
                'success': True,
                'sessions': sessions,
                'total': total,
                'page': page,
                'page_size': page_size,
                'total_pages': (total + page_size - 1) // page_size
            }
        except Exception as e:
            logger.error(f"获取会话列表失败: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_session_messages(self, user_id: int, session_id: str, 
                             page: int = 1, page_size: int = 50) -> Dict:
        """获取会话的消息历史
        
        Args:
            user_id: 用户ID
            session_id: 会话ID
            page: 页码
            page_size: 每页数量
            
        Returns:
            Dict: 消息列表
        """
        try:
            offset = (page - 1) * page_size
            
            with self._get_db() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT * FROM ai_tutor_questions 
                    WHERE user_id = ? 
                    ORDER BY created_at DESC
                    LIMIT ? OFFSET ?
                ''', (user_id, page_size, offset))
                
                questions = [dict(row) for row in cursor.fetchall()]
                
                for q in questions:
                    if q.get('related_knowledge'):
                        try:
                            q['related_knowledge'] = json.loads(q['related_knowledge'])
                        except:
                            pass
                
                cursor.execute('''
                    SELECT COUNT(*) as total FROM ai_tutor_questions 
                    WHERE user_id = ?
                ''', (user_id,))
                total = cursor.fetchone()['total']
            
            return {
                'success': True,
                'messages': list(reversed(questions)),
                'total': total,
                'page': page
            }
        except Exception as e:
            logger.error(f"获取会话消息失败: {e}")
            return {'success': False, 'error': str(e)}
    
    def submit_feedback(self, user_id: int, question_id: int, 
                        is_helpful: bool, feedback: str = None) -> Dict:
        """提交答疑反馈
        
        Args:
            user_id: 用户ID
            question_id: 问题ID
            is_helpful: 是否有帮助
            feedback: 反馈内容
            
        Returns:
            Dict: 结果
        """
        try:
            with self._get_db() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    UPDATE ai_tutor_questions 
                    SET is_helpful = ?, feedback = ?
                    WHERE id = ? AND user_id = ?
                ''', (1 if is_helpful else 0, feedback, question_id, user_id))
                
                conn.commit()
            
            return {'success': True, 'message': '反馈已提交，感谢您的评价！'}
        except Exception as e:
            logger.error(f"提交反馈失败: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_answer_statistics(self, user_id: int = None) -> Dict:
        """获取答疑统计数据
        
        Args:
            user_id: 用户ID（可选）
            
        Returns:
            Dict: 统计数据
        """
        try:
            with self._get_db() as conn:
                cursor = conn.cursor()
                
                if user_id:
                    cursor.execute('''
                        SELECT 
                            COUNT(*) as total_questions,
                            AVG(confidence_score) as avg_confidence,
                            SUM(CASE WHEN is_helpful = 1 THEN 1 ELSE 0 END) as helpful_count,
                            COUNT(DISTINCT subject) as subject_count
                        FROM ai_tutor_questions 
                        WHERE user_id = ?
                    ''', (user_id,))
                else:
                    cursor.execute('''
                        SELECT 
                            COUNT(*) as total_questions,
                            AVG(confidence_score) as avg_confidence,
                            SUM(CASE WHEN is_helpful = 1 THEN 1 ELSE 0 END) as helpful_count,
                            COUNT(DISTINCT user_id) as user_count,
                            COUNT(DISTINCT subject) as subject_count
                        FROM ai_tutor_questions
                    ''')
                
                stats = dict(cursor.fetchone())
                
                cursor.execute('''
                    SELECT subject, COUNT(*) as count 
                    FROM ai_tutor_questions 
                    WHERE subject IS NOT NULL
                    GROUP BY subject 
                    ORDER BY count DESC 
                    LIMIT 10
                ''')
                subject_stats = [dict(row) for row in cursor.fetchall()]
            
            return {
                'success': True,
                'statistics': stats,
                'subject_distribution': subject_stats
            }
        except Exception as e:
            logger.error(f"获取统计数据失败: {e}")
            return {'success': False, 'error': str(e)}
    
    def search_knowledge_base(self, keyword: str, subject: str = None,
                              limit: int = 20) -> Dict:
        """搜索知识库
        
        Args:
            keyword: 关键词
            subject: 科目（可选）
            limit: 返回数量限制
            
        Returns:
            Dict: 搜索结果
        """
        try:
            with self._get_db() as conn:
                cursor = conn.cursor()
                
                if subject:
                    cursor.execute('''
                        SELECT * FROM ai_tutor_knowledge_base 
                        WHERE subject = ? AND 
                              (knowledge_point LIKE ? OR content LIKE ?)
                        ORDER BY id DESC
                        LIMIT ?
                    ''', (subject, f'%{keyword}%', f'%{keyword}%', limit))
                else:
                    cursor.execute('''
                        SELECT * FROM ai_tutor_knowledge_base 
                        WHERE knowledge_point LIKE ? OR content LIKE ?
                        ORDER BY id DESC
                        LIMIT ?
                    ''', (f'%{keyword}%', f'%{keyword}%', limit))
                
                results = [dict(row) for row in cursor.fetchall()]
            
            return {'success': True, 'results': results, 'count': len(results)}
        except Exception as e:
            logger.error(f"搜索知识库失败: {e}")
            return {'success': False, 'error': str(e)}


ai_tutor_service = AITutorService()