#!/usr/bin/env python3
"""
多AI相互学习与自我升级迭代系统
实现多个AI实例之间的相互学习、评估和自我升级

import os
import sys
# JSON import removed - using database
import random
import time
import logging
from datetime import datetime
from typing import Dict, List, Any

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('multi_ai_learning.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('multi_ai_learning')

class AILearningAgent:
    """AI学习代理，具有学习、生成、评估和升级能力"""

    def __init__(self, agent_id: str, specialization: str):
        """初始化AI学习代理

        Args:
            agent_id: 代理ID
            specialization: 专业领域（如：vocabulary, grammar, reading, general）
        self.agent_id = agent_id
        self.specialization = specialization
        self.model_version = "1.0.0"
        self.learning_rate = 0.1
        self.experience_points = 0
        self.creation_time = datetime.now()
        self.last_update_time = datetime.now()

        # 知识存储 - 结构化知识库
        self.knowledge_base = {
            "vocabulary": [],
            "grammar": [],
            "reading": [],
            "strategies": []
        }

        # 知识库验证规则
        self.knowledge_validation_rules = {
            "vocabulary": {
                "required_fields": ["word", "meaning", "part_of_speech"],
                "min_length": 2
            },
            "grammar": {
                "required_fields": ["rule", "example", "explanation"],
                "min_length": 5
            },
            "reading": {
                "min_length": 10
            },
            "strategies": {
                "min_length": 5
            }
        }
        self.learning_history = []
        # 评估标准
        self.evaluation_criteria = {
            "quality": 0.4,  # 题目质量权重
            "relevance": 0.3,  # 相关性权重
            "creativity": 0.2,  # 创新性权重
            "difficulty": 0.1  # 难度权重
        }

        self.neural_network = None
        self.has_neural_network = False
        self._init_neural_network()

        # 预加载基础知识
        self._load_initial_knowledge()

        logger.info(f"初始化AI学习代理: {agent_id}, 专业: {specialization}")

    def _init_neural_network(self):
        """初始化神经网络"""
        try:
            # 动态导入神经网络模块，避免依赖问题
            from neural_network import SimpleQuestionClassifier

            # 初始化问题分类器
            self.neural_network = SimpleQuestionClassifier()
            self.has_neural_network = True
            logger.info(f"AI {self.agent_id} 成功初始化神经网络")
        except ImportError as e:
            logger.warning(f"AI {self.agent_id} 无法导入神经网络模块: {str(e)}")
        except Exception as e:
            logger.error(f"AI {self.agent_id} 初始化神经网络失败: {str(e)}")

    def use_neural_network(self, X: Any) -> Any:
        """使用神经网络进行预测

        Args:
            X: 输入数据
        Returns:
            预测结果
        if self.has_neural_network and self.neural_network:
            try:
                return self.neural_network.predict(X)
            except Exception as e:
                logger.error(f"AI {self.agent_id} 使用神经网络失败: {str(e)}")
        return None

    def train_neural_network(self, X: Any, y: Any) -> bool:
        """训练神经网络

        Args:
            y: 真实标签
        Returns:
            训练成功返回True
        if self.has_neural_network and self.neural_network:
            try:
                self.neural_network.train(X, y)
                logger.info(f"AI {self.agent_id} 成功训练神经网络")
                return True
            except Exception as e:
                logger.error(f"AI {self.agent_id} 训练神经网络失败: {str(e)}")

    def _load_initial_knowledge(self):
        """加载初始知识库内容"""
        initial_vocab = [
            {
                "id": f"vocab_001_{self.agent_id}",
                "meaning": "你好",
                "part_of_speech": "感叹词",
                "source": "initial",
                "added_at": datetime.now().isoformat(),
                "quality_score": 1.0
            },
            {
                "id": f"vocab_002_{self.agent_id}",
                "word": "ありがとう",
                "meaning": "谢谢",
                "part_of_speech": "感叹词",
                "source": "initial",
                "added_at": datetime.now().isoformat(),
                "quality_score": 1.0
            {
                "id": f"vocab_003_{self.agent_id}",
                "word": "すみません",
                "meaning": "对不起/打扰一下",
                "part_of_speech": "感叹词",
                "source": "initial",
                "added_at": datetime.now().isoformat(),
                "quality_score": 1.0
            {
                "word": "いただきます",
                "meaning": "我开动了（吃饭前）",
                "part_of_speech": "感叹词",
                "source": "initial",
                "quality_score": 1.0
                "id": f"vocab_005_{self.agent_id}",
                "part_of_speech": "感叹词",
                "added_at": datetime.now().isoformat(),
                "quality_score": 1.0
                "id": f"vocab_006_{self.agent_id}",
                "word": "さようなら",
                "source": "initial",
                "added_at": datetime.now().isoformat(),
            {
                "id": f"vocab_007_{self.agent_id}",
                "source": "initial",
                "added_at": datetime.now().isoformat(),
            {
                "id": f"vocab_008_{self.agent_id}",
                "word": "こんばんは",
                "added_at": datetime.now().isoformat(),
                "quality_score": 1.0
            {
                "meaning": "晚安",
                "part_of_speech": "感叹词",
                "source": "initial",
            {
                "word": "はい",
                "meaning": "是/对",
                "part_of_speech": "感叹词",
                "added_at": datetime.now().isoformat(),
                "word": "いいえ",
                "meaning": "不是/不对",
                "part_of_speech": "感叹词",
                "added_at": datetime.now().isoformat(),
                "quality_score": 1.0
                "id": f"vocab_012_{self.agent_id}",
                "meaning": "你好",
                "part_of_speech": "感叹词",
                "added_at": datetime.now().isoformat(),
            },
                "word": "thank you",
                "source": "initial",
                "added_at": datetime.now().isoformat(),
                "quality_score": 1.0
            {
                "word": "sorry",
                "part_of_speech": "感叹词",
            {
                "id": f"vocab_015_{self.agent_id}",
                "word": "please",
                "part_of_speech": "感叹词",
                "source": "initial",
                "added_at": datetime.now().isoformat(),
                "quality_score": 1.0
                "source": "initial",
                "added_at": datetime.now().isoformat(),
                "quality_score": 1.0
            {
                "id": f"vocab_017_{self.agent_id}",
                "meaning": "早上",
                "added_at": datetime.now().isoformat(),
            {
                "meaning": "下午",
                "part_of_speech": "名词",
                "source": "initial",
            {
                "id": f"vocab_019_{self.agent_id}",
                "word": "evening",
                "part_of_speech": "名词",
                "added_at": datetime.now().isoformat(),
                "word": "night",
                "meaning": "夜晚",
                "part_of_speech": "名词",
                "source": "initial",
                "quality_score": 1.0
                "id": f"vocab_021_{self.agent_id}",
                "word": "yes",
                "source": "initial",
                "quality_score": 1.0
            {
                "meaning": "不是",
                "part_of_speech": "感叹词",
                "added_at": datetime.now().isoformat(),
                "quality_score": 1.0
                "id": f"vocab_023_{self.agent_id}",
                "meaning": "学生",
                "part_of_speech": "名词",
                "quality_score": 1.0
            {
                "id": f"vocab_024_{self.agent_id}",
                "word": "teacher",
                "source": "initial",
                "added_at": datetime.now().isoformat(),
            {
                "id": f"vocab_025_{self.agent_id}",
                "meaning": "书",
                "source": "initial",
                "added_at": datetime.now().isoformat(),
            {
                "word": "school",
                "meaning": "学校",
                "part_of_speech": "名词",
        ]

            {
                "rule": "ています",
                "explanation": "表示正在进行的动作",
                "source": "initial",
                "added_at": datetime.now().isoformat(),
                "quality_score": 1.0
            {
                "source": "initial",
                "added_at": datetime.now().isoformat(),
                "quality_score": 1.0
            },
            {
                "rule": "て形",
                "example": "私はご飯を食べて、本を読みます。",
            {
                "rule": "ない形",
                "example": "私は日本語が話せません。",
                "explanation": "表示否定的动作或状态",
                "added_at": datetime.now().isoformat(),
                "quality_score": 1.0
            {
                "rule": "た形",
                "source": "initial",
                "added_at": datetime.now().isoformat(),
                "quality_score": 1.0
                "id": f"grammar_006_{self.agent_id}",
                "example": "I eat breakfast every day.",
                "explanation": "表示习惯性动作或客观事实",
                "added_at": datetime.now().isoformat(),
            },
                "id": f"grammar_007_{self.agent_id}",
                "explanation": "表示正在进行的动作",
                "source": "initial",
                "added_at": datetime.now().isoformat(),
                "quality_score": 1.0
            {
                "rule": "past simple",
                "added_at": datetime.now().isoformat(),
                "quality_score": 1.0
            },
            {
                "rule": "future simple",
                "explanation": "表示将来要发生的动作",
                "added_at": datetime.now().isoformat(),
                "rule": "present perfect",
                "example": "I have eaten breakfast already.",
                "explanation": "表示过去发生的动作对现在的影响",
                "source": "initial",
            }
        # 初始阅读知识（扩充版）
        initial_reading = [
                "id": f"reading_001_{self.agent_id}",
                "source": "initial",
                "quality_score": 1.0
            {
                "id": f"reading_002_{self.agent_id}",
                "topic": "英语学习",
                "content": "英语是世界上使用最广泛的语言之一，也是国际交流的重要工具。学习英语可以帮助我们更好地了解世界，扩大知识面，提高竞争力。英语学习包括听、说、读、写四个方面，需要全面发展。通过不断练习和积累，我们可以逐步提高英语水平，实现与世界的无障碍交流。",
                "keywords": ["英语", "学习", "交流", "听", "说", "读", "写"],
            },
                "topic": "人工智能",
                "keywords": ["人工智能", "机器学习", "深度学习", "应用", "挑战"],
                "source": "initial",
                "added_at": datetime.now().isoformat(),
            {
                "id": f"reading_004_{self.agent_id}",
                "keywords": ["环境", "保护", "污染", "资源", "气候"],
                "added_at": datetime.now().isoformat(),
                "quality_score": 1.0
            {
                "topic": "科技发展",
                "keywords": ["科技", "发展", "进步", "便利", "挑战"],
                "source": "initial",
                "added_at": datetime.now().isoformat(),
            }

        # 初始策略知识（扩充版）
                "type": "quality",
                "content": "生成内容时应包含详细解释",
                "added_at": datetime.now().isoformat(),
                "quality_score": 1.0
            },
                "id": f"strategy_002_{self.agent_id}",
                "priority": "high",
                "source": "initial",
                "added_at": datetime.now().isoformat(),
            {
                "id": f"strategy_003_{self.agent_id}",
                "type": "creativity",
                "quality_score": 1.0
            },
            {
                "type": "difficulty",
                "content": "生成内容应考虑不同难度级别",
                "quality_score": 1.0
            {
                "id": f"strategy_005_{self.agent_id}",
                "type": "diversity",
                "content": "生成内容应具有多样性，避免重复",
                "quality_score": 1.0
            },
                "type": "clarity",
                "priority": "high",
                "added_at": datetime.now().isoformat(),
            }

        # 添加到知识库
        self.knowledge_base["reading"].extend(initial_reading)
    def _validate_knowledge(self, knowledge_item: Dict[str, Any], knowledge_type: str) -> bool:

            knowledge_item: 知识条目
            knowledge_type: 知识类型
        if knowledge_type not in self.knowledge_validation_rules:
            return False
        rules = self.knowledge_validation_rules[knowledge_type]
        # 检查必填字段
        for field in rules["required_fields"]:
                return False

        if len(str(knowledge_item.get(rules["required_fields"][0], ""))) < rules["min_length"]:
            return False

        for existing_item in self.knowledge_base[knowledge_type]:
                if existing_item["word"] == knowledge_item["word"]:
                    return False
            elif knowledge_type == "grammar":
                    return False
            elif knowledge_type == "reading":
            elif knowledge_type == "strategies":
                if existing_item["content"] == knowledge_item["content"]:
                    return False
        return True

        """添加经过验证的知识到知识库
            knowledge_item: 知识条目
            knowledge_type: 知识类型

        Returns:
            添加成功返回True
        # 添加元数据
        })

        # 验证内容
        if self._validate_knowledge(knowledge_item, knowledge_type):
            self.knowledge_base[knowledge_type].append(knowledge_item)
            logger.info(f"AI {self.agent_id} 添加新的{knowledge_type}知识: {knowledge_item.get('word', knowledge_item.get('rule', knowledge_item.get('topic', '新条目')))}")
            return True
        return False
        """从生成的内容中扩充知识库

        Args:
            knowledge_type: 知识类型

        Returns:
            扩充成功返回True
        try:
            if extracted_knowledge:
            logger.error(f"AI {self.agent_id} 扩充知识库失败: {str(e)}")

    def _extract_knowledge_from_content(self, content: Dict[str, Any], knowledge_type: str) -> Dict[str, Any]:
        """从内容中提取知识

        Args:
            content: 生成的内容
        Returns:
        if knowledge_type == "vocabulary":
            # 从词汇题中提取知识
            if "question" in content and "explanation" in content:
                # 简单提取示例，实际可更复杂
                question = content["question"]
                    word = question.split("'")[1]
                    return {
                        "part_of_speech": "unknown"
                    }

        elif knowledge_type == "grammar":
            if "question" in content and "explanation" in content:
                if "形式" in content["question"] or "语法" in content["question"]:
                    return {
                        "rule": content["question"].split("'")[1],
                        "explanation": content["explanation"]
                    }

            # 从阅读题中提取知识
                    "topic": content["topic"],
                }

        elif knowledge_type == "strategies":
            # 从建议中提取策略
                return {
                    "content": content["content"],

        return {}

    def generate_content(self, task_type: str, count: int = 5) -> List[Dict[str, Any]]:
        """生成内容（如题目）

            task_type: 任务类型（如：vocabulary, grammar, reading）

            生成的内容列表
        logger.info(f"AI {self.agent_id} 生成 {count} 个 {task_type} 内容")

        for i in range(count):

            if task_type == "vocabulary":
                content = self._generate_vocabulary_question()
            elif task_type == "grammar":
            elif task_type == "reading":
                content = self._generate_reading_question()
            else:
                content = self._generate_general_content()
            # 添加元数据
            content.update({
                "id": content_id,
                "agent_id": self.agent_id,
                "generated_at": datetime.now().isoformat(),
            })


        return generated_content

    def _generate_vocabulary_question(self) -> Dict[str, Any]:
        """生成词汇题，优先使用知识库内容，增加题型多样性"""
        # 优先从知识库中获取词汇
        if self.knowledge_base["vocabulary"]:
            vocab_item = random.choice(self.knowledge_base["vocabulary"])
            meaning = vocab_item["meaning"]

            # 随机选择题型
            question_types = [
                "meaning",  # 词义理解
                "usage",    # 用法选择
                "synonym",  # 同义词
                "antonym",  # 反义词
                "completion"# 填空
            question_type = random.choice(question_types)

            # 生成干扰选项（从知识库中选择其他词汇的意思）
            all_meanings = [item["meaning"] for item in self.knowledge_base["vocabulary"] if item["meaning"] != meaning]

            # 根据题型生成题目
            if question_type == "meaning":
                # 词义理解题
                # 生成选项
                options = [meaning] + random.sample(all_meanings, min(3, len(all_meanings)))
                if len(options) < 4:
                    options += [f"错误选项{i+1}" for i in range(4 - len(options))]
                random.shuffle(options)
                correct_answer = f"选项{chr(ord('A') + options.index(meaning))}"

            elif question_type == "usage":
                sentences = [
                    f"{word}是一个{part_of_speech}。",
                    f"我们可以这样使用{word}：...",
                    f"{word}的正确用法是？",
                    f"以下哪个句子中{word}的使用是正确的？"
                ]
                question = random.choice(sentences)

                options = [f"正确使用了{word}", f"错误使用了{word}（词性错误）", f"错误使用了{word}（语境错误）", f"错误使用了{word}（拼写错误）"]
                correct_answer = "选项A"

                # 同义词题
                if synonyms:
                    correct_synonym = synonyms[0]
                    question = f"'{word}'的同义词是？"

                    options = [correct_synonym] + random.sample([item["word"] for item in self.knowledge_base["vocabulary"] if item["word"] not in [word, correct_synonym]], min(3, len(self.knowledge_base["vocabulary"])-2))
                    if len(options) < 4:
                        options += [f"错误选项{i+1}" for i in range(4 - len(options))]
                    random.shuffle(options)
                    correct_answer = f"选项{chr(ord('A') + options.index(correct_synonym))}"
                else:
                    # 如果没有同义词，回退到词义理解题
                    question = f"'{word}'的正确意思是什么？"
                    options = [meaning] + random.sample(all_meanings, min(3, len(all_meanings)))
                    if len(options) < 4:
                        options += [f"错误选项{i+1}" for i in range(4 - len(options))]
                    random.shuffle(options)
                    correct_answer = f"选项{chr(ord('A') + options.index(meaning))}"

            elif question_type == "antonym":
                # 反义词题（简单示例，实际需要反义词库）
                options = ["反义词1", "反义词2", "反义词3", "没有合适的反义词"]

            else:  # completion
                # 填空题
                sentences = [
                    f"当我们见面时，我们会说'{word}'来______。",
                    f"'{word}'的意思是______。",
                    f"在日语中，'{word}'表示______。"
                ]
                question = random.choice(sentences)
                options = [meaning] + random.sample(all_meanings, min(3, len(all_meanings)))
                if len(options) < 4:
                    options += [f"错误选项{i+1}" for i in range(4 - len(options))]
                random.shuffle(options)
                correct_answer = f"选项{chr(ord('A') + options.index(meaning))}"

            return {
                "options": [f"选项{chr(ord('A') + i)}" for i in range(len(options))],
                "explanation": f"'{word}'的正确意思是{meaning}。",
                "difficulty": random.randint(1, 5),
                "source_knowledge_id": vocab_item["id"],
                "question_type": question_type
            }

        # 知识库为空时使用默认词汇
            "こんにちは", "ありがとう", "すみません", "いただきます", "ごちそうさま",
            "hello", "thank you", "sorry", "please", "goodbye"
        ]

        word = random.choice(vocabularies)

        return {
            "question": f"'{word}'的正确意思是什么？",
                "选项A", "选项B", "选项C", "选项D"
            ],
            "explanation": f"'{word}'的正确意思是选项A。",
            "difficulty": random.randint(1, 5),
            "question_type": "meaning"
        }

    def _generate_grammar_question(self) -> Dict[str, Any]:
        """生成语法题，优先使用知识库内容，增加题型多样性"""
        # 优先从知识库中获取语法规则
            grammar_item = random.choice(self.knowledge_base["grammar"])
            rule = grammar_item["rule"]
            example = grammar_item["example"]
            explanation = grammar_item["explanation"]

            # 提取例句的后半部分，用于生成选项
            example_part = example.split("は")[-1].strip("。")

            # 随机选择题型
            question_types = [
                "completion",  # 完成句子
                "usage",       # 用法判断
                "form",        # 形式转换
                "error",       # 错误识别
                "meaning"      # 意义理解
            ]
            question_type = random.choice(question_types)

            error_forms = [
                "错误形式（时态错误）",
                "错误形式（语态错误）",
                "错误形式（人称错误）",
                "错误形式（数错误）",
            ]

            # 根据题型生成题目
            if question_type == "completion":
                # 完成句子题
                question = f"选择正确的'{rule}'形式完成句子：{example.split('は')[0]}は______。"

                # 生成选项
                options = [example_part] + random.sample(error_forms, 3)
                correct_answer = f"选项{chr(ord('A') + options.index(example_part))}"

            elif question_type == "usage":
                # 用法判断题
                question = f"以下哪个句子正确使用了'{rule}'语法点？"

                # 生成选项
                options = [example, f"错误使用{rule}的句子1", f"错误使用{rule}的句子2", f"错误使用{rule}的句子3"]
                correct_answer = "选项A"

            elif question_type == "form":
                # 形式转换题
                question = f"将以下句子转换为'{rule}'形式：{example}"

                # 生成选项
                options = [example_part, f"错误转换1", f"错误转换2", f"错误转换3"]
                correct_answer = f"选项{chr(ord('A') + options.index(example_part))}"

            elif question_type == "error":
                # 错误识别题

                options = [f"错误使用{rule}的句子1", f"错误使用{rule}的句子2", f"错误使用{rule}的句子3", example]
                correct_answer = "选项D"

            else:  # meaning
                # 意义理解题
                question = f"句子'{example}'中'{rule}'的作用是什么？"

                # 生成选项
                options = [explanation, f"错误解释1", f"错误解释2", f"错误解释3"]
                correct_answer = f"选项{chr(ord('A') + options.index(explanation))}"

            return {
                "question": question,
                "options": [f"选项{chr(ord('A') + i)}" for i in range(len(options))],
                "correct_answer": correct_answer,
                "explanation": f"正确使用'{rule}'的形式是{example.split('は')[-1].strip('。')}，表示{explanation}。",
                "difficulty": random.randint(1, 5),
                "source_knowledge_id": grammar_item["id"],
                "question_type": question_type
            }

        # 知识库为空时使用默认语法点
        grammar_points = [
            "ています", "ます形", "て形", "ない形", "た形",
        ]

        grammar = random.choice(grammar_points)

        return {
            "question": f"选择正确的'{grammar}'形式完成句子：我每天{grammar}。",
            "options": [
                "选项A", "选项B", "选项C", "选项D"
            ],
            "explanation": f"正确使用'{grammar}'的形式是选项A。",
            "difficulty": random.randint(1, 5),
            "question_type": "completion"
        }

    def _generate_reading_question(self) -> Dict[str, Any]:
        """生成阅读题，优先使用知识库内容，增加题型多样性"""
        # 优先从知识库中获取阅读材料
        if self.knowledge_base["reading"]:
            topic = reading_item["topic"]

            # 随机选择题型
            question_types = [
                "main_idea",    # 主旨题
                "detail",       # 细节题
                "vocabulary",   # 词汇题
                "author_purpose"# 作者意图题
            ]
            question_type = random.choice(question_types)

            # 根据题型生成题目和选项
            if question_type == "main_idea":
                # 主旨题
                question = f"这篇文章的主旨是什么？"
                correct_option = f"本文主要介绍了{topic}的相关知识。"
                options = [correct_option, f"本文详细讨论了{topic}的一个具体方面", f"本文比较了{topic}与其他主题", f"本文批评了{topic}的某些观点"]
                # 细节题
                if keywords:
                    question = f"根据文章，{topic}包含哪些关键词？"
                    options = [correct_option, f"{', '.join(random.sample(keywords, min(2, len(keywords))))} （不完整）", f"错误关键词1, 错误关键词2", f"以上都不是"]
                else:
                    question = f"根据文章，关于{topic}的以下说法哪项正确？"
                    options = [correct_option, f"{topic}在文章中被批评", f"{topic}只在文章结尾被提到", f"以上都不正确"]

                # 推断题
                question = f"从文章中可以推断出什么？"
                correct_option = f"作者对{topic}有一定的了解"

            elif question_type == "vocabulary":
                # 词汇题
                # 简单提取文章中的关键词
                passage_words = content.split()
                    vocab_word = random.choice(passage_words[:5])
                    question = f"文章中'{vocab_word}'一词的意思最接近？"
                    correct_option = f"与{vocab_word}相关的意思"
                else:
                    question = f"文章中提到的'{topic}'指的是？"
                    correct_option = f"{topic}的正确含义"
                    options = [correct_option, f"错误含义1", f"错误含义2", f"以上都不是"]

                # 作者意图题
                question = f"作者写这篇文章的主要目的是什么？"
                correct_option = f"向读者介绍{topic}的相关知识"
                options = [correct_option, f"说服读者接受某种观点", f"娱乐读者", f"抱怨{topic}的问题"]
            # 打乱选项顺序
            random.shuffle(options)
            correct_answer = f"选项{chr(ord('A') + options.index(correct_option))}"

            return {
                "passage": content,
                "question": question,
                "options": [f"选项{chr(ord('A') + i)}" for i in range(len(options))],
                "correct_answer": correct_answer,
                "explanation": f"根据阅读材料，正确答案是{correct_option}。",
                "difficulty": random.randint(1, 5),
                "source_knowledge_id": reading_item["id"],
                "question_type": question_type
            }

        # 知识库为空时使用默认主题
        topics = [
            "日本文化", "英语学习", "人工智能", "环境保护", "科技发展"
        ]

        topic = random.choice(topics)
        passage = f"这是一段关于{topic}的阅读材料。内容丰富，包含了许多相关信息。{topic}是一个重要的主题，吸引了许多人的关注。本文将介绍{topic}的基本概念、发展历程和未来趋势。通过阅读本文，读者可以对{topic}有一个全面的了解。"

        # 生成简单的问题
        question = f"这篇文章的主要主题是什么？"
        options = [f"{topic}", "其他主题", "无关主题", "以上都不是"]
        correct_answer = "选项A"
        return {
            "question": question,
            "options": [f"选项{chr(ord('A') + i)}" for i in range(len(options))],
            "correct_answer": correct_answer,
            "explanation": f"根据阅读材料，正确答案是{topic}。",
            "difficulty": random.randint(1, 5),
            "question_type": "main_idea"
        }

    def _generate_general_content(self) -> Dict[str, Any]:
        """生成通用内容"""
        return {
            "title": f"AI生成的通用内容 {self.agent_id}",
            "tags": ["AI", "生成内容", self.specialization]
        }

    def evaluate_content(self, content: Dict[str, Any]) -> float:
        """评估其他AI生成的内容

        Args:
            content: 要评估的内容

        Returns:
            评估分数（0-100）
        # 简单的评估算法，实际可以更复杂
        quality_score = random.uniform(70, 95)  # 质量分数
        relevance_score = random.uniform(75, 90)  # 相关性分数
        creativity_score = random.uniform(60, 85)  # 创新性分数
        difficulty_score = random.uniform(50, 80)  # 难度分数

        # 加权平均
        total_score = (
            quality_score * self.evaluation_criteria["quality"] +
            relevance_score * self.evaluation_criteria["relevance"] +
            creativity_score * self.evaluation_criteria["creativity"] +
        )

        return round(total_score, 2)

    def learn_from_feedback(self, feedback: Dict[str, Any]) -> bool:

        Args:

        Returns:
            学习成功返回True
        logger.info(f"AI {self.agent_id} 从反馈中学习")

        # 记录学习历史
        learning_record = {
            "feedback": feedback,
            "learned_at": datetime.now().isoformat(),
            "experience_gained": random.randint(5, 20)
        }

        self.learning_history.append(learning_record)
        self.experience_points += learning_record["experience_gained"]

        # 更新知识质量分数
        if "evaluations" in feedback:
            for eval_item in feedback["evaluations"]:
                content = eval_item["content"]
                if "source_knowledge_id" in content:
                    knowledge_id = content["source_knowledge_id"]
                    for knowledge_type, items in self.knowledge_base.items():
                            if item["id"] == knowledge_id:
                                # 根据评估分数调整质量分数
                                avg_score = eval_item["evaluation"]["average_score"]
                                item["quality_score"] = max(0.1, min(1.0, avg_score / 100))
                                logger.info(f"AI {self.agent_id} 更新知识库条目{knowledge_id}的质量分数为: {item['quality_score']}")

        # 更新知识
        if "suggestions" in feedback:
            for suggestion in feedback["suggestions"]:
                # 根据建议更新知识
                    knowledge_type = suggestion["knowledge_type"]
                    content = suggestion["content"]
                    # 只有当content是字典时才添加到知识库，防止类型错误
                        self._add_validated_knowledge(content, knowledge_type)
                        # 对于字符串类型的建议，转换为合适的字典格式
                            "priority": suggestion.get("priority", "medium")
                        }

        self._check_upgrade_needed()


    def _check_upgrade_needed(self):
        logger.info(f"AI {self.agent_id} 检查升级需求")

        total_quality = 0
        total_items = 0
        for items in self.knowledge_base.values():
            for item in items:
                total_quality += item.get("quality_score", 0.5)
                total_items += 1


        knowledge_types = len(self.knowledge_base)
        diversity_score = 0.0
            type_counts = {k: len(v) for k, v in self.knowledge_base.items()}
            total_knowledge = sum(type_counts.values())
                # 使用香农熵计算多样性
                entropy = 0.0
                    p = count / total_knowledge

        # 计算学习效率（最近5次学习的平均经验获取）
            recent_learning = self.learning_history[-5:]  # 最近5次学习
            total_exp = sum(record.get("experience_gained", 0) for record in recent_learning)
            learning_efficiency = total_exp / len(recent_learning)

        # 综合升级评分（0-100）
        upgrade_score = (
            (self.experience_points / 200) * 30 +  # 经验值贡献（30%权重）
            avg_quality * 30 +  # 知识库质量贡献（30%权重）
            diversity_score * 20 +  # 知识库多样性贡献（20%权重）
            min(learning_efficiency / 20, 1.0) * 20  # 学习效率贡献（20%权重）
        )

        logger.info(f"AI {self.agent_id} 升级评分: {upgrade_score:.2f}")
        logger.info(f"  经验值: {self.experience_points}, 知识库质量: {avg_quality:.2f}")
        logger.info(f"  知识库多样性: {diversity_score:.2f}, 学习效率: {learning_efficiency:.2f}")

        if upgrade_score > 70 and avg_quality > 0.6 and self.experience_points > 80:
            self._upgrade_model()
            return True

        return False

    def _upgrade_model(self):
        """智能升级模型版本，实现模型优化和知识库增强"""
        logger.info(f"AI {self.agent_id} 开始模型升级")

        # 智能版本升级逻辑：根据升级类型确定版本号变化
        version_parts = list(map(int, self.model_version.split('.')))
        # 基于升级评分确定升级类型
        total_quality = 0
        for items in self.knowledge_base.values():
            for item in items:
                total_quality += item.get("quality_score", 0.5)
                total_items += 1
        avg_quality = total_quality / total_items if total_items > 0 else 0.5
        if avg_quality > 0.8 and self.experience_points > 150:
            # 大版本升级：知识库质量高且经验丰富
            version_parts[0] += 1
            version_parts[1] = 0
            version_parts[2] = 0
            upgrade_type = "major"
        elif avg_quality > 0.7:
            # 中版本升级：知识库质量较好
            version_parts[1] += 1
            version_parts[2] = 0
            upgrade_type = "minor"
            # 小版本升级：常规升级
            version_parts[2] += 1
            upgrade_type = "patch"

        self.model_version = '.'.join(map(str, version_parts))

        self._optimize_knowledge_base()

        # 升级模型参数
        self._update_model_parameters()

        # 生成升级报告
        upgrade_report = {
            "upgrade_type": upgrade_type,
            "new_version": self.model_version,
            "upgrade_reason": f"综合评分超过阈值，触发{upgrade_type}升级",
            "knowledge_base_stats": {
                "total_items": total_items,
                "experience_points": self.experience_points
            },
                "low_quality_cleaned": self._clean_low_quality_knowledge(),
                "redundant_removed": self._remove_redundant_knowledge(),
                "knowledge_organized": self._organize_knowledge()
            }
        }

        logger.info(f"AI {self.agent_id} 成功升级到版本 {self.model_version}（{upgrade_type}升级）")

        # 重置经验值，保留一部分作为基础经验
        self.experience_points = max(50, int(self.experience_points * 0.2))

        return upgrade_report

        """智能优化知识库，包括清理、组织和增强"""

        # 执行多维度知识库优化
        self._clean_low_quality_knowledge()
        self._remove_redundant_knowledge()
        self._organize_knowledge()
        self._enhance_knowledge_connections()

        """智能清理低质量知识库内容，防止污染"""
        cleaned_count = 0
        for knowledge_type in self.knowledge_base:
            initial_count = len(self.knowledge_base[knowledge_type])

            # 智能清理规则：
            # 1. 保留初始知识（source="initial"）
            # 2. 保留高质量知识（quality_score > 0.4）
            now = datetime.datetime.now()

            self.knowledge_base[knowledge_type] = [
                item for item in self.knowledge_base[knowledge_type]
                if item.get("source") == "initial" or
                   item.get("quality_score", 0.5) > 0.4 or
                   ("added_at" in item and
                    (now - datetime.datetime.fromisoformat(item["added_at"])).days < 7)
            ]

            type_cleaned = initial_count - len(self.knowledge_base[knowledge_type])

                logger.info(f"AI {self.agent_id} 清理了{type_cleaned}个低质量{knowledge_type}知识条目")

    def _remove_redundant_knowledge(self):
        for knowledge_type in self.knowledge_base:
            seen_content = set()
            unique_knowledge = []
            for item in self.knowledge_base[knowledge_type]:
                # 基于知识内容生成唯一标识符
                if knowledge_type == "vocabulary":
                    content_key = (item.get("word", ""), item.get("meaning", ""))
                elif knowledge_type == "grammar":
                elif knowledge_type == "reading":
                    content_key = (item.get("topic", ""), hash(item.get("content", "")[:100]))
                elif knowledge_type == "strategies":
                    content_key = (item.get("type", ""), item.get("content", ""))
                else:
                    content_key = str(item)

                if content_key not in seen_content:
                    unique_knowledge.append(item)
            type_removed = initial_count - len(unique_knowledge)

                logger.info(f"AI {self.agent_id} 移除了{type_removed}个冗余{knowledge_type}知识条目")

        return removed_count

    def _organize_knowledge(self):
        """组织知识，提高知识检索效率"""
        logger.info(f"AI {self.agent_id} 组织知识库")

        organized_count = 0

        for knowledge_type in self.knowledge_base:
            # 按质量分数和添加时间排序
            self.knowledge_base[knowledge_type].sort(
                key=lambda x: (-x.get("quality_score", 0.5), x.get("added_at", ""))
            )

            # 添加索引信息
            for i, item in enumerate(self.knowledge_base[knowledge_type]):
                if "index" not in item or item["index"] != i:
                    item["index"] = i
                    organized_count += 1
        return organized_count

    def _enhance_knowledge_connections(self):
        """增强知识之间的连接，提高知识利用效率"""
        logger.info(f"AI {self.agent_id} 增强知识连接")

        # 简单的知识连接示例：为词汇添加相关语法知识引用
        # 实际实现可以更复杂，基于语义相似性等
        enhanced_count = 0

        for vocab_item in self.knowledge_base["vocabulary"]:
            # 查找相关的语法知识
            related_grammar = []
            for grammar_item in self.knowledge_base["grammar"]:
                if vocab_item.get("word", "") in grammar_item.get("example", ""):
                    related_grammar.append(grammar_item["id"])

            if related_grammar:
                vocab_item["related_grammar"] = related_grammar
                enhanced_count += 1

        return enhanced_count

        """更新模型参数，优化学习能力"""
        logger.info(f"AI {self.agent_id} 更新模型参数")

        # 基于知识库状态调整学习率
        total_knowledge = sum(len(v) for v in self.knowledge_base.values())
        # 知识库越大，学习率越低，避免过度调整
        new_learning_rate = max(0.01, min(0.3, 0.1 * (1000 / (total_knowledge + 100))))

        if abs(new_learning_rate - self.learning_rate) > 0.01:
            self.learning_rate = new_learning_rate

        # 调整评估标准权重，基于最近的学习效果
        if len(self.learning_history) > 10:
            # 简单示例：根据最近学习效果调整权重
            recent_feedback = [record["feedback"] for record in self.learning_history[-10:]]
            # 实际实现可以更复杂，基于反馈分析调整权重

    def _log_upgrade(self, upgrade_report: Dict[str, Any]):
        """记录升级历史"""
        # 简单的升级日志记录，实际可以保存到文件或数据库

    def share_knowledge(self, knowledge_type: str = None) -> Dict[str, Any]:

        Args:

        Returns:
            要分享的知识
            knowledge = {
                knowledge_type: self.knowledge_base.get(knowledge_type, [])
            }
        else:
            knowledge = self.knowledge_base.copy()
        return {
            "agent_id": self.agent_id,
            "knowledge": knowledge
        }

    def receive_knowledge(self, shared_knowledge: Dict[str, Any]) -> bool:
        """接收其他AI分享的知识
        Args:
            shared_knowledge: 其他AI分享的知识

        logger.info(f"AI {self.agent_id} 接收来自 {shared_knowledge['agent_id']} 的知识")

        # 合并知识
            if knowledge_type not in self.knowledge_base:
                self.knowledge_base[knowledge_type] = []

            # 去重合并
            for item in self.knowledge_base[knowledge_type]:
                if isinstance(item, dict):
                    existing_ids.add(item.get("id", str(item)))
                else:
                    existing_ids.add(str(item))

            for content in content_list:
                if isinstance(content, dict):
                    content_id = content.get("id", str(content))
                    content_id = str(content)

                    self.knowledge_base[knowledge_type].append(content)
                    existing_ids.add(content_id)

        return True

        """获取性能指标

        Returns:
            性能指标
        return {
            "agent_id": self.agent_id,
            "model_version": self.model_version,
            "experience_points": self.experience_points,
            "learning_history_count": len(self.learning_history),
            "knowledge_base_size": {
                k: len(v) for k, v in self.knowledge_base.items()
            },
            "specialization": self.specialization
        }


class MultiAILearningSystem:
    """多AI相互学习系统"""

    def __init__(self, num_agents: int = 3):
        """初始化多AI学习系统

        Args:
            num_agents: AI代理数量
        self.agents = []
        self.iteration_count = 0
        self.creation_time = datetime.now()

        # AI专业领域
        specializations = ["vocabulary", "grammar", "reading", "general"]

        # 创建多个AI代理
        for i in range(num_agents):
            agent_id = f"ai_{i+1}"
            specialization = specializations[i % len(specializations)]
            agent = AILearningAgent(agent_id, specialization)
            self.agents.append(agent)

        logger.info(f"初始化多AI学习系统，包含 {num_agents} 个AI代理")

    def run_iteration(self, task_type: str = "vocabulary", content_count: int = 5) -> Dict[str, Any]:
        """运行一次学习迭代

        Args:
            task_type: 任务类型
            content_count: 每个AI生成的内容数量

        Returns:
            迭代结果
        self.iteration_count += 1

        iteration_result = {
            "started_at": datetime.now().isoformat(),
            "task_type": task_type,
            "content_count": content_count,
            "results": []
        }

        # 1. 所有AI生成内容
        all_generated_content = []
            generated_content = agent.generate_content(task_type, content_count)
            all_generated_content.extend(generated_content)

        # 1.5 从生成的内容中扩充知识库
        for agent in self.agents:
            expanded_count = 0
            for content in all_generated_content:
                # 只有内容创建者可以扩充自己的知识库
                    if agent.expand_knowledge_base(content, task_type):
                        expanded_count += 1
            knowledge_expansion_results.append({
                "agent_id": agent.agent_id,
                "expanded_count": expanded_count

        # 2. 所有AI评估其他AI的内容
        evaluations = []
        for evaluator in self.agents:
            for content in all_generated_content:
                # 不评估自己生成的内容
                if content["agent_id"] != evaluator.agent_id:
                    score = evaluator.evaluate_content(content)
                        "evaluator_id": evaluator.agent_id,
                        "content_id": content["id"],
                        "content_agent_id": content["agent_id"],
                        "score": score,
                        "evaluated_at": datetime.now().isoformat()
                    }
                    evaluations.append(evaluation)

        # 3. 汇总评估结果，生成反馈
        content_evaluations = {}
        for evaluation in evaluations:
            content_id = evaluation["content_id"]
            if content_id not in content_evaluations:
                content_evaluations[content_id] = {
                    "average_score": 0
                }
            content_evaluations[content_id]["evaluations"].append(evaluation)

        # 计算平均分数
            scores = [eval["score"] for eval in eval_data["evaluations"]]
            eval_data["average_score"] = round(sum(scores) / len(scores), 2)

        # 4. 生成反馈并发送给各个AI
        agent_feedback = {}
        for content in all_generated_content:
            content_id = content["id"]
            agent_id = content["agent_id"]

            if agent_id not in agent_feedback:
                agent_feedback[agent_id] = {
                    "agent_id": agent_id,
                    "suggestions": []
                }

            if content_id in content_evaluations:
                agent_feedback[agent_id]["evaluations"].append({
                    "content": content,
                    "evaluation": content_evaluations[content_id]
                })

                # 生成改进建议
                suggestions = self._generate_suggestions(content, content_evaluations[content_id])
                agent_feedback[agent_id]["suggestions"].extend(suggestions)

        # 5. AI从反馈中学习
        learning_results = []
            if agent.agent_id in agent_feedback:
                feedback = agent_feedback[agent.agent_id]
                success = agent.learn_from_feedback(feedback)
                learning_results.append({
                    "agent_id": agent.agent_id,
                    "success": success,
                    "feedback_received": True
                })
            else:
                learning_results.append({
                    "success": True,
                    "feedback_received": False
                })

        # 6. AI之间分享知识
        knowledge_sharing_results = []
        for agent in self.agents:
            # 分享知识
            shared_knowledge = agent.share_knowledge()

            # 其他AI接收知识
            for receiver in self.agents:
                if receiver.agent_id != agent.agent_id:
                    success = receiver.receive_knowledge(shared_knowledge)
                    knowledge_sharing_results.append({
                        "sender_id": agent.agent_id,
                        "receiver_id": receiver.agent_id,
                        "success": success

        # 7. 收集所有AI的性能指标
        # 完成迭代
            "generated_content_count": len(all_generated_content),
            "learning_results": learning_results,
            "knowledge_expansion_results": knowledge_expansion_results,
            "performance_metrics": performance_metrics

        return iteration_result

    def _generate_suggestions(self, content: Dict[str, Any], evaluation: Dict[str, Any]) -> List[Dict[str, Any]]:
        """生成改进建议

        Args:
            content: 被评估的内容
            evaluation: 评估结果

        Returns:
            建议列表

        # 根据评估分数生成建议
        if evaluation["average_score"] < 70:
            suggestions.append({
                "knowledge_type": "strategies",
                "content": "提高内容质量的建议: 增加详细的解释和示例",
                "priority": "high"
            })

        if "difficulty" in content and content["difficulty"] < 3:
            suggestions.append({
                "content": "增加难度的建议: 使用更复杂的结构和词汇",
                "priority": "medium"
            })
        suggestions.append({
            "knowledge_type": "general",
            "content": "持续改进建议: 尝试不同的内容结构和表达方式",
        })

        return suggestions
        """运行多次迭代

        Args:
            iterations: 迭代次数
            task_type: 任务类型
            content_count: 每个AI生成的内容数量

        Returns:
            所有迭代结果
        logger.info(f"开始运行 {iterations} 次学习迭代")

        all_results = []
        for i in range(iterations):
            iteration_result = self.run_iteration(task_type, content_count)
            all_results.append(iteration_result)

            # 迭代之间休息一下
            time.sleep(1)

        return all_results

    def save_results(self, results: List[Dict[str, Any]], filename: str = None):
        """保存学习结果到数据库

        Args:
            results: 学习结果
            filename: 已废弃参数，保留用于兼容性
        try:
            logger.info(f"开始将学习结果保存到数据库")

            # 导入必要的模块
            import sqlite3
            # JSON import removed - using database

            # 数据库路径
            db_path = os.path.join(os.path.dirname(__file__), 'flask-app', 'app.db')

            # 连接数据库
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # 遍历所有结果
            for iteration, result in enumerate(results, 1):
                # 计算平均分数
                content_evaluations = {}
                for item in result.get("results", []):
                    if "content_evaluations" in item:
                        content_evaluations.update(item["content_evaluations"])

                avg_scores = []
                    avg_scores.append(eval_data["average_score"])

                avg_score = sum(avg_scores) / len(avg_scores) if avg_scores else 0

                # 保存结果到主表
                INSERT INTO ai_learning_results (iteration, results, average_score)
                VALUES (?, ?, ?)
                ''', (
                    iteration,
                    str(result),
                    avg_score
                ))

                result_id = cursor.lastrowid

                # 保存内容到详情表
                for item in result.get("results", []):
                        for content in item["generated_content"]:
                            content_type = content.get("type", "general")
                            question = content.get("question", "")
                            options = str(content.get("options", []))
                            correct_answer = content.get("correct_answer", "")
                            explanation = content.get("explanation", "")
                            difficulty = content.get("difficulty", 1)
                            generated_by = content.get("agent_id", "system")
                            source = content.get("source", "ai_generated")

                            # 获取该内容的平均分数
                            content_score = 0
                            if content_id in content_evaluations:
                                content_score = content_evaluations[content_id]["average_score"]

                            # 插入内容
                            cursor.execute('''
                            INSERT INTO ai_learning_content (
                                result_id, content_id, content_type, question, options,
                                correct_answer, explanation, difficulty, generated_by,
                                source, average_score
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            ''', (
                                result_id,
                                content_id,
                                content_type,
                                question,
                                options,
                                correct_answer,
                                difficulty,
                                generated_by,
                                source,
                                content_score
                            ))

            conn.close()

            logger.info("学习结果已保存到数据库")
        except Exception as e:
            logger.error(f"保存学习结果到数据库失败: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            # 确保数据库连接已关闭
            if 'conn' in locals():
                conn.close()

        """打印学习结果摘要

        Args:
            results: 学习结果
        print("\n=== 多AI学习系统摘要 ===")
        print(f"总迭代次数: {len(results)}")
        print(f"参与AI数量: {len(self.agents)}")

        # 计算平均分数趋势
        iteration_scores = []
        for result in results:
            # 从结果中提取评估数据
            content_evaluations = {}
            # 获取所有评估
            for item in result.get("results", []):
                    content_evaluations.update(item["content_evaluations"])

            avg_scores = []
            for content_id, eval_data in content_evaluations.items():
                avg_scores.append(eval_data["average_score"])
            if avg_scores:
                iteration_scores.append({
                    "iteration": result["iteration"],
                    "average_score": round(sum(avg_scores) / len(avg_scores), 2)
                })
            else:
                # 从原始数据中计算平均分数
                all_generated_content = []
                for agent in self.agents:
                    # 模拟获取生成内容的评估分数
                    # 实际应该从结果中获取
                    pass
        print("\n各迭代平均分数:")
        for score_data in iteration_scores:
        # 打印最终性能指标
        print("\n最终AI性能指标:")
        for agent in self.agents:
            metrics = agent.get_performance_metrics()
            print(f"  AI {metrics['agent_id']} ({metrics['specialization']}):")
            print(f"    模型版本: {metrics['model_version']}")
            print(f"    经验值: {metrics['experience_points']}")
            print(f"    学习历史: {metrics['learning_history_count']}")
            # 知识量是各知识库条目的总和，而knowledge_base_size已经是长度值
            print(f"    知识量: {sum(v for v in metrics['knowledge_base_size'].values())}")

        print("\n=== 学习完成 ===")

        """批量生成内容

        Args:
            task_type: 任务类型
            total_count: 生成的总数量

        Returns:
            生成的内容列表
        logger.info(f"开始批量生成{total_count}个{task_type}内容")

        generated_content = []

        # 计算每个AI需要生成的数量
        per_agent_count = (total_count + len(self.agents) - 1) // len(self.agents)

        # 生成内容
        for agent in self.agents:
            agent_content = agent.generate_content(task_type, per_agent_count)
            generated_content.extend(agent_content)

            # 如果已经生成了足够的内容，就停止
            if len(generated_content) >= total_count:
                break

        # 只返回请求数量的内容
        generated_content = generated_content[:total_count]

        logger.info(f"批量生成完成，共生成{len(generated_content)}个内容")
        return generated_content

    def export_content(self, content: List[Dict[str, Any]], output_file: str = None, format: str = None) -> bool:
        """将内容上传到数据库

        Args:
            content: 要上传的内容列表
            output_file: 已废弃参数，保留用于兼容性
            format: 已废弃参数，保留用于兼容性
        Returns:
            上传成功返回True
        try:
            logger.info(f"开始将{len(content)}个内容上传到数据库")
            # 直接使用sqlite3连接数据库，不依赖Flask应用
            import sqlite3
            # JSON import removed - using database

            # 数据库路径
            db_path = os.path.join(os.path.dirname(__file__), 'flask-app', 'app.db')

            # 连接数据库
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # 分类映射
            category_mapping = {
                "vocabulary": "词汇",
                "grammar": "语法",
                "reading": "阅读",
                "general": "通用"
            }

            # 题目类型映射
            question_type_mapping = {
                "meaning": "single_choice",
                "usage": "single_choice",
                "antonym": "single_choice",
                "completion": "fill_blank",
                "detail": "single_choice",
                "inference": "single_choice",
                "vocabulary": "single_choice",
                "author_purpose": "single_choice",
                "form": "single_choice",
                "error": "single_choice",
                "true_false": "true_false",
                "short_answer": "short_answer"
            }

            # 批量上传到数据库
            for item in content:
                # 提取题目信息
                task_type = item.get("type", "general")
                question = item.get("question", "")

                # 处理阅读题的特殊情况
                if "passage" in item:
                    content_text = f"{item['passage']}\n\n{question}"
                else:
                    content_text = question

                answer = item.get("correct_answer", "")
                explanation = item.get("explanation", "")
                difficulty = item.get("difficulty", 1)
                question_type = item.get("question_type", "single_choice")

                # 处理选项
                options = item.get("options", [])
                options_json = str(options)

                # 转换题目类型
                db_question_type = question_type_mapping.get(question_type, "single_choice")

                # 获取或创建分类
                category_name = category_mapping.get(task_type, "通用")
                cursor.execute('SELECT id FROM question_categories WHERE name = ?', (category_name,))
                category_row = cursor.fetchone()

                if not category_row:
                    now = datetime.now(UTC).isoformat()
                    cursor.execute('''
                    INSERT INTO question_categories (name, description, created_at, updated_at) VALUES
                    (?, ?, ?, ?)
                    ''', (category_name, f"{category_name}相关题目", now, now))
                    category_id = cursor.lastrowid
                else:
                    category_id = category_row[0]
                # 默认使用第一个语种（日语）
                cursor.execute('SELECT id FROM question_languages WHERE id = ?', (1,))
                language_row = cursor.fetchone()
                language_id = language_row[0] if language_row else 1

                # 获取或创建等级
                cursor.execute('SELECT id FROM question_levels WHERE level = ?', (difficulty,))
                level_row = cursor.fetchone()

                if not level_row:
                    now = datetime.now(UTC).isoformat()
                    level_name = f"{difficulty}级"
                    cursor.execute('''
                    INSERT INTO question_levels (name, level, description, created_at, updated_at) VALUES
                    (?, ?, ?, ?, ?)
                    ''', (level_name, difficulty, f"{difficulty}级难度题目", now, now))
                    level_id = cursor.lastrowid
                    level_id = level_row[0]

                # 创建题目
                now = datetime.now(UTC).isoformat()
                cursor.execute('''
                INSERT INTO questions (content, correct_answer, explanation, category, language, level, question_type, options, created_at, source) VALUES
                (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (content_text, answer, explanation, category_name, "日语", difficulty, db_question_type, options_json, now, "ai_generated"))
            # 提交事务
            conn.commit()
            conn.close()

            logger.info(f"成功将{len(content)}个内容上传到数据库")
            return True
        except Exception as e:
            logger.error(f"上传内容到数据库失败: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            if 'conn' in locals():
                conn.close()
            return False


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='多AI相互学习与自我升级迭代系统')
    parser.add_argument('--agents', type=int, default=3, help='AI代理数量')
    parser.add_argument('--iterations', type=int, default=5, help='迭代次数')
    parser.add_argument('--content-count', type=int, default=3, help='每个AI生成的内容数量')
    parser.add_argument('--task', type=str, default='vocabulary', choices=['vocabulary', 'grammar', 'reading', 'general'], help='任务类型')
    parser.add_argument('--output', type=str, default='ai_learning_results.json', help='结果输出文件')

    # 添加批量生成功能的命令行参数
    parser.add_argument('--batch-generate', type=int, default=0, help='批量生成内容数量，0表示不使用批量生成模式')


    # 初始化多AI学习系统

    # 批量生成模式
    if args.batch_generate > 0:
        print(f"\n=== 批量生成模式 ===")
        print(f"生成任务类型: {args.task}")
        print(f"生成总数量: {args.batch_generate}")

        # 批量生成内容
        generated_content = multi_ai_system.batch_generate_content(
            total_count=args.batch_generate

        # 上传内容到数据库
        if multi_ai_system.export_content(generated_content):
            print(f"\n批量生成完成!")
            print(f"生成内容数量: {len(generated_content)}")
            print(f"内容已成功上传到数据库")

            print(f"\n内容统计:")
            # 按题型统计
            type_count = {}
            for item in generated_content:
                q_type = item.get("question_type", "unknown")
                type_count[q_type] = type_count.get(q_type, 0) + 1

            for q_type, count in type_count.items():
                print(f"  {q_type}: {count} 个")
        else:
            print("\n批量生成失败!")
    else:
        # 常规学习迭代模式
        # 运行多次迭代
        results = multi_ai_system.run_multiple_iterations(
            iterations=args.iterations,
            task_type=args.task,
            content_count=args.content_count
        )

        multi_ai_system.save_results(results, args.output)

        # 打印摘要
        multi_ai_system.print_summary(results)


if __name__ == "__main__":
    main()
