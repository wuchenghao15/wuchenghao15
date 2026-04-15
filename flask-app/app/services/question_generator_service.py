#!/usr/bin/env python3
"""
考题生成服务模块
负责考题生成，集成本地AI自动填充拓展功能
"""

import os
import sys
import sqlite3
import json
import random
import re
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class QuestionGeneratorService:
    """考题生成服务类"""
    
    def __init__(self, db_path="app.db"):
        """初始化考题生成服务"""
        self.db_path = db_path
        self.conn = None
        self.cursor = None
        
        # 自动填充配置
        self.auto_fill_config = {
            "enabled": True,
            "fields": ["question", "options", "answer", "explanation"],
            "context_aware": True,
            "learning_rate": 0.1
        }
        
        # 题目类型模板
        self.question_templates = {
            "multiple_choice": {
                "templates": [
                    "以下关于{topic}的说法，正确的是：",
                    "{topic}的主要特点是：",
                    "在{topic}中，{concept}指的是：",
                    "关于{topic}，下列哪项描述最准确？"
                ],
                "options_count": 4
            },
            "fill_blank": {
                "templates": [
                    "{topic}是_________。",
                    "在{topic}中，{concept}_________。",
                    "_________是{topic}的重要组成部分。"
                ]
            },
            "short_answer": {
                "templates": [
                    "请简述{topic}的主要特点。",
                    "解释{topic}中{concept}的含义。",
                    "{topic}在实际应用中有哪些作用？"
                ]
            },
            "essay": {
                "templates": [
                    "请详细论述{topic}的发展历程及其影响。",
                    "结合实例，分析{topic}在实际中的应用。",
                    "比较{topic}与{comparison_topic}的异同点。"
                ]
            }
        }
        
        # 完整知识库 - 覆盖全学科，难度1-10级
        self.knowledge_base = {
            # 数学 - 九年制 + 高等教育
            "数学": {
                "九年制基础": {
                    "concepts": ["整数运算", "分数运算", "小数运算", "百分数", "基础几何", "简单方程", "数据统计"],
                    "difficulty_range": (1, 3),
                    "exam_type": "九年义务教育",
                    "level": "小学-初中"
                },
                "九年制进阶": {
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
                    "exam_type": "大学",
                    "level": "本科-研究生"
                }
            },
            # 英语 - 九年制、四级、六级、专四、专八
            "英语": {
                "九年制基础": {
                    "concepts": ["26个字母", "基础词汇", "简单句", "一般现在时", "一般过去时", "基础对话", "日常用语"],
                    "difficulty_range": (1, 2),
                    "exam_type": "九年义务教育",
                    "level": "小学-初中"
                },
                "九年制进阶": {
                    "concepts": ["时态综合", "从句基础", "被动语态", "词汇扩展", "阅读理解", "书面表达", "听力训练"],
                    "difficulty_range": (2, 4),
                    "exam_type": "九年义务教育",
                    "level": "初中"
                },
                "四级": {
                    "concepts": ["词汇(4500)", "语法综合", "快速阅读", "听力理解", "翻译", "写作", "选词填空"],
                    "difficulty_range": (3, 5),
                    "exam_type": "CET",
                    "level": "CET-4"
                },
                "六级": {
                    "concepts": ["词汇(5500)", "高级语法", "深度阅读", "学术听力", "汉译英", "议论文写作", "长篇阅读"],
                    "difficulty_range": (4, 6),
                    "exam_type": "CET",
                    "level": "CET-6"
                },
                "专四": {
                    "concepts": ["词汇(8000)", "专业语法", "文学阅读", "专业听力", "翻译技巧", "学术写作", "语言学基础"],
                    "difficulty_range": (5, 7),
                    "exam_type": "TEM",
                    "level": "TEM-4"
                },
                "专八": {
                    "concepts": ["词汇(13000)", "高级语言学", "文学分析", "同声传译", "翻译理论", "研究论文", "英美文化"],
                    "difficulty_range": (7, 10),
                    "exam_type": "TEM",
                    "level": "TEM-8"
                }
            },
            # 日语 - JLPT N5-N1等级
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
                    "concepts": ["中级语法", "动词变形(全部)", "敬语基础", "助词进阶", "中篇文章", "汉字(600字)", "听力理解"],
                    "difficulty_range": (3, 5),
                    "exam_type": "JLPT",
                    "level": "N3"
                },
                "N2": {
                    "concepts": ["高级语法", "商务日语", "惯用语", "新闻阅读", "学术听力", "汉字(1000字)", "文化理解"],
                    "difficulty_range": (5, 7),
                    "exam_type": "JLPT",
                    "level": "N2"
                },
                "N1": {
                    "concepts": ["专业语法", "古典日语", "高级商务", "学术论文", "文学作品分析", "汉字(2000字)", "深层文化"],
                    "difficulty_range": (7, 10),
                    "exam_type": "JLPT",
                    "level": "N1"
                }
            },
            # 物理 - 九年制 + 高等教育
            "物理": {
                "九年制基础": {
                    "concepts": ["声现象", "光现象", "热现象", "简单机械", "力与运动", "压强", "浮力", "功和能"],
                    "difficulty_range": (2, 4),
                    "exam_type": "九年义务教育",
                    "level": "初中"
                },
                "九年制进阶": {
                    "concepts": ["电学基础", "欧姆定律", "电功率", "磁现象", "电磁感应", "电路分析", "能量转化"],
                    "difficulty_range": (3, 5),
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
            # 化学 - 九年制 + 高等教育
            "化学": {
                "九年制基础": {
                    "concepts": ["物质的构成", "元素", "化学式", "化学反应", "空气", "水", "溶液", "酸碱盐"],
                    "difficulty_range": (2, 4),
                    "exam_type": "九年义务教育",
                    "level": "初中"
                },
                "九年制进阶": {
                    "concepts": ["金属", "非金属", "有机物", "化学实验", "化学计算", "化学与生活", "环境保护"],
                    "difficulty_range": (3, 5),
                    "exam_type": "九年义务教育",
                    "level": "初中"
                },
                "高中化学": {
                    "concepts": ["物质的量", "氧化还原", "离子反应", "元素周期律", "化学键", "化学反应速率", "化学平衡", "电化学", "有机化学基础"],
                    "difficulty_range": (4, 7),
                    "exam_type": "高考",
                    "level": "高中"
                },
                "大学化学": {
                    "concepts": ["无机化学", "有机化学", "分析化学", "物理化学", "结构化学", "生物化学", "高分子化学"],
                    "difficulty_range": (6, 10),
                    "exam_type": "大学",
                    "level": "本科-研究生"
                }
            },
            # 生物 - 九年制 + 高等教育
            "生物": {
                "九年制基础": {
                    "concepts": ["生物的特征", "细胞", "生物圈", "植物", "动物", "人体生理", "健康"],
                    "difficulty_range": (2, 4),
                    "exam_type": "九年义务教育",
                    "level": "初中"
                },
                "九年制进阶": {
                    "concepts": ["生物的生殖", "遗传", "变异", "进化", "生态系统", "生物技术", "环境保护"],
                    "difficulty_range": (3, 5),
                    "exam_type": "九年义务教育",
                    "level": "初中"
                },
                "高中生物": {
                    "concepts": ["分子与细胞", "遗传与进化", "稳态与环境", "生物技术实践", "生物科学与社会", "现代生物科技"],
                    "difficulty_range": (4, 7),
                    "exam_type": "高考",
                    "level": "高中"
                },
                "大学生物": {
                    "concepts": ["细胞生物学", "遗传学", "生物化学", "分子生物学", "生态学", "生理学", "进化生物学"],
                    "difficulty_range": (6, 10),
                    "exam_type": "大学",
                    "level": "本科-研究生"
                }
            },
            # 历史 - 九年制 + 高等教育
            "历史": {
                "九年制基础": {
                    "concepts": ["中国古代史", "中国近代史", "世界古代史", "世界近代史", "重要事件", "历史人物", "文化传统"],
                    "difficulty_range": (2, 4),
                    "exam_type": "九年义务教育",
                    "level": "初中"
                },
                "九年制进阶": {
                    "concepts": ["历史发展脉络", "重大历史变革", "文明交流", "历史思维", "史料分析", "历史评价"],
                    "difficulty_range": (3, 5),
                    "exam_type": "九年义务教育",
                    "level": "初中"
                },
                "高中历史": {
                    "concepts": ["政治文明", "经济文明", "思想文化", "历史人物评说", "历史重大改革", "战争与和平"],
                    "difficulty_range": (4, 7),
                    "exam_type": "高考",
                    "level": "高中"
                },
                "大学历史": {
                    "concepts": ["史学理论", "历史研究方法", "专门史", "区域史", "全球史", "历史哲学"],
                    "difficulty_range": (6, 10),
                    "exam_type": "大学",
                    "level": "本科-研究生"
                }
            },
            # 地理 - 九年制 + 高等教育
            "地理": {
                "九年制基础": {
                    "concepts": ["地球与地图", "世界地理", "中国地理", "乡土地理", "人口与聚落", "气候与天气", "自然资源"],
                    "difficulty_range": (2, 4),
                    "exam_type": "九年义务教育",
                    "level": "初中"
                },
                "九年制进阶": {
                    "concepts": ["区域地理", "人文地理", "经济地理", "环境地理", "地理信息技术", "可持续发展"],
                    "difficulty_range": (3, 5),
                    "exam_type": "九年义务教育",
                    "level": "初中"
                },
                "高中地理": {
                    "concepts": ["自然地理", "人文地理", "区域发展", "地理信息技术", "环境保护", "城乡规划"],
                    "difficulty_range": (4, 7),
                    "exam_type": "高考",
                    "level": "高中"
                },
                "大学地理": {
                    "concepts": ["自然地理学", "人文地理学", "地理信息系统", "遥感技术", "环境地理", "经济地理"],
                    "difficulty_range": (6, 10),
                    "exam_type": "大学",
                    "level": "本科-研究生"
                }
            },
            # 计算机 - 九年制 + 高等教育
            "计算机": {
                "九年制基础": {
                    "concepts": ["计算机基础", "操作系统", "办公软件", "网络基础", "信息安全", "信息伦理", "编程入门"],
                    "difficulty_range": (2, 4),
                    "exam_type": "九年义务教育",
                    "level": "初中"
                },
                "九年制进阶": {
                    "concepts": ["算法思维", "程序设计", "数据处理", "多媒体技术", "网络应用", "人工智能初步"],
                    "difficulty_range": (3, 5),
                    "exam_type": "九年义务教育",
                    "level": "初中"
                },
                "高中信息技术": {
                    "concepts": ["数据与计算", "信息系统", "数据结构与算法", "人工智能", "网络技术", "信息系统安全"],
                    "difficulty_range": (4, 7),
                    "exam_type": "高考",
                    "level": "高中"
                },
                "大学计算机": {
                    "concepts": ["程序设计", "数据结构", "算法", "操作系统", "计算机网络", "数据库", "软件工程"],
                    "difficulty_range": (6, 10),
                    "exam_type": "大学",
                    "level": "本科-研究生"
                }
            }
        }
        
        # 难度级别描述
        self.difficulty_descriptions = {
            1: "入门级 - 基础概念理解",
            2: "初级 - 简单应用",
            3: "初中级 - 基础运算",
            4: "中级 - 综合应用",
            5: "中高级 - 分析推理",
            6: "高级 - 复杂问题",
            7: "专业级 - 深入理解",
            8: "专家级 - 创新应用",
            9: "研究级 - 前沿问题",
            10: "大师级 - 原创性工作"
        }
    
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
    
    def generate_question(self, question_type, difficulty_level, subject=None, topic=None, context=None):
        """生成考题 - 支持难度1-10级"""
        if not self.connect():
            return None
        
        try:
            # 验证难度级别
            difficulty_level = max(1, min(10, difficulty_level))
            
            # 如果没有指定主题，从知识库中随机选择
            if not subject:
                subject = random.choice(list(self.knowledge_base.keys()))
            
            # 根据难度级别选择合适的topic
            if not topic:
                if subject in self.knowledge_base:
                    # 筛选符合难度范围的topic
                    suitable_topics = []
                    for t, data in self.knowledge_base[subject].items():
                        if isinstance(data, dict) and "difficulty_range" in data:
                            min_diff, max_diff = data["difficulty_range"]
                            if min_diff <= difficulty_level <= max_diff:
                                suitable_topics.append(t)
                    
                    if suitable_topics:
                        topic = random.choice(suitable_topics)
                    else:
                        # 如果没有完全匹配的，选择最接近的
                        topic = random.choice(list(self.knowledge_base[subject].keys()))
                else:
                    topic = "基础知识"
            
            # 获取概念和难度信息
            concept = ""
            topic_difficulty_range = (1, 10)
            if subject in self.knowledge_base and topic in self.knowledge_base[subject]:
                topic_data = self.knowledge_base[subject][topic]
                if isinstance(topic_data, dict):
                    concept = random.choice(topic_data.get("concepts", ["基础概念"]))
                    topic_difficulty_range = topic_data.get("difficulty_range", (1, 10))
                else:
                    concept = random.choice(topic_data) if isinstance(topic_data, list) else "基础概念"
            
            # 根据难度调整题目复杂度
            difficulty_description = self.difficulty_descriptions.get(difficulty_level, "中级")
            
            # 选择模板
            if question_type in self.question_templates:
                template = random.choice(self.question_templates[question_type]["templates"])
                question_text = template.format(
                    topic=topic,
                    concept=concept,
                    comparison_topic=random.choice(list(self.knowledge_base.get(subject, {}).keys())) if subject else topic
                )
            else:
                question_text = f"关于{topic}的问题"
            
            # 根据难度调整题目描述
            if difficulty_level >= 8:
                question_text = f"【高难度】{question_text}（要求深入理解和创新应用）"
            elif difficulty_level >= 6:
                question_text = f"【中高级】{question_text}（需要综合分析和推理）"
            elif difficulty_level <= 2:
                question_text = f"【入门级】{question_text}（基础概念理解）"
            
            # 生成选项（如果是选择题）
            options = []
            answer = ""
            explanation = ""
            
            if question_type == "multiple_choice":
                options = self._generate_options(question_text, topic, concept, difficulty_level)
                answer = random.choice(["A", "B", "C", "D"]) if options else ""
                
                # 根据难度调整解析详细程度
                if difficulty_level >= 7:
                    explanation = f"正确答案是{answer}。{concept}是{topic}中的高级概念，需要深入理解其原理和应用。本题难度等级：{difficulty_level}/10。"
                elif difficulty_level >= 4:
                    explanation = f"正确答案是{answer}。{concept}是{topic}中的重要概念。本题难度等级：{difficulty_level}/10。"
                else:
                    explanation = f"正确答案是{answer}。{concept}是{topic}的基础概念。本题难度等级：{difficulty_level}/10。"
                    
            elif question_type == "fill_blank":
                answer = concept if concept else "答案"
                explanation = f"填空处应填写'{answer}'。难度等级：{difficulty_level}/10。"
                
            elif question_type == "short_answer":
                if difficulty_level >= 7:
                    answer = f"{topic}的核心要点包括：1. 深入理解概念本质；2. 掌握高级应用场景；3. 能够进行创新思考；4. 具备解决复杂问题的能力。"
                elif difficulty_level >= 4:
                    answer = f"{topic}的主要特点包括：1. 核心概念理解；2. 典型应用场景；3. 与其他知识的联系。"
                else:
                    answer = f"{topic}的主要特点包括：1. 基础概念；2. 简单应用；3. 基本特征。"
                explanation = f"这是一个简答题，难度等级：{difficulty_level}/10。{difficulty_description}。"
                
            elif question_type == "essay":
                if difficulty_level >= 8:
                    answer = f"请从理论深度、实践应用、创新思考三个维度全面论述{topic}..."
                elif difficulty_level >= 5:
                    answer = f"请结合理论和实例详细论述{topic}..."
                else:
                    answer = f"请简要论述{topic}..."
                explanation = f"这是一个论述题，难度等级：{difficulty_level}/10。{difficulty_description}。"
            
            # 构建题目数据
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
            
            # 保存生成历史
            self._save_generation_history(1, question_type, difficulty_level, subject, question_data)
            
            return question_data
        except Exception as e:
            print(f"生成考题失败: {str(e)}")
            return None
        finally:
            self.close()
    
    def _generate_options(self, question_text, topic, concept, difficulty_level):
        """生成选择题选项"""
        options = []
        
        # 生成正确答案
        correct_answer = f"{concept}的正确描述"
        options.append(correct_answer)
        
        # 生成干扰项
        distractors = [
            f"错误的{concept}描述1",
            f"错误的{concept}描述2",
            f"错误的{concept}描述3"
        ]
        options.extend(distractors)
        
        # 打乱选项顺序
        random.shuffle(options)
        
        return options
    
    def _save_generation_history(self, user_id, question_type, difficulty_level, subject, generated_content):
        """保存生成历史"""
        if not self.connect():
            return False
        
        try:
            sql = """
            INSERT INTO question_generation_history 
            (user_id, question_type, difficulty_level, subject, generated_content)
            VALUES (?, ?, ?, ?, ?)
            """
            self.cursor.execute(sql, (
                user_id,
                question_type,
                difficulty_level,
                subject,
                json.dumps(generated_content, ensure_ascii=False)
            ))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"保存生成历史失败: {str(e)}")
            return False
        finally:
            self.close()
    
    def save_auto_fill_data(self, user_id, field_name, field_value, context=None, question_type=None, subject=None):
        """保存自动填充数据"""
        if not self.connect():
            return False
        
        try:
            # 检查是否已存在
            sql = """
            SELECT id, usage_count FROM question_auto_fill
            WHERE user_id = ? AND field_name = ? AND field_value = ? AND question_type = ? AND subject = ?
            """
            self.cursor.execute(sql, (user_id, field_name, field_value, question_type, subject))
            existing = self.cursor.fetchone()
            
            if existing:
                # 更新使用次数
                sql = """
                UPDATE question_auto_fill
                SET usage_count = usage_count + 1, last_used = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """
                self.cursor.execute(sql, (existing[0],))
            else:
                # 插入新数据
                sql = """
                INSERT INTO question_auto_fill 
                (user_id, field_name, field_value, context, question_type, subject, usage_count, last_used)
                VALUES (?, ?, ?, ?, ?, ?, 1, CURRENT_TIMESTAMP)
                """
                self.cursor.execute(sql, (
                    user_id, field_name, field_value, 
                    json.dumps(context) if context else None,
                    question_type, subject
                ))
            
            self.conn.commit()
            return True
        except Exception as e:
            print(f"保存自动填充数据失败: {str(e)}")
            return False
        finally:
            self.close()
    
    def get_auto_fill_suggestions(self, user_id, field_name, context=None, question_type=None, subject=None):
        """获取自动填充建议"""
        if not self.connect():
            return []
        
        try:
            # 构建查询条件
            conditions = ["user_id = ?", "field_name = ?"]
            params = [user_id, field_name]
            
            if question_type:
                conditions.append("question_type = ?")
                params.append(question_type)
            
            if subject:
                conditions.append("subject = ?")
                params.append(subject)
            
            where_clause = " AND ".join(conditions)
            sql = f"""
            SELECT field_value, usage_count, context, question_type, subject
            FROM question_auto_fill
            WHERE {where_clause}
            ORDER BY usage_count DESC, last_used DESC
            LIMIT 5
            """
            
            self.cursor.execute(sql, params)
            
            suggestions = []
            for row in self.cursor.fetchall():
                # 计算匹配度
                score = row[1]  # 基础分数基于使用次数
                
                # 如果提供了上下文，计算上下文匹配度
                if context and row[2]:
                    try:
                        stored_context = json.loads(row[2])
                        if isinstance(stored_context, dict) and isinstance(context, dict):
                            common_keys = set(stored_context.keys()) & set(context.keys())
                            if common_keys:
                                match_count = sum(1 for key in common_keys if stored_context.get(key) == context.get(key))
                                score += match_count * 2
                    except:
                        pass
                
                suggestions.append({
                    "value": row[0],
                    "score": score,
                    "context": json.loads(row[2]) if row[2] else None,
                    "question_type": row[3],
                    "subject": row[4]
                })
            
            # 按分数排序
            suggestions.sort(key=lambda x: x["score"], reverse=True)
            
            return suggestions
        except Exception as e:
            print(f"获取自动填充建议失败: {str(e)}")
            return []
        finally:
            self.close()
    
    def get_generation_history(self, user_id, question_type=None, subject=None, limit=50, offset=0):
        """获取生成历史"""
        if not self.connect():
            return []
        
        try:
            # 构建查询条件
            conditions = ["user_id = ?"]
            params = [user_id]
            
            if question_type:
                conditions.append("question_type = ?")
                params.append(question_type)
            
            if subject:
                conditions.append("subject = ?")
                params.append(subject)
            
            where_clause = " AND ".join(conditions)
            sql = f"""
            SELECT id, question_type, difficulty_level, subject, generated_content, 
                   quality_score, user_feedback, created_at
            FROM question_generation_history
            WHERE {where_clause}
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
            """
            
            params.extend([limit, offset])
            self.cursor.execute(sql, params)
            
            history = []
            for row in self.cursor.fetchall():
                item = {
                    "id": row[0],
                    "question_type": row[1],
                    "difficulty_level": row[2],
                    "subject": row[3],
                    "generated_content": json.loads(row[4]) if row[4] else None,
                    "quality_score": row[5],
                    "user_feedback": row[6],
                    "created_at": row[7]
                }
                history.append(item)
            
            return history
        except Exception as e:
            print(f"获取生成历史失败: {str(e)}")
            return []
        finally:
            self.close()
    
    def evaluate_question_quality(self, question_id, clarity_score=None, difficulty_accuracy=None, 
                                  answer_correctness=None, overall_score=None, feedback=None, evaluator=None):
        """评估题目质量"""
        if not self.connect():
            return False
        
        try:
            sql = """
            INSERT INTO question_quality 
            (question_id, clarity_score, difficulty_accuracy, answer_correctness, overall_score, feedback, evaluator)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """
            self.cursor.execute(sql, (
                question_id, clarity_score, difficulty_accuracy, 
                answer_correctness, overall_score, feedback, evaluator
            ))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"评估题目质量失败: {str(e)}")
            return False
        finally:
            self.close()
    
    def get_question_quality(self, question_id):
        """获取题目质量评估"""
        if not self.connect():
            return None
        
        try:
            sql = """
            SELECT clarity_score, difficulty_accuracy, answer_correctness, overall_score, feedback, evaluator, created_at
            FROM question_quality
            WHERE question_id = ?
            ORDER BY created_at DESC
            LIMIT 1
            """
            self.cursor.execute(sql, (question_id,))
            row = self.cursor.fetchone()
            
            if row:
                return {
                    "clarity_score": row[0],
                    "difficulty_accuracy": row[1],
                    "answer_correctness": row[2],
                    "overall_score": row[3],
                    "feedback": row[4],
                    "evaluator": row[5],
                    "created_at": row[6]
                }
            return None
        except Exception as e:
            print(f"获取题目质量评估失败: {str(e)}")
            return None
        finally:
            self.close()

