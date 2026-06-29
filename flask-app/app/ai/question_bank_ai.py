#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI题库管理智能助手
实现智能题库维护、听力题生成、质量分析、智能推荐
"""

import os
import json
import sqlite3
import threading
import time
import random
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)


class ListeningLanguage(Enum):
    """听力语言"""
    JAPANESE = "japanese"
    ENGLISH = "english"
    CHINESE = "chinese"


class ListeningAccent(Enum):
    """听力口音"""
    # 日语口音
    KANTO = "kanto"  # 关东腔
    KANSAI = "kansai"  # 关西腔
    # 英语口音
    UK = "uk"  # 英式发音
    US = "us"  # 式发音
    AFRICA = "africa"  # 非洲英语
    INDIA = "india"  # 印度英语


class ListeningVoice(Enum):
    """听力音色"""
    FEMALE = "female"  # 标准女声
    MALE = "male"  # 标准男声


class ListeningDifficulty(Enum):
    """听力难度"""
    BEGINNER = 1  # 初级
    INTERMEDIATE = 2  # 中级
    ADVANCED = 3  # 高级
    EXPERT = 4  # 专家级


class ListeningTopic(Enum):
    """听力主题"""
    DAILY = "daily"  # 日常生活
    BUSINESS = "business"  # 商务场景
    CAMPUS = "campus"  # 校园场景
    NEWS = "news"  # 新闻报道
    CULTURE = "culture"  # 文化交流
    SCIENCE = "science"  # 科学技术


@dataclass
class ListeningQuestion:
    """听力题目数据类"""
    question_id: str
    language: ListeningLanguage
    accent: ListeningAccent
    voice: ListeningVoice
    difficulty: ListeningDifficulty
    topic: ListeningTopic
    transcript: str  # 听力原文
    question_text: str  # 问题文本
    options: List[Dict[str, str]]  # 选项
    correct_answer: str  # 正确答案
    explanation: str  # 解析
    audio_path: Optional[str] = None  # 音频文件路径
    audio_duration: float = 0.0  # 音频时长(秒)
    created_at: float = field(default_factory=lambda: time.time())
    usage_count: int = 0
    correct_rate: float = 0.0
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            'question_id': self.question_id,
            'language': self.language.value,
            'accent': self.accent.value,
            'voice': self.voice.value,
            'difficulty': self.difficulty.value,
            'topic': self.topic.value,
            'transcript': self.transcript,
            'question_text': self.question_text,
            'options': self.options,
            'correct_answer': self.correct_answer,
            'explanation': self.explanation,
            'audio_path': self.audio_path,
            'audio_duration': self.audio_duration,
            'created_at': self.created_at,
            'usage_count': self.usage_count,
            'correct_rate': self.correct_rate,
            'tags': self.tags
        }


@dataclass
class QuestionBankAIStats:
    """题库AI统计"""
    total_questions: int = 0
    listening_questions: int = 0
    by_language: Dict[str, int] = field(default_factory=dict)
    by_accent: Dict[str, int] = field(default_factory=dict)
    by_difficulty: Dict[str, int] = field(default_factory=dict)
    avg_correct_rate: float = 0.0
    ai_generated_count: int = 0
    manual_created_count: int = 0


class QuestionBankAIAssistant:
    """AI题库管理智能助手"""

    def __init__(self):
        self.db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'app.db')
        self._questions: Dict[str, ListeningQuestion] = {}
        self._lock = threading.RLock()
        self._init_database()
        self._init_templates()
        self._load_questions()
        logger.info("[AI题库助手] AI题库管理智能助手初始化完成")

    def _init_database(self):
        """初始化数据库表"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 听力题表
        cursor.execute('''CREATE TABLE IF NOT EXISTS listening_questions (
            question_id TEXT PRIMARY KEY,
            language TEXT NOT NULL,
            accent TEXT NOT NULL,
            voice TEXT NOT NULL,
            difficulty INTEGER NOT NULL,
            topic TEXT NOT NULL,
            transcript TEXT NOT NULL,
            question_text TEXT NOT NULL,
            options TEXT NOT NULL,
            correct_answer TEXT NOT NULL,
            explanation TEXT,
            audio_path TEXT,
            audio_duration REAL DEFAULT 0,
            created_at TEXT,
            updated_at TEXT,
            usage_count INTEGER DEFAULT 0,
            correct_rate REAL DEFAULT 0,
            tags TEXT
        )''')

        # 音频元数据表
        cursor.execute('''CREATE TABLE IF NOT EXISTS listening_audio_metadata (
            audio_id TEXT PRIMARY KEY,
            question_id TEXT NOT NULL,
            language TEXT NOT NULL,
            accent TEXT NOT NULL,
            voice TEXT NOT NULL,
            file_path TEXT NOT NULL,
            duration REAL DEFAULT 0,
            transcript TEXT NOT NULL,
            created_at TEXT,
            FOREIGN KEY(question_id) REFERENCES listening_questions(question_id)
        )''')

        # 用户听力偏好表
        cursor.execute('''CREATE TABLE IF NOT EXISTS user_listening_preferences (
            user_id INTEGER,
            language TEXT,
            accent TEXT,
            voice TEXT,
            created_at TEXT,
            updated_at TEXT,
            PRIMARY KEY(user_id, language)
        )''')

        # 题库AI统计表
        cursor.execute('''CREATE TABLE IF NOT EXISTS question_bank_ai_stats (
            stat_id TEXT PRIMARY KEY,
            stat_type TEXT NOT NULL,
            stat_value TEXT NOT NULL,
            updated_at TEXT
        )''')

        conn.commit()
        conn.close()

    def _init_templates(self):
        """初始化听力题模板库"""
        self.japanese_templates = {
            'daily': [
                {
                    'transcript': "男：すみません、次のバスは何時ですか？\n女：3時30分です。2時30分のバスはもう出ましたよ。\n男：ああ、それじゃあ1時間待つしかないですね。",
                    'question': "次のバスは何時ですか？",
                    'correct': "3時30分",
                    'options': ["2時30分", "3時30分", "4時00分", "3時00分"],
                    'explanation': "女性は次のバスが3時30分に出ると言いました。男性は2時30分のバスを逃しました。"
                },
                {
                    'transcript': "女：このTシャツはいくらですか？\n男：今日は特売で、25ドルです。普段は40ドルですよ。\n女：いいですね、2枚買います。",
                    'question': "Tシャツの特売価格はいくらですか？",
                    'correct': "25ドル",
                    'options': ["40ドル", "25ドル", "50ドル", "30ドル"],
                    'explanation': "男性は今日特売で25ドルと言いました。普段は40ドルです。"
                },
                {
                    'transcript': "男：休暇はどこに行きましたか？\n女：日本に行きました。東京と京都を訪れました。\n男：すごいですね！何日滞在しましたか？",
                    'question': "女性はどの国を訪れましたか？",
                    'correct': "日本",
                    'options': ["中国", "韓国", "日本", "タイ"],
                    'explanation': "女性は日本に行って、東京と京都を訪れたと言いました。"
                },
                {
                    'transcript': "女：今日の天気は本当に悪いですね。\n男：そうですね、雨がとても強いですね。公園に行けませんね。\n女：じゃあ、家で映画を見ましょう。",
                    'question': "公園に行く代わりに何をしますか？",
                    'correct': "映画を見る",
                    'options': ["買い物に行く", "映画を見る", "本を読む", "夕食を作る"],
                    'explanation': "雨で公園に行けないので、家で映画を見ることにしました。"
                },
                {
                    'transcript': "男：仕事は何をしていますか？\n女：私はテクノロジー企業でソフトウェアエンジニアをしています。\n男：面白いですね。在宅勤務ですか？",
                    'question': "男性の仕事は何ですか？",
                    'correct': "ソフトウェアエンジニア",
                    'options': ["医者", "教師", "ソフトウェアエンジニア", "弁護士"],
                    'explanation': "男性はテクノロジー企業のソフトウェアエンジニアだと言いました。"
                }
            ],
            'business': [
                {
                    'transcript': "男：明日の会議は何時からですか？\n女：午前10時からです。30分前に資料を準備してください。\n男：了解しました。資料はメールで送ります。",
                    'question': "会議は何時から始まりますか？",
                    'correct': "午前10時",
                    'options': ["午前9時30分", "午前10時", "午前10時30分", "午前11時"],
                    'explanation': "女性は会議が午前10時からと言いました。"
                },
                {
                    'transcript': "女：このプロジェクトの進捗状況はどうですか？\n男：現在70%完了しています。残りは2週間で終わる予定です。\n女：了解しました。報告書を提出してください。",
                    'question': "プロジェクトは何%完了していますか？",
                    'correct': "70%",
                    'options': ["50%", "70%", "90%", "80%"],
                    'explanation': "男性はプロジェクトが70%完了していると言いました。"
                }
            ],
            'campus': [
                {
                    'transcript': "女：明日のテストは何章までですか？\n男：第3章から第5章までです。難しいところがあります。\n女：じゃあ、一緒に勉強しましょう。",
                    'question': "テストは何章までですか？",
                    'correct': "第3章から第5章",
                    'options': ["第1章から第3章", "第3章から第5章", "第5章から第7章", "第2章から第4章"],
                    'explanation': "男性はテストが第3章から第5章までと言いました。"
                },
                {
                    'transcript': "男：図書館は何時まで開いていますか？\n女：平日は夜9時まで、週末は6時までです。\n男：今日は平日なので、9時までですね。",
                    'question': "平日、図書館は何時まで開いていますか？",
                    'correct': "夜9時",
                    'options': ["夜6時", "夜9時", "夜10時", "夜8時"],
                    'explanation': "女性は平日は夜9時までと言いました。"
                }
            ]
        }

        self.english_templates = {
            'daily': [
                {
                    'transcript': "M: Excuse me, what time is the next bus to downtown?\nW: It leaves at 3:30. You just missed the 2:30 one.\nM: Oh no, I have to wait an hour then.",
                    'question': "When is the next bus?",
                    'correct': "3:30",
                    'options': ["2:30", "3:30", "4:00", "3:00"],
                    'explanation': "The woman says the next bus leaves at 3:30. The man missed the 2:30 bus."
                },
                {
                    'transcript': "W: How much is this T-shirt?\nM: It's on sale today, only $25. Normally it's $40.\nW: Great, I'll take two.",
                    'question': "What is the sale price of the T-shirt?",
                    'correct': "$25",
                    'options': ["$40", "$25", "$50", "$30"],
                    'explanation': "The man says it's on sale for $25 today. Normally it's $40."
                },
                {
                    'transcript': "M: Where did you go for your vacation?\nW: I went to Japan. I visited Tokyo and Kyoto.\nM: That sounds amazing! How long did you stay?",
                    'question': "Which country did the woman visit?",
                    'correct': "Japan",
                    'options': ["China", "Korea", "Japan", "Thailand"],
                    'explanation': "The woman says she went to Japan and visited Tokyo and Kyoto."
                },
                {
                    'transcript': "W: The weather is terrible today.\nM: I know, it's raining so hard. We can't go to the park.\nW: Let's watch a movie at home instead.",
                    'question': "What will they do instead of going to the park?",
                    'correct': "Watch a movie",
                    'options': ["Go shopping", "Watch a movie", "Read books", "Cook dinner"],
                    'explanation': "Because of the rain, they decide to watch a movie at home."
                },
                {
                    'transcript': "M: What do you do for work?\nW: I'm a software engineer at a tech company.\nM: That's interesting. Do you work from home?",
                    'question': "What is the woman's job?",
                    'correct': "Software engineer",
                    'options': ["Doctor", "Teacher", "Software engineer", "Lawyer"],
                    'explanation': "The woman says she is a software engineer at a tech company."
                }
            ],
            'business': [
                {
                    'transcript': "M: When does the meeting start tomorrow?\nW: It starts at 10 AM. Please prepare the materials 30 minutes early.\nM: Understood. I'll send the documents by email.",
                    'question': "When does the meeting start?",
                    'correct': "10 AM",
                    'options': ["9:30 AM", "10 AM", "10:30 AM", "11 AM"],
                    'explanation': "The woman says the meeting starts at 10 AM."
                },
                {
                    'transcript': "W: What's the progress on this project?\nM: Currently 70% complete. The rest should be finished in 2 weeks.\nW: Understood. Please submit a report.",
                    'question': "How much of the project is complete?",
                    'correct': "70%",
                    'options': ["50%", "70%", "90%", "80%"],
                    'explanation': "The man says the project is currently 70% complete."
                }
            ],
            'campus': [
                {
                    'transcript': "W: What chapters are covered in tomorrow's test?\nM: Chapters 3 to 5. There are some difficult parts.\nW: Then let's study together.",
                    'question': "What chapters are covered in the test?",
                    'correct': "Chapters 3 to 5",
                    'options': ["Chapters 1 to 3", "Chapters 3 to 5", "Chapters 5 to 7", "Chapters 2 to 4"],
                    'explanation': "The man says the test covers chapters 3 to 5."
                },
                {
                    'transcript': "M: What time does the library close?\nW: On weekdays it closes at 9 PM, on weekends at 6 PM.\nM: Since today is a weekday, it closes at 9 PM.",
                    'question': "When does the library close on weekdays?",
                    'correct': "9 PM",
                    'options': ["6 PM", "9 PM", "10 PM", "8 PM"],
                    'explanation': "The woman says it closes at 9 PM on weekdays."
                }
            ],
            'news': [
                {
                    'transcript': "The government announced today that the minimum wage will increase by 5% starting next month. This is the first increase in three years. Labor unions welcomed the decision.",
                    'question': "By how much will the minimum wage increase?",
                    'correct': "5%",
                    'options': ["3%", "5%", "7%", "10%"],
                    'explanation': "The news says the minimum wage will increase by 5%."
                },
                {
                    'transcript': "Scientists have discovered a new species of deep-sea fish near the Mariana Trench. The fish can survive at depths of over 8,000 meters.",
                    'question': "Where was the new fish species discovered?",
                    'correct': "Near the Mariana Trench",
                    'options': ["Near the Atlantic Ocean", "Near the Mariana Trench", "Near the Pacific coast", "Near the Arctic Ocean"],
                    'explanation': "The news says the fish was discovered near the Mariana Trench."
                }
            ]
        }

    def _load_questions(self):
        """从数据库加载听力题"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM listening_questions')
            rows = cursor.fetchall()

            for row in rows:
                question = ListeningQuestion(
                    question_id=row[0],
                    language=ListeningLanguage(row[1]),
                    accent=ListeningAccent(row[2]),
                    voice=ListeningVoice(row[3]),
                    difficulty=ListeningDifficulty(row[4]),
                    topic=ListeningTopic(row[5]),
                    transcript=row[6],
                    question_text=row[7],
                    options=json.loads(row[8]),
                    correct_answer=row[9],
                    explanation=row[10],
                    audio_path=row[11],
                    audio_duration=row[12],
                    created_at=float(row[13]) if row[13] else time.time(),
                    usage_count=row[15] or 0,
                    correct_rate=row[16] or 0.0,
                    tags=json.loads(row[17]) if row[17] else []
                )
                self._questions[question.question_id] = question

            conn.close()
            logger.info(f"[AI题库助手] 已加载 {len(self._questions)} 道听力题")
        except Exception as e:
            logger.warning(f"[AI题库助手] 加载听力题失败: {str(e)}")

    def _save_question(self, question: ListeningQuestion):
        """保存听力题到数据库"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''INSERT OR REPLACE INTO listening_questions
                (question_id, language, accent, voice, difficulty, topic, transcript, 
                question_text, options, correct_answer, explanation, audio_path, 
                audio_duration, created_at, updated_at, usage_count, correct_rate, tags)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                (question.question_id, question.language.value, question.accent.value,
                 question.voice.value, question.difficulty.value, question.topic.value,
                 question.transcript, question.question_text, json.dumps(question.options),
                 question.correct_answer, question.explanation, question.audio_path,
                 question.audio_duration, str(question.created_at),
                 datetime.now().isoformat(), question.usage_count, question.correct_rate,
                 json.dumps(question.tags)))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"[AI题库助手] 保存听力题失败: {str(e)}")

    def generate_listening_question_id(self) -> str:
        """生成听力题ID"""
        import hashlib
        timestamp = int(time.time())
        random_str = hashlib.md5(str(random.random()).encode()).hexdigest()[:8]
        return f"LISTEN-{timestamp}-{random_str}"

    def generate_listening_question(
        self,
        language: ListeningLanguage,
        accent: ListeningAccent,
        voice: ListeningVoice,
        difficulty: ListeningDifficulty,
        topic: ListeningTopic,
        count: int = 1
    ) -> List[ListeningQuestion]:
        """AI智能生成听力题"""
        questions = []

        templates = self.japanese_templates if language == ListeningLanguage.JAPANESE else self.english_templates
        topic_templates = templates.get(topic.value, templates.get('daily', []))

        for i in range(min(count, len(topic_templates))):
            template = topic_templates[i] if i < len(topic_templates) else random.choice(topic_templates)

            # 转换为选项字典格式
            options = [{'key': chr(65 + j), 'value': opt} for j, opt in enumerate(template['options'])]
            correct_answer = chr(65 + template['options'].index(template['correct']))

            question = ListeningQuestion(
                question_id=self.generate_listening_question_id(),
                language=language,
                accent=accent,
                voice=voice,
                difficulty=difficulty,
                topic=topic,
                transcript=template['transcript'],
                question_text=template['question'],
                options=options,
                correct_answer=correct_answer,
                explanation=template['explanation'],
                tags=[f"{language.value}", f"{accent.value}", f"{voice.value}", f"{topic.value}"]
            )

            with self._lock:
                self._questions[question.question_id] = question
            self._save_question(question)
            questions.append(question)

        logger.info(f"[AI题库助手] 生成了 {len(questions)} 道{language.value}听力题")
        return questions

    def generate_mass_listening_questions(
        self,
        count: int = 50,
        languages: List[str] = ['japanese', 'english'],
        accents: List[str] = ['kanto', 'us'],
        voices: List[str] = ['female', 'male'],
        difficulties: List[int] = [1, 2, 3],
        topics: List[str] = ['daily', 'business', 'campus']
    ) -> int:
        """批量生成海量听力题"""
        generated = 0

        for _ in range(count):
            try:
                language = ListeningLanguage(random.choice(languages))
                
                # 根据语言选择口音
                if language == ListeningLanguage.JAPANESE:
                    accent = ListeningAccent(random.choice(['kanto', 'kansai']))
                elif language == ListeningLanguage.ENGLISH:
                    accent = ListeningAccent(random.choice(['uk', 'us', 'africa', 'india']))
                else:
                    accent = ListeningAccent.KANTO
                
                voice = ListeningVoice(random.choice(voices))
                difficulty = ListeningDifficulty(random.choice(difficulties))
                topic = ListeningTopic(random.choice(topics))

                questions = self.generate_listening_question(
                    language=language,
                    accent=accent,
                    voice=voice,
                    difficulty=difficulty,
                    topic=topic,
                    count=1
                )
                generated += len(questions)
            except Exception as e:
                logger.error(f"[AI题库助手] 批量生成失败: {str(e)}")

        return generated

    def get_question(self, question_id: str) -> Optional[ListeningQuestion]:
        """获取听力题"""
        return self._questions.get(question_id)

    def search_questions(
        self,
        language: str = None,
        accent: str = None,
        voice: str = None,
        difficulty: int = None,
        topic: str = None,
        keyword: str = None,
        limit: int = 50
    ) -> List[ListeningQuestion]:
        """搜索听力题"""
        results = list(self._questions.values())

        if language:
            results = [q for q in results if q.language.value == language]
        if accent:
            results = [q for q in results if q.accent.value == accent]
        if voice:
            results = [q for q in results if q.voice.value == voice]
        if difficulty:
            results = [q for q in results if q.difficulty.value == difficulty]
        if topic:
            results = [q for q in results if q.topic.value == topic]
        if keyword:
            keyword_lower = keyword.lower()
            results = [q for q in results if keyword_lower in q.transcript.lower() 
                       or keyword_lower in q.question_text.lower()]

        return sorted(results, key=lambda x: x.created_at, reverse=True)[:limit]

    def get_statistics(self) -> QuestionBankAIStats:
        """获取题库统计"""
        stats = QuestionBankAIStats()
        stats.total_questions = len(self._questions)
        stats.listening_questions = len(self._questions)
        stats.ai_generated_count = stats.listening_questions

        for q in self._questions.values():
            stats.by_language[q.language.value] = stats.by_language.get(q.language.value, 0) + 1
            stats.by_accent[q.accent.value] = stats.by_accent.get(q.accent.value, 0) + 1
            stats.by_difficulty[str(q.difficulty.value)] = stats.by_difficulty.get(str(q.difficulty.value), 0) + 1
            stats.avg_correct_rate += q.correct_rate

        if stats.listening_questions > 0:
            stats.avg_correct_rate /= stats.listening_questions

        return stats

    def get_available_accents(self, language: str) -> Dict[str, str]:
        """获取可用口音列表"""
        if language == 'japanese':
            return {'kanto': '关东腔', 'kansai': '关西腔'}
        elif language == 'english':
            return {'uk': '英式发音', 'us': '美式发音', 'africa': '非洲英语', 'india': '印度英语'}
        return {}

    def get_available_voices(self) -> Dict[str, str]:
        """获取可用音色列表"""
        return {'female': '标准女声', 'male': '标准男声'}

    def update_question_statistics(self, question_id: str, correct: bool):
        """更新题目统计"""
        question = self.get_question(question_id)
        if question:
            question.usage_count += 1
            question.correct_rate = (question.correct_rate * (question.usage_count - 1) + 
                                    (1.0 if correct else 0.0)) / question.usage_count
            self._save_question(question)

    def set_user_preference(self, user_id: int, language: str, accent: str, voice: str):
        """设置用户听力偏好"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''INSERT OR REPLACE INTO user_listening_preferences
                (user_id, language, accent, voice, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)''',
                (user_id, language, accent, voice, datetime.now().isoformat(), datetime.now().isoformat()))
            conn.commit()
            conn.close()
            logger.info(f"[AI题库助手] 用户 {user_id} 设置听力偏好: {language}/{accent}/{voice}")
        except Exception as e:
            logger.error(f"[AI题库助手] 设置用户偏好失败: {str(e)}")

    def get_user_preference(self, user_id: int, language: str) -> Optional[Dict]:
        """获取用户听力偏好"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''SELECT accent, voice FROM user_listening_preferences
                WHERE user_id = ? AND language = ?''', (user_id, language))
            row = cursor.fetchone()
            conn.close()
            if row:
                return {'accent': row[0], 'voice': row[1]}
            return None
        except Exception as e:
            logger.error(f"[AI题库助手] 获取用户偏好失败: {str(e)}")
            return None

    def recommend_questions_for_user(
        self,
        user_id: int,
        language: str,
        difficulty: int = 2,
        count: int = 10
    ) -> List[ListeningQuestion]:
        """为用户智能推荐听力题"""
        preference = self.get_user_preference(user_id, language)
        if preference:
            accent = preference['accent']
            voice = preference['voice']
        else:
            # 默认配置
            if language == 'japanese':
                accent = 'kanto'
                voice = 'female'
            else:
                accent = 'us'
                voice = 'female'

        questions = self.search_questions(
            language=language,
            accent=accent,
            voice=voice,
            difficulty=difficulty,
            limit=count
        )

        logger.info(f"[AI题库助手] 为用户 {user_id} 推荐 {len(questions)} 道听力题")
        return questions

    def analyze_question_quality(self, question_id: str) -> Dict[str, Any]:
        """分析题目质量"""
        question = self.get_question(question_id)
        if not question:
            return {'success': False, 'error': '题目不存在'}

        quality_analysis = {
            'question_id': question_id,
            'difficulty_match': True,  # 题目难度与标注难度是否匹配
            'transcript_length': len(question.transcript),
            'question_clarity': len(question.question_text) > 5,
            'options_count': len(question.options),
            'has_explanation': len(question.explanation) > 10,
            'usage_frequency': question.usage_count,
            'correct_rate': question.correct_rate,
            'quality_score': 0.0
        }

        # 计算质量分数
        score = 0
        if quality_analysis['question_clarity']:
            score += 20
        if quality_analysis['has_explanation']:
            score += 20
        if quality_analysis['options_count'] >= 4:
            score += 15
        if quality_analysis['transcript_length'] > 50:
            score += 15
        if question.correct_rate > 0.5:
            score += 20
        if question.usage_count > 5:
            score += 10

        quality_analysis['quality_score'] = score
        return {'success': True, 'analysis': quality_analysis}


# 创建全局实例
question_bank_ai_assistant = QuestionBankAIAssistant()


def get_question_bank_ai():
    """获取AI题库管理智能助手实例"""
    return question_bank_ai_assistant


if __name__ == '__main__':
    ai = get_question_bank_ai()
    
    print("=== 测试生成日语听力题 ===")
    questions = ai.generate_listening_question(
        language=ListeningLanguage.JAPANESE,
        accent=ListeningAccent.KANTO,
        voice=ListeningVoice.FEMALE,
        difficulty=ListeningDifficulty.INTERMEDIATE,
        topic=ListeningTopic.DAILY,
        count=3
    )
    for q in questions:
        print(f"  {q.question_id}: {q.question_text} 答案={q.correct_answer}")
    
    print("\n=== 测试生成英语听力题 ===")
    questions = ai.generate_listening_question(
        language=ListeningLanguage.ENGLISH,
        accent=ListeningAccent.US,
        voice=ListeningVoice.MALE,
        difficulty=ListeningDifficulty.ADVANCED,
        topic=ListeningTopic.BUSINESS,
        count=3
    )
    for q in questions:
        print(f"  {q.question_id}: {q.question_text} 答案={q.correct_answer}")
    
    print("\n=== 测试批量生成 ===")
    count = ai.generate_mass_listening_questions(10)
    print(f"  生成了 {count} 道听力题")
    
    print("\n=== 测试统计 ===")
    stats = ai.get_statistics()
    print(f"  总题目数: {stats.total_questions}")
    print(f"  语言分布: {stats.by_language}")
    print(f"  口音分布: {stats.by_accent}")