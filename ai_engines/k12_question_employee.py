#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
K12题库专业AI员工
专门负责K12（基础教育）题目的生成、整理、更新，包括各学科各年级的题目
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logger = logging.getLogger(__name__)


class K12QuestionEmployee:
    """K12题库专业AI员工"""

    def __init__(self, employee_id: str, name: str, level: int = 1):
        self.employee_id = employee_id
        self.name = name
        self.level = level
        self.type = "k12_question"
        self.status = "active"
        self.task_count = 0
        self.success_count = 0
        self.failure_count = 0
        self.performance_score = 80 + level * 2

        self.skills = [
            {"name": "primary_education", "level": 5 + level, "experience": 0.0},
            {"name": "junior_high", "level": 5 + level, "experience": 0.0},
            {"name": "senior_high", "level": 5 + level, "experience": 0.0},
            {"name": "math_education", "level": 4 + level, "experience": 0.0},
            {"name": "chinese_education", "level": 4 + level, "experience": 0.0},
            {"name": "english_education", "level": 4 + level, "experience": 0.0},
            {"name": "science_education", "level": 4 + level, "experience": 0.0},
            {"name": "exam_analysis", "level": 4 + level, "experience": 0.0}
        ]

        self._lock = threading.RLock()
        self._db_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'app.db'
        )

        self._subjects = {
            "primary": {
                "name": "小学",
                "grades": ["一年级", "二年级", "三年级", "四年级", "五年级", "六年级"],
                "subjects": ["语文", "数学", "英语", "科学", "道德与法治"]
            },
            "junior": {
                "name": "初中",
                "grades": ["初一", "初二", "初三"],
                "subjects": ["语文", "数学", "英语", "物理", "化学", "生物", "历史", "地理", "政治"]
            },
            "senior": {
                "name": "高中",
                "grades": ["高一", "高二", "高三"],
                "subjects": ["语文", "数学", "英语", "物理", "化学", "生物", "历史", "地理", "政治"]
            }
        }

        self._question_sources = [
            "历年真题", "模拟试题", "单元测试", "期中考试", "期末考试",
            "高频考点", "易错题型", "压轴题", "竞赛题", "自主招生题"
        ]

        logger.info(f"[K12题库员工] 创建: {self.name} ({self.employee_id}) 级别: {self.level}")

    def start(self):
        """启动员工"""
        self.status = "active"
        logger.info(f"[K12题库员工] {self.name} 已启动")

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
            "supported_stages": list(self._subjects.keys())
        }

    def execute_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行任务"""
        self.task_count += 1
        start_time = time.time()

        try:
            task_type = task_data.get("task_type", "generate_questions")

            if task_type == "generate_questions":
                result = self._generate_questions(task_data)
            elif task_type == "generate_real_exam":
                result = self._generate_real_exam_questions(task_data)
            elif task_type == "generate_high_frequency":
                result = self._generate_high_frequency_questions(task_data)
            elif task_type == "generate_competition":
                result = self._generate_competition_questions(task_data)
            elif task_type == "generate_self_admission":
                result = self._generate_self_admission_questions(task_data)
            elif task_type == "generate_by_stage":
                result = self._generate_by_stage(task_data)
            elif task_type == "get_statistics":
                result = self._get_statistics()
            elif task_type == "get_subjects":
                result = self._get_subjects()
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
            logger.error(f"[K12题库员工] 任务执行失败: {self.name}, 错误: {e}")
            return {
                "success": False,
                "error": str(e),
                "execution_time": time.time() - start_time,
                "employee_id": self.employee_id,
                "employee_name": self.name
            }

    def _generate_questions(self, task_data: Dict) -> Dict:
        """生成K12题目"""
        count = int(task_data.get("count", 50))
        stage = task_data.get("stage", "all")
        subject = task_data.get("subject", "all")
        question_type = task_data.get("question_type", "all")

        generated = []

        try:
            from app.services.enhanced_question_bank_service import enhanced_question_bank_service

            for _ in range(count):
                try:
                    question = self._create_k12_question(stage, subject, question_type)
                    if question:
                        enhanced_question_bank_service.add_question(question)
                        generated.append(question)
                except Exception:
                    continue

            return {
                "success": True,
                "message": f"成功生成 {len(generated)} 道K12题目",
                "generated_count": len(generated),
                "stage": stage,
                "subject": subject
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _create_k12_question(self, stage: str, subject: str, q_type: str) -> Optional[Dict]:
        """创建单个K12题目"""
        try:
            if stage == "all":
                stage = random.choice(["primary", "junior", "senior"])

            stage_info = self._subjects.get(stage, self._subjects["junior"])

            if subject == "all":
                subject = random.choice(stage_info["subjects"])

            grade = random.choice(stage_info["grades"])

            if q_type == "all":
                q_type = random.choice([
                    "single_choice", "multiple_choice", "true_false",
                    "fill_blank", "calculation", "short_answer"
                ])

            source = random.choice(self._question_sources)
            difficulty = random.choice(["easy", "medium", "hard"])

            content = self._generate_question_content(stage, subject, grade, q_type, difficulty)

            question = {
                "type": q_type,
                "category": self._get_category_from_source(source),
                "difficulty": difficulty,
                "content": f"【{grade}{subject}】{content}",
                "options": self._generate_options(subject, q_type),
                "correct_answer": self._generate_answer(q_type),
                "explanation": f"本题考查{grade}{subject}的相关知识点。",
                "analysis": f"考点：{subject}知识点",
                "tags": ["K12", stage_info["name"], grade, subject, source, difficulty],
                "knowledge_points": [subject],
                "source": f"AI生成-K12{source}",
                "score": self._calculate_score(difficulty, q_type),
                "stage": stage,
                "grade": grade,
                "subject_k12": subject
            }

            return question

        except Exception as e:
            logger.error(f"[K12题库员工] 创建题目失败: {e}")
            return None

    def _generate_question_content(self, stage: str, subject: str, grade: str,
                                    q_type: str, difficulty: str) -> str:
        """生成题目内容"""
        content_templates = {
            "语文": [
                "下列词语中，加点字的读音全部正确的一项是？",
                "下列句子中，没有语病的一项是？",
                "对下列句子所用修辞手法判断正确的一项是？",
                "下列关于文学常识的表述，不正确的一项是？",
                "阅读下面的文字，回答问题。",
                "下列加点词语使用正确的一项是？"
            ],
            "数学": [
                "计算下列各题：",
                "解方程：",
                "下列说法正确的是？",
                "如图所示，已知条件如下，求未知量。",
                "化简下列各式：",
                "证明下列命题："
            ],
            "英语": [
                "Choose the best answer:",
                "Fill in the blanks with proper words:",
                "Which of the following is correct?",
                "Choose the correct form of the verb:",
                "Read the passage and answer the questions:",
                "Complete the following sentences:"
            ],
            "物理": [
                "下列说法正确的是？",
                "计算下列物理量：",
                "如图所示的电路中，求未知量。",
                "下列关于物理概念的表述，正确的是？",
                "分析下列物理现象：",
                "推导下列公式："
            ],
            "化学": [
                "下列化学方程式书写正确的是？",
                "下列说法正确的是？",
                "计算下列化学问题：",
                "下列物质分类正确的是？",
                "完成下列化学反应方程式：",
                "下列实验操作正确的是？"
            ],
            "生物": [
                "下列说法正确的是？",
                "下列关于生物概念的表述，正确的是？",
                "分析下列生物现象：",
                "下列关于细胞的说法，正确的是？",
                "下列遗传问题的解答，正确的是？",
                "下列关于生态系统的说法，正确的是？"
            ],
            "历史": [
                "下列说法正确的是？",
                "下列历史事件按时间顺序排列正确的是？",
                "下列关于历史人物的表述，正确的是？",
                "分析下列历史现象的原因：",
                "下列关于历史制度的说法，正确的是？",
                "简述下列历史事件的意义："
            ],
            "地理": [
                "下列说法正确的是？",
                "下列关于地理概念的表述，正确的是？",
                "读图回答下列问题：",
                "下列关于气候的说法，正确的是？",
                "下列关于地形的说法，正确的是？",
                "分析下列地理现象的成因："
            ],
            "政治": [
                "下列说法正确的是？",
                "下列关于政治概念的表述，正确的是？",
                "分析下列政治现象：",
                "下列关于制度的说法，正确的是？",
                "下列关于权利义务的说法，正确的是？",
                "简述下列问题："
            ],
            "科学": [
                "下列说法正确的是？",
                "下列关于科学概念的表述，正确的是？",
                "观察下列实验现象：",
                "下列关于自然现象的说法，正确的是？",
                "完成下列实验：",
                "下列科学探究的步骤，正确的是？"
            ],
            "道德与法治": [
                "下列说法正确的是？",
                "下列关于道德的表述，正确的是？",
                "下列行为符合道德规范的是？",
                "下列关于法律的说法，正确的是？",
                "分析下列情境：",
                "下列做法正确的是？"
            ]
        }

        templates = content_templates.get(subject, content_templates["语文"])
        return random.choice(templates)

    def _generate_options(self, subject: str, q_type: str) -> List[Dict]:
        """生成选项"""
        if q_type not in ["single_choice", "multiple_choice"]:
            return []

        option_bases = {
            "语文": ["正确答案", "近义词干扰", "反义词干扰", "无关选项"],
            "数学": ["正确答案", "计算错误答案", "概念混淆答案", "单位错误答案"],
            "英语": ["correct answer", "grammar error", "vocabulary error", "meaning error"],
            "物理": ["正确答案", "公式错误答案", "单位错误答案", "概念错误答案"],
            "化学": ["正确答案", "配平错误答案", "概念混淆答案", "计算错误答案"],
            "生物": ["正确答案", "概念错误答案", "张冠李戴答案", "无关选项"],
            "历史": ["正确答案", "时间错误答案", "人物混淆答案", "事件顺序错误"],
            "地理": ["正确答案", "概念错误答案", "位置错误答案", "成因错误答案"],
            "政治": ["正确答案", "概念混淆答案", "表述错误答案", "无关选项"]
        }

        bases = option_bases.get(subject, option_bases["语文"])
        return [{"key": chr(65 + i), "value": base} for i, base in enumerate(bases)]

    def _generate_answer(self, q_type: str) -> str:
        """生成答案"""
        if q_type == "multiple_choice":
            return random.choice(["ABC", "ABD", "ACD", "BCD", "ABCD"])
        elif q_type == "true_false":
            return random.choice(["A", "B"])
        else:
            return "A"

    def _get_category_from_source(self, source: str) -> str:
        """根据来源获取类别"""
        category_map = {
            "历年真题": "real_exam",
            "模拟试题": "special_topic",
            "单元测试": "special_topic",
            "期中考试": "special_topic",
            "期末考试": "special_topic",
            "高频考点": "must_know",
            "易错题型": "error_prone",
            "压轴题": "final",
            "竞赛题": "final",
            "自主招生题": "bonus"
        }
        return category_map.get(source, "special_topic")

    def _calculate_score(self, difficulty: str, q_type: str) -> float:
        """计算分值"""
        score_map = {"easy": 2.0, "medium": 5.0, "hard": 10.0, "expert": 15.0}
        type_multiplier = {
            "single_choice": 1.0, "multiple_choice": 1.5, "true_false": 0.5,
            "fill_blank": 1.0, "calculation": 1.5, "short_answer": 2.0,
            "essay": 3.0
        }
        base = score_map.get(difficulty, 5.0)
        multiplier = type_multiplier.get(q_type, 1.0)
        return base * multiplier

    def _generate_real_exam_questions(self, task_data: Dict) -> Dict:
        """生成历年真题风格题目"""
        count = int(task_data.get("count", 30))
        stage = task_data.get("stage", "senior")
        subject = task_data.get("subject", "all")
        years = task_data.get("years", [2020, 2021, 2022, 2023, 2024, 2025])

        generated = []

        try:
            from app.services.enhanced_question_bank_service import enhanced_question_bank_service

            for i in range(count):
                year = random.choice(years)
                question = self._create_k12_question(stage, subject, "single_choice")
                if question:
                    question["category"] = "real_exam"
                    question["content"] = f"【{year}年真题】{question['content']}"
                    question["year"] = year
                    question["source"] = f"AI生成-{year}年真题风格"
                    enhanced_question_bank_service.add_question(question)
                    generated.append(question)

            return {
                "success": True,
                "message": f"成功生成 {len(generated)} 道历年真题风格题目",
                "generated_count": len(generated),
                "years": years,
                "stage": stage
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _generate_high_frequency_questions(self, task_data: Dict) -> Dict:
        """生成高频练习题"""
        count = int(task_data.get("count", 40))
        stage = task_data.get("stage", "all")
        subject = task_data.get("subject", "all")

        generated = []

        try:
            from app.services.enhanced_question_bank_service import enhanced_question_bank_service

            for i in range(count):
                question = self._create_k12_question(stage, subject, "all")
                if question:
                    question["category"] = "must_know"
                    question["tags"].append("高频考点")
                    question["tags"].append("必考题")
                    question["source"] = "AI生成-高频考点"
                    enhanced_question_bank_service.add_question(question)
                    generated.append(question)

            return {
                "success": True,
                "message": f"成功生成 {len(generated)} 道高频练习题",
                "generated_count": len(generated)
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _generate_competition_questions(self, task_data: Dict) -> Dict:
        """生成竞赛题"""
        count = int(task_data.get("count", 20))
        subject = task_data.get("subject", "数学")

        generated = []

        try:
            from app.services.enhanced_question_bank_service import enhanced_question_bank_service

            competition_types = ["全国联赛", "奥林匹克竞赛", "希望杯", "华罗庚金杯", "五大学科竞赛"]

            for i in range(count):
                competition = random.choice(competition_types)
                question = self._create_k12_question("senior", subject, "calculation")
                if question:
                    question["category"] = "final"
                    question["difficulty"] = "expert"
                    question["content"] = f"【{competition}竞赛题】{question['content']}"
                    question["tags"].extend(["竞赛题", competition])
                    question["source"] = f"AI生成-{competition}风格"
                    question["score"] = 20.0
                    enhanced_question_bank_service.add_question(question)
                    generated.append(question)

            return {
                "success": True,
                "message": f"成功生成 {len(generated)} 道竞赛题",
                "generated_count": len(generated),
                "competition_types": competition_types
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _generate_self_admission_questions(self, task_data: Dict) -> Dict:
        """生成自主招生题"""
        count = int(task_data.get("count", 20))

        generated = []

        try:
            from app.services.enhanced_question_bank_service import enhanced_question_bank_service

            schools = ["清北", "华五", "C9联盟", "985高校", "211高校", "双一流大学"]

            for i in range(count):
                school = random.choice(schools)
                question = self._create_k12_question("senior", "all", "all")
                if question:
                    question["category"] = "bonus"
                    question["difficulty"] = "hard"
                    question["content"] = f"【{school}自主招生】{question['content']}"
                    question["tags"].extend(["自主招生", school])
                    question["source"] = f"AI生成-{school}自主招生风格"
                    question["score"] = 15.0
                    enhanced_question_bank_service.add_question(question)
                    generated.append(question)

            return {
                "success": True,
                "message": f"成功生成 {len(generated)} 道自主招生题",
                "generated_count": len(generated),
                "schools": schools
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _generate_by_stage(self, task_data: Dict) -> Dict:
        """按学段生成题目"""
        count = int(task_data.get("count", 100))
        stage = task_data.get("stage", "junior")

        generated = []

        try:
            from app.services.enhanced_question_bank_service import enhanced_question_bank_service

            stage_info = self._subjects.get(stage, self._subjects["junior"])
            subjects = stage_info["subjects"]
            per_subject = max(1, count // len(subjects))

            for subject in subjects:
                for _ in range(per_subject):
                    question = self._create_k12_question(stage, subject, "all")
                    if question:
                        enhanced_question_bank_service.add_question(question)
                        generated.append(question)

            return {
                "success": True,
                "message": f"成功生成 {len(generated)} 道{stage_info['name']}题目",
                "generated_count": len(generated),
                "stage": stage,
                "subjects": subjects
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _get_statistics(self) -> Dict:
        """获取统计信息"""
        try:
            from app.services.enhanced_question_bank_service import enhanced_question_bank_service
            stats = enhanced_question_bank_service.get_statistics()

            return {
                "success": True,
                "total_questions": stats.total_questions,
                "by_type": stats.by_type,
                "by_category": stats.by_category,
                "by_difficulty": stats.by_difficulty
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _get_subjects(self) -> Dict:
        """获取K12学科信息"""
        return {
            "success": True,
            "subjects": self._subjects,
            "question_sources": self._question_sources
        }

    def _update_performance(self, success: bool, duration: float):
        """更新绩效"""
        if success:
            self.performance_score = min(100, self.performance_score + 0.5)
            for skill in self.skills:
                skill["experience"] += 0.1
        else:
            self.performance_score = max(60, self.performance_score - 0.3)


def create_k12_question_employee(employee_id: str = None,
                                  name: str = "K12题库AI",
                                  level: int = 5) -> K12QuestionEmployee:
    """创建K12题库AI员工"""
    if not employee_id:
        employee_id = f"k12_{uuid.uuid4().hex[:8]}"
    return K12QuestionEmployee(employee_id, name, level)
