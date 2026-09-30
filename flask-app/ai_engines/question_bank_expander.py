import secrets
# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
AI驱动的题库拓展系统
使用AI自动生成新题目,拓展题库内容,增加题目储量
"""

import time
import threading
import concurrent.futures
import random, secrets
import logging
from typing import Dict, List, Optional, Any

from app.models.question import QuestionManager, Question
from app.utils.logging import logger

logger = logging.getLogger(__name__)


class QuestionBankExpander:
    """AI驱动的题库拓展系统"""

    def __init__(self):
        """初始化题库拓展系统"""
        self._config = {
            "expander_id": f"question_bank_expander_{int(time.time())}_{(1000 + secrets.randbelow(int(9999) - int(1000) + 1))}",
            "expander_name": "Question Bank Expander AI",
            "enabled": True,
            "auto_expansion_enabled": True,
            "expansion_interval": 3600,
            "questions_per_expansion": 100,
            "max_questions_per_category": 10000,
            "max_questions_per_language": 50000,
            "max_questions_per_level": 20000,
            "difficulty_distribution": {
                "easy": 0.3,
                "medium": 0.5,
                "hard": 0.2
            },
            "question_type_distribution": {
                "single_choice": 0.3,
                "multiple_choice": 0.25,
                "true_false": 0.1,
                "fill_blank": 0.1,
                "short_answer": 0.1,
                "listening": 0.15
            },
            "subjects": {
                "math": {
                    "name": "数学",
                    "categories": ["算术", "代数", "几何", "概率", "统计"],
                    "templates": {
                        "single_choice": [
                            "{operation}的结果是多少?",
                            "{expression}等于多少?",
                            "下列哪个选项是{problem}的解?",
                            "{question}的正确答案是?"
                        ],
                        "multiple_choice": [
                            "下列哪些选项是{problem}的解?",
                            "关于{topic},下列说法正确的是?"
                        ],
                        "true_false": [
                            "{statement}是正确的.",
                            "{statement}是错误的."
                        ],
                        "fill_blank": [
                            "{problem}的结果是{blank}.",
                        ],
                        "short_answer": [
                            "请计算{problem}.",
                        ]
                    }
                },
                "english": {
                    "name": "英语",
                    "categories": ["词汇", "语法", "阅读", "听力", "写作"],
                    "templates": {
                        "single_choice": [
                            "下列哪个选项是{word}的同义词?",
                            "选择正确的语法结构:{sentence}"
                        ],
                        "multiple_choice": [
                            "下列哪些是{topic}的正确用法?",
                        ],
                        "true_false": [
                            "{statement}是正确的.",
                            "{statement}是错误的."
                        ],
                        "fill_blank": [
                            "完成句子:{sentence}"
                        ],
                        "short_answer": [
                            "请用{word}造句."
                        ]
                    }
                },
                "japanese": {
                    "name": "日语",
                    "categories": ["词汇", "语法", "听力", "阅读", "写作"],
                    "templates": {
                        "single_choice": [
                            "{word}の同義語はどれですか?",
                        ],
                        "multiple_choice": [
                            "{topic}の正しい使い方はどれですか?",
                            "{grammar}について,正しい説明はどれですか?"
                        ],
                        "true_false": [
                            "{statement}は正しいです.",
                        ],
                        "fill_blank": [
                            "正しい単語を入れてください:{sentence}",
                        ],
                        "short_answer": [
                            "{word}の意味を説明してください.",
                            "{word}を使って文を作ってください."
                        ]
                    }
                },
                "chinese": {
                    "name": "语文",
                    "templates": {
                        "single_choice": [
                        ],
                        "multiple_choice": [
                            "下列哪些是{topic}的正确用法?",
                            "关于{grammar},下列说法正确的是?"
                        ],
                        "true_false": [
                            "{statement}是错误的."
                        ],
                        "fill_blank": [
                            "填写正确的词语:{sentence}",
                            "完成句子:{sentence}"
                        ],
                        "short_answer": [
                            "请解释{word}的含义.",
                        ]
                    }
                }
            }
        }
        self._status = {
            "running": False,
            "total_questions_generated": 0,
            "last_expansion": 0,
            "expansion_history": [],
            "expansion_count": 0
        }
        self._lock = threading.Lock()
        self._expansion_thread = None
        self._question_manager = QuestionManager()
        logger.info("题库拓展系统初始化完成")

    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """初始化题库拓展系统

        Args:
            config: 可选的配置字典

        Returns:
            bool: 是否初始化成功
        """
        try:
            logger.info("开始初始化题库拓展系统...")
            if config:
                self._config.update(config)

            self._start_expansion_thread()

            self._status["running"] = True

            logger.info(f"题库拓展系统初始化成功,ID: {self._config['expander_id']}")
            return True
        except Exception as e:
            logger.error(f"题库拓展系统初始化失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

    def _start_expansion_thread(self):
        """启动拓展线程"""
        def expansion_loop():
            while self._status["running"]:
                time.sleep(self._config["expansion_interval"])
                self.expand_question_bank()

        self._expansion_thread = threading.Thread(target=expansion_loop, daemon=True)
        self._expansion_thread.start()
        logger.info("题库拓展线程启动成功")

    def expand_question_bank(self, count: Optional[int] = None) -> Dict[str, Any]:
        """拓展题库

        Args:
            count: 生成题目的数量,默认使用配置中的值

        Returns:
            Dict[str, Any]: 拓展结果
        """
        try:
            logger.info("开始拓展题库...")

            bank_status = self._analyze_question_bank()
            logger.info(f"当前题库状态: {bank_status}")

            questions_count = count or self._config["questions_per_expansion"]

            generated_questions = []
            success_count = 0
            failed_count = 0

            def generate_question_worker():
                nonlocal success_count, failed_count
                question_params = self._determine_question_params(bank_status)
                question = self._generate_question(**question_params)
                if question:
                    generated_questions.append(question)
                    success_count += 1
                else:
                    failed_count += 1

            max_workers = min(10, questions_count)

            with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = [executor.submit(generate_question_worker) for _ in range(questions_count)]
                concurrent.futures.wait(futures)

            bank_status_after = self._analyze_question_bank()
            expansion_record = {
                "timestamp": time.time(),
                "questions_generated": success_count,
                "questions_failed": failed_count,
                "bank_status_before": bank_status,
                "bank_status_after": bank_status_after
            }

            self._status["expansion_count"] += 1
            self._status["total_questions_generated"] += success_count
            self._status["last_expansion"] = time.time()
            self._status["expansion_history"].append(expansion_record)

            logger.info(f"题库拓展完成,成功生成 {success_count} 道题目,失败 {failed_count} 道")
            return expansion_record
        except Exception as e:
            logger.error(f"拓展题库失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                "timestamp": time.time(),
                "questions_generated": 0,
                "questions_failed": 0,
                "error": str(e)
            }

    def _analyze_question_bank(self) -> Dict[str, Any]:
        """分析当前题库状态

        Returns:
            Dict[str, Any]: 题库状态
        """
        report = self._question_manager.generate_question_bank_report()

        categories = self._question_manager.get_all_categories()
        category_stats = {}
        for category in categories:
            category_questions = self._question_manager.get_questions(category_id=category.id, limit=1000)
            category_stats[category.id] = {
                "name": category.name,
                "count": len(category_questions)
            }

        languages = self._question_manager.get_all_languages()
        language_stats = {}
        for language in languages:
            language_questions = self._question_manager.get_questions(language_id=language.id, limit=1000)
            language_stats[language.id] = {
                "name": language.name,
                "code": language.code,
                "count": len(language_questions)
            }

        levels = self._question_manager.get_all_levels()
        level_stats = {}
        for level in levels:
            level_questions = self._question_manager.get_questions(level_id=level.id, limit=1000)
            level_stats[level.id] = {
                "name": level.name,
                "level": level.level,
                "count": len(level_questions)
            }

        question_types = ["single_choice", "multiple_choice", "true_false", "fill_blank", "short_answer"]
        type_stats = {}
        for question_type in question_types:
            type_questions = self._question_manager.get_questions(question_type=question_type, limit=1000)
            type_stats[question_type] = len(type_questions)

        return {
            "total_questions": report.get("total_questions", 0),
            "category_stats": category_stats,
            "language_stats": language_stats,
            "level_stats": level_stats,
            "type_stats": type_stats
        }

    def _determine_question_params(self, bank_status: Dict[str, Any]) -> Dict[str, Any]:
        """确定生成题目的参数

        Args:
            bank_status: 题库状态

        Returns:
            Dict[str, Any]: 题目参数
        """
        language_id = self._select_language(bank_status)
        level_id = self._select_level(bank_status)
        category_id = self._select_category(bank_status, language_id)
        question_type = self._select_question_type(bank_status)
        difficulty = self._select_difficulty(level_id)

        return {
            "language_id": language_id,
            "level_id": level_id,
            "category_id": category_id,
            "question_type": question_type,
            "difficulty": difficulty
        }

    def _select_language(self, bank_status: Dict[str, Any]) -> int:
        """智能选择语种

        Args:
            bank_status: 题库状态

        Returns:
            int: 语种ID
        """
        language_stats = bank_status.get("language_stats", {})

        if not language_stats:
            return 1

        total_questions = sum(stats["count"] for stats in language_stats.values())
        if total_questions == 0:
            return 1

        ideal_ratio = 1.0 / len(language_stats)

        imbalance_scores = {}
        for language_id, stats in language_stats.items():
            current_ratio = stats["count"] / total_questions
            imbalance = abs(current_ratio - ideal_ratio)
            imbalance_scores[language_id] = imbalance

        selected_language = max(imbalance_scores, key=imbalance_scores.get)
        return selected_language

    def _select_level(self, bank_status: Dict[str, Any]) -> int:
        """智能选择等级

        Args:
            bank_status: 题库状态

        Returns:
            int: 等级ID
        """
        level_stats = bank_status.get("level_stats", {})

        if not level_stats:
            return 1

        total_questions = sum(stats["count"] for stats in level_stats.values())
        if total_questions == 0:
            return 1

        ideal_ratio = 1.0 / len(level_stats)

        imbalance_scores = {}
        for level_id, stats in level_stats.items():
            current_ratio = stats["count"] / total_questions
            imbalance = abs(current_ratio - ideal_ratio)
            imbalance_scores[level_id] = imbalance

        selected_level = max(imbalance_scores, key=imbalance_scores.get)
        return selected_level

    def _select_category(self, bank_status: Dict[str, Any], language_id: int) -> int:
        """智能选择分类

        Args:
            bank_status: 题库状态
            language_id: 语言ID

        Returns:
            int: 分类ID
        """
        category_stats = bank_status.get("category_stats", {})

        if not category_stats:
            return 1

        min_count = float('inf')
        selected_category = None

        for category_id, stats in category_stats.items():
            if stats["count"] < min_count:
                min_count = stats["count"]
                selected_category = category_id

        return selected_category or 1

    def _select_question_type(self, bank_status: Dict[str, Any]) -> str:
        """智能选择题目类型

        Args:
            bank_status: 题库状态

        Returns:
            str: 题目类型
        """
        type_stats = bank_status.get("type_stats", {})

        if not type_stats:
            types = list(self._config["question_type_distribution"].keys())
            weights = list(self._config["question_type_distribution"].values())
            return random.choices(types, weights=weights)[0]

        total_questions = sum(count for count in type_stats.values())
        if total_questions == 0:
            types = list(self._config["question_type_distribution"].keys())
            weights = list(self._config["question_type_distribution"].values())
            return random.choices(types, weights=weights)[0]

        ideal_distribution = self._config["question_type_distribution"]

        imbalance_scores = {}
        for question_type, count in type_stats.items():
            ideal_ratio = ideal_distribution.get(question_type, 0)
            current_ratio = count / total_questions
            imbalance = abs(current_ratio - ideal_ratio)
            imbalance_scores[question_type] = imbalance

        selected_type = max(imbalance_scores, key=imbalance_scores.get)
        return selected_type

    def _select_difficulty(self, level_id: int = 1) -> str:
        """根据等级选择难度

        Args:
            level_id: 等级ID,用于调整难度分布

        Returns:
            str: 难度级别
        """
        if level_id == 1:
            difficulty_distribution = {
                "easy": 0.6,
                "medium": 0.3,
                "hard": 0.1
            }
        elif level_id == 2:
            difficulty_distribution = {
                "easy": 0.3,
                "medium": 0.5,
                "hard": 0.2
            }
        else:
            difficulty_distribution = {
                "easy": 0.1,
                "medium": 0.4,
                "hard": 0.5
            }

        difficulties = list(difficulty_distribution.keys())
        weights = list(difficulty_distribution.values())
        return random.choices(difficulties, weights=weights)[0]

    def _generate_question(self, language_id: int, level_id: int, category_id: int,
                           question_type: str, difficulty: str, check_duplicate: bool = True) -> Optional[Question]:
        """生成题目

        Args:
            language_id: 语种ID
            level_id: 等级ID
            category_id: 分类ID
            question_type: 题目类型
            difficulty: 难度级别
            check_duplicate: 是否检查重复

        Returns:
            Optional[Question]: 生成的题目
        """
        try:
            max_attempts = 10
            for attempt in range(max_attempts):
                subject = self._determine_subject(language_id, category_id)

                if subject == "math":
                    question = self._generate_math_question(
                        language_id, level_id, category_id, question_type, difficulty
                    )
                elif subject == "english":
                    question = self._generate_english_question(
                        language_id, level_id, category_id, question_type, difficulty
                    )
                elif subject == "japanese":
                    question = self._generate_japanese_question(
                        language_id, level_id, category_id, question_type, difficulty
                    )
                elif subject == "chinese":
                    question = self._generate_chinese_question(
                        language_id, level_id, category_id, question_type, difficulty
                    )
                else:
                    if question_type == "single_choice":
                        question = self._generate_single_choice_question(
                            language_id, level_id, category_id, difficulty
                        )
                    elif question_type == "multiple_choice":
                        question = self._generate_multiple_choice_question(
                            language_id, level_id, category_id, difficulty
                        )
                    elif question_type == "true_false":
                        question = self._generate_true_false_question(
                            language_id, level_id, category_id, difficulty
                        )
                    elif question_type == "fill_blank":
                        question = self._generate_fill_blank_question(
                            language_id, level_id, category_id, difficulty
                        )
                    elif question_type == "short_answer":
                        question = self._generate_short_answer_question(
                            language_id, level_id, category_id, difficulty
                        )
                    elif question_type == "listening":
                        question = self._generate_listening_question(
                            language_id, level_id, category_id, difficulty
                        )
                    else:
                        logger.warning(f"不支持的题目类型: {question_type}")
                        return None

                if question:
                    if check_duplicate:
                        is_duplicate = self._question_manager.check_question_duplicate(
                            question.content, language_id, level_id
                        )
                        if not is_duplicate:
                            return question
                    else:
                        return question

            if check_duplicate:
                logger.warning("多次尝试后仍然重复,放弃生成题目")
            return None
        except Exception as e:
            logger.error(f"生成题目失败: {str(e)}")
            return None

    def _generate_japanese_word(self, difficulty: str) -> str:
        """生成日语单词

        Args:
            difficulty: 难度级别

        Returns:
            str: 日语单词
        """
        words = {
            "easy": ["猫", "犬", "本", "家", "学校", "食べる", "飲む", "行く", "来る", "見る", "聞く", "話す", "書く", "読む", "步く", "走る", "跳ぶ", "泳ぐ", "歌う", "踊る"],
            "medium": ["勉強", "仕事", "友達", "家族", "電話", "コンピューター", "インターネット", "映画", "音楽", "スポーツ", "旅行", "食事", "睡眠", "運動", "休暇", "趣味"],
            "hard": ["認識", "理解", "分析", "統合", "創造", "革新", "挑戦", "突破", "達成", "超越", "認知", "洞察", "思考", "論理", "推理", "発展", "進化", "変革"]
        }
        return random.choice(words.get(difficulty, words["easy"]))

    def _determine_subject(self, language_id: int, category_id: int) -> str:
        """根据语言ID和分类ID确定学科

        Args:
            language_id: 语言ID
            category_id: 分类ID

        Returns:
            str: 学科名称
        """
        if language_id == 1:
            return "japanese"
        elif language_id == 2:
            return "english"
        elif language_id == 3:
            return "chinese"
        else:
            if category_id in [1, 2, 3]:
                return "math"
            elif category_id in [4, 5, 6]:
                return "chinese"
            elif category_id in [7, 8, 9]:
                return "english"
            elif category_id in [10, 11, 12]:
                return "japanese"
            else:
                return "general"

    def _generate_math_question(self, language_id: int, level_id: int, category_id: int,
                                question_type: str, difficulty: str) -> Optional[Question]:
        """生成数学题目

        Args:
            language_id: 语言ID
            level_id: 等级ID
            category_id: 分类ID
            question_type: 题目类型
            difficulty: 难度级别

        Returns:
            Optional[Question]: 生成的题目
        """
        try:
            if question_type == "single_choice":
                if difficulty == "easy":
                    a = (1 + secrets.randbelow(int(10) - int(1) + 1))
                    b = random.randint(1, 10)
                    operations = ["+", "-", "*", "/"]
                    operation = random.choice(operations)

                    if operation == "+":
                        answer = a + b
                        content = f"{a} {operation} {b} 的结果是多少?"
                    elif operation == "-":
                        if b > a:
                            a, b = b, a
                        answer = a - b
                        content = f"{a} {operation} {b} 的结果是多少?"
                    elif operation == "*":
                        answer = a * b
                        content = f"{a} {operation} {b} 的结果是多少?"
                    elif operation == "/":
                        b = (1 + secrets.randbelow(int(10) - int(1) + 1))
                        a = b * random.randint(1, 10)
                        answer = a // b
                        content = f"{a} {operation} {b} 的结果是多少?"

                    options = [answer]
                    while len(options) < 4:
                        wrong_answer = answer + random.randint(-5, 5)
                        if wrong_answer != answer and wrong_answer >= 0:
                            options.append(wrong_answer)
                    random.shuffle(options)

                    difficulty_score = {
                        "easy": 1.0,
                        "medium": 2.0,
                        "hard": 3.0
                    }.get(difficulty, 1.0)

                    question = Question(
                        content=content,
                        question_type=question_type,
                        language_id=language_id,
                        level_id=level_id,
                        category_id=category_id,
                        options=options,
                        explanation=f"{a} {operation} {b} = {answer}",
                        difficulty_score=difficulty_score
                    )
                    return question
            return None
        except Exception as e:
            logger.error(f"生成数学题目失败: {str(e)}")
            return None

    def _generate_english_question(self, language_id: int, level_id: int, category_id: int,
                                   question_type: str, difficulty: str) -> Optional[Question]:
        """生成英语题目

        Args:
            language_id: 语言ID
            level_id: 等级ID
            category_id: 分类ID
            question_type: 题目类型
            difficulty: 难度级别

        Returns:
            Optional[Question]: 生成的题目
        """
        try:
            if question_type == "single_choice":
                word = self._generate_english_word(difficulty)
                content = f"选择{word}的正确中文意思"

                options = ["选项1", "选项2", "选项3", "选项4"]
                correct_answer = str(random.randint(0, 3))

                difficulty_score = {
                    "easy": 1.0,
                    "medium": 2.0,
                    "hard": 3.0
                }.get(difficulty, 1.0)

                question = Question(
                    content=content,
                    question_type=question_type,
                    language_id=language_id,
                    level_id=level_id,
                    category_id=category_id,
                    options=options,
                    explanation=f"{word}的正确意思是{options[int(correct_answer)]}",
                    difficulty_score=difficulty_score
                )
                return question
            return None
        except Exception as e:
            logger.error(f"生成英语题目失败: {str(e)}")
            return None

    def _generate_japanese_question(self, language_id: int, level_id: int, category_id: int,
                                    question_type: str, difficulty: str) -> Optional[Question]:
        """生成日语题目

        Args:
            language_id: 语言ID
            level_id: 等级ID
            category_id: 分类ID
            question_type: 题目类型
            difficulty: 难度级别

        Returns:
            Optional[Question]: 生成的题目
        """
        try:
            if question_type == "single_choice":
                word = self._generate_japanese_word(difficulty)
                content = f"選擇{word}的正確中文意思"

                options = ["選項1", "選項2", "選項3", "選項4"]
                correct_answer = str(random.randint(0, 3))

                difficulty_score = {
                    "easy": 1.0,
                    "medium": 2.0,
                    "hard": 3.0
                }.get(difficulty, 1.0)

                question = Question(
                    content=content,
                    question_type=question_type,
                    language_id=language_id,
                    level_id=level_id,
                    category_id=category_id,
                    options=options,
                    explanation=f"{word}的正確意思是{options[int(correct_answer)]}",
                    difficulty_score=difficulty_score
                )
                return question
            return None
        except Exception as e:
            logger.error(f"生成日语题目失败: {str(e)}")
            return None

    def _generate_chinese_question(self, language_id: int, level_id: int, category_id: int,
                                   question_type: str, difficulty: str) -> Optional[Question]:
        """生成语文题目

        Args:
            language_id: 语言ID
            level_id: 等级ID
            category_id: 分类ID
            question_type: 题目类型
            difficulty: 难度级别

        Returns:
            Optional[Question]: 生成的题目
        """
        try:
            if question_type == "single_choice":
                words = ["美丽", "漂亮", "好看", "美观"]
                word = random.choice(words)
                content = f"选择与{word}意思最接近的词语"

                options = ["美丽", "漂亮", "好看", "美观"]
                random.shuffle(options)
                correct_answer = str(random.randint(0, 3))

                difficulty_score = {
                    "easy": 1.0,
                    "medium": 2.0,
                    "hard": 3.0
                }.get(difficulty, 1.0)

                question = Question(
                    content=content,
                    question_type=question_type,
                    language_id=language_id,
                    level_id=level_id,
                    category_id=category_id,
                    options=options,
                    answer=correct_answer,
                    explanation=f"{word}的意思与{options[int(correct_answer)]}最接近",
                    difficulty_score=difficulty_score
                )
                return question

            return None
        except Exception as e:
            logger.error(f"生成语文题目失败: {str(e)}")
            return None

    def _generate_english_word(self, difficulty: str) -> str:
        """生成英语单词

        Args:
            difficulty: 难度级别

        Returns:
            str: 英语单词
        """
        words = {
            "easy": ["cat", "dog", "book", "house", "school", "eat", "drink", "go", "come", "see", "hear", "speak", "write", "read", "walk", "run", "jump", "swim", "sing", "dance"],
            "medium": ["study", "work", "friend", "family", "phone", "computer", "internet", "movie", "music", "sports", "travel", "meal", "sleep", "exercise", "learning", "job", "vacation", "hobby", "career", "education"],
            "hard": ["recognition", "understanding", "analysis", "integration", "creation", "innovation", "challenge", "breakthrough", "achievement", "transcendence", "cognition", "insight", "thinking", "logic", "reasoning", "creativity", "development", "evolution", "transformation"]
        }
        return random.choice(words.get(difficulty, words["easy"]))

    def _generate_english_statement(self, difficulty: str = "easy") -> str:
        """生成英语陈述句

        Args:
            difficulty: 难度级别

        Returns:
            str: 英语陈述
        """
        statements = [
            "Water boils at 100 degrees Celsius.",
            "Humans need oxygen to survive.",
            "The capital of Japan is Tokyo.",
            "The human body has 206 bones.",
            "Birds can fly.",
            "The moon orbits the Earth.",
            "The Earth orbits the sun.",
            "December is the last month of the year.",
            "Summer is hotter than winter.",
        ]
        return random.choice(statements)

    def _generate_english_blank_sentence(self) -> str:
        """生成英语填空题

        Returns:
            str: 英语填空题
        """
        sentences = [
            "She is___.",
            "They are___.",
            "He likes___.",
            "We live in___.",
            "The cat is___.",
            "Today is___.",
            "Tomorrow will be___.",
            "Yesterday was___.",
            "I can___.",
            "She can't___.",
            "They will___.",
            "He has___.",
            "We need___.",
            "The dog has___.",
            "She wants___.",
            "They want___.",
            "He needs___.",
            "We have___."
        ]
        return random.choice(sentences)

    def _generate_single_choice_question(self, language_id: int, level_id: int,
                                         category_id: int, difficulty: str) -> Question:
        """生成单选题

        Args:
            language_id: 语种ID
            level_id: 等级ID
            category_id: 分类ID
            difficulty: 难度级别

        Returns:
            Question: 生成的题目
        """
        word = self._generate_english_word(difficulty)
        if language_id == 1:
            content = f"次の単語の正しい意味を選んでください.{word}"
            options = [
                f"選択肢1 - {word}",
                f"選択肢2 - {word}",
                f"選択肢3 - {word}",
                f"選択肢4 - {word}"
            ]
            answer = "A"
        else:
            content = f"Choose the correct meaning of the following word: {word}"
            options = [
                "Option 1",
                "Option 2",
                "Option 3",
                "Option 4"
            ]
            answer = "A"

        explanation = f"The correct answer is {answer}"

        question = self._question_manager.create_question(
            content=content,
            answer=answer,
            explanation=explanation,
            category_id=category_id,
            language_id=language_id,
            question_type="single_choice",
            level_id=level_id,
            options=options,
            tags=[difficulty, "single_choice"]
        )

        return question

    def _generate_multiple_choice_question(self, language_id: int, level_id: int,
                                           category_id: int, difficulty: str) -> Question:
        """生成多选题

        Args:
            language_id: 语种ID
            level_id: 等级ID
            category_id: 分类ID
            difficulty: 难度级别

        Returns:
            Question: 生成的题目
        """
        if language_id == 1:
            content = f"次の文で正しい選択肢を全て選んでください.{self._generate_english_statement(difficulty)}"
            options = [
                "選択肢1",
                "選択肢2",
                "選択肢3",
                "選択肢4"
            ]
            explanation = "正しい答えは..."
        else:
            content = f"Choose all correct options for the following sentence: {self._generate_english_statement(difficulty)}"
            options = [
                "Option 1",
                "Option 2",
                "Option 3",
                "Option 4"
            ]
            answer = "AB"
            explanation = "The correct answers are..."

        question = self._question_manager.create_question(
            content=content,
            answer=answer,
            explanation=explanation,
            category_id=category_id,
            language_id=language_id,
            level_id=level_id,
            question_type="multiple_choice",
            options=options,
            tags=[difficulty, "multiple_choice"]
        )

        return question

    def _generate_true_false_question(self, language_id: int, level_id: int,
                                      category_id: int, difficulty: str) -> Question:
        """生成判断题

        Args:
            language_id: 语种ID
            level_id: 等级ID
            category_id: 分类ID
            difficulty: 难度级别

        Returns:
            Question: 生成的题目
        """
        if language_id == 1:
            content = f"次の文が正しいかどうかを判断してください.{self._generate_english_statement(difficulty)}"
            options = ["正しい", "間違っている"]
            answer = "A"
            explanation = "この文は..."
        else:
            content = f"Is the following statement correct? {self._generate_english_statement(difficulty)}"
            options = ["True", "False"]
            answer = "A"
            explanation = "This statement is..."

        question = self._question_manager.create_question(
            content=content,
            answer=answer,
            explanation=explanation,
            category_id=category_id,
            language_id=language_id,
            level_id=level_id,
            question_type="true_false",
            options=options,
            tags=[difficulty, "true_false"]
        )

        return question

    def _generate_fill_blank_question(self, language_id: int, level_id: int,
                                      category_id: int, difficulty: str) -> Question:
        """生成填空题

        Args:
            language_id: 语种ID
            level_id: 等级ID
            category_id: 分类ID
            difficulty: 难度级别

        Returns:
            Question: 生成的题目
        """
        if language_id == 1:
            content = f"次の文の空欄に入る適切な単語を入力してください.{self._generate_english_blank_sentence()}"
            answer = "正解の単語"
            explanation = "正しい答えは..."
        else:
            content = f"Fill in the blank with the appropriate word: {self._generate_english_blank_sentence()}"
            answer = "Correct word"
            explanation = "The correct answer is..."

        question = self._question_manager.create_question(
            content=content,
            answer=answer,
            explanation=explanation,
            category_id=category_id,
            language_id=language_id,
            level_id=level_id,
            question_type="fill_blank",
            tags=[difficulty, "fill_blank"]
        )

        return question

    def _generate_short_answer_question(self, language_id: int, level_id: int,
                                        category_id: int, difficulty: str) -> Question:
        """生成简答题

        Args:
            language_id: 语种ID
            level_id: 等级ID
            category_id: 分类ID
            difficulty: 难度级别

        Returns:
            Question: 生成的题目
        """
        if language_id == 1:
            content = f"次の質問に答えてください.{self._generate_english_question(difficulty)}"
            answer = "正解の回答"
            explanation = "正しい答えは..."
        else:
            content = f"Answer the following question: {self._generate_english_question(difficulty)}"
            answer = "Correct answer"
            explanation = "The correct answer is..."

        question = self._question_manager.create_question(
            content=content,
            answer=answer,
            explanation=explanation,
            category_id=category_id,
            language_id=language_id,
            level_id=level_id,
            question_type="short_answer",
            tags=[difficulty, "short_answer"]
        )

        return question

    def _generate_english_question(self, difficulty: str) -> str:
        """生成英语问题

        Args:
            difficulty: 难度级别

        Returns:
            str: 英语问题
        """
        questions = [
            "What is the capital of France?",
            "How many continents are there?",
            "What is the largest planet in our solar system?",
            "Who wrote 'Romeo and Juliet'?",
            "What is the chemical symbol for water?",
        ]
        return random.choice(questions)

    def _generate_japanese_sentence(self, difficulty: str) -> str:
        """生成日语句子

        Args:
            difficulty: 难度级别

        Returns:
            str: 日语句子
        """
        sentences = {
            "easy": ["私は学生です.", "今日は晴天です.", "猫はかわいいです."],
            "medium": ["昨日は友達と映画を見ました.", "明日は試験があります.", "毎朝散歩しています."],
            "hard": ["この問題は複雑で解決が難しいです.", "彼は仕事で大きな成果を上げました.", "将来の計画を立てる必要があります."]
        }
        return random.choice(sentences.get(difficulty, sentences["easy"]))

    def _generate_english_sentence(self, difficulty: str) -> str:
        """生成英语句子

        Args:
            difficulty: 难度级别

        Returns:
            str: 英语句子
        """
        sentences = {
            "easy": ["I am a student.", "Today is sunny.", "Cats are cute."],
            "medium": ["I watched a movie with friends yesterday.", "I have an exam tomorrow.", "I take a walk every morning."],
            "hard": ["This problem is complex and difficult to solve.", "He achieved great results at work.", "We need to make future plans."]
        }
        return random.choice(sentences.get(difficulty, sentences["easy"]))

    def _generate_japanese_statement(self, difficulty: str) -> str:
        """生成日语陈述

        Args:
            difficulty: 难度级别

        Returns:
            str: 日语陈述
        """
        statements = {
            "easy": ["日本の首都は東京です.", "猫は四本足で歩きます.", "水は透明です."],
            "medium": ["日本語は難しい言語です.", "毎日運動すると健康になります.", "地球は丸いです."],
            "hard": ["量子力学は非常に複雑な学問です.", "経済成長は環境に悪い影響を与えることがあります.", "人工知能は私たちの生活を大きく変えるでしょう."]
        }
        return random.choice(statements.get(difficulty, statements["easy"]))

    def _generate_english_vocabulary(self, difficulty: str) -> str:
        """生成英语词汇

        Args:
            difficulty: 难度级别

        Returns:
            str: 英语词汇
        """
        vocabulary = {
            "easy": ["cat", "dog", "book", "house", "school", "eat", "go", "come", "see"],
            "medium": ["study", "work", "friend", "family", "phone", "computer", "internet", "movie", "music", "sports"],
            "hard": ["recognition", "understanding", "analysis", "integration", "creation", "innovation", "challenge", "breakthrough", "achievement", "transcendence"]
        }
        return random.choice(vocabulary.get(difficulty, vocabulary["easy"]))

    def _generate_japanese_fill_blank(self, difficulty: str) -> str:
        """生成日语填空题

        Args:
            difficulty: 难度级别

        Returns:
            str: 日语填空题
        """
        blanks = {
            "easy": ["昨日は友達と___を見ました.", "毎朝___をしています.", "明日は___があります."],
            "medium": ["___を食べました.", "___に行きました.", "___を書きました."],
            "hard": ["___について研究しました.", "___を分析しました.", "___を創造しました."]
        }
        return random.choice(blanks.get(difficulty, blanks["easy"]))

    def _generate_english_fill_blank(self, difficulty: str) -> str:
        """生成英语填空题

        Args:
            difficulty: 难度级别

        Returns:
            str: 英语填空题
        """
        blanks = {
            "easy": ["I am a___.", "___ are cute.", "Today is___."],
            "medium": ["I watched a___ with friends yesterday.", "I take a___ every morning.", "I have an___ tomorrow."],
            "hard": ["This problem is___ and difficult to solve.", "He achieved great___ at work.", "We need to make future___."]
        }
        return random.choice(blanks.get(difficulty, blanks["easy"]))

    def _generate_listening_question(self, language_id: int, level_id: int,
                                     category_id: int, difficulty: str) -> Question:
        """生成听力题

        Args:
            language_id: 语种ID
            level_id: 等级ID
            category_id: 分类ID
            difficulty: 难度级别

        Returns:
            Question: 生成的题目
        """
        if language_id == 1:
            content = "以下の音声を聞いて,正しい答えを選んでください."
            options = [
                "選択肢1",
                "選択肢2",
                "選択肢3",
                "選択肢4"
            ]
            answer = "A"
            explanation = "正しい答えは..."
            audio_url = f"https://example.com/audio/japanese/{difficulty}.mp3"
        else:
            content = "Listen to the following audio and choose the correct answer."
            options = [
                "Option 1",
                "Option 2",
                "Option 3",
                "Option 4"
            ]
            answer = "A"
            explanation = "The correct answer is..."
            audio_url = f"https://example.com/audio/english/{difficulty}.mp3"

        question = self._question_manager.create_question(
            content=content,
            answer=answer,
            explanation=explanation,
            category_id=category_id,
            language_id=language_id,
            level_id=level_id,
            question_type="listening",
            options=options,
            audio_url=audio_url,
            tags=[difficulty, "listening"]
        )

        return question

    def get_status(self) -> Dict[str, Any]:
        """获取题库拓展系统状态

        Returns:
            Dict[str, Any]: 状态信息
        """
        with self._lock:
            current_bank_status = self._analyze_question_bank()
            return {
                "config": self._config.copy(),
                "status": self._status.copy(),
                "current_bank_status": current_bank_status
            }

    def update_config(self, new_config: Dict[str, Any]):
        """更新配置

        Args:
            new_config: 新配置
        """
        with self._lock:
            self._config.update(new_config)
            logger.info(f"题库拓展系统配置更新: {new_config}")

    def shutdown(self) -> bool:
        """关闭题库拓展系统

        Returns:
            bool: 是否关闭成功
        """
        with self._lock:
            if not self._status["running"]:
                logger.warning("题库拓展系统已经关闭")
                return True
            try:
                logger.info("开始关闭题库拓展系统...")
                self._status["running"] = False
                logger.info("题库拓展系统关闭成功")
                return True
            except Exception as e:
                logger.error(f"题库拓展系统关闭失败: {str(e)}")
                return False


question_bank_expander = QuestionBankExpander()
ai_question_bank_expander = question_bank_expander
