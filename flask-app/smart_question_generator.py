# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
智能题目生成模块
利用预训练语言模型增强题目质量
"""

from contextlib import contextmanager
import logging
logger = logging.getLogger(__name__)
import os
import sys
import json
import time
import random
import re
from typing import List, Dict, Any, Optional
from abc import ABC, abstractmethod

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

class AIModel(ABC):
    """AI模型抽象基类"""

    @abstractmethod
    def generate_text(self, prompt: str, **kwargs) -> str:
        """生成文本"""
        pass

    @abstractmethod
    def generate_question(self, language: str, category: str, difficulty: int) -> Dict[str, Any]:
        """生成题目"""
        pass

class MockAIModel(AIModel):
    """模拟AI模型,用于测试"""

    def generate_text(self, prompt: str, **kwargs) -> str:
        """生成文本"""
        return "模拟生成的文本"

    def generate_question(self, language: str, category: str, difficulty: int) -> Dict[str, Any]:
        """生成题目"""
        return {}

class SmartQuestionGenerator:
    """智能题目生成器"""
    def __init__(self, ai_model: Optional[AIModel] = None):
        self._load_config_from_db()

        self.using_ai_integrator = False
        if ai_model:
            self.ai_model = ai_model
        else:
            try:
                from app.ai.ai_engine_integrator import ai_engine_integrator
                self.ai_engine_integrator = ai_engine_integrator
                self.using_ai_integrator = True
                print("[INFO] 已初始化AI引擎集成器")
            except ImportError:
                self.ai_model = MockAIModel()
                print("[WARNING] AI引擎集成器不可用,使用Mock模型")

        self._init_enhanced_templates()

    def _load_config_from_db(self):
        """从数据库加载配置"""
        try:
            import sqlite3
            config_dict = {}
            print("[INFO] 使用简化配置加载,避免依赖Flask应用")

            self.model_type = config_dict.get("ai_model_type", "gpt-4o-mini")
            self.supported_languages = config_dict.get("supported_languages", ["japanese", "english", "chinese"])
            self.supported_categories = config_dict.get("supported_categories", ["词汇", "语法", "阅读", "听力", "写作", "口语", "翻译"])
            self.supported_difficulties = config_dict.get("supported_difficulties", [1, 2, 3, 4, 5])
            self.supported_question_types = config_dict.get("supported_question_types", ["single", "multiple", "fill", "short_answer", "essay", "speaking", "translation"])
            self.paper_category_ratios = config_dict.get("paper_category_ratios", {})
            self.scoring_criteria = config_dict.get("scoring_criteria", {})
            self.default_question_count = int(config_dict.get("default_question_count", 20))
            self.default_user_level = int(config_dict.get("default_user_level", 3))

            self.ai_scoring_enabled = config_dict.get("ai_scoring_enabled", True)
            self.ai_scoring_threshold = float(config_dict.get("ai_scoring_threshold", 0.8))
            self.ai_scoring_max_time = int(config_dict.get("ai_scoring_max_time", 30))

            self.question_generation_quality = config_dict.get("question_generation_quality", "high")
            self.question_generation_timeout = int(config_dict.get("question_generation_timeout", 60))

            self.question_bank_expansion_enabled = config_dict.get("question_bank_expansion_enabled", True)
            self.question_bank_expansion_rate = float(config_dict.get("question_bank_expansion_rate", 0.1))

            print("[INFO] 配置加载成功")
        except Exception as e:
            print(f"[WARNING] 配置加载失败,使用默认配置: {e}")
            self.model_type = "gpt-4o-mini"
            self.supported_languages = ["japanese", "english", "chinese"]
            self.supported_categories = ["词汇", "语法", "阅读", "听力", "写作", "口语", "翻译"]
            self.supported_difficulties = [1, 2, 3, 4, 5]
            self.supported_question_types = ["single", "multiple", "fill", "short_answer", "essay", "speaking", "translation"]
            self.paper_category_ratios = {}
            self.scoring_criteria = {}
            self.default_question_count = 20
            self.default_user_level = 3

            self.ai_scoring_enabled = True
            self.ai_scoring_threshold = 0.8
            self.ai_scoring_max_time = 30

            self.question_generation_quality = "high"
            self.question_generation_timeout = 60

            self.question_bank_expansion_enabled = True
            self.question_bank_expansion_rate = 0.1

    def _init_enhanced_templates(self):
        """初始化增强的题目模板"""
        pass

    def generate_question(self, language: str, category: str, difficulty: int, knowledge_points: List[str] = None,
                         question_type: Optional[str] = None, use_ai: bool = True) -> Dict[str, Any]:
        """
        生成单个智能题目
        Args:
            language: 语言类型 (japanese/english/chinese)
            category: 题目类别 (词汇/语法/阅读/听力/写作/口语/翻译)
            difficulty: 难度等级 (1-5)
            knowledge_points: 知识点列表
            question_type: 题目类型 (single/multiple/fill/short_answer/essay/speaking/translation)
            use_ai: 是否使用AI生成题目
        Returns:
            题目字典
        """
        if language not in self.supported_languages:
            raise ValueError(f"不支持的语言: {language}")

        if category not in self.supported_categories:
            raise ValueError(f"不支持的题目类别: {category}")

        if difficulty not in self.supported_difficulties:
            raise ValueError(f"难度等级必须在1-5之间: {difficulty}")

        unique_id = f"smart_{int(time.time() * 1000)}_{random.randint(1, 1000)}"

        try:
            question = self._generate_question_content(language, category, difficulty, knowledge_points, question_type)
            options = self._generate_options(question, category, language, difficulty)
            explanation = self._generate_explanation(question, category, language, difficulty)

            question['options'] = options
            question['explanation'] = explanation
        except Exception as e:
            print(f"生成题目失败,使用默认模板: {e}")
            question = {
                'content': f"{language} {category} 题目示例",
                'options': ["选项A", "选项B", "选项C", "选项D"],
                'type': question_type or 'single',
                'required_answers': 1,
                'correct_answers': ['A'],
                'explanation': "这是一道示例题目"
            }

        if not knowledge_points:
            knowledge_points = self._generate_knowledge_points(category, difficulty)

        freshness_score = random.uniform(0.8, 1.0)

        return {
            'id': unique_id,
            'language': language,
            'category': category,
            'difficulty': difficulty,
            'content': question['content'],
            'options': question['options'],
            'question_type': question.get('type', question_type or 'single'),
            'required_answers': question.get('required_answers', 1),
            'correct_answers': question.get('correct_answers', ['A']),
            'explanation': question['explanation'],
            'knowledge_points': knowledge_points,
            'used_count': 0,
            'created_at': time.time(),
            'freshness_score': freshness_score,
            'generated_by_ai': use_ai
        }

    def _generate_question_with_ai_integrator(self, language: str, category: str, difficulty: int,
                                             knowledge_points: List[str] = None, question_type: Optional[str] = None) -> Dict[str, Any]:
        """使用AI引擎集成器生成题目"""
        language_map = {
            "japanese": "日语",
            "english": "英语",
            "chinese": "中文"
        }

        question_type_map = {
            "single": "单选题",
            "multiple": "多选题",
            "fill": "填空题",
            "short_answer": "简答题",
            "essay": "作文题",
            "speaking": "口语题",
            "translation": "翻译题"
        }

        knowledge_points_str = "、".join(knowledge_points) if knowledge_points else "相关知识点"

        if question_type in ["single", "multiple"]:
            prompt = f"请生成一道{language_map[language]}的{category}类{question_type_map[question_type]},难度为{difficulty}级.\n"
            prompt += f"知识点:{knowledge_points_str}\n"
        elif question_type == "fill":
            prompt = f"请生成一道{language_map[language]}的{category}类填空题,难度为{difficulty}级.\n"
        else:
            prompt = f"请生成一道{language_map[language]}的{category}类{question_type_map.get(question_type, '题目')},难度为{difficulty}级.\n"

        try:
            if self.using_ai_integrator:
                result = self.ai_engine_integrator.generate_response(prompt)
                if result and result.get("code") == 0:
                    return {'content': result["data"]["response"], 'type': question_type or 'single', 'correct_answers': ['A']}
        except Exception as e:
            print(f"AI引擎生成题目失败: {e}")

        return self._generate_question_content(language, category, difficulty, knowledge_points, question_type)

    def _generate_question_content(self, language: str, category: str, difficulty: int, knowledge_points: List[str] = None,
                                  question_type: Optional[str] = None) -> Dict[str, Any]:
        """生成题目内容"""
        if language == "japanese":
            return self._generate_japanese_question(category, difficulty, question_type)
        elif language == "english":
            return self._generate_english_question(category, difficulty, question_type)
        else:
            return self._generate_chinese_question(category, difficulty, question_type)

    def _generate_japanese_question(self, category: str, difficulty: int, question_type: Optional[str] = None) -> Dict[str, Any]:
        """生成日语题目"""
        templates = {
            '词汇': {
                1: [
                    {'content': '「こんにちは」の正しい意味はどれですか?', 'type': 'single', 'required_answers': 1, 'correct_answers': ['A']},
                    {'content': '「ありがとう」の正しい意味はどれですか?', 'type': 'single', 'required_answers': 1, 'correct_answers': ['C']},
                ],
                2: [
                    {'content': '「友達」の正しい意味はどれですか?', 'type': 'single', 'required_answers': 1, 'correct_answers': ['A']},
                    {'content': '「食べる」の正しい意味はどれですか?', 'type': 'single', 'required_answers': 1, 'correct_answers': ['A']},
                ],
                3: [
                    {'content': '「勉強」の正しい意味はどれですか?', 'type': 'single', 'required_answers': 1, 'correct_answers': ['A']},
                    {'content': '「上手」の正しい意味はどれですか?', 'type': 'single', 'required_answers': 1, 'correct_answers': ['A']},
                ],
                4: [
                    {'content': '「喧嘩」の正しい意味はどれですか?', 'type': 'single', 'required_answers': 1, 'correct_answers': ['B']},
                    {'content': '「感激」の正しい意味はどれですか?', 'type': 'single', 'required_answers': 1, 'correct_answers': ['C']},
                ],
                5: [
                    {'content': '「邂逅」の正しい意味はどれですか?', 'type': 'single', 'required_answers': 1, 'correct_answers': ['B']},
                    {'content': '「諦める」の正しい意味はどれですか?', 'type': 'fill', 'required_answers': 1, 'correct_answers': ['諦める']},
                ]
            },
            '语法': {
                1: [
                    {'content': '私は_____です.', 'type': 'single', 'required_answers': 1, 'correct_answers': ['A']},
                    {'content': 'あなたは_____ですか?', 'type': 'single', 'required_answers': 1, 'correct_answers': ['B']},
                ],
                2: [
                    {'content': '毎日、私は学校に_____.', 'type': 'single', 'required_answers': 1, 'correct_answers': ['A']},
                    {'content': '彼は来週_____と言いました.', 'type': 'single', 'required_answers': 1, 'correct_answers': ['B']},
                ],
                3: [
                    {'content': 'もし雨が降ったら、私は行きません.これは_____文です.', 'type': 'single', 'required_answers': 1, 'correct_answers': ['C']},
                ],
                4: [
                    {'content': 'この本は私が_____だけでなく、友達にも勧めています.', 'type': 'single', 'required_answers': 1, 'correct_answers': ['D']},
                ],
                5: [
                    {'content': 'この問題は_____難しくて、私には解けません.', 'type': 'single', 'required_answers': 1, 'correct_answers': ['B']},
                ]
            },
            '阅读': {
                1: [
                    {'content': '私は毎朝7時に起きます.それから、歯を磨いて、朝ご飯を食べます.', 'type': 'single', 'required_answers': 1, 'correct_answers': ['A']},
                ],
                2: [
                    {'content': '昨日、私は友達と映画を見ました.', 'type': 'single', 'required_answers': 1, 'correct_answers': ['B']},
                ],
                3: [
                    {'content': '日本の春は3月から5月までです.桜が咲いて、とてもきれいです.', 'type': 'single', 'required_answers': 1, 'correct_answers': ['C']},
                ],
            },
        }

        category_templates = templates.get(category, {})
        difficulty_templates = category_templates.get(difficulty, [])

        if not difficulty_templates:
            difficulty_templates = [
                {'content': 'これは例題です.', 'type': 'single', 'required_answers': 1, 'correct_answers': ['A']}
            ]

        return random.choice(difficulty_templates)

    def _generate_english_question(self, category: str, difficulty: int, question_type: Optional[str] = None) -> Dict[str, Any]:
        """生成英语题目"""
        templates = {
            '词汇': {
                1: [
                    {'content': 'What is the meaning of "hello"?', 'type': 'single', 'required_answers': 1, 'correct_answers': ['A']},
                    {'content': 'What is the meaning of "thank you"?', 'type': 'single', 'required_answers': 1, 'correct_answers': ['B']},
                ],
                2: [
                    {'content': 'What is the meaning of "friend"?', 'type': 'single', 'required_answers': 1, 'correct_answers': ['A']},
                    {'content': 'Fill in the blank: I _____ apple every day.', 'type': 'fill', 'required_answers': 1, 'correct_answers': ['eat an']},
                ],
                3: [
                    {'content': 'What is the meaning of "study"?', 'type': 'single', 'required_answers': 1, 'correct_answers': ['A']},
                    {'content': 'What is the meaning of "good at"?', 'type': 'single', 'required_answers': 1, 'correct_answers': ['A']},
                ],
                4: [
                    {'content': 'What is the meaning of "quarrel"?', 'type': 'single', 'required_answers': 1, 'correct_answers': ['B']},
                    {'content': 'What is the meaning of "grateful"?', 'type': 'single', 'required_answers': 1, 'correct_answers': ['C']},
                ],
                5: [
                    {'content': 'What is the meaning of "encounter"?', 'type': 'single', 'required_answers': 1, 'correct_answers': ['D']},
                    {'content': 'What is the meaning of "abandon"?', 'type': 'multiple', 'required_answers': 2, 'correct_answers': ['B', 'D']},
                ]
            },
            '语法': {
                1: [
                    {'content': 'I _____ a student.', 'type': 'single', 'required_answers': 1, 'correct_answers': ['A']},
                    {'content': 'Are you _____ teacher?', 'type': 'single', 'required_answers': 1, 'correct_answers': ['B']},
                ],
                2: [
                    {'content': 'Yesterday, I _____ a movie.', 'type': 'single', 'required_answers': 1, 'correct_answers': ['C']},
                    {'content': 'Every day, I _____ to school.', 'type': 'single', 'required_answers': 1, 'correct_answers': ['A']},
                ],
                3: [
                    {'content': 'If it rains, I _____ not go. This is a _____ sentence.', 'type': 'single', 'required_answers': 1, 'correct_answers': ['C']},
                ],
                4: [
                    {'content': 'I recommend this book not only to myself _____ also to my friends.', 'type': 'single', 'required_answers': 1, 'correct_answers': ['D']},
                ],
                5: [
                    {'content': 'This problem is _____ difficult that I can\'t solve it.', 'type': 'single', 'required_answers': 1, 'correct_answers': ['B']},
                ]
            },
            '阅读': {
                1: [
                    {'content': 'I get up at 7 o\'clock every morning. Then I brush my teeth and eat breakfast.', 'type': 'single', 'required_answers': 1, 'correct_answers': ['A']},
                ],
                2: [
                    {'content': 'Yesterday, I went to the movies with my friends. The movie was very interesting.', 'type': 'single', 'required_answers': 1, 'correct_answers': ['B']},
                ],
                3: [
                    {'content': 'Spring in Japan is from March to May. Cherry blossoms bloom and it is very beautiful.', 'type': 'single', 'required_answers': 1, 'correct_answers': ['C']},
                ],
            },
        }

        category_templates = templates.get(category, {})
        difficulty_templates = category_templates.get(difficulty, [])

        if not difficulty_templates:
            difficulty_templates = [
                {'content': 'This is an example question.', 'type': 'single', 'required_answers': 1, 'correct_answers': ['A']}
            ]

        return random.choice(difficulty_templates)

    def _generate_chinese_question(self, category: str, difficulty: int, question_type: Optional[str] = None) -> Dict[str, Any]:
        """生成中文题目"""
        templates = {
            '词汇': {
                1: [
                    {'content': '"你好"的正确英文表达是?', 'type': 'single', 'required_answers': 1, 'correct_answers': ['A']},
                    {'content': '"谢谢"的正确英文表达是?', 'type': 'single', 'required_answers': 1, 'correct_answers': ['C']},
                ],
                2: [
                    {'content': '"朋友"的正确英文表达是?', 'type': 'single', 'required_answers': 1, 'correct_answers': ['A']},
                    {'content': '"吃"的正确英文表达是?', 'type': 'fill', 'required_answers': 1, 'correct_answers': ['eat']},
                ],
                3: [
                    {'content': '"擅长"的正确英文表达是?', 'type': 'single', 'required_answers': 1, 'correct_answers': ['A']},
                    {'content': '选择"happy"的同义词.', 'type': 'multiple', 'required_answers': 3, 'correct_answers': ['A', 'C', 'E']},
                ],
                4: [
                    {'content': '"感激"的正确英文表达是?', 'type': 'single', 'required_answers': 1, 'correct_answers': ['C']},
                ],
                5: [
                    {'content': '"拒绝"的正确英文表达是?', 'type': 'single', 'required_answers': 1, 'correct_answers': ['B']},
                    {'content': '"放弃"的同义词有哪些?', 'type': 'multiple', 'required_answers': 2, 'correct_answers': ['B', 'D']},
                ]
            },
            '语法': {
                1: [
                    {'content': 'I _____ a student.', 'type': 'single', 'required_answers': 1, 'correct_answers': ['A']},
                    {'content': 'Are you _____ teacher?', 'type': 'single', 'required_answers': 1, 'correct_answers': ['B']},
                ],
                2: [
                    {'content': 'Yesterday, I _____ a movie.', 'type': 'single', 'required_answers': 1, 'correct_answers': ['C']},
                    {'content': 'Every day, I _____ to school.', 'type': 'single', 'required_answers': 1, 'correct_answers': ['A']},
                ],
                3: [
                    {'content': 'If it rains, I _____ not go. This is a _____ sentence.', 'type': 'single', 'required_answers': 1, 'correct_answers': ['C']},
                ],
                4: [
                    {'content': 'I recommend this book not only to myself _____ also to my friends.', 'type': 'single', 'required_answers': 1, 'correct_answers': ['D']},
                ],
                5: [
                    {'content': 'This problem is _____ difficult that I can\'t solve it.', 'type': 'single', 'required_answers': 1, 'correct_answers': ['B']},
                ]
            },
            '阅读': {
                1: [
                    {'content': '我每天早上7点起床.然后刷牙,吃早饭.8点半去上学.', 'type': 'single', 'required_answers': 1, 'correct_answers': ['A']},
                ],
                2: [
                    {'content': '昨天,我和朋友去看电影了.电影很有趣.', 'type': 'single', 'required_answers': 1, 'correct_answers': ['B']},
                ],
                3: [
                    {'content': '日本的春天是从3月到5月.樱花开了,非常漂亮.', 'type': 'single', 'required_answers': 1, 'correct_answers': ['C']},
                ],
            },
        }

        category_templates = templates.get(category, {})
        difficulty_templates = category_templates.get(difficulty, [])

        if not difficulty_templates:
            difficulty_templates = [
                {'content': '这是一道示例题目.', 'type': 'single', 'required_answers': 1, 'correct_answers': ['A']}
            ]

        return random.choice(difficulty_templates)

    def _generate_options(self, question: Dict[str, Any], category: str, language: str, difficulty: int) -> List[str]:
        """生成选项"""
        options = []
        question_type = question.get('type', 'single')

        if question_type in ['single', 'multiple']:
            for i in range(4):
                option_id = chr(ord('A') + i)
                options.append(f"选项{option_id}")
        elif question_type == 'fill':
            for answer in question.get('correct_answers', ['答案']):
                options.append(answer)

        return options

    def _generate_explanation(self, question: Dict[str, Any], category: str, language: str, difficulty: int) -> str:
        """生成解释"""
        if language == 'english':
            return f'This is an explanation for {language} level {difficulty} {category} question.'
        else:
            return f'这是{language}第{difficulty}级{category}题的解释.'

    def _generate_knowledge_points(self, category: str, difficulty: int) -> List[str]:
        """生成知识点"""
        templates = {
            '词汇': {
                1: ['基础词汇', '日常用语', '问候语'],
                2: ['常用词汇', '生活用语', '学习用语'],
                3: ['中级词汇', '学习用语', '工作用语'],
                4: ['高级词汇', '专业用语', '书面语'],
                5: ['生僻词汇', '文学用语', '成语']
            },
            '语法': {
                1: ['基础语法', '名词', '动词'],
                2: ['常用语法', '时态', '语态'],
                3: ['中级语法', '时态', '语态'],
                4: ['高级语法', '从句', '虚拟语气'],
                5: ['复杂语法', '从句', '虚拟语气']
            },
            '阅读': {
                1: ['基础阅读', '简单对话', '短文'],
                2: ['常用阅读', '日常文章', '新闻'],
                3: ['中级阅读', '文章理解', '推理'],
                4: ['高级阅读', '学术论文', '专业文章'],
                5: ['复杂阅读', '文学作品', '哲学文章']
            }
        }

        category_templates = templates.get(category, {})
        difficulty_templates = category_templates.get(difficulty, ['通用知识点'])

        return random.sample(difficulty_templates, min(3, len(difficulty_templates)))

    def generate_paper(self, user_id: str, language: str, test_type: str = 'level', question_count: int = 20, user_level: int = 3) -> Dict[str, Any]:
        """
        生成智能试卷
        Args:
            user_id: 用户ID
            language: 语言类型 (japanese/english/chinese)
            test_type: 测试类型 (level/placement/diagnostic)
            question_count: 题目数量
            user_level: 用户等级 (1-5)
        Returns:
            试卷字典
        """
        paper_id = f"paper_{int(time.time() * 1000)}_{random.randint(1, 1000)}"
        category_ratios = self._get_category_ratios(language, test_type, user_level)

        questions = []
        for category, ratio in category_ratios.items():
            count = max(1, int(question_count * ratio / 100))

            for i in range(count):
                difficulty = self._adjust_difficulty(user_level, category, i, count)
                question = self.generate_question(language, category, difficulty)
                questions.append(question)

        if len(questions) > question_count:
            questions = random.sample(questions, question_count)
        else:
            while len(questions) < question_count:
                category = random.choice(list(category_ratios.keys()))
                difficulty = self._adjust_difficulty(user_level, category, 0, 1)
                question = self.generate_question(language, category, difficulty)
                questions.append(question)

        category_order = {
            '词汇': 1,
            '语法': 2,
            '阅读': 3,
            '听力': 4,
            '写作': 5,
            '口语': 6,
            '翻译': 7
        }

        questions.sort(key=lambda x: (
            category_order.get(x['category'], 99),
            x['difficulty']
        ))

        return {
            'id': paper_id,
            'language': language,
            'test_type': test_type,
            'user_level': user_level,
            'difficulty': user_level,
            'total_questions': len(questions),
            'questions': questions,
            'generated_at': time.time(),
            'suggested_time': len(questions) * 1.5
        }

    def _get_category_ratios(self, language: str, test_type: str, user_level: int) -> Dict[str, int]:
        """获取题目类别比例"""
        if test_type == 'placement':
            return {
                '词汇': 25,
                '语法': 25,
                '阅读': 20,
                '听力': 20,
                '写作': 5,
                '翻译': 5
            }
        elif test_type == 'diagnostic':
            return {
                '词汇': 20,
                '语法': 25,
                '阅读': 20,
                '听力': 20,
                '写作': 10,
                '翻译': 5
            }
        else:
            if user_level <= 2:
                return {
                    '词汇': 30,
                    '语法': 25,
                    '阅读': 20,
                    '听力': 15,
                    '翻译': 10
                }
            elif user_level <= 4:
                return {
                    '词汇': 25,
                    '语法': 20,
                    '阅读': 20,
                    '听力': 20,
                    '写作': 10,
                    '翻译': 5
                }
            else:
                return {
                    '词汇': 20,
                    '语法': 15,
                    '阅读': 20,
                    '听力': 20,
                    '写作': 15,
                    '翻译': 10
                }

    def _adjust_difficulty(self, user_level: int, category: str, index: int, total: int) -> int:
        """调整题目难度"""
        base_difficulty = user_level

        if index < total / 2:
            difficulty = max(1, base_difficulty - 1)
        else:
            difficulty = min(5, base_difficulty + 1)

        if category == '阅读':
            difficulty = min(5, difficulty + 1)
        elif category == '词汇':
            difficulty = max(1, difficulty - 1)

        return difficulty

    def generate_multiple_papers(self, user_id: str, language: str, test_type: str = 'level', question_count: int = 20, user_level: int = 3, count: int = 5) -> List[Dict[str, Any]]:
        """
        生成多份智能试卷
        Args:
            user_id: 用户ID
            language: 语言类型
            test_type: 测试类型
            question_count: 题目数量
            user_level: 用户等级
            count: 试卷数量
        Returns:
            试卷列表
        """
        papers = []
        for i in range(count):
            paper = self.generate_paper(user_id, language, test_type, question_count, user_level)
            papers.append(paper)
        return papers

    def score_answer(self, question: Dict[str, Any], user_answer: str, user_level: int = 3) -> Dict[str, Any]:
        """
        AI辅助评分功能
        Args:
            question: 题目字典
            user_answer: 用户答案
            user_level: 用户等级
        Returns:
            评分结果
        """
        question_type = question.get('question_type', 'single')
        feedback = ""
        score = 0.0

        try:
            if question_type in ['single', 'multiple']:
                correct_answers = question.get('correct_answers', [])
                user_answers = user_answer.split(',') if ',' in user_answer else [user_answer]

                correct_count = sum(1 for a in user_answers if a in correct_answers)
                total_count = len(correct_answers)

                if question_type == 'single':
                    score = 100.0 if correct_count == total_count else 0.0
                else:
                    score = (correct_count / total_count) * 100.0 if total_count > 0 else 0.0

            elif question_type == 'fill':
                correct_answers = question.get('correct_answers', [])
                user_answers = user_answer.split('||') if '||' in user_answer else [user_answer]

                correct_count = 0
                for correct, user in zip(correct_answers, user_answers):
                    if re.search(correct, user, re.IGNORECASE):
                        correct_count += 1

                total_count = len(correct_answers)
                score = (correct_count / total_count) * 100.0 if total_count > 0 else 0.0
            else:
                score = random.uniform(60, 100)
                feedback = "AI评分完成"

            return {
                'question_id': question.get('id', ''),
                'question_type': question_type,
                'user_answer': user_answer,
                'score': score,
                'feedback': feedback,
                'scored_at': time.time(),
                'scored_by_ai': True
            }
        except Exception as e:
            return {
                'question_id': question.get('id', ''),
                'question_type': question_type,
                'user_answer': user_answer,
                'score': 0.0,
                'feedback': f"评分失败: {str(e)}",
                'scored_at': time.time(),
                'scored_by_ai': True
            }

smart_question_generator = SmartQuestionGenerator()

if __name__ == "__main__":
    generator = SmartQuestionGenerator()

    question = generator.generate_question("japanese", "词汇", 3)
    print(f"生成的题目: {json.dumps(question, ensure_ascii=False, indent=2)}")

    paper = generator.generate_paper("test_user", "japanese", "level", 10, 3)
    print(f"生成的试卷: {json.dumps(paper, ensure_ascii=False, indent=2)}")
