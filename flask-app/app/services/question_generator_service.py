# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
考题生成服务模块
负责考题生成, 集成本地AI自动填充拓展功能
"""

import logging
logger = logging.getLogger(__name__)
import os
import sys
import sqlite3
from contextlib import contextmanager
import random
import re
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class QuestionGeneratorService:
    """考题生成服务类"""

    def __init__(self, db_path="app.db"):
        """初始化考题生成服务"""
        self.db_path = db_path
        self.conn = None
        self.cursor = None

        self.auto_fill_config = {
            "enabled": True,
            "fields": ["question", "options", "answer", "explanation"],
            "context_aware": True,
            "learning_rate": 0.1
        }

        self.question_templates = {
            "multiple_choice": {
                "templates": [
                    "以下关于{topic}的说法, 正确的是",
                    "{topic}的主要特点是",
                    "在{topic}中, {concept}指的是",
                    "关于{topic}, 下列哪项描述最准确?"
                ],
                "options_count": 4
            },
            "fill_blank": {
                "templates": [
                    "在{topic}中, {concept}_________.",
                    "_________是{topic}的重要组成部分."
                ]
            },
            "short_answer": {
                "templates": [
                    "解释{topic}中{concept}的含义.",
                    "{topic}在实际应用中有哪些作用?"
                ]
            },
            "essay": {
                "templates": [
                    "论述{topic}的重要意义.",
                    "分析{topic}在实践中的应用."
                ]
            }
        }

        self.knowledge_base = {
            "数学": {
                "小学数学": {
                    "concepts": ["整数运算", "分数运算", "小数运算", "百分数", "基础几何", "简单方程", "数据统计"],
                    "difficulty_range": (1, 3),
                    "exam_type": "九年义务教育",
                    "level": "小学-初中"
                },
                "初中数学": {
                    "concepts": ["代数基础", "函数初步", "平面几何", "立体几何", "概率统计", "三角函数基础", "数列"],
                    "difficulty_range": (3, 5),
                    "exam_type": "九年义务教育",
                    "level": "初中"
                },
                "高中数学": {
                    "concepts": ["集合", "函数", "三角函数", "向量", "数列", "不等式", "解析几何", "立体几何", "概率统计", "导数"],
                    "difficulty_range": (4, 7),
                    "exam_type": "高考",
                    "level": "高中"
                },
                "高等数学": {
                    "concepts": ["微积分", "线性代数", "微分方程", "复变函数", "实变函数", "拓扑学", "泛函分析"],
                    "difficulty_range": (6, 10),
                    "level": "本科-研究生"
                }
            },
            "英语": {
                "九年制基础": {
                    "concepts": ["26个字母", "基础词汇", "简单句", "一般现在时", "一般过去时", "基础对话", "日常用语"],
                    "difficulty_range": (1, 2),
                    "exam_type": "九年义务教育",
                    "level": "小学"
                },
                "九年制进阶": {
                    "concepts": ["时态综合", "从句基础", "被动语态", "词汇扩展", "阅读理解", "书面表达", "听力训练"],
                    "difficulty_range": (2, 4),
                    "exam_type": "九年义务教育",
                    "level": "初中"
                },
                "CET-4": {
                    "concepts": ["词汇(4500)", "语法综合", "快速阅读", "听力理解", "翻译", "写作", "选词填空"],
                    "difficulty_range": (3, 5),
                    "exam_type": "CET",
                    "level": "CET-4"
                },
                "CET-6": {
                    "concepts": ["词汇(5500)", "高级语法", "深度阅读", "学术听力", "汉译英", "议论文写作", "长篇阅读"],
                    "difficulty_range": (4, 6),
                    "level": "CET-6"
                },
                "TEM-4": {
                    "concepts": ["词汇(8000)", "高级语法", "翻译技巧", "写作", "听力"],
                    "difficulty_range": (5, 7),
                    "exam_type": "TEM",
                    "level": "TEM-4"
                },
                "TEM-8": {
                    "concepts": ["词汇(13000)", "高级语言学", "文学分析", "同声传译", "翻译理论", "研究论文", "英美文化"],
                    "difficulty_range": (7, 10),
                    "exam_type": "TEM",
                    "level": "TEM-8"
                }
            },
            "日语": {
                "N5": {
                    "concepts": ["平假名", "片假名", "基础汉字(100字)", "数字", "时间", "问候语", "自我介绍", "简单句型"],
                    "difficulty_range": (1, 2),
                    "exam_type": "JLPT",
                    "level": "N5"
                },
                "N4": {
                    "concepts": ["基础语法", "动词变形(基本形)", "形容词", "助词基础", "日常会话", "基础汉字(300字)", "简单阅读"],
                    "difficulty_range": (2, 3),
                    "exam_type": "JLPT",
                    "level": "N4"
                },
                "N3": {
                    "concepts": ["中级语法", "阅读理解", "听力", "汉字(600字)"],
                    "difficulty_range": (3, 5),
                    "exam_type": "JLPT",
                    "level": "N3"
                },
                "N2": {
                    "concepts": ["高级语法", "复杂阅读", "商务日语"],
                    "difficulty_range": (5, 7),
                    "exam_type": "JLPT",
                    "level": "N2"
                },
                "N1": {
                    "concepts": ["最高级语法", "文学阅读", "专业日语"],
                    "difficulty_range": (7, 10),
                    "exam_type": "JLPT",
                    "level": "N1"
                }
            },
            "物理": {
                "初中物理": {
                    "concepts": ["声现象", "光现象", "热现象", "简单机械", "力与运动", "压强", "浮力", "功和能"],
                    "difficulty_range": (2, 4),
                    "exam_type": "九年义务教育",
                    "level": "初中"
                },
                "高中物理": {
                    "concepts": ["力学", "运动学", "牛顿定律", "能量", "动量", "电场", "磁场", "电磁感应", "光学", "原子物理"],
                    "difficulty_range": (4, 7),
                    "exam_type": "高考",
                    "level": "高中"
                },
                "大学物理": {
                    "concepts": ["理论力学", "热力学", "电磁学", "光学", "近代物理", "量子力学", "统计物理"],
                    "difficulty_range": (6, 10),
                    "exam_type": "大学",
                    "level": "本科-研究生"
                }
            },
            "化学": {
                "初中化学": {
                    "concepts": ["物质的构成", "元素", "化学式", "化学反应", "空气", "水", "溶液", "酸碱盐"],
                    "difficulty_range": (2, 4),
                    "level": "初中"
                },
                "高中化学": {
                    "concepts": ["物质的量", "氧化还原", "离子反应", "元素周期律", "化学键", "化学反应速率", "化学平衡", "电化学", "有机化学基础"],
                    "difficulty_range": (4, 7),
                    "level": "高中"
                },
                "大学化学": {
                    "concepts": ["无机化学", "有机化学", "分析化学", "物理化学", "结构化学", "生物化学", "高分子化学"],
                    "difficulty_range": (6, 10),
                    "level": "本科-研究生"
                }
            },
            "生物": {
                "初中生物": {
                    "concepts": ["生物的生殖", "遗传", "变异", "进化", "生态系统", "生物技术", "环境保护"],
                    "difficulty_range": (2, 4),
                    "level": "初中"
                },
                "高中生物": {
                    "concepts": ["分子与细胞", "遗传与进化", "稳态与环境", "生物技术实践", "生物科学与社会", "现代生物科技"],
                    "difficulty_range": (4, 7),
                    "level": "高中"
                },
                "大学生物": {
                    "concepts": ["分子生物学", "细胞生物学", "遗传学", "生态学"],
                    "difficulty_range": (6, 10),
                    "level": "本科-研究生"
                }
            },
            "历史": {
                "初中历史": {
                    "concepts": ["中国古代史", "中国近代史", "世界古代史", "世界近代史", "重要事件", "历史人物", "文化传统"],
                    "difficulty_range": (2, 4),
                    "level": "初中"
                },
                "高中历史": {
                    "concepts": ["政治文明", "经济文明", "思想文化", "历史人物评说", "历史重大改革", "战争与和平"],
                    "difficulty_range": (4, 7),
                    "exam_type": "高考",
                    "level": "高中"
                },
                "大学历史": {
                    "concepts": ["史学理论", "中国通史", "世界通史", "史学方法"],
                    "difficulty_range": (6, 10),
                    "exam_type": "大学",
                    "level": "本科-研究生"
                }
            },
            "地理": {
                "初中地理": {
                    "concepts": ["地球与地图", "世界地理", "中国地理", "乡土地理", "人口与聚落", "气候与天气", "自然资源"],
                    "difficulty_range": (2, 4),
                    "level": "初中"
                },
                "高中地理": {
                    "concepts": ["自然地理", "人文地理", "区域地理", "地理信息技术"],
                    "difficulty_range": (4, 7),
                    "exam_type": "高考",
                    "level": "高中"
                },
                "大学地理": {
                    "concepts": ["自然地理学", "人文地理学", "地理信息系统", "遥感技术", "环境地理", "经济地理"],
                    "difficulty_range": (6, 10),
                    "level": "本科-研究生"
                }
            },
            "信息技术": {
                "初中信息技术": {
                    "concepts": ["计算机基础", "操作系统", "办公软件", "网络基础", "信息安全", "信息伦理", "编程入门"],
                    "difficulty_range": (2, 4),
                    "exam_type": "九年义务教育",
                    "level": "初中"
                },
                "高中信息技术": {
                    "concepts": ["算法思维", "程序设计", "数据处理", "多媒体技术", "网络应用", "人工智能初步"],
                    "difficulty_range": (4, 7),
                    "exam_type": "高考",
                    "level": "高中"
                },
                "大学计算机": {
                    "concepts": ["数据结构", "算法设计", "操作系统", "计算机网络", "数据库", "软件工程"],
                    "difficulty_range": (6, 10),
                    "exam_type": "大学",
                    "level": "本科-研究生"
                }
            }
        }

        self.difficulty_descriptions = {
            1: "入门级 - 基础概念",
            2: "初级 - 简单应用",
            3: "初中级 - 基本理解",
            4: "中级 - 综合应用",
            5: "中高级 - 分析推理",
            6: "高级 - 深入分析",
            7: "专业级 - 综合运用",
            8: "专家级 - 创新应用",
            9: "研究级 - 前沿问题",
            10: "大师级 - 学术前沿"
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

    def generate_question(self, question_type="multiple_choice", difficulty_level=5, subject=None, topic=None, context=None):
        """生成考题 - 支持难度1-10级"""
        if not self.connect():
            return None

        try:
            difficulty_level = max(1, min(10, difficulty_level))

            if not subject:
                subject = random.choice(list(self.knowledge_base.keys()))

            if not topic:
                if subject in self.knowledge_base:
                    suitable_topics = []
                    for t, data in self.knowledge_base[subject].items():
                        if isinstance(data, dict):
                            min_diff, max_diff = data.get('difficulty_range', (1, 10))
                            if min_diff <= difficulty_level <= max_diff:
                                suitable_topics.append(t)
                    if suitable_topics:
                        topic = random.choice(suitable_topics)
                    else:
                        topic = random.choice(list(self.knowledge_base[subject].keys()))
                else:
                    topic = "基础知识"

            topic_difficulty_range = (1, 10)
            concept = "基础概念"
            if subject in self.knowledge_base and topic in self.knowledge_base[subject]:
                topic_data = self.knowledge_base[subject][topic]
                if isinstance(topic_data, dict):
                    topic_difficulty_range = topic_data.get('difficulty_range', (1, 10))
                    concepts = topic_data.get('concepts', ["基础概念"])
                    concept = random.choice(concepts)

            difficulty_description = self.difficulty_descriptions.get(difficulty_level, "中级")

            if question_type in self.question_templates:
                template = random.choice(self.question_templates[question_type]["templates"])
                question_text = template.format(topic=topic, concept=concept)
            else:
                question_text = f"关于{topic}的问题"

            if difficulty_level >= 8:
                question_text = f"[高难度]{question_text}(要求深入理解和创新应用)"
            elif difficulty_level >= 6:
                question_text = f"[中高级]{question_text}(需要综合分析和推理)"
            elif difficulty_level <= 2:
                question_text = f"[基础]{question_text}"

            options = []
            answer = ""
            explanation = ""

            if question_type == "multiple_choice":
                options = self._generate_options(question_text, topic, concept, difficulty_level)
                answer = random.choice(["A", "B", "C", "D"]) if options else ""

                if difficulty_level >= 7:
                    explanation = f"正确答案是{answer}. {concept}是{topic}中的重要概念. 本题难度等级: {difficulty_level}/10."
                else:
                    explanation = f"正确答案是{answer}. {concept}是{topic}的基础概念. 本题难度等级: {difficulty_level}/10."

            elif question_type == "fill_blank":
                answer = concept
                explanation = f"填空处应填写'{answer}'. 难度等级: {difficulty_level}/10."

            elif question_type == "short_answer":
                if difficulty_level >= 7:
                    answer = f"{topic}的核心要点包括: 1. 深入理解概念本质; 2. 掌握高级应用场景; 3. 能够进行创新思考; 4. 具备解决复杂问题的能力."
                elif difficulty_level >= 4:
                    answer = f"{topic}的主要特点包括: 1. 核心概念理解; 2. 典型应用场景; 3. 与其他知识的联系."
                else:
                    answer = f"{topic}的主要特点包括: 1. 基础概念; 2. 简单应用; 3. 基本特征."
                explanation = f"简答题参考答案. 难度等级: {difficulty_level}/10."

            elif question_type == "essay":
                if difficulty_level >= 8:
                    answer = f"请从理论深度、实践应用、创新思考三个维度全面论述{topic}..."
                elif difficulty_level >= 5:
                    answer = f"请结合理论和实例详细论述{topic}..."
                else:
                    answer = f"请简要论述{topic}..."
                explanation = f"这是一个论述题, 难度等级: {difficulty_level}/10. {difficulty_description}."

            question_data = {
                "question_type": question_type,
                "difficulty_level": difficulty_level,
                "difficulty_description": difficulty_description,
                "subject": subject,
                "topic": topic,
                "concept": concept,
                "question": question_text,
                "options": options,
                "answer": answer,
                "explanation": explanation,
                "context": context,
                "topic_difficulty_range": topic_difficulty_range
            }

            self._save_generation_history(1, question_type, difficulty_level, subject, question_data)

            return question_data

        except Exception as e:
            logger.error(f"生成考题失败: {str(e)}")
            return None
        finally:
            self.close()

    def _generate_options(self, question_text, topic, concept, difficulty_level):
        """生成选择题选项"""
        options = []

        correct_answer = f"{concept}的正确描述"
        options.append(correct_answer)

        distractors = [
            f"错误的{concept}描述1",
            f"错误的{concept}描述2",
            f"错误的{concept}描述3"
        ]
        options.extend(distractors)

        random.shuffle(options)

        return options

    def _save_generation_history(self, user_id, question_type, difficulty_level, subject, generated_content):
        """保存生成历史"""
        if not self.connect():
            return False

        try:
            self.cursor.execute('''
                INSERT INTO question_generation_history 
                (user_id, question_type, difficulty_level, subject, generated_content, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (user_id, question_type, difficulty_level, subject, str(generated_content), datetime.now().isoformat()))
            self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"保存生成历史失败: {str(e)}")
            return False
        finally:
            self.close()

    def save_auto_fill_data(self, user_id, field_name, field_value, context=None, question_type=None, subject=None):
        """保存自动填充数据"""
        if not self.connect():
            return False

        try:
            self.cursor.execute('''
                INSERT INTO auto_fill_data 
                (user_id, field_name, field_value, context, question_type, subject, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, field_name, field_value, context, question_type, subject, datetime.now().isoformat()))
            self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"保存自动填充数据失败: {str(e)}")
            return False
        finally:
            self.close()

    def get_auto_fill_suggestions(self, user_id, field_name, context=None, question_type=None, subject=None):
        """获取自动填充建议"""
        if not self.connect():
            return []

        try:
            query = "SELECT field_value FROM auto_fill_data WHERE user_id = ? AND field_name = ?"
            params = [user_id, field_name]

            if question_type:
                query += " AND question_type = ?"
                params.append(question_type)
            if subject:
                query += " AND subject = ?"
                params.append(subject)

            query += " ORDER BY created_at DESC LIMIT 10"

            self.cursor.execute(query, params)
            results = self.cursor.fetchall()
            return [r[0] for r in results]
        except Exception as e:
            logger.error(f"获取自动填充建议失败: {str(e)}")
            return []
        finally:
            self.close()

    def get_generation_history(self, user_id, question_type=None, subject=None, limit=50, offset=0):
        """获取生成历史"""
        if not self.connect():
            return []

        try:
            query = "SELECT * FROM question_generation_history WHERE user_id = ?"
            params = [user_id]

            if question_type:
                query += " AND question_type = ?"
                params.append(question_type)
            if subject:
                query += " AND subject = ?"
                params.append(subject)

            query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])

            self.cursor.execute(query, params)
            results = self.cursor.fetchall()
            return results
        except Exception as e:
            logger.error(f"获取生成历史失败: {str(e)}")
            return []
        finally:
            self.close()

    def get_question_quality(self, question_id):
        """获取题目质量评估"""
        if not self.connect():
            return None

        try:
            self.cursor.execute('''
                SELECT quality_score, feedback FROM question_quality 
                WHERE question_id = ?
            ''', (question_id,))
            result = self.cursor.fetchone()
            if result:
                return {'quality_score': result[0], 'feedback': result[1]}
            return None
        except Exception as e:
            logger.error(f"获取题目质量评估失败: {str(e)}")
            return None
        finally:
            self.close()


question_generator_service = QuestionGeneratorService()


def get_question_generator_service():
    """获取考题生成服务实例"""
    return question_generator_service
