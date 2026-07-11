# -*- coding: utf-8 -*-
"""
智能错题本服务
自动收集错题，智能推荐复习，分析薄弱知识点
"""

import logging
import sqlite3
import json
import time
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import os

logger = logging.getLogger(__name__)

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), 'split_databases/learning.db')


class WrongBookService:
    """智能错题本服务"""
    
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
                    CREATE TABLE IF NOT EXISTS wrong_questions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        question_id INTEGER,
                        question_text TEXT NOT NULL,
                        question_type TEXT DEFAULT 'single',
                        subject TEXT,
                        knowledge_point TEXT,
                        user_answer TEXT,
                        correct_answer TEXT,
                        difficulty TEXT DEFAULT 'medium',
                        wrong_count INTEGER DEFAULT 1,
                        mastery_level INTEGER DEFAULT 0,
                        last_wrong_time REAL,
                        last_review_time REAL,
                        next_review_time REAL,
                        review_count INTEGER DEFAULT 0,
                        created_at REAL,
                        tags TEXT,
                        note TEXT,
                        is_starred INTEGER DEFAULT 0
                    )
                ''')
                
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS wrong_review_records (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        wrong_question_id INTEGER NOT NULL,
                        result TEXT,
                        time_spent INTEGER,
                        reviewed_at REAL
                    )
                ''')
                
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS weak_points (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        subject TEXT,
                        knowledge_point TEXT NOT NULL,
                        wrong_count INTEGER DEFAULT 0,
                        total_count INTEGER DEFAULT 0,
                        error_rate REAL DEFAULT 0,
                        mastery_level INTEGER DEFAULT 0,
                        last_updated REAL
                    )
                ''')
                
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_wq_user_id 
                    ON wrong_questions(user_id)
                ''')
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_wq_subject 
                    ON wrong_questions(subject)
                ''')
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_wq_knowledge 
                    ON wrong_questions(knowledge_point)
                ''')
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_wp_user 
                    ON weak_points(user_id)
                ''')
                
                conn.commit()
        except Exception as e:
            logger.error(f"初始化错题本数据库失败: {e}")
    
    def add_wrong_question(self, user_id: int, question_id: int = None,
                           question_text: str = '', question_type: str = 'single',
                           subject: str = None, knowledge_point: str = None,
                           user_answer: str = '', correct_answer: str = '',
                           difficulty: str = 'medium') -> Dict:
        """添加错题
        
        Args:
            user_id: 用户ID
            question_id: 题目ID
            question_text: 题目内容
            question_type: 题目类型
            subject: 科目
            knowledge_point: 知识点
            user_answer: 用户答案
            correct_answer: 正确答案
            difficulty: 难度
            
        Returns:
            Dict: 结果
        """
        try:
            now = time.time()
            
            with self._get_db() as conn:
                cursor = conn.cursor()
                
                if question_id:
                    cursor.execute('''
                        SELECT id, wrong_count FROM wrong_questions 
                        WHERE user_id = ? AND question_id = ?
                    ''', (user_id, question_id))
                    existing = cursor.fetchone()
                else:
                    existing = None
                
                if existing:
                    cursor.execute('''
                        UPDATE wrong_questions 
                        SET wrong_count = wrong_count + 1,
                            last_wrong_time = ?,
                            user_answer = ?,
                            mastery_level = MAX(0, mastery_level - 1)
                        WHERE id = ?
                    ''', (now, user_answer, existing['id']))
                    wrong_id = existing['id']
                    is_new = False
                else:
                    next_review = now + 24 * 3600
                    
                    cursor.execute('''
                        INSERT INTO wrong_questions 
                        (user_id, question_id, question_text, question_type, subject,
                         knowledge_point, user_answer, correct_answer, difficulty,
                         last_wrong_time, next_review_time, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        user_id, question_id, question_text, question_type, subject,
                        knowledge_point, user_answer, correct_answer, difficulty,
                        now, next_review, now
                    ))
                    wrong_id = cursor.lastrowid
                    is_new = True
                
                if knowledge_point and subject:
                    cursor.execute('''
                        SELECT id FROM weak_points 
                        WHERE user_id = ? AND subject = ? AND knowledge_point = ?
                    ''', (user_id, subject, knowledge_point))
                    
                    wp = cursor.fetchone()
                    if wp:
                        cursor.execute('''
                            UPDATE weak_points 
                            SET wrong_count = wrong_count + 1,
                                total_count = total_count + 1,
                                error_rate = wrong_count * 1.0 / (total_count + 1),
                                last_updated = ?
                            WHERE id = ?
                        ''', (now, wp['id']))
                    else:
                        cursor.execute('''
                            INSERT INTO weak_points 
                            (user_id, subject, knowledge_point, wrong_count, total_count, 
                             error_rate, last_updated)
                            VALUES (?, ?, ?, 1, 1, 1.0, ?)
                        ''', (user_id, subject, knowledge_point, now))
                
                conn.commit()
            
            return {
                'success': True,
                'wrong_id': wrong_id,
                'is_new': is_new,
                'message': '错题已添加到错题本'
            }
        except Exception as e:
            logger.error(f"添加错题失败: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_wrong_questions(self, user_id: int, subject: str = None,
                            knowledge_point: str = None, 
                            mastery_level: int = None,
                            is_starred: bool = None,
                            page: int = 1, page_size: int = 20) -> Dict:
        """获取错题列表
        
        Args:
            user_id: 用户ID
            subject: 科目筛选
            knowledge_point: 知识点筛选
            mastery_level: 掌握程度筛选
            is_starred: 是否收藏
            page: 页码
            page_size: 每页数量
            
        Returns:
            Dict: 错题列表
        """
        try:
            offset = (page - 1) * page_size
            
            query = "FROM wrong_questions WHERE user_id = ?"
            params = [user_id]
            
            if subject:
                query += " AND subject = ?"
                params.append(subject)
            if knowledge_point:
                query += " AND knowledge_point = ?"
                params.append(knowledge_point)
            if mastery_level is not None:
                query += " AND mastery_level = ?"
                params.append(mastery_level)
            if is_starred is not None:
                query += " AND is_starred = ?"
                params.append(1 if is_starred else 0)
            
            with self._get_db() as conn:
                cursor = conn.cursor()
                
                cursor.execute(f"SELECT COUNT(*) as total {query}", params)
                total = cursor.fetchone()['total']
                
                cursor.execute(f"SELECT * {query} ORDER BY last_wrong_time DESC LIMIT ? OFFSET ?", 
                              params + [page_size, offset])
                
                questions = []
                for row in cursor.fetchall():
                    q = dict(row)
                    if q.get('tags'):
                        try:
                            q['tags'] = json.loads(q['tags'])
                        except:
                            q['tags'] = []
                    questions.append(q)
            
            return {
                'success': True,
                'questions': questions,
                'total': total,
                'page': page,
                'page_size': page_size,
                'total_pages': (total + page_size - 1) // page_size
            }
        except Exception as e:
            logger.error(f"获取错题列表失败: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_today_review(self, user_id: int, count: int = 20) -> Dict:
        """获取今日待复习题目
        
        Args:
            user_id: 用户ID
            count: 题目数量
            
        Returns:
            Dict: 待复习题目
        """
        try:
            now = time.time()
            
            with self._get_db() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT * FROM wrong_questions 
                    WHERE user_id = ? AND next_review_time <= ?
                    ORDER BY mastery_level ASC, wrong_count DESC
                    LIMIT ?
                ''', (user_id, now, count))
                
                questions = [dict(row) for row in cursor.fetchall()]
                
                cursor.execute('''
                    SELECT COUNT(*) as count FROM wrong_questions 
                    WHERE user_id = ? AND next_review_time <= ?
                ''', (user_id, now))
                due_count = cursor.fetchone()['count']
                
                cursor.execute('''
                    SELECT COUNT(*) as count FROM wrong_questions 
                    WHERE user_id = ?
                ''', (user_id,))
                total_count = cursor.fetchone()['count']
            
            return {
                'success': True,
                'questions': questions,
                'due_count': due_count,
                'total_count': total_count,
                'message': f'今日有 {due_count} 道题待复习'
            }
        except Exception as e:
            logger.error(f"获取待复习题目失败: {e}")
            return {'success': False, 'error': str(e)}
    
    def submit_review_result(self, user_id: int, wrong_question_id: int,
                             is_correct: bool, time_spent: int = 0) -> Dict:
        """提交复习结果
        
        Args:
            user_id: 用户ID
            wrong_question_id: 错题ID
            is_correct: 是否答对
            time_spent: 用时（秒）
            
        Returns:
            Dict: 结果
        """
        try:
            now = time.time()
            
            with self._get_db() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT mastery_level, review_count FROM wrong_questions 
                    WHERE id = ? AND user_id = ?
                ''', (wrong_question_id, user_id))
                
                question = cursor.fetchone()
                if not question:
                    return {'success': False, 'error': '错题不存在'}
                
                current_mastery = question['mastery_level']
                review_count = question['review_count']
                
                if is_correct:
                    new_mastery = min(5, current_mastery + 1)
                    interval = [1, 2, 4, 7, 15, 30][new_mastery]
                    next_review = now + interval * 24 * 3600
                else:
                    new_mastery = max(0, current_mastery - 1)
                    next_review = now + 24 * 3600
                
                cursor.execute('''
                    UPDATE wrong_questions 
                    SET mastery_level = ?,
                        review_count = review_count + 1,
                        last_review_time = ?,
                        next_review_time = ?
                    WHERE id = ? AND user_id = ?
                ''', (new_mastery, now, next_review, wrong_question_id, user_id))
                
                cursor.execute('''
                    INSERT INTO wrong_review_records 
                    (user_id, wrong_question_id, result, time_spent, reviewed_at)
                    VALUES (?, ?, ?, ?, ?)
                ''', (user_id, wrong_question_id, 
                      'correct' if is_correct else 'wrong', time_spent, now))
                
                conn.commit()
            
            return {
                'success': True,
                'new_mastery': new_mastery,
                'next_review': next_review,
                'message': '复习结果已记录'
            }
        except Exception as e:
            logger.error(f"提交复习结果失败: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_weak_points(self, user_id: int, subject: str = None,
                        limit: int = 20) -> Dict:
        """获取薄弱知识点
        
        Args:
            user_id: 用户ID
            subject: 科目（可选）
            limit: 返回数量
            
        Returns:
            Dict: 薄弱知识点列表
        """
        try:
            with self._get_db() as conn:
                cursor = conn.cursor()
                
                if subject:
                    cursor.execute('''
                        SELECT * FROM weak_points 
                        WHERE user_id = ? AND subject = ?
                        ORDER BY error_rate DESC, wrong_count DESC
                        LIMIT ?
                    ''', (user_id, subject, limit))
                else:
                    cursor.execute('''
                        SELECT * FROM weak_points 
                        WHERE user_id = ?
                        ORDER BY error_rate DESC, wrong_count DESC
                        LIMIT ?
                    ''', (user_id, limit))
                
                weak_points = [dict(row) for row in cursor.fetchall()]
                
                cursor.execute('''
                    SELECT subject, 
                           COUNT(*) as point_count,
                           SUM(wrong_count) as total_wrong
                    FROM weak_points 
                    WHERE user_id = ?
                    GROUP BY subject
                    ORDER BY total_wrong DESC
                ''', (user_id,))
                subject_stats = [dict(row) for row in cursor.fetchall()]
            
            return {
                'success': True,
                'weak_points': weak_points,
                'subject_stats': subject_stats
            }
        except Exception as e:
            logger.error(f"获取薄弱知识点失败: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_statistics(self, user_id: int) -> Dict:
        """获取错题本统计数据
        
        Args:
            user_id: 用户ID
            
        Returns:
            Dict: 统计数据
        """
        try:
            with self._get_db() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT 
                        COUNT(*) as total_wrong,
                        SUM(CASE WHEN mastery_level = 0 THEN 1 ELSE 0 END) as level0,
                        SUM(CASE WHEN mastery_level = 1 THEN 1 ELSE 0 END) as level1,
                        SUM(CASE WHEN mastery_level = 2 THEN 1 ELSE 0 END) as level2,
                        SUM(CASE WHEN mastery_level = 3 THEN 1 ELSE 0 END) as level3,
                        SUM(CASE WHEN mastery_level >= 4 THEN 1 ELSE 0 END) as level4plus,
                        SUM(CASE WHEN is_starred = 1 THEN 1 ELSE 0 END) as starred_count,
                        SUM(review_count) as total_reviews
                    FROM wrong_questions 
                    WHERE user_id = ?
                ''', (user_id,))
                
                stats = dict(cursor.fetchone())
                
                cursor.execute('''
                    SELECT 
                        subject,
                        COUNT(*) as question_count,
                        SUM(wrong_count) as total_wrong
                    FROM wrong_questions 
                    WHERE user_id = ? AND subject IS NOT NULL
                    GROUP BY subject
                    ORDER BY question_count DESC
                ''', (user_id,))
                
                subject_dist = [dict(row) for row in cursor.fetchall()]
                
                cursor.execute('''
                    SELECT 
                        DATE(reviewed_at, 'unixepoch') as date,
                        COUNT(*) as review_count,
                        SUM(CASE WHEN result = 'correct' THEN 1 ELSE 0 END) as correct_count
                    FROM wrong_review_records 
                    WHERE user_id = ? AND reviewed_at >= ?
                    GROUP BY DATE(reviewed_at, 'unixepoch')
                    ORDER BY date DESC
                    LIMIT 30
                ''', (user_id, time.time() - 30 * 24 * 3600))
                
                review_history = [dict(row) for row in cursor.fetchall()]
            
            return {
                'success': True,
                'statistics': stats,
                'subject_distribution': subject_dist,
                'review_history': list(reversed(review_history))
            }
        except Exception as e:
            logger.error(f"获取统计数据失败: {e}")
            return {'success': False, 'error': str(e)}
    
    def toggle_star(self, user_id: int, wrong_question_id: int) -> Dict:
        """切换收藏状态
        
        Args:
            user_id: 用户ID
            wrong_question_id: 错题ID
            
        Returns:
            Dict: 结果
        """
        try:
            with self._get_db() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    UPDATE wrong_questions 
                    SET is_starred = 1 - is_starred
                    WHERE id = ? AND user_id = ?
                ''', (wrong_question_id, user_id))
                
                cursor.execute('''
                    SELECT is_starred FROM wrong_questions 
                    WHERE id = ? AND user_id = ?
                ''', (wrong_question_id, user_id))
                
                is_starred = cursor.fetchone()['is_starred'] == 1
                
                conn.commit()
            
            return {
                'success': True,
                'is_starred': is_starred,
                'message': '已取消收藏' if not is_starred else '已添加收藏'
            }
        except Exception as e:
            logger.error(f"切换收藏失败: {e}")
            return {'success': False, 'error': str(e)}
    
    def update_note(self, user_id: int, wrong_question_id: int, note: str) -> Dict:
        """更新错题笔记
        
        Args:
            user_id: 用户ID
            wrong_question_id: 错题ID
            note: 笔记内容
            
        Returns:
            Dict: 结果
        """
        try:
            with self._get_db() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    UPDATE wrong_questions 
                    SET note = ?
                    WHERE id = ? AND user_id = ?
                ''', (note, wrong_question_id, user_id))
                
                conn.commit()
            
            return {'success': True, 'message': '笔记已更新'}
        except Exception as e:
            logger.error(f"更新笔记失败: {e}")
            return {'success': False, 'error': str(e)}
    
    def delete_wrong_question(self, user_id: int, wrong_question_id: int) -> Dict:
        """删除错题
        
        Args:
            user_id: 用户ID
            wrong_question_id: 错题ID
            
        Returns:
            Dict: 结果
        """
        try:
            with self._get_db() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    DELETE FROM wrong_questions 
                    WHERE id = ? AND user_id = ?
                ''', (wrong_question_id, user_id))
                
                cursor.execute('''
                    DELETE FROM wrong_review_records 
                    WHERE wrong_question_id = ? AND user_id = ?
                ''', (wrong_question_id, user_id))
                
                conn.commit()
            
            return {'success': True, 'message': '错题已删除'}
        except Exception as e:
            logger.error(f"删除错题失败: {e}")
            return {'success': False, 'error': str(e)}


wrong_book_service = WrongBookService()