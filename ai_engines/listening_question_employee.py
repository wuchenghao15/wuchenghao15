#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
听力题库专业AI员工
专门负责日语、英语听力题目的生成、整理、更新，包括多口音多难度听力题
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


class ListeningQuestionEmployee:
    """听力题库专业AI员工"""

    def __init__(self, employee_id: str, name: str, level: int = 1):
        self.employee_id = employee_id
        self.name = name
        self.level = level
        self.type = "listening_question"
        self.status = "active"
        self.task_count = 0
        self.success_count = 0
        self.failure_count = 0
        self.performance_score = 80 + level * 2

        self.skills = [
            {"name": "japanese_listening", "level": 5 + level, "experience": 0.0},
            {"name": "english_listening", "level": 5 + level, "experience": 0.0},
            {"name": "dialogue_creation", "level": 5 + level, "experience": 0.0},
            {"name": "accent_variation", "level": 4 + level, "experience": 0.0},
            {"name": "difficulty_control", "level": 4 + level, "experience": 0.0},
            {"name": "audio_script_generation", "level": 5 + level, "experience": 0.0},
            {"name": "comprehension_questions", "level": 4 + level, "experience": 0.0}
        ]

        self._lock = threading.RLock()
        self._db_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'app.db'
        )

        self._languages = {
            "japanese": {
                "name": "日语",
                "accents": ["kanto", "kansai"],
                "accent_names": {"kanto": "关东腔", "kansai": "关西腔"},
                "voices": ["female", "male"],
                "voice_names": {"female": "女声", "male": "男声"},
                "levels": ["N5", "N4", "N3", "N2", "N1"],
                "topics": [
                    "日常生活", "学校生活", "工作职场", "购物消费",
                    "交通出行", "餐饮美食", "旅游观光", "健康医疗",
                    "天气气候", "新闻报道", "文化介绍", "科技发展"
                ]
            },
            "english": {
                "name": "英语",
                "accents": ["us", "uk", "australia", "canada", "india"],
                "accent_names": {
                    "us": "美式", "uk": "英式", "australia": "澳式",
                    "canada": "加拿大", "india": "印度"
                },
                "voices": ["female", "male"],
                "voice_names": {"female": "女声", "male": "男声"},
                "levels": ["初级", "中级", "高级", "专业级"],
                "topics": [
                    "Daily Life", "School & Education", "Work & Business",
                    "Shopping", "Transportation", "Food & Dining",
                    "Travel", "Health", "Weather", "News",
                    "Culture", "Science & Technology"
                ]
            }
        }

        self._japanese_dialogues = {
            "easy": [
                {
                    "topic": "购物",
                    "transcript": "A：すみません、このりんごはいくらですか。\nB：一つ200円です。\nA：じゃ、三つください。",
                    "question": "女の人は何を買いますか。",
                    "options": ["りんご", "ばなな", "みかん", "ぶどう"],
                    "answer": 0
                },
                {
                    "topic": "天気",
                    "transcript": "A：今日はいい天気ですね。\nB：ええ、とても晴れています。\nA：明日も晴れるかな。",
                    "question": "今日の天気はどうですか。",
                    "options": ["晴れ", "雨", "曇り", "雪"],
                    "answer": 0
                }
            ],
            "medium": [
                {
                    "topic": "学校",
                    "transcript": "A：田中さん、明日の試験の準備はできましたか。\nB：まだです。数学が難しくて、なかなか勉強が進まないんです。\nA：そうですか。私も数学は苦手です。一緒に勉強しませんか。\nB：いいですね。じゃ、図書館で午後2時からどうですか。",
                    "question": "二人はどこで勉強しますか。",
                    "options": ["図書館", "教室", "田中さんの家", "カフェ"],
                    "answer": 0
                }
            ],
            "hard": [
                {
                    "topic": "社会問題",
                    "transcript": "近年、高齢化社会の進行に伴い、医療や介護の問題が深刻化しています。政府は様々な施策を講じていますが、問題の解決には時間がかかると見られています。特に、都市部と地方の格差が大きいことが課題となっています。",
                    "question": "この話の内容と合っているものはどれですか。",
                    "options": [
                        "高齢化社会の問題は深刻化している",
                        "医療問題はすでに解決した",
                        "都市部と地方の格差はない",
                        "介護の問題は存在しない"
                    ],
                    "answer": 0
                }
            ]
        }

        self._english_dialogues = {
            "easy": [
                {
                    "topic": "Greetings",
                    "transcript": "A: Good morning! How are you today?\nB: I'm fine, thank you. And you?\nA: I'm great, thanks for asking.",
                    "question": "How is person B feeling?",
                    "options": ["Fine", "Tired", "Sick", "Sad"],
                    "answer": 0
                },
                {
                    "topic": "Shopping",
                    "transcript": "A: How much is this shirt?\nB: It's $25.\nA: OK, I'll take it.",
                    "question": "What does the person want to buy?",
                    "options": ["A shirt", "A dress", "Shoes", "A hat"],
                    "answer": 0
                }
            ],
            "medium": [
                {
                    "topic": "Work",
                    "transcript": "A: Hi Sarah, did you finish the report for the meeting?\nB: Almost. I just need to add some data from last quarter.\nA: When do you think you'll be done?\nB: Probably by 3 PM. I'll send it to you as soon as it's ready.\nA: Great, thanks. The meeting is at 4, so we have time.",
                    "question": "When will Sarah finish the report?",
                    "options": ["By 3 PM", "By 4 PM", "By 5 PM", "Tomorrow"],
                    "answer": 0
                }
            ],
            "hard": [
                {
                    "topic": "Technology",
                    "transcript": "The rapid advancement of artificial intelligence has transformed various industries. From healthcare to finance, AI applications are improving efficiency and enabling new capabilities. However, this technological progress also raises important ethical questions about privacy, employment, and the future of work. Society must carefully consider how to harness these benefits while addressing potential challenges.",
                    "question": "What is the main topic of this passage?",
                    "options": [
                        "The impact of AI on society",
                        "Healthcare technology",
                        "Financial services",
                        "Employment statistics"
                    ],
                    "answer": 0
                }
            ]
        }

        logger.info(f"[听力题库员工] 创建: {self.name} ({self.employee_id}) 级别: {self.level}")

    def start(self):
        """启动员工"""
        self.status = "active"
        logger.info(f"[听力题库员工] {self.name} 已启动")

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
            "supported_languages": list(self._languages.keys())
        }

    def execute_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行任务"""
        self.task_count += 1
        start_time = time.time()

        try:
            task_type = task_data.get("task_type", "generate_listening")

            if task_type == "generate_listening":
                result = self._generate_listening_questions(task_data)
            elif task_type == "generate_japanese":
                result = self._generate_japanese_listening(task_data)
            elif task_type == "generate_english":
                result = self._generate_english_listening(task_data)
            elif task_type == "generate_by_difficulty":
                result = self._generate_by_difficulty(task_data)
            elif task_type == "generate_by_topic":
                result = self._generate_by_topic(task_data)
            elif task_type == "generate_mass":
                result = self._generate_mass_questions(task_data)
            elif task_type == "get_statistics":
                result = self._get_statistics()
            elif task_type == "get_languages":
                result = self._get_languages()
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
            logger.error(f"[听力题库员工] 任务执行失败: {self.name}, 错误: {e}")
            return {
                "success": False,
                "error": str(e),
                "execution_time": time.time() - start_time,
                "employee_id": self.employee_id,
                "employee_name": self.name
            }

    def _generate_listening_questions(self, task_data: Dict) -> Dict:
        """生成听力题目"""
        count = int(task_data.get("count", 50))
        language = task_data.get("language", "all")
        accent = task_data.get("accent", None)
        difficulty = task_data.get("difficulty", None)
        question_type = task_data.get("question_type", "dialogue")

        generated = []
        languages = ["japanese", "english"] if language == "all" else [language]

        try:
            from app.ai.question_bank_ai import get_question_bank_ai
            ai = get_question_bank_ai()

            per_language = max(1, count // len(languages))

            for lang in languages:
                for _ in range(per_language):
                    try:
                        lang_info = self._languages.get(lang, self._languages["english"])
                        ac = accent if accent and accent in lang_info["accents"] else random.choice(lang_info["accents"])
                        voice = random.choice(lang_info["voices"])
                        diff_level = random.randint(1, 4)
                        topic = random.choice(lang_info["topics"])

                        questions = ai.generate_listening_question(
                            language=lang,
                            accent=ac,
                            voice=voice,
                            difficulty=diff_level,
                            topic=self._topic_to_enum(topic, lang),
                            count=1
                        )

                        if questions:
                            generated.extend(questions)
                    except Exception:
                        continue
        except Exception as e:
            logger.warning(f"[听力题库员工] AI生成听力题失败，使用本地生成: {e}")

        if len(generated) == 0:
            try:
                for i in range(count):
                    lang = random.choice(languages)
                    question = self._create_listening_question(lang)
                    if question:
                        generated.append(question)
            except Exception as e:
                logger.error(f"[听力题库员工] 本地生成听力题失败: {e}")
                return {"success": False, "error": str(e), "generated_count": 0}

        return {
            "success": True,
            "message": f"成功生成 {len(generated)} 道听力题",
            "generated_count": len(generated),
            "languages": languages,
            "questions": generated[:count]
        }

    def _create_listening_question(self, language: str) -> Optional[Dict]:
        """创建单个听力题"""
        try:
            lang_info = self._languages.get(language, self._languages["english"])
            accent = random.choice(lang_info["accents"])
            voice = random.choice(lang_info["voices"])
            difficulty = random.choice(["easy", "medium", "hard"])
            topic = random.choice(lang_info["topics"])

            dialogues = self._japanese_dialogues if language == "japanese" else self._english_dialogues
            dialogue_list = dialogues.get(difficulty, dialogues["medium"])
            dialogue = random.choice(dialogue_list)

            question = {
                "type": "single_choice",
                "category": "comprehension",
                "difficulty": difficulty,
                "content": dialogue["question"],
                "options": [{"key": chr(65 + i), "value": opt} for i, opt in enumerate(dialogue["options"])],
                "correct_answer": chr(65 + dialogue["answer"]),
                "explanation": f"听力原文：{dialogue['transcript'][:100]}...",
                "analysis": f"考点：{topic}听力理解",
                "tags": ["听力", language, accent, voice, topic, difficulty],
                "knowledge_points": ["听力理解", topic],
                "source": f"AI生成-{lang_info['name']}听力",
                "score": 2.0 if difficulty == "easy" else (5.0 if difficulty == "medium" else 10.0),
                "language": language,
                "accent": accent,
                "voice": voice,
                "transcript": dialogue["transcript"],
                "topic": topic
            }

            return question

        except Exception as e:
            logger.error(f"[听力题库员工] 创建听力题失败: {e}")
            return None

    def _topic_to_enum(self, topic: str, language: str) -> str:
        """将主题转换为枚举值"""
        topic_map = {
            "japanese": {
                "日常生活": "daily", "学校生活": "campus", "工作职场": "business",
                "购物消费": "daily", "交通出行": "daily", "餐饮美食": "daily",
                "旅游观光": "culture", "健康医疗": "daily", "天气气候": "daily",
                "新闻报道": "news", "文化介绍": "culture", "科技发展": "science"
            },
            "english": {
                "Daily Life": "daily", "School & Education": "campus",
                "Work & Business": "business", "Shopping": "daily",
                "Transportation": "daily", "Food & Dining": "daily",
                "Travel": "culture", "Health": "daily", "Weather": "daily",
                "News": "news", "Culture": "culture", "Science & Technology": "science"
            }
        }

        lang_map = topic_map.get(language, topic_map["english"])
        return lang_map.get(topic, "daily")

    def _generate_japanese_listening(self, task_data: Dict) -> Dict:
        """生成日语听力题"""
        count = int(task_data.get("count", 50))
        task_data["language"] = "japanese"
        result = self._generate_listening_questions(task_data)
        result["message"] = f"成功生成 {result.get('generated_count', 0)} 道日语听力题"
        return result

    def _generate_english_listening(self, task_data: Dict) -> Dict:
        """生成英语听力题"""
        count = int(task_data.get("count", 50))
        task_data["language"] = "english"
        result = self._generate_listening_questions(task_data)
        result["message"] = f"成功生成 {result.get('generated_count', 0)} 道英语听力题"
        return result

    def _generate_by_difficulty(self, task_data: Dict) -> Dict:
        """按难度生成听力题"""
        count = int(task_data.get("count", 30))
        language = task_data.get("language", "all")
        difficulty = int(task_data.get("difficulty", 2))

        generated = []

        try:
            from app.ai.question_bank_ai import get_question_bank_ai
            ai = get_question_bank_ai()

            if language == "all":
                languages = ["japanese", "english"]
            else:
                languages = [language]

            per_language = max(1, count // len(languages))

            for lang in languages:
                lang_info = self._languages.get(lang, self._languages["english"])
                accent = random.choice(lang_info["accents"])
                voice = random.choice(lang_info["voices"])
                topic = random.choice(lang_info["topics"])

                questions = ai.generate_listening_question(
                    language=lang,
                    accent=accent,
                    voice=voice,
                    difficulty=difficulty,
                    topic=self._topic_to_enum(topic, lang),
                    count=per_language
                )

                if questions:
                    generated.extend(questions)

            return {
                "success": True,
                "message": f"成功生成 {len(generated)} 道难度{difficulty}的听力题",
                "generated_count": len(generated),
                "difficulty": difficulty
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _generate_by_topic(self, task_data: Dict) -> Dict:
        """按主题生成听力题"""
        count = int(task_data.get("count", 20))
        language = task_data.get("language", "japanese")
        topic = task_data.get("topic", "daily")

        generated = []

        try:
            from app.ai.question_bank_ai import get_question_bank_ai
            ai = get_question_bank_ai()

            lang_info = self._languages.get(language, self._languages["japanese"])
            accent = random.choice(lang_info["accents"])
            voice = random.choice(lang_info["voices"])

            questions = ai.generate_listening_question(
                language=language,
                accent=accent,
                voice=voice,
                difficulty=2,
                topic=topic,
                count=count
            )

            if questions:
                generated.extend(questions)

            return {
                "success": True,
                "message": f"成功生成 {len(generated)} 道{topic}主题听力题",
                "generated_count": len(generated),
                "topic": topic
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _generate_mass_questions(self, task_data: Dict) -> Dict:
        """批量生成海量听力题"""
        count = int(task_data.get("count", 200))
        languages = task_data.get("languages", ["japanese", "english"])
        accents = task_data.get("accents", ["kanto", "us"])
        voices = task_data.get("voices", ["female", "male"])
        difficulties = task_data.get("difficulties", [1, 2, 3])
        topics = task_data.get("topics", ["daily", "business", "campus"])

        generated = []

        try:
            from app.ai.question_bank_ai import get_question_bank_ai
            ai = get_question_bank_ai()

            per_lang = max(1, count // len(languages))

            for lang in languages:
                for i in range(per_lang):
                    try:
                        accent = random.choice(accents)
                        voice = random.choice(voices)
                        difficulty = random.choice(difficulties)
                        topic = random.choice(topics)

                        questions = ai.generate_listening_question(
                            language=lang,
                            accent=accent,
                            voice=voice,
                            difficulty=difficulty,
                            topic=topic,
                            count=1
                        )

                        if questions:
                            generated.extend(questions)
                    except Exception:
                        continue

            return {
                "success": True,
                "message": f"批量生成完成，共 {len(generated)} 道听力题",
                "generated_count": len(generated),
                "config": {
                    "languages": languages,
                    "accents": accents,
                    "voices": voices,
                    "difficulties": difficulties,
                    "topics": topics
                }
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _get_statistics(self) -> Dict:
        """获取统计信息"""
        try:
            from app.ai.question_bank_ai import get_question_bank_ai
            ai = get_question_bank_ai()
            stats = ai.get_statistics()

            return {
                "success": True,
                "statistics": {
                    "total_questions": stats.total_questions,
                    "listening_questions": stats.listening_questions,
                    "by_language": stats.by_language,
                    "by_accent": stats.by_accent,
                    "by_difficulty": stats.by_difficulty,
                    "avg_correct_rate": stats.avg_correct_rate
                }
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _get_languages(self) -> Dict:
        """获取语言配置"""
        return {
            "success": True,
            "languages": self._languages,
            "total_languages": len(self._languages)
        }

    def _update_performance(self, success: bool, duration: float):
        """更新绩效"""
        if success:
            self.performance_score = min(100, self.performance_score + 0.5)
            for skill in self.skills:
                skill["experience"] += 0.1
        else:
            self.performance_score = max(60, self.performance_score - 0.3)


def create_listening_question_employee(employee_id: str = None,
                                        name: str = "听力题库AI",
                                        level: int = 5) -> ListeningQuestionEmployee:
    """创建听力题库AI员工"""
    if not employee_id:
        employee_id = f"list_{uuid.uuid4().hex[:8]}"
    return ListeningQuestionEmployee(employee_id, name, level)
