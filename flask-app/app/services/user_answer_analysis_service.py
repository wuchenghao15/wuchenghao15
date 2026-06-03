# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
用户答题习惯分析服务
负责分析用户的答题历史,识别薄弱环节和错题题型
"""

import logging
logger = logging.getLogger(__name__)
import os
import sys
import sqlite3
from contextlib import contextmanager
from collections import defaultdict
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class UserAnswerAnalysisService:
    """用户答题习惯分析服务"""

    def __init__(self, db_path="app.db"):
        """初始化分析服务"""
        self.db_path = db_path
        self.conn = None
        self.cursor = None

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

    def analyze_user_weaknesses(self, user_id, limit=100):
        """
        分析用户的薄弱环节

        Args:
            user_id: 用户ID
            limit: 分析的最近答题记录数量

        Returns:
            薄弱环节分析结果
        """
        if not self.connect():
            return None

        try:
            sql = """
                SELECT q.question_type, q.level_id, e.is_correct, e.time_spent
                FROM exam_results e
                JOIN questions q ON e.question_id = q.id
                WHERE e.user_id = ?
                ORDER BY e.created_at DESC
                LIMIT ?
            """
            self.cursor.execute(sql, (user_id, limit))
            results = self.cursor.fetchall()

            type_stats = defaultdict(lambda: {'total': 0, 'correct': 0, 'time_spent': 0})
            level_stats = defaultdict(lambda: {'total': 0, 'correct': 0})

            for row in results:
                question_type, level_id, is_correct, time_spent = row
                type_stats[question_type]['total'] += 1
                if is_correct:
                    type_stats[question_type]['correct'] += 1
                if time_spent:
                    type_stats[question_type]['time_spent'] += time_spent

                level_stats[level_id]['total'] += 1
                if is_correct:
                    level_stats[level_id]['correct'] += 1

            weaknesses = []
            for q_type, stats in type_stats.items():
                accuracy = stats['correct'] / stats['total'] if stats['total'] > 0 else 0
                if accuracy < 0.7:
                    weaknesses.append({
                        'question_type': q_type,
                        'accuracy': accuracy,
                        'total': stats['total'],
                        'correct': stats['correct'],
                        'avg_time': stats['time_spent'] / stats['total'] if stats['total'] > 0 else 0
                    })

            level_weaknesses = []
            for level_id, stats in level_stats.items():
                accuracy = stats['correct'] / stats['total'] if stats['total'] > 0 else 0
                level_weaknesses.append({
                    'level_id': level_id,
                    'accuracy': accuracy,
                    'total': stats['total'],
                    'correct': stats['correct']
                })

            total_questions = sum(s['total'] for s in type_stats.values())
            total_correct = sum(s['correct'] for s in type_stats.values())
            overall_accuracy = total_correct / total_questions if total_questions > 0 else 0

            return {
                'weaknesses': sorted(weaknesses, key=lambda x: x['accuracy']),
                'level_weaknesses': sorted(level_weaknesses, key=lambda x: x['accuracy']),
                'overall_accuracy': overall_accuracy,
                'total_analyzed': total_questions
            }
        except Exception as e:
            logger.error(f"分析用户薄弱环节失败: {str(e)}")
            return None
        finally:
            self.close()

    def analyze_answer_patterns(self, user_id, days=30):
        """
        分析用户答题模式

        Args:
            user_id: 用户ID
            days: 分析最近多少天的答题记录

        Returns:
            答题模式分析结果
        """
        if not self.connect():
            return None

        try:
            sql = """
                SELECT e.created_at, q.question_type, q.level_id, e.is_correct, e.time_spent
                FROM exam_results e
                JOIN questions q ON e.question_id = q.id
                WHERE e.user_id = ? AND e.created_at >= datetime('now', '-' || ? || ' days')
            """
            self.cursor.execute(sql, (user_id, days))
            results = self.cursor.fetchall()

            daily_stats = defaultdict(lambda: {'total': 0, 'correct': 0, 'time_spent': 0})
            time_of_day_stats = defaultdict(lambda: {'total': 0, 'correct': 0})
            question_type_trend = defaultdict(list)
            level_trend = defaultdict(list)

            for row in results:
                created_at, question_type, level_id, is_correct, time_spent = row
                date = created_at.split(' ')[0] if created_at else None
                if date:
                    daily_stats[date]['total'] += 1
                    if is_correct:
                        daily_stats[date]['correct'] += 1
                    if time_spent:
                        daily_stats[date]['time_spent'] += time_spent

                    hour = int(created_at.split(' ')[1].split(':')[0])
                    time_slot = f"{hour:02d}:00-{hour+1:02d}:00"
                    time_of_day_stats[time_slot]['total'] += 1
                    if is_correct:
                        time_of_day_stats[time_slot]['correct'] += 1

                    question_type_trend[question_type].append({'date': date, 'correct': is_correct})
                    level_trend[level_id].append({'date': date, 'correct': is_correct})

            daily_accuracy = []
            for date, stats in sorted(daily_stats.items()):
                accuracy = stats['correct'] / stats['total'] if stats['total'] > 0 else 0
                avg_time = stats['time_spent'] / stats['total'] if stats['total'] > 0 else 0
                daily_accuracy.append({
                    'date': date,
                    'total': stats['total'],
                    'accuracy': accuracy,
                    'avg_time': avg_time
                })

            time_slot_accuracy = []
            for time_slot, stats in sorted(time_of_day_stats.items()):
                accuracy = stats['correct'] / stats['total'] if stats['total'] > 0 else 0
                time_slot_accuracy.append({
                    'time_slot': time_slot,
                    'total': stats['total'],
                    'correct': stats['correct'],
                    'accuracy': accuracy
                })

            best_time_slot = None
            best_accuracy = 0
            for item in time_slot_accuracy:
                if item['accuracy'] > best_accuracy and item['total'] >= 5:
                    best_accuracy = item['accuracy']
                    best_time_slot = item['time_slot']

            question_type_analysis = []
            for q_type, trends in question_type_trend.items():
                total = len(trends)
                correct = sum(1 for t in trends if t['correct'])
                accuracy = correct / total if total > 0 else 0

                recent_trends = trends[-7:] if len(trends) >= 7 else trends
                recent_correct = sum(1 for t in recent_trends if t['correct'])
                recent_accuracy = recent_correct / len(recent_trends) if recent_trends else 0

                if len(trends) >= 14:
                    older_accuracy = sum(1 for t in trends[:-7] if t['correct']) / len(trends[:-7])
                    trend = 'improving' if recent_accuracy > older_accuracy else 'declining'
                else:
                    trend = 'stable'

                question_type_analysis.append({
                    'question_type': q_type,
                    'total': total,
                    'correct': correct,
                    'accuracy': accuracy,
                    'recent_accuracy': recent_accuracy,
                    'trend': trend
                })

            level_analysis = []
            for level_id, trends in level_trend.items():
                total = len(trends)
                correct = sum(1 for t in trends if t['correct'])
                accuracy = correct / total if total > 0 else 0

                level_analysis.append({
                    'level_id': level_id,
                    'total': total,
                    'correct': correct,
                    'accuracy': accuracy
                })

            analysis = {
                'daily_accuracy': daily_accuracy,
                'time_slot_accuracy': time_slot_accuracy,
                'best_time_slot': best_time_slot,
                'question_type_analysis': question_type_analysis,
                'level_analysis': level_analysis,
                'recommendations': []
            }

            if best_time_slot:
                analysis['recommendations'].append(f'建议在 {best_time_slot} 时间段进行重要的考试或练习,这是您的最佳答题时间')

            improving_types = [t for t in question_type_analysis if t['trend'] == 'improving']
            if improving_types:
                analysis['recommendations'].append(f'您在 {improving_types[0]["question_type"]} 题型上有明显进步,继续保持')

            declining_types = [t for t in question_type_analysis if t['trend'] == 'declining']
            if declining_types:
                analysis['recommendations'].append(f'注意 {declining_types[0]["question_type"]} 题型准确率有所下降,需要加强练习')

            return analysis
        except Exception as e:
            logger.error(f"分析答题模式失败: {str(e)}")
            return None
        finally:
            self.close()

    def generate_personalized_study_plan(self, user_id):
        """
        生成个性化学习计划

        Args:
            user_id: 用户ID

        Returns:
            个性化学习计划
        """
        weaknesses_analysis = self.analyze_user_weaknesses(user_id)
        patterns_analysis = self.analyze_answer_patterns(user_id)

        study_plan = {
            'user_id': user_id,
            'weak_areas': [],
            'recommended_practice': [],
            'schedule_suggestions': [],
            'goals': []
        }

        if weaknesses_analysis:
            for weak_type in weaknesses_analysis.get('weaknesses', []):
                if weak_type['accuracy'] < 0.6:
                    study_plan['weak_areas'].append({
                        'area': weak_type['question_type'],
                        'accuracy': weak_type['accuracy'],
                        'priority': 'high' if weak_type['accuracy'] < 0.4 else 'medium'
                    })

        if patterns_analysis:
            if patterns_analysis.get('best_time_slot'):
                study_plan['schedule_suggestions'].append(
                    f'在 {patterns_analysis["best_time_slot"]} 时间段安排重要的学习和练习'
                )

            if weaknesses_analysis:
                current_accuracy = weaknesses_analysis['overall_accuracy']
                target_accuracy = min(0.95, current_accuracy + 0.15)
                study_plan['goals'].append(f'将整体准确率从 {current_accuracy:.2f} 提高到 {target_accuracy:.2f}')

            if study_plan['weak_areas']:
                for area in study_plan['weak_areas']:
                    target_area_accuracy = min(0.85, area['accuracy'] + 0.2)
                    study_plan['goals'].append(
                        f'将 {area["area"]} 题型的准确率从 {area["accuracy"]:.2f} 提高到 {target_area_accuracy:.2f}'
                    )

        if not study_plan['weak_areas']:
            study_plan['recommended_practice'].append('增加基础题目的练习量,确保基础知识掌握')

        return study_plan


user_answer_analysis_service = UserAnswerAnalysisService()
