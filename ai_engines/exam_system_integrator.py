# -*- coding: utf-8 -*-
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
考试系统整合AI管理器
整合专家AI、老师AI、题库AI等,实现完整的智能考试系统
"""

import random
import sqlite3
import uuid
import logging
from contextlib import contextmanager
from datetime import datetime
from typing import Dict, List, Any, Optional
import sys
import os
import json


# 确保日志目录存在
LOG_DIR = os.path.join(
    os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__)
        )
    ),
    '..',
    'logs'
)

os.makedirs(LOG_DIR, exist_ok=True)

# 配置日志
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# 避免重复添加handler
if not logger.handlers:
    handler = logging.FileHandler(os.path.join(LOG_DIR, 'exam_system.log'))
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.ai.question_generator import question_generator
from app.ai.narrow_road_question_bank import narrow_road_question_bank

DATABASE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '..', 'app.db')


class ExamSystemIntegrator:
    """考试系统整合AI管理器"""
    
    def __init__(self):
        self.question_generator = question_generator
        self.question_bank = narrow_road_question_bank
        self.init_database()
    
    @contextmanager
    def get_db_connection(self):
        """获取数据库连接上下文管理器"""
        conn = sqlite3.connect(DATABASE_PATH, timeout=10)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
    
    def init_database(self):
        """初始化数据库表结构"""
        try:
            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS ai_generated_questions (
                        id TEXT PRIMARY KEY,
                        exam_id TEXT,
                        question_type TEXT,
                        language TEXT,
                        difficulty TEXT,
                        content TEXT,
                        options TEXT,
                        correct_answer TEXT,
                        explanation TEXT,
                        generated_by TEXT,
                        generated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        used_count INTEGER DEFAULT 0
                    )
                ''')
                
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS exam_sessions (
                        id TEXT PRIMARY KEY,
                        exam_id TEXT,
                        user_id TEXT,
                        start_time TEXT DEFAULT CURRENT_TIMESTAMP,
                        end_time TEXT,
                        status TEXT DEFAULT 'in_progress',
                        score REAL,
                        ai_analysis TEXT,
                        metadata TEXT,
                        total_questions INTEGER DEFAULT 0,
                        correct_count INTEGER DEFAULT 0
                    )
                ''')
                
                # 添加缺失的列
                for column_name, column_def in [
                    ('end_time', 'TEXT'),
                    ('score', 'REAL'),
                    ('ai_analysis', 'TEXT'),
                    ('metadata', 'TEXT'),
                    ('total_questions', 'INTEGER DEFAULT 0'),
                    ('correct_count', 'INTEGER DEFAULT 0')
                ]:
                    try:
                        cursor.execute(f'ALTER TABLE exam_sessions ADD COLUMN {column_name} {column_def}')
                    except sqlite3.OperationalError:
                        pass
                
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS exam_answers (
                        id TEXT PRIMARY KEY,
                        session_id TEXT,
                        question_id TEXT,
                        user_answer TEXT,
                        correct_answer TEXT,
                        is_correct BOOLEAN,
                        answered_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        time_spent INTEGER DEFAULT 0
                    )
                ''')
                
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS ai_feedback (
                        id TEXT PRIMARY KEY,
                        user_id TEXT,
                        exam_id TEXT,
                        session_id TEXT,
                        feedback_type TEXT,
                        content TEXT,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        read_at TEXT
                    )
                ''')
                
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_ai_q_exam_id ON ai_generated_questions(exam_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_exam_sessions_user_id ON exam_sessions(user_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_exam_sessions_exam_id ON exam_sessions(exam_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_answers_session_id ON exam_answers(session_id)')
                
                conn.commit()
                logger.info("考试系统数据库表初始化成功")
        except Exception as e:
            logger.error(f"初始化考试系统数据库表失败: {str(e)}")
    
    def generate_exam_questions(self, exam_id: str) -> Dict[str, Any]:
        """为考试生成完整题目"""
        try:
            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM exams WHERE id = ?', (exam_id,))
                exam = cursor.fetchone()
            
            if exam:
                exam_dict = dict(exam)
                questions = self._generate_questions_for_exam(exam_dict)
                return {"success": True, "questions": questions, "exam_info": exam_dict}
            else:
                questions = self._generate_questions_for_exam({})
                return {"success": True, "questions": questions, "exam_info": {"id": exam_id, "name": "默认考试"}}
        
        except Exception as e:
            logger.error(f"生成题目失败: {str(e)}")
            questions = self._generate_questions_for_exam({})
            return {"success": True, "questions": questions, "exam_info": {"id": exam_id, "name": "默认考试"}}
    
    def _generate_questions_for_exam(self, exam_info: Dict) -> List[Dict]:
        """根据考试信息生成题目"""
        questions = []
        try:
            question_count = exam_info.get('question_count', 20)
            subject = exam_info.get('subject', 'math')
            difficulty = exam_info.get('difficulty', 'medium')
            question_types = exam_info.get('question_types', ['single_choice'])
            
            for _ in range(question_count):
                q_type = random.choice(question_types)
                question = self._generate_single_question(subject, difficulty, q_type)
                if question:
                    questions.append(question)
            
            return questions
        except Exception as e:
            logger.error(f"生成题目失败: {str(e)}")
            return []
    
    def _generate_single_question(self, subject: str, difficulty: str, q_type: str) -> Optional[Dict]:
        """生成单个题目"""
        try:
            if hasattr(self.question_generator, 'generate'):
                question = self.question_generator.generate(subject, difficulty, q_type)
            else:
                question = self._create_default_question(subject, difficulty, q_type)
            
            return question
        except Exception as e:
            logger.error(f"生成单个题目失败: {str(e)}")
            return self._create_default_question(subject, difficulty, q_type)
    
    def _create_default_question(self, subject: str, difficulty: str, q_type: str) -> Dict:
        """创建默认题目"""
        subjects = {
            'math': '数学',
            'chinese': '语文',
            'english': '英语',
            'physics': '物理',
            'chemistry': '化学',
            'japanese': '日语'
        }
        
        questions = {

            'math': [
                {"content": f"{subjects[subject]}题目:计算 2 + 3 = ?", "options": ["A. 4", "B. 5", "C. 6", "D. 7"], "correct_answer": "B"},
                {"content": f"{subjects[subject]}题目:计算 10 × 5 = ?", "options": ["A. 40", "B. 50", "C. 60", "D. 55"], "correct_answer": "B"},
                {"content": f"{subjects[subject]}题目:计算 100 ÷ 4 = ?", "options": ["A. 25", "B. 20", "C. 30", "D. 15"], "correct_answer": "A"}
            ],
            'chinese': [
                {"content": f"{subjects[subject]}题目:下列哪个是正确的成语?", "options": ["A. 马到成功", "B. 马道成功", "C. 马到城功", "D. 马到乘功"], "correct_answer": "A"},
                {"content": f"{subjects[subject]}题目:\"床前明月光\"的作者是?", "options": ["A. 杜甫", "B. 李白", "C. 白居易", "D. 王维"], "correct_answer": "B"}
            ],
            'english': [
                {"content": f"{subjects[subject]}题目:What is the capital of China?", "options": ["A. Shanghai", "B. Beijing", "C. Guangzhou", "D. Shenzhen"], "correct_answer": "B"},
                {"content": f"{subjects[subject]}题目:Choose the correct form: He ___ to school every day.", "options": ["A. go", "B. goes", "C. going", "D. went"], "correct_answer": "B"}
            ],
            'japanese': [
                {"content": f"{subjects[subject]}题目:「こんにちは」の意味は?", "options": ["A. さようなら", "B. こんばんは", "C. 你好", "D. ありがとう"], "correct_answer": "C"},
                {"content": f"{subjects[subject]}题目:「私は学生です」の正しい訳は?", "options": ["A. I am a teacher", "B. I am a student", "C. You are a student", "D. He is a student"], "correct_answer": "B"}
            ]
        }
        
        q_list = questions.get(subject, questions['math'])
        return random.choice(q_list)
    
    def start_exam_session(self, exam_id: str, user_id: str) -> Dict[str, Any]:
        """开始考试会话"""
        try:
            session_id = f"SES_{uuid.uuid4().hex[:12]}"
            
            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO exam_sessions (id, exam_id, user_id, status, start_time)
                    VALUES (?, ?, ?, 'in_progress', ?)
                ''', (session_id, exam_id, user_id, datetime.now().isoformat()))
                
                conn.commit()
            
            questions_result = self.generate_exam_questions(exam_id)
            
            if not questions_result.get('success'):
                return {"success": False, "message": questions_result.get("message", "获取题目失败")}
            
            questions = questions_result.get('questions', [])
            
            return {
                "success": True,
                "session_id": session_id,
                "exam_id": exam_id,
                "user_id": user_id,
                "questions": questions,
                "total_questions": len(questions),
                "start_time": datetime.now().isoformat(),
                "message": "考试会话已开始"
            }
        
        except Exception as e:
            logger.error(f"开始考试会话失败: {str(e)}")
            return {"success": False, "message": f"开始考试失败: {str(e)}"}
    
    def submit_exam_answer(self, session_id: str, question_id: str, user_answer: str, correct_answer: str = None) -> Dict[str, Any]:
        """提交答题"""
        try:
            is_correct = False
            if correct_answer:
                is_correct = (user_answer == correct_answer)
            
            answer_id = f"ANS_{uuid.uuid4().hex[:12]}"
            
            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO exam_answers (id, session_id, question_id, user_answer, correct_answer, is_correct, answered_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (answer_id, session_id, question_id, user_answer, correct_answer, is_correct, datetime.now().isoformat()))
                
                conn.commit()
            
            return {
                "success": True,
                "session_id": session_id,
                "question_id": question_id,
                "is_correct": is_correct,
                "message": "答案已提交"
            }
        
        except Exception as e:
            logger.error(f"提交答案失败: {str(e)}")
            return {"success": False, "message": f"提交答案失败: {str(e)}"}
    
    def finish_exam_session(self, session_id: str) -> Dict[str, Any]:
        """结束考试并获取AI分析"""
        try:
            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('SELECT * FROM exam_sessions WHERE id = ?', (session_id,))
                session = cursor.fetchone()
                
                if not session:
                    return {"success": False, "message": "会话不存在"}
                
                cursor.execute('SELECT * FROM exam_answers WHERE session_id = ?', (session_id,))
                answers = cursor.fetchall()
                
                cursor.execute('UPDATE exam_sessions SET status = ?, end_time = ? WHERE id = ?',
                            ('completed', datetime.now().isoformat(), session_id))
                
                conn.commit()
            
            exam_id = session['exam_id'] if isinstance(session, dict) else session[1]
            user_id = session['user_id'] if isinstance(session, dict) else session[2]
            
            correct_count = 0
            for ans in answers:
                if isinstance(ans, dict):
                    correct_count += 1 if ans.get('is_correct', False) else 0
                else:
                    correct_count += 1 if (len(ans) > 5 and ans[5]) else 0
            
            total_count = len(answers) if answers else 1
            score = round((correct_count / total_count) * 100, 2) if total_count > 0 else 0
            
            ai_analysis = self._generate_ai_analysis(session_id, answers, score, exam_id, user_id)
            
            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE exam_sessions SET score = ?, ai_analysis = ?, correct_count = ?, total_questions = ?
                    WHERE id = ?
                ''', (score, ai_analysis, correct_count, total_count, session_id))
                conn.commit()
            
            return {
                "success": True,
                "session_id": session_id,
                "score": score,
                "correct_count": correct_count,
                "total_count": total_count,
                "ai_analysis": ai_analysis,
                "message": "考试已结束"
            }
        
        except Exception as e:
            logger.error(f"结束考试失败: {str(e)}")
            return {"success": False, "message": f"结束考试失败: {str(e)}"}
    
    def _generate_ai_analysis(self, session_id: str, answers: List, score: float, exam_id: str, user_id: str) -> str:
        """生成AI分析报告"""
        try:
            analysis = self._generate_default_analysis(score, answers)
            return json.dumps(analysis, ensure_ascii=False)
        except Exception as e:
            logger.error(f"生成AI分析失败: {str(e)}")
            return json.dumps(self._generate_default_analysis(score, answers), ensure_ascii=False)
    
    def _generate_default_analysis(self, score: float, answers: List) -> Dict:
        """生成默认分析报告"""
        if score >= 90:
            level = "优秀"
            suggestion = "表现出色!继续保持,可以尝试更具挑战性的题目."
        elif score >= 80:
            level = "良好"
            suggestion = "表现不错!还有提升空间,建议复习错题."
        elif score >= 60:
            level = "及格"
            suggestion = "刚刚及格,建议加强练习,重点复习薄弱知识点."
        else:
            level = "需努力"
            suggestion = "需要更多练习,建议从基础开始复习."
        
        wrong_questions = []
        for ans in answers:
            if isinstance(ans, dict):
                is_correct = ans.get('is_correct', False)
            else:
                is_correct = ans[5] if len(ans) > 5 else False
            if not is_correct:
                wrong_questions.append(ans)
        
        return {
            "overall_level": level,
            "score": score,
            "suggestion": suggestion,
            "wrong_count": len(wrong_questions),
            "total_questions": len(answers),
            "analysis_time": datetime.now().isoformat(),
            "improvement_areas": self._identify_improvement_areas(wrong_questions)
        }
    
    def _identify_improvement_areas(self, wrong_questions: List) -> List[str]:
        """识别需要改进的领域"""
        if not wrong_questions:
            return ["继续保持,暂无需要特别改进的领域"]
        
        return [
            "建议复习基础概念",
            "加强练习提高准确率",
            "注意审题细节",
            "提高答题速度"
        ]
    
    def get_exam_history(self, user_id: str, limit: int = 10) -> List[Dict]:
        """获取用户考试历史"""
        try:
            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT * FROM exam_sessions 
                    WHERE user_id = ? AND status = 'completed'
                    ORDER BY end_time DESC LIMIT ?
                ''', (user_id, limit))
                
                sessions = cursor.fetchall()
            
            return [dict(session) for session in sessions]
        except Exception as e:
            logger.error(f"获取考试历史失败: {str(e)}")
            return []


exam_system_integrator = ExamSystemIntegrator()
