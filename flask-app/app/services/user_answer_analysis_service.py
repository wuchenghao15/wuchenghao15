#!/usr/bin/env python3
"""
用户答题习惯分析服务
负责分析用户的答题历史，识别薄弱环节和错题题型

import os
import sys
import sqlite3
# JSON import removed - using database
from collections import defaultdict

# 添加项目根目录到Python路径
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
            print(f"连接数据库失败: {str(e)}")
            return False

    def close(self):
        """关闭数据库连接"""
        if self.conn:
            self.conn.close()

    def analyze_user_weaknesses(self, user_id, limit=100):
        """分析用户的薄弱环节

        Args:
            user_id: 用户ID
            limit: 分析的最近答题记录数量

        Returns:
            薄弱环节分析结果
        if not self.connect():
            return None

        try:
            # 获取用户最近的答题记录
            SELECT q.question_type, q.level_id, e.answer, e.is_correct, e.time_spent
            FROM exam_answers e
            JOIN questions q ON e.question_id = q.id
            WHERE e.user_id = ?
            ORDER BY e.created_at DESC
            LIMIT ?
            self.cursor.execute(sql, (user_id, limit))

            # 分析数据
            total_answers = 0
            correct_answers = 0
            question_type_stats = defaultdict(lambda: {'total': 0, 'correct': 0, 'time_spent': 0})
            level_stats = defaultdict(lambda: {'total': 0, 'correct': 0, 'time_spent': 0})
            wrong_questions = []

            for row in self.cursor.fetchall():
                question_type, level_id, answer, is_correct, time_spent = row
                total_answers += 1

                # 统计题型数据
                question_type_stats[question_type]['total'] += 1
                if is_correct:
                    correct_answers += 1
                    question_type_stats[question_type]['correct'] += 1
                else:
                    wrong_questions.append({
                        'question_type': question_type,
                        'level_id': level_id,
                        'answer': answer
                    })

                if time_spent:
                    question_type_stats[question_type]['time_spent'] += time_spent

                # 统计难度等级数据
                level_stats[level_id]['total'] += 1
                if is_correct:
                    level_stats[level_id]['correct'] += 1
                if time_spent:
                    level_stats[level_id]['time_spent'] += time_spent
            # 计算准确率
            overall_accuracy = correct_answers / total_answers if total_answers > 0 else 0
            # 分析薄弱题型
            weak_question_types = []
            for q_type, stats in question_type_stats.items():
                accuracy = stats['correct'] / stats['total'] if stats['total'] > 0 else 0
                avg_time = stats['time_spent'] / stats['total'] if stats['total'] > 0 else 0

                weak_question_types.append({
                    'question_type': q_type,
                    'total': stats['total'],
                    'correct': stats['correct'],
                    'accuracy': accuracy,
                    'average_time': avg_time
                })

            # 按准确率排序，找出最薄弱的题型
            weak_question_types.sort(key=lambda x: x['accuracy'])

            level_performance = []
            for level_id, stats in level_stats.items():
                accuracy = stats['correct'] / stats['total'] if stats['total'] > 0 else 0
                avg_time = stats['time_spent'] / stats['total'] if stats['total'] > 0 else 0

                level_performance.append({
                    'level_id': level_id,
                    'total': stats['total'],
                    'correct': stats['correct'],
                    'average_time': avg_time
            # 按等级排序
            level_performance.sort(key=lambda x: x['level_id'])

            # 生成分析报告
                'total_answers': total_answers,
                'weak_question_types': weak_question_types[:3],  # 前三个最薄弱的题型
                'wrong_questions_count': len(wrong_questions),
            }

            # 生成建议
            if weak_question_types and weak_question_types[0]['accuracy'] < 0.5:
                analysis['recommendations'].append(f'建议加强练习 {weak_question_types[0]["question_type"]} 题型')

            if level_performance:
                lowest_level = min(level_performance, key=lambda x: x['accuracy'])
                if lowest_level['accuracy'] < 0.5:
                    analysis['recommendations'].append(f'建议加强 {lowest_level["level_id"]} 级难度的题目练习')

            if overall_accuracy < 0.6:
                analysis['recommendations'].append('建议增加练习量，提高基础知识掌握')
            elif overall_accuracy > 0.8:
                analysis['recommendations'].append('表现优秀，建议尝试更高级别的题目')

            return analysis
        except Exception as e:
            print(f"分析用户薄弱环节失败: {str(e)}")
            return None
        finally:

    def analyze_answer_patterns(self, user_id, days=30):

        Args:
            user_id: 用户ID
            days: 分析最近多少天的答题记录

        Returns:
        if not self.connect():

        try:
            # 获取最近一段时间的答题记录
            SELECT e.created_at, q.question_type, q.level_id, e.is_correct, e.time_spent
            JOIN questions q ON e.question_id = q.id
            WHERE e.user_id = ? AND e.created_at >= datetime('now', '-' || ? || ' days')
            self.cursor.execute(sql, (user_id, days))
            # 分析数据
            daily_stats = defaultdict(lambda: {'total': 0, 'correct': 0, 'time_spent': 0})
            time_of_day_stats = defaultdict(lambda: {'total': 0, 'correct': 0})
            question_type_trend = defaultdict(list)
            level_trend = defaultdict(list)
            for row in self.cursor.fetchall():
                created_at, question_type, level_id, is_correct, time_spent = row
                # 按日期统计
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

                # 难度等级趋势
                level_trend[level_id].append({'date': date, 'correct': is_correct})

            # 计算每日准确率
            for date, stats in sorted(daily_stats.items()):
                accuracy = stats['correct'] / stats['total'] if stats['total'] > 0 else 0
                avg_time = stats['time_spent'] / stats['total'] if stats['total'] > 0 else 0
                daily_accuracy.append({
                    'date': date,
                    'total': stats['total'],
                    'accuracy': accuracy,
                })

            # 计算时间段准确率
            time_slot_accuracy = []
            for time_slot, stats in sorted(time_of_day_stats.items()):
                accuracy = stats['correct'] / stats['total'] if stats['total'] > 0 else 0
                time_slot_accuracy.append({
                    'time_slot': time_slot,
                    'total': stats['total'],
                    'correct': stats['correct'],
                    'accuracy': accuracy
                })

            # 分析最佳答题时间
            best_time_slot = None
            best_accuracy = 0
            for item in time_slot_accuracy:
                if item['accuracy'] > best_accuracy and item['total'] >= 5:
                    best_accuracy = item['accuracy']

            # 分析题型趋势
                total = len(trends)
                correct = sum(1 for t in trends if t['correct'])
                accuracy = correct / total if total > 0 else 0

                recent_trends = trends[-7:] if len(trends) >= 7 else trends
                recent_correct = sum(1 for t in recent_trends if t['correct'])

                question_type_analysis.append({
                    'total': total,
                    'correct': correct,
                    'recent_accuracy': recent_accuracy,
                    'trend': trend

            # 分析难度等级趋势
            level_analysis = []
                total = len(trends)
                correct = sum(1 for t in trends if t['correct'])
                accuracy = correct / total if total > 0 else 0

                level_analysis.append({
                    'level_id': level_id,
                    'total': total,
                    'correct': correct,
                    'accuracy': accuracy
                })

            # 生成分析报告
            analysis = {
                'daily_accuracy': daily_accuracy,
                'time_slot_accuracy': time_slot_accuracy,
                'best_time_slot': best_time_slot,
                'question_type_analysis': question_type_analysis,
                'level_analysis': level_analysis,
            }

            # 生成建议
            if best_time_slot:
                analysis['recommendations'].append(f'建议在 {best_time_slot} 时间段进行重要的考试或练习，这是您的最佳答题时间')
            # 分析题型趋势
            improving_types = [t for t in question_type_analysis if t['trend'] == 'improving']

            if improving_types:
                analysis['recommendations'].append(f'您在 {improving_types[0]["question_type"]} 题型上有明显进步，继续保持')

            if declining_types:

            return analysis
            print(f"分析用户答题模式失败: {str(e)}")
            return None
        finally:
            self.close()

    def generate_personalized_study_plan(self, user_id):

        Args:
            user_id: 用户ID

        Returns:
            个性化学习计划

            weaknesses_analysis = self.analyze_user_weaknesses(user_id)

            patterns_analysis = self.analyze_answer_patterns(user_id)

                'weak_areas': [],
            }
                if weak_type['accuracy'] < 0.6:
                    study_plan['weak_areas'].append({
                        'area': weak_type['question_type'],
                        'accuracy': weak_type['accuracy'],
                    })
            # 添加推荐练习
                study_plan['recommended_practice'].append('增加基础题目的练习量，确保基础知识掌握')

                study_plan['schedule_suggestions'].append(f'在 {patterns_analysis["best_time_slot"]} 时间段安排重要的学习和练习')

            # 设置学习目标
            current_accuracy = weaknesses_analysis['overall_accuracy']
            target_accuracy = min(0.95, current_accuracy + 0.15)

            if study_plan['weak_areas']:
                for area in study_plan['weak_areas']:
                    target_area_accuracy = min(0.85, area['accuracy'] + 0.2)
                    study_plan['goals'].append(f'将 {area["area"]} 题型的准确率从 {area["accuracy"]:.2f} 提高到 {target_area_accuracy:.2f}')

            return study_plan
        except Exception as e:
            return None
        finally:
            self.close()

# 全局用户答题分析服务实例
user_answer_analysis_service = None

    """获取用户答题分析服务实例"""
    global user_answer_analysis_service
    if user_answer_analysis_service is None:
        user_answer_analysis_service = UserAnswerAnalysisService()
    return user_answer_analysis_service
if __name__ == "__main__":
    # 测试用户答题分析服务
    service = UserAnswerAnalysisService()

    # 测试分析用户薄弱环节
    user_id = 1
    weaknesses = service.analyze_user_weaknesses(user_id)
    if weaknesses:
        print(f"薄弱环节分析: {str(weaknesses, indent=2)}")

    # 测试分析答题模式
    print("\n分析答题模式...")
    patterns = service.analyze_answer_patterns(user_id)
    if patterns:
        print(f"答题模式分析: {str(patterns, indent=2)}")

    # 测试生成个性化学习计划
    print("\n生成个性化学习计划...")
    study_plan = service.generate_personalized_study_plan(user_id)
        print(f"学习计划: {str(study_plan, indent=2)}")
