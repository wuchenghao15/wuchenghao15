#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
政治题库专业AI员工
专门负责政治题目的生成、整理、更新，包括时事政治、历年真题等
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


class PoliticsQuestionEmployee:
    """政治题库专业AI员工"""

    def __init__(self, employee_id: str, name: str, level: int = 1):
        self.employee_id = employee_id
        self.name = name
        self.level = level
        self.type = "politics_question"
        self.status = "active"
        self.task_count = 0
        self.success_count = 0
        self.failure_count = 0
        self.performance_score = 80 + level * 2

        self.skills = [
            {"name": "politics_theory", "level": 6 + level, "experience": 0.0},
            {"name": "current_affairs", "level": 5 + level, "experience": 0.0},
            {"name": "exam_analysis", "level": 5 + level, "experience": 0.0},
            {"name": "question_generation", "level": 5 + level, "experience": 0.0},
            {"name": "answer_analysis", "level": 4 + level, "experience": 0.0},
            {"name": "hot_topic_tracking", "level": 5 + level, "experience": 0.0}
        ]

        self._lock = threading.RLock()
        self._db_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'app.db'
        )

        self._politics_topics = {
            "marxism": {
                "name": "马克思主义基本原理",
                "sub_topics": ["唯物论", "辩证法", "认识论", "历史唯物主义", "政治经济学", "科学社会主义"],
                "weight": 0.20
            },
            "mao_zedong": {
                "name": "毛泽东思想",
                "sub_topics": ["新民主主义革命理论", "社会主义改造理论", "社会主义建设道路探索", "毛泽东思想活的灵魂"],
                "weight": 0.15
            },
            "socialism_with_chinese_characteristics": {
                "name": "中国特色社会主义理论体系",
                "sub_topics": ["邓小平理论", "三个代表重要思想", "科学发展观", "习近平新时代中国特色社会主义思想"],
                "weight": 0.30
            },
            "morality_and_law": {
                "name": "思想道德修养与法律基础",
                "sub_topics": ["理想信念", "爱国主义", "人生价值观", "道德修养", "法律基础", "法治观念"],
                "weight": 0.15
            },
            "modern_history": {
                "name": "中国近现代史纲要",
                "sub_topics": ["旧民主主义革命", "新民主主义革命", "社会主义革命", "改革开放", "中国特色社会主义新时代"],
                "weight": 0.10
            },
            "current_politics": {
                "name": "形势与政策",
                "sub_topics": ["国内时政", "国际形势", "党和国家重大方针政策", "重要会议精神", "重大事件"],
                "weight": 0.10
            }
        }

        self._question_templates = self._init_question_templates()

        logger.info(f"[政治题库员工] 创建: {self.name} ({self.employee_id}) 级别: {self.level}")

    def _init_question_templates(self) -> Dict:
        """初始化题目模板"""
        return {
            "single_choice": [
                {
                    "pattern": "马克思主义哲学认为，_____是世界的本原。",
                    "options": ["物质", "意识", "精神", "理念"],
                    "answer": "A",
                    "category": "marxism",
                    "sub_topic": "唯物论",
                    "difficulty": "easy"
                },
                {
                    "pattern": "唯物辩证法的实质和核心是_____。",
                    "options": ["对立统一规律", "质量互变规律", "否定之否定规律", "联系和发展"],
                    "answer": "A",
                    "category": "marxism",
                    "sub_topic": "辩证法",
                    "difficulty": "medium"
                },
                {
                    "pattern": "实践是检验真理的唯一标准，这是由_____决定的。",
                    "options": ["真理的本性和实践的特点", "真理的相对性", "真理的绝对性", "真理的具体性"],
                    "answer": "A",
                    "category": "marxism",
                    "sub_topic": "认识论",
                    "difficulty": "medium"
                },
                {
                    "pattern": "新民主主义革命的三大法宝是_____。",
                    "options": ["统一战线、武装斗争、党的建设", "实事求是、群众路线、独立自主",
                              "理论联系实际、密切联系群众、批评与自我批评", "解放思想、实事求是、与时俱进"],
                    "answer": "A",
                    "category": "mao_zedong",
                    "sub_topic": "新民主主义革命理论",
                    "difficulty": "easy"
                },
                {
                    "pattern": "习近平新时代中国特色社会主义思想的核心要义是_____。",
                    "options": ["坚持和发展中国特色社会主义", "实现中华民族伟大复兴",
                              "全面建设社会主义现代化国家", "推进国家治理体系现代化"],
                    "answer": "A",
                    "category": "socialism_with_chinese_characteristics",
                    "sub_topic": "习近平新时代中国特色社会主义思想",
                    "difficulty": "easy"
                },
                {
                    "pattern": "社会主义核心价值观在国家层面的价值目标是_____。",
                    "options": ["富强、民主、文明、和谐", "自由、平等、公正、法治",
                              "爱国、敬业、诚信、友善", "独立、自主、和平、发展"],
                    "answer": "A",
                    "category": "morality_and_law",
                    "sub_topic": "人生价值观",
                    "difficulty": "easy"
                },
                {
                    "pattern": "中国近代史的开端是_____。",
                    "options": ["鸦片战争", "甲午战争", "辛亥革命", "五四运动"],
                    "answer": "A",
                    "category": "modern_history",
                    "sub_topic": "旧民主主义革命",
                    "difficulty": "easy"
                },
                {
                    "pattern": "新时代我国社会主要矛盾是_____。",
                    "options": ["人民日益增长的美好生活需要和不平衡不充分的发展之间的矛盾",
                              "人民日益增长的物质文化需要同落后的社会生产之间的矛盾",
                              "无产阶级和资产阶级的矛盾",
                              "社会主义和资本主义的矛盾"],
                    "answer": "A",
                    "category": "socialism_with_chinese_characteristics",
                    "sub_topic": "习近平新时代中国特色社会主义思想",
                    "difficulty": "medium"
                }
            ],
            "multiple_choice": [
                {
                    "pattern": "马克思主义的三个组成部分是_____。",
                    "options": ["马克思主义哲学", "马克思主义政治经济学", "科学社会主义", "空想社会主义"],
                    "answer": "ABC",
                    "category": "marxism",
                    "sub_topic": "马克思主义基本原理",
                    "difficulty": "easy"
                },
                {
                    "pattern": "毛泽东思想活的灵魂是_____。",
                    "options": ["实事求是", "群众路线", "独立自主", "艰苦奋斗"],
                    "answer": "ABC",
                    "category": "mao_zedong",
                    "sub_topic": "毛泽东思想活的灵魂",
                    "difficulty": "easy"
                },
                {
                    "pattern": "\"四个全面\"战略布局包括_____。",
                    "options": ["全面建设社会主义现代化国家", "全面深化改革", "全面依法治国", "全面从严治党"],
                    "answer": "ABCD",
                    "category": "socialism_with_chinese_characteristics",
                    "sub_topic": "习近平新时代中国特色社会主义思想",
                    "difficulty": "medium"
                },
                {
                    "pattern": "社会主义核心价值观的内容包括_____层面。",
                    "options": ["国家层面", "社会层面", "公民层面", "国际层面"],
                    "answer": "ABC",
                    "category": "morality_and_law",
                    "sub_topic": "人生价值观",
                    "difficulty": "easy"
                }
            ],
            "true_false": [
                {
                    "pattern": "物质是标志客观实在的哲学范畴。",
                    "answer": True,
                    "category": "marxism",
                    "sub_topic": "唯物论",
                    "difficulty": "easy"
                },
                {
                    "pattern": "实践是认识的来源和发展动力。",
                    "answer": True,
                    "category": "marxism",
                    "sub_topic": "认识论",
                    "difficulty": "easy"
                },
                {
                    "pattern": "中华人民共和国的成立标志着社会主义制度在中国的确立。",
                    "answer": False,
                    "category": "modern_history",
                    "sub_topic": "社会主义革命",
                    "difficulty": "medium"
                },
                {
                    "pattern": "改革开放是决定当代中国命运的关键抉择。",
                    "answer": True,
                    "category": "modern_history",
                    "sub_topic": "改革开放",
                    "difficulty": "easy"
                }
            ],
            "short_answer": [
                {
                    "pattern": "简述马克思主义物质观的理论意义。",
                    "answer": "马克思主义物质观的理论意义：第一，坚持了物质的客观实在性原则...",
                    "category": "marxism",
                    "sub_topic": "唯物论",
                    "difficulty": "medium"
                },
                {
                    "pattern": "为什么说实践是检验真理的唯一标准？",
                    "answer": "实践是检验真理的唯一标准，这是由真理的本性和实践的特点决定的...",
                    "category": "marxism",
                    "sub_topic": "认识论",
                    "difficulty": "medium"
                },
                {
                    "pattern": "简述习近平新时代中国特色社会主义思想的历史地位。",
                    "answer": "习近平新时代中国特色社会主义思想的历史地位：1. 马克思主义中国化最新成果...",
                    "category": "socialism_with_chinese_characteristics",
                    "sub_topic": "习近平新时代中国特色社会主义思想",
                    "difficulty": "medium"
                }
            ],
            "essay": [
                {
                    "pattern": "论述矛盾普遍性和特殊性辩证关系原理及其对建设中国特色社会主义的指导意义。",
                    "answer": "一、矛盾普遍性和特殊性的辩证关系原理... 二、对建设中国特色社会主义的指导意义...",
                    "category": "marxism",
                    "sub_topic": "辩证法",
                    "difficulty": "hard"
                },
                {
                    "pattern": "论述中国共产党领导是中国特色社会主义最本质的特征。",
                    "answer": "一、这是由科学社会主义的理论逻辑所决定的... 二、这是由中国特色社会主义产生与发展的历史逻辑所决定的...",
                    "category": "socialism_with_chinese_characteristics",
                    "sub_topic": "习近平新时代中国特色社会主义思想",
                    "difficulty": "hard"
                }
            ]
        }

    def start(self):
        """启动员工"""
        self.status = "active"
        logger.info(f"[政治题库员工] {self.name} 已启动")

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
            "politics_topics": list(self._politics_topics.keys())
        }

    def execute_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行任务"""
        self.task_count += 1
        start_time = time.time()

        try:
            task_type = task_data.get("task_type", "generate_questions")

            if task_type == "generate_questions":
                result = self._generate_questions(task_data)
            elif task_type == "generate_current_affairs":
                result = self._generate_current_affairs_questions(task_data)
            elif task_type == "generate_real_exam":
                result = self._generate_real_exam_questions(task_data)
            elif task_type == "generate_high_frequency":
                result = self._generate_high_frequency_questions(task_data)
            elif task_type == "get_statistics":
                result = self._get_statistics()
            elif task_type == "get_topics":
                result = self._get_topics()
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
            logger.error(f"[政治题库员工] 任务执行失败: {self.name}, 错误: {e}")
            return {
                "success": False,
                "error": str(e),
                "execution_time": time.time() - start_time,
                "employee_id": self.employee_id,
                "employee_name": self.name
            }

    def _generate_questions(self, task_data: Dict) -> Dict:
        """生成政治题目"""
        count = int(task_data.get("count", 50))
        question_type = task_data.get("question_type", "all")
        category = task_data.get("category", "all")
        difficulty = task_data.get("difficulty", "all")

        generated = []

        try:
            from app.services.enhanced_question_bank_service import enhanced_question_bank_service

            for _ in range(count):
                try:
                    question = self._create_single_question(question_type, category, difficulty)
                    if question:
                        enhanced_question_bank_service.add_question(question)
                        generated.append(question)
                except Exception:
                    continue

            return {
                "success": True,
                "message": f"成功生成 {len(generated)} 道政治题目",
                "generated_count": len(generated),
                "questions": generated[:10]
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _create_single_question(self, q_type: str, category: str, difficulty: str) -> Optional[Dict]:
        """创建单个政治题目"""
        try:
            if q_type == "all":
                q_type = random.choice(["single_choice", "multiple_choice", "true_false", "short_answer", "essay"])

            templates = self._question_templates.get(q_type, [])
            if not templates:
                return None

            if category != "all":
                templates = [t for t in templates if t.get("category") == category]
            if difficulty != "all":
                templates = [t for t in templates if t.get("difficulty") == difficulty]

            if not templates:
                templates = self._question_templates.get("single_choice", [])

            template = random.choice(templates)

            question = {
                "type": q_type,
                "category": "must_know" if template.get("difficulty") in ["easy", "medium"] else "real_exam",
                "difficulty": template.get("difficulty", "medium"),
                "content": template["pattern"],
                "options": [{"key": chr(65 + i), "value": opt} for i, opt in enumerate(template.get("options", []))],
                "correct_answer": template.get("answer", "A"),
                "explanation": f"本题考查{self._politics_topics.get(template.get('category', 'marxism'), {}).get('name', '')}中的{template.get('sub_topic', '')}知识点。",
                "analysis": f"考点：{template.get('sub_topic', '')}",
                "tags": ["政治", template.get("category", ""), template.get("sub_topic", ""), template.get("difficulty", "")],
                "knowledge_points": [template.get("sub_topic", "")],
                "source": "AI生成-政治题库",
                "score": self._calculate_score(template.get("difficulty", "medium"), q_type)
            }

            return question

        except Exception as e:
            logger.error(f"[政治题库员工] 创建题目失败: {e}")
            return None

    def _generate_current_affairs_questions(self, task_data: Dict) -> Dict:
        """生成时事政治题目"""
        count = int(task_data.get("count", 20))

        current_topics = [
            "二十届三中全会精神", "全国两会精神", "十四五规划", "中国式现代化",
            "高质量发展", "新发展理念", "新发展格局", "共同富裕",
            "科技自立自强", "乡村振兴", "双碳目标", "一带一路"
        ]

        generated = []

        try:
            from app.services.enhanced_question_bank_service import enhanced_question_bank_service

            for i in range(count):
                topic = random.choice(current_topics)
                q_type = random.choice(["single_choice", "multiple_choice", "true_false"])

                question = {
                    "type": q_type,
                    "category": "real_exam",
                    "difficulty": "medium",
                    "content": f"关于{topic}，下列说法正确的是？",
                    "options": [
                        {"key": "A", "value": f"{topic}是党和国家的重要战略部署"},
                        {"key": "B", "value": f"{topic}与经济发展无关"},
                        {"key": "C", "value": f"{topic}是临时政策"},
                        {"key": "D", "value": f"以上说法都不对"}
                    ],
                    "correct_answer": "A",
                    "explanation": f"本题考查时事政治中的{topic}相关内容。",
                    "analysis": f"考点：{topic}",
                    "tags": ["政治", "时事政治", topic],
                    "knowledge_points": [topic, "形势与政策"],
                    "source": "AI生成-时事政治",
                    "score": 5.0,
                    "year": 2026
                }

                enhanced_question_bank_service.add_question(question)
                generated.append(question)

            return {
                "success": True,
                "message": f"成功生成 {len(generated)} 道时事政治题目",
                "generated_count": len(generated),
                "topics": current_topics
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _generate_real_exam_questions(self, task_data: Dict) -> Dict:
        """生成历年真题风格题目"""
        count = int(task_data.get("count", 30))
        years = task_data.get("years", [2023, 2024, 2025])

        generated = []

        try:
            from app.services.enhanced_question_bank_service import enhanced_question_bank_service

            for i in range(count):
                year = random.choice(years)
                q_type = random.choice(["single_choice", "multiple_choice", "analysis"])

                categories = list(self._politics_topics.keys())
                category = random.choice(categories)
                category_info = self._politics_topics[category]
                sub_topic = random.choice(category_info["sub_topics"])

                question = {
                    "type": q_type,
                    "category": "real_exam",
                    "difficulty": random.choice(["medium", "hard"]),
                    "content": f"【{year}年考研政治{category_info['name']}】关于{sub_topic}的正确表述是？",
                    "options": [
                        {"key": "A", "value": f"选项A：关于{sub_topic}的正确表述"},
                        {"key": "B", "value": f"选项B：干扰项"},
                        {"key": "C", "value": f"选项C：干扰项"},
                        {"key": "D", "value": f"选项D：干扰项"}
                    ],
                    "correct_answer": "A",
                    "explanation": f"本题出自{year}年考研政治，考查{category_info['name']}中的{sub_topic}知识点。",
                    "analysis": f"真题解析：{year}年考查{sub_topic}",
                    "tags": ["政治", "历年真题", str(year), category, sub_topic],
                    "knowledge_points": [sub_topic],
                    "source": f"AI生成-{year}年真题风格",
                    "score": random.choice([2.0, 5.0, 10.0]),
                    "year": year
                }

                enhanced_question_bank_service.add_question(question)
                generated.append(question)

            return {
                "success": True,
                "message": f"成功生成 {len(generated)} 道历年真题风格题目",
                "generated_count": len(generated),
                "years": years
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _generate_high_frequency_questions(self, task_data: Dict) -> Dict:
        """生成高频练习题"""
        count = int(task_data.get("count", 40))

        generated = []

        try:
            from app.services.enhanced_question_bank_service import enhanced_question_bank_service

            high_freq_topics = [
                "物质与意识", "对立统一规律", "实践与认识", "社会基本矛盾",
                "新民主主义革命", "社会主义改造", "改革开放",
                "中国特色社会主义", "新时代主要矛盾", "社会主义核心价值观",
                "四个全面", "五位一体", "新发展理念", "党的建设"
            ]

            for i in range(count):
                topic = random.choice(high_freq_topics)
                q_type = random.choice(["single_choice", "multiple_choice", "true_false"])

                question = {
                    "type": q_type,
                    "category": "must_know",
                    "difficulty": "medium",
                    "content": f"【高频考点】{topic}的核心要点是？",
                    "options": [
                        {"key": "A", "value": f"核心要点：{topic}的本质内容"},
                        {"key": "B", "value": f"次要要点"},
                        {"key": "C", "value": f"相关但非核心"},
                        {"key": "D", "value": f"无关内容"}
                    ],
                    "correct_answer": "A",
                    "explanation": f"本题为高频考点，考查{topic}的核心内容。",
                    "analysis": f"高频考点解析：{topic}",
                    "tags": ["政治", "高频考点", "必考题", topic],
                    "knowledge_points": [topic],
                    "source": "AI生成-高频考点",
                    "score": 2.0
                }

                enhanced_question_bank_service.add_question(question)
                generated.append(question)

            return {
                "success": True,
                "message": f"成功生成 {len(generated)} 道高频练习题",
                "generated_count": len(generated),
                "high_freq_topics": high_freq_topics
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _calculate_score(self, difficulty: str, q_type: str) -> float:
        """计算分值"""
        score_map = {"easy": 1.0, "medium": 2.0, "hard": 5.0, "expert": 10.0}
        type_multiplier = {
            "single_choice": 1.0, "multiple_choice": 1.5, "true_false": 0.5,
            "fill_blank": 1.0, "short_answer": 3.0, "essay": 5.0, "analysis": 5.0
        }
        base = score_map.get(difficulty, 2.0)
        multiplier = type_multiplier.get(q_type, 1.0)
        return base * multiplier

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
                "politics_topics": self._politics_topics
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _get_topics(self) -> Dict:
        """获取政治学科主题"""
        return {
            "success": True,
            "topics": self._politics_topics,
            "total_topics": len(self._politics_topics)
        }

    def _update_performance(self, success: bool, duration: float):
        """更新绩效"""
        if success:
            self.performance_score = min(100, self.performance_score + 0.5)
            for skill in self.skills:
                skill["experience"] += 0.1
        else:
            self.performance_score = max(60, self.performance_score - 0.3)


def create_politics_question_employee(employee_id: str = None,
                                       name: str = "政治题库AI",
                                       level: int = 5) -> PoliticsQuestionEmployee:
    """创建政治题库AI员工"""
    if not employee_id:
        employee_id = f"pol_{uuid.uuid4().hex[:8]}"
    return PoliticsQuestionEmployee(employee_id, name, level)
