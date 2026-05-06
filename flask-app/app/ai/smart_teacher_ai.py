#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能教师AI模块
提供错题分析、个性化反馈、学习建议等功能
"""
import sqlite3
import os
from typing import List, Dict, Any
from datetime import datetime
from app.utils.logging import logger

DATABASE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'app.db')

class SmartTeacherAI:
    """智能教师AI"""
    
    def __init__(self):
        self.analysis_db = {}
        logger.info("智能教师AI初始化成功")
    
    def analyze_exam_result(self, exam_session_id: int) -> Dict[str, Any]:
        """分析考试结果"""
        try:
            conn = sqlite3.connect(DATABASE_PATH)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # 获取考试会话信息
            cursor.execute('SELECT * FROM exam_sessions WHERE id = ?', (exam_session_id,))
            session = cursor.fetchone()
            
            if not session:
                return {'success': False, 'message': '考试会话不存在'}
            
            # 获取答题详情
            cursor.execute('SELECT * FROM exam_answers WHERE session_id = ?', (exam_session_id,))
            answers = cursor.fetchall()
            
            conn.close()
            
            total = len(answers)
            correct = sum(1 for a in answers if a['is_correct'])
            score = (correct / total * 100) if total > 0 else 0
            
            # 详细分析
            analysis = {
                'overall_score': score,
                'correct_count': correct,
                'total_count': total,
                'accuracy_rate': score,
                'performance_level': self._get_performance_level(score),
                'strengths': self._identify_strengths(score),
                'weaknesses': self._identify_weaknesses(score, answers),
                'suggestions': self._generate_suggestions(score, total),
                'next_steps': self._generate_next_steps(score)
            }
            
            return {'success': True, 'analysis': analysis}
        except Exception as e:
            logger.error(f"分析考试结果失败: {str(e)}")
            return {'success': False, 'message': f'分析失败: {str(e)}'}
    
    def _get_performance_level(self, score: float) -> str:
        """获取表现等级"""
        if score >= 90:
            return '优秀'
        elif score >= 80:
            return '良好'
        elif score >= 70:
            return '中等'
        elif score >= 60:
            return '及格'
        else:
            return '需要加强'
    
    def _identify_strengths(self, score: float) -> List[str]:
        """识别强项"""
        strengths = []
        if score >= 80:
            strengths.extend([
                '基础知识掌握扎实',
                '答题思路清晰',
                '学习态度认真'
            ])
        elif score >= 60:
            strengths.extend([
                '有一定基础',
                '基本概念理解'
            ])
        else:
            strengths.extend([
                '有提升潜力',
                '需要建立学习基础'
            ])
        return strengths
    
    def _identify_weaknesses(self, score: float, answers: List) -> List[str]:
        """识别弱项"""
        weaknesses = []
        if score < 80:
            weaknesses.extend([
                '部分知识点掌握不牢固',
                '需要更多练习'
            ])
        if score < 60:
            weaknesses.extend([
                '基础较薄弱',
                '需要系统学习'
            ])
        return weaknesses
    
    def _generate_suggestions(self, score: float, total: int) -> List[str]:
        """生成建议"""
        suggestions = []
        
        if score >= 90:
            suggestions.extend([
                '保持现有状态',
                '挑战更高难度的题目',
                '尝试拓展学习'
            ])
        elif score >= 80:
            suggestions.extend([
                '复习错题，巩固知识点',
                '继续加强练习',
                '可以尝试更高难度'
            ])
        elif score >= 70:
            suggestions.extend([
                '重点复习错题',
                '加强薄弱环节',
                '增加练习量'
            ])
        elif score >= 60:
            suggestions.extend([
                '从基础开始复习',
                '制定学习计划',
                '多做相关练习'
            ])
        else:
            suggestions.extend([
                '从最基础开始',
                '制定详细学习计划',
                '每天坚持学习'
            ])
        
        return suggestions
    
    def _generate_next_steps(self, score: float) -> List[str]:
        """生成下一步计划"""
        return [
            '查看详细错题分析',
            '复习错题',
            '进行针对性练习',
            '参加下一次考试'
        ]
    
    def generate_personalized_feedback(self, user_id: int, exam_id: int, 
                                     session_id: int) -> Dict[str, Any]:
        """生成个性化反馈"""
        try:
            analysis_result = self.analyze_exam_result(session_id)
            
            if not analysis_result['success']:
                return analysis_result
            
            analysis = analysis_result['analysis']
            
            feedback = {
                'score': analysis['overall_score'],
                'performance_level': analysis['performance_level'],
                'feedback_message': self._generate_feedback_message(analysis),
                'strengths': analysis['strengths'],
                'weaknesses': analysis['weaknesses'],
                'suggestions': analysis['suggestions'],
                'next_steps': analysis['next_steps'],
                'generated_at': datetime.now().isoformat()
            }
            
            return {'success': True, 'feedback': feedback}
        except Exception as e:
            logger.error(f"生成个性化反馈失败: {str(e)}")
            return {'success': False, 'message': f'生成反馈失败: {str(e)}'}
    
    def _generate_feedback_message(self, analysis: Dict) -> str:
        """生成反馈信息"""
        score = analysis['overall_score']
        
        if score >= 90:
            return f"太棒了！你这次考了 {score:.1f} 分，表现非常优秀！继续保持这个势头！"
        elif score >= 80:
            return f"很好！你考了 {score:.1f} 分，表现良好！再加把劲就能更上一层楼！"
        elif score >= 70:
            return f"还不错！你考了 {score:.1f} 分，有一定基础！努力一下就能更好！"
        elif score >= 60:
            return f"刚好及格！你考了 {score:.1f} 分，加油！针对薄弱环节多下功夫！"
        else:
            return f"别灰心！你这次考了 {score:.1f} 分，这只是起点！让我们一起努力提高！"
    
    def analyze_error_patterns(self, user_id: int) -> Dict[str, Any]:
        """分析错误模式"""
        try:
            conn = sqlite3.connect(DATABASE_PATH)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT a.* FROM exam_answers a 
                INNER JOIN exam_sessions s ON a.session_id = s.id 
                WHERE s.user_id = ? AND a.is_correct = 0
                ORDER BY a.answered_at DESC
                LIMIT 50
            ''', (user_id,))
            recent_errors = cursor.fetchall()
            
            conn.close()
            
            error_analysis = {
                'total_errors': len(recent_errors),
                'common_patterns': ['需要加强练习', '注意细节问题'],
                'improvement_tips': ['复习错题', '多做练习', '总结规律']
            }
            
            return {'success': True, 'analysis': error_analysis}
        except Exception as e:
            logger.error(f"分析错误模式失败: {str(e)}")
            return {'success': False, 'message': f'分析失败: {str(e)}'}
    
    def generate_practice_questions(self, user_id: int, knowledge_point: str, 
                                  difficulty: str = 'medium') -> List[Dict]:
        """生成练习题目"""
        try:
            conn = sqlite3.connect(DATABASE_PATH)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM ai_generated_questions 
                WHERE difficulty = ? 
                LIMIT 10
            ''', (difficulty,))
            questions = cursor.fetchall()
            
            conn.close()
            
            practice_questions = []
            for q in questions:
                practice_questions.append({
                    'id': q['id'],
                    'type': q['question_type'] or '单选题',
                    'content': q['content'],
                    'correct_answer': q['correct_answer'],
                    'explanation': q['explanation']
                })
            
            return practice_questions
        except Exception as e:
            logger.error(f"生成练习题目失败: {str(e)}")
            return []

smart_teacher = SmartTeacherAI()