# 全局考题生成服务实例
question_generator_service = None

def get_question_generator_service():
    """获取考题生成服务实例"""
    global question_generator_service
    if question_generator_service is None:
        question_generator_service = QuestionGeneratorService()
    return question_generator_service

if __name__ == "__main__":
    # 测试考题生成服务
    service = QuestionGeneratorService()
    
    # 测试生成选择题
    print("生成选择题...")
    question = service.generate_question("multiple_choice", 3, "数学", "代数")
    print(f"生成的题目: {json.dumps(question, indent=2, ensure_ascii=False)}")
    
    # 测试生成填空题
    print("\n生成填空题...")
    question = service.generate_question("fill_blank", 2, "英语", "语法")
    print(f"生成的题目: {json.dumps(question, indent=2, ensure_ascii=False)}")
    
    # 测试生成简答题
    print("\n生成简答题...")
    question = service.generate_question("short_answer", 4, "日语", "文化")
    print(f"生成的题目: {json.dumps(question, indent=2, ensure_ascii=False)}")
    
    # 测试保存自动填充数据
    print("\n保存自动填充数据...")
    result = service.save_auto_fill_data(
        1, "question", "以下关于代数的说法，正确的是：",
        context={"subject": "数学", "topic": "代数"},
        question_type="multiple_choice",
        subject="数学"
    )
    print(f"保存结果: {result}")
    
    # 测试获取自动填充建议
    print("\n获取自动填充建议...")
    suggestions = service.get_auto_fill_suggestions(
        1, "question",
        context={"subject": "数学", "topic": "代数"},
        question_type="multiple_choice",
        subject="数学"
    )
    print(f"建议: {json.dumps(suggestions, indent=2, ensure_ascii=False)}")
    
    # 测试获取生成历史
    print("\n获取生成历史...")
    history = service.get_generation_history(1)
    print(f"历史记录数: {len(history)}")
    
    # 测试评估题目质量
    print("\n评估题目质量...")
    result = service.evaluate_question_quality(
        1, clarity_score=4.5, difficulty_accuracy=4.0, 
        answer_correctness=5.0, overall_score=4.5,
        feedback="题目清晰，难度适中",
        evaluator="系统自动评估"
    )
    print(f"评估结果: {result}")
