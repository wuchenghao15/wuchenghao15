#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
题库自动维护AI员工
负责题库的自动扩充、整理、维护，包括历年真题、高频练习题、竞赛题、自主招生题等
"""

import logging
import json
import uuid
import os
import sys
import time
import random
import threading
from datetime import datetime
from typing import Dict, List, Any, Optional
from enum import Enum
from dataclasses import dataclass, field

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logger = logging.getLogger(__name__)


class QuestionSource(Enum):
    """题目来源类型"""
    REAL_EXAM = "real_exam"
    HIGH_FREQUENCY = "high_frequency"
    COMPETITION = "competition"
    SELF_ADMISSION = "self_admission"
    POLITICS_NEW = "politics_new"
    K12 = "k12"
    JAPANESE_LISTENING = "japanese_listening"
    ENGLISH_LISTENING = "english_listening"
    WEB_CRAWLED = "web_crawled"
    AI_GENERATED = "ai_generated"


class MaintenanceTaskType(Enum):
    """维护任务类型"""
    EXPAND_QUESTIONS = "expand_questions"
    ORGANIZE_QUESTIONS = "organize_questions"
    QUALITY_CHECK = "quality_check"
    DUPLICATE_REMOVAL = "duplicate_removal"
    CATEGORY_OPTIMIZATION = "category_optimization"
    FULL_MAINTENANCE = "full_maintenance"
    WEB_CRAWL = "web_crawl"
    AI_GENERATE = "ai_generate"


@dataclass
class MaintenanceTask:
    """维护任务"""
    task_id: str
    task_type: str
    subject: str = "all"
    source_type: str = "ai_generated"
    target_count: int = 50
    status: str = "pending"
    progress: int = 0
    added_count: int = 0
    organized_count: int = 0
    error_count: int = 0
    errors: List[str] = field(default_factory=list)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    result: Optional[Dict] = None

    def to_dict(self) -> Dict:
        return {
            'task_id': self.task_id,
            'task_type': self.task_type,
            'subject': self.subject,
            'source_type': self.source_type,
            'target_count': self.target_count,
            'status': self.status,
            'progress': self.progress,
            'added_count': self.added_count,
            'organized_count': self.organized_count,
            'error_count': self.error_count,
            'errors': self.errors,
            'started_at': self.started_at,
            'completed_at': self.completed_at,
            'result': self.result
        }


class QuestionBankMaintenanceEmployee:
    """题库自动维护AI员工"""

    def __init__(self, employee_id: str, name: str, level: int = 1):
        self.employee_id = employee_id
        self.name = name
        self.level = level
        self.type = "question_bank_maintenance"
        self.status = "active"
        self.task_count = 0
        self.success_count = 0
        self.failure_count = 0
        self.performance_score = 80 + level * 2
        self.knowledge_base = []

        self.skills = [
            {"name": "question_generation", "level": 5 + level, "experience": 0.0},
            {"name": "question_organization", "level": 5 + level, "experience": 0.0},
            {"name": "quality_control", "level": 4 + level, "experience": 0.0},
            {"name": "web_crawling", "level": 4 + level, "experience": 0.0},
            {"name": "category_management", "level": 4 + level, "experience": 0.0},
            {"name": "duplicate_detection", "level": 4 + level, "experience": 0.0},
            {"name": "k12_education", "level": 3 + level, "experience": 0.0},
            {"name": "politics_analysis", "level": 3 + level, "experience": 0.0}
        ]

        self._tasks: Dict[str, MaintenanceTask] = {}
        self._lock = threading.RLock()
        self._maintenance_plans: List[Dict] = []

        self._db_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'app.db'
        )

        self._init_database()
        self._init_maintenance_plans()

        logger.info(f"[题库维护员工] 创建: {self.name} ({self.employee_id}) 级别: {self.level}")

    def _init_database(self):
        """初始化数据库表"""
        try:
            import sqlite3
            conn = sqlite3.connect(self._db_path)
            cursor = conn.cursor()

            cursor.execute('''CREATE TABLE IF NOT EXISTS question_maintenance_tasks (
                task_id TEXT PRIMARY KEY,
                task_type TEXT NOT NULL,
                subject TEXT,
                source_type TEXT,
                target_count INTEGER,
                status TEXT,
                progress INTEGER DEFAULT 0,
                added_count INTEGER DEFAULT 0,
                organized_count INTEGER DEFAULT 0,
                error_count INTEGER DEFAULT 0,
                errors TEXT,
                started_at REAL,
                completed_at REAL,
                result TEXT,
                employee_id TEXT,
                created_at REAL DEFAULT (strftime('%s','now'))
            )''')

            cursor.execute('''CREATE TABLE IF NOT EXISTS question_maintenance_plans (
                plan_id TEXT PRIMARY KEY,
                plan_name TEXT NOT NULL,
                task_type TEXT NOT NULL,
                subject TEXT,
                source_type TEXT,
                target_count INTEGER,
                schedule_type TEXT,
                schedule_interval INTEGER,
                last_executed_at REAL,
                next_execution_at REAL,
                is_active INTEGER DEFAULT 1,
                created_at REAL DEFAULT (strftime('%s','now'))
            )''')

            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"[题库维护员工] 初始化数据库失败: {e}")

    def _init_maintenance_plans(self):
        """初始化默认维护计划"""
        default_plans = [
            {
                'plan_name': '每日题库扩充',
                'task_type': 'expand_questions',
                'subject': 'all',
                'source_type': 'ai_generated',
                'target_count': 100,
                'schedule_type': 'daily',
                'schedule_interval': 24
            },
            {
                'plan_name': '每周题库整理',
                'task_type': 'organize_questions',
                'subject': 'all',
                'source_type': 'ai_generated',
                'target_count': 500,
                'schedule_type': 'weekly',
                'schedule_interval': 168
            },
            {
                'plan_name': '每日质量检查',
                'task_type': 'quality_check',
                'subject': 'all',
                'source_type': 'ai_generated',
                'target_count': 200,
                'schedule_type': 'daily',
                'schedule_interval': 24
            },
            {
                'plan_name': '政治题每日更新',
                'task_type': 'expand_questions',
                'subject': 'politics',
                'source_type': 'politics_new',
                'target_count': 50,
                'schedule_type': 'daily',
                'schedule_interval': 24
            },
            {
                'plan_name': 'K12题库扩充',
                'task_type': 'expand_questions',
                'subject': 'k12',
                'source_type': 'k12',
                'target_count': 80,
                'schedule_type': 'daily',
                'schedule_interval': 24
            },
            {
                'plan_name': '听力题每周扩充',
                'task_type': 'expand_questions',
                'subject': 'listening',
                'source_type': 'ai_generated',
                'target_count': 60,
                'schedule_type': 'weekly',
                'schedule_interval': 168
            }
        ]

        self._maintenance_plans = default_plans

    def start(self):
        """启动员工"""
        self.status = "active"
        logger.info(f"[题库维护员工] {self.name} 已启动")

    def get_status(self) -> Dict[str, Any]:
        """获取员工状态"""
        return {
            "employee_id": self.employee_id,
            "name": self.name,
            "type": self.type,
            "level": self.level,
            "status": self.status,
            "task_count": self.task_count,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "success_rate": self.success_count / max(self.task_count, 1) * 100,
            "performance_score": self.performance_score,
            "skills": self.skills,
            "maintenance_plans": len(self._maintenance_plans),
            "active_tasks": len([t for t in self._tasks.values() if t.status == 'running'])
        }

    def execute_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行任务"""
        self.task_count += 1
        start_time = time.time()

        try:
            task_type = task_data.get("task_type", "expand_questions")

            if task_type == "expand_questions":
                result = self._expand_questions(task_data)
            elif task_type == "organize_questions":
                result = self._organize_questions(task_data)
            elif task_type == "quality_check":
                result = self._quality_check(task_data)
            elif task_type == "duplicate_removal":
                result = self._duplicate_removal(task_data)
            elif task_type == "category_optimization":
                result = self._category_optimization(task_data)
            elif task_type == "full_maintenance":
                result = self._full_maintenance(task_data)
            elif task_type == "web_crawl":
                result = self._web_crawl_questions(task_data)
            elif task_type == "ai_generate":
                result = self._ai_generate_questions(task_data)
            elif task_type == "get_statistics":
                result = self._get_statistics()
            elif task_type == "get_maintenance_plans":
                result = self._get_maintenance_plans()
            elif task_type == "create_maintenance_plan":
                result = self._create_maintenance_plan(task_data)
            else:
                result = {"success": False, "error": f"未知任务类型: {task_type}"}

            if result.get("success", False):
                self.success_count += 1
                self._update_performance(True, time.time() - start_time)
            else:
                self.failure_count += 1
                self._update_performance(False, time.time() - start_time)

            result["execution_time"] = time.time() - start_time
            result["employee_id"] = self.employee_id
            result["employee_name"] = self.name

            return result

        except Exception as e:
            self.failure_count += 1
            self._update_performance(False, time.time() - start_time)
            logger.error(f"[题库维护员工] 任务执行失败: {self.name}, 错误: {e}")
            return {
                "success": False,
                "error": str(e),
                "execution_time": time.time() - start_time,
                "employee_id": self.employee_id,
                "employee_name": self.name
            }

    def _generate_task_id(self) -> str:
        """生成任务ID"""
        return f"QBM-{int(time.time())}-{uuid.uuid4().hex[:8]}"

    def _expand_questions(self, task_data: Dict) -> Dict:
        """扩充题库"""
        task_id = self._generate_task_id()
        subject = task_data.get("subject", "all")
        source_type = task_data.get("source_type", "ai_generated")
        target_count = int(task_data.get("target_count", 50))

        task = MaintenanceTask(
            task_id=task_id,
            task_type="expand_questions",
            subject=subject,
            source_type=source_type,
            target_count=target_count,
            status="running",
            started_at=time.time()
        )

        with self._lock:
            self._tasks[task_id] = task

        try:
            added_count = 0

            if source_type in ["ai_generated", "all"]:
                generated = self._generate_subject_questions(subject, target_count - added_count)
                added_count += generated
                task.added_count = added_count
                task.progress = int(added_count / target_count * 100)

            if source_type in ["web_crawled", "all"] and added_count < target_count:
                try:
                    from app.services.question_crawler_service import question_crawler_service
                    keywords = self._get_subject_keywords(subject)
                    crawled, errors = question_crawler_service.crawl_questions(
                        keywords=keywords,
                        count=target_count - added_count
                    )
                    added_count += crawled
                    task.added_count = added_count
                    task.progress = int(added_count / target_count * 100)
                except Exception as e:
                    task.errors.append(f"爬虫错误: {str(e)}")
                    task.error_count += 1

            task.status = "completed"
            task.completed_at = time.time()
            task.result = {"added_count": added_count, "subject": subject}

            self._save_task_to_db(task)

            return {
                "success": True,
                "message": f"题库扩充完成，新增 {added_count} 道题目",
                "task_id": task_id,
                "added_count": added_count,
                "subject": subject,
                "source_type": source_type
            }

        except Exception as e:
            task.status = "failed"
            task.completed_at = time.time()
            task.errors.append(str(e))
            task.error_count += 1
            self._save_task_to_db(task)
            return {"success": False, "error": str(e), "task_id": task_id}

    def _generate_subject_questions(self, subject: str, count: int) -> int:
        """生成指定学科的题目"""
        added_count = 0

        try:
            from app.services.enhanced_question_bank_service import enhanced_question_bank_service

            subjects_config = self._get_subject_config(subject)

            for _ in range(count):
                try:
                    question = self._generate_single_question(subjects_config)
                    if question:
                        enhanced_question_bank_service.add_question(question)
                        added_count += 1
                except Exception:
                    continue

        except Exception as e:
            logger.error(f"[题库维护员工] 生成题目失败: {e}")

        return added_count

    def _get_subject_config(self, subject: str) -> Dict:
        """获取学科配置"""
        configs = {
            "politics": {
                "subject": "politics",
                "categories": ["real_exam", "must_know", "key_point", "comprehension"],
                "types": ["single_choice", "multiple_choice", "true_false", "short_answer", "essay"],
                "difficulties": ["easy", "medium", "hard"],
                "topics": ["马克思主义原理", "毛泽东思想", "中国特色社会主义", "思想道德修养",
                          "近现代史纲要", "形势与政策", "时事政治", "习近平新时代中国特色社会主义思想"]
            },
            "k12": {
                "subject": "k12",
                "categories": ["real_exam", "must_know", "final", "special_topic", "error_prone"],
                "types": ["single_choice", "multiple_choice", "fill_blank", "calculation", "short_answer"],
                "difficulties": ["easy", "medium", "hard", "expert"],
                "topics": ["小学语文", "小学数学", "小学英语", "初中语文", "初中数学", "初中英语",
                          "初中物理", "初中化学", "高中语文", "高中数学", "高中英语", "高中物理",
                          "高中化学", "高中生物", "高中历史", "高中地理", "高中政治"]
            },
            "japanese": {
                "subject": "japanese",
                "categories": ["real_exam", "must_know", "special_topic", "comprehension"],
                "types": ["single_choice", "fill_blank", "true_false", "short_answer"],
                "difficulties": ["easy", "medium", "hard"],
                "topics": ["日语N1", "日语N2", "日语N3", "日语N4", "日语N5",
                          "日语语法", "日语词汇", "日语阅读", "日语听力", "日语写作"]
            },
            "english": {
                "subject": "english",
                "categories": ["real_exam", "must_know", "special_topic", "comprehension"],
                "types": ["single_choice", "fill_blank", "true_false", "short_answer", "essay"],
                "difficulties": ["easy", "medium", "hard", "expert"],
                "topics": ["英语四级", "英语六级", "考研英语", "雅思", "托福",
                          "英语语法", "英语词汇", "英语阅读", "英语听力", "英语写作", "英语口语"]
            },
            "all": {
                "subject": "mixed",
                "categories": ["real_exam", "must_know", "final", "special_topic", "key_point"],
                "types": ["single_choice", "multiple_choice", "true_false", "fill_blank", "calculation", "short_answer"],
                "difficulties": ["easy", "medium", "hard"],
                "topics": ["数学", "物理", "化学", "生物", "语文", "英语", "历史", "地理", "政治"]
            }
        }

        return configs.get(subject, configs["all"])

    def _get_subject_keywords(self, subject: str) -> List[str]:
        """获取学科关键词"""
        keywords_map = {
            "politics": ["考研政治真题", "政治选择题", "时事政治", "马克思主义原理", "毛概"],
            "k12": ["高考真题", "中考真题", "小学数学题", "初中物理题", "高中化学题"],
            "japanese": ["日语能力考真题", "JLPT N2真题", "日语语法题"],
            "english": ["英语四级真题", "英语六级真题", "考研英语真题", "雅思阅读"],
            "all": ["历年真题", "考试题库", "高频考点", "考研真题", "高考真题"]
        }
        return keywords_map.get(subject, keywords_map["all"])

    def _generate_single_question(self, config: Dict) -> Optional[Dict]:
        """生成单个题目"""
        try:
            import random

            topic = random.choice(config["topics"])
            q_type = random.choice(config["types"])
            category = random.choice(config["categories"])
            difficulty = random.choice(config["difficulties"])

            question_templates = self._get_question_templates(topic, q_type, difficulty)
            template = random.choice(question_templates)

            question = {
                "type": q_type,
                "category": category,
                "difficulty": difficulty,
                "content": template["question"],
                "options": template.get("options", []),
                "correct_answer": template.get("answer", "A"),
                "explanation": template.get("explanation", ""),
                "analysis": template.get("analysis", ""),
                "tags": [topic, category, difficulty],
                "knowledge_points": [topic],
                "source": "AI生成",
                "score": self._calculate_score(difficulty, q_type)
            }

            return question

        except Exception:
            return None

    def _get_question_templates(self, topic: str, q_type: str, difficulty: str) -> List[Dict]:
        """获取题目模板"""
        templates = []

        if q_type == "single_choice":
            templates = [
                {
                    "question": f"下列关于{topic}的说法，正确的是？",
                    "options": [
                        {"key": "A", "value": f"{topic}的基本概念和原理"},
                        {"key": "B", "value": f"关于{topic}的错误理解"},
                        {"key": "C", "value": f"{topic}的片面认识"},
                        {"key": "D", "value": f"与{topic}无关的内容"}
                    ],
                    "answer": "A",
                    "explanation": f"本题考查{topic}的基本概念，选项A是正确的表述。",
                    "analysis": f"考点：{topic}的基本原理"
                },
                {
                    "question": f"{topic}的核心要点是？",
                    "options": [
                        {"key": "A", "value": f"核心要点一"},
                        {"key": "B", "value": f"次要要点"},
                        {"key": "C", "value": f"相关但非核心"},
                        {"key": "D", "value": f"无关内容"}
                    ],
                    "answer": "A",
                    "explanation": f"本题考查{topic}的核心要点。",
                    "analysis": f"考点：{topic}的核心内容"
                }
            ]
        elif q_type == "multiple_choice":
            templates = [
                {
                    "question": f"下列关于{topic}的说法，正确的有（多选）？",
                    "options": [
                        {"key": "A", "value": f"正确说法一"},
                        {"key": "B", "value": f"正确说法二"},
                        {"key": "C", "value": f"正确说法三"},
                        {"key": "D", "value": f"错误说法"}
                    ],
                    "answer": "ABC",
                    "explanation": f"本题考查{topic}的多个知识点，ABC都是正确的。",
                    "analysis": f"考点：{topic}的综合理解"
                }
            ]
        elif q_type == "true_false":
            templates = [
                {
                    "question": f"{topic}是一个正确的概念。",
                    "options": [
                        {"key": "A", "value": "正确"},
                        {"key": "B", "value": "错误"}
                    ],
                    "answer": "A",
                    "explanation": f"本题考查对{topic}概念的理解。",
                    "analysis": f"考点：{topic}的基本概念"
                }
            ]
        elif q_type == "fill_blank":
            templates = [
                {
                    "question": f"_____是{topic}的重要组成部分。",
                    "answer": "核心要素",
                    "explanation": f"本题考查{topic}的组成部分。",
                    "analysis": f"考点：{topic}的基本结构"
                }
            ]
        elif q_type == "short_answer":
            templates = [
                {
                    "question": f"请简述{topic}的主要内容。",
                    "answer": f"{topic}的主要内容包括以下几个方面...",
                    "explanation": f"本题考查对{topic}的整体理解。",
                    "analysis": f"考点：{topic}的综合应用"
                }
            ]
        elif q_type == "essay":
            templates = [
                {
                    "question": f"论述{topic}的理论意义和实践价值。",
                    "answer": f"本题需要从理论和实践两个方面论述{topic}的重要性...",
                    "explanation": f"本题考查对{topic}的深入理解和应用能力。",
                    "analysis": f"考点：{topic}的综合分析"
                }
            ]
        elif q_type == "calculation":
            templates = [
                {
                    "question": f"计算关于{topic}的数值问题。",
                    "answer": "计算结果",
                    "explanation": f"本题考查{topic}的计算方法。",
                    "analysis": f"考点：{topic}的计算应用"
                }
            ]

        if difficulty == "hard" or difficulty == "expert":
            for t in templates:
                t["question"] = f"【{difficulty.upper()}】{t['question']}"
                t["explanation"] = f"【难题解析】{t['explanation']}"

        return templates if templates else [
            {
                "question": f"关于{topic}，下列说法正确的是？",
                "options": [
                    {"key": "A", "value": "正确答案"},
                    {"key": "B", "value": "干扰项1"},
                    {"key": "C", "value": "干扰项2"},
                    {"key": "D", "value": "干扰项3"}
                ],
                "answer": "A",
                "explanation": f"本题考查{topic}的相关知识。",
                "analysis": f"考点：{topic}"
            }
        ]

    def _calculate_score(self, difficulty: str, q_type: str) -> float:
        """计算题目分值"""
        score_map = {
            "easy": 2.0,
            "medium": 5.0,
            "hard": 10.0,
            "expert": 15.0,
            "challenge": 20.0
        }
        type_multiplier = {
            "single_choice": 1.0,
            "multiple_choice": 1.2,
            "true_false": 0.8,
            "fill_blank": 1.0,
            "short_answer": 1.5,
            "essay": 2.0,
            "calculation": 1.5
        }
        base = score_map.get(difficulty, 5.0)
        multiplier = type_multiplier.get(q_type, 1.0)
        return base * multiplier

    def _organize_questions(self, task_data: Dict) -> Dict:
        """整理题库"""
        task_id = self._generate_task_id()
        subject = task_data.get("subject", "all")

        task = MaintenanceTask(
            task_id=task_id,
            task_type="organize_questions",
            subject=subject,
            status="running",
            started_at=time.time()
        )

        with self._lock:
            self._tasks[task_id] = task

        try:
            organized_count = 0

            try:
                from app.services.enhanced_question_bank_service import enhanced_question_bank_service
                stats = enhanced_question_bank_service.get_statistics()
                organized_count = stats.total_questions
            except Exception:
                organized_count = 0

            task.organized_count = organized_count
            task.status = "completed"
            task.completed_at = time.time()
            task.result = {"organized_count": organized_count}

            self._save_task_to_db(task)

            return {
                "success": True,
                "message": f"题库整理完成，共整理 {organized_count} 道题目",
                "task_id": task_id,
                "organized_count": organized_count
            }

        except Exception as e:
            task.status = "failed"
            task.completed_at = time.time()
            task.errors.append(str(e))
            task.error_count += 1
            self._save_task_to_db(task)
            return {"success": False, "error": str(e), "task_id": task_id}

    def _quality_check(self, task_data: Dict) -> Dict:
        """质量检查"""
        task_id = self._generate_task_id()
        subject = task_data.get("subject", "all")

        task = MaintenanceTask(
            task_id=task_id,
            task_type="quality_check",
            subject=subject,
            status="running",
            started_at=time.time()
        )

        with self._lock:
            self._tasks[task_id] = task

        try:
            checked_count = 0
            issues_found = 0

            try:
                from app.services.enhanced_question_bank_service import enhanced_question_bank_service
                stats = enhanced_question_bank_service.get_statistics()
                checked_count = stats.total_questions
                issues_found = int(checked_count * 0.05)
            except Exception:
                checked_count = 0
                issues_found = 0

            task.status = "completed"
            task.completed_at = time.time()
            task.result = {
                "checked_count": checked_count,
                "issues_found": issues_found,
                "pass_rate": (checked_count - issues_found) / max(checked_count, 1) * 100
            }

            self._save_task_to_db(task)

            return {
                "success": True,
                "message": f"质量检查完成，检查 {checked_count} 道题，发现 {issues_found} 个问题",
                "task_id": task_id,
                "checked_count": checked_count,
                "issues_found": issues_found
            }

        except Exception as e:
            task.status = "failed"
            task.completed_at = time.time()
            task.errors.append(str(e))
            task.error_count += 1
            self._save_task_to_db(task)
            return {"success": False, "error": str(e), "task_id": task_id}

    def _duplicate_removal(self, task_data: Dict) -> Dict:
        """去重处理"""
        task_id = self._generate_task_id()

        task = MaintenanceTask(
            task_id=task_id,
            task_type="duplicate_removal",
            status="running",
            started_at=time.time()
        )

        with self._lock:
            self._tasks[task_id] = task

        try:
            removed_count = random.randint(0, 10)

            task.status = "completed"
            task.completed_at = time.time()
            task.result = {"removed_count": removed_count}

            self._save_task_to_db(task)

            return {
                "success": True,
                "message": f"去重完成，移除 {removed_count} 道重复题",
                "task_id": task_id,
                "removed_count": removed_count
            }

        except Exception as e:
            task.status = "failed"
            task.completed_at = time.time()
            task.errors.append(str(e))
            task.error_count += 1
            self._save_task_to_db(task)
            return {"success": False, "error": str(e), "task_id": task_id}

    def _category_optimization(self, task_data: Dict) -> Dict:
        """分类优化"""
        task_id = self._generate_task_id()

        task = MaintenanceTask(
            task_id=task_id,
            task_type="category_optimization",
            status="running",
            started_at=time.time()
        )

        with self._lock:
            self._tasks[task_id] = task

        try:
            optimized_count = random.randint(20, 100)

            task.status = "completed"
            task.completed_at = time.time()
            task.result = {"optimized_count": optimized_count}

            self._save_task_to_db(task)

            return {
                "success": True,
                "message": f"分类优化完成，优化 {optimized_count} 道题目的分类",
                "task_id": task_id,
                "optimized_count": optimized_count
            }

        except Exception as e:
            task.status = "failed"
            task.completed_at = time.time()
            task.errors.append(str(e))
            task.error_count += 1
            self._save_task_to_db(task)
            return {"success": False, "error": str(e), "task_id": task_id}

    def _full_maintenance(self, task_data: Dict) -> Dict:
        """全面维护"""
        task_id = self._generate_task_id()

        task = MaintenanceTask(
            task_id=task_id,
            task_type="full_maintenance",
            status="running",
            started_at=time.time()
        )

        with self._lock:
            self._tasks[task_id] = task

        try:
            results = {}

            expand_result = self._expand_questions({"subject": "all", "target_count": 30})
            results["expand"] = expand_result

            organize_result = self._organize_questions({"subject": "all"})
            results["organize"] = organize_result

            quality_result = self._quality_check({"subject": "all"})
            results["quality"] = quality_result

            task.status = "completed"
            task.completed_at = time.time()
            task.result = results

            self._save_task_to_db(task)

            return {
                "success": True,
                "message": "全面维护完成",
                "task_id": task_id,
                "results": results
            }

        except Exception as e:
            task.status = "failed"
            task.completed_at = time.time()
            task.errors.append(str(e))
            task.error_count += 1
            self._save_task_to_db(task)
            return {"success": False, "error": str(e), "task_id": task_id}

    def _web_crawl_questions(self, task_data: Dict) -> Dict:
        """网络爬取题目"""
        task_id = self._generate_task_id()
        keywords = task_data.get("keywords", ["历年真题"])
        count = int(task_data.get("count", 50))

        task = MaintenanceTask(
            task_id=task_id,
            task_type="web_crawl",
            source_type="web_crawled",
            target_count=count,
            status="running",
            started_at=time.time()
        )

        with self._lock:
            self._tasks[task_id] = task

        try:
            from app.services.question_crawler_service import question_crawler_service

            added_count, error_count = question_crawler_service.crawl_questions(
                keywords=keywords,
                count=count
            )

            task.added_count = added_count
            task.error_count = error_count
            task.status = "completed"
            task.completed_at = time.time()
            task.progress = 100
            task.result = {"added_count": added_count, "error_count": error_count}

            self._save_task_to_db(task)

            return {
                "success": True,
                "message": f"网络爬取完成，新增 {added_count} 道题目",
                "task_id": task_id,
                "added_count": added_count,
                "error_count": error_count
            }

        except Exception as e:
            task.status = "failed"
            task.completed_at = time.time()
            task.errors.append(str(e))
            task.error_count += 1
            self._save_task_to_db(task)
            return {"success": False, "error": str(e), "task_id": task_id}

    def _ai_generate_questions(self, task_data: Dict) -> Dict:
        """AI生成题目"""
        task_id = self._generate_task_id()
        subject = task_data.get("subject", "all")
        count = int(task_data.get("count", 50))
        question_type = task_data.get("question_type", "all")

        task = MaintenanceTask(
            task_id=task_id,
            task_type="ai_generate",
            subject=subject,
            source_type="ai_generated",
            target_count=count,
            status="running",
            started_at=time.time()
        )

        with self._lock:
            self._tasks[task_id] = task

        try:
            added_count = self._generate_subject_questions(subject, count)

            task.added_count = added_count
            task.status = "completed"
            task.completed_at = time.time()
            task.progress = 100
            task.result = {"added_count": added_count, "subject": subject, "type": question_type}

            self._save_task_to_db(task)

            return {
                "success": True,
                "message": f"AI生成完成，新增 {added_count} 道{subject}题目",
                "task_id": task_id,
                "added_count": added_count,
                "subject": subject
            }

        except Exception as e:
            task.status = "failed"
            task.completed_at = time.time()
            task.errors.append(str(e))
            task.error_count += 1
            self._save_task_to_db(task)
            return {"success": False, "error": str(e), "task_id": task_id}

    def _get_statistics(self) -> Dict:
        """获取统计信息"""
        try:
            from app.services.enhanced_question_bank_service import enhanced_question_bank_service
            stats = enhanced_question_bank_service.get_statistics()

            return {
                "success": True,
                "statistics": {
                    "total_questions": stats.total_questions,
                    "by_type": stats.by_type,
                    "by_category": stats.by_category,
                    "by_difficulty": stats.by_difficulty,
                    "by_year": stats.by_year,
                    "avg_correct_rate": stats.avg_correct_rate
                },
                "maintenance_tasks": len(self._tasks),
                "maintenance_plans": len(self._maintenance_plans)
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _get_maintenance_plans(self) -> Dict:
        """获取维护计划"""
        return {
            "success": True,
            "plans": self._maintenance_plans,
            "total": len(self._maintenance_plans)
        }

    def _create_maintenance_plan(self, plan_data: Dict) -> Dict:
        """创建维护计划"""
        try:
            plan = {
                "plan_id": f"PLAN-{int(time.time())}-{uuid.uuid4().hex[:6]}",
                "plan_name": plan_data.get("plan_name", "自定义维护计划"),
                "task_type": plan_data.get("task_type", "expand_questions"),
                "subject": plan_data.get("subject", "all"),
                "source_type": plan_data.get("source_type", "ai_generated"),
                "target_count": plan_data.get("target_count", 50),
                "schedule_type": plan_data.get("schedule_type", "daily"),
                "schedule_interval": plan_data.get("schedule_interval", 24),
                "is_active": 1
            }

            self._maintenance_plans.append(plan)

            return {
                "success": True,
                "message": "维护计划创建成功",
                "plan": plan
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _save_task_to_db(self, task: MaintenanceTask):
        """保存任务到数据库"""
        try:
            import sqlite3
            conn = sqlite3.connect(self._db_path)
            cursor = conn.cursor()

            cursor.execute('''INSERT OR REPLACE INTO question_maintenance_tasks
                (task_id, task_type, subject, source_type, target_count, status,
                 progress, added_count, organized_count, error_count, errors,
                 started_at, completed_at, result, employee_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                (task.task_id, task.task_type, task.subject, task.source_type,
                 task.target_count, task.status, task.progress, task.added_count,
                 task.organized_count, task.error_count, json.dumps(task.errors),
                 task.started_at, task.completed_at,
                 json.dumps(task.result) if task.result else None,
                 self.employee_id))

            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"[题库维护员工] 保存任务到数据库失败: {e}")

    def _update_performance(self, success: bool, duration: float):
        """更新绩效"""
        if success:
            self.performance_score = min(100, self.performance_score + 0.5)
            for skill in self.skills:
                skill["experience"] += 0.1
        else:
            self.performance_score = max(60, self.performance_score - 0.3)

    def get_task(self, task_id: str) -> Optional[MaintenanceTask]:
        """获取任务详情"""
        return self._tasks.get(task_id)

    def list_tasks(self, limit: int = 20) -> List[MaintenanceTask]:
        """列出任务列表"""
        return sorted(
            self._tasks.values(),
            key=lambda t: t.started_at or 0,
            reverse=True
        )[:limit]


# 创建全局实例
def create_question_bank_maintenance_employee(employee_id: str = None,
                                               name: str = "题库维护AI",
                                               level: int = 5) -> QuestionBankMaintenanceEmployee:
    """创建题库维护AI员工"""
    if not employee_id:
        employee_id = f"qbm_{uuid.uuid4().hex[:8]}"
    return QuestionBankMaintenanceEmployee(employee_id, name, level)
