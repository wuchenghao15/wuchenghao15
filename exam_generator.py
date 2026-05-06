#!/usr/bin/env python3
"""
试卷试题生成模块
利用AI和Python技术自动升级并拓展试卷试题生成功能

import os
import sys
# JSON import removed - using database
import random
import logging
import time
import sqlite3
from datetime import datetime
from typing import Dict, List, Any, Tuple, Optional
from collections import defaultdict

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('exam_generator.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('exam_generator')

class ExamGenerator:
    """试卷生成器"""

    def __init__(self, ai_system=None):
        """初始化试卷生成器

        Args:
            ai_system: 多AI学习系统实例
        self.ai_system = ai_system
        self.version = "2.0.0"
        self.creation_time = datetime.now()
        self.last_update_time = datetime.now()

        # 试卷配置
        self.exam_config = {
            "default_duration": 60,  # 默认考试时长（分钟）
            "default_total_score": 100,  # 默认总分
            "question_types": {
                "vocabulary": {
                "weight": 0.15,  # 词汇题权重
                "min_difficulty": 1,
                "max_difficulty": 5
            },
            "grammar": {
                "weight": 0.15,  # 语法题权重
                "min_difficulty": 1,
                "max_difficulty": 5
            "reading": {
                "min_difficulty": 2,
            },
                "listening": {
                "min_difficulty": 1,
                "max_difficulty": 5,
                    "easy": [30, 60],
                    "medium": [60, 120],
                    "hard": [120, 240]
                },
                "speeds": ["slow", "normal", "fast"]
            },
                "writing": {
                    "weight": 0.1,  # 写作题权重
                    "min_difficulty": 2,
                },
                    "weight": 0.1,  # 口语题权重
                    "max_difficulty": 5
                }
            },
                "medium": 0.5,  # 中等题比例
                "hard": 0.2   # 困难题比例
            "languages": {
                "supported": ["zh-CN", "en-US", "ja-JP"],
            },
            # 日语能力等级映射 (JLPT N1-N5)
                "N1": {"difficulty": 5, "description": "高级日语能力"},
                "N3": {"difficulty": 3, "description": "中级日语能力"},
                "N4": {"difficulty": 2, "description": "初级日语能力"},
                "N5": {"difficulty": 1, "description": "入门级日语能力"}
            # 摸底测试配置
            "placement_test": {
                "total_questions": 20,
                "duration": 30,
                "total_score": 100,
                "question_types": {
                    "vocabulary": 0.25,
                    "listening": 0.25
                },
                "level_detection": {
                    "90-100": "N1",
                    "80-89": "N2",
                    "70-79": "N3",
                    "60-69": "N4",
                    "0-59": "N5"
                }
            },
            "enable_personalization": True,
            "enable_feedback_learning": True,
            "question_bank_threshold": 0.7  # 题库使用率阈值，低于此值则自动扩充
        }

        # 支持的题型
        self.supported_question_types = {
            "grammar": ["structure", "usage", "error_correction", "sentence_translation", "completion", "tense", "voice"],
            "reading": ["main_idea", "detail_understanding", "inference", "vocabulary_in_context", "author_intent", "text_structure", "tone"],
            "listening": ["main_idea", "detail_understanding", "inference", "vocabulary_in_context", "speaker_intent", "conversation_flow", "pronunciation", "tone_recognition", "speaker_identification", "content_summarization", "time_sequence", "location_identification"],
            "writing": ["essay", "email", "report", "summary", "description", "argumentation", "narration"],
            "speaking": ["topic_discussion", "picture_description", "role_play", "story_telling", "opinion_expression", "sight_interpretation", "Q&A"]
        }

        # 题库连接信息
        self.db_path = "flask-app/app.db"

        # 自我学习数据
        self.learning_data = {
            "question_performance": defaultdict(dict),  # 题目表现数据
            "difficulty_adjustments": defaultdict(float),  # 难度调整系数
            "topic_coverage": defaultdict(float),  # 知识点覆盖情况
            "feedback_count": 0  # 反馈次数
        }

        logger.info(f"初始化试卷生成器，版本: {self.version}")

    def generate_exam(self, exam_config: Dict[str, Any] = None, user_info: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """生成试卷

        Args:
            exam_config: 试卷配置

        Returns:
            生成的试卷
        logger.info("开始生成试卷")

        # 使用默认配置或传入的配置
        config = exam_config or self.exam_config

        # 生成试卷基本信息
        language = config.get("language", self.exam_config["languages"]["default"])
        difficulty_level = config.get("difficulty_level", "mixed")

        # 计算自适应难度
        if self.exam_config["enable_adaptive_difficulty"] and user_info:
            adaptive_difficulty = self._calculate_adaptive_difficulty(user_info)
            logger.info(f"根据用户信息计算的自适应难度: {adaptive_difficulty}")
            # 将自适应难度应用到配置中
            config["adaptive_difficulty"] = adaptive_difficulty

        exam = {
            "id": f"exam_{int(time.time() * 1000)}",
            "version": self.version,
            "generated_at": datetime.now().isoformat(),
            "title": config.get("title", self._get_exam_title(language)),
            "duration": config.get("duration", self.exam_config["default_duration"]),
            "total_score": config.get("total_score", self.exam_config["default_total_score"]),
            "language": language,
            "difficulty_level": difficulty_level,
            "adaptive_difficulty": config.get("adaptive_difficulty", None),
            "user_profile": user_info.get("profile", {}) if user_info else {},
            "sections": []
        }

        # 生成各部分试题
        total_questions = config.get("total_questions", 30)

        # 根据权重分配各题型数量
        question_distribution = self._calculate_question_distribution(total_questions, config)

        # 生成各题型试题
        for question_type, count in question_distribution.items():
            if count <= 0:
                continue

            logger.info(f"生成{count}道{question_type}题")

            # 生成该类型的试题
            questions = self._generate_section_questions(question_type, count, config, user_info)

            if questions:
                # 计算该部分的分数
                question_types = config.get("question_types", self.exam_config["question_types"])
                section_weight = question_types[question_type]["weight"]
                section_score = int(exam["total_score"] * section_weight)
                score_per_question = section_score / len(questions)

                # 更新每个题目的分数
                for question in questions:
                    question["score"] = score_per_question

                # 添加到试卷中
                section = {
                    "type": question_type,
                    "title": self._get_section_title(question_type),
                    "questions": questions,
                    "total_questions": len(questions),
                    "total_score": section_score,
                    "score_per_question": score_per_question
                }
                exam["sections"].append(section)

        logger.info(f"成功生成试卷，共{sum(len(s['questions']) for s in exam['sections'])}道题")

        # 生成后进行自我学习
        self.self_learn()

        return exam

    def _calculate_question_distribution(self, total_questions: int, config: Dict[str, Any]) -> Dict[str, int]:
        """计算各题型的数量分布

        Args:
            total_questions: 总题数
            config: 试卷配置
        Returns:
            各题型数量分布
        distribution = {}
        remaining_questions = total_questions

        # 使用默认的question_types配置，如果传入的config中没有的话
        question_types = config.get("question_types", self.exam_config["question_types"])

        # 根据权重分配题数
        for question_type, type_config in question_types.items():
            count = int(total_questions * type_config["weight"])
            distribution[question_type] = count
            remaining_questions -= count

        # 处理剩余题数
        if remaining_questions > 0:
            # 将剩余题数分配给权重最大的题型
            max_weight_type = max(question_types.items(), key=lambda x: x[1]["weight"])[0]
            distribution[max_weight_type] += remaining_questions

        return distribution

    def _generate_section_questions(self, question_type: str, count: int, config: Dict[str, Any], user_info: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """生成某一类型的试题

            question_type: 题型
            count: 数量
            config: 试卷配置

        Returns:
            生成的试题列表
        questions = []
        # 1. 首先从题库获取题目
        bank_questions = self._get_questions_from_bank(question_type, count, config)
        questions.extend(bank_questions)

        # 2. 检查题库中获取的题目数量是否足够
        remaining_count = count - len(questions)

        if remaining_count > 0:
            logger.info(f"题库中{question_type}题型的题目不足，需要扩充{remaining_count}道题")

            # 3. 自动扩充题库
            expand_success = self._expand_question_bank(question_type, remaining_count)

            if expand_success:
                # 4. 从扩充后的题库中获取剩余题目
                additional_questions = self._get_questions_from_bank(question_type, remaining_count, config)
                questions.extend(additional_questions)

            # 5. 如果扩充后仍不足，使用AI或示例生成
            still_remaining = count - len(questions)
            if still_remaining > 0:
                logger.info(f"题库扩充后仍不足，使用AI生成剩余{still_remaining}道{question_type}题")
                    # 使用AI系统生成试题
                    generated_content = self.ai_system.generate_content(question_type, still_remaining)

                    for content in generated_content:
                        # 转换为试卷题目的格式
                        question = self._convert_to_exam_question(content, question_type)
                        questions.append(question)
                else:
                    # 生成简单的示例试题
                    for i in range(still_remaining):
                        question = self._generate_sample_question(question_type, len(questions) + 1)
                        questions.append(question)

        # 6. 根据自适应难度调整题目
        adaptive_difficulty = config.get("adaptive_difficulty", None)
        if adaptive_difficulty:
            # 调整题目难度以匹配自适应难度
            questions = self._adjust_questions_for_adaptive_difficulty(questions, adaptive_difficulty)

        # 7. 限制最终题目数量
        return questions[:count]

    def _adjust_questions_for_adaptive_difficulty(self, questions: List[Dict[str, Any]], target_difficulty: float) -> List[Dict[str, Any]]:
        """根据自适应难度调整题目

        Args:
            questions: 题目列表
            target_difficulty: 目标难度

        Returns:
        if not questions:
            return questions

        adjusted_questions = []

        for question in questions:
            # 获取题目当前难度
            current_difficulty = question["difficulty"]

            # 根据目标难度调整题目难度
            if abs(current_difficulty - target_difficulty) > 1.0:
                # 调整幅度不超过1.0，保持题目原有特性
                if current_difficulty < target_difficulty:
                else:
                    adjusted_difficulty = max(1, current_difficulty - 1.0)

                # 更新题目难度
                question["difficulty"] = adjusted_difficulty
                question["difficulty_adjusted"] = True
            else:
                question["difficulty_adjusted"] = False

            adjusted_questions.append(question)

        return adjusted_questions

        """将生成的内容转换为试卷题目的格式

        Args:
            content: 生成的内容
            question_type: 题型

        Returns:
            试卷题目
        difficulty = content.get("difficulty", random.randint(1, 5))

        # 生成题目类型

        # 构建题目
        question = {
            "id": content["id"],
            "type": question_type,
            "subtype": question_subtype,
            "question": content["question"],
            "options": content.get("options", []),
            "correct_answer": content["correct_answer"],
            "explanation": content.get("explanation", ""),
            "difficulty": difficulty,
            "generated_by": content.get("agent_id", "system"),
            "source": content.get("source", "ai_generated")
        }

        # 添加特定题型的字段
            question["passage"] = content.get("passage", "")

        return question

    def _generate_sample_question(self, question_type: str, question_number: int) -> Dict[str, Any]:
        """生成示例试题
        Args:
            question_type: 题型
            question_number: 题序号

            示例试题
        # 日语N1级别题目数据库
            {
                "type": "vocabulary",
                "subtype": "collocation",
                "question": "「この計画は、実行に移す前に再三（　）必要がある。」下線に適切な言葉を入れなさい。",
                "options": ["吟味する", "吟醸する", "吟味になる", "吟醸になる"],
                "correct_answer": "吟味する",
                "explanation": "「吟味する」は「十分に考えて判断する」という意味で、計画や提案などに使われます。「吟醸する」は「じっくり考えて作り上げる」という意味で、酒や詩文などの创作に使われます。",
                "difficulty": 5
            },
            {
                "subtype": "structure",
                "question": "「彼は、長年の研究（　）、難しい問題を解決した。」下線に適切な助詞を入れなさい。",
                "options": ["をもって", "によって", "を通じて", "に基づいて"],
                "correct_answer": "をもって",
                "explanation": "「～をもって」は「手段・方法・資格などを示す」という意味で、特に努力や能力を手段として成果を上げる場合に使われます。",
                "difficulty": 5
            },
            {
                "type": "reading",
                "subtype": "inference",
                "passage": "現代社会において、情報技術の発展により、人々の生活スタイルは大きく変わってきています。特にスマートフォンの普及により、情報の入手やコミュニケーションの方法は飛躍的に進歩しました。しかし、これらの技術は便利である一方で、人々の注意力を分散させる原因ともなっています。研究によると、スマートフォンの使用が増えるにつれて、集中力が低下し、睡眠の質が悪化する傾向があることが明らかになっています。",
                "question": "文章によると、情報技術の発展はどのような影響を与えているか。",
                "options": [
                    "生活が便利になるだけで、悪影響はない。",
                    "情報入手とコミュニケーションが進歩し、集中力が向上する。",
                    "情報入手とコミュニケーションが進歩するが、集中力が低下する。",
                    "睡眠の質が向上するが、コミュニケーションが悪化する。"
                ],
                "difficulty": 5
            }
        ]

        # 生成示例试题
            # 随机选择日语N1词汇题或生成示例题
                # 选择日语N1词汇题
                n1_question = [q for q in japanese_n1_questions if q["type"] == "vocabulary"][0]
                    "id": f"japanese_n1_vocab_{question_number}",
                    "type": "vocabulary",
                    "subtype": n1_question["subtype"],
                    "question": n1_question["question"],
                    "options": n1_question["options"],
                    "correct_answer": n1_question["correct_answer"],
                    "explanation": n1_question["explanation"],
                    "difficulty": n1_question["difficulty"],
                    "score": 0,
                    "generated_by": "ai_japanese_n1",
                    "source": "japanese_n1"
                }
            else:
                # 生成英语示例题
                return {
                    "id": f"sample_vocab_{question_number}",
                    "type": "vocabulary",
                    "subtype": random.choice(self.supported_question_types["vocabulary"]),
                    "question": f"示例词汇题 {question_number}: 'example'的正确意思是什么？",
                    "options": ["选项A: 例子", "选项B: 样本", "选项C: 榜样", "选项D: 实例"],
                    "correct_answer": "选项A",
                    "explanation": "'example'的正确意思是'例子'。",
                    "difficulty": random.randint(1, 5),
                    "score": 0,
                    "generated_by": "system",
                }
        elif question_type == "grammar":
            # 随机选择日语N1语法题或生成示例题
            if random.random() < 0.5 and self.exam_config.get("language") == "ja-JP":
                # 选择日语N1语法题
                n1_question = [q for q in japanese_n1_questions if q["type"] == "grammar"][0]
                return {
                    "id": f"japanese_n1_grammar_{question_number}",
                    "type": "grammar",
                    "subtype": n1_question["subtype"],
                    "question": n1_question["question"],
                    "options": n1_question["options"],
                    "correct_answer": n1_question["correct_answer"],
                    "explanation": n1_question["explanation"],
                    "score": 0,
                    "generated_by": "ai_japanese_n1",
                    "source": "japanese_n1"
                }
            else:
                # 生成英语示例题
                return {
                    "id": f"sample_grammar_{question_number}",
                    "type": "grammar",
                    "subtype": random.choice(self.supported_question_types["grammar"]),
                    "question": f"示例语法题 {question_number}: 选择正确的语法结构。",
                    "correct_answer": "选项B",
                    "explanation": "主语是第三人称单数，动词需要加s。",
                    "difficulty": random.randint(1, 5),
                    "score": 0,
                    "generated_by": "system",
                    "source": "sample"
                }
        elif question_type == "reading":
            japanese_n1_questions = [
                {
                    "type": "reading",
                    "subtype": "inference",
                    "passage": "現代社会において、情報技術の発展により、人々の生活スタイルは大きく変わってきています。特にスマートフォンの普及により、情報の入手やコミュニケーションの方法は飛躍的に進歩しました。しかし、これらの技術は便利である一方で、人々の注意力を分散させる原因ともなっています。研究によると、スマートフォンの使用が増えるにつれて、集中力が低下し、睡眠の質が悪化する傾向があることが明らかになっています。",
                    "question": "文章によると、情報技術の発展はどのような影響を与えているか。",
                        "生活が便利になるだけで、悪影響はない。",
                        "情報入手とコミュニケーションが進歩するが、集中力が低下する。",
                        "睡眠の質が向上するが、コミュニケーションが悪化する。"
                    ],
                    "correct_answer": "情報入手とコミュニケーションが進歩するが、集中力が低下する。",
                    "explanation": "文章では、「情報技術の発展により、人々の生活スタイルは大きく変わってきています。特にスマートフォンの普及により、情報の入手やコミュニケーションの方法は飛躍的に進歩しました。しかし、これらの技術は便利である一方で、人々の注意力を分散させる原因ともなっています。」と述べられているため、正解は3番です。",
                    "difficulty": 5
                }
            ]

            if random.random() < 0.5 and self.exam_config.get("language") == "ja-JP":
                # 选择日语N1阅读题
                n1_question = japanese_n1_questions[0]
                return {
                    "subtype": n1_question["subtype"],
                    "passage": n1_question["passage"],
                    "question": n1_question["question"],
                    "explanation": n1_question["explanation"],
                    "difficulty": n1_question["difficulty"],
                    "score": 0,
                    "source": "japanese_n1"
            else:
                return {
                    "type": "reading",
                    "passage": "这是一段示例阅读材料，主要讲述了人工智能的发展历程和应用前景。",
                    "options": ["选项A: AI的历史", "选项B: AI的应用", "选项C: AI的发展和前景", "选项D: AI的挑战"],
                    "score": 0,
                    "source": "sample"
                }

                question_text = f"示例听力题 {question_number}: 这段听力材料的主要内容是什么？"
                options = ["选项A: 关于环境保护的讨论", "选项B: 介绍新的科技产品", "选项C: 描述一次旅行经历", "选项D: 解释一个科学现象"]
                correct_answer = "选项B"
            elif subtype == "detail_understanding":
                question_text = f"示例听力题 {question_number}: 说话者提到的会议时间是什么时候？"
                options = ["选项A: 周一上午10点", "选项B: 周二下午2点", "选项C: 周三上午9点", "选项D: 周四下午3点"]
                explanation = "听力中明确提到会议将在周三上午9点举行。"
                question_text = f"示例听力题 {question_number}: 从对话中可以推断出什么？"
            elif subtype == "vocabulary_in_context":
                correct_answer = "选项B"
            elif subtype == "speaker_intent":
                options = ["选项A: 提出建议", "选项B: 表达不满", "选项C: 请求帮助", "选项D: 分享经验"]
                question_text = f"示例听力题 {question_number}: 说话者强调的单词是哪个？"
                correct_answer = "选项B"
                explanation = "从说话者的语调可以判断出他非常兴奋。"
                question_text = f"示例听力题 {question_number}: 对话中女性说话者的身份是什么？"
                options = ["选项A: 教师", "选项B: 医生", "选项C: 记者", "选项D: 工程师"]
                correct_answer = "选项C"
                explanation = "根据对话内容，女性说话者是一名记者，正在进行采访。"
                question_text = f"示例听力题 {question_number}: 下列事件发生的正确顺序是什么？"
                options = ["选项A: 准备材料 → 开会讨论 → 执行计划", "选项B: 执行计划 → 准备材料 → 开会讨论", "选项C: 开会讨论 → 执行计划 → 准备材料", "选项D: 准备材料 → 执行计划 → 开会讨论"]
                correct_answer = "选项A"
                explanation = "听力中明确说明了事件的先后顺序：先准备材料，然后开会讨论，最后执行计划。"
                question_text = f"示例听力题 {question_number}: 对话发生在什么地方？"
                options = ["选项A: 办公室", "选项B: 医院", "选项C: 餐厅", "选项D: 机场"]
                explanation = "从对话中的背景声音和内容可以判断，对话发生在机场。"
            else:  # content_summarization
                question_text = f"示例听力题 {question_number}: 以下哪项最能概括听力内容？"
                options = ["选项A: 如何提高工作效率", "选项B: 介绍一家新公司", "选项C: 讨论健康饮食的重要性", "选项D: 解释气候变化的原因"]
                explanation = "听力主要讨论了提高工作效率的方法和技巧。"

            # 生成音频相关属性
            if difficulty <= 2:
                audio_type = random.choice(["dialogue", "monologue"])
                duration = random.randint(30, 60)
                audio_type = random.choice(["dialogue", "monologue", "news"])
                duration = random.randint(60, 120)
            else:
                speed = "fast"
                duration = random.randint(120, 240)
            return {
                "id": f"sample_listening_{question_number}",
                "subtype": subtype,
                "audio_url": f"sample_audio_{question_number}.mp3",
                "audio_type": audio_type,
                "audio_duration": duration,  # 秒
                "question": question_text,
                "options": options,
                "explanation": explanation,
                "difficulty": difficulty,
                "score": 0,
                "generated_by": "system",
                "source": "sample"
            }
        elif question_type == "writing":
                "id": f"sample_writing_{question_number}",
                "type": "writing",
                "subtype": random.choice(self.supported_question_types["writing"]),
                "question": f"示例写作题 {question_number}: 请以'人工智能对生活的影响'为题，写一篇不少于200字的短文。",
                "options": [],
                "correct_answer": "请根据题目要求完成写作。",
                "explanation": "评分标准：内容完整性（30%）、语言表达（40%）、结构合理性（30%）。",
                "difficulty": random.randint(2, 5),
                "generated_by": "system",
                "source": "sample"
            }
            return {
                "id": f"sample_speaking_{question_number}",
                "subtype": random.choice(self.supported_question_types["speaking"]),
                "question": f"示例口语题 {question_number}: 请谈谈你对'远程办公'的看法，时间约2分钟。",
                "options": [],
                "correct_answer": "请根据题目要求完成口语表达。",
                "explanation": "评分标准：流利度（30%）、词汇量（30%）、语法准确性（20%）、发音清晰度（20%）。",
                "difficulty": random.randint(2, 5),
                "score": 0,
                "generated_by": "system",
                "source": "sample"
            }
            return {
                "id": f"sample_{question_type}_{question_number}",
                "type": question_type,
                "subtype": "general",
                "question": f"示例{question_type}题 {question_number}",
                "options": ["选项A", "选项B", "选项C", "选项D"],
                "correct_answer": "选项A",
                "explanation": "示例解释。",
                "difficulty": random.randint(1, 5),
                "score": 0,
                "generated_by": "system",
                "source": "sample"
            }

    def _get_section_title(self, question_type: str) -> str:

        Args:
            question_type: 题型

        Returns:
            "vocabulary": "词汇部分",
            "grammar": "语法部分",
            "reading": "阅读部分",
            "speaking": "口语部分"
        }
        return titles.get(question_type, f"{question_type}部分")

    def _get_exam_title(self, language: str) -> str:
        """获取试卷标题

            language: 语言代码
        Returns:
            试卷标题
            "zh-CN": "自动生成试卷",
            "en-US": "Auto-Generated Exam",
            "ja-JP": "自動生成試験"
        }
        return titles.get(language, "自动生成试卷")
    def _connect_db(self):
        Returns:
            sqlite3连接对象

    def _get_questions_from_bank(self, question_type: str, count: int, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """从题库获取题目

        Args:
            count: 需要的题目数量

            从题库获取的题目列表
        questions = []

        try:
            conn = self._connect_db()
            conn.row_factory = sqlite3.Row
            # 获取难度范围
            min_diff = config.get("min_difficulty", self.exam_config["question_types"][question_type]["min_difficulty"])
            max_diff = config.get("max_difficulty", self.exam_config["question_types"][question_type]["max_difficulty"])

            SELECT question_id, question_text, question_type, subtype,
                   options, correct_answer, explanation, difficulty,
                   audio_url, audio_type, audio_duration, audio_speed,
            FROM exam_questions
            WHERE question_type = ? AND difficulty BETWEEN ? AND ?
            ORDER BY RANDOM()
            LIMIT ?

            cursor.execute(query, (question_type, min_diff, max_diff, count))
            rows = cursor.fetchall()

            # 转换为字典格式
                question = {
                    "question": row["question_text"],
                    "options": eval(row["options"]) if row["options"] else [],
                    "correct_answer": row["correct_answer"],
                    "difficulty": row["difficulty"],
                    "score": 0,  # 分数将在试卷级别设置
                    "generated_by": row["generated_by"],
                    "source": row["source"]
                }

                # 添加特定题型的字段
                    question.update({
                        "audio_type": row["audio_type"],
                        "audio_speed": row["audio_speed"]
                    })
                elif question_type == "reading":
                    question["passage"] = row["passage"]
            cursor.close()
            conn.close()

            logger.info(f"从题库获取了{len(questions)}道{question_type}题")
            return questions
        except Exception as e:
            return []


        Args:
            question_type: 需要扩充的题型
            needed_count: 需要扩充的题目数量

            扩充成功返回True

        try:
            new_questions = []

                # 使用AI系统生成新题目
                for content in generated_content:
                    # 转换为数据库格式
                        "question_id": f"ai_gen_{int(time.time() * 1000)}_{random.randint(1, 1000)}",
                        "question_text": content["question"],
                        "question_type": question_type,
                        "options": str(content.get("options", [])),
                        "correct_answer": content["correct_answer"],
                        "explanation": content.get("explanation", ""),
                        "difficulty": content.get("difficulty", random.randint(1, 5)),
                        "audio_url": content.get("audio_url", ""),
                        "audio_type": content.get("audio_type", ""),
                        "audio_duration": content.get("audio_duration", 0),
                        "audio_speed": content.get("audio_speed", ""),
                        "generated_by": content.get("agent_id", "system"),
                        "source": "ai_expanded",
                        "passage": content.get("passage", "")
                    }
                    new_questions.append(question)
                # 生成示例题目作为后备
                for i in range(needed_count):
                    sample_question = self._generate_sample_question(question_type, i + 1)
                    question = {
                        "question_id": sample_question["id"],
                        "question_text": sample_question["question"],
                        "question_type": sample_question["type"],
                        "subtype": sample_question["subtype"],
                        "options": str(sample_question["options"]),
                        "correct_answer": sample_question["correct_answer"],
                        "difficulty": sample_question["difficulty"],
                        "audio_url": sample_question.get("audio_url", ""),
                        "audio_type": sample_question.get("audio_type", ""),
                        "audio_speed": sample_question.get("audio_speed", ""),
                        "generated_by": sample_question["generated_by"],
                    }
                    new_questions.append(question)

            # 将新题目存入数据库
            if new_questions:
                conn = self._connect_db()
                cursor = conn.cursor()

                for question in new_questions:
                    cursor.execute('''
                    INSERT INTO exam_questions (
                        question_id, question_text, question_type, subtype,
                        options, correct_answer, explanation, difficulty,
                        generated_by, source, passage
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        question["question_id"],
                        question["question_type"],
                        question["subtype"],
                        question["options"],
                        question["correct_answer"],
                        question["explanation"],
                        question["difficulty"],
                        question["audio_type"],
                        question["audio_duration"],
                        question["audio_speed"],
                        question["generated_by"],
                        question["passage"]
                    ))

                conn.commit()
                cursor.close()
                conn.close()

                logger.info(f"成功扩充{len(new_questions)}道{question_type}题到题库")
                return True

            return False
        except Exception as e:
            return False

    def _calculate_adaptive_difficulty(self, user_info: Optional[Dict[str, Any]] = None) -> float:
        """计算自适应难度

        Args:
            user_info: 用户信息，包含历史表现等
        Returns:
            return 3.0  # 默认中等难度

        # 基于用户历史表现计算难度
        try:
            # 提取用户历史数据
            history_scores = user_info.get("history_scores", [])
            if not history_scores:
                return 3.0
            # 计算平均分数

            if avg_score >= 90:
                return min(5.0, 3.0 + 1.5)  # 高分学生，增加难度
            elif avg_score >= 70:
                return min(5.0, 3.0 + 0.5)  # 中等偏上，小幅增加难度
            elif avg_score >= 60:
                return 3.0  # 中等难度
            else:
                return max(1.0, 3.0 - 1.0)  # 低分学生，降低难度
        except Exception as e:
            logger.error(f"计算自适应难度失败: {str(e)}")
            return 3.0

    def update_learning_data(self, exam_id: str, user_performance: Dict[str, Any]) -> bool:
        """更新学习数据

        Args:
            exam_id: 试卷ID
            user_performance: 用户表现数据

        Returns:
            更新成功返回True
        try:
            # 解析用户表现数据
            question_results = user_performance.get("question_results", [])

            for result in question_results:
                actual_difficulty = result.get("actual_difficulty", 0)  # 用户实际感受到的难度
                is_correct = result.get("is_correct", False)
                response_time = result.get("response_time", 0)  # 答题时间

                # 更新题目表现数据
                    self.learning_data["question_performance"][question_id] = {
                        "correct_attempts": 0,
                        "avg_response_time": 0,
                        "difficulty_feedback": []
                    }

                qp = self.learning_data["question_performance"][question_id]
                qp["total_attempts"] += 1
                if is_correct:
                    qp["correct_attempts"] += 1

                # 更新平均响应时间
                qp["avg_response_time"] = ((qp["avg_response_time"] * (qp["total_attempts"] - 1)) + response_time) / qp["total_attempts"]

                # 更新难度反馈
                qp["difficulty_feedback"].append(actual_difficulty)

            # 更新反馈计数
            self.learning_data["feedback_count"] += 1

            logger.info(f"成功更新学习数据，当前反馈次数: {self.learning_data['feedback_count']}")
            return True
        except Exception as e:
            logger.error(f"更新学习数据失败: {str(e)}")
            return False

    def self_learn(self) -> bool:
        """自我学习，优化试卷生成算法

        Returns:
            学习成功返回True
        logger.info("开始自我学习")

        try:
            # 基于收集到的学习数据优化模型
            if self.learning_data["feedback_count"] < 10:  # 至少需要10条反馈数据
                return False

            # 分析题目难度调整
            for question_id, performance in self.learning_data["question_performance"].items():
                if performance["total_attempts"] < 5:  # 至少需要5次尝试
                    continue

                # 计算实际通过率
                pass_rate = performance["correct_attempts"] / performance["total_attempts"]

                # 基于通过率调整难度
                if pass_rate < 0.3:  # 通过率低，实际难度较高
                    adjustment = 0.5
                    adjustment = -0.5
                else:
                    adjustment = 0

                # 更新难度调整系数
                self.learning_data["difficulty_adjustments"][question_id] = adjustment

            # 优化题型分布
            # 这里可以添加更复杂的优化逻辑，例如基于用户表现调整各题型权重

            logger.info("自我学习完成")
            return True
        except Exception as e:
            logger.error(f"自我学习失败: {str(e)}")
            return False

    def load_japanese_level(self, user_info: Dict[str, Any]) -> Optional[str]:
        """从用户信息中载入日语能力等级

        Args:
            user_info: 用户信息

        Returns:
            用户的日语能力等级，如N1-N5，或None如果未指定
        if not user_info:
            return None

        # 从用户信息中获取日语能力等级
        profile = user_info.get("profile", {})
        language_level = profile.get("language_level", "")
        # 检查是否是有效的日语能力等级
            return language_level.upper()

        # 检查是否有JLPT相关信息
        if jlpt_level.upper() in self.exam_config["japanese_levels"]:

        return None

    def generate_placement_test(self, language: str = "ja-JP") -> Dict[str, Any]:
        """生成日语等级摸底测试

            language: 语言代码，默认为日语
        Returns:
        logger.info("开始生成日语等级摸底测试")

        # 获取摸底测试配置
        placement_config = self.exam_config["placement_test"]

        # 生成测试基本信息
        test = {
            "id": f"placement_test_{int(time.time() * 1000)}",
            "generated_at": datetime.now().isoformat(),
            "title": f"日语等级摸底测试",
            "duration": placement_config["duration"],
            "total_score": placement_config["total_score"],
            "language": language,
            "test_type": "placement",
        }

        # 生成各部分试题
        total_questions = placement_config["total_questions"]

        # 根据权重分配各题型数量
        for question_type, weight in placement_config["question_types"].items():
            count = int(total_questions * weight)
            if count <= 0:
                continue


            # 生成该类型的试题，难度覆盖所有级别
            config = {
                "min_difficulty": 1,
                "max_difficulty": 5
            }
            questions = self._generate_section_questions(question_type, count, config)

                # 计算该部分的分数
                section_score = int(test["total_score"] * weight)
                score_per_question = section_score / len(questions)

                # 更新每个题目的分数
                for question in questions:
                    question["score"] = score_per_question

                # 添加到测试中
                section = {
                    "type": question_type,
                    "title": self._get_section_title(question_type),
                    "questions": questions,
                    "total_questions": len(questions),
                    "total_score": section_score,
                    "score_per_question": score_per_question
                }

        logger.info(f"成功生成日语等级摸底测试，共{sum(len(s['questions']) for s in test['sections'])}道题")
        return test

    def evaluate_placement_test(self, test_results: Dict[str, Any]) -> str:
        """评估摸底测试结果并确定日语能力等级

        Args:
            test_results: 测试结果，包含总分

        Returns:
            确定的日语能力等级，如N1-N5

        try:
            # 获取测试总分
            placement_config = self.exam_config["placement_test"]
            # 根据分数范围确定等级
            for score_range, level in placement_config["level_detection"].items():
                min_score, max_score = map(int, score_range.split("-"))
                if min_score <= total_score <= max_score:
                    logger.info(f"测试总分{total_score}，确定等级为{level}")
                    return level

            # 默认返回最低等级
        except Exception as e:
            return "N5"

    def generate_japanese_exam(self, user_info: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """生成日语考试，自动处理等级确定
        Args:
            user_info: 用户信息
        Returns:
            生成的试卷或摸底测试
        logger.info("开始生成日语考试")
        # 检查用户日语能力等级
        user_level = self.load_japanese_level(user_info)

            # 用户已有明确等级，生成对应难度的试卷
            logger.info(f"用户已有日语能力等级: {user_level}")

            level_config = self.exam_config["japanese_levels"][user_level]

            # 生成试卷配置
            exam_config = {
                "language": "ja-JP",
                "difficulty_level": user_level,
                "total_questions": 30,
                "duration": 60,
                "total_score": 100
            }

            # 生成试卷
            return self.generate_exam(exam_config, user_info)
            # 用户等级不确定，生成摸底测试
            return self.generate_placement_test()

        """处理日语考试请求，自动管理等级确定流程
        Args:
            user_info: 用户信息
        Returns:
        result = {
            "status": "success",
            "data": {}
        }

            # 生成日语考试或摸底测试

            # 检查是否是摸底测试
            if exam.get("test_type") == "placement":
            else:

            return result
            result["status"] = "error"
            return result
    def auto_upgrade(self) -> bool:
        """自动升级试卷生成器

        Returns:
            升级成功返回True
        logger.info("开始自动升级试卷生成器")

        # 检查是否需要升级
        if self._check_upgrade_needed():
            # 执行升级
            upgrade_result = self._perform_upgrade()
            if upgrade_result:
                logger.info(f"试卷生成器成功升级到版本 {self.version}")
                return True

        logger.info("试卷生成器已是最新版本，无需升级")
        return False

    def _check_upgrade_needed(self) -> bool:
        """检查是否需要升级

        Returns:
            需要升级返回True
        # 简单的升级检查逻辑，实际可以从服务器获取最新版本信息
        import random
        return random.choice([True, False])  # 随机决定是否需要升级

    def _perform_upgrade(self) -> bool:
        """执行升级

        Returns:
            升级成功返回True
        try:
            # 升级版本号
            version_parts = list(map(int, self.version.split('.')))
            version_parts[2] += 1  # 升级补丁版本
            self.version = '.'.join(map(str, version_parts))

            self._expand_supported_question_types()

            # 更新配置
            self._update_exam_config()

            self.last_update_time = datetime.now()

            logger.info(f"成功升级试卷生成器到版本 {self.version}")
        except Exception as e:
            logger.error(f"升级失败: {str(e)}")
            return False

    def _expand_supported_question_types(self) -> None:
        """扩展支持的题型
        # 添加新的题型
        new_question_types = {
            "listening": ["main_idea", "detail_understanding", "inference", "vocabulary_in_context", "speaker_intent"],
            "writing": ["essay", "email", "report", "summary", "description"],
            "speaking": ["topic_discussion", "picture_description", "role_play", "story_telling", "opinion_expression"]
        }

        # 更新支持的题型

        # 更新试题类型配置
        for question_type in new_question_types:
            if question_type not in self.exam_config["question_types"]:
                self.exam_config["question_types"][question_type] = {
                    "min_difficulty": 1,
                    "max_difficulty": 5
                }

        logger.info(f"扩展支持的题型，现在支持{len(self.supported_question_types)}种题型")

    def _update_exam_config(self) -> None:
        """更新试卷配置
        # 更新配置，添加新的设置
        self.exam_config["enable_adaptive_difficulty"] = True
        self.exam_config["enable_personalization"] = True
        self.exam_config["enable_feedback_learning"] = True

        logger.info("更新了试卷配置，添加了自适应难度、个性化和反馈学习功能")
    def export_exam(self, exam: Dict[str, Any], format: str = "db", output_file: str = None) -> str:
        """导出试卷

            exam: 试卷
            output_file: 输出文件路径

        Returns:
            输出文件路径或成功消息
        logger.info(f"导出试卷，格式: {format}")

        if format == "db":
            # 将试卷保存到数据库
            cursor = conn.cursor()

            try:
                # 插入试卷基本信息
                cursor.execute('''
                INSERT INTO exam_papers (id, title, duration, total_score, language, difficulty_level, generated_at, version, total_questions)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    exam['id'],
                    exam['title'],
                    exam['duration'],
                    exam['total_score'],
                    exam['language'],
                    exam['difficulty_level'],
                    exam['version'],
                    sum(len(s['questions']) for s in exam['sections'])
                ))
                for section in exam['sections']:
                    cursor.execute('''
                    INSERT INTO exam_sections (paper_id, type, title, total_questions, total_score, score_per_question)
                    VALUES (?, ?, ?, ?, ?, ?)
                        exam['id'],
                        section['type'],
                        section['title'],
                        section['total_questions'],
                        section['total_score'],
                        section['score_per_question']
                    ))
                    section_id = cursor.lastrowid

                    # 插入题目信息
                    for question in section['questions']:
                        # 处理选项，转换为JSON字符串（数据库中存储为TEXT）
                        options_json = str(question.get('options', []))

                        cursor.execute('''
                        INSERT INTO exam_questions (
                            paper_id, section_id, question_id, question_text, question_type, subtype,
                            options, correct_answer, explanation, difficulty, score,
                            audio_url, audio_type, audio_duration, audio_speed,
                            generated_by, source, passage
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            exam['id'],
                            section_id,
                            question['id'],
                            question['question'],
                            question['type'],
                            question['subtype'],
                            options_json,
                            question['correct_answer'],
                            question.get('explanation', ''),
                            question['difficulty'],
                            question.get('audio_url', ''),
                            question.get('audio_type', ''),
                            question.get('audio_duration', 0),
                            question.get('audio_speed', ''),
                            question.get('generated_by', 'system'),
                            question.get('source', 'ai_generated'),
                            question.get('passage', '')
                        ))

                conn.commit()
                return f"试卷已保存到数据库，ID: {exam['id']}"
            except Exception as e:
                logger.error(f"保存试卷到数据库失败: {str(e)}")
                conn.rollback()
            finally:
                cursor.close()
                conn.close()
            # 导出为Markdown
            if not output_file:
                output_file = f"exam_{exam['id']}.markdown"

            markdown_content = self._convert_to_markdown(exam)
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
            logger.info(f"试卷已导出为Markdown文件: {output_file}")
            return output_file
        else:
            logger.error(f"不支持的导出格式: {format}")
            return None

    def _convert_to_markdown(self, exam: Dict[str, Any]) -> str:
        """将试卷转换为Markdown格式

        Args:
            exam: 试卷

        Returns:
            Markdown格式的试卷
        md = f"# {exam['title']}\n\n"
        md += f"**试卷ID**: {exam['id']}\n"
        md += f"**生成时间**: {exam['generated_at']}\n"
        md += f"**时长**: {exam['duration']}分钟\n"
        md += f"**总分**: {exam['total_score']}分\n\n"

        for section in exam['sections']:
            md += f"## {section['title']}\n\n"
            md += f"**题型**: {section['type']}\n"
            md += f"**题数**: {section['total_questions']}题\n"
            md += f"**分值**: {section['total_score']}分\n\n"

            for i, question in enumerate(section['questions'], 1):
                md += f"### 第 {i} 题 ({question['score']:.1f}分)\n"
                md += f"**题型**: {question['subtype']}\n"
                md += f"**难度**: {'★' * question['difficulty']}\n\n"

                    md += f"**阅读材料**:\n{question['passage']}\n\n"

                md += f"**题目**: {question['question']}\n\n"

                if question['options']:
                    md += "**选项**:\n"
                    for option in question['options']:
                        md += f"- {option}\n"

                md += f"**正确答案**: {question['correct_answer']}\n\n"

                if question['explanation']:
                    md += f"**解析**: {question['explanation']}\n\n"

        return md

    def evaluate_exam(self, exam: Dict[str, Any]) -> Dict[str, Any]:
        """评估试卷质量

        Args:
            exam: 试卷

        Returns:
            评估结果
        logger.info(f"评估试卷 {exam['id']}")

        # 计算试卷评估指标
        total_questions = sum(len(s['questions']) for s in exam['sections'])
        difficulty_levels = [q['difficulty'] for s in exam['sections'] for q in s['questions']]
        avg_difficulty = sum(difficulty_levels) / total_questions if total_questions > 0 else 0

        question_type_distribution = {}
        for section in exam['sections']:
            question_type_distribution[section['type']] = section['total_questions']

        # 计算难度分布
        difficulty_distribution = {
            "easy": sum(1 for d in difficulty_levels if d <= 2),
            "medium": sum(1 for d in difficulty_levels if 3 <= d <= 4),
            "hard": sum(1 for d in difficulty_levels if d == 5)
        }

        # 计算题型多样性
        unique_subtypes = set()
        for section in exam['sections']:
            for question in section['questions']:
                unique_subtypes.add(f"{question['type']}_{question['subtype']}")

        # 计算各部分分数分布
        section_score_distribution = {}
            section_score_distribution[section['type']] = section['total_score']

        # 生成评估结果
        coverage_score = self._calculate_coverage_score(exam)
        diversity_score = self._calculate_diversity_score(exam)

        # 计算总分
        overall_score = (coverage_score * 0.4 + diversity_score * 0.3 + balance_score * 0.3)

        evaluation = {
            "exam_id": exam['id'],
            "evaluation_time": datetime.now().isoformat(),
            "total_questions": total_questions,
            "total_score": exam['total_score'],
            "avg_difficulty": round(avg_difficulty, 2),
            "difficulty_distribution": difficulty_distribution,
            "section_score_distribution": section_score_distribution,
            "unique_subtypes_count": len(unique_subtypes),
            "coverage_score": round(coverage_score, 2),
            "diversity_score": round(diversity_score, 2),
            "balance_score": round(balance_score, 2),
            "overall_score": round(overall_score, 2),
            "recommendations": []
        }

        # 生成建议
        evaluation["recommendations"] = self._generate_recommendations(evaluation, exam)

        logger.info(f"试卷评估完成，总分: {evaluation['overall_score']:.2f}")
        return evaluation

    def _calculate_coverage_score(self, exam: Dict[str, Any]) -> float:
        """计算知识点覆盖率分数

        Args:
            exam: 试卷

        Returns:
            覆盖率分数（0-100）
        # 简单的覆盖率计算，实际可以基于知识库计算
        return random.uniform(70, 95)

    def _calculate_diversity_score(self, exam: Dict[str, Any]) -> float:
        """计算题型多样性分数

        Args:
            exam: 试卷
        Returns:
            多样性分数（0-100）
        # 计算题型多样性
        unique_subtypes = set()
        for section in exam['sections']:
            for question in section['questions']:

        # 计算多样性分数
        total_possible_subtypes = sum(len(v) for v in self.supported_question_types.values())
        diversity_ratio = len(unique_subtypes) / total_possible_subtypes
        return diversity_ratio * 100

    def _calculate_balance_score(self, exam: Dict[str, Any]) -> float:
        """计算试卷平衡性分数

        Args:
            exam: 试卷

            平衡性分数（0-100）
        # 计算题型平衡性
        total_questions = sum(len(s['questions']) for s in exam['sections'])
        ideal_distribution = self.exam_config["question_types"]

        # 计算各题型实际比例与理想比例的偏差
        balance_score = 100
        for section in exam['sections']:
            question_type = section['type']
            if question_type in ideal_distribution:
                actual_ratio = len(section['questions']) / total_questions
                deviation = abs(actual_ratio - ideal_ratio)
                balance_score -= deviation * 100

        return max(0, min(100, balance_score))

    def _generate_recommendations(self, evaluation: Dict[str, Any], exam: Dict[str, Any]) -> List[str]:
        """生成改进建议

            evaluation: 评估结果
            exam: 试卷

            改进建议列表
        recommendations = []

        # 难度分布建议
        if evaluation["avg_difficulty"] < 2:
            recommendations.append("建议增加一些难度较高的题目，以提高试卷的区分度")
            recommendations.append("建议增加一些难度较低的题目，以照顾不同水平的考生")

        # 难度比例建议
        total_questions = evaluation["total_questions"]
            recommendations.append("建议增加简单题的比例，以符合一般试卷难度分布")
            recommendations.append("建议增加难题的比例，以更好地区分优秀考生")

        # 知识点覆盖率建议
        if evaluation["coverage_score"] < 80:

        # 题型多样性建议
        if evaluation["diversity_score"] < 70:
            recommendations.append("建议增加题型多样性，使用更多不同类型的题目")

        # 试卷平衡性建议
        if evaluation["balance_score"] < 70:
            recommendations.append("建议调整各题型的比例，使其更符合理想分布")
        if exam['language'] not in self.exam_config["languages"]["supported"]:
            recommendations.append(f"建议使用支持的语言：{', '.join(self.exam_config['languages']['supported'])}")
        return recommendations
        """与AI系统集成
            ai_system: AI系统实例
            集成成功返回True
        try:
            self.ai_system = ai_system
            logger.info("成功与AI系统集成")
            return True
        except Exception as e:
            return False

# 导入缺失的模块

# 简单的测试函数
def test_exam_generator():
    """测试试卷生成器"""
    # 创建试卷生成器
    generator = ExamGenerator()

    # 测试1: 基本试卷生成
    exam = generator.generate_exam({
        "total_questions": 20,
        "total_score": 100,
        "language": "zh-CN",
        "difficulty_level": "medium"
    })

    print(f"生成的试卷包含{sum(len(s['questions']) for s in exam['sections'])}道题")

    # 测试2: 自适应难度生成
    print("\n=== 测试2: 自适应难度生成 ===")
    user_info = {
            "user_id": "test_user_1",
            "language_level": "B2",
            "subject": "English"
        },
        "history_scores": [95, 92, 88, 90, 94]  # 高分学生，应该生成难度较高的题目
    }

    adaptive_exam = generator.generate_exam(
        {
            "total_questions": 10,
            "difficulty_level": "adaptive"
        },
        user_info=user_info
    )

    print(f"自适应试卷包含{sum(len(s['questions']) for s in adaptive_exam['sections'])}道题")
    print(f"自适应难度: {adaptive_exam.get('adaptive_difficulty')}")

    # 计算自适应试卷的平均难度
    total_difficulty = 0
    total_questions = 0
    for section in adaptive_exam['sections']:
        for question in section['questions']:
            total_difficulty += question['difficulty']
            total_questions += 1
    print(f"自适应试卷平均难度: {avg_difficulty:.2f}")
    # 测试3: 题库扩充功能
    print("\n=== 测试3: 题库扩充功能 ===")
    # 统计各题型的题目数量
    conn = generator._connect_db()
    cursor = conn.cursor()

    cursor.execute("SELECT question_type, COUNT(*) FROM exam_questions GROUP BY question_type")
    question_counts = cursor.fetchall()

    print("当前题库各题型数量:")
    for question_type, count in question_counts:
        print(f"  {question_type}: {count}道题")

    cursor.close()
    conn.close()

    # 测试4: 学习数据更新
    print("\n=== 测试4: 学习数据更新 ===")
    # 模拟用户表现数据
    user_performance = {
        "question_results": [
            {
                "question_id": "sample_vocab_1",
                "actual_difficulty": 3
            },
            {
                "question_id": "sample_grammar_1",
                "is_correct": False,
                "response_time": 25,
                "actual_difficulty": 4
            },
            {
                "question_id": "sample_reading_1",
                "is_correct": True,
                "response_time": 30,
                "actual_difficulty": 3.5
            }
        ]
    }

    update_result = generator.update_learning_data(exam['id'], user_performance)
    print(f"学习数据更新结果: {'成功' if update_result else '失败'}")
    print(f"当前反馈次数: {generator.learning_data['feedback_count']}")

    # 测试5: 自我学习功能
    # 为了触发自我学习，我们需要添加更多反馈数据
    for i in range(10):
    print(f"增加反馈数据后，当前反馈次数: {generator.learning_data['feedback_count']}")
    learn_result = generator.self_learn()
    print(f"自我学习结果: {'成功' if learn_result else '失败'}")

    # 测试6: 导出功能
    print("\n=== 测试6: 导出功能 ===")
    md_file = generator.export_exam(exam, format="markdown")
    print(f"Markdown导出结果: {md_file}")

    print("\n=== 测试7: 试卷评估 ===")
    evaluation = generator.evaluate_exam(exam)
    print(f"试卷评估总分: {evaluation['overall_score']:.2f}")
    print(f"建议: {evaluation['recommendations']}")

    # 测试8: 自动升级
    print("\n=== 测试8: 自动升级 ===")
    upgrade_result = generator.auto_upgrade()
    print(f"自动升级结果: {'成功' if upgrade_result else '失败'}")
    print(f"升级后版本: {generator.version}")

    # 测试9: 日语能力等级载入
    print("\n=== 测试9: 日语能力等级载入 ===")
    # 测试有明确日语等级的用户
            "user_id": "japanese_user_1",
            "language_level": "N2",
            "subject": "Japanese"
        }
    }

    loaded_level = generator.load_japanese_level(user_with_japanese_level)
    print(f"有明确等级的用户，载入结果: {loaded_level}")

    # 测试无明确日语等级的用户
    user_without_japanese_level = {
        "profile": {
            "user_id": "new_japanese_user",
            "language_level": "beginner",
            "subject": "Japanese"
        }
    }

    loaded_level = generator.load_japanese_level(user_without_japanese_level)
    print(f"无明确等级的用户，载入结果: {loaded_level}")

    # 测试10: 日语等级摸底测试生成
    print("\n=== 测试10: 日语等级摸底测试生成 ===")
    placement_test = generator.generate_placement_test()
    print(f"摸底测试包含{sum(len(s['questions']) for s in placement_test['sections'])}道题")
    print(f"测试类型: {placement_test['test_type']}")
    print(f"测试时长: {placement_test['duration']}分钟")
    # 测试11: 日语等级评估
    print("\n=== 测试11: 日语等级评估 ===")
    # 测试不同分数对应的等级
    test_results = {"total_score": 95}
    level = generator.evaluate_placement_test(test_results)

    test_results = {"total_score": 75}
    level = generator.evaluate_placement_test(test_results)
    print(f"总分75分，评估等级: {level}")

    test_results = {"total_score": 55}
    level = generator.evaluate_placement_test(test_results)
    print(f"总分55分，评估等级: {level}")

    # 测试12: 日语考试生成（有明确等级）
    print("\n=== 测试12: 日语考试生成（有明确等级） ===")
    japanese_exam_with_level = generator.generate_japanese_exam(user_with_japanese_level)
    print(f"有明确等级的日语考试，测试类型: {japanese_exam_with_level.get('test_type', 'exam')}")
    print(f"考试难度等级: {japanese_exam_with_level['difficulty_level']}")
    print(f"考试包含{sum(len(s['questions']) for s in japanese_exam_with_level['sections'])}道题")

    # 测试13: 日语考试生成（无明确等级，生成摸底测试）
    print("\n=== 测试13: 日语考试生成（无明确等级） ===")
    japanese_exam_without_level = generator.generate_japanese_exam(user_without_japanese_level)
    print(f"无明确等级的日语考试，测试类型: {japanese_exam_without_level['test_type']}")
    print(f"测试包含{sum(len(s['questions']) for s in japanese_exam_without_level['sections'])}道题")

    # 测试14: 日语考试请求处理
    print("\n=== 测试14: 日语考试请求处理 ===")
    # 处理有明确等级的用户请求
    result_with_level = generator.process_japanese_exam_request(user_with_japanese_level)
    print(f"有明确等级的请求处理结果: {result_with_level['status']}")
    print(f"处理消息: {result_with_level['message']}")

    # 处理无明确等级的用户请求
    result_without_level = generator.process_japanese_exam_request(user_without_japanese_level)
    print(f"无明确等级的请求处理结果: {result_without_level['status']}")
    print(f"处理消息: {result_without_level['message']}")

if __name__ == "__main__":
    test_exam_generator()
