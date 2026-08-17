# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
专家AI分析服务
负责基于用户答题行为生成针对性的试卷
"""

import logging
logger = logging.getLogger(__name__)
import os
import sys
import sqlite3
from contextlib import contextmanager
import random
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class ExpertAIAnalysisService:
    """专家AI分析服务"""

    def __init__(self, db_path="app.db"):
        """初始化专家AI分析服务"""
        self.db_path = db_path
        self.conn = None
        self.cursor = None

        self.exam_config = {
            'weak_area_weight': 0.6,
            'strong_area_weight': 0.3,
            'challenge_weight': 0.1,
            'default_exam_size': 10,
            'max_weak_area_questions': 8,
            'min_strong_area_questions': 2
        }

    def connect(self):
        """连接数据库"""
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.cursor = self.conn.cursor()
            return True
        except Exception as e:
            logger.error(f"连接数据库失败: {str(e)}")
            return False

    def close(self):
        """关闭数据库连接"""
        if self.conn:
            self.conn.close()
            self.conn = None
            self.cursor = None

    def analyze_user_performance(self, user_id):
        """分析用户表现

        Args:
            user_id: 用户ID

        Returns:
            用户表现分析结果
        """
        if not self.connect():
            return None

        try:
            sql = """
                SELECT eq.subject, eq.topic, eq.difficulty, er.is_correct, er.time_spent
                FROM exam_results er
                JOIN exam_questions eq ON er.question_id = eq.question_id
                WHERE er.user_id = ?
                ORDER BY er.created_at DESC
            """
            self.cursor.execute(sql, (user_id,))
            results = self.cursor.fetchall()

            if not results:
                return None

            subject_performance = defaultdict(lambda: {'total': 0, 'correct': 0, 'time_spent': 0})
            topic_performance = defaultdict(lambda: {'total': 0, 'correct': 0, 'time_spent': 0})
            difficulty_performance = defaultdict(lambda: {'total': 0, 'correct': 0})

            for subject, topic, difficulty, is_correct, time_spent in results:
                subject_performance[subject]['total'] += 1
                topic_performance[topic]['total'] += 1
                difficulty_performance[difficulty]['total'] += 1

                if is_correct:
                    subject_performance[subject]['correct'] += 1
                    topic_performance[topic]['correct'] += 1
                    difficulty_performance[difficulty]['correct'] += 1

                if time_spent:
                    subject_performance[subject]['time_spent'] += time_spent
                    topic_performance[topic]['time_spent'] += time_spent

            analysis = {
                'subject_performance': {},
                'topic_performance': {},
                'weak_areas': [],
                'strong_areas': [],
                'recommended_difficulty': 5
            }

            for subject, stats in subject_performance.items():
                accuracy = stats['correct'] / stats['total'] if stats['total'] > 0 else 0
                avg_time = stats['time_spent'] / stats['total'] if stats['total'] > 0 else 0
                analysis['subject_performance'][subject] = {
                    'accuracy': accuracy,
                    'total': stats['total'],
                    'correct': stats['correct'],
                    'average_time': avg_time
                }

            for topic, stats in topic_performance.items():
                accuracy = stats['correct'] / stats['total'] if stats['total'] > 0 else 0
                avg_time = stats['time_spent'] / stats['total'] if stats['total'] > 0 else 0
                analysis['topic_performance'][topic] = {
                    'accuracy': accuracy,
                    'total': stats['total'],
                    'correct': stats['correct'],
                    'average_time': avg_time
                }

                if accuracy < 0.5:
                    analysis['weak_areas'].append(topic)
                elif accuracy > 0.8:
                    analysis['strong_areas'].append(topic)

            return analysis

        except Exception as e:
            logger.error(f"分析用户表现失败: {str(e)}")
            return None
        finally:
            self.close()

    def generate_personalized_exam(self, user_id, subject=None, count=None):
        """生成个性化试卷"""
        if count is None:
            count = self.exam_config['default_exam_size']

        analysis = self.analyze_user_performance(user_id)
        if not analysis:
            return []

        questions = []

        weak_count = int(count * self.exam_config['weak_area_weight'])
        strong_count = int(count * self.exam_config['strong_area_weight'])
        challenge_count = count - weak_count - strong_count

        if analysis['weak_areas']:
            weak_questions = self._get_weak_area_questions(
                user_id, analysis['weak_areas'], weak_count, subject
            )
            questions.extend(weak_questions)

        if analysis['strong_areas']:
            strong_questions = self._get_strong_area_questions(
                user_id, analysis['strong_areas'], strong_count, subject
            )
            questions.extend(strong_questions)

        challenge_questions = self._get_challenge_questions(user_id, challenge_count, subject)
        questions.extend(challenge_questions)

        random.shuffle(questions)
        return questions[:count]

    def _get_weak_area_questions(self, user_id, weak_areas, count, subject):
        """获取薄弱环节题目"""
        if not self.connect():
            return []

        try:
            placeholders = ','.join(['?' for _ in weak_areas])
            sql = f'''
                SELECT * FROM exam_questions 
                WHERE topic IN ({placeholders})
            '''
            params = list(weak_areas)

            if subject:
                sql += ' AND subject = ?'
                params.append(subject)

            sql += ' ORDER BY RANDOM() LIMIT ?'
            params.append(count)

            self.cursor.execute(sql, params)
            columns = [description[0] for description in cursor.description]
            return [dict(zip(columns, row)) for row in self.cursor.fetchall()]
        except Exception as e:
            logger.error(f"获取薄弱环节题目失败: {str(e)}")
            return []
        finally:
            self.close()

    def _get_strong_area_questions(self, user_id, strong_areas, count, subject):
        """获取优势环节题目"""
        if not self.connect():
            return []

        try:
            placeholders = ','.join(['?' for _ in strong_areas])
            sql = f'''
                SELECT * FROM exam_questions 
                WHERE topic IN ({placeholders}) AND difficulty >= 6
            '''
            params = list(strong_areas)

            if subject:
                sql += ' AND subject = ?'
                params.append(subject)

            sql += ' ORDER BY RANDOM() LIMIT ?'
            params.append(count)

            self.cursor.execute(sql, params)
            columns = [description[0] for description in cursor.description]
            return [dict(zip(columns, row)) for row in self.cursor.fetchall()]
        except Exception as e:
            logger.error(f"获取优势环节题目失败: {str(e)}")
            return []
        finally:
            self.close()

    def _get_challenge_questions(self, user_id, count, subject):
        """获取挑战题目"""
        if not self.connect():
            return []

        try:
            sql = '''
                SELECT * FROM exam_questions 
                WHERE difficulty >= 7
            '''
            params = []

            if subject:
                sql += ' AND subject = ?'
                params.append(subject)

            sql += ' ORDER BY RANDOM() LIMIT ?'
            params.append(count)

            self.cursor.execute(sql, params)
            columns = [description[0] for description in cursor.description]
            return [dict(zip(columns, row)) for row in self.cursor.fetchall()]
        except Exception as e:
            logger.error(f"获取挑战题目失败: {str(e)}")
            return []
        finally:
            self.close()

    def generate_analysis_report(self, user_id, exam_id):
        """生成分析报告

        Args:
            user_id: 用户ID
            exam_id: 考试ID

        Returns:
            分析报告
        """
        if not self.connect():
            return None

        try:
            sql = """
                SELECT er.question_id, er.is_correct, er.time_spent, er.answer,
                       eq.question_type, eq.level_id, eq.subject, eq.topic
                FROM exam_results er
                JOIN exam_questions eq ON er.question_id = eq.question_id
                WHERE er.user_id = ? AND er.exam_id = ?
                ORDER BY er.created_at DESC
            """
            self.cursor.execute(sql, (user_id, exam_id))
            results = self.cursor.fetchall()

            if not results:
                return None

            total_questions = len(results)
            correct_answers = sum(1 for r in results if r[1])
            total_time = sum(r[2] or 0 for r in results)

            accuracy = correct_answers / total_questions if total_questions > 0 else 0
            avg_time_per_question = total_time / total_questions if total_questions > 0 else 0

            question_type_performance = defaultdict(lambda: {'total': 0, 'correct': 0, 'time_spent': 0})
            level_performance = defaultdict(lambda: {'total': 0, 'correct': 0, 'time_spent': 0})

            for row in results:
                question_id, is_correct, time_spent, answer, question_type, level_id, subject, topic = row

                question_type_performance[question_type]['total'] += 1
                level_performance[level_id]['total'] += 1

                if is_correct:
                    question_type_performance[question_type]['correct'] += 1
                    level_performance[level_id]['correct'] += 1

                if time_spent:
                    question_type_performance[question_type]['time_spent'] += time_spent
                    level_performance[level_id]['time_spent'] += time_spent

            weak_types = []
            strong_types = []

            for q_type, stats in question_type_performance.items():
                type_accuracy = stats['correct'] / stats['total'] if stats['total'] > 0 else 0
                avg_type_time = stats['time_spent'] / stats['total'] if stats['total'] > 0 else 0

                type_info = {
                    'question_type': q_type,
                    'accuracy': type_accuracy,
                    'total': stats['total'],
                    'correct': stats['correct'],
                    'average_time': avg_type_time
                }

                if type_accuracy < 0.6:
                    weak_types.append(type_info)
                elif type_accuracy > 0.8:
                    strong_types.append(type_info)

            weak_types.sort(key=lambda x: x['accuracy'])
            strong_types.sort(key=lambda x: x['accuracy'], reverse=True)

            difficulty_level = '中等'
            if accuracy < 0.4:
                difficulty_level = '需要加强'
            elif accuracy > 0.8:
                difficulty_level = '掌握良好'

            report = {
                'user_id': user_id,
                'exam_id': exam_id,
                'total_questions': total_questions,
                'correct_answers': correct_answers,
                'accuracy': accuracy,
                'total_time': total_time,
                'average_time_per_question': avg_time_per_question,
                'difficulty_level': difficulty_level,
                'question_type_performance': dict(question_type_performance),
                'level_performance': dict(level_performance),
                'weak_types': weak_types,
                'strong_types': strong_types,
                'recommendations': []
            }

            if weak_types:
                report['recommendations'].append(f'建议加强 {weak_types[0]["question_type"]} 题型的练习')

            if accuracy < 0.6:
                report['recommendations'].append('建议多做基础练习, 巩固知识点')
            elif accuracy > 0.8:
                report['recommendations'].append('表现优秀, 可以尝试更高难度的题目')

            if avg_time_per_question > 60:
                report['recommendations'].append('答题速度较慢, 建议提高解题速度')

            return report

        except Exception as e:
            logger.error(f"生成分析报告失败: {str(e)}")
            return None
        finally:
            self.close()


expert_ai_analysis_service = ExpertAIAnalysisService()
