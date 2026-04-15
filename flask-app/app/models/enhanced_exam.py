#!/usr/bin/env python3
"""
增强的考试系统模型
"""

import time
import json
from typing import Dict, List, Any, Optional

from app.utils.db import db_manager
from app.utils.logging import logger

class EnhancedExam:
    """增强的考试模型"""
    
    def __init__(self):
        """初始化考试模型"""
        self._create_tables()
    
    def _create_tables(self):
        """创建必要的表"""
        try:
            # 创建考试表
            db_manager.execute('''
                CREATE TABLE IF NOT EXISTS exams (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    description TEXT,
                    duration INTEGER,  -- 考试时长（分钟）
                    total_questions INTEGER,
                    passing_score REAL,
                    is_active INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 创建题目表（增强版）
            db_manager.execute('''
                CREATE TABLE IF NOT EXISTS questions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    exam_id INTEGER,
                    type TEXT NOT NULL,  -- multiple_choice, true_false, short_answer, essay, listening
                    content TEXT NOT NULL,
                    options TEXT,  -- JSON格式存储选项
                    correct_answer TEXT,
                    difficulty INTEGER DEFAULT 1,  -- 1-5
                    points REAL DEFAULT 1.0,
                    audio_url TEXT,  -- 听力题音频URL
                    tags TEXT,  -- 题目标签，逗号分隔
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (exam_id) REFERENCES exams(id)
                )
            ''')
            
            # 创建考试记录表
            db_manager.execute('''
                CREATE TABLE IF NOT EXISTS exam_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    exam_id INTEGER,
                    score REAL,
                    total_questions INTEGER,
                    correct_answers INTEGER,
                    start_time TIMESTAMP,
                    end_time TIMESTAMP,
                    duration INTEGER,  -- 实际考试时长（秒）
                    status TEXT DEFAULT 'completed',  -- pending, in_progress, completed, cancelled
                    answers TEXT,  -- JSON格式存储答案
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES user(id),
                    FOREIGN KEY (exam_id) REFERENCES exams(id)
                )
            ''')
            
            # 创建答题记录表
            db_manager.execute('''
                CREATE TABLE IF NOT EXISTS answer_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    exam_record_id INTEGER,
                    question_id INTEGER,
                    user_answer TEXT,
                    is_correct INTEGER,
                    points_earned REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (exam_record_id) REFERENCES exam_records(id),
                    FOREIGN KEY (question_id) REFERENCES questions(id)
                )
            ''')
            
            logger.info("考试系统表结构创建完成")
            
        except Exception as e:
            logger.error(f"创建考试系统表结构失败: {str(e)}")
    
    def create_exam(self, name: str, description: str, duration: int, total_questions: int, passing_score: float) -> int:
        """
        创建新考试
        
        Args:
            name: 考试名称
            description: 考试描述
            duration: 考试时长（分钟）
            total_questions: 总题数
            passing_score: 及格分数
        
        Returns:
            考试ID
        """
        try:
            db_manager.execute(
                '''
                INSERT INTO exams (name, description, duration, total_questions, passing_score)
                VALUES (?, ?, ?, ?, ?)
                ''',
                (name, description, duration, total_questions, passing_score)
            )
            # 获取最后插入的ID
            result = db_manager.fetch_one('SELECT last_insert_rowid()')
            if result:
                if isinstance(result, dict):
                    return result['last_insert_rowid()']
                return result[0]
            return -1
        except Exception as e:
            logger.error(f"创建考试失败: {str(e)}")
            return -1
    
    def add_question(self, exam_id: int, question_type: str, content: str, options: List[str] = None, 
                     correct_answer: str = None, difficulty: int = 1, points: float = 1.0, 
                     audio_url: str = None, tags: List[str] = None) -> int:
        """
        添加题目
        
        Args:
            exam_id: 考试ID
            question_type: 题目类型
            content: 题目内容
            options: 选项列表（选择题）
            correct_answer: 正确答案
            difficulty: 难度（1-5）
            points: 分值
            audio_url: 音频URL（听力题）
            tags: 标签列表
        
        Returns:
            题目ID
        """
        try:
            options_json = json.dumps(options) if options else None
            tags_str = ','.join(tags) if tags else None
            
            db_manager.execute(
                '''
                INSERT INTO questions (exam_id, type, content, options, correct_answer, difficulty, points, audio_url, tags)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''',
                (exam_id, question_type, content, options_json, correct_answer, difficulty, points, audio_url, tags_str)
            )
            # 获取最后插入的ID
            result = db_manager.fetch_one('SELECT last_insert_rowid()')
            if result:
                if isinstance(result, dict):
                    return result['last_insert_rowid()']
                return result[0]
            return -1
        except Exception as e:
            logger.error(f"添加题目失败: {str(e)}")
            return -1
    
    def start_exam(self, user_id: int, exam_id: int) -> int:
        """
        开始考试
        
        Args:
            user_id: 用户ID
            exam_id: 考试ID
        
        Returns:
            考试记录ID
        """
        try:
            start_time = time.time()
            
            db_manager.execute(
                '''
                INSERT INTO exam_records (user_id, exam_id, start_time, status)
                VALUES (?, ?, ?, ?)
                ''',
                (user_id, exam_id, start_time, 'in_progress')
            )
            # 获取最后插入的ID
            result = db_manager.fetch_one('SELECT last_insert_rowid()')
            if result:
                if isinstance(result, dict):
                    return result['last_insert_rowid()']
                return result[0]
            return -1
        except Exception as e:
            logger.error(f"开始考试失败: {str(e)}")
            return -1
    
    def submit_exam(self, exam_record_id: int, answers: Dict[int, str]) -> Dict[str, Any]:
        """
        提交考试
        
        Args:
            exam_record_id: 考试记录ID
            answers: 答案字典 {question_id: answer}
        
        Returns:
            考试结果
        """
        try:
            # 获取考试记录
            record = db_manager.fetch_one(
                'SELECT * FROM exam_records WHERE id = ?',
                (exam_record_id,)
            )
            
            if not record:
                raise Exception("考试记录不存在")
            
            user_id = record['user_id'] if isinstance(record, dict) else record[1]
            exam_id = record['exam_id'] if isinstance(record, dict) else record[2]
            start_time = record['start_time'] if isinstance(record, dict) else record[6]
            
            # 获取所有题目
            questions = db_manager.fetch_all(
                'SELECT * FROM questions WHERE exam_id = ?',
                (exam_id,)
            )
            
            # 计算分数
            total_score = 0
            correct_count = 0
            total_questions = len(questions)
            answer_records = []
            
            for question in questions:
                q_id = question['id'] if isinstance(question, dict) else question[0]
                q_type = question['type'] if isinstance(question, dict) else question[3]
                correct_answer = question['correct_answer'] if isinstance(question, dict) else question[5]
                points = question['points'] if isinstance(question, dict) else question[7]
                
                user_answer = answers.get(str(q_id), '')
                is_correct = 0
                points_earned = 0
                
                # 判断答案是否正确
                if q_type in ['multiple_choice', 'true_false']:
                    if user_answer == correct_answer:
                        is_correct = 1
                        points_earned = points
                elif q_type == 'short_answer':
                    # 简单的短答案判断
                    if user_answer.strip().lower() == correct_answer.strip().lower():
                        is_correct = 1
                        points_earned = points
                elif q_type == 'listening':
                    # 听力题判断
                    if user_answer == correct_answer:
                        is_correct = 1
                        points_earned = points
                # 作文题暂不自动评分
                
                total_score += points_earned
                if is_correct:
                    correct_count += 1
                
                # 保存答题记录
                db_manager.execute(
                    '''
                    INSERT INTO answer_records (exam_record_id, question_id, user_answer, is_correct, points_earned)
                    VALUES (?, ?, ?, ?, ?)
                    ''',
                    (exam_record_id, q_id, user_answer, is_correct, points_earned)
                )
            
            # 更新考试记录
            end_time = time.time()
            duration = int(end_time - start_time)
            answers_json = json.dumps(answers)
            
            db_manager.execute(
                '''
                UPDATE exam_records
                SET score = ?, total_questions = ?, correct_answers = ?, end_time = ?, duration = ?, status = ?, answers = ?
                WHERE id = ?
                ''',
                (total_score, total_questions, correct_count, end_time, duration, 'completed', answers_json, exam_record_id)
            )
            
            # 获取考试信息
            exam = db_manager.fetch_one(
                'SELECT passing_score FROM exams WHERE id = ?',
                (exam_id,)
            )
            passing_score = exam['passing_score'] if isinstance(exam, dict) else exam[0]
            passed = total_score >= passing_score
            
            return {
                'exam_record_id': exam_record_id,
                'score': total_score,
                'total_questions': total_questions,
                'correct_answers': correct_count,
                'duration': duration,
                'passed': passed,
                'passing_score': passing_score
            }
            
        except Exception as e:
            logger.error(f"提交考试失败: {str(e)}")
            return None
    
    def get_exam(self, exam_id: int) -> Dict[str, Any]:
        """
        获取考试信息
        
        Args:
            exam_id: 考试ID
        
        Returns:
            考试信息
        """
        try:
            exam = db_manager.fetch_one(
                'SELECT * FROM exams WHERE id = ?',
                (exam_id,)
            )
            
            if not exam:
                return None
            
            # 获取题目
            questions = db_manager.fetch_all(
                'SELECT * FROM questions WHERE exam_id = ?',
                (exam_id,)
            )
            
            # 格式化题目
            formatted_questions = []
            for question in questions:
                q_dict = {
                    'id': question['id'] if isinstance(question, dict) else question[0],
                    'type': question['type'] if isinstance(question, dict) else question[3],
                    'content': question['content'] if isinstance(question, dict) else question[4],
                    'difficulty': question['difficulty'] if isinstance(question, dict) else question[6],
                    'points': question['points'] if isinstance(question, dict) else question[7],
                    'audio_url': question['audio_url'] if isinstance(question, dict) else question[8]
                }
                
                # 解析选项
                options = question['options'] if isinstance(question, dict) else question[5]
                if options:
                    q_dict['options'] = json.loads(options)
                
                # 解析标签
                tags = question['tags'] if isinstance(question, dict) else question[9]
                if tags:
                    q_dict['tags'] = tags.split(',')
                
                formatted_questions.append(q_dict)
            
            return {
                'id': exam['id'] if isinstance(exam, dict) else exam[0],
                'name': exam['name'] if isinstance(exam, dict) else exam[1],
                'description': exam['description'] if isinstance(exam, dict) else exam[2],
                'duration': exam['duration'] if isinstance(exam, dict) else exam[3],
                'total_questions': exam['total_questions'] if isinstance(exam, dict) else exam[4],
                'passing_score': exam['passing_score'] if isinstance(exam, dict) else exam[5],
                'is_active': exam['is_active'] if isinstance(exam, dict) else exam[6],
                'questions': formatted_questions
            }
            
        except Exception as e:
            logger.error(f"获取考试信息失败: {str(e)}")
            return None
    
    def get_user_exam_records(self, user_id: int) -> List[Dict[str, Any]]:
        """
        获取用户考试记录
        
        Args:
            user_id: 用户ID
        
        Returns:
            考试记录列表
        """
        try:
            records = db_manager.fetch_all(
                '''
                SELECT er.*, e.name as exam_name
                FROM exam_records er
                JOIN exams e ON er.exam_id = e.id
                WHERE er.user_id = ?
                ORDER BY er.created_at DESC
                ''',
                (user_id,)
            )
            
            formatted_records = []
            for record in records:
                formatted_records.append({
                    'id': record['id'] if isinstance(record, dict) else record[0],
                    'exam_id': record['exam_id'] if isinstance(record, dict) else record[2],
                    'exam_name': record['exam_name'] if isinstance(record, dict) else record[13],
                    'score': record['score'] if isinstance(record, dict) else record[3],
                    'total_questions': record['total_questions'] if isinstance(record, dict) else record[4],
                    'correct_answers': record['correct_answers'] if isinstance(record, dict) else record[5],
                    'start_time': record['start_time'] if isinstance(record, dict) else record[6],
                    'end_time': record['end_time'] if isinstance(record, dict) else record[7],
                    'duration': record['duration'] if isinstance(record, dict) else record[8],
                    'status': record['status'] if isinstance(record, dict) else record[9],
                    'created_at': record['created_at'] if isinstance(record, dict) else record[11]
                })
            
            return formatted_records
            
        except Exception as e:
            logger.error(f"获取用户考试记录失败: {str(e)}")
            return []
    
    def get_exam_statistics(self, exam_id: int) -> Dict[str, Any]:
        """
        获取考试统计信息
        
        Args:
            exam_id: 考试ID
        
        Returns:
            统计信息
        """
        try:
            # 获取考试信息
            exam = db_manager.fetch_one(
                'SELECT * FROM exams WHERE id = ?',
                (exam_id,)
            )
            
            if not exam:
                return None
            
            # 获取统计数据
            stats = db_manager.fetch_one(
                '''
                SELECT 
                    COUNT(*) as total_takers,
                    AVG(score) as average_score,
                    MIN(score) as min_score,
                    MAX(score) as max_score,
                    SUM(CASE WHEN score >= ? THEN 1 ELSE 0 END) as passed_count
                FROM exam_records
                WHERE exam_id = ? AND status = 'completed'
                ''',
                (exam['passing_score'] if isinstance(exam, dict) else exam[5], exam_id)
            )
            
            if not stats:
                return {
                    'exam_id': exam_id,
                    'exam_name': exam['name'] if isinstance(exam, dict) else exam[1],
                    'total_takers': 0,
                    'average_score': 0,
                    'min_score': 0,
                    'max_score': 0,
                    'passed_count': 0,
                    'pass_rate': 0
                }
            
            total_takers = stats['total_takers'] if isinstance(stats, dict) else stats[0]
            passed_count = stats['passed_count'] if isinstance(stats, dict) else stats[4]
            pass_rate = (passed_count / total_takers * 100) if total_takers > 0 else 0
            
            return {
                'exam_id': exam_id,
                'exam_name': exam['name'] if isinstance(exam, dict) else exam[1],
                'total_takers': total_takers,
                'average_score': stats['average_score'] if isinstance(stats, dict) else stats[1],
                'min_score': stats['min_score'] if isinstance(stats, dict) else stats[2],
                'max_score': stats['max_score'] if isinstance(stats, dict) else stats[3],
                'passed_count': passed_count,
                'pass_rate': pass_rate
            }
            
        except Exception as e:
            logger.error(f"获取考试统计信息失败: {str(e)}")
            return None

# 创建全局考试系统实例
enhanced_exam_system = EnhancedExam()
