#!/usr/bin/env python3
"""
独立的题库扩充脚本，不依赖Flask应用，直接操作数据库
生成各种题型的题目，包括听力题，丰富题库内容

import sqlite3
# JSON import removed - using database
import random
import os
from datetime import datetime

# 数据库路径
DATABASE_PATH = os.path.join(os.path.dirname(__file__), 'instance', 'mtscos_ai.db')

class QuestionBankExpander:
    """题库扩充器，使用AI脑图概念生成各种题型的题目"""

    def __init__(self):
        # AI脑图概念 - 题库分类结构
        self.brain_map = {
            "japanese": {
                "categories": {
                    "日常对话": {
                        "topics": ["问候与介绍", "购物", "餐厅", "交通", "住宿", "天气", "健康", "兴趣爱好"],
                        "difficulty_levels": {"beginner": 0.4, "intermediate": 0.4, "advanced": 0.2}
                    },
                    "商务日语": {
                        "topics": ["职场礼仪", "商务会议", "邮件写作", "谈判技巧", "产品介绍"],
                        "difficulty_levels": {"intermediate": 0.5, "advanced": 0.5}
                    },
                        "topics": ["论文写作", "学术演讲", "研究方法", "专业术语"],
                        "difficulty_levels": {"advanced": 0.6, "expert": 0.4}
                    }
                },
            },
                "categories": {
                        "topics": ["Greetings", "Shopping", "Restaurant", "Transportation", "Accommodation", "Weather", "Health", "Hobbies"],
                        "difficulty_levels": {"beginner": 0.4, "intermediate": 0.4, "advanced": 0.2}
                    },
                        "topics": ["Business Etiquette", "Meetings", "Email Writing", "Negotiation", "Product Presentation"],
                    },
                    "学术英语": {
                        "topics": ["Academic Writing", "Presentations", "Research Methods", "Technical Terms"],
                    }
                },
                "question_types": ["multiple_choice", "fill_in_blank", "true_false", "short_answer", "listening"]

        # 生成的题目计数
        self.generated_counts = {
            "japanese": {"multiple_choice": 0, "fill_in_blank": 0, "true_false": 0, "short_answer": 0, "listening": 0},
        }
    def _connect_db(self):
        """连接数据库"""
        """创建题目表（如果不存在），并添加缺失的列"""
        conn = self._connect_db()
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                language TEXT NOT NULL,
                level TEXT NOT NULL,
                category TEXT NOT NULL,
                content TEXT NOT NULL,
                options TEXT NOT NULL,
                correct_answer TEXT NOT NULL,
                explanation TEXT,
                source TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                usage_count INTEGER DEFAULT 0,
                last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                accuracy REAL DEFAULT NULL,
                question_type TEXT DEFAULT 'multiple_choice' NOT NULL,
                audio_url TEXT,
                transcript TEXT,
                listening_context TEXT
            )
        ''')

        # 检查并添加缺失的字段
        cursor.execute("PRAGMA table_info(questions)")
        columns = [column[1] for column in cursor.fetchall()]

        # 需要添加的字段列表
        fields_to_add = [
            ('question_type', 'TEXT DEFAULT "multiple_choice" NOT NULL'),
            ('audio_url', 'TEXT'),
            ('transcript', 'TEXT'),
            ('listening_context', 'TEXT')
        ]

        for field_name, field_type in fields_to_add:
            if field_name not in columns:
                cursor.execute(f'ALTER TABLE questions ADD COLUMN {field_name} {field_type}')
                print(f"已添加缺失字段: {field_name}")

        conn.commit()
        conn.close()
        print("题目表检查/创建完成")

    def _calculate_similarity(self, str1, str2):
        """计算两个字符串的相似度，使用词级Jaccard相似度算法"""
        import re

        # 处理英语（按空格分词）和日语（按字符分词但保留单词结构）
        # 使用正则表达式匹配单词或汉字
        if any('\u4e00' <= c <= '\u9fff' for c in str1) or any('\u4e00' <= c <= '\u9fff' for c in str2):
            # 包含中文或日语，按字符和单词分词
            # 匹配汉字、假名和英文单词
            words1 = re.findall(r'[\u4e00-\u9fff]+|[\u3040-\u309f\u30a0-\u30ff]+|[a-zA-Z]+', str1.lower())
            words2 = re.findall(r'[\u4e00-\u9fff]+|[\u3040-\u309f\u30a0-\u30ff]+|[a-zA-Z]+', str2.lower())
        else:
            # 英语，按空格分词
            words1 = str1.lower().split()
            words2 = str2.lower().split()

        # 转换为词集合
        set1 = set(words1)
        set2 = set(words2)

        # 计算交集和并集
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))

        # 避免除以零
        if union == 0:
            return 0.0

        # 计算Jaccard相似度
        return intersection / union

    def _is_duplicate_question(self, content, language, category, similarity_threshold=0.8):
        """检查题目是否重复或相似"""
        conn = self._connect_db()
        cursor = conn.cursor()

        try:
            # 1. 首先进行精确匹配检查
            cursor.execute('''
                SELECT COUNT(*) FROM questions
                WHERE language = ?
                AND category = ?
                AND LOWER(content) = LOWER(?)
                LIMIT 1
            ''', (language, category, content))

            count = cursor.fetchone()[0]
            if count > 0:
                return True
            # 2. 如果没有精确匹配，进行相似度检测
            cursor.execute('''
                SELECT content FROM questions
                WHERE language = ?
                AND category = ?
            ''', (language, category))

            existing_contents = [row[0] for row in cursor.fetchall()]

            # 计算与现有题目的相似度
            for existing_content in existing_contents:
                similarity = self._calculate_similarity(content, existing_content)
                if similarity >= similarity_threshold:
                    return True

            return False
        finally:
            conn.close()

    def generate_japanese_multiple_choice(self, category, topic, level):
        """生成日语选择题"""
        templates = [
                "question": "{context}、どう言いますか？",
                "options": ["{option1}", "{option2}", "{option3}", "{option4}"],
                "answer": "{answer}",
                "explanation": "{explanation}"
            },
            {
                "question": "{context}の正しい表現はどれですか？",
                "answer": "{answer}",
                "explanation": "{explanation}"
        ]

        # 根据主题和难度生成具体题目
        if category == "日常对话" and topic == "问候与介绍":
            contexts = [
                "朝、先生に会ったとき",
                "初めて人に会ったとき",
                "お客様を迎えるとき",
                "友人と久しぶりに会ったとき"
            ]

                {
                    "context": contexts[0],
                    "options": ["おはようございます", "こんにちは", "こんばんは", "おやすみなさい"],
                    "answer": "おはようございます",
                    "explanation": "朝の挨拶は'おはようございます'です。"
                {
                    "context": contexts[1],
                }
        elif category == "日常对话" and topic == "餐厅":
                {
                    "context": "レストランで注文するとき",
                    "options": ["メニューをください", "お会計をください", "トイレはどこですか", "これをください"],
                    "explanation": "レストランで注文する前にメニューをもらうときは'メニューをください'と言います。"
                }
            ]
        else:
            # 默认题目
                {
                    "context": f"{topic}に関する質問",
                    "answer": "選択肢1",
                    "explanation": "これは正しい答えです。"
                }
            ]

        """生成英语选择题"""
        questions = [
            {
                "context": f"{topic} related question",
                "options": ["Option A", "Option B", "Option C", "Option D"],
                "answer": "Option A",
                "explanation": "This is the correct answer."
            {
                "explanation": "This is the appropriate response."
            }
        ]

    def generate_fill_in_blank(self, language, category, topic, level):
        if language == "japanese":
                {
                    "content": f"{topic}では、'__'と言います。",
                    "explanation": f"{topic}の正しい表現です。"
                }
            ]
            questions = [
                {
                    "content": f"In {topic}, we say '__'.",
                    "explanation": f"This is the correct term for {topic}."
                }
            ]
        return random.choice(questions)

        """生成判断题"""
            questions = [
                    "content": f"{topic}は日本語で'正しい表現'と言います。",
                    "correct_answer": "True",
                    "explanation": f"{topic}の正しい表現です。"
                {
                    "explanation": f"{topic}の正しい表現ではありません。"
            ]
        else:
            questions = [
                {
                    "correct_answer": "True",
                    "explanation": f"This is the correct meaning of {topic}."
                },
                {
                    "content": f"{topic} means 'wrong expression' in English.",
                }
    def generate_short_answer(self, language, category, topic, level):
        """生成简答题"""
        if language == "japanese":
            questions = [
                {
                    "content": f"{topic}について簡単に説明してください。",
                }
        else:
            questions = [
                    "content": f"Please briefly explain what {topic} means.",
                    "correct_answer": f"{topic} is an English expression.",
                    "explanation": f"This is a basic explanation of {topic}."
            ]
        return random.choice(questions)
        """生成听力题"""
        if language == "japanese":
            # 模拟听力题数据
                {
                    "audio_url": f"https://example.com/audio/japanese/{topic}.mp3",
                    "content": "会話の中でBが言った内容は何ですか？",
                    "correct_answer": f"{topic}は日本語です",
                }
        else:
            listening_questions = [
                    "audio_url": f"https://example.com/audio/english/{topic}.mp3",
                    "content": "What did B say about {topic}?",
                    "explanation": "In the conversation, B said '{topic} is an English expression'."
                }
            ]

        """根据语言和题型生成题目"""
        question_data = {
            "level": level,
            "category": category,
            "question_type": question_type,

            if language == "japanese":
                q = self.generate_japanese_multiple_choice(category, topic, level)
                # 直接使用context作为内容，不需要格式化
                question_data["content"] = q["context"]
            else:
                question_data["content"] = q["context"]

                "options": q["options"],
                "correct_answer": q["answer"],
                "explanation": q["explanation"]
            })
            question_data.update({
                "options": [],
                "correct_answer": q["correct_answer"],
            q = self.generate_true_false(language, category, topic, level)
            question_data.update({
                "correct_answer": q["correct_answer"],
            })
        elif question_type == "short_answer":
            question_data.update({
                "content": q["content"],
                "options": [],
                "explanation": q["explanation"]
            })
        elif question_type == "listening":
            q = self.generate_listening_question(language, category, topic, level)
            question_data.update({
                "content": q["content"],
                "options": q["options"],
                "correct_answer": q["correct_answer"],
                "explanation": q["explanation"],
                "transcript": q["transcript"],
                "listening_context": q["listening_context"]
            })

        return question_data

    def _save_question(self, question_data):
        conn = self._connect_db()
        cursor = conn.cursor()
        options_json = str(question_data["options"])

        # 插入新题目
        cursor.execute('''
            INSERT INTO questions (language, level, category, content, options, correct_answer, explanation, source, question_type, audio_url, transcript, listening_context)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            question_data["language"],
            question_data["level"],
            question_data["category"],
            question_data["content"],
            options_json,
            question_data["correct_answer"],
            question_data["explanation"],
            question_data["source"],
            question_data["question_type"],
            question_data.get("audio_url"),
            question_data.get("transcript"),
        ))

        question_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return question_id

    def generate_questions_for_language(self, language, num_questions=50):
        """为指定语言生成题目"""
        print(f"开始为{language}生成{num_questions}道题目...")

        language_config = self.brain_map[language]
        question_types = language_config["question_types"]

        while generated < num_questions:
            # 随机选择分类
            category = random.choices(
                weights=[len(cat["topics"]) for cat in categories.values()]
            )[0]

            category_config = categories[category]

            # 随机选择主题
            topic = random.choice(category_config["topics"])

            # 根据难度分布随机选择难度
            level = random.choices(
                list(category_config["difficulty_levels"].keys()),
                weights=list(category_config["difficulty_levels"].values())
            )[0]

            question_type = random.choice(question_types)

            try:
                # 生成题目
                question_data = self.generate_question(
                    language, question_type, category, topic, level
                )

                # 检查是否重复
                    question_data["content"],
                    question_data["language"],
                    question_data["category"],
                    similarity_threshold=0.8
                    self._save_question(question_data)

                    if generated % 10 == 0:

            except Exception as e:

        print(f"生成的{language}题目分布: {self.generated_counts[language]}")
        """扩充题库"""
        print("=== 开始扩充题库 ===")


        for language in self.brain_map.keys():

        for language, counts in self.generated_counts.items():
            total = sum(counts.values())

        """获取当前题库统计信息"""
        print("=== 当前题库统计信息 ===")

        cursor = conn.cursor()

            for language in ["japanese", "english"]:
                print(f"\n{language}题库统计:")
                for question_type in ["multiple_choice", "fill_in_blank", "true_false", "short_answer", "listening"]:
                    cursor.execute('''
                        SELECT COUNT(*) FROM questions
                        WHERE language = ? AND question_type = ?
                    ''', (language, question_type))
                    count = cursor.fetchone()[0]
                    print(f"  {question_type}: {count}道")

                # 按难度统计
                for level in ["beginner", "intermediate", "advanced", "expert"]:
                    cursor.execute('''
                        SELECT COUNT(*) FROM questions
                        WHERE language = ? AND level = ?
                    ''', (language, level))
                    count = cursor.fetchone()[0]
                    print(f"  {level}: {count}道")

            # 总题目数
            cursor.execute('SELECT COUNT(*) FROM questions')
            total = cursor.fetchone()[0]
            print(f"\n总题目数: {total}道")
        finally:
            conn.close()

def main():
    """主函数"""
    expander = QuestionBankExpander()

    # 显示当前统计信息

    # 扩充题库
    expander.expand_question_bank(num_questions_per_language=100)  # 每种语言生成100道题目
    # 显示扩充后的统计信息
    expander.get_current_statistics()

if __name__ == "__main__":
    main()
