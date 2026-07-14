# -*- coding: utf-8 -*-
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能教师AI模块
提供错题分析、个性化反馈、学习建议等功能
"""

import sqlite3
from contextlib import contextmanager
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

    @contextmanager
    def get_db_connection(self):
        """获取数据库连接"""
        conn = sqlite3.connect(DATABASE_PATH)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def analyze_exam_result(self, exam_session_id: int) -> Dict[str, Any]:
        """分析考试结果"""
        try:
            with self.get_db_connection() as conn:
                cursor = conn.cursor()

                cursor.execute('SELECT * FROM exam_sessions WHERE id = ?', (exam_session_id,))
                session = cursor.fetchone()

                if not session:
                    return {'success': False, 'message': '考试会话不存在'}

                cursor.execute('''
                    SELECT q.*, ua.selected_answer, ua.is_correct, ua.time_spent
                    FROM user_answers ua
                    JOIN questions q ON ua.question_id = q.id
                    WHERE ua.exam_session_id = ?
                ''', (exam_session_id,))
                answers = cursor.fetchall()

                total_questions = len(answers)
                correct_answers = sum(1 for a in answers if a['is_correct'])
                accuracy = correct_answers / total_questions if total_questions > 0 else 0

                wrong_answers = [a for a in answers if not a['is_correct']]

                weak_points = self._analyze_weak_points(wrong_answers)

                recommendations = self._generate_recommendations(weak_points, accuracy)

                return {
                    'success': True,
                    'exam_session_id': exam_session_id,
                    'total_questions': total_questions,
                    'correct_answers': correct_answers,
                    'accuracy': accuracy,
                    'weak_points': weak_points,
                    'recommendations': recommendations
                }

        except Exception as e:
            logger.error(f"分析考试结果失败: {str(e)}")
            return {'success': False, 'message': f'分析失败: {str(e)}'}

    def _analyze_weak_points(self, wrong_answers: List[Any]) -> List[Dict[str, Any]]:
        """分析薄弱点"""
        weak_points = []
        topic_errors = {}

        for answer in wrong_answers:
            topic = answer.get('topic', 'unknown')
            if topic not in topic_errors:
                topic_errors[topic] = {'count': 0, 'questions': []}
            topic_errors[topic]['count'] += 1
            topic_errors[topic]['questions'].append({
                'question_id': answer['id'],
                'content': answer.get('content', ''),
                'selected_answer': answer['selected_answer'],
                'correct_answer': answer.get('correct_answer', '')
            })

        for topic, data in sorted(topic_errors.items(), key=lambda x: x[1]['count'], reverse=True):
            weak_points.append({
                'topic': topic,
                'error_count': data['count'],
                'questions': data['questions'][:5]
            })

        return weak_points

    def _generate_recommendations(self, weak_points: List[Dict[str, Any]], accuracy: float) -> List[Dict[str, Any]]:
        """生成学习建议"""
        recommendations = []

        if accuracy < 0.6:
            recommendations.append({
                'type': 'general',
                'priority': 'high',
                'content': '建议加强基础知识学习,多做练习题巩固基础概念'
            })
        elif accuracy < 0.8:
            recommendations.append({
                'type': 'general',
                'priority': 'medium',
                'content': '表现良好,建议针对错题进行专项练习'
            })
        else:
            recommendations.append({
                'type': 'general',
                'priority': 'low',
                'content': '表现优秀,继续保持并尝试更高难度的题目'
            })

        for wp in weak_points[:3]:
            recommendations.append({
                'type': 'topic_specific',
                'priority': 'high' if wp['error_count'] > 3 else 'medium',
                'topic': wp['topic'],
                'content': f"建议重点复习 {wp['topic']} 相关知识点"
            })

        return recommendations

    def get_personalized_questions(self, user_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """获取个性化推荐题目"""
        try:
            with self.get_db_connection() as conn:
                cursor = conn.cursor()

                cursor.execute('''
                    SELECT topic, COUNT(*) as error_count
                    FROM user_answers ua
                    JOIN questions q ON ua.question_id = q.id
                    WHERE ua.user_id = ? AND ua.is_correct = 0
                    GROUP BY topic
                    ORDER BY error_count DESC
                    LIMIT 3
                ''', (user_id,))
                weak_topics = [row['topic'] for row in cursor.fetchall()]

                if not weak_topics:
                    cursor.execute('''
                        SELECT * FROM questions
                        ORDER BY RANDOM()
                        LIMIT ?
                    ''', (limit,))
                else:
                    placeholders = ','.join(['?' for _ in weak_topics])
                    cursor.execute(f'''
                        SELECT * FROM questions
                        WHERE topic IN ({placeholders})
                        ORDER BY RANDOM()
                        LIMIT ?
                    ''', weak_topics + [limit])

                questions = [dict(row) for row in cursor.fetchall()]
                return questions

        except Exception as e:
            logger.error(f"获取个性化题目失败: {str(e)}")
            return []

    def generate_study_plan(self, user_id: int, days: int = 7) -> Dict[str, Any]:
        """生成学习计划"""
        try:
            with self.get_db_connection() as conn:
                cursor = conn.cursor()

                cursor.execute('''
                    SELECT topic, COUNT(*) as error_count
                    FROM user_answers ua
                    JOIN questions q ON ua.question_id = q.id
                    WHERE ua.user_id = ? AND ua.is_correct = 0
                    GROUP BY topic
                    ORDER BY error_count DESC
                ''', (user_id,))
                weak_topics = cursor.fetchall()

                daily_plans = []
                questions_per_day = max(10, len(weak_topics) * 5)

                for day in range(days):
                    daily_plan = {
                        'day': day + 1,
                        'date': (datetime.now() + timedelta(days=day)).strftime('%Y-%m-%d'),
                        'topics': [],
                        'questions_count': questions_per_day
                    }

                    for i, topic in enumerate(weak_topics):
                        if i < 2:
                            daily_plan['topics'].append({
                                'topic': topic['topic'],
                                'priority': 'high' if i == 0 else 'medium',
                                'suggested_questions': max(5, topic['error_count'])
                            })

                    daily_plans.append(daily_plan)

                return {
                    'success': True,
                    'user_id': user_id,
                    'total_days': days,
                    'daily_plans': daily_plans
                }

        except Exception as e:
            logger.error(f"生成学习计划失败: {str(e)}")
            return {'success': False, 'message': f'生成失败: {str(e)}'}

    def provide_feedback(self, question_id: int, user_answer: str, is_correct: bool) -> Dict[str, Any]:
        """提供答题反馈"""
        try:
            with self.get_db_connection() as conn:
                cursor = conn.cursor()

                cursor.execute('SELECT * FROM questions WHERE id = ?', (question_id,))
                question = cursor.fetchone()

                if not question:
                    return {'success': False, 'message': '题目不存在'}

                if is_correct:
                    feedback = {
                        'type': 'positive',
                        'message': '回答正确!继续保持!',
                        'explanation': question.get('explanation', '')
                    }
                else:
                    feedback = {
                        'type': 'constructive',
                        'message': '回答错误,让我们来分析一下',
                        'correct_answer': question.get('correct_answer', ''),
                        'explanation': question.get('explanation', ''),
                        'hint': question.get('hint', '')
                    }

                return {
                    'success': True,
                    'question_id': question_id,
                    'is_correct': is_correct,
                    'feedback': feedback
                }

        except Exception as e:
            logger.error(f"提供反馈失败: {str(e)}")
            return {'success': False, 'message': f'反馈失败: {str(e)}'}


from datetime import timedelta
import logging
