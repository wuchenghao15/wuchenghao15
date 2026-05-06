#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
考试系统整合AI管理器
整合专家AI、老师AI、题库AI等，实现完整的智能考试系统
"""
import random
import sqlite3
from datetime import datetime
from typing import Dict, List, Any, Optional
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app.ai.exam_expert_ai import ExamExpertAI
from app.ai.question_generator import question_generator
from app.ai.exam_expert_generator import enhanced_exam_generator
from app.ai.narrow_road_question_bank import narrow_road_question_bank
from app.ai.teacher_ai import teacher_ai_map
from app.utils.logging import logger

DATABASE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'app.db')

class ExamSystemIntegrator:
    """考试系统整合AI管理器"""
    
    def __init__(self):
        self.exam_expert_ai = ExamExpertAI()
        self.question_generator = question_generator
        self.question_bank = narrow_road_question_bank
        self.teacher_ai_map = teacher_ai_map
        
        self.init_database()
        logger.info("考试系统整合AI管理器初始化成功")
    
    def init_database(self):
        """初始化数据库表结构"""
        try:
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()
            
            # AI生成题目记录
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ai_generated_questions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    exam_id INTEGER,
                    question_type TEXT,
                    language TEXT,
                    difficulty TEXT,
                    content TEXT,
                    options TEXT,
                    correct_answer TEXT,
                    explanation TEXT,
                    generated_by TEXT,
                    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    used_count INTEGER DEFAULT 0
                )
            ''')
            
            # 考试会话
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS exam_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    exam_id INTEGER,
                    user_id INTEGER,
                    start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    end_time TIMESTAMP,
                    status TEXT DEFAULT 'in_progress',
                    score REAL,
                    ai_analysis TEXT
                )
            ''')
            
            # 答题记录
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS exam_answers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id INTEGER,
                    question_id INTEGER,
                    user_answer TEXT,
                    correct_answer TEXT,
                    is_correct BOOLEAN,
                    answered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # AI反馈记录
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ai_feedback (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    exam_id INTEGER,
                    feedback_type TEXT,
                    content TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    read_at TIMESTAMP
                )
            ')
            
            # 创建索引
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_ai_q_exam_id ON ai_generated_questions(exam_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_exam_sessions_user_id ON exam_sessions(user_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_answers_session_id ON exam_answers(session_id)')
            
            conn.commit()
            conn.close()
            logger.info("AI相关数据库表初始化成功")
        except Exception as e:
            logger.error(f"初始化AI数据库表失败: {str(e)}")
    
    def generate_exam_questions(self, exam_id: int) -> Dict[str, Any]:
        """为考试生成完整题目"""
        try:
            conn = sqlite3.connect(DATABASE_PATH)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM t_a4394fa841fb07b4 WHERE id = ?', (exam_id,))
            exam = cursor.fetchone()
            conn.close()
            
            if not exam:
                return {"success": False, "message": "考试不存在"}
            
            language = exam['language'] or '日语'
            difficulty = exam['difficulty_level'] or '中级'
            exam_type = exam['exam_type'] or 'standard'
            total_questions = exam['total_questions'] or 10
            
            questions = enhanced_exam_generator.generate_questions(
            language=language,
            difficulty=difficulty,
            exam_type=exam_type,
            question_count=total_questions
        )
            
            # 保存AI生成的题目
            self._save_ai_generated_questions(exam_id, questions)
            
            return {
                "success": True,
                "questions": questions,
                "exam_info": {
                    "name": exam['name'],
                    "language": language,
                    "difficulty": difficulty,
                    "total_questions": len(questions)
                }
            }
        except Exception as e:
            logger.error(f"生成考试题目失败: {str(e)}")
            return {"success": False, "message": f"生成题目失败: {str(e)}"}
    
    def _save_ai_generated_questions(self, exam_id: int, questions: List[Dict]):
        """保存AI生成的题目"""
        try:
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()
            
            for q in questions:
                cursor.execute('''
                    INSERT INTO ai_generated_questions 
                    (exam_id, question_type, language, content, options, correct_answer, explanation, generated_by)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    exam_id,
                    q.get('type', '单选题'),
                    q.get('language', '未知'),
                    q.get('content', ''),
                    str(q.get('options', [])),
                    q.get('correct_answer', ''),
                    q.get('explanation', ''),
                    'ExamExpertAI'
                ))
            
            conn.commit()
            conn.close()
            logger.info(f"保存了 {len(questions)} 道AI生成的题目")
        except Exception as e:
            logger.error(f"保存AI生成题目失败: {str(e)}")
    
    def start_exam_session(self, exam_id: int, user_id: int) -> Dict[str, Any]:
        """开始考试会话"""
        try:
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO exam_sessions (exam_id, user_id, status)
                VALUES (?, ?, 'in_progress')
            ''', (exam_id, user_id))
            
            session_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            questions_result = self.generate_exam_questions(exam_id)
            
            return {
                "success": True,
                "session_id": session_id,
                "questions": questions_result.get('questions', []),
                "exam_info": questions_result.get('exam_info', {})
            }
        except Exception as e:
            logger.error(f"开始考试会话失败: {str(e)}")
            return {"success": False, "message": f"开始考试失败: {str(e)}"}
    
    def submit_exam_answer(self, session_id: int, question_id: int, 
                          user_answer: str, correct_answer: str) -> Dict[str, Any]:
        """提交答题"""
        try:
            is_correct = (user_answer == correct_answer)
            
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO exam_answers (session_id, question_id, user_answer, correct_answer, is_correct)
                VALUES (?, ?, ?, ?, ?)
            ''', (session_id, question_id, user_answer, correct_answer, is_correct))
            
            conn.commit()
            conn.close()
            
            return {"success": True, "is_correct": is_correct}
        except Exception as e:
            logger.error(f"提交答题失败: {str(e)}")
            return {"success": False, "message": f"提交答案失败: {str(e)}"}
    
    def finish_exam_session(self, session_id: int) -> Dict[str, Any]:
        """结束考试会话并进行AI分析"""
        try:
            conn = sqlite3.connect(DATABASE_PATH)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # 获取答题记录
            cursor.execute('SELECT * FROM exam_answers WHERE session_id = ?', (session_id,))
            answers = cursor.fetchall()
            
            total = len(answers)
            correct = sum(1 for a in answers if a['is_correct'])
            score = (correct / total * 100) if total > 0 else 0
            
            cursor.execute('''
                UPDATE exam_sessions 
                SET end_time = CURRENT_TIMESTAMP, status = 'completed', score = ?
                WHERE id = ?
            ''', (score, session_id))
            
            # 生成AI分析
            ai_analysis = self._generate_ai_analysis(session_id, answers, score)
            
            cursor.execute('''
                UPDATE exam_sessions 
                SET ai_analysis = ?
                WHERE id = ?
            ''', (str(ai_analysis), session_id))
            
            conn.commit()
            conn.close()
            
            return {
                "success": True,
                "session_id": session_id,
                "score": score,
                "correct_count": correct,
                "total_count": total,
                "ai_analysis": ai_analysis
            }
        except Exception as e:
            logger.error(f"结束考试会话失败: {str(e)}")
            return {"success": False, "message": f"结束考试失败: {str(e)}"}
    
    def _generate_ai_analysis(self, session_id: int, answers: List, score: float) -> Dict:
        """生成AI分析报告"""
        analysis = {
            "overall_score": score,
            "performance_level": self._get_performance_level(score),
            "strengths": [],
            "weaknesses": [],
            "suggestions": [],
            "next_steps": []
        }
        
        # 分析强弱项
        if score >= 80:
            analysis["strengths"] = ["整体表现优秀", "知识点掌握较好", "答题速度稳定"]
            analysis["suggestions"] = ["保持现有状态", "挑战更高难度", "尝试拓展学习"]
        elif score >= 60:
            analysis["strengths"] = ["有一定基础", "理解基本概念"]
            analysis["weaknesses"] = ["部分知识点不牢固", "需要更多练习"]
            analysis["suggestions"] = ["重点复习错题", "加强薄弱环节", "多做相关练习"]
        else:
            analysis["weaknesses"] = ["基础较薄弱", "知识点掌握不全面", "需要系统学习"]
            analysis["suggestions"] = ["从基础开始复习", "制定学习计划", "寻求AI老师辅导"]
        
        analysis["next_steps"] = [
            "查看AI老师详细反馈",
            "复习错题本",
            "进行针对性练习",
            "参加下一次考试"
        ]
        
        return analysis
    
    def _get_performance_level(self, score: float) -> str:
        """获取表现等级"""
        if score >= 90:
            return "优秀"
        elif score >= 80:
            return "良好"
        elif score >= 70:
            return "中等"
        elif score >= 60:
            return "及格"
        else:
            return "需要加强"
    
    def get_ai_teacher_feedback(self, user_id: int, exam_id: int, session_id: int) -> Dict:
        """获取AI老师的个性化反馈"""
        try:
            conn = sqlite3.connect(DATABASE_PATH)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM exam_sessions WHERE id = ?', (session_id,))
            session = cursor.fetchone()
            
            cursor.execute('SELECT * FROM t_a4394fa841fb07b4 WHERE id = ?', (exam_id,))
            exam = cursor.fetchone()
            
            conn.close()
            
            if not session or not exam:
                return {"success": False, "message": "数据不存在"}
            
            subject = self._map_language_to_subject(exam['language'])
            teacher_ai = self.teacher_ai_map.get(subject)
            
            if teacher_ai:
                feedback = {
                    "teacher_name": teacher_ai.name,
                    "subject": teacher_ai.subject,
                    "score": session['score'],
                    "feedback": self._generate_teacher_feedback(session, exam),
                    "strengths": [
                        f"在{exam['name']}中表现稳定",
                        "答题思路清晰"
                    ],
                    "improvement_points": [
                        "建议加强基础练习",
                        "注意细节问题"
                    ],
                    "resources": [
                        "复习教材相关章节",
                        "查看错题解析"
                    ]
                }
            else:
                feedback = {
                    "teacher_name": "通用AI老师",
                    "subject": "综合",
                    "score": session['score'],
                    "feedback": "继续努力！",
                    "strengths": [],
                    "improvement_points": [],
                    "resources": []
                }
            
            return {"success": True, "feedback": feedback}
        except Exception as e:
            logger.error(f"获取AI老师反馈失败: {str(e)}")
            return {"success": False, "message": f"获取反馈失败: {str(e)}"}
    
    def _map_language_to_subject(self, language: str) -> str:
        """将语言映射到科目"""
        if language == '日语':
            return 'english'
        elif language == '英语':
            return 'english'
        elif language == '中文':
            return 'math'
        else:
            return 'english'
    
    def _generate_teacher_feedback(self, session, exam) -> str:
        """生成个性化反馈内容"""
        score = session['score']
        feedback = f"你好！我是{exam['name']}的AI老师。\n\n"
        
        if score >= 80:
            feedback += "很好！这次考试你表现得非常出色，大部分题目都答对了。"
            feedback += "建议你保持这个状态，继续挑战更高难度的题目。"
        elif score >= 60:
            feedback += "还不错！这次考试你及格了，但还有提升的空间。"
            feedback += "建议你复习一下错题，巩固薄弱环节。"
        else:
            feedback += "别灰心！学习是个过程，这次考试说明你还需要更多练习。"
            feedback += "建议从基础开始，系统地复习相关知识点。"
        
        return feedback
    
    def get_user_exam_history(self, user_id: int) -> Dict:
        """获取用户考试历史"""
        try:
            conn = sqlite3.connect(DATABASE_PATH)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT es.*, e.name as exam_name 
                FROM exam_sessions es
                LEFT JOIN t_a4394fa841fb07b4 e ON es.exam_id = e.id
                WHERE es.user_id = ?
                ORDER BY es.start_time DESC
                LIMIT 20
            ''', (user_id,))
            
            sessions = []
            for row in cursor.fetchall():
                sessions.append({
                    "id": row['id'],
                    "exam_id": row['exam_id'],
                    "exam_name": row['exam_name'],
                    "score": row['score'],
                    "status": row['status'],
                    "start_time": row['start_time'],
                    "end_time": row['end_time']
                })
            
            conn.close()
            
            return {
                "success": True,
                "sessions": sessions,
                "total": len(sessions)
            }
        except Exception as e:
            logger.error(f"获取考试历史失败: {str(e)}")
            return {"success": False, "message": f"获取历史失败: {str(e)}"}

# 创建单例
exam_system_integrator = ExamSystemIntegrator()
