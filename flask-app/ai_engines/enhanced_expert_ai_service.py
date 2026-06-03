# -*- coding: utf-8 -*-
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
优化后的专家AI分析服务
包含:
"""
import logging
logger = logging.getLogger(__name__)
import os
import sys
import sqlite3
from contextlib import contextmanager
import random
from collections import defaultdict
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class EnhancedExpertAIService:
    """优化后的专家AI分析服务"""

    def __init__(self, db_path="app.db"):
        """初始化服务"""
        self.db_path = db_path
        self.conn = None
        self.cursor = None

        self.level_up_config = {
            'min_answers': 20,
            'min_accuracy': 0.75,
            'high_level_accuracy': 0.70,
            'consecutive_exams': 2,
            'time_window_days': 30,
            'min_improvement_trend': 0.05
        }

        self.improvement_exam_config = {
            'current_level_weight': 0.40,
            'next_level_weight': 0.35,
            'weak_area_weight': 0.15,
            'review_weight': 0.10,
            'default_exam_size': 15,
            'include_listening': True,
            'include_writing': False,
            'adaptive_difficulty': True
        }

        self.question_bank_requirements = {
            'min_questions_per_level': 30,
            'min_questions_per_type': 15,
            'question_types': ['multiple_choice', 'fill_in_blank', 'true_false', 'short_answer', 'listening'],
            'min_audio_per_language': 10,
            'accents_required': {
                'english': ['british', 'american'],
                'japanese': ['kanto', 'kansai']
            },
            'difficulty_distribution': {
                1: 0.25,
                2: 0.25,
                3: 0.20,
                4: 0.15,
                5: 0.15
            },
            'freshness_threshold_days': 180
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

    def analyze_level_eligibility(self, user_id, language='japanese'):
        """分析用户是否具备等级提升资格
        
        Args:
            user_id: 用户ID
            language: 语言
            
        Returns:
            等级提升分析结果
        """
        if not self.connect():
            return None
        
        try:
            current_level = self._get_user_level(user_id, language)
            exam_stats = self._get_user_exam_stats(user_id, language)
            improvement_trend = self._calculate_improvement_trend(user_id, language)
            
            eligibility = {
                'user_id': user_id,
                'current_level': current_level,
                'next_level': current_level + 1 if current_level < 5 else None,
                'eligible': False,
                'reasons': [],
                'exam_stats': exam_stats,
                'improvement_trend': improvement_trend
            }
            
            if exam_stats.get('total_exams', 0) < self.level_up_config['consecutive_exams']:
                eligibility['reasons'].append(f"需要完成至少 {self.level_up_config['consecutive_exams']} 次考试")
            
            if exam_stats.get('consecutive_passed', 0) >= self.level_up_config['consecutive_exams']:
                eligibility['eligible'] = True
                eligibility['reasons'].append("连续考试达标")
            
            if improvement_trend >= self.level_up_config['min_improvement_trend']:
                eligibility['eligible'] = True
                eligibility['reasons'].append(f"提升趋势良好 ({improvement_trend:.2%})")
            
            return eligibility
        except Exception as e:
            logger.error(f"分析等级提升资格失败: {str(e)}")
            return None
        finally:
            self.close()

    def _get_user_level(self, user_id, language):
        """获取用户当前等级"""
        try:
            sql = """
            SELECT level FROM user_levels
            WHERE user_id = ?
            ORDER BY updated_at DESC LIMIT 1
            """
            self.cursor.execute(sql, (user_id,))
            result = self.cursor.fetchone()
            return result[0] if result else 1
        except Exception as e:
            logger.error(f"获取用户等级失败: {str(e)}")
            return 1

    def _get_user_exam_stats(self, user_id, language):
        """获取用户考试统计"""
        try:
            sql = """
            SELECT score, created_at
            FROM exam_performance
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT 10
            """
            self.cursor.execute(sql, (user_id,))
            exams = self.cursor.fetchall()

            total_exams = len(exams)
            avg_score = sum(exam[0] for exam in exams) / total_exams if total_exams > 0 else 0
            
            consecutive_passed = 0
            for exam in exams:
                score = exam[0]
                if score >= 70:
                    consecutive_passed += 1
                else:
                    break
            
            return {
                'total_exams': total_exams,
                'average_score': avg_score,
                'consecutive_passed': consecutive_passed
            }
        except Exception as e:
            logger.error(f"获取考试统计失败: {str(e)}")
            return {'total_exams': 0, 'average_score': 0, 'consecutive_passed': 0}

    def _calculate_improvement_trend(self, user_id, language):
        """计算提升趋势"""
        try:
            sql = """
            SELECT score, created_at
            FROM exam_performance
            WHERE user_id = ?
            ORDER BY created_at ASC
            LIMIT 10
            """
            self.cursor.execute(sql, (user_id,))
            exams = self.cursor.fetchall()
            
            if len(exams) < 3:
                return 0.1
            
            recent_scores = [exam[0] for exam in exams[-3:]]
            early_scores = [exam[0] for exam in exams[:3]]
            
            recent_avg = sum(recent_scores) / len(recent_scores)
            early_avg = sum(early_scores) / len(early_scores)
            
            if early_avg == 0:
                return 0.1
            
            return (recent_avg - early_avg) / early_avg
        except Exception as e:
            logger.error(f"计算提升趋势失败: {str(e)}")
            return 0.1

    def generate_improvement_exam(self, user_id, exam_size=None, language='japanese'):
        """生成提升试卷
        
        Args:
            user_id: 用户ID
            exam_size: 试卷大小
            language: 语言
            
        Returns:
            提升试卷题目列表
        """
        if exam_size is None:
            exam_size = self.improvement_exam_config['default_exam_size']

        current_level = self._get_user_level_simple(user_id)

        current_level_count = int(exam_size * self.improvement_exam_config['current_level_weight'])
        next_level_count = int(exam_size * self.improvement_exam_config['next_level_weight'])
        weak_area_count = int(exam_size * self.improvement_exam_config['weak_area_weight'])
        review_count = int(exam_size * self.improvement_exam_config['review_weight'])

        review_count = max(0, review_count)

        total = current_level_count + next_level_count + weak_area_count + review_count
        if total != exam_size:
            current_level_count += exam_size - total

        questions = []

        if current_level_count > 0:
            current_level_questions = self._get_questions_by_level(
                current_level, current_level_count, language
            )
            questions.extend(current_level_questions)

        if next_level_count > 0 and current_level < 5:
            next_level_questions = self._get_questions_by_level(
                current_level + 1, next_level_count, language
            )
            questions.extend(next_level_questions)

        if weak_area_count > 0:
            weak_questions = self._get_weak_area_questions(user_id, weak_area_count, language)
            questions.extend(weak_questions)

        if review_count > 0 and current_level > 1:
            review_questions = self._get_questions_by_level(
                max(1, current_level - 1), review_count, language,
                include_audio=self.improvement_exam_config['include_listening']
            )
            questions.extend(review_questions)

        while len(questions) < exam_size:
            additional = self._get_questions_by_level(current_level, 1, language, True)
            if additional:
                questions.extend(additional)
            else:
                break

        if self.improvement_exam_config['adaptive_difficulty']:
            questions = self._adjust_questions_difficulty(questions, current_level)

        random.shuffle(questions)

        return questions[:exam_size]

    def _get_user_level_simple(self, user_id):
        """简单获取用户等级"""
        if not self.connect():
            return 1
        try:
            self.cursor.execute("SELECT level FROM user_levels WHERE user_id = ? ORDER BY updated_at DESC LIMIT 1", (user_id,))
            result = self.cursor.fetchone()
            return result[0] if result else 1
        except Exception:
            return 1
        finally:
            self.close()

    def _get_questions_by_level(self, level, count, language, include_audio=False):
        """根据等级获取题目"""
        if not self.connect():
            return []
        try:
            sql = """
            SELECT id, content, options, answer, explanation, difficulty, type, audio_id, audio_filename, audio_url, audio_accent, audio_transcript
            FROM questions
            WHERE level = ? AND language = ?
            ORDER BY RANDOM()
            LIMIT ?
            """
            self.cursor.execute(sql, (level, language, count))
            rows = self.cursor.fetchall()
            return [self._format_question(row) for row in rows]
        except Exception as e:
            logger.error(f"获取题目失败: {str(e)}")
            return []
        finally:
            self.close()

    def _get_weak_area_questions(self, user_id, count, language):
        """获取薄弱环节题目"""
        performance = self._analyze_user_performance_simple(user_id)
        weak_types = performance.get('weak_areas', []) if performance else []
        
        if not self.connect():
            return []
        try:
            if weak_types:
                placeholders = ','.join(['?' for _ in weak_types])
                sql = f"""
                SELECT id, content, options, answer, explanation, difficulty, type, audio_id, audio_filename, audio_url, audio_accent, audio_transcript
                FROM questions
                WHERE type IN ({placeholders}) AND language = ?
                ORDER BY RANDOM()
                LIMIT ?
                """
                self.cursor.execute(sql, weak_types + [language, count])
            else:
                sql = """
                SELECT id, content, options, answer, explanation, difficulty, type, audio_id, audio_filename, audio_url, audio_accent, audio_transcript
                FROM questions
                WHERE language = ?
                ORDER BY RANDOM()
                LIMIT ?
                """
                self.cursor.execute(sql, (language, count))
            
            rows = self.cursor.fetchall()
            return [self._format_question(row) for row in rows]
        except Exception as e:
            logger.error(f"获取薄弱环节题目失败: {str(e)}")
            return []
        finally:
            self.close()

    def _analyze_user_performance_simple(self, user_id):
        """简单分析用户表现"""
        if not self.connect():
            return None
        try:
            sql = """
            SELECT type, AVG(score) as avg_score
            FROM question_performance
            WHERE user_id = ?
            GROUP BY type
            """
            self.cursor.execute(sql, (user_id,))
            results = self.cursor.fetchall()
            
            if not results:
                return None
            
            weak_areas = [row[0] for row in results if row[1] < 70]
            return {'weak_areas': weak_areas}
        except Exception as e:
            logger.error(f"分析用户表现失败: {str(e)}")
            return None
        finally:
            self.close()

    def _format_question(self, row):
        """格式化题目"""
        question = {
            'id': row[0],
            'content': row[1],
            'options': eval(row[2]) if row[2] else [],
            'answer': row[3],
            'explanation': row[4],
            'difficulty': row[5],
            'type': row[6]
        }
        
        if len(row) > 7 and row[7]:
            question['audio'] = {
                'id': row[7],
                'filename': row[8],
                'url': row[9],
                'accent': row[10],
                'transcript': row[11]
            }
        
        return question

    def _adjust_questions_difficulty(self, questions, current_level):
        """调整题目难度"""
        return questions

    def generate_question_bank_requirements(self, language='japanese'):
        """生成题库需求清单
        
        Args:
            language: 语言
            
        Returns:
            题库需求清单
        """
        health_report = self.analyze_question_bank_health(language)
        if not health_report:
            return None
        
        requirements = {
            'language': language,
            'current_status': health_report,
            'requirements': self.question_bank_requirements,
            'recommendations': []
        }
        
        for level, required in self.question_bank_requirements['difficulty_distribution'].items():
            current = health_report.get('level_distribution', {}).get(level, 0)
            if current < required:
                requirements['recommendations'].append(
                    f"等级 {level} 题目不足,建议增加 {int((required - current) * 100)} 道"
                )
        
        return requirements

    def analyze_question_bank_health(self, language='japanese'):
        """分析题库健康状态"""
        if not self.connect():
            return None
        try:
            self.cursor.execute("SELECT COUNT(*) FROM questions WHERE language = ?", (language,))
            total = self.cursor.fetchone()[0]
            
            self.cursor.execute("SELECT level, COUNT(*) FROM questions WHERE language = ? GROUP BY level", (language,))
            level_distribution = {row[0]: row[1] / total if total > 0 else 0 for row in self.cursor.fetchall()}
            
            return {
                'total_questions': total,
                'level_distribution': level_distribution,
                'health_score': min(100, total / self.question_bank_requirements['min_questions_per_level'] * 20)
            }
        except Exception as e:
            logger.error(f"分析题库健康状态失败: {str(e)}")
            return None
        finally:
            self.close()

_enhanced_expert_ai_service = None

def get_enhanced_expert_ai_service():
    """获取优化后的专家AI服务实例"""
    global _enhanced_expert_ai_service
    if _enhanced_expert_ai_service is None:
        _enhanced_expert_ai_service = EnhancedExpertAIService()
    return _enhanced_expert_ai_service
