# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
考试系统管理器
整合考试生成、题库管理、考试统计和学习系统整合功能
"""

import os
import sys
import json
import random
import uuid
from datetime import datetime, UTC
import logging
from typing import Dict, List, Any, Optional

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('exam_system_manager.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('exam_system_manager')


class ExamSystemManager:
    """考试系统管理器"""

    def __init__(self):
        """初始化考试系统管理器"""
        self.exam_generator = None
        self.question_manager = None
        self.learning_system = None

        # 加载配置
        self.config = self._load_config()

        # 初始化组件
        self._initialize_components()

        # 初始化缓存
        self._init_cache()

        logger.info("考试系统管理器初始化完成")

    def _load_config(self) -> Dict[str, Any]:
        """加载配置"""
        config = {
            "default_question_count": 20,
            "default_test_duration": 60,
            "difficulty_distribution": "3:5:2",
            "max_repeated_questions": 10,
            "vocabulary_ratio": 30,
            "grammar_ratio": 30,
            "reading_ratio": 40,
            "listening_enabled": False,
            "listening_ratio": 0,
            "enable_ai_question_generation": True,
            "ai_generation_threshold": 50,
            "knowledge_coverage_threshold": 80,
            "difficulty_gradient_enabled": True,
            "enable_timer": True,
            "allow_backtracking": True,
            "auto_submit_on_timeout": True,
            "show_feedback": True,
            "enable_paper_validation": True,
            "validation_severity": "standard"
        }

        # 尝试从配置文件加载
        try:
            config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config', 'exam_system_config.json')
            if os.path.exists(config_file):
                with open(config_file, 'r', encoding='utf-8') as f:
                    file_config = json.load(f)
                    config.update(file_config)
                logger.info("从配置文件加载配置成功")
        except Exception as e:
            logger.warning(f"从配置文件加载配置失败: {str(e)}")

        return config

    def _initialize_components(self):
        """初始化依赖组件"""
        try:
            from exam_generator import ExamGenerator
            self.exam_generator = ExamGenerator()
            logger.info("✓ 考试生成器初始化成功")
        except Exception as e:
            logger.error(f"✗ 考试生成器初始化失败: {str(e)}")

        try:
            from app.data.dao.exam_dao import ExamDAO
            self.question_manager = ExamDAO()
            logger.info("✓ 题库管理器初始化成功")
        except Exception as e:
            logger.error(f"✗ 题库管理器初始化失败: {str(e)}")

        try:
            from app.models.learning_system import LearningSystem
            self.learning_system = LearningSystem()
            logger.info("✓ 学习系统初始化成功")
        except Exception as e:
            logger.error(f"✗ 学习系统初始化失败: {str(e)}")

    def _init_cache(self):
        """初始化缓存"""
        self.question_cache = {}
        self.user_learning_cache = {}
        self.cache_expire_time = 3600  # 缓存过期时间(秒)

    def generate_personalized_exam(self, user_id: str, subject: str, question_count: int = None, 
                                   difficulty: str = None, **kwargs) -> Dict[str, Any]:
        """
        生成个性化试卷

        Args:
            user_id: 用户ID
            subject: 科目
            question_count: 题目数量
            difficulty: 难度
            **kwargs: 其他参数

        Returns:
            生成的试卷数据
        """
        logger.info(f"为用户 {user_id} 生成 {subject} 个性化试卷")

        start_time = datetime.now(UTC)

        # 使用默认值
        question_count = question_count or self.config["default_question_count"]

        # 获取用户学习数据,用于个性化生成(带缓存)
        user_learning_data = self._get_user_learning_data(user_id, subject)

        # 基于用户学习数据调整难度
        adjusted_difficulty = self._adjust_difficulty_by_learning_data(user_learning_data, difficulty)

        # 生成试卷
        exam = {
            "exam_id": f"exam-{uuid.uuid4().hex[:8]}",
            "user_id": user_id,
            "subject": subject,
            "title": f"{subject}个性化试卷",
            "question_count": question_count,
            "difficulty": adjusted_difficulty,
            "duration": self.config["default_test_duration"],
            "generated_at": start_time.isoformat(),
            "questions": [],
            "exam_type": "personalized",
            "settings": {
                "enable_timer": self.config["enable_timer"],
                "allow_backtracking": self.config["allow_backtracking"],
                "auto_submit_on_timeout": self.config["auto_submit_on_timeout"],
                "show_feedback": self.config["show_feedback"],
                "enable_progress_save": True,
                "save_interval": 30
            }
        }

        # 生成题目
        questions = self._generate_questions_for_exam(
            subject=subject,
            count=question_count,
            difficulty=adjusted_difficulty,
            user_learning_data=user_learning_data,
            **kwargs
        )

        exam["questions"] = questions

        # 计算生成时间
        end_time = datetime.now(UTC)
        generation_time = (end_time - start_time).total_seconds()

        logger.info(f"成功为用户 {user_id} 生成 {subject} 个性化试卷,包含 {len(questions)} 道题目,生成时间:{generation_time:.2f}秒")

        # 添加生成时间到试卷信息
        exam["generation_time"] = generation_time

        return exam

    def _get_user_learning_data(self, user_id: str, subject: str) -> Dict[str, Any]:
        """获取用户学习数据"""
        learning_data = {
            "completed_courses": 0,
            "completed_lessons": 0,
            "average_score": 0,
            "weak_knowledge_points": [],
            "strong_knowledge_points": [],
            "wrong_questions": [],
            "learning_level": "beginner"
        }

        try:
            if self.learning_system:
                learning_summary = self.learning_system.get_user_learning_summary(user_id)
                learning_data["completed_courses"] = learning_summary.get("completed_courses", 0)
                learning_data["completed_lessons"] = learning_summary.get("completed_lessons", 0)
                learning_data["average_score"] = learning_summary.get("average_score", 0)
        except Exception as e:
            logger.error(f"获取用户学习摘要失败: {str(e)}")

        try:
            if self.exam_generator:
                wrong_questions = self.exam_generator.get_user_wrong_questions(user_id, subject, 20)
                learning_data["wrong_questions"] = wrong_questions
        except Exception as e:
            logger.error(f"获取用户错题失败: {str(e)}")

        # 根据平均分数确定学习水平
        if learning_data["average_score"] >= 85:
            learning_data["learning_level"] = "advanced"
        elif learning_data["average_score"] >= 70:
            learning_data["learning_level"] = "intermediate"
        else:
            learning_data["learning_level"] = "beginner"

        return learning_data

    def _adjust_difficulty_by_learning_data(self, learning_data: Dict, base_difficulty: str = None) -> str:
        """根据用户学习数据调整难度"""
        if base_difficulty:
            return base_difficulty
        return learning_data["learning_level"]

    def _generate_questions_for_exam(self, subject: str, count: int, difficulty: str, 
                                     user_learning_data: Dict, **kwargs) -> List[Dict]:
        """为试卷生成题目"""
        logger.info(f"为试卷生成 {count} 道 {subject} 题目,难度: {difficulty}")

        questions = []

        question_type_ratios = kwargs.get("question_type_ratios", {
            "single_choice": 40,
            "multiple_choice": 30,
            "true_false": 15,
            "fill_blank": 10,
            "short_answer": 5
        })

        knowledge_points = kwargs.get("knowledge_points", [])
        difficulty_gradient = kwargs.get("difficulty_gradient", "mixed")

        # 1. 添加错题
        wrong_questions = user_learning_data.get("wrong_questions", [])
        if wrong_questions:
            num_wrong_questions = min(len(wrong_questions), count // 4)
            selected_wrong_questions = wrong_questions[:num_wrong_questions]
            questions.extend(selected_wrong_questions)
            logger.info(f"添加了 {num_wrong_questions} 道错题")

        # 2. 根据题型比例生成题目
        remaining_count = count - len(questions)
        if remaining_count > 0:
            total_ratio = sum(question_type_ratios.values())
            questions_by_type = {}
            for q_type, ratio in question_type_ratios.items():
                q_count = int(remaining_count * ratio / total_ratio)
                if q_count > 0:
                    questions_by_type[q_type] = q_count

            total_calculated = sum(questions_by_type.values())
            if total_calculated < remaining_count:
                for q_type in questions_by_type:
                    if total_calculated >= remaining_count:
                        break
                    questions_by_type[q_type] += 1
                    total_calculated += 1

            for q_type, q_count in questions_by_type.items():
                try:
                    db_questions = self._get_questions_from_db(
                        subject=subject,
                        difficulty=difficulty,
                        question_type=q_type,
                        count=q_count,
                        knowledge_points=knowledge_points,
                        **kwargs
                    )
                    questions.extend(db_questions)
                    logger.info(f"从数据库获取了 {len(db_questions)} 道 {q_type} 题目")

                    if len(db_questions) < q_count and self.config["enable_ai_question_generation"]:
                        remaining_q_count = q_count - len(db_questions)
                        ai_questions = self._generate_ai_questions(
                            subject=subject,
                            difficulty=difficulty,
                            question_type=q_type,
                            count=remaining_q_count
                        )
                        questions.extend(ai_questions)
                        logger.info(f"使用AI生成了 {len(ai_questions)} 道 {q_type} 题目")
                except Exception as e:
                    logger.error(f"生成 {q_type} 题目失败: {str(e)}")

        # 3. 补充普通题目
        remaining_count = count - len(questions)
        if remaining_count > 0 and self.config["enable_ai_question_generation"]:
            available_types = ["single_choice", "multiple_choice", "true_false", "fill_blank", "short_answer"]
            ai_questions = self._generate_ai_questions(
                subject=subject,
                question_type=random.choice(available_types),
                count=remaining_count
            )
            questions.extend(ai_questions)
            logger.info(f"使用AI生成了 {len(ai_questions)} 道补充题目")

        # 4. 确保题目数量正确
        if len(questions) > count:
            questions = questions[:count]

        # 5. 根据难度梯度调整顺序
        if difficulty_gradient == "easy_to_hard":
            questions.sort(key=lambda x: {
                "beginner": 0,
                "intermediate": 1,
                "advanced": 2,
            }.get(x.get("difficulty", "beginner"), 0))
        elif difficulty_gradient == "hard_to_easy":
            questions.sort(key=lambda x: {
                "beginner": 3,
                "intermediate": 2,
                "advanced": 1,
                "expert": 0
            }.get(x.get("difficulty", "beginner"), 3))
        else:
            random.shuffle(questions)

        # 6. 智能难度调整
        questions = self._intelligently_adjust_difficulty(questions, user_learning_data)

        logger.info(f"成功生成 {len(questions)} 道题目")
        return questions

    def _get_questions_from_db(self, subject: str, difficulty: str, question_type: str, 
                               count: int, knowledge_points: List[str] = None, **kwargs) -> List[Dict]:
        """从数据库获取题目"""
        try:
            if self.question_manager and hasattr(self.question_manager, 'get_questions'):
                return self.question_manager.get_questions(
                    subject=subject,
                    difficulty=difficulty,
                    question_type=question_type,
                    count=count,
                    knowledge_points=knowledge_points or [],
                    **kwargs
                )
        except Exception as e:
            logger.error(f"从数据库获取题目失败: {str(e)}")
        return []

    def _generate_ai_questions(self, subject: str, difficulty: str, question_type: str, count: int) -> List[Dict]:
        """使用AI生成题目"""
        try:
            if self.exam_generator and hasattr(self.exam_generator, 'generate_questions_with_ai'):
                return self.exam_generator.generate_questions_with_ai(
                    subject=subject,
                    difficulty=difficulty,
                    question_type=question_type,
                    count=count
                )
        except Exception as e:
            logger.error(f"AI生成题目失败: {str(e)}")
        return []

    def _intelligently_adjust_difficulty(self, questions: List[Dict], user_learning_data: Dict) -> List[Dict]:
        """智能调整题目难度"""
        logger.info("智能调整题目难度")

        learning_level = user_learning_data.get("learning_level", "beginner")

        difficulty_adjustment = {
            "beginner": {"easy": 60, "medium": 30, "hard": 10},
            "intermediate": {"easy": 30, "medium": 50, "hard": 20},
            "advanced": {"easy": 10, "medium": 30, "hard": 60}
        }

        target_distribution = difficulty_adjustment.get(learning_level, difficulty_adjustment["beginner"])

        current_distribution = {"easy": 0, "medium": 0, "hard": 0}
        for q in questions:
            q_diff = q.get("difficulty", "beginner")
            if q_diff == "beginner":
                current_distribution["easy"] += 1
            elif q_diff == "intermediate":
                current_distribution["medium"] += 1
            else:
                current_distribution["hard"] += 1

        total = len(questions)
        if total == 0:
            return questions

        logger.info(f"题目难度调整完成,当前分布: {current_distribution}")
        return questions

    def save_exam_result(self, user_id: int, exam_id: str, result_data: Dict) -> bool:
        """保存考试结果"""
        try:
            exam_result = {
                "result_id": f"result-{uuid.uuid4().hex[:8]}",
                "exam_id": exam_id,
                "user_id": user_id,
                "score": result_data.get("score", 0),
                "total_questions": result_data.get("total_questions", 0),
                "correct_answers": result_data.get("correct_answers", 0),
                "wrong_answers": result_data.get("wrong_answers", 0),
                "skipped_questions": result_data.get("skipped_questions", 0),
                "completion_time": result_data.get("completion_time", 0),
                "started_at": result_data.get("started_at", datetime.now(UTC).isoformat()),
                "submitted_at": datetime.now(UTC).isoformat(),
                "answers": json.dumps(result_data.get("answers", [])),
                "wrong_question_ids": json.dumps(result_data.get("wrong_question_ids", [])),
                "performance_analysis": json.dumps(result_data.get("performance_analysis", {}))
            }

            from app.models.learning_system import LearningAnalytics

            conn = LearningAnalytics._connect_db()
            cursor = conn.cursor()

            cursor.execute("PRAGMA table_info(exam_results)")
            columns = [col[1] for col in cursor.fetchall()]
            if not columns:
                cursor.execute('''
                    CREATE TABLE exam_results (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        result_id TEXT UNIQUE NOT NULL,
                        exam_id TEXT NOT NULL,
                        user_id INTEGER NOT NULL,
                        score REAL NOT NULL,
                        total_questions INTEGER NOT NULL,
                        correct_answers INTEGER NOT NULL,
                        wrong_answers INTEGER NOT NULL,
                        skipped_questions INTEGER NOT NULL,
                        completion_time INTEGER NOT NULL,
                        started_at TEXT NOT NULL,
                        submitted_at TEXT NOT NULL,
                        answers TEXT NOT NULL,
                        wrong_question_ids TEXT NOT NULL,
                        performance_analysis TEXT NOT NULL,
                        FOREIGN KEY (user_id) REFERENCES users(id)
                    )
                ''')

            cursor.execute('''
                INSERT INTO exam_results (
                    result_id, exam_id, user_id, score, total_questions,
                    correct_answers, wrong_answers, skipped_questions,
                    completion_time, started_at, submitted_at, answers,
                    wrong_question_ids, performance_analysis
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                exam_result["result_id"],
                exam_result["exam_id"],
                exam_result["user_id"],
                exam_result["score"],
                exam_result["total_questions"],
                exam_result["correct_answers"],
                exam_result["wrong_answers"],
                exam_result["skipped_questions"],
                exam_result["completion_time"],
                exam_result["started_at"],
                exam_result["submitted_at"],
                exam_result["answers"],
                exam_result["wrong_question_ids"],
                exam_result["performance_analysis"]
            ))

            conn.commit()
            conn.close()

            analytics = LearningAnalytics(
                user_id=user_id,
                metric_name="exam_score",
                metric_value=exam_result["score"],
                metric_type="gauge",
                category="exam"
            )
            analytics.save()

            logger.info(f"考试结果保存成功: {exam_result['result_id']}")
            return True
        except Exception as e:
            logger.error(f"保存考试结果失败: {str(e)}")
            return False

    def get_user_exam_history(self, user_id: int, limit: int = 10, offset: int = 0) -> List[Dict]:
        """获取用户考试历史"""
        logger.info(f"获取用户 {user_id} 的考试历史,限制: {limit},偏移: {offset}")

        try:
            from app.models.learning_system import LearningAnalytics
            conn = LearningAnalytics._connect_db()
            cursor = conn.cursor()

            cursor.execute('''
                SELECT * FROM exam_results WHERE user_id=?
                ORDER BY submitted_at DESC LIMIT ? OFFSET ?
            ''', (user_id, limit, offset))

            rows = cursor.fetchall()
            conn.close()

            exam_history = []
            for row in rows:
                exam_history.append({
                    "result_id": row[1],
                    "exam_id": row[2],
                    "user_id": row[3],
                    "score": row[4],
                    "total_questions": row[5],
                    "correct_answers": row[6],
                    "wrong_answers": row[7],
                    "skipped_questions": row[8],
                    "completion_time": row[9],
                    "started_at": row[10],
                    "submitted_at": row[11],
                    "answers": json.loads(row[12]),
                    "wrong_question_ids": json.loads(row[13]),
                    "performance_analysis": json.loads(row[14])
                })

            logger.info(f"成功获取用户 {user_id} 的考试历史,共 {len(exam_history)} 条记录")
            return exam_history
        except Exception as e:
            logger.error(f"获取用户考试历史失败: {str(e)}")
            return []

    def get_exam_statistics(self, user_id: int, subject: str = None, time_range: str = "30d") -> Dict[str, Any]:
        """获取考试统计数据"""
        logger.info(f"获取用户 {user_id} 的考试统计数据,科目: {subject},时间范围: {time_range}")
        try:
            from app.models.learning_system import LearningAnalytics
            conn = LearningAnalytics._connect_db()
            cursor = conn.cursor()

            query = 'SELECT * FROM exam_results WHERE user_id=?'
            params = [user_id]

            if time_range == "7d":
                query += ' AND submitted_at >= datetime("now", "-7 days")'
            elif time_range == "30d":
                query += ' AND submitted_at >= datetime("now", "-30 days")'
            elif time_range == "90d":
                query += ' AND submitted_at >= datetime("now", "-90 days")'
            elif time_range == "1y":
                query += ' AND submitted_at >= datetime("now", "-1 year")'

            cursor.execute(query, params)
            rows = cursor.fetchall()

            total_exams = len(rows)
            if total_exams == 0:
                conn.close()
                return {
                    "total_exams": 0,
                    "average_score": 0,
                    "highest_score": 0,
                    "lowest_score": 0,
                    "pass_rate": 0,
                    "total_questions": 0,
                    "correct_answers": 0,
                    "wrong_answers": 0,
                    "skipped_questions": 0,
                    "average_completion_time": 0,
                    "score_trend": [],
                    "subject_breakdown": {},
                    "knowledge_point_analysis": {},
                    "question_type_analysis": {},
                    "difficulty_analysis": {},
                    "monthly_trend": {},
                    "performance_comparison": {}
                }

            scores = [row[4] for row in rows]
            completion_times = [row[9] for row in rows]
            total_questions = sum([row[5] for row in rows])
            correct_answers = sum([row[6] for row in rows])
            wrong_answers = sum([row[7] for row in rows])
            skipped_questions = sum([row[8] for row in rows])
            pass_count = len([score for score in scores if score >= 60])
            pass_rate = pass_count / total_exams if total_exams > 0 else 0

            score_trend = []
            for row in rows:
                analysis = json.loads(row[14])
                score_trend.append({
                    "score": row[4],
                    "exam_id": row[2],
                    "total_questions": row[5],
                    "correct_answers": row[6],
                    "wrong_answers": row[7],
                    "date": row[11]
                })

            score_trend.sort(key=lambda x: x["date"])

            knowledge_point_analysis = self._analyze_knowledge_points(rows, conn)
            question_type_analysis = self._analyze_question_types(rows, conn)
            difficulty_analysis = self._analyze_difficulty(rows, conn)
            monthly_trend = self._analyze_monthly_trend(rows)
            performance_comparison = self._analyze_performance_comparison(rows, user_id)

            conn.close()

            statistics = {
                "total_exams": total_exams,
                "average_score": sum(scores) / total_exams,
                "highest_score": max(scores),
                "lowest_score": min(scores),
                "pass_rate": pass_rate,
                "total_questions": total_questions,
                "correct_answers": correct_answers,
                "wrong_answers": wrong_answers,
                "skipped_questions": skipped_questions,
                "accuracy_rate": correct_answers / total_questions if total_questions > 0 else 0,
                "average_completion_time": sum(completion_times) / total_exams if completion_times else 0,
                "score_trend": score_trend,
                "subject_breakdown": self._analyze_subject_breakdown(rows),
                "question_type_analysis": question_type_analysis,
                "difficulty_analysis": difficulty_analysis,
                "monthly_trend": monthly_trend,
                "performance_comparison": performance_comparison
            }

            logger.info(f"成功获取用户 {user_id} 的考试统计数据")
            return statistics
        except Exception as e:
            logger.error(f"获取考试统计数据失败: {str(e)}")
            return {}

    def _analyze_subject_breakdown(self, rows: List) -> Dict[str, Dict]:
        """分析科目分布"""
        subject_stats = {}
        for row in rows:
            performance = json.loads(row[14])
            subj = performance.get("subject", "general")

            if subj not in subject_stats:
                subject_stats[subj] = {
                    "exam_count": 0,
                    "average_score": 0,
                    "total_questions": 0,
                    "correct_answers": 0
                }

            subject_stats[subj]["exam_count"] += 1
            subject_stats[subj]["average_score"] += row[4]
            subject_stats[subj]["total_questions"] += row[5]
            subject_stats[subj]["correct_answers"] += row[6]

        for subj in subject_stats:
            subject_stats[subj]["average_score"] /= subject_stats[subj]["exam_count"]
            subject_stats[subj]["accuracy"] = subject_stats[subj]["correct_answers"] / subject_stats[subj]["total_questions"]

        return subject_stats

    def _analyze_knowledge_points(self, rows: List, conn) -> Dict[str, Dict]:
        """分析知识点掌握情况"""
        knowledge_points = {}
        cursor = conn.cursor()

        for row in rows:
            wrong_question_ids = json.loads(row[13])

            for q_id in wrong_question_ids:
                cursor.execute('''
                    SELECT content, question_type, options, answer, explanation, knowledge_points FROM questions WHERE id=?
                ''', (q_id,))
                question = cursor.fetchone()

                if question and question[5]:
                    kps = json.loads(question[5]) if question[5] else []
                    for kp in kps:
                        if kp not in knowledge_points:
                            knowledge_points[kp] = {
                                "wrong_count": 0,
                                "correct_count": 0,
                                "total_count": 0
                            }
                        knowledge_points[kp]["wrong_count"] += 1

            performance = json.loads(row[14])
            correct_question_ids = performance.get("correct_question_ids", [])
            for q_id in correct_question_ids:
                cursor.execute('''
                    SELECT knowledge_points FROM questions WHERE id=?
                ''', (q_id,))
                question = cursor.fetchone()

                if question and question[0]:
                    kps = json.loads(question[0]) if question[0] else []
                    for kp in kps:
                        if kp not in knowledge_points:
                            knowledge_points[kp] = {
                                "wrong_count": 0,
                                "total_count": 0,
                                "correct_count": 0
                            }
                        knowledge_points[kp]["correct_count"] += 1

        for kp in knowledge_points:
            kp_data = knowledge_points[kp]
            kp_data["total_count"] = kp_data["correct_count"] + kp_data["wrong_count"]
            if kp_data["total_count"] > 0:
                kp_data["accuracy"] = kp_data["correct_count"] / kp_data["total_count"]
            else:
                kp_data["accuracy"] = 0

        return knowledge_points

    def _analyze_question_types(self, rows: List, conn) -> Dict[str, Dict]:
        """分析题型掌握情况"""
        question_types = {
            "single_choice": {"correct": 0, "total": 0},
            "multiple_choice": {"correct": 0, "total": 0},
            "fill_blank": {"correct": 0, "total": 0},
            "short_answer": {"correct": 0, "total": 0}
        }

        cursor = conn.cursor()
        for row in rows:
            performance = json.loads(row[14])
            if "question_type_stats" in performance:
                for q_type, stats in performance["question_type_stats"].items():
                    if q_type in question_types:
                        question_types[q_type]["correct"] += stats.get("correct", 0)
                        question_types[q_type]["total"] += stats.get("total", 0)
            else:
                all_question_ids = []
                if "wrong_question_ids" in performance:
                    all_question_ids.extend(performance["wrong_question_ids"])
                if "correct_question_ids" in performance:
                    all_question_ids.extend(performance["correct_question_ids"])

                for q_id in all_question_ids:
                    cursor.execute('''
                        SELECT question_type FROM questions WHERE id=?
                    ''', (q_id,))
                    question = cursor.fetchone()

                    if question:
                        q_type = question[0]
                        if q_type in question_types:
                            question_types[q_type]["total"] += 1

        for q_type in question_types:
            stats = question_types[q_type]
            if stats["total"] > 0:
                stats["accuracy"] = stats["correct"] / stats["total"]
            else:
                stats["accuracy"] = 0

        return question_types

    def _analyze_difficulty(self, rows: List, conn) -> Dict[str, Dict]:
        """分析不同难度级别的表现"""
        difficulty_stats = {
            "easy": {"correct": 0, "total": 0},
            "medium": {"correct": 0, "total": 0},
            "hard": {"correct": 0, "total": 0}
        }

        for row in rows:
            performance = json.loads(row[14])
            if "difficulty_stats" in performance:
                for diff, stats in performance["difficulty_stats"].items():
                    if diff in difficulty_stats:
                        difficulty_stats[diff]["correct"] += stats.get("correct", 0)
                        difficulty_stats[diff]["total"] += stats.get("total", 0)

        for diff in difficulty_stats:
            stats = difficulty_stats[diff]
            if stats["total"] > 0:
                stats["accuracy"] = stats["correct"] / stats["total"]
            else:
                stats["accuracy"] = 0

        return difficulty_stats

    def _analyze_monthly_trend(self, rows: List) -> Dict[str, Dict]:
        """分析月度趋势"""
        monthly_trend = {}

        for row in rows:
            date = datetime.fromisoformat(row[11])
            month_key = date.strftime("%Y-%m")

            if month_key not in monthly_trend:
                monthly_trend[month_key] = {
                    "exam_count": 0,
                    "average_score": 0,
                    "total_questions": 0,
                    "correct_answers": 0
                }

            monthly_trend[month_key]["exam_count"] += 1
            monthly_trend[month_key]["average_score"] += row[4]
            monthly_trend[month_key]["total_questions"] += row[5]
            monthly_trend[month_key]["correct_answers"] += row[6]

        for month, month_data in monthly_trend.items():
            if month_data["exam_count"] > 0:
                month_data["average_score"] /= month_data["exam_count"]
                month_data["accuracy"] = month_data["correct_answers"] / month_data["total_questions"] if month_data["total_questions"] > 0 else 0

        return dict(sorted(monthly_trend.items()))

    def _analyze_performance_comparison(self, rows: List, user_id: int) -> Dict[str, Any]:
        """分析性能对比(与自身历史对比)"""
        if len(rows) < 2:
            return {
                "improvement_trend": "insufficient_data",
                "score_improvement": 0,
                "accuracy_improvement": 0,
                "completion_time_improvement": 0
            }

        sorted_rows = sorted(rows, key=lambda x: x[11])

        first_exam = sorted_rows[0]
        latest_exam = sorted_rows[-1]

        score_improvement = latest_exam[4] - first_exam[4]
        first_accuracy = first_exam[6] / first_exam[5] if first_exam[5] > 0 else 0
        latest_accuracy = latest_exam[6] / latest_exam[5] if latest_exam[5] > 0 else 0
        accuracy_improvement = latest_accuracy - first_accuracy
        completion_time_improvement = first_exam[9] - latest_exam[9]

        if score_improvement > 5:
            improvement_trend = "improving"
        elif score_improvement < -5:
            improvement_trend = "declining"
        else:
            improvement_trend = "stable"

        return {
            "improvement_trend": improvement_trend,
            "score_improvement": score_improvement,
            "accuracy_improvement": accuracy_improvement,
            "completion_time_improvement": completion_time_improvement,
            "latest_exam_date": latest_exam[11]
        }

    def generate_wrong_question_practice(self, user_id: int, subject: str, count: int = 20) -> Dict[str, Any]:
        """生成错题练习试卷"""
        logger.info(f"为用户 {user_id} 生成 {subject} 错题练习试卷,数量: {count}")

        if self.exam_generator and hasattr(self.exam_generator, 'generate_wrong_question_practice'):
            return self.exam_generator.generate_wrong_question_practice(user_id, subject, count)

        return self._generate_wrong_question_practice_backup(user_id, subject, count)

    def save_exam_progress(self, user_id: int, exam_id: str, progress_data: Dict) -> bool:
        """保存考试进度"""
        try:
            from app.models.learning_system import LearningAnalytics
            conn = LearningAnalytics._connect_db()
            cursor = conn.cursor()

            cursor.execute("PRAGMA table_info(exam_progress)")
            columns = [col[1] for col in cursor.fetchall()]
            if not columns:
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS exam_progress (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        exam_id TEXT NOT NULL,
                        current_question_index INTEGER NOT NULL,
                        answers TEXT NOT NULL,
                        remaining_time INTEGER NOT NULL,
                        started_at TEXT NOT NULL,
                        last_saved_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        is_completed INTEGER DEFAULT 0,
                        FOREIGN KEY (user_id) REFERENCES users(id)
                    )
                ''')

            cursor.execute('''
                SELECT id FROM exam_progress WHERE user_id=? AND exam_id=?
            ''', (user_id, exam_id))
            existing = cursor.fetchone()

            if existing:
                cursor.execute('''
                    UPDATE exam_progress SET
                        current_question_index=?,
                        answers=?,
                        remaining_time=?,
                        last_saved_at=CURRENT_TIMESTAMP
                    WHERE id=?
                ''', (
                    progress_data.get("current_question_index", 0),
                    json.dumps(progress_data.get("answers", [])),
                    progress_data.get("remaining_time", 0),
                    existing[0]
                ))
                logger.info(f"更新考试进度成功: {exam_id}")
            else:
                cursor.execute('''
                    INSERT INTO exam_progress (
                        user_id, exam_id, current_question_index, answers, 
                        remaining_time, started_at, last_saved_at
                    ) VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ''', (
                    user_id,
                    exam_id,
                    progress_data.get("current_question_index", 0),
                    json.dumps(progress_data.get("answers", [])),
                    progress_data.get("remaining_time", 0),
                    progress_data.get("started_at", datetime.now(UTC).isoformat())
                ))
                logger.info(f"创建考试进度成功: {exam_id}")

            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"保存考试进度失败: {str(e)}")
            return False

    def restore_exam_progress(self, user_id: int, exam_id: str) -> Optional[Dict]:
        """恢复考试进度"""
        logger.info(f"恢复用户 {user_id} 的考试 {exam_id} 进度")
        try:
            from app.models.learning_system import LearningAnalytics
            conn = LearningAnalytics._connect_db()
            cursor = conn.cursor()

            cursor.execute('''
                SELECT * FROM exam_progress WHERE user_id=? AND exam_id=?
            ''', (user_id, exam_id))

            row = cursor.fetchone()
            conn.close()

            if row:
                progress_data = {
                    "id": row[0],
                    "user_id": row[1],
                    "exam_id": row[2],
                    "current_question_index": row[3],
                    "answers": json.loads(row[4]),
                    "remaining_time": row[5],
                    "started_at": row[6],
                    "last_saved_at": row[7],
                    "is_completed": row[8]
                }
                logger.info(f"成功恢复考试进度: {exam_id}")
                return progress_data

            logger.info(f"未找到考试进度: {exam_id}")
            return None
        except Exception as e:
            logger.error(f"恢复考试进度失败: {str(e)}")
            return None

    def get_user_saved_progress(self, user_id: int) -> List[Dict]:
        """获取用户所有保存的考试进度"""
        try:
            from app.models.learning_system import LearningAnalytics
            conn = LearningAnalytics._connect_db()
            cursor = conn.cursor()

            cursor.execute('''
                SELECT * FROM exam_progress WHERE user_id=? AND is_completed=0
            ''', (user_id,))

            rows = cursor.fetchall()
            conn.close()

            progress_list = []
            for row in rows:
                progress_list.append({
                    "user_id": row[1],
                    "exam_id": row[2],
                    "current_question_index": row[3],
                    "answers": json.loads(row[4]),
                    "remaining_time": row[5],
                    "last_saved_at": row[7]
                })

            logger.info(f"成功获取 {len(progress_list)} 条保存的考试进度")
            return progress_list
        except Exception as e:
            logger.error(f"获取保存的考试进度失败: {str(e)}")
            return []

    def mark_exam_completed(self, user_id: int, exam_id: str) -> bool:
        """标记考试进度为已完成"""
        logger.info(f"标记用户 {user_id} 的考试 {exam_id} 进度为已完成")
        try:
            from app.models.learning_system import LearningAnalytics
            conn = LearningAnalytics._connect_db()
            cursor = conn.cursor()

            cursor.execute('''
                UPDATE exam_progress SET is_completed=1, last_saved_at=CURRENT_TIMESTAMP
                WHERE user_id=? AND exam_id=?
            ''', (user_id, exam_id))

            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"标记考试进度为已完成失败: {str(e)}")
            return False

    def get_user_wrong_question_book(self, user_id: int, subject: str = None, 
                                      limit: int = 20, offset: int = 0) -> List[Dict]:
        """获取用户错题本"""
        logger.info(f"获取用户 {user_id} 的错题本,科目: {subject},限制: {limit},偏移: {offset}")

        try:
            from app.models.learning_system import LearningAnalytics
            from collections import Counter

            conn = LearningAnalytics._connect_db()
            cursor = conn.cursor()

            query = '''
                SELECT wrong_question_ids FROM exam_results WHERE user_id=?
                ORDER BY submitted_at DESC
            '''
            params = [user_id]

            cursor.execute(query, params)
            rows = cursor.fetchall()

            all_wrong_question_ids = []
            for row in rows:
                wrong_question_ids = json.loads(row[0])
                all_wrong_question_ids.extend(wrong_question_ids)

            if not all_wrong_question_ids:
                conn.close()
                return []

            wrong_question_counts = Counter(all_wrong_question_ids)
            top_wrong_questions = wrong_question_counts.most_common(limit + offset)[offset:]

            wrong_question_book = []
            for q_id, count in top_wrong_questions:
                cursor.execute('''
                    SELECT id, content, question_type, options, answer, explanation, knowledge_points
                    FROM questions WHERE id=?
                ''', (q_id,))
                question = cursor.fetchone()

                if question:
                    wrong_question_book.append({
                        "question_id": question[0],
                        "content": question[1],
                        "question_type": question[2],
                        "options": json.loads(question[3]) if question[3] else [],
                        "correct_answer": question[4],
                        "explanation": question[5],
                        "knowledge_points": json.loads(question[6]) if question[6] else [],
                        "wrong_count": count
                    })

            conn.close()
            logger.info(f"成功获取用户 {user_id} 的错题本,共 {len(wrong_question_book)} 道错题")
            return wrong_question_book
        except Exception as e:
            logger.error(f"获取错题本失败: {str(e)}")
            return []

    def remove_from_wrong_question_book(self, user_id: int, question_id: str) -> bool:
        """从错题本中移除特定题目"""
        logger.info(f"从用户 {user_id} 的错题本中移除题目 {question_id}")

        try:
            from app.models.learning_system import LearningAnalytics
            conn = LearningAnalytics._connect_db()
            cursor = conn.cursor()

            cursor.execute('''
                SELECT id, wrong_question_ids FROM exam_results WHERE user_id=?
            ''', (user_id,))
            rows = cursor.fetchall()

            for row in rows:
                result_id = row[0]
                wrong_ids = json.loads(row[1])
                if question_id in wrong_ids:
                    wrong_ids.remove(question_id)
                    cursor.execute('''
                        UPDATE exam_results SET wrong_question_ids=? WHERE id=?
                    ''', (json.dumps(wrong_ids), result_id))

            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"从错题本中移除题目失败: {str(e)}")
            return False

    def _generate_wrong_question_practice_backup(self, user_id: int, subject: str, count: int) -> Dict[str, Any]:
        """备用的错题练习生成方法"""
        logger.info(f"使用备用方法为用户 {user_id} 生成 {subject} 错题练习试卷")

        exam = {
            "exam_id": f"exam-{uuid.uuid4().hex[:8]}",
            "user_id": user_id,
            "subject": subject,
            "title": f"{subject}错题练习",
            "total_questions": count,
            "time_limit": 60,
            "generated_at": datetime.now(UTC).isoformat(),
            "questions": [],
            "exam_type": "wrong_question_practice"
        }

        wrong_questions = []
        try:
            from app.models.learning_system import LearningAnalytics
            conn = LearningAnalytics._connect_db()
            cursor = conn.cursor()

            cursor.execute('''
                SELECT wrong_question_ids FROM exam_results WHERE user_id=?
                ORDER BY submitted_at DESC LIMIT 5
            ''', (user_id,))
            rows = cursor.fetchall()
            conn.close()

            all_wrong_question_ids = []
            for row in rows:
                wrong_question_ids = json.loads(row[0])
                all_wrong_question_ids.extend(wrong_question_ids)

            unique_wrong_question_ids = list(set(all_wrong_question_ids))

            for question_id in unique_wrong_question_ids[:count]:
                question = self._get_question_by_id(question_id)
                if question:
                    wrong_questions.append(question)

        except Exception as e:
            logger.error(f"获取用户错题失败: {str(e)}")

        if len(wrong_questions) < count:
            remaining_count = count - len(wrong_questions)
            additional_questions = self._get_questions_from_db(
                subject=subject,
                difficulty="medium",
                question_type="single_choice",
                count=remaining_count
            )
            wrong_questions.extend(additional_questions)

        exam["questions"] = wrong_questions[:count]
        return exam

    def _get_question_by_id(self, question_id: str) -> Optional[Dict]:
        """根据ID获取题目"""
        try:
            if self.question_manager and hasattr(self.question_manager, 'get_question'):
                question = self.question_manager.get_question(question_id)
                return question.to_dict() if hasattr(question, 'to_dict') else dict(question)
        except Exception as e:
            logger.error(f"获取题目失败: {str(e)}")
        return None

    def get_practice_suggestions(self, user_id: int, subject: str) -> List[Dict]:
        """获取练习建议"""
        if self.exam_generator and hasattr(self.exam_generator, 'get_practice_suggestions'):
            return self.exam_generator.get_practice_suggestions(user_id, subject)

        return [
            {
                "type": "practice_more",
                "reason": "建议多进行练习,提高知识掌握程度",
                "subject": subject
            }
        ]

    def export_exam_result(self, result_id: str, export_format: str = "json") -> Optional[Any]:
        """导出考试结果"""
        logger.info(f"导出考试结果 {result_id},格式: {export_format}")

        try:
            from app.models.learning_system import LearningAnalytics
            import csv
            from io import StringIO

            conn = LearningAnalytics._connect_db()
            cursor = conn.cursor()

            cursor.execute('SELECT * FROM exam_results WHERE result_id=?', (result_id,))
            row = cursor.fetchone()
            conn.close()

            if not row:
                logger.error(f"考试结果 {result_id} 不存在")
                return None

            exam_result = {
                "result_id": row[1],
                "exam_id": row[2],
                "user_id": row[3],
                "score": row[4],
                "total_questions": row[5],
                "correct_answers": row[6],
                "wrong_answers": row[7],
                "skipped_questions": row[8],
                "completion_time": row[9],
                "started_at": row[10],
                "submitted_at": row[11],
                "answers": json.loads(row[12]),
                "wrong_question_ids": json.loads(row[13]),
                "performance_analysis": json.loads(row[14])
            }

            if export_format == "json":
                return json.dumps(exam_result, ensure_ascii=False, indent=2)
            elif export_format == "csv":
                csv_output = StringIO()
                writer = csv.writer(csv_output)

                writer.writerow(["字段", "值"])
                writer.writerow(["结果ID", exam_result["result_id"]])
                writer.writerow(["考试ID", exam_result["exam_id"]])
                writer.writerow(["用户ID", exam_result["user_id"]])
                writer.writerow(["得分", exam_result["score"]])
                writer.writerow(["总题数", exam_result["total_questions"]])
                writer.writerow(["正确答案数", exam_result["correct_answers"]])
                writer.writerow(["错误答案数", exam_result["wrong_answers"]])
                writer.writerow(["跳过题数", exam_result["skipped_questions"]])
                writer.writerow(["完成时间(秒)", exam_result["completion_time"]])
                writer.writerow(["开始时间", exam_result["started_at"]])
                writer.writerow(["提交时间", exam_result["submitted_at"]])

                return csv_output.getvalue()
        except Exception as e:
            logger.error(f"导出考试结果失败: {str(e)}")
            return None

    def batch_import_questions(self, questions_data: List[Dict]) -> Dict[str, Any]:
        """批量导入题目"""
        logger.info(f"批量导入 {len(questions_data)} 道题目")

        success_count = 0
        error_count = 0
        errors = []

        for question_data in questions_data:
            try:
                if not self._validate_question_data(question_data):
                    error_count += 1
                    errors.append(f"题目数据验证失败: {str(question_data)[:100]}...")
                    continue

                if self.question_manager and hasattr(self.question_manager, 'create_question'):
                    self.question_manager.create_question(
                        content=question_data["content"],
                        answer=question_data["answer"],
                        explanation=question_data.get("explanation"),
                        category_id=question_data.get("category_id"),
                        options=question_data.get("options", []),
                        question_type=question_data.get("question_type", "single_choice")
                    )
                    success_count += 1
            except Exception as e:
                error_count += 1
                errors.append(f"导入题目失败: {str(e)}")

        return {
            "success_count": success_count,
            "error_count": error_count,
            "errors": errors
        }

    def _validate_question_data(self, question_data: Dict) -> bool:
        """验证题目数据"""
        required_fields = ["content", "answer"]
        for field in required_fields:
            if field not in question_data:
                return False

        valid_question_types = ["single_choice", "multiple_choice", "true_false", "fill_blank", "short_answer"]
        question_type = question_data.get("question_type", "single_choice")
        if question_type not in valid_question_types:
            return False

        if question_type in ["single_choice", "multiple_choice"] and not question_data.get("options"):
            return False

        return True

    def generate_question_bank_report(self) -> Dict[str, Any]:
        """生成题库报告"""
        logger.info("生成题库报告")

        try:
            from app.models.learning_system import LearningAnalytics
            conn = LearningAnalytics._connect_db()
            cursor = conn.cursor()

            cursor.execute('SELECT COUNT(*) FROM questions')
            total_questions = cursor.fetchone()[0]

            cursor.execute('SELECT question_type, COUNT(*) FROM questions GROUP BY question_type')
            type_distribution = {row[0]: row[1] for row in cursor.fetchall()}

            cursor.execute('SELECT difficulty, COUNT(*) FROM questions GROUP BY difficulty')
            level_distribution = {row[0]: row[1] for row in cursor.fetchall()}

            cursor.execute('SELECT category_id, COUNT(*) FROM questions GROUP BY category_id')
            category_distribution = {row[0]: row[1] for row in cursor.fetchall()}

            cursor.execute('SELECT language_id, COUNT(*) FROM questions GROUP BY language_id')
            language_distribution = {row[0]: row[1] for row in cursor.fetchall()}

            conn.close()

            category_names = {}
            level_names = {}
            language_names = {}

            try:
                if self.question_manager:
                    categories = getattr(self.question_manager, 'get_all_categories', lambda: [])()
                    category_names = {cat.id: cat.name for cat in categories if hasattr(cat, 'id') and hasattr(cat, 'name')}

                    levels = getattr(self.question_manager, 'get_all_levels', lambda: [])()
                    level_names = {level.id: level.name for level in levels if hasattr(level, 'id') and hasattr(level, 'name')}

                    languages = getattr(self.question_manager, 'get_all_languages', lambda: [])()
                    language_names = {lang.id: lang.name for lang in languages if hasattr(lang, 'id') and hasattr(lang, 'name')}
            except Exception as e:
                logger.warning(f"获取分类信息失败: {str(e)}")

            return {
                "total_questions": total_questions,
                "type_distribution": type_distribution,
                "level_distribution": level_distribution,
                "category_distribution": category_distribution,
                "language_distribution": language_distribution,
                "category_names": category_names,
                "level_names": level_names,
                "language_names": language_names,
                "generated_at": datetime.now(UTC).isoformat()
            }
        except Exception as e:
            logger.error(f"生成题库报告失败: {str(e)}")
            return {}


# 全局实例
exam_system_manager = ExamSystemManager()
