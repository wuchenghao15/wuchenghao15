import logging
logger = logging.getLogger(__name__)

# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
升级考试服务模块
负责升级考试,补考和留级机制
"""

import sqlite3
import json
from datetime import datetime
from typing import Dict, Optional, List

class PromotionExamService:
    """升级考试服务"""
    
    def __init__(self, db_path="app.db"):
        self.db_path = db_path
        self.PASS_SCORE = 60  # 及格分数
        self.MAX_RETAKE = 1    # 最大补考次数
    
    def _connect(self):
        return sqlite3.connect(self.db_path)
    
    def init_database(self):
        """初始化数据库表"""
        with self._connect() as conn:
            cursor = conn.cursor()
            
            # 创建升级考试表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS promotion_exams (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    current_grade TEXT NOT NULL,
                    target_grade TEXT NOT NULL,
                    exam_type TEXT DEFAULT 'normal',
                    status TEXT DEFAULT 'created',
                    score INTEGER DEFAULT 0,
                    max_score INTEGER DEFAULT 100,
                    passed BOOLEAN DEFAULT FALSE,
                    attempt_count INTEGER DEFAULT 1,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    completed_at TEXT,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            ''')
            
            # 创建升级考试题目关联表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS promotion_exam_questions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    exam_id INTEGER NOT NULL,
                    question_id INTEGER NOT NULL,
                    order_num INTEGER DEFAULT 0,
                    FOREIGN KEY (exam_id) REFERENCES promotion_exams(id)
                )
            ''')
            
            # 创建学生升级记录表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS grade_promotion_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    from_grade TEXT NOT NULL,
                    to_grade TEXT,
                    exam_id INTEGER,
                    result TEXT,
                    promoted_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id),
                    FOREIGN KEY (exam_id) REFERENCES promotion_exams(id)
                )
            ''')
            
            # 确保users表有相关字段
            cursor.execute("PRAGMA table_info(users)")
            columns = [col[1] for col in cursor.fetchall()]
            if 'promotion_attempts' not in columns:
                cursor.execute('ALTER TABLE users ADD COLUMN promotion_attempts INTEGER DEFAULT 0')
            if 'last_promotion_date' not in columns:
                cursor.execute('ALTER TABLE users ADD COLUMN last_promotion_date TEXT')
            
            conn.commit()
    
    def can_take_promotion_exam(self, user_id: int) -> Dict:
        """检查用户是否可以参加升级考试"""
        from app.services.grade_manager import get_grade_manager
        grade_manager = get_grade_manager()
        
        user_grade = grade_manager.get_user_grade(user_id)
        if not user_grade:
            return {'can_take': False, 'reason': '未设置年级'}
        
        # 大学及以上不参与升级考试
        if grade_manager.is_college_level(user_grade):
            return {'can_take': False, 'reason': '大学及以上级别不参与升级考试'}
        
        # 检查是否已完成当年升级考试
        today = datetime.now()
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT COUNT(*) FROM promotion_exams 
                WHERE user_id = ? AND strftime('%Y', created_at) = ?
            ''', (user_id, str(today.year)))
            count = cursor.fetchone()[0]
            
            if count >= 2:  # 正常考试 + 补考
                return {'can_take': False, 'reason': '本年度升级机会已用完'}
        
        return {'can_take': True, 'reason': '可以参加升级考试', 'current_grade': user_grade}
    
    def create_promotion_exam(self, user_id: int, exam_type: str = 'normal') -> Optional[Dict]:
        """创建升级考试"""
        from app.services.grade_manager import get_grade_manager
        grade_manager = get_grade_manager()
        
        user_grade = grade_manager.get_user_grade(user_id)
        if not user_grade:
            return None
        
        grade_index = grade_manager.get_grade_index(user_grade)
        if grade_index < 0 or grade_index >= len(grade_manager.GRADE_LEVELS) - 2:
            return None
        
        target_grade = grade_manager.GRADE_LEVELS[grade_index + 1]
        
        # 检查是否已有未完成的考试
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id FROM promotion_exams 
                WHERE user_id = ? AND status = 'created'
            ''', (user_id,))
            if cursor.fetchone():
                return None
            
            # 创建考试
            cursor.execute('''
                INSERT INTO promotion_exams 
                (user_id, current_grade, target_grade, exam_type, status, attempt_count)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (user_id, user_grade, target_grade, exam_type, 'created', 1))
            
            exam_id = cursor.lastrowid
            
            # 关联题目
            cursor.execute('''
                SELECT id FROM questions 
                WHERE category IN ('math', 'chinese', 'english') 
                ORDER BY RANDOM() LIMIT 20
            ''')
            questions = [row[0] for row in cursor.fetchall()]
            
            for i, q_id in enumerate(questions):
                cursor.execute('''
                    INSERT INTO promotion_exam_questions (exam_id, question_id, order_num)
                    VALUES (?, ?, ?)
                ''', (exam_id, q_id, i + 1))
            
            conn.commit()
        
        return {
            'exam_id': exam_id,
            'user_id': user_id,
            'current_grade': user_grade,
            'target_grade': target_grade,
            'exam_type': exam_type,
            'question_count': len(questions)
        }
    
    def get_promotion_exam(self, exam_id: int) -> Optional[Dict]:
        """获取升级考试信息"""
        with self._connect() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, user_id, current_grade, target_grade, exam_type, status, 
                       score, max_score, passed, attempt_count, created_at, completed_at
                FROM promotion_exams WHERE id = ?
            ''', (exam_id,))
            
            row = cursor.fetchone()
            if not row:
                return None
            
            cursor.execute('''
                SELECT qe.question_id, q.question_text, q.options, q.correct_answer, qe.order_num
                FROM promotion_exam_questions qe
                JOIN questions q ON qe.question_id = q.id
                WHERE qe.exam_id = ?
                ORDER BY qe.order_num
            ''', (exam_id,))
            
            questions = []
            for q_row in cursor.fetchall():
                questions.append({
                    'question_id': q_row[0],
                    'question_text': q_row[1],
                    'options': json.loads(q_row[2]),
                    'correct_answer': q_row[3],
                    'order_num': q_row[4]
                })
            
            return {
                'id': row[0],
                'user_id': row[1],
                'current_grade': row[2],
                'target_grade': row[3],
                'exam_type': row[4],
                'status': row[5],
                'score': row[6],
                'max_score': row[7],
                'passed': bool(row[8]),
                'attempt_count': row[9],
                'created_at': row[10],
                'completed_at': row[11],
                'questions': questions
            }
    
    def start_exam(self, exam_id: int) -> bool:
        """开始考试"""
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE promotion_exams SET status = 'in_progress' 
                WHERE id = ? AND status = 'created'
            ''', (exam_id,))
            conn.commit()
            return cursor.rowcount > 0
    
    def submit_answers(self, exam_id: int, answers: Dict[int, str]) -> Dict:
        """提交答案并评分"""
        exam = self.get_promotion_exam(exam_id)
        if not exam or exam['status'] != 'in_progress':
            return {'success': False, 'message': '考试状态无效'}
        
        correct_count = 0
        for q in exam['questions']:
            if answers.get(q['question_id']) == q['correct_answer']:
                correct_count += 1
        
        score = int((correct_count / len(exam['questions'])) * exam['max_score'])
        passed = score >= self.PASS_SCORE
        
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE promotion_exams 
                SET status = 'completed', score = ?, passed = ?, completed_at = ?
                WHERE id = ?
            ''', (score, passed, datetime.now(), exam_id))
            conn.commit()
        
        return {
            'success': True,
            'score': score,
            'max_score': exam['max_score'],
            'passed': passed,
            'correct_count': correct_count,
            'total_questions': len(exam['questions'])
        }
    
    def process_promotion_result(self, exam_id: int) -> Dict:
        """处理升级考试结果"""
        exam = self.get_promotion_exam(exam_id)
        if not exam or exam['status'] != 'completed':
            return {'success': False, 'message': '考试未完成'}
        
        from app.services.grade_manager import get_grade_manager
        grade_manager = get_grade_manager()
        
        result = {}
        
        if exam['passed']:
            # 升级成功
            grade_manager.set_user_grade(exam['user_id'], exam['target_grade'])
            
            # 更新用户升级记录
            with self._connect() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO grade_promotion_records 
                    (user_id, from_grade, to_grade, exam_id, result)
                    VALUES (?, ?, ?, ?, ?)
                ''', (exam['user_id'], exam['current_grade'], exam['target_grade'], exam_id, 'promoted'))
                
                cursor.execute('''
                    UPDATE users 
                    SET promotion_attempts = 0, last_promotion_date = ?
                    WHERE id = ?
                ''', (datetime.now(), exam['user_id']))
                
                conn.commit()
            
            result = {
                'success': True,
                'result': 'promoted',
                'message': f'升级成功!从{exam["current_grade"]}升级到{exam["target_grade"]}',
                'new_grade': exam['target_grade']
            }
        else:
            # 升级失败
            if exam['attempt_count'] < self.MAX_RETAKE + 1:  # 1次正常 + 1次补考
                # 可以补考
                result = {
                    'success': True,
                    'result': 'retake_available',
                    'message': f'升级考试未通过,分数{exam["score"]}分,可申请补考',
                    'score': exam['score'],
                    'can_retake': True
                }
            else:
                # 留级
                result = {
                    'success': True,
                    'result': 'retained',
                    'message': f'升级考试和补考均未通过,留级至{exam["current_grade"]}',
                    'retained_grade': exam['current_grade']
                }
                
                # 记录留级
                with self._connect() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO grade_promotion_records 
                        (user_id, from_grade, to_grade, exam_id, result)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (exam['user_id'], exam['current_grade'], None, exam_id, 'retained'))
                    
                    cursor.execute('''
                        UPDATE users SET promotion_attempts = 0 WHERE id = ?
                    ''', (exam['user_id'],))
                    
                    conn.commit()
        
        return result
    
    def create_retake_exam(self, user_id: int) -> Optional[Dict]:
        """创建补考"""
        from app.services.grade_manager import get_grade_manager
        grade_manager = get_grade_manager()
        
        user_grade = grade_manager.get_user_grade(user_id)
        if not user_grade:
            return None
        
        # 检查是否有资格补考
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT COUNT(*) FROM promotion_exams 
                WHERE user_id = ? AND exam_type = 'normal' AND passed = FALSE
                AND strftime('%Y', created_at) = ?
            ''', (user_id, str(datetime.now().year)))
            
            if cursor.fetchone()[0] == 0:
                return None  # 没有需要补考的考试
            
            # 检查是否已经补考
            cursor.execute('''
                SELECT COUNT(*) FROM promotion_exams 
                WHERE user_id = ? AND exam_type = 'retake'
                AND strftime('%Y', created_at) = ?
            ''', (user_id, str(datetime.now().year)))
            
            if cursor.fetchone()[0] > 0:
                return None  # 已经补考了
        
        return self.create_promotion_exam(user_id, 'retake')
    
    def get_user_promotion_history(self, user_id: int, limit: int = 10) -> List[Dict]:
        """获取用户升级历史"""
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT pr.from_grade, pr.to_grade, pr.result, pr.promoted_at, pe.score, pe.exam_type
                FROM grade_promotion_records pr
                LEFT JOIN promotion_exams pe ON pr.exam_id = pe.id
                WHERE pr.user_id = ?
                ORDER BY pr.promoted_at DESC
                LIMIT ?
            ''', (user_id, limit))
            
            records = []
            for row in cursor.fetchall():
                records.append({
                    'from_grade': row[0],
                    'to_grade': row[1],
                    'result': row[2],
                    'promoted_at': row[3],
                    'score': row[4],
                    'exam_type': row[5]
                })
            
            return records
    
    def get_retake_status(self, user_id: int) -> Dict:
        """获取补考状态"""
        with self._connect() as conn:
            cursor = conn.cursor()
            
            # 检查是否有未通过的正常考试
            cursor.execute('''
                SELECT id, score, current_grade, target_grade FROM promotion_exams 
                WHERE user_id = ? AND exam_type = 'normal' AND passed = FALSE
                AND strftime('%Y', created_at) = ?
            ''', (user_id, str(datetime.now().year)))
            
            normal_exam = cursor.fetchone()
            
            if not normal_exam:
                return {'can_retake': False, 'reason': '没有需要补考的考试'}
            
            # 检查是否已经补考
            cursor.execute('''
                SELECT COUNT(*) FROM promotion_exams 
                WHERE user_id = ? AND exam_type = 'retake'
                AND strftime('%Y', created_at) = ?
            ''', (user_id, str(datetime.now().year)))
            
            if cursor.fetchone()[0] > 0:
                return {'can_retake': False, 'reason': '本年度已补考'}
            
            return {
                'can_retake': True,
                'exam_id': normal_exam[0],
                'score': normal_exam[1],
                'current_grade': normal_exam[2],
                'target_grade': normal_exam[3]
            }

# 全局实例
promotion_exam_service = None

def get_promotion_exam_service():
    """获取升级考试服务实例"""
    global promotion_exam_service
    if promotion_exam_service is None:
        promotion_exam_service = PromotionExamService()
    return promotion_exam_service

if __name__ == "__main__":
    service = PromotionExamService()
    service.init_database()
    logger.info("升级考试服务初始化完成")
