import logging
logger = logging.getLogger(__name__)

# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
考试系统增强服务模块
提供高级考试功能:成绩分析,排名系统,证书颁发,错题本等
"""

import sqlite3
import json
import random
from datetime import datetime
from typing import Dict, List, Optional

class ExamEnhancementService:
    """考试系统增强服务"""
    
    def __init__(self, db_path="app.db"):
        self.db_path = db_path
    
    def _connect(self):
        return sqlite3.connect(self.db_path)
    
    def init_database(self):
        """初始化数据库表"""
        with self._connect() as conn:
            cursor = conn.cursor()
            
            # 创建考试成绩表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS exam_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    exam_id INTEGER NOT NULL,
                    score INTEGER DEFAULT 0,
                    max_score INTEGER DEFAULT 100,
                    correct_count INTEGER DEFAULT 0,
                    total_questions INTEGER DEFAULT 0,
                    completed_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    time_spent INTEGER DEFAULT 0,
                    FOREIGN KEY (user_id) REFERENCES users(id),
                    FOREIGN KEY (exam_id) REFERENCES exams(id)
                )
            ''')
            
            # 创建错题本表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS mistake_notebook (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    question_id INTEGER NOT NULL,
                    exam_id INTEGER,
                    wrong_answer TEXT,
                    correct_answer TEXT,
                    added_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    reviewed BOOLEAN DEFAULT FALSE,
                    review_count INTEGER DEFAULT 0,
                    FOREIGN KEY (user_id) REFERENCES users(id),
                    FOREIGN KEY (question_id) REFERENCES questions(id)
                )
            ''')
            
            # 创建考试排名表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS exam_rankings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    exam_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    score INTEGER NOT NULL,
                    rank INTEGER DEFAULT 0,
                    completed_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (exam_id) REFERENCES exams(id),
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            ''')
            
            # 创建证书表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS certificates (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    exam_id INTEGER NOT NULL,
                    certificate_type TEXT DEFAULT 'achievement',
                    issued_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    expires_at TEXT,
                    FOREIGN KEY (user_id) REFERENCES users(id),
                    FOREIGN KEY (exam_id) REFERENCES exams(id)
                )
            ''')
            
            # 创建学习进度表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS learning_progress (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    category TEXT NOT NULL,
                    total_questions INTEGER DEFAULT 0,
                    correct_questions INTEGER DEFAULT 0,
                    last_practice_date TEXT,
                    streak_days INTEGER DEFAULT 0,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            ''')
            
            conn.commit()
    
    def record_exam_result(self, user_id: int, exam_id: int, answers: Dict[int, str]) -> Dict:
        """记录考试结果并评分"""
        with self._connect() as conn:
            cursor = conn.cursor()
            
            # 获取考试题目
            cursor.execute('''
                SELECT eq.question_id, q.correct_answer
                FROM exam_questions eq
                JOIN questions q ON eq.question_id = q.id
                WHERE eq.exam_id = ?
                ORDER BY eq.order_num
            ''', (exam_id,))
            
            questions = cursor.fetchall()
            correct_count = 0
            wrong_questions = []
            
            for q_id, correct_answer in questions:
                user_answer = answers.get(q_id, '')
                if user_answer == correct_answer:
                    correct_count += 1
                else:
                    wrong_questions.append({'question_id': q_id, 'correct_answer': correct_answer, 'wrong_answer': user_answer})
            
            total_questions = len(questions)
            max_score = 100
            score = int((correct_count / total_questions) * max_score) if total_questions > 0 else 0
            
            # 记录考试结果
            cursor.execute('''
                INSERT INTO exam_results 
                (user_id, exam_id, score, max_score, correct_count, total_questions)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (user_id, exam_id, score, max_score, correct_count, total_questions))
            
            result_id = cursor.lastrowid
            
            # 添加错题到错题本
            for wq in wrong_questions:
                cursor.execute('''
                    INSERT OR IGNORE INTO mistake_notebook 
                    (user_id, question_id, exam_id, wrong_answer, correct_answer)
                    VALUES (?, ?, ?, ?, ?)
                ''', (user_id, wq['question_id'], exam_id, wq['wrong_answer'], wq['correct_answer']))
            
            # 更新学习进度
            cursor.execute('''
                SELECT category FROM exams WHERE id = ?
            ''', (exam_id,))
            row = cursor.fetchone()
            if row:
                category = row[0]
                self._update_learning_progress(user_id, category, correct_count, total_questions)
            
            # 更新排名
            self._update_ranking(exam_id, user_id, score)
            
            # 颁发证书
            certificate = self._award_certificate(user_id, exam_id, score)
            
            conn.commit()
            
            return {
                'success': True,
                'result_id': result_id,
                'score': score,
                'max_score': max_score,
                'correct_count': correct_count,
                'total_questions': total_questions,
                'certificate': certificate,
                'wrong_count': len(wrong_questions)
            }
    
    def _update_learning_progress(self, user_id: int, category: str, correct: int, total: int):
        """更新学习进度"""
        with self._connect() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT total_questions, correct_questions FROM learning_progress
                WHERE user_id = ? AND category = ?
            ''', (user_id, category))
            
            row = cursor.fetchone()
            
            if row:
                new_total = row[0] + total
                new_correct = row[1] + correct
                cursor.execute('''
                    UPDATE learning_progress 
                    SET total_questions = ?, correct_questions = ?, last_practice_date = ?
                    WHERE user_id = ? AND category = ?
                ''', (new_total, new_correct, datetime.now(), user_id, category))
            else:
                cursor.execute('''
                    INSERT INTO learning_progress 
                    (user_id, category, total_questions, correct_questions, last_practice_date)
                    VALUES (?, ?, ?, ?, ?)
                ''', (user_id, category, total, correct, datetime.now()))
    
    def _update_ranking(self, exam_id: int, user_id: int, score: int):
        """更新排名"""
        with self._connect() as conn:
            cursor = conn.cursor()
            
            # 计算排名
            cursor.execute('''
                SELECT COUNT(*) FROM exam_rankings 
                WHERE exam_id = ? AND score > ?
            ''', (exam_id, score))
            rank = cursor.fetchone()[0] + 1
            
            cursor.execute('''
                INSERT INTO exam_rankings (exam_id, user_id, score, rank)
                VALUES (?, ?, ?, ?)
            ''', (exam_id, user_id, score, rank))
    
    def _award_certificate(self, user_id: int, exam_id: int, score: int) -> Optional[Dict]:
        """颁发证书"""
        certificate_type = None
        
        if score == 100:
            certificate_type = 'perfect'  # 满分证书
        elif score >= 90:
            certificate_type = 'excellence'  # 优秀证书
        elif score >= 60:
            certificate_type = 'achievement'  # 合格证书
        
        if certificate_type:
            with self._connect() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO certificates (user_id, exam_id, certificate_type)
                    VALUES (?, ?, ?)
                ''', (user_id, exam_id, certificate_type))
                
                cert_id = cursor.lastrowid
                conn.commit()
                
                return {
                    'id': cert_id,
                    'type': certificate_type,
                    'type_label': {
                        'perfect': '满分证书',
                        'excellence': '优秀证书',
                        'achievement': '合格证书'
                    }[certificate_type]
                }
        
        return None
    
    def get_user_exam_history(self, user_id: int, limit: int = 20) -> List[Dict]:
        """获取用户考试历史"""
        with self._connect() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT er.score, er.max_score, er.correct_count, er.total_questions, 
                       er.completed_at, e.name, e.category, e.duration
                FROM exam_results er
                JOIN exams e ON er.exam_id = e.id
                WHERE er.user_id = ?
                ORDER BY er.completed_at DESC
                LIMIT ?
            ''', (user_id, limit))
            
            history = []
            for row in cursor.fetchall():
                history.append({
                    'score': row[0],
                    'max_score': row[1],
                    'correct_count': row[2],
                    'total_questions': row[3],
                    'completed_at': row[4],
                    'exam_name': row[5],
                    'category': row[6],
                    'duration': row[7],
                    'accuracy': round((row[2] / row[3]) * 100, 2) if row[3] > 0 else 0
                })
            
            return history
    
    def get_mistake_notebook(self, user_id: int, limit: int = 50) -> List[Dict]:
        """获取错题本"""
        with self._connect() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT mn.question_id, mn.wrong_answer, mn.correct_answer, 
                       mn.added_at, mn.reviewed, mn.review_count, q.question_text, q.options, q.category
                FROM mistake_notebook mn
                JOIN questions q ON mn.question_id = q.id
                WHERE mn.user_id = ?
                ORDER BY mn.added_at DESC
                LIMIT ?
            ''', (user_id, limit))
            
            mistakes = []
            for row in cursor.fetchall():
                mistakes.append({
                    'question_id': row[0],
                    'wrong_answer': row[1],
                    'correct_answer': row[2],
                    'added_at': row[3],
                    'reviewed': bool(row[4]),
                    'review_count': row[5],
                    'question_text': row[6],
                    'options': json.loads(row[7]),
                    'category': row[8]
                })
            
            return mistakes
    
    def review_mistake(self, user_id: int, question_id: int):
        """标记错题已复习"""
        with self._connect() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE mistake_notebook 
                SET reviewed = ?, review_count = review_count + 1
                WHERE user_id = ? AND question_id = ?
            ''', (True, user_id, question_id))
            
            conn.commit()
    
    def get_learning_progress(self, user_id: int) -> Dict:
        """获取学习进度"""
        with self._connect() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT category, total_questions, correct_questions, streak_days
                FROM learning_progress
                WHERE user_id = ?
            ''', (user_id,))
            
            progress = {}
            total_all = 0
            correct_all = 0
            
            for row in cursor.fetchall():
                category = row[0]
                total = row[1]
                correct = row[2]
                progress[category] = {
                    'total_questions': total,
                    'correct_questions': correct,
                    'accuracy': round((correct / total) * 100, 2) if total > 0 else 0,
                    'streak_days': row[3]
                }
                total_all += total
                correct_all += correct
            
            progress['overall'] = {
                'total_questions': total_all,
                'correct_questions': correct_all,
                'accuracy': round((correct_all / total_all) * 100, 2) if total_all > 0 else 0
            }
            
            return progress
    
    def get_exam_ranking(self, exam_id: int, limit: int = 10) -> List[Dict]:
        """获取考试排名"""
        with self._connect() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT er.rank, u.username, er.score, er.completed_at
                FROM exam_rankings er
                JOIN users u ON er.user_id = u.id
                WHERE er.exam_id = ?
                ORDER BY er.rank
                LIMIT ?
            ''', (exam_id, limit))
            
            rankings = []
            for row in cursor.fetchall():
                rankings.append({
                    'rank': row[0],
                    'username': row[1],
                    'score': row[2],
                    'completed_at': row[3]
                })
            
            return rankings
    
    def get_user_certificates(self, user_id: int) -> List[Dict]:
        """获取用户证书"""
        with self._connect() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT c.id, c.certificate_type, c.issued_at, e.name, e.category
                FROM certificates c
                JOIN exams e ON c.exam_id = e.id
                WHERE c.user_id = ?
                ORDER BY c.issued_at DESC
            ''', (user_id,))
            
            certificates = []
            for row in cursor.fetchall():
                certificates.append({
                    'id': row[0],
                    'type': row[1],
                    'type_label': {
                        'perfect': '满分证书',
                        'excellence': '优秀证书',
                        'achievement': '合格证书'
                    }[row[1]],
                    'issued_at': row[2],
                    'exam_name': row[3],
                    'category': row[4]
                })
            
            return certificates
    
    def generate_practice_set(self, user_id: int, category: str, count: int = 10) -> List[Dict]:
        """生成练习题目(基于错题和薄弱环节)"""
        with self._connect() as conn:
            cursor = conn.cursor()
            
            # 首先从错题本中选择未复习的题目
            cursor.execute('''
                SELECT q.id, q.question_text, q.options, q.correct_answer, q.difficulty, q.category
                FROM mistake_notebook mn
                JOIN questions q ON mn.question_id = q.id
                WHERE mn.user_id = ? AND mn.reviewed = FALSE AND (? IS NULL OR q.category = ?)
                ORDER BY mn.added_at DESC
                LIMIT ?
            ''', (user_id, category, category, count // 2))
            
            practice_questions = []
            for row in cursor.fetchall():
                practice_questions.append({
                    'question_id': row[0],
                    'question_text': row[1],
                    'options': json.loads(row[2]),
                    'correct_answer': row[3],
                    'difficulty': row[4],
                    'category': row[5],
                    'from_mistake': True
                })
            
            # 补充其他题目
            if len(practice_questions) < count:
                remaining = count - len(practice_questions)
                cursor.execute('''
                    SELECT id, question_text, options, correct_answer, difficulty, category
                    FROM questions 
                    WHERE (? IS NULL OR category = ?)
                    ORDER BY RANDOM()
                    LIMIT ?
                ''', (category, category, remaining))
                
                for row in cursor.fetchall():
                    practice_questions.append({
                        'question_id': row[0],
                        'question_text': row[1],
                        'options': json.loads(row[2]),
                        'correct_answer': row[3],
                        'difficulty': row[4],
                        'category': row[5],
                        'from_mistake': False
                    })
            
            random.shuffle(practice_questions)
            return practice_questions
    
    def get_statistics(self, user_id: int) -> Dict:
        """获取用户统计数据"""
        with self._connect() as conn:
            cursor = conn.cursor()
            
            # 考试总数和平均分
            cursor.execute('''
                SELECT COUNT(*), AVG(score) FROM exam_results WHERE user_id = ?
            ''', (user_id,))
            row = cursor.fetchone()
            total_exams = row[0]
            avg_score = round(row[1], 2) if row[1] else 0
            
            # 证书数量
            cursor.execute('''
                SELECT COUNT(*) FROM certificates WHERE user_id = ?
            ''', (user_id,))
            cert_count = cursor.fetchone()[0]
            
            # 错题数量
            cursor.execute('''
                SELECT COUNT(*) FROM mistake_notebook WHERE user_id = ?
            ''', (user_id,))
            mistake_count = cursor.fetchone()[0]
            
            # 学习进度
            progress = self.get_learning_progress(user_id)
            
            return {
                'total_exams': total_exams,
                'avg_score': avg_score,
                'certificate_count': cert_count,
                'mistake_count': mistake_count,
                'learning_progress': progress
            }

# 全局实例
exam_enhancement_service = None

def get_exam_enhancement_service():
    """获取考试增强服务实例"""
    global exam_enhancement_service
    if exam_enhancement_service is None:
        exam_enhancement_service = ExamEnhancementService()
    return exam_enhancement_service

if __name__ == "__main__":
    service = ExamEnhancementService()
    service.init_database()
    logger.info("考试增强服务初始化完成")
