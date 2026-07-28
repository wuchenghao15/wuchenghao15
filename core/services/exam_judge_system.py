#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI考试系统全面优化器
优化多种考试类型的判断逻辑：
1. 学生摸底考试
2. 随机小测试
3. 课后测试
4. 期中期末考试
5. 升学考试
6. 补考
"""

import logging
import os
import sys
import sqlite3
import json
import hashlib
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from enum import Enum

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class ExamType(Enum):
    """考试类型枚举"""
    PLACEMENT = "placement"           # 摸底考试
    RANDOM_QUIZ = "random_quiz"       # 随机小测试
    POST_LESSON = "post_lesson"       # 课后测试
    MIDTERM = "midterm"               # 期中考试
    FINAL = "final"                   # 期末考试
    PROMOTION = "promotion"          # 升学考试
    RETEST = "retest"                # 补考
    MOCK = "mock"                    # 模拟考试
    DIAGNOSTIC = "diagnostic"        # 诊断性考试
    ACHIEVEMENT = "achievement"      # 成就测试


class ExamJudgeSystem:
    """AI考试判断系统"""

    def __init__(self, db_path="app.db"):
        self.db_path = db_path

    def connect(self):
        """连接数据库"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute("PRAGMA foreign_keys = ON")
            return conn
        except Exception as e:
            logger.error(f"连接数据库失败: {str(e)}")
            return None

    def _ensure_tables(self, conn):
        """确保必要的表存在"""
        cursor = conn.cursor()

        # 创建考试记录表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS exam_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                record_id TEXT UNIQUE NOT NULL,
                user_id INTEGER,
                exam_id INTEGER,
                exam_type TEXT NOT NULL,
                exam_name TEXT,
                subject TEXT,
                difficulty TEXT,
                total_questions INTEGER DEFAULT 0,
                correct_count INTEGER DEFAULT 0,
                score REAL DEFAULT 0,
                max_score REAL DEFAULT 100,
                duration INTEGER DEFAULT 0,
                time_spent INTEGER DEFAULT 0,
                started_at TEXT,
                submitted_at TEXT,
                status TEXT DEFAULT 'pending',
                result TEXT,
                feedback TEXT,
                next_action TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # 创建考试配置表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS exam_configs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                exam_type TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                rules TEXT,
                scoring_rules TEXT,
                pass_threshold REAL DEFAULT 60.0,
                question_count_range TEXT,
                difficulty_weights TEXT,
                time_limits TEXT,
                retake_rules TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # 创建用户学习记录表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_learning_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                subject TEXT,
                level TEXT,
                mastery_rate REAL DEFAULT 0.0,
                weak_areas TEXT,
                strong_areas TEXT,
                recent_scores TEXT,
                exam_history TEXT,
                last_updated TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        conn.commit()

    # ============ 考试配置初始化 ============

    def init_exam_configs(self):
        """初始化考试配置"""
        configs = {
            ExamType.PLACEMENT.value: {
                "name": "学生摸底考试",
                "description": "入学前的能力评估测试，用于了解学生当前水平",
                "pass_threshold": 50.0,
                "question_count_range": json.dumps({"min": 20, "max": 50}),
                "difficulty_weights": json.dumps({"easy": 0.4, "medium": 0.4, "hard": 0.2}),
                "scoring_rules": json.dumps({
                    "correct": 5,
                    "partial": 2,
                    "incorrect": 0,
                    "time_bonus": True
                }),
                "retake_rules": json.dumps({
                    "allowed": True,
                    "max_attempts": 3,
                    "cooldown_hours": 24
                }),
                "time_limits": json.dumps({
                    "min_per_question": 30,
                    "max_per_question": 180
                })
            },
            ExamType.RANDOM_QUIZ.value: {
                "name": "随机小测试",
                "description": "日常随机练习，快速检测学习效果",
                "pass_threshold": 0,
                "question_count_range": json.dumps({"min": 5, "max": 15}),
                "difficulty_weights": json.dumps({"easy": 0.5, "medium": 0.4, "hard": 0.1}),
                "scoring_rules": json.dumps({
                    "correct": 1,
                    "partial": 0.5,
                    "incorrect": 0,
                    "time_bonus": False
                }),
                "retake_rules": json.dumps({
                    "allowed": True,
                    "max_attempts": 999,
                    "cooldown_hours": 0
                }),
                "time_limits": json.dumps({
                    "min_per_question": 10,
                    "max_per_question": 60
                })
            },
            ExamType.POST_LESSON.value: {
                "name": "课后测试",
                "description": "课程结束后的巩固测试",
                "pass_threshold": 70.0,
                "question_count_range": json.dumps({"min": 10, "max": 30}),
                "difficulty_weights": json.dumps({"easy": 0.3, "medium": 0.5, "hard": 0.2}),
                "scoring_rules": json.dumps({
                    "correct": 5,
                    "partial": 2,
                    "incorrect": 0,
                    "time_bonus": False
                }),
                "retake_rules": json.dumps({
                    "allowed": True,
                    "max_attempts": 5,
                    "cooldown_hours": 1
                }),
                "time_limits": json.dumps({
                    "min_per_question": 20,
                    "max_per_question": 120
                })
            },
            ExamType.MIDTERM.value: {
                "name": "期中考试",
                "description": "学期中期的综合能力测试",
                "pass_threshold": 60.0,
                "question_count_range": json.dumps({"min": 40, "max": 60}),
                "difficulty_weights": json.dumps({"easy": 0.2, "medium": 0.5, "hard": 0.3}),
                "scoring_rules": json.dumps({
                    "correct": 5,
                    "partial": 2,
                    "incorrect": 0,
                    "time_bonus": False
                }),
                "retake_rules": json.dumps({
                    "allowed": False,
                    "max_attempts": 1,
                    "cooldown_hours": 0
                }),
                "time_limits": json.dumps({
                    "min_per_question": 30,
                    "max_per_question": 150
                })
            },
            ExamType.FINAL.value: {
                "name": "期末考试",
                "description": "学期末的综合能力测试",
                "pass_threshold": 60.0,
                "question_count_range": json.dumps({"min": 50, "max": 80}),
                "difficulty_weights": json.dumps({"easy": 0.15, "medium": 0.45, "hard": 0.4}),
                "scoring_rules": json.dumps({
                    "correct": 5,
                    "partial": 2,
                    "incorrect": 0,
                    "time_bonus": False
                }),
                "retake_rules": json.dumps({
                    "allowed": True,
                    "max_attempts": 1,
                    "cooldown_hours": 168
                }),
                "time_limits": json.dumps({
                    "min_per_question": 30,
                    "max_per_question": 180
                })
            },
            ExamType.PROMOTION.value: {
                "name": "升学考试",
                "description": "升入下一阶段的选拔考试",
                "pass_threshold": 75.0,
                "question_count_range": json.dumps({"min": 60, "max": 100}),
                "difficulty_weights": json.dumps({"easy": 0.1, "medium": 0.4, "hard": 0.5}),
                "scoring_rules": json.dumps({
                    "correct": 5,
                    "partial": 1,
                    "incorrect": 0,
                    "time_bonus": True
                }),
                "retake_rules": json.dumps({
                    "allowed": True,
                    "max_attempts": 2,
                    "cooldown_hours": 720
                }),
                "time_limits": json.dumps({
                    "min_per_question": 45,
                    "max_per_question": 180
                })
            },
            ExamType.RETEST.value: {
                "name": "补考",
                "description": "不及格后的重新测试",
                "pass_threshold": 60.0,
                "question_count_range": json.dumps({"min": 20, "max": 50}),
                "difficulty_weights": json.dumps({"easy": 0.3, "medium": 0.5, "hard": 0.2}),
                "scoring_rules": json.dumps({
                    "correct": 5,
                    "partial": 2,
                    "incorrect": 0,
                    "time_bonus": False
                }),
                "retake_rules": json.dumps({
                    "allowed": True,
                    "max_attempts": 2,
                    "cooldown_hours": 72
                }),
                "time_limits": json.dumps({
                    "min_per_question": 30,
                    "max_per_question": 150
                })
            }
        }

        conn = self.connect()
        if not conn:
            return

        try:
            cursor = conn.cursor()
            self._ensure_tables(conn)

            for exam_type, config in configs.items():
                cursor.execute('''
                    INSERT OR REPLACE INTO exam_configs 
                    (exam_type, name, description, pass_threshold, question_count_range,
                     difficulty_weights, scoring_rules, retake_rules, time_limits, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    exam_type,
                    config["name"],
                    config["description"],
                    config["pass_threshold"],
                    config["question_count_range"],
                    config["difficulty_weights"],
                    config["scoring_rules"],
                    config["retake_rules"],
                    config["time_limits"],
                    datetime.now().isoformat()
                ))

            conn.commit()
            print(f"✅ 初始化了 {len(configs)} 种考试配置")

        except Exception as e:
            logger.error(f"初始化考试配置失败: {str(e)}")
        finally:
            conn.close()

    # ============ 考试判断逻辑 ============

    def judge_placement_exam(self, user_id: int, score: float, answers: List[Dict]) -> Dict:
        """判断摸底考试结果"""
        result = {
            "action": "recommend_level",
            "recommended_level": "",
            "strengths": [],
            "weaknesses": [],
            "study_plan": []
        }

        # 根据分数判断推荐级别
        if score >= 90:
            result["recommended_level"] = "advanced"
            result["action"] = "skip_basics"
            result["study_plan"] = ["高级内容学习", "专项强化训练", "模拟考试"]
        elif score >= 75:
            result["recommended_level"] = "intermediate"
            result["action"] = "standard_progress"
            result["study_plan"] = ["标准课程学习", "重点突破", "定期测试"]
        elif score >= 60:
            result["recommended_level"] = "elementary"
            result["action"] = "strengthen_basics"
            result["study_plan"] = ["基础巩固", "逐步进阶", "加强练习"]
        else:
            result["recommended_level"] = "beginner"
            result["action"] = "start_from_scratch"
            result["study_plan"] = ["从头开始学习", "基础夯实", "循序渐进"]

        # 分析答案找出强项和弱项
        topic_performance = {}
        for answer in answers:
            topic = answer.get("topic", "general")
            if topic not in topic_performance:
                topic_performance[topic] = {"correct": 0, "total": 0}
            topic_performance[topic]["total"] += 1
            if answer.get("is_correct"):
                topic_performance[topic]["correct"] += 1

        for topic, stats in topic_performance.items():
            rate = stats["correct"] / stats["total"] if stats["total"] > 0 else 0
            if rate >= 0.8:
                result["strengths"].append(topic)
            elif rate < 0.5:
                result["weaknesses"].append(topic)

        return result

    def judge_random_quiz(self, score: float, time_spent: int, answers: List[Dict]) -> Dict:
        """判断随机小测试结果"""
        result = {
            "action": "continue_practice",
            "message": "",
            "next_quiz_type": "similar"
        }

        # 快速判断
        if score >= 80:
            result["action"] = "increase_difficulty"
            result["message"] = "表现优秀，可以挑战更高难度"
            result["next_quiz_type"] = "harder"
        elif score >= 60:
            result["action"] = "maintain_level"
            result["message"] = "表现良好，继续保持"
            result["next_quiz_type"] = "similar"
        else:
            result["action"] = "review_basics"
            result["message"] = "建议复习基础知识"
            result["next_quiz_type"] = "easier"

        return result

    def judge_post_lesson_exam(self, user_id: int, score: float, lesson_id: str, 
                               answers: List[Dict], time_spent: int) -> Dict:
        """判断课后测试结果"""
        result = {
            "action": "proceed",
            "passed": score >= 70,
            "weak_topics": [],
            "review_materials": [],
            "next_steps": []
        }

        # 分析错误题目
        wrong_answers = [a for a in answers if not a.get("is_correct")]
        
        for answer in wrong_answers:
            topic = answer.get("topic", "general")
            if topic not in result["weak_topics"]:
                result["weak_topics"].append(topic)

        # 根据结果给出建议
        if result["passed"]:
            result["action"] = "proceed_next_lesson"
            result["next_steps"] = ["进入下一课", "继续练习"]
        else:
            result["action"] = "review_and_retry"
            result["next_steps"] = ["复习本章内容", "重新测试", "观看讲解视频"]
            result["review_materials"] = [
                f"第{lesson_id}课知识点回顾",
                "相关练习题强化"
            ]

        return result

    def judge_midterm_exam(self, user_id: int, score: float, total_score: float,
                            answers: List[Dict], duration: int, time_spent: int) -> Dict:
        """判断期中考试结果"""
        percentage = (score / total_score * 100) if total_score > 0 else 0
        
        result = {
            "action": "adjust_study_plan",
            "passed": percentage >= 60,
            "grade": "",
            "analysis": {},
            "recommendations": []
        }

        # 评分等级
        if percentage >= 90:
            result["grade"] = "A"
        elif percentage >= 80:
            result["grade"] = "B"
        elif percentage >= 70:
            result["grade"] = "C"
        elif percentage >= 60:
            result["grade"] = "D"
        else:
            result["grade"] = "F"

        # 时间效率分析
        time_per_question = time_spent / len(answers) if answers else 0
        result["analysis"]["time_efficiency"] = "fast" if time_per_question < 60 else "normal"

        # 章节分析
        chapter_performance = {}
        for answer in answers:
            chapter = answer.get("chapter", "general")
            if chapter not in chapter_performance:
                chapter_performance[chapter] = {"correct": 0, "total": 0}
            chapter_performance[chapter]["total"] += 1
            if answer.get("is_correct"):
                chapter_performance[chapter]["correct"] += 1

        result["analysis"]["chapter_scores"] = chapter_performance

        # 建议
        if result["passed"]:
            result["action"] = "continue_to_final"
            result["recommendations"] = [
                "继续保持学习节奏",
                "加强薄弱章节",
                "准备期末考试"
            ]
        else:
            result["action"] = "need_remediation"
            result["recommendations"] = [
                "需要复习前半学期内容",
                "参加辅导课程",
                "准备补考或重修"
            ]

        return result

    def judge_final_exam(self, user_id: int, score: float, total_score: float,
                         answers: List[Dict], duration: int, time_spent: int) -> Dict:
        """判断期末考试结果"""
        percentage = (score / total_score * 100) if total_score > 0 else 0
        
        result = {
            "action": "semester_complete",
            "passed": percentage >= 60,
            "grade": "",
            "gpa_contribution": 0.0,
            "semester_summary": {},
            "next_semester_plan": []
        }

        # GPA计算
        grade_points = {"A": 4.0, "B": 3.0, "C": 2.0, "D": 1.0, "F": 0.0}
        
        if percentage >= 90:
            result["grade"] = "A"
        elif percentage >= 80:
            result["grade"] = "B"
        elif percentage >= 70:
            result["grade"] = "C"
        elif percentage >= 60:
            result["grade"] = "D"
        else:
            result["grade"] = "F"

        result["gpa_contribution"] = grade_points.get(result["grade"], 0.0)

        # 学期总结
        correct_answers = [a for a in answers if a.get("is_correct")]
        result["semester_summary"] = {
            "total_questions": len(answers),
            "correct_count": len(correct_answers),
            "accuracy_rate": round(len(correct_answers) / len(answers) * 100, 2) if answers else 0
        }

        # 下学期计划
        if result["passed"]:
            result["next_semester_plan"] = [
                "恭喜通过本学期课程",
                "下学期将学习进阶内容",
                "建议预习下学期内容"
            ]
        else:
            result["next_semester_plan"] = [
                "需要参加补考",
                "补考时间请关注通知",
                "补考复习重点章节"
            ]

        return result

    def judge_promotion_exam(self, user_id: int, score: float, total_score: float,
                              target_level: str, current_level: str, answers: List[Dict]) -> Dict:
        """判断升学考试结果"""
        percentage = (score / total_score * 100) if total_score > 0 else 0
        
        result = {
            "action": "promotion_decision",
            "passed": percentage >= 75,
            "promoted": False,
            "level_change": "",
            "gap_analysis": {},
            "next_steps": []
        }

        # 升学判断
        if percentage >= 90:
            result["action"] = "promote_with_distinction"
            result["promoted"] = True
            result["level_change"] = f"{current_level} → {target_level} (优秀)"
        elif percentage >= 75:
            result["action"] = "promote_conditionally"
            result["promoted"] = True
            result["level_change"] = f"{current_level} → {target_level} (及格)"
        else:
            result["action"] = "stay_current_level"
            result["promoted"] = False
            result["level_change"] = f"继续留在 {current_level}"

        # 差距分析
        topic_gaps = {}
        for answer in answers:
            topic = answer.get("topic", "general")
            if topic not in topic_gaps:
                topic_gaps[topic] = {"score": 0, "weight": 1}
            if not answer.get("is_correct"):
                topic_gaps[topic]["score"] -= 1

        result["gap_analysis"] = topic_gaps

        # 下一步
        if result["promoted"]:
            result["next_steps"] = [
                f"恭喜升入 {target_level}",
                "建议预习新级别内容",
                "做好学习规划"
            ]
        else:
            result["next_steps"] = [
                "本次升学未通过",
                f"需要加强 {current_level} 内容",
                "参加下一期升学考试",
                "建议针对性复习"
            ]

        return result

    def judge_retest(self, user_id: int, original_score: float, retest_score: float,
                     total_score: float, retest_count: int, answers: List[Dict]) -> Dict:
        """判断补考结果"""
        original_percentage = (original_score / total_score * 100) if total_score > 0 else 0
        retest_percentage = (retest_score / total_score * 100) if total_score > 0 else 0
        
        result = {
            "action": "retest_decision",
            "passed": retest_percentage >= 60,
            "improvement": retest_percentage - original_percentage,
            "status": "",
            "final_decision": ""
        }

        # 补考结果判断
        if result["passed"]:
            if retest_percentage >= 90:
                result["status"] = "excellent_recovery"
                result["final_decision"] = "补考通过，获得优秀"
            elif retest_percentage >= 75:
                result["status"] = "good_recovery"
                result["final_decision"] = "补考通过，良好"
            else:
                result["status"] = "barely_passed"
                result["final_decision"] = "补考通过，仍需努力"
        else:
            if retest_count >= 2:
                result["status"] = "failed_permanently"
                result["final_decision"] = "补考次数用尽，需重修"
            else:
                result["status"] = "failed_retry"
                result["final_decision"] = f"补考未通过，还剩{2 - retest_count}次机会"

        return result

    # ============ 统一判断接口 ============

    def judge_exam(self, exam_type: str, user_id: int, score: float, 
                   total_score: float, answers: List[Dict], 
                   time_spent: int = 0, duration: int = 0, **kwargs) -> Dict:
        """统一的考试判断接口"""
        
        percentage = (score / total_score * 100) if total_score > 0 else 0

        # 基础结果
        base_result = {
            "exam_type": exam_type,
            "score": score,
            "total_score": total_score,
            "percentage": round(percentage, 2),
            "passed": percentage >= 60,
            "timestamp": datetime.now().isoformat()
        }

        # 根据不同考试类型调用相应的判断方法
        try:
            if exam_type == ExamType.PLACEMENT.value:
                specific_result = self.judge_placement_exam(user_id, score, answers)
            elif exam_type == ExamType.RANDOM_QUIZ.value:
                specific_result = self.judge_random_quiz(score, time_spent, answers)
            elif exam_type == ExamType.POST_LESSON.value:
                specific_result = self.judge_post_lesson_exam(
                    user_id, score, 
                    kwargs.get('lesson_id', ''), 
                    answers, time_spent
                )
            elif exam_type == ExamType.MIDTERM.value:
                specific_result = self.judge_midterm_exam(
                    user_id, score, total_score, answers, duration, time_spent
                )
            elif exam_type == ExamType.FINAL.value:
                specific_result = self.judge_final_exam(
                    user_id, score, total_score, answers, duration, time_spent
                )
            elif exam_type == ExamType.PROMOTION.value:
                specific_result = self.judge_promotion_exam(
                    user_id, score, total_score,
                    kwargs.get('target_level', ''),
                    kwargs.get('current_level', ''),
                    answers
                )
            elif exam_type == ExamType.RETEST.value:
                specific_result = self.judge_retest(
                    user_id,
                    kwargs.get('original_score', 0),
                    score,  # retest_score
                    total_score,
                    kwargs.get('retest_count', 1),
                    answers
                )
            else:
                specific_result = {}

            return {**base_result, **specific_result}

        except Exception as e:
            logger.error(f"考试判断失败: {str(e)}")
            return {**base_result, "error": str(e)}

    # ============ 考试记录管理 ============

    def save_exam_record(self, exam_type: str, user_id: int, exam_id: int,
                         exam_name: str, score: float, total_score: float,
                         correct_count: int, total_questions: int,
                         time_spent: int, duration: int,
                         answers: List[Dict] = None, **kwargs) -> str:
        """保存考试记录"""
        conn = self.connect()
        if not conn:
            return None

        try:
            cursor = conn.cursor()
            self._ensure_tables(conn)

            record_id = f"EX{ datetime.now().strftime('%Y%m%d%H%M%S') }{uuid.uuid4().hex[:6].upper()}"
            
            # 判断结果
            answers_for_judge = answers or []
            judgment = self.judge_exam(
                exam_type, user_id, score, total_score,
                answers_for_judge, time_spent, duration, **kwargs
            )

            # 保存记录
            cursor.execute('''
                INSERT INTO exam_records
                (record_id, user_id, exam_id, exam_type, exam_name, difficulty,
                 total_questions, correct_count, score, max_score, duration, time_spent,
                 started_at, submitted_at, status, result, feedback, next_action)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                record_id,
                user_id,
                exam_id,
                exam_type,
                exam_name,
                kwargs.get("difficulty", "medium"),
                total_questions,
                correct_count,
                score,
                total_score,
                duration,
                time_spent,
                kwargs.get("started_at", datetime.now().isoformat()),
                datetime.now().isoformat(),
                "completed",
                json.dumps(judgment.get("result", "")),
                json.dumps(judgment.get("feedback", "")),
                judgment.get("action", "")
            ))

            conn.commit()
            return record_id

        except Exception as e:
            logger.error(f"保存考试记录失败: {str(e)}")
            return None
        finally:
            conn.close()

    # ============ 统计报告 ============

    def generate_exam_report(self, user_id: int = None, exam_type: str = None) -> Dict:
        """生成考试报告"""
        conn = self.connect()
        if not conn:
            return {}

        try:
            cursor = conn.cursor()
            
            query = "SELECT * FROM exam_records WHERE 1=1"
            params = []
            
            if user_id:
                query += " AND user_id = ?"
                params.append(user_id)
            if exam_type:
                query += " AND exam_type = ?"
                params.append(exam_type)
            
            query += " ORDER BY created_at DESC LIMIT 100"
            
            cursor.execute(query, params)
            records = cursor.fetchall()
            
            if not records:
                return {"message": "没有找到考试记录"}

            columns = [desc[0] for desc in cursor.description]
            records = [dict(zip(columns, row)) for row in records]

            # 统计
            total_exams = len(records)
            passed_exams = sum(1 for r in records if r.get("score", 0) / r.get("max_score", 1) >= 0.6)
            avg_score = sum(r.get("score", 0) / r.get("max_score",
            1) * 100 for r in records) / total_exams if total_exams > 0 else 0

            return {
                "total_exams": total_exams,
                "passed_exams": passed_exams,
                "pass_rate": round(passed_exams / total_exams * 100, 2) if total_exams > 0 else 0,
                "average_score": round(avg_score, 2),
                "recent_exams": records[:10],
                "exam_type_breakdown": self._get_exam_type_breakdown(records)
            }

        except Exception as e:
            logger.error(f"生成报告失败: {str(e)}")
            return {"error": str(e)}
        finally:
            conn.close()

    def _get_exam_type_breakdown(self, records: List[Dict]) -> Dict:
        """获取各类型考试统计"""
        breakdown = {}
        
        for record in records:
            exam_type = record.get("exam_type", "unknown")
            if exam_type not in breakdown:
                breakdown[exam_type] = {"count": 0, "total_score": 0, "max_score": 0}
            
            breakdown[exam_type]["count"] += 1
            breakdown[exam_type]["total_score"] += record.get("score", 0)
            breakdown[exam_type]["max_score"] += record.get("max_score", 0)

        # 计算各类型的平均分
        for exam_type, stats in breakdown.items():
            if stats["max_score"] > 0:
                stats["avg_percentage"] = round(stats["total_score"] / stats["max_score"] * 100, 2)
            else:
                stats["avg_percentage"] = 0

        return breakdown

    def show_exam_type_guide(self):
        """显示考试类型指南"""
        print("\n" + "=" * 80)
        print("📚 考试类型判断逻辑指南")
        print("=" * 80)

        guides = {
            "摸底考试 (placement)": """
  目的：了解学生初始水平
  特点：全面评估，不设通过门槛
  判断：按分数分4个级别（beginner/elementary/intermediate/advanced）
  重点：分析强项和弱项，制定个性化学习计划""",

            "随机小测试 (random_quiz)": """
  目的：日常快速检测
  特点：题量少（5-15题），可无限次重做
  判断：即时反馈，鼓励为主
  重点：激发学习兴趣，保持练习习惯""",

            "课后测试 (post_lesson)": """
  目的：巩固课堂学习成果
  特点：针对性强，难度适中
  判断：70%为通过线
  重点：找出未掌握的知识点""",

            "期中考试 (midterm)": """
  目的：检验阶段性学习成果
  特点：综合性强，时间压力大
  判断：60%为通过线，按分数分A/B/C/D/F等级
  重点：时间管理，章节均衡""",

            "期末考试 (final)": """
  目的：综合能力终极检验
  特点：题量最大，覆盖最广
  判断：60%为通过线，影响GPA
  重点：全面复习，理解应用""",

            "升学考试 (promotion)": """
  目的：选拔进入下一级别
  特点：高标准，竞争性强
  判断：75%为通过线，90%以上优秀
  重点：突破难点，展现综合实力""",

            "补考 (retest)": """
  目的：为未通过者提供机会
  特点：针对性复习，限次重考
  判断：60%为通过线，最多2次机会
  重点：分析差距，重点突破"""
        }

        for exam_type, guide in guides.items():
            print(f"\n【{exam_type}】{guide}")

        print("\n" + "=" * 80)


def main():
    """主函数"""
    print("\n" + "=" * 80)
    print("🎓 AI考试系统优化器")
    print("=" * 80)

    judge_system = ExamJudgeSystem()

    # 初始化考试配置
    print("\n正在初始化考试配置...")
    judge_system.init_exam_configs()

    # 显示考试类型指南
    judge_system.show_exam_type_guide()

    # 生成测试报告
    print("\n📊 生成考试报告示例...")
    report = judge_system.generate_exam_report()
    if report and "message" not in report:
        print(f"总考试数: {report.get('total_exams', 0)}")
        print(f"通过数: {report.get('passed_exams', 0)}")
        print(f"平均分: {report.get('average_score', 0)}%")
    else:
        print("暂无考试记录")

    print("\n" + "=" * 80)
    print("✅ 考试系统优化完成!")
    print("=" * 80)


if __name__ == "__main__":
    main()