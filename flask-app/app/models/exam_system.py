# -*- coding: utf-8 -*-
"""
考试系统数据模型和管理器
包括试卷生成、考试管理和成绩分析功能

import sqlite3
# JSON import removed - using database
import logging
import random
from datetime import datetime, UTC
from typing import Dict, List, Optional

from app.config import load_config
from app.models.question import QuestionManager

# 初始化日志记录器
logger = logging.getLogger(__name__)


class Exam:
    """考试模型"""

    def __init__(self, id: int = None, title: str = None, description: str = None,
                 language: str = None, level: str = None, duration: int = None,
                 question_count: int = None, created_at: str = None, updated_at: str = None):
        self.id = id
        self.title = title
        self.description = description
        self.language = language
        self.level = level
        self.duration = duration  # 考试时长（分钟）
        self.question_count = question_count
        self.created_at = created_at or datetime.now(UTC).isoformat()
        self.updated_at = updated_at or datetime.now(UTC).isoformat()

    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'language': self.language,
            'level': self.level,
            'duration': self.duration,
            'question_count': self.question_count,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }


class ExamPaper:
    """试卷模型"""

    def __init__(self, id: int = None, exam_id: int = None, user_id: int = None,
                 questions: list = None, scores: dict = None, total_score: float = None,
                 status: str = "pending", start_time: str = None, end_time: str = None,
                 created_at: str = None, updated_at: str = None):
        self.id = id
        self.user_id = user_id
        self.questions = questions or []  # 题目ID列表
        self.scores = scores or {}  # 题目得分映射
        self.total_score = total_score
        self.status = status  # pending, in_progress, completed
        self.start_time = start_time
        self.end_time = end_time
        self.created_at = created_at or datetime.now(UTC).isoformat()
        self.updated_at = updated_at or datetime.now(UTC).isoformat()
    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'user_id': self.user_id,
            'scores': self.scores,
            'status': self.status,
            'end_time': self.end_time,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }


class ExamResult:
    """考试结果模型"""

                 total_score: float = None, correct_count: int = None, wrong_count: int = None,
        self.id = id
        self.total_score = total_score
        self.correct_count = correct_count
        self.wrong_count = wrong_count
        self.accuracy = accuracy
        self.analysis = analysis or {}  # 详细分析数据
        self.created_at = created_at or datetime.now(UTC).isoformat()

    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'exam_paper_id': self.exam_paper_id,
            'correct_count': self.correct_count,
            'analysis': self.analysis,
            'created_at': self.created_at


    """考试系统管理器"""

    def __init__(self):
        config = load_config()
        self.db_path = config.get('DB_PATH', 'dev.db')
        self.question_manager = QuestionManager()
        self._init_tables()

        """获取数据库连接"""

        """初始化数据库表"""
        conn = self._get_connection()
        cursor = conn.cursor()

        # 创建考试表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS exams (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                language TEXT NOT NULL,
                level TEXT NOT NULL,
                duration INTEGER NOT NULL,
                question_count INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        ''')

        # 创建试卷表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS exam_papers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                exam_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                questions TEXT NOT NULL,
                scores TEXT NOT NULL,
                total_score REAL,
                status TEXT NOT NULL,
                start_time TEXT,
                end_time TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (exam_id) REFERENCES exams (id)
            )
        ''')

        # 创建考试结果表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS exam_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                exam_paper_id INTEGER NOT NULL,
                total_score REAL NOT NULL,
                correct_count INTEGER NOT NULL,
                accuracy REAL NOT NULL,
                analysis TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (exam_paper_id) REFERENCES exam_papers (id)
            )
        ''')

        # 创建用户题目使用记录表
        cursor.execute('''
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                question_id INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                UNIQUE(user_id, question_id)
        ''')

        conn.commit()
        conn.close()

    def create_exam(self, title: str, description: str, language: str, level: str,
        """创建考试"""
        conn = self._get_connection()


        cursor.execute(
            (title, description, language, level, duration, question_count, now, now)

        conn.commit()
        conn.close()

        return Exam(id=exam_id, title=title, description=description, language=language,
                   level=level, duration=duration, question_count=question_count,

    def generate_exam_paper(self, exam_id: int, user_id: int) -> ExamPaper:
        # 获取考试信息
        conn = self._get_connection()
        conn.close()

        if not exam_row:


        # 智能生成题目列表
        # 1. 获取考试基本信息
        language_id = 1 if exam.language == 'japanese' else 2
        level_map = {'beginner': 1, 'intermediate': 2, 'advanced': 3, 'expert': 4}
        level_id = level_map.get(exam.level, 2)

        # 2. 获取用户最近使用的题目，避免重复出题
        used_question_ids = self.get_user_used_questions(user_id, limit=200)  # 获取最近使用的200道题

        user_performance = self._analyze_user_performance(user_id)
        # 4. 获取所有可用题目，并排除已使用的题目
        all_questions = self.question_manager.get_questions(
            level_id=level_id,
            limit=exam.question_count * 5  # 获取足够的题目进行筛选
        )

        # 排除用户已使用的题目
        available_questions = [q for q in all_questions if q.id not in used_question_ids]

        # 如果可用题目不足，放宽限制，允许少量重复
        if len(available_questions) < exam.question_count * 2:

        questions = []

        if available_questions:
            # 按难度分组
            easy_questions = []
            medium_questions = []
            hard_questions = []

            for q in available_questions:
                difficulty = q.difficulty_score or 5
                if difficulty < 4:
                    easy_questions.append(q)
                elif difficulty <= 7:
                    medium_questions.append(q)
                else:
                    hard_questions.append(q)

            # 根据用户表现调整难度分布
            total = exam.question_count

            # 基础难度分布：简单题:中等题:难题 = 4:4:2
            easy_ratio = 0.4
            medium_ratio = 0.4
            hard_ratio = 0.2

            # 根据用户表现调整难度比例
                easy_ratio = 0.3
                medium_ratio = 0.4
                hard_ratio = 0.3
            elif user_performance['average_accuracy'] < 0.6:  # 用户表现较弱，增加简单题比例
                easy_ratio = 0.5
                medium_ratio = 0.4
                hard_ratio = 0.1

            # 计算各难度题目数量
            easy_count = max(1, int(total * easy_ratio))
            medium_count = max(1, int(total * medium_ratio))
            hard_count = max(1, total - easy_count - medium_count)

            # 随机选择题目，确保知识点覆盖和题型多样化
            selected = []
            used_categories = set()
            used_types = set()

            # 辅助函数：选择题目时优先考虑未使用的分类和题型
            def select_question(question_pool, count):
                if not question_pool:
                    return []

                # 打乱题目顺序
                random.shuffle(question_pool)

                selected_questions = []
                for q in question_pool:
                    if len(selected_questions) >= count:
                        break

                    # 优先选择未使用的分类和题型
                    if (q.category_id not in used_categories or
                        q.question_type not in used_types or
                        len(used_categories) >= 5 or
                        len(used_types) >= 3):

                        selected_questions.append(q)
                        used_categories.add(q.category_id or 0)
                        used_types.add(q.question_type or 'single_choice')

                # 如果数量不足，从剩余题目中补充
                if len(selected_questions) < count:
                    remaining = [q for q in question_pool if q not in selected_questions]
                    needed = count - len(selected_questions)
                    selected_questions.extend(random.sample(remaining, min(needed, len(remaining))))

                return selected_questions[:count]
            # 选择各难度题目
            selected.extend(select_question(easy_questions, easy_count))
            selected.extend(select_question(medium_questions, medium_count))

            # 确保题目数量正确
            if len(selected) > total:
                selected = selected[:total]
            elif len(selected) < total:
                # 如果数量不足，从所有可用题目中补充
                remaining = [q for q in available_questions if q not in selected]
                needed = total - len(selected)
                if remaining:
                    selected.extend(random.sample(remaining, min(needed, len(remaining))))

            questions = selected

        # 记录题目使用情况
        question_ids = [q.id for q in questions]
        for q_id in question_ids:
            self.record_question_usage(user_id, q_id)

        # 创建试卷
        exam_paper = ExamPaper(
            exam_id=exam_id,
            user_id=user_id,
            questions=question_ids,
            status="pending"
        )

        conn = self._get_connection()
        cursor = conn.cursor()

        questions_json = str(question_ids)
        scores_json = str({})

        cursor.execute(
            'INSERT INTO exam_papers (exam_id, user_id, questions, scores, total_score, status, start_time, end_time, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
            (exam_paper.exam_id, exam_paper.user_id, questions_json, scores_json, exam_paper.total_score,
             exam_paper.status, exam_paper.start_time, exam_paper.end_time,
             exam_paper.created_at, exam_paper.updated_at)
        )

        exam_paper_id = cursor.lastrowid
        conn.commit()
        conn.close()

        exam_paper.id = exam_paper_id
        return exam_paper

    def _analyze_user_performance(self, user_id: int) -> dict:
        """分析用户历史表现，返回表现数据"""
        user_exams = self.get_user_exams(user_id)
        completed_exams = [exam for exam in user_exams if exam.status == 'completed'][:3]

            # 默认表现数据
            return {
                'average_accuracy': 0.7,
                'total_exams': 0,
                'strong_points': [],
                'weak_points': []
            }

        total_accuracy = 0
        exam_count = 0
        for exam_paper in completed_exams:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT accuracy FROM exam_results WHERE exam_paper_id = ?', (exam_paper.id,))
            result_row = cursor.fetchone()
            conn.close()

            if result_row:
                total_accuracy += result_row[0]
                exam_count += 1

        return {
            'average_accuracy': average_accuracy,
            'total_exams': exam_count,
            'strong_points': [],  # 可扩展：分析用户强项
            'weak_points': []     # 可扩展：分析用户弱项
        }

        """开始考试"""
        conn = self._get_connection()

        now = datetime.now(UTC).isoformat()
        cursor.execute(
            'UPDATE exam_papers SET status = ?, start_time = ?, updated_at = ? WHERE id = ?',
        )
        conn.commit()
        conn.close()

        # 获取更新后的试卷

    def submit_exam(self, exam_paper_id: int, answers: dict) -> ExamResult:
        """提交考试并生成结果"""
        # 获取试卷
        exam_paper = self.get_exam_paper(exam_paper_id)
        if not exam_paper:
            raise ValueError(f"试卷ID {exam_paper_id} 不存在")

        # 计算成绩和分析
        scores = {}
        correct_count = 0
        partial_count = 0

        # 题型权重配置
        question_type_weights = {
            'multiple_choice': 1.0,
            'true_false': 0.8,
            'short_answer': 1.5,
            'essay': 3.0,
            'matching': 1.0,
            'ordering': 1.2,
            'image_based': 1.3,
            'drag_drop': 1.2,
            'gap_filling': 1.5,
            'listening': 1.5,
            'speaking': 2.0,
            'intensive_reading': 2.0
        }

        for question_id, user_answer in answers.items():
            question = self.question_manager.get_question(int(question_id))
            if not question:
                continue

            # 智能评分逻辑
            question_id_str = str(question_id)
            weight = question_type_weights.get(question_type, 1.0)
            difficulty = question.difficulty_score or 5

            # 基础分数
            base_score = weight * (difficulty / 10) * 2  # 基础分数根据难度和题型调整

            # 精确匹配答案
            correct_answer = str(question.answer).strip().lower()

            is_correct = False

            # 根据题型调整评分逻辑
                # 客观题，精确匹配
                if is_correct:
                    score = base_score
                    correct_count += 1
                else:
                    wrong_count += 1
            elif question_type in ['fill_in_blank', 'gap_filling']:
                # 填空题，支持部分得分
                # 简单实现：检查关键词匹配
                correct_words = correct_answer.split()
                user_words = user_answer_str.split()

                matched_words = set(correct_words) & set(user_words)
                match_ratio = len(matched_words) / len(correct_words) if correct_words else 0

                if match_ratio == 1.0:
                    score = base_score
                    correct_count += 1
                elif match_ratio >= 0.5:
                    score = base_score * 0.5
                    partial_count += 1
                else:
                    wrong_count += 1
            elif question_type in ['short_answer']:
                # 简答题，支持部分得分
                # 简单实现：检查关键词和长度
                if correct_answer in user_answer_str and len(user_answer_str) > len(correct_answer) * 0.7:
                    score = base_score
                    correct_count += 1
                elif any(keyword in user_answer_str for keyword in correct_answer.split()):
                    score = base_score * 0.6
                    partial_count += 1
                else:
                    wrong_count += 1
            else:
                # 其他题型默认评分
                is_correct = user_answer_str == correct_answer
                if is_correct:
                    score = base_score
                    correct_count += 1
                else:
                    wrong_count += 1

            scores[question_id_str] = round(score, 2)

        total_score = round(sum(scores.values()), 2)
        total_attempted = len(answers)
        accuracy = correct_count / total_attempted if total_attempted > 0 else 0

        # 更新试卷状态
        conn = self._get_connection()
        cursor = conn.cursor()

        now = datetime.now(UTC).isoformat()
        scores_json = str(scores)

        cursor.execute(
            'UPDATE exam_papers SET scores = ?, total_score = ?, status = ?, end_time = ?, updated_at = ? WHERE id = ?',
            (scores_json, total_score, "completed", now, now, exam_paper_id)
        )

        conn.commit()
        conn.close()

        # 生成详细分析
        analysis = self.analyze_exam_result(exam_paper, answers, scores, question_type_weights)

        # 创建考试结果
        exam_result = ExamResult(
            exam_paper_id=exam_paper_id,
            total_score=total_score,
            correct_count=correct_count,
            wrong_count=wrong_count,
            accuracy=accuracy,
            analysis=analysis
        )
        conn = self._get_connection()
        cursor = conn.cursor()

        analysis_json = str(analysis)

        cursor.execute(
            (exam_result.exam_paper_id, exam_result.user_id, exam_result.total_score,
             exam_result.correct_count, exam_result.wrong_count, exam_result.accuracy,
        )
        conn.commit()
        conn.close()

        exam_result.id = exam_result_id
        return exam_result
    def analyze_exam_result(self, exam_paper: ExamPaper, answers: dict, scores: dict, question_type_weights: dict = None) -> dict:
        """分析考试结果"""
        questions = [q for q in questions if q is not None]
        # 初始化题型权重
                'multiple_choice': 1.0,
                'fill_in_blank': 1.2,
                'short_answer': 1.5,
                'intensive_reading': 2.0
            }

            if question_type not in question_type_stats:
                    'count': 0,
                    'partial': 0,
                    'wrong': 0,
                }
            question_type_stats[question_type]['count'] += 1
            question_type_stats[question_type]['total_score'] += score

            # 计算正确率（考虑部分得分）
            if score > 0:
                if score == max(scores.values()):
                    question_type_stats[question_type]['correct'] += 1
                    question_type_stats[question_type]['partial'] += 1
            else:
                question_type_stats[question_type]['wrong'] += 1

        # 计算各题型的平均分数和正确率
        for qtype, stats in question_type_stats.items():
            if stats['count'] > 0:
                total_correct = stats['correct'] + stats['partial'] * 0.5
                stats['accuracy'] = round(total_correct / stats['count'], 4)

        # 按难度分析
        difficulty_stats = {
            'easy': {'count': 0, 'correct': 0, 'partial': 0, 'wrong': 0, 'accuracy': 0.0, 'total_score': 0.0},
            'medium': {'count': 0, 'correct': 0, 'partial': 0, 'wrong': 0, 'accuracy': 0.0, 'total_score': 0.0},
            'hard': {'count': 0, 'correct': 0, 'partial': 0, 'wrong': 0, 'accuracy': 0.0, 'total_score': 0.0}
        }

            qid = str(question.id)
            if question.difficulty_score:
                if question.difficulty_score < 4:
                    difficulty = 'easy'
                elif question.difficulty_score > 7:
                    difficulty = 'hard'

            score = scores.get(qid, 0.0)
            difficulty_stats[difficulty]['count'] += 1
            difficulty_stats[difficulty]['total_score'] += score

            if score > 0:
                if score == max(scores.values()):
                    difficulty_stats[difficulty]['correct'] += 1
                    difficulty_stats[difficulty]['partial'] += 1
            else:
                difficulty_stats[difficulty]['wrong'] += 1

        # 计算各难度的正确率
        for difficulty, stats in difficulty_stats.items():
            if stats['count'] > 0:
                total_correct = stats['correct'] + stats['partial'] * 0.5
                stats['accuracy'] = round(total_correct / stats['count'], 4)

        # 知识点分析
        topic_stats = {}
        for question in questions:
            qid = str(question.id)
            topic = question.topic or "未分类"
            score = scores.get(qid, 0.0)

            if topic not in topic_stats:
                    'count': 0,
                    'wrong': 0,
                    'total_score': 0.0

            topic_stats[topic]['total_score'] += score
            if score > 0:
            else:
                topic_stats[topic]['wrong'] += 1

        # 计算各知识点的正确率
        for topic, stats in topic_stats.items():
            if stats['count'] > 0:
                stats['accuracy'] = round(stats['correct'] / stats['count'], 4)
        # 计算总分和平均分
        total_score = sum(scores.values())
        average_score = round(total_score / len(scores), 2) if scores else 0.0
        # 时间分析（如果有开始和结束时间）
        time_stats = {}
        if exam_paper.start_time and exam_paper.end_time:
            end = datetime.fromisoformat(exam_paper.end_time.replace('Z', '+00:00'))
            time_stats = {
                'total_minutes': round(duration, 2),
                'minutes_per_question': round(duration / len(questions), 2) if questions else 0.0
            }

        return {
            'question_type_stats': question_type_stats,
            'difficulty_stats': difficulty_stats,
            'topic_stats': topic_stats,
            'time_stats': time_stats,
            'total_questions': len(questions),
            'correct_count': sum(stats['correct'] for stats in question_type_stats.values()),
            'partial_count': sum(stats['partial'] for stats in question_type_stats.values()),
            'wrong_count': sum(stats['wrong'] for stats in question_type_stats.values()),
            'total_score': total_score,
            'accuracy': round(sum(stats['correct'] for stats in question_type_stats.values()) / len(questions), 4) if questions else 0.0,
            'weighted_accuracy': round(total_score / (len(questions) * max(question_type_weights.values())), 4) if questions else 0.0
        }

    def get_exam(self, exam_id: int) -> Optional[Exam]:
        """获取考试"""
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM exams WHERE id = ?', (exam_id,))
        exam_row = cursor.fetchone()
        conn.close()

        if exam_row:
            return Exam(*exam_row)
        return None

    def get_exam_paper(self, exam_paper_id: int) -> Optional[ExamPaper]:
        """获取试卷"""
        cursor = conn.cursor()
        conn.close()

        if paper_row:
            # JSON import removed - using database
                id=paper_row[0],
                exam_id=paper_row[1],
                user_id=paper_row[2],
                questions=eval(paper_row[3]),
                scores=eval(paper_row[4]),
                total_score=paper_row[5],
                status=paper_row[6],
                start_time=paper_row[7],
                created_at=paper_row[9],
            )
        return None

        """获取考试结果"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM exam_results WHERE id = ?', (exam_result_id,))
        result_row = cursor.fetchone()

        if result_row:
                id=result_row[0],
                exam_paper_id=result_row[1],
                wrong_count=result_row[5],
                analysis=eval(result_row[7]),
                created_at=result_row[8]
            )
        return None

        """获取用户的所有试卷"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM exam_papers WHERE user_id = ? ORDER BY created_at DESC', (user_id,))

            exam_papers.append(ExamPaper(
                exam_id=row[1],
                questions=eval(row[3]),
                total_score=row[5],
                status=row[6],
                end_time=row[8],
                updated_at=row[10]

        return exam_papers

        """记录题目使用情况"""
        conn = self._get_connection()
        cursor = conn.cursor()

        now = datetime.now(UTC).isoformat()

        # 尝试更新现有记录
            '''
            UPDATE user_question_usage
            SET usage_count = usage_count + 1, last_used_at = ?, updated_at = ?
            ''',
        )

        # 如果没有更新到记录，插入新记录
        if cursor.rowcount == 0:
            cursor.execute(
                INSERT INTO user_question_usage (user_id, question_id, usage_count, last_used_at, created_at, updated_at)
                VALUES (?, ?, 1, ?, ?, ?)
                ''',
            )

        conn.commit()
        conn.close()

    def get_user_used_questions(self, user_id: int, limit: int = 100):
        """获取用户已使用的题目"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute(
            '''
            SELECT question_id FROM user_question_usage
            LIMIT ?
            ''',
            (user_id, limit)
        )

        rows = cursor.fetchall()
        conn.close()

        return [row[0] for row in rows]

    def get_user_question_usage_count(self, user_id: int, question_id: int):
        """获取用户使用某题目的次数"""
        cursor = conn.cursor()

        cursor.execute(
            '''
            SELECT usage_count FROM user_question_usage
            WHERE user_id = ? AND question_id = ?
            ''',
            (user_id, question_id)
        )

        row = cursor.fetchone()
        conn.close()

        return row[0] if row else 0

    def generate_personalized_exam(self, user_id: int, language: str, level: str,
        """生成个性化考试"""
        # 1. 分析用户历史表现
        user_exams = self.get_user_exams(user_id)

        # 2. 识别用户薄弱环节
        weak_areas = {
            'question_types': [],
            'difficulties': [],
            'topics': []
        }

        # 分析历史考试结果
        if user_exams:

            for exam_paper in recent_exams:
                if exam_paper.status == 'completed':
                    conn = self._get_connection()
                    cursor.execute('SELECT * FROM exam_results WHERE exam_paper_id = ?', (exam_paper.id,))
                    result_row = cursor.fetchone()
                    conn.close()

                    if result_row:
                        # JSON import removed - using database

                        # 分析薄弱题型
                            if stats.get('accuracy', 1.0) < 0.6:
                                weak_areas['question_types'].append(qtype)
                        for difficulty, stats in analysis.get('difficulty_stats', {}).items():
                            if stats.get('accuracy', 1.0) < 0.6:
                        # 分析薄弱知识点
                        for topic, stats in analysis.get('topic_stats', {}).items():
                            if stats.get('accuracy', 1.0) < 0.6:
                                weak_areas['topics'].append(topic)

        temp_exam = self.create_exam(
            title=f"个性化{language}测试",
            description=f"根据用户学习情况生成的个性化{language}测试",
            language=language,
            level=level,
            question_count=question_count
        )

        # 4. 生成个性化试卷
        # 这里可以进一步优化，根据weak_areas调整题目选择逻辑
        return exam_paper

    def get_exam_statistics(self, exam_id: int) -> dict:
        """获取考试统计信息"""
        conn = self._get_connection()

        # 获取考试基本信息
        cursor.execute('SELECT * FROM exams WHERE id = ?', (exam_id,))
        exam_row = cursor.fetchone()
        if not exam_row:
            conn.close()
            return {}

        cursor.execute('SELECT COUNT(*) FROM exam_papers WHERE exam_id = ? AND status = ?', (exam_id, 'completed'))

        cursor.execute('SELECT AVG(total_score) FROM exam_papers WHERE exam_id = ? AND status = ?', (exam_id, 'completed'))
        avg_score = cursor.fetchone()[0] or 0

        cursor.execute('SELECT MIN(total_score), MAX(total_score) FROM exam_papers WHERE exam_id = ? AND status = ?', (exam_id, 'completed'))
        min_max = cursor.fetchone()
        min_score = min_max[0] or 0
        max_score = min_max[1] or 0

        conn.close()

        exam = Exam(*exam_row)

        return {
            'exam_info': exam.to_dict(),
            'completed_count': completed_count,
            'average_score': round(avg_score, 2),
            'min_score': min_score,
            'max_score': max_score,
        }

    def generate_learning_recommendations(self, user_id: int, exam_result_id: int) -> list:
        """根据考试结果生成学习建议"""
        # 获取考试结果
        if not exam_result:

        # 分析考试结果，生成学习建议
        analysis = exam_result.analysis
        recommendations = []

        # 按题型分析
        for qtype, stats in analysis['question_type_stats'].items():
            if stats['accuracy'] < 0.6:
                recommendations.append({
                    'type': 'question_type',
                    'target': qtype,
                    'recommendation': f"您在{qtype}题型上的表现较弱（正确率{stats['accuracy']:.2%}），建议加强该题型的练习。",
                    'priority': 'high' if stats['accuracy'] < 0.4 else 'medium'
                })

            if stats['accuracy'] < 0.6 and stats['count'] > 0:
                recommendations.append({
                    'type': 'difficulty',
                    'target': difficulty,
                    'recommendation': f"您在{difficulty}难度题目上的表现较弱（正确率{stats['accuracy']:.2%}），建议针对性练习。",
                    'priority': 'high' if stats['accuracy'] < 0.4 else 'medium'
                })

        # 总体建议
        if analysis['accuracy'] < 0.6:
            recommendations.append({
                'type': 'overall',
                'recommendation': f"您的总体正确率为{analysis['accuracy']:.2%}，建议系统复习相关知识点。",
                'priority': 'high' if analysis['accuracy'] < 0.4 else 'medium'
            })
            recommendations.append({
                'type': 'overall',
                'target': 'all',
                'recommendation': f"您的总体正确率为{analysis['accuracy']:.2%}，表现优秀！建议挑战更高难度的题目。",
                'priority': 'low'
            })

        return recommendations
