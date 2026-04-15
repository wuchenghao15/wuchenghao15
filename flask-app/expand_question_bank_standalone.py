#!/usr/bin/env python3
"""
独立的题库扩充脚本，不依赖Flask应用，直接操作数据库
生成各种题型的题目，包括听力题，丰富题库内容
"""

import sqlite3
import json
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
                    "学术日语": {
                        "topics": ["论文写作", "学术演讲", "研究方法", "专业术语"],
                        "difficulty_levels": {"advanced": 0.6, "expert": 0.4}
                    }
                },
                "question_types": ["multiple_choice", "fill_in_blank", "true_false", "short_answer", "listening"]
            },
            "english": {
                "categories": {
                    "日常英语": {
                        "topics": ["Greetings", "Shopping", "Restaurant", "Transportation", "Accommodation", "Weather", "Health", "Hobbies"],
                        "difficulty_levels": {"beginner": 0.4, "intermediate": 0.4, "advanced": 0.2}
                    },
                    "商务英语": {
                        "topics": ["Business Etiquette", "Meetings", "Email Writing", "Negotiation", "Product Presentation"],
                        "difficulty_levels": {"intermediate": 0.5, "advanced": 0.5}
                    },
                    "学术英语": {
                        "topics": ["Academic Writing", "Presentations", "Research Methods", "Technical Terms"],
                        "difficulty_levels": {"advanced": 0.6, "expert": 0.4}
                    }
                },
                "question_types": ["multiple_choice", "fill_in_blank", "true_false", "short_answer", "listening"]
            }
        }
        
        # 生成的题目计数
        self.generated_counts = {
            "japanese": {"multiple_choice": 0, "fill_in_blank": 0, "true_false": 0, "short_answer": 0, "listening": 0},
            "english": {"multiple_choice": 0, "fill_in_blank": 0, "true_false": 0, "short_answer": 0, "listening": 0}
        }
    
    def _connect_db(self):
        """连接数据库"""
        return sqlite3.connect(DATABASE_PATH)
    
    def _create_table_if_not_exists(self):
        """创建题目表（如果不存在），并添加缺失的列"""
        conn = self._connect_db()
        cursor = conn.cursor()
        
        # 创建题目表
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
            # 获取同语言同类别下的所有题目内容
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
        # 基础题目模板
        templates = [
            {
                "question": "{context}、どう言いますか？",
                "options": ["{option1}", "{option2}", "{option3}", "{option4}"],
                "answer": "{answer}",
                "explanation": "{explanation}"
            },
            {
                "question": "{context}の正しい表現はどれですか？",
                "options": ["{option1}", "{option2}", "{option3}", "{option4}"],
                "answer": "{answer}",
                "explanation": "{explanation}"
            }
        ]
        
        # 根据主题和难度生成具体题目
        if category == "日常对话" and topic == "问候与介绍":
            contexts = [
                "朝、先生に会ったとき",
                "初めて人に会ったとき",
                "お客様を迎えるとき",
                "友人と久しぶりに会ったとき"
            ]
            
            questions = [
                {
                    "context": contexts[0],
                    "options": ["おはようございます", "こんにちは", "こんばんは", "おやすみなさい"],
                    "answer": "おはようございます",
                    "explanation": "朝の挨拶は'おはようございます'です。"
                },
                {
                    "context": contexts[1],
                    "options": ["お元気ですか", "初めまして", "さようなら", "ありがとう"],
                    "answer": "初めまして",
                    "explanation": "初めて会う人には'初めまして'と言います。"
                }
            ]
        elif category == "日常对话" and topic == "餐厅":
            questions = [
                {
                    "context": "レストランで注文するとき",
                    "options": ["メニューをください", "お会計をください", "トイレはどこですか", "これをください"],
                    "answer": "メニューをください",
                    "explanation": "レストランで注文する前にメニューをもらうときは'メニューをください'と言います。"
                }
            ]
        else:
            # 默认题目
            questions = [
                {
                    "context": f"{topic}に関する質問",
                    "options": ["選択肢1", "選択肢2", "選択肢3", "選択肢4"],
                    "answer": "選択肢1",
                    "explanation": "これは正しい答えです。"
                }
            ]
        
        return random.choice(questions)
    
    def generate_english_multiple_choice(self, category, topic, level):
        """生成英语选择题"""
        questions = [
            {
                "context": f"{topic} related question",
                "options": ["Option A", "Option B", "Option C", "Option D"],
                "answer": "Option A",
                "explanation": "This is the correct answer."
            },
            {
                "context": f"When talking about {topic}",
                "options": ["Yes", "No", "Maybe", "Not sure"],
                "answer": "Yes",
                "explanation": "This is the appropriate response."
            }
        ]
        return random.choice(questions)
    
    def generate_fill_in_blank(self, language, category, topic, level):
        """生成填空题"""
        if language == "japanese":
            questions = [
                {
                    "content": f"{topic}では、'__'と言います。",
                    "correct_answer": f"{topic}",
                    "explanation": f"{topic}の正しい表現です。"
                }
            ]
        else:
            questions = [
                {
                    "content": f"In {topic}, we say '__'.",
                    "correct_answer": f"{topic}",
                    "explanation": f"This is the correct term for {topic}."
                }
            ]
        return random.choice(questions)
    
    def generate_true_false(self, language, category, topic, level):
        """生成判断题"""
        if language == "japanese":
            questions = [
                {
                    "content": f"{topic}は日本語で'正しい表現'と言います。",
                    "correct_answer": "True",
                    "explanation": f"{topic}の正しい表現です。"
                },
                {
                    "content": f"{topic}は日本語で'間違った表現'と言います。",
                    "correct_answer": "False",
                    "explanation": f"{topic}の正しい表現ではありません。"
                }
            ]
        else:
            questions = [
                {
                    "content": f"{topic} means 'correct expression' in English.",
                    "correct_answer": "True",
                    "explanation": f"This is the correct meaning of {topic}."
                },
                {
                    "content": f"{topic} means 'wrong expression' in English.",
                    "correct_answer": "False",
                    "explanation": f"This is not the correct meaning of {topic}."
                }
            ]
        return random.choice(questions)
    
    def generate_short_answer(self, language, category, topic, level):
        """生成简答题"""
        if language == "japanese":
            questions = [
                {
                    "content": f"{topic}について簡単に説明してください。",
                    "correct_answer": f"{topic}は日本語での表現です。",
                    "explanation": f"{topic}に関する基本的な説明です。"
                }
            ]
        else:
            questions = [
                {
                    "content": f"Please briefly explain what {topic} means.",
                    "correct_answer": f"{topic} is an English expression.",
                    "explanation": f"This is a basic explanation of {topic}."
                }
            ]
        return random.choice(questions)
    
    def generate_listening_question(self, language, category, topic, level):
        """生成听力题"""
        if language == "japanese":
            # 模拟听力题数据
            listening_questions = [
                {
                    "listening_context": f"{topic}に関する会話",
                    "transcript": f"A: こんにちは。{topic}について教えてください。\nB: はい、{topic}は日本語での表現です。\nA: ありがとうございます。",
                    "audio_url": f"https://example.com/audio/japanese/{topic}.mp3",
                    "content": "会話の中でBが言った内容は何ですか？",
                    "options": [f"{topic}は日本語です", f"{topic}は英語です", f"{topic}はフランス語です", f"{topic}はドイツ語です"],
                    "correct_answer": f"{topic}は日本語です",
                    "explanation": "会話の中でBは'{topic}は日本語での表現です'と言いました。"
                }
            ]
        else:
            listening_questions = [
                {
                    "listening_context": f"Conversation about {topic}",
                    "transcript": f"A: Hello. Can you tell me about {topic}?\nB: Yes, {topic} is an English expression.\nA: Thank you.",
                    "audio_url": f"https://example.com/audio/english/{topic}.mp3",
                    "content": "What did B say about {topic}?",
                    "options": [f"{topic} is English", f"{topic} is Spanish", f"{topic} is French", f"{topic} is German"],
                    "correct_answer": f"{topic} is English",
                    "explanation": "In the conversation, B said '{topic} is an English expression'."
                }
            ]
        return random.choice(listening_questions)
    
    def generate_question(self, language, question_type, category, topic, level):
        """根据语言和题型生成题目"""
        question_data = {
            "language": language,
            "level": level,
            "category": category,
            "topic": topic,
            "question_type": question_type,
            "source": "ai_generated",
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        if question_type == "multiple_choice":
            if language == "japanese":
                q = self.generate_japanese_multiple_choice(category, topic, level)
                # 直接使用context作为内容，不需要格式化
                question_data["content"] = q["context"]
            else:
                q = self.generate_english_multiple_choice(category, topic, level)
                question_data["content"] = q["context"]
            
            question_data.update({
                "options": q["options"],
                "correct_answer": q["answer"],
                "explanation": q["explanation"]
            })
        elif question_type == "fill_in_blank":
            q = self.generate_fill_in_blank(language, category, topic, level)
            question_data.update({
                "content": q["content"],
                "options": [],
                "correct_answer": q["correct_answer"],
                "explanation": q["explanation"]
            })
        elif question_type == "true_false":
            q = self.generate_true_false(language, category, topic, level)
            question_data.update({
                "content": q["content"],
                "options": ["True", "False"],
                "correct_answer": q["correct_answer"],
                "explanation": q["explanation"]
            })
        elif question_type == "short_answer":
            q = self.generate_short_answer(language, category, topic, level)
            question_data.update({
                "content": q["content"],
                "options": [],
                "correct_answer": q["correct_answer"],
                "explanation": q["explanation"]
            })
        elif question_type == "listening":
            q = self.generate_listening_question(language, category, topic, level)
            question_data.update({
                "content": q["content"],
                "options": q["options"],
                "correct_answer": q["correct_answer"],
                "explanation": q["explanation"],
                "audio_url": q["audio_url"],
                "transcript": q["transcript"],
                "listening_context": q["listening_context"]
            })
        
        return question_data
    
    def _save_question(self, question_data):
        """保存题目到数据库"""
        conn = self._connect_db()
        cursor = conn.cursor()
        
        options_json = json.dumps(question_data["options"])
        
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
            question_data.get("listening_context")
        ))
        
        question_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return question_id
    
    def generate_questions_for_language(self, language, num_questions=50):
        """为指定语言生成题目"""
        print(f"开始为{language}生成{num_questions}道题目...")
        
        language_config = self.brain_map[language]
        categories = language_config["categories"]
        question_types = language_config["question_types"]
        
        generated = 0
        while generated < num_questions:
            # 随机选择分类
            category = random.choices(
                list(categories.keys()),
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
            
            # 随机选择题型
            question_type = random.choice(question_types)
            
            try:
                # 生成题目
                question_data = self.generate_question(
                    language, question_type, category, topic, level
                )
                
                # 检查是否重复
                if not self._is_duplicate_question(
                    question_data["content"],
                    question_data["language"],
                    question_data["category"],
                    similarity_threshold=0.8
                ):
                    self._save_question(question_data)
                    generated += 1
                    self.generated_counts[language][question_type] += 1
                    
                    if generated % 10 == 0:
                        print(f"已生成{generated}/{num_questions}道{language}题目")
                        
            except Exception as e:
                print(f"生成题目失败: {str(e)}")
                continue
        
        print(f"完成{language}题目的生成！")
        print(f"生成的{language}题目分布: {self.generated_counts[language]}")
    
    def expand_question_bank(self, num_questions_per_language=50):
        """扩充题库"""
        print("=== 开始扩充题库 ===")
        
        # 确保表存在
        self._create_table_if_not_exists()
        
        # 为每种语言生成题目
        for language in self.brain_map.keys():
            self.generate_questions_for_language(language, num_questions_per_language)
        
        print("=== 题库扩充完成 ===")
        print("生成的题目总分布:")
        for language, counts in self.generated_counts.items():
            print(f"{language}: {counts}")
            total = sum(counts.values())
            print(f"{language}总计: {total}道题目")
    
    def get_current_statistics(self):
        """获取当前题库统计信息"""
        print("=== 当前题库统计信息 ===")
        
        conn = self._connect_db()
        cursor = conn.cursor()
        
        try:
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
    expander.get_current_statistics()
    
    # 扩充题库
    expander.expand_question_bank(num_questions_per_language=100)  # 每种语言生成100道题目
    
    # 显示扩充后的统计信息
    expander.get_current_statistics()

if __name__ == "__main__":
    main()
