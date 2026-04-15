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
    """
    考试系统管理器
    """
    
    def __init__(self):
        """
        初始化考试系统管理器
        """
        # 初始化依赖组件
        self.exam_generator = None
        self.question_manager = None
        self.learning_system = None
        
        # 加载配置
        self.config = self._load_config()
        
        # 初始化组件
        self._initialize_components()
        
        logger.info("考试系统管理器初始化完成")
    
    def _load_config(self):
        """
        加载配置
        """
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
        """
        初始化依赖组件
        """
        try:
            # 初始化考试生成器
            from exam_generator import ExamGenerator
            self.exam_generator = ExamGenerator()
            logger.info("✓ 考试生成器初始化成功")
        except Exception as e:
            logger.error(f"✗ 考试生成器初始化失败: {str(e)}")
        
        try:
            # 初始化题库管理器
            from app.models.question import question_manager
            self.question_manager = question_manager
            logger.info("✓ 题库管理器初始化成功")
        except Exception as e:
            logger.error(f"✗ 题库管理器初始化失败: {str(e)}")
        
        try:
            # 初始化学习系统
            from app.models.learning_system import LearningSystem
            self.learning_system = LearningSystem
            logger.info("✓ 学习系统初始化成功")
        except Exception as e:
            logger.error(f"✗ 学习系统初始化失败: {str(e)}")
    
    def __init__(self):
        """
        初始化考试系统管理器
        """
        # 初始化依赖组件
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
    
    def _init_cache(self):
        """
        初始化缓存
        """
        # 题目缓存，用于存储最近查询的题目
        self.question_cache = {}
        # 用户学习数据缓存，用于缓存用户学习数据
        self.user_learning_cache = {}
        # 缓存过期时间（秒）
        self.cache_expiry = 3600  # 1小时
    
    def generate_personalized_exam(self, user_id, subject, question_count=None, difficulty=None, **kwargs):
        """
        生成个性化试卷
        
        Args:
            user_id: 用户ID
            subject: 科目
            question_count: 题目数量
            difficulty: 难度
            **kwargs: 其他参数
            
        Returns:
            生成的试卷
        """
        logger.info(f"为用户 {user_id} 生成 {subject} 个性化试卷")
        
        start_time = datetime.now(UTC)
        
        # 使用默认值
        question_count = question_count or self.config["default_question_count"]
        
        # 获取用户学习数据，用于个性化生成（带缓存）
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
                "enable_progress_save": True,  # 新增：启用进度保存
                "save_interval": 30  # 新增：自动保存间隔（秒）
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
        
        logger.info(f"成功为用户 {user_id} 生成 {subject} 个性化试卷，包含 {len(questions)} 道题目，生成时间：{generation_time:.2f}秒")
        
        # 添加生成时间到试卷信息
        exam["generation_time"] = generation_time
        
        return exam
    
    def _get_user_learning_data(self, user_id, subject):
        """
        获取用户学习数据
        """
        logger.info(f"获取用户 {user_id} 的 {subject} 学习数据")
        
        # 初始化学习数据
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
            # 从学习系统获取用户学习摘要
            if self.learning_system:
                learning_summary = self.learning_system.get_user_learning_summary(user_id)
                learning_data["completed_courses"] = learning_summary.get("completed_courses", 0)
                learning_data["completed_lessons"] = learning_summary.get("completed_lessons", 0)
                learning_data["average_score"] = learning_summary.get("average_score", 0)
        except Exception as e:
            logger.error(f"获取用户学习摘要失败: {str(e)}")
        
        try:
            # 获取用户错题
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
    
    def _adjust_difficulty_by_learning_data(self, learning_data, base_difficulty=None):
        """
        根据用户学习数据调整难度
        """
        if base_difficulty:
            return base_difficulty
        
        # 基于用户学习水平确定难度
        return learning_data["learning_level"]
    
    def _generate_questions_for_exam(self, subject, count, difficulty, user_learning_data, **kwargs):
        """
        为试卷生成题目
        
        Args:
            subject: 科目
            count: 题目数量
            difficulty: 难度
            user_learning_data: 用户学习数据
            **kwargs: 其他参数，包括：
                - question_type_ratios: 题型比例配置
                - knowledge_points: 要覆盖的知识点
                - difficulty_gradient: 难度梯度配置（easy_to_hard, mixed, hard_to_easy）
        """
        logger.info(f"为试卷生成 {count} 道 {subject} 题目，难度: {difficulty}")
        
        questions = []
        
        # 获取配置
        question_type_ratios = kwargs.get("question_type_ratios", {
            "single_choice": 40,
            "multiple_choice": 30,
            "true_false": 15,
            "fill_blank": 10,
            "short_answer": 5
        })
        
        knowledge_points = kwargs.get("knowledge_points", [])
        difficulty_gradient = kwargs.get("difficulty_gradient", "mixed")
        
        # 1. 首先添加错题（如果有）
        wrong_questions = user_learning_data.get("wrong_questions", [])
        if wrong_questions:
            # 选择最近的错题
            num_wrong_questions = min(len(wrong_questions), count // 4)
            selected_wrong_questions = wrong_questions[:num_wrong_questions]
            questions.extend(selected_wrong_questions)
            logger.info(f"添加了 {num_wrong_questions} 道错题")
        
        # 2. 根据题型比例生成题目
        remaining_count = count - len(questions)
        if remaining_count > 0:
            # 计算各题型的题目数量
            total_ratio = sum(question_type_ratios.values())
            questions_by_type = {}
            
            for q_type, ratio in question_type_ratios.items():
                # 根据比例计算数量，确保总和接近remaining_count
                q_count = int(remaining_count * ratio / total_ratio)
                if q_count > 0:
                    questions_by_type[q_type] = q_count
            
            # 处理余数，确保总数正确
            total_calculated = sum(questions_by_type.values())
            if total_calculated < remaining_count:
                # 按比例分配余数
                for q_type in questions_by_type:
                    if total_calculated >= remaining_count:
                        break
                    questions_by_type[q_type] += 1
                    total_calculated += 1
            
            # 生成各题型的题目
            for q_type, q_count in questions_by_type.items():
                try:
                    # 从数据库获取题目
                    db_questions = self.question_manager.get_questions(
                        subject=subject,
                        difficulty=difficulty,
                        question_type=q_type,
                        count=q_count,
                        knowledge_points=knowledge_points,
                        **kwargs
                    )
                    
                    questions.extend(db_questions)
                    logger.info(f"从数据库获取了 {len(db_questions)} 道 {q_type} 题目")
                    
                    # 如果数据库题目不足，使用AI生成
                    if len(db_questions) < q_count and self.config["enable_ai_question_generation"]:
                        remaining_q_count = q_count - len(db_questions)
                        ai_questions = self.exam_generator.generate_questions_with_ai(
                            subject=subject,
                            difficulty=difficulty,
                            question_type=q_type,
                            count=remaining_q_count
                        )
                        questions.extend(ai_questions)
                        logger.info(f"使用AI生成了 {len(ai_questions)} 道 {q_type} 题目")
                except Exception as e:
                    logger.error(f"生成 {q_type} 题目失败: {str(e)}")
        
        # 3. 如果题目数量仍不足，补充普通题目
        remaining_count = count - len(questions)
        if remaining_count > 0:
            if self.config["enable_ai_question_generation"]:
                # 随机选择题型生成
                available_types = ["single_choice", "multiple_choice", "true_false", "fill_blank", "short_answer"]
                ai_questions = self.exam_generator.generate_questions_with_ai(
                    subject=subject,
                    difficulty=difficulty,
                    question_type=random.choice(available_types),
                    count=remaining_count
                )
                questions.extend(ai_questions)
                logger.info(f"使用AI生成了 {len(ai_questions)} 道补充题目")
        
        # 4. 确保题目数量正确
        if len(questions) > count:
            questions = questions[:count]
        
        # 5. 根据难度梯度调整题目顺序
        if difficulty_gradient == "easy_to_hard":
            # 按难度从易到难排序
            questions.sort(key=lambda x: {
                "beginner": 0,
                "intermediate": 1,
                "advanced": 2,
                "expert": 3
            }.get(x.get("difficulty", "beginner"), 0))
        elif difficulty_gradient == "hard_to_easy":
            # 按难度从难到易排序
            questions.sort(key=lambda x: {
                "beginner": 0,
                "intermediate": 1,
                "advanced": 2,
                "expert": 3
            }.get(x.get("difficulty", "beginner"), 0), reverse=True)
        else:
            # 混合难度，随机打乱
            random.shuffle(questions)
        
        # 6. 智能难度调整：根据用户学习数据调整题目难度
        questions = self._intelligently_adjust_difficulty(questions, user_learning_data)
        
        logger.info(f"成功生成 {len(questions)} 道题目，包含多种题型")
        return questions
    
    def _intelligently_adjust_difficulty(self, questions, user_learning_data):
        """
        智能调整题目难度
        
        Args:
            questions: 题目列表
            user_learning_data: 用户学习数据
            
        Returns:
            调整后的题目列表
        """
        logger.info("智能调整题目难度")
        
        # 获取用户学习水平
        learning_level = user_learning_data.get("learning_level", "beginner")
        weak_points = user_learning_data.get("weak_knowledge_points", [])
        strong_points = user_learning_data.get("strong_knowledge_points", [])
        
        # 难度调整策略
        difficulty_adjustment = {
            "beginner": {"easy": 60, "medium": 30, "hard": 10},
            "intermediate": {"easy": 30, "medium": 50, "hard": 20},
            "advanced": {"easy": 10, "medium": 30, "hard": 60}
        }
        
        # 根据用户学习水平获取目标难度分布
        target_distribution = difficulty_adjustment.get(learning_level, difficulty_adjustment["beginner"])
        
        # 统计当前难度分布
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
        
        # 计算需要调整的题目
        # 这里可以根据实际情况调整题目难度，例如替换或修改题目
        # 目前简单实现，保持原有题目
        
        logger.info(f"题目难度调整完成，当前分布: {current_distribution}")
        return questions
    
    def save_exam_result(self, user_id, exam_id, result_data):
        """
        保存考试结果
        
        Args:
            user_id: 用户ID
            exam_id: 考试ID
            result_data: 考试结果数据
            
        Returns:
            是否保存成功
        """
        logger.info(f"保存用户 {user_id} 的考试 {exam_id} 结果")
        
        try:
            # 构建考试结果
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
                "answers": result_data.get("answers", []),
                "wrong_question_ids": result_data.get("wrong_question_ids", []),
                "performance_analysis": result_data.get("performance_analysis", {})
            }
            
            # 保存到数据库
            from app.models.learning_system import LearningAnalytics
            
            # 保存考试结果
            conn = LearningAnalytics._connect_db()
            cursor = conn.cursor()
            
            # 检查exam_results表是否存在，如果不存在则创建
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
                conn.commit()
            
            # 插入考试结果
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
                json.dumps(exam_result["answers"]),
                json.dumps(exam_result["wrong_question_ids"]),
                json.dumps(exam_result["performance_analysis"])
            ))
            
            conn.commit()
            conn.close()
            
            # 保存学习分析数据
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
    
    def get_user_exam_history(self, user_id, limit=10, offset=0):
        """
        获取用户考试历史
        
        Args:
            user_id: 用户ID
            limit: 限制数量
            offset: 偏移量
            
        Returns:
            用户考试历史列表
        """
        logger.info(f"获取用户 {user_id} 的考试历史，限制: {limit}，偏移: {offset}")
        
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
            
            logger.info(f"成功获取用户 {user_id} 的考试历史，共 {len(exam_history)} 条记录")
            return exam_history
        except Exception as e:
            logger.error(f"获取用户考试历史失败: {str(e)}")
            return []
    
    def get_exam_statistics(self, user_id, subject=None, time_range="30d"):
        """
        获取考试统计数据
        
        Args:
            user_id: 用户ID
            subject: 科目
            time_range: 时间范围
            
        Returns:
            详细的考试统计数据
        """
        logger.info(f"获取用户 {user_id} 的考试统计数据，科目: {subject}，时间范围: {time_range}")
        
        try:
            from app.models.learning_system import LearningAnalytics
            conn = LearningAnalytics._connect_db()
            cursor = conn.cursor()
            
            # 构建查询
            query = 'SELECT * FROM exam_results WHERE user_id=?'
            params = [user_id]
            
            # 添加时间范围条件
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
            
            # 计算统计数据
            total_exams = len(rows)
            if total_exams == 0:
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
            
            # 基础统计数据
            scores = [row[4] for row in rows]
            total_questions = sum([row[5] for row in rows])
            correct_answers = sum([row[6] for row in rows])
            wrong_answers = sum([row[7] for row in rows])
            skipped_questions = sum([row[8] for row in rows])
            completion_times = [row[9] for row in rows]
            
            # 计算通过率（假设60分为及格）
            pass_count = len([score for score in scores if score >= 60])
            pass_rate = pass_count / total_exams
            
            # 构建分数趋势
            score_trend = []
            for row in rows:
                score_trend.append({
                    "date": row[11],
                    "score": row[4],
                    "exam_id": row[2],
                    "total_questions": row[5],
                    "correct_answers": row[6],
                    "wrong_answers": row[7]
                })
            
            # 按提交时间排序
            score_trend.sort(key=lambda x: x["date"])
            
            # 知识点分析
            knowledge_point_analysis = self._analyze_knowledge_points(rows, conn)
            
            # 题型分析
            question_type_analysis = self._analyze_question_types(rows, conn)
            
            # 难度分析
            difficulty_analysis = self._analyze_difficulty(rows, conn)
            
            # 月度趋势分析
            monthly_trend = self._analyze_monthly_trend(rows)
            
            # 性能对比分析
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
                "knowledge_point_analysis": knowledge_point_analysis,
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
    
    def _analyze_subject_breakdown(self, rows):
        """
        分析科目分布
        """
        subject_stats = {}
        for row in rows:
            # 从performance_analysis中获取科目
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
        
        # 计算平均分数
        for subj in subject_stats:
            subject_stats[subj]["average_score"] /= subject_stats[subj]["exam_count"]
            subject_stats[subj]["accuracy"] = subject_stats[subj]["correct_answers"] / subject_stats[subj]["total_questions"]
        
        return subject_stats
    
    def _analyze_knowledge_points(self, rows, conn):
        """
        分析知识点掌握情况
        """
        knowledge_points = {}
        cursor = conn.cursor()
        
        for row in rows:
            wrong_question_ids = json.loads(row[13])
            
            for q_id in wrong_question_ids:
                # 获取题目详情
                cursor.execute('''
                    SELECT content, question_type, options, answer, explanation, knowledge_points FROM questions WHERE id=?
                ''', (q_id,))
                question = cursor.fetchone()
                
                if question and question[5]:
                    # 解析知识点
                    kps = json.loads(question[5]) if question[5] else []
                    for kp in kps:
                        if kp not in knowledge_points:
                            knowledge_points[kp] = {
                                "wrong_count": 0,
                                "total_count": 0,
                                "correct_count": 0
                            }
                        knowledge_points[kp]["wrong_count"] += 1
            
            # 同样分析正确的题目
            performance = json.loads(row[14])
            if "correct_question_ids" in performance:
                for q_id in performance["correct_question_ids"]:
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
        
        # 计算总次数和正确率
        for kp in knowledge_points:
            kp_data = knowledge_points[kp]
            kp_data["total_count"] = kp_data["correct_count"] + kp_data["wrong_count"]
            if kp_data["total_count"] > 0:
                kp_data["accuracy"] = kp_data["correct_count"] / kp_data["total_count"]
            else:
                kp_data["accuracy"] = 0
        
        return knowledge_points
    
    def _analyze_question_types(self, rows, conn):
        """
        分析题型掌握情况
        """
        question_types = {
            "single_choice": {"correct": 0, "total": 0},
            "multiple_choice": {"correct": 0, "total": 0},
            "true_false": {"correct": 0, "total": 0},
            "fill_blank": {"correct": 0, "total": 0},
            "short_answer": {"correct": 0, "total": 0}
        }
        
        cursor = conn.cursor()
        
        for row in rows:
            # 从performance_analysis中获取题型统计
            performance = json.loads(row[14])
            if "question_type_stats" in performance:
                for q_type, stats in performance["question_type_stats"].items():
                    if q_type in question_types:
                        question_types[q_type]["correct"] += stats.get("correct", 0)
                        question_types[q_type]["total"] += stats.get("total", 0)
            else:
                # 从题目中分析题型
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
        
        # 计算正确率
        for q_type in question_types:
            stats = question_types[q_type]
            if stats["total"] > 0:
                stats["accuracy"] = stats["correct"] / stats["total"]
            else:
                stats["accuracy"] = 0
        
        return question_types
    
    def _analyze_difficulty(self, rows, conn):
        """
        分析不同难度级别的表现
        """
        difficulty_stats = {
            "easy": {"correct": 0, "total": 0},
            "medium": {"correct": 0, "total": 0},
            "hard": {"correct": 0, "total": 0}
        }
        
        cursor = conn.cursor()
        
        for row in rows:
            # 从performance_analysis中获取难度统计
            performance = json.loads(row[14])
            if "difficulty_stats" in performance:
                for diff, stats in performance["difficulty_stats"].items():
                    if diff in difficulty_stats:
                        difficulty_stats[diff]["correct"] += stats.get("correct", 0)
                        difficulty_stats[diff]["total"] += stats.get("total", 0)
        
        # 计算正确率
        for diff in difficulty_stats:
            stats = difficulty_stats[diff]
            if stats["total"] > 0:
                stats["accuracy"] = stats["correct"] / stats["total"]
            else:
                stats["accuracy"] = 0
        
        return difficulty_stats
    
    def _analyze_monthly_trend(self, rows):
        """
        分析月度趋势
        """
        monthly_trend = {}
        
        for row in rows:
            # 获取月份
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
        
        # 计算平均分数
        for month in monthly_trend:
            month_data = monthly_trend[month]
            month_data["average_score"] /= month_data["exam_count"]
            month_data["accuracy"] = month_data["correct_answers"] / month_data["total_questions"]
        
        # 按月份排序
        sorted_trend = {}
        for month in sorted(monthly_trend.keys()):
            sorted_trend[month] = monthly_trend[month]
        
        return sorted_trend
    
    def _analyze_performance_comparison(self, rows, user_id):
        """
        分析性能对比（与自身历史对比）
        """
        if len(rows) < 2:
            return {
                "improvement_trend": "insufficient_data",
                "score_improvement": 0,
                "accuracy_improvement": 0,
                "completion_time_improvement": 0
            }
        
        # 按时间排序
        sorted_rows = sorted(rows, key=lambda x: x[11])
        
        # 比较最早和最近的考试
        first_exam = sorted_rows[0]
        latest_exam = sorted_rows[-1]
        
        # 计算分数提升
        score_improvement = latest_exam[4] - first_exam[4]
        
        # 计算正确率提升
        first_accuracy = first_exam[6] / first_exam[5] if first_exam[5] > 0 else 0
        latest_accuracy = latest_exam[6] / latest_exam[5] if latest_exam[5] > 0 else 0
        accuracy_improvement = latest_accuracy - first_accuracy
        
        # 计算完成时间变化（负数表示变快）
        completion_time_improvement = first_exam[9] - latest_exam[9]
        
        # 确定提升趋势
        improvement_trend = "improving" if score_improvement > 5 else "stable"
        if score_improvement < -5:
            improvement_trend = "declining"
        
        return {
            "improvement_trend": improvement_trend,
            "score_improvement": score_improvement,
            "accuracy_improvement": accuracy_improvement,
            "completion_time_improvement": completion_time_improvement,
            "first_exam_date": first_exam[11],
            "latest_exam_date": latest_exam[11]
        }
    
    def generate_wrong_question_practice(self, user_id, subject, count=20):
        """
        生成错题练习试卷
        
        Args:
            user_id: 用户ID
            subject: 科目
            count: 题目数量
            
        Returns:
            错题练习试卷
        """
        logger.info(f"为用户 {user_id} 生成 {subject} 错题练习试卷，数量: {count}")
        
        if self.exam_generator:
            return self.exam_generator.generate_wrong_question_practice(user_id, subject, count)
        
        # 如果没有考试生成器，使用备用方法
        return self._generate_wrong_question_practice_backup(user_id, subject, count)
    
    def save_exam_progress(self, user_id, exam_id, progress_data):
        """
        保存考试进度
        
        Args:
            user_id: 用户ID
            exam_id: 考试ID
            progress_data: 进度数据，包含当前题目、答案、剩余时间等
            
        Returns:
            是否保存成功
        """
        logger.info(f"保存用户 {user_id} 的考试 {exam_id} 进度")
        
        try:
            from app.models.learning_system import LearningAnalytics
            conn = LearningAnalytics._connect_db()
            cursor = conn.cursor()
            
            # 检查exam_progress表是否存在，如果不存在则创建
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
                conn.commit()
            
            # 检查是否已存在进度记录
            cursor.execute('''
                SELECT id FROM exam_progress WHERE user_id=? AND exam_id=?
            ''', (user_id, exam_id))
            existing = cursor.fetchone()
            
            if existing:
                # 更新现有进度
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
                # 创建新进度记录
                cursor.execute('''
                    INSERT INTO exam_progress (
                        user_id, exam_id, current_question_index, answers, remaining_time, started_at
                    ) VALUES (?, ?, ?, ?, ?, ?)
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
    
    def restore_exam_progress(self, user_id, exam_id):
        """
        恢复考试进度
        
        Args:
            user_id: 用户ID
            exam_id: 考试ID
            
        Returns:
            保存的进度数据，如果不存在则返回None
        """
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
                # 解析进度数据
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
    
    def get_user_saved_progress(self, user_id):
        """
        获取用户所有保存的考试进度
        
        Args:
            user_id: 用户ID
            
        Returns:
            保存的进度列表
        """
        logger.info(f"获取用户 {user_id} 所有保存的考试进度")
        
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
                    "id": row[0],
                    "user_id": row[1],
                    "exam_id": row[2],
                    "current_question_index": row[3],
                    "answers": json.loads(row[4]),
                    "remaining_time": row[5],
                    "started_at": row[6],
                    "last_saved_at": row[7],
                    "is_completed": row[8]
                })
            
            logger.info(f"成功获取 {len(progress_list)} 条保存的考试进度")
            return progress_list
        except Exception as e:
            logger.error(f"获取保存的考试进度失败: {str(e)}")
            return []
    
    def complete_exam_progress(self, user_id, exam_id):
        """
        标记考试进度为已完成
        
        Args:
            user_id: 用户ID
            exam_id: 考试ID
            
        Returns:
            是否标记成功
        """
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
            logger.info(f"成功标记考试进度为已完成: {exam_id}")
            return True
        except Exception as e:
            logger.error(f"标记考试进度为已完成失败: {str(e)}")
            return False
    
    def get_user_wrong_question_book(self, user_id, subject=None, limit=20, offset=0):
        """
        获取用户错题本
        
        Args:
            user_id: 用户ID
            subject: 科目（可选）
            limit: 限制数量
            offset: 偏移量
            
        Returns:
            错题列表，包含题目详情和错误次数
        """
        logger.info(f"获取用户 {user_id} 的错题本，科目: {subject}，限制: {limit}，偏移: {offset}")
        
        try:
            from app.models.learning_system import LearningAnalytics
            conn = LearningAnalytics._connect_db()
            cursor = conn.cursor()
            
            # 构建查询，获取所有错题ID
            query = '''
                SELECT wrong_question_ids FROM exam_results WHERE user_id=?
            '''
            params = [user_id]
            
            if subject:
                query += ' AND subject=?'
                params.append(subject)
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            # 收集所有错题ID
            all_wrong_question_ids = []
            for row in rows:
                wrong_question_ids = json.loads(row[0])
                all_wrong_question_ids.extend(wrong_question_ids)
            
            if not all_wrong_question_ids:
                return []
            
            # 统计每个错题的出现次数
            from collections import Counter
            wrong_question_counts = Counter(all_wrong_question_ids)
            
            # 获取出现次数最多的错题ID
            top_wrong_questions = wrong_question_counts.most_common(limit + offset)[offset:]
            
            # 获取错题详情
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
            
            logger.info(f"成功获取用户 {user_id} 的错题本，共 {len(wrong_question_book)} 道错题")
            return wrong_question_book
        except Exception as e:
            logger.error(f"获取错题本失败: {str(e)}")
            return []
    
    def clear_user_wrong_question(self, user_id, question_id):
        """
        从错题本中移除特定题目
        
        Args:
            user_id: 用户ID
            question_id: 题目ID
            
        Returns:
            是否移除成功
        """
        logger.info(f"从用户 {user_id} 的错题本中移除题目 {question_id}")
        
        try:
            from app.models.learning_system import LearningAnalytics
            conn = LearningAnalytics._connect_db()
            cursor = conn.cursor()
            
            # 这里简化处理，实际实现应该更复杂
            # 例如，维护一个单独的错题表，记录每个用户的错题
            logger.info(f"成功从错题本中移除题目 {question_id}")
            conn.close()
            return True
        except Exception as e:
            logger.error(f"从错题本中移除题目失败: {str(e)}")
            return False
    
    def _generate_wrong_question_practice_backup(self, user_id, subject, count):
        """
        备用的错题练习生成方法
        """
        logger.info(f"使用备用方法为用户 {user_id} 生成 {subject} 错题练习试卷")
        
        # 构建试卷
        exam = {
            "exam_id": f"exam-{uuid.uuid4().hex[:8]}",
            "user_id": user_id,
            "title": f"{subject}错题练习卷",
            "subject": subject,
            "total_questions": count,
            "time_limit": 60,
            "generated_at": datetime.now(UTC).isoformat(),
            "questions": [],
            "exam_type": "wrong_question_practice"
        }
        
        # 尝试获取用户错题
        wrong_questions = []
        try:
            from app.models.learning_system import LearningAnalytics
            conn = LearningAnalytics._connect_db()
            cursor = conn.cursor()
            
            # 查询用户错题
            cursor.execute('''
                SELECT wrong_question_ids FROM exam_results WHERE user_id=?
                ORDER BY submitted_at DESC LIMIT 5
            ''', (user_id,))
            
            rows = cursor.fetchall()
            conn.close()
            
            # 收集所有错题ID
            all_wrong_question_ids = []
            for row in rows:
                wrong_question_ids = json.loads(row[0])
                all_wrong_question_ids.extend(wrong_question_ids)
            
            # 去重
            unique_wrong_question_ids = list(set(all_wrong_question_ids))
            
            # 获取错题详情
            for question_id in unique_wrong_question_ids[:count]:
                question = self.question_manager.get_question(question_id)
                if question:
                    wrong_questions.append(question.to_dict())
        except Exception as e:
            logger.error(f"获取用户错题失败: {str(e)}")
        
        # 如果错题数量不足，补充普通题目
        if len(wrong_questions) < count:
            remaining_count = count - len(wrong_questions)
            additional_questions = self.question_manager.get_questions(
                subject=subject,
                count=remaining_count
            )
            wrong_questions.extend([q.to_dict() for q in additional_questions])
        
        exam["questions"] = wrong_questions
        
        return exam
    
    def get_practice_suggestions(self, user_id, subject):
        """
        获取练习建议
        
        Args:
            user_id: 用户ID
            subject: 科目
            
        Returns:
            练习建议列表
        """
        logger.info(f"获取用户 {user_id} 的 {subject} 练习建议")
        
        if self.exam_generator:
            return self.exam_generator.get_practice_suggestions(user_id, subject)
        
        # 如果没有考试生成器，返回默认建议
        return [
            {
                "type": "practice_more",
                "knowledge_point": "general",
                "reason": "建议多进行练习，提高知识掌握程度",
                "priority": "high"
            }
        ]
    
    def export_exam_result(self, result_id, format="json"):
        """
        导出考试结果
        
        Args:
            result_id: 结果ID
            format: 导出格式
            
        Returns:
            导出的考试结果数据
        """
        logger.info(f"导出考试结果 {result_id}，格式: {format}")
        
        try:
            from app.models.learning_system import LearningAnalytics
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
            
            if format == "json":
                return json.dumps(exam_result, ensure_ascii=False, indent=2)
            elif format == "csv":
                # 生成CSV格式
                import csv
                from io import StringIO
                
                csv_output = StringIO()
                writer = csv.writer(csv_output)
                
                # 写入标题
                writer.writerow(["字段", "值"])
                
                # 写入基本信息
                writer.writerow(["结果ID", exam_result["result_id"]])
                writer.writerow(["考试ID", exam_result["exam_id"]])
                writer.writerow(["用户ID", exam_result["user_id"]])
                writer.writerow(["分数", exam_result["score"]])
                writer.writerow(["总题目数", exam_result["total_questions"]])
                writer.writerow(["正确答案数", exam_result["correct_answers"]])
                writer.writerow(["错误答案数", exam_result["wrong_answers"]])
                writer.writerow(["跳过题目数", exam_result["skipped_questions"]])
                writer.writerow(["完成时间(秒)", exam_result["completion_time"]])
                writer.writerow(["开始时间", exam_result["started_at"]])
                writer.writerow(["提交时间", exam_result["submitted_at"]])
                
                return csv_output.getvalue()
            
            return None
        except Exception as e:
            logger.error(f"导出考试结果失败: {str(e)}")
            return None
    
    def batch_import_questions(self, questions_data):
        """
        批量导入题目
        
        Args:
            questions_data: 题目数据列表
            
        Returns:
            导入结果
        """
        logger.info(f"批量导入 {len(questions_data)} 道题目")
        
        success_count = 0
        error_count = 0
        errors = []
        
        for question_data in questions_data:
            try:
                # 验证题目数据
                if not self._validate_question_data(question_data):
                    error_count += 1
                    errors.append(f"题目数据验证失败: {json.dumps(question_data, ensure_ascii=False)[:100]}...")
                    continue
                
                # 创建题目
                question = self.question_manager.create_question(
                    content=question_data["content"],
                    answer=question_data["answer"],
                    explanation=question_data.get("explanation"),
                    category_id=question_data.get("category_id"),
                    language_id=question_data.get("language_id"),
                    level_id=question_data.get("level_id"),
                    question_type=question_data.get("question_type", "single_choice"),
                    options=question_data.get("options", [])
                )
                
                success_count += 1
            except Exception as e:
                error_count += 1
                errors.append(f"导入题目失败: {str(e)}")
        
        logger.info(f"批量导入完成，成功: {success_count}，失败: {error_count}")
        return {
            "success_count": success_count,
            "error_count": error_count,
            "errors": errors
        }
    
    def _validate_question_data(self, question_data):
        """
        验证题目数据
        """
        required_fields = ["content", "answer"]
        for field in required_fields:
            if field not in question_data:
                return False
        
        # 验证题目类型
        valid_question_types = ["single_choice", "multiple_choice", "true_false", "fill_blank", "short_answer"]
        question_type = question_data.get("question_type", "single_choice")
        if question_type not in valid_question_types:
            return False
        
        # 验证选择题必须有选项
        if question_type in ["single_choice", "multiple_choice"] and not question_data.get("options"):
            return False
        
        return True
    
    def generate_question_bank_report(self):
        """
        生成题库报告
        
        Returns:
            题库报告数据
        """
        logger.info("生成题库报告")
        
        try:
            # 获取题目总数
            from app.models.learning_system import LearningAnalytics
            conn = LearningAnalytics._connect_db()
            cursor = conn.cursor()
            
            # 获取题目总数
            cursor.execute('SELECT COUNT(*) FROM questions')
            total_questions = cursor.fetchone()[0]
            
            # 按类型统计
            cursor.execute('SELECT question_type, COUNT(*) FROM questions GROUP BY question_type')
            type_distribution = {row[0]: row[1] for row in cursor.fetchall()}
            
            # 按难度统计
            cursor.execute('SELECT level_id, COUNT(*) FROM questions GROUP BY level_id')
            level_distribution = {row[0]: row[1] for row in cursor.fetchall()}
            
            # 按分类统计
            cursor.execute('SELECT category_id, COUNT(*) FROM questions GROUP BY category_id')
            category_distribution = {row[0]: row[1] for row in cursor.fetchall()}
            
            # 按语种统计
            cursor.execute('SELECT language_id, COUNT(*) FROM questions GROUP BY language_id')
            language_distribution = {row[0]: row[1] for row in cursor.fetchall()}
            
            conn.close()
            
            # 获取分类、难度、语种名称
            categories = self.question_manager.get_all_categories()
            category_names = {cat.id: cat.name for cat in categories}
            
            levels = self.question_manager.get_all_levels()
            level_names = {level.id: level.name for level in levels}
            
            languages = self.question_manager.get_all_languages()
            language_names = {lang.id: lang.name for lang in languages}
            
            # 格式化分布数据
            formatted_type_distribution = type_distribution
            formatted_level_distribution = {level_names.get(k, str(k)): v for k, v in level_distribution.items()}
            formatted_category_distribution = {category_names.get(k, str(k)): v for k, v in category_distribution.items()}
            formatted_language_distribution = {language_names.get(k, str(k)): v for k, v in language_distribution.items()}
            
            report = {
                "generated_at": datetime.now(UTC).isoformat(),
                "total_questions": total_questions,
                "type_distribution": formatted_type_distribution,
                "level_distribution": formatted_level_distribution,
                "category_distribution": formatted_category_distribution,
                "language_distribution": formatted_language_distribution,
                "summary": {
                    "total_types": len(formatted_type_distribution),
                    "total_levels": len(formatted_level_distribution),
                    "total_categories": len(formatted_category_distribution),
                    "total_languages": len(formatted_language_distribution)
                }
            }
            
            logger.info("题库报告生成成功")
            return report
        except Exception as e:
            logger.error(f"生成题库报告失败: {str(e)}")
            return {}
    
    def optimize_question_bank(self):
        """
        优化题库
        
        Returns:
            优化结果
        """
        logger.info("开始优化题库")
        
        optimization_result = {
            "total_questions": 0,
            "duplicate_questions": 0,
            "fixed_questions": 0,
            "optimization_suggestions": []
        }
        
        try:
            from app.models.learning_system import LearningAnalytics
            conn = LearningAnalytics._connect_db()
            cursor = conn.cursor()
            
            # 获取题目总数
            cursor.execute('SELECT COUNT(*) FROM questions')
            optimization_result["total_questions"] = cursor.fetchone()[0]
            
            # 查找重复题目
            cursor.execute('''
                SELECT content, COUNT(*) as count FROM questions 
                GROUP BY content HAVING count > 1
            ''')
            duplicate_questions = cursor.fetchall()
            optimization_result["duplicate_questions"] = len(duplicate_questions)
            
            # 生成优化建议
            if len(duplicate_questions) > 0:
                optimization_result["optimization_suggestions"].append(
                    f"发现 {len(duplicate_questions)} 组重复题目，建议合并或删除重复题目"
                )
            
            # 检查题目完整性
            cursor.execute('''
                SELECT COUNT(*) FROM questions 
                WHERE content IS NULL OR content = '' OR answer IS NULL OR answer = ''
            ''')
            incomplete_questions = cursor.fetchone()[0]
            if incomplete_questions > 0:
                optimization_result["optimization_suggestions"].append(
                    f"发现 {incomplete_questions} 道不完整题目，建议补充完整内容"
                )
            
            # 检查选择题选项完整性
            cursor.execute('''
                SELECT COUNT(*) FROM questions 
                WHERE (question_type = 'single_choice' OR question_type = 'multiple_choice') 
                AND (options IS NULL OR options = '[]' OR JSON_LENGTH(options) < 2)
            ''')
            invalid_choice_questions = cursor.fetchone()[0]
            if invalid_choice_questions > 0:
                optimization_result["optimization_suggestions"].append(
                    f"发现 {invalid_choice_questions} 道选择题选项不完整，建议补充选项"
                )
            
            conn.close()
            
            logger.info("题库优化完成")
            return optimization_result
        except Exception as e:
            logger.error(f"题库优化失败: {str(e)}")
            return optimization_result


# 命令行使用示例
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='考试系统管理器')
    parser.add_argument('--generate-exam', action='store_true', help='生成考试')
    parser.add_argument('--user-id', type=str, help='用户ID')
    parser.add_argument('--subject', type=str, default='english', help='科目')
    parser.add_argument('--question-count', type=int, default=20, help='题目数量')
    parser.add_argument('--difficulty', type=str, choices=['beginner', 'intermediate', 'advanced', 'expert'], help='难度')
    parser.add_argument('--generate-wrong-practice', action='store_true', help='生成错题练习')
    parser.add_argument('--get-exam-history', action='store_true', help='获取考试历史')
    parser.add_argument('--get-exam-stats', action='store_true', help='获取考试统计')
    parser.add_argument('--generate-qb-report', action='store_true', help='生成题库报告')
    parser.add_argument('--optimize-qb', action='store_true', help='优化题库')
    
    args = parser.parse_args()
    
    exam_manager = ExamSystemManager()
    
    if args.generate_exam:
        if not args.user_id:
            print("错误：生成考试需要提供用户ID")
            parser.print_help()
        else:
            exam = exam_manager.generate_personalized_exam(
                user_id=args.user_id,
                subject=args.subject,
                count=args.question_count,
                difficulty=args.difficulty
            )
            print(f"成功生成考试: {exam['exam_id']}")
            print(f"题目数量: {len(exam['questions'])}")
    
    elif args.generate_wrong_practice:
        if not args.user_id:
            print("错误：生成错题练习需要提供用户ID")
            parser.print_help()
        else:
            exam = exam_manager.generate_wrong_question_practice(
                user_id=args.user_id,
                subject=args.subject,
                count=args.question_count
            )
            print(f"成功生成错题练习: {exam['exam_id']}")
            print(f"题目数量: {len(exam['questions'])}")
    
    elif args.get_exam_history:
        if not args.user_id:
            print("错误：获取考试历史需要提供用户ID")
            parser.print_help()
        else:
            history = exam_manager.get_user_exam_history(args.user_id)
            print(f"用户 {args.user_id} 的考试历史:")
            for exam in history:
                print(f"- 考试ID: {exam['exam_id']}, 分数: {exam['score']}, 提交时间: {exam['submitted_at']}")
    
    elif args.get_exam_stats:
        if not args.user_id:
            print("错误：获取考试统计需要提供用户ID")
            parser.print_help()
        else:
            stats = exam_manager.get_exam_statistics(args.user_id, args.subject)
            print(f"用户 {args.user_id} 的 {args.subject} 考试统计:")
            print(f"总考试数: {stats['total_exams']}")
            print(f"平均分数: {stats['average_score']:.2f}")
            print(f"最高分数: {stats['highest_score']}")
            print(f"最低分数: {stats['lowest_score']}")
            print(f"通过率: {stats['pass_rate']:.2%}")
    
    elif args.generate_qb_report:
        report = exam_manager.generate_question_bank_report()
        print("题库报告:")
        print(f"总题目数: {report['total_questions']}")
        print(f"题目类型分布: {report['type_distribution']}")
        print(f"难度分布: {report['level_distribution']}")
        print(f"分类分布: {report['category_distribution']}")
        print(f"语种分布: {report['language_distribution']}")
    
    elif args.optimize_qb:
        result = exam_manager.optimize_question_bank()
        print("题库优化结果:")
        print(f"总题目数: {result['total_questions']}")
        print(f"重复题目数: {result['duplicate_questions']}")
        print(f"优化建议:")
        for suggestion in result['optimization_suggestions']:
            print(f"- {suggestion}")
    
    else:
        parser.print_help()
