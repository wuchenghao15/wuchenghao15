# -*- coding: utf-8 -*-
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI出题专家系统 - 根据考试类型和语言生成高质量题目
支持从数据库题库随机出题,确保选项具有混淆性和易错性
"""

import logging
logger = logging.getLogger(__name__)
import random
import sqlite3
from contextlib import contextmanager
import os
import json


class QuestionGenerator:
    """AI出题专家 - 根据语言和难度生成高质量题目"""
    
    def __init__(self):
        self.db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'app.db')
        
        self.japanese_vocabulary = {
            '初级': [
                {'word': '猫', 'kana': 'ねこ', 'meaning': '猫', 'confusions': ['犬', '鳥', '魚']},
                {'word': '犬', 'kana': 'いぬ', 'meaning': '狗', 'confusions': ['猫', '馬', '牛']},
                {'word': '本', 'kana': 'ほん', 'meaning': '书', 'confusions': ['雑誌', '新聞', '辞書']},
                {'word': '水', 'kana': 'みず', 'meaning': '水', 'confusions': ['お茶', 'コーヒー', 'ジュース']},
                {'word': '食べる', 'kana': 'たべる', 'meaning': '吃', 'confusions': ['飲む', '話す', '見る']},
                {'word': '行く', 'kana': 'いく', 'meaning': '去', 'confusions': ['来る', '帰る', '出る']},
                {'word': '見る', 'kana': 'みる', 'meaning': '看', 'confusions': ['聞く', '話す', '食べる']},
                {'word': '聞く', 'kana': 'きく', 'meaning': '听', 'confusions': ['見る', '話す', '読む']},
                {'word': '話す', 'kana': 'はなす', 'meaning': '说', 'confusions': ['聞く', '読む', '書く']},
                {'word': '読む', 'kana': 'よむ', 'meaning': '读', 'confusions': ['書く', '話す', '見る']},
            ],
            '中级': [
                {'word': '勉強', 'kana': 'べんきょう', 'meaning': '学习', 'confusions': ['仕事', '働く', '研究']},
                {'word': '研究', 'kana': 'けんきゅう', 'meaning': '研究', 'confusions': ['勉強', '調査', '開発']},
                {'word': '開発', 'kana': 'かいはつ', 'meaning': '开发', 'confusions': ['研究', '設計', '製造']},
                {'word': '設計', 'kana': 'せっけい', 'meaning': '设计', 'confusions': ['開発', '製造', '企画']},
            ],
            '高级': [
                {'word': '認識', 'kana': 'にんしき', 'meaning': '认识', 'confusions': ['認知', '意識', '理解']},
                {'word': '意識', 'kana': 'いしき', 'meaning': '意识', 'confusions': ['認識', '認知', '知識']},
            ]
        }
        
        self.english_vocabulary = {
            '初级': [
                {'word': 'apple', 'meaning': '苹果', 'confusions': ['orange', 'banana', 'grape']},
                {'word': 'book', 'meaning': '书', 'confusions': ['notebook', 'magazine', 'dictionary']},
                {'word': 'happy', 'meaning': '快乐的', 'confusions': ['sad', 'angry', 'tired']},
                {'word': 'run', 'meaning': '跑', 'confusions': ['walk', 'jump', 'swim']},
            ],
            '中级': [
                {'word': 'knowledge', 'meaning': '知识', 'confusions': ['information', 'intelligence', 'wisdom']},
                {'word': 'development', 'meaning': '发展', 'confusions': ['progress', 'growth', 'improvement']},
            ],
            '高级': [
                {'word': 'comprehensive', 'meaning': '综合的', 'confusions': ['comprehensible', 'complicative', 'complementary']},
                {'word': 'sophisticated', 'meaning': '复杂的', 'confusions': ['simplistic', 'sophomoric', 'soporific']},
            ]
        }
        
        logger.info("AI出题专家初始化完成")
    
    @contextmanager
    def get_db_connection(self):
        """获取数据库连接"""
        conn = sqlite3.connect(self.db_path, timeout=10)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
    
    def generate(self, subject: str, difficulty: str, question_type: str = 'single_choice') -> dict:
        """生成题目"""
        try:
            if subject == 'japanese' or subject == '日语':
                return self.generate_japanese_question(difficulty)
            elif subject == 'english' or subject == '英语':
                return self.generate_english_question(difficulty)
            else:
                return self.generate_math_question(difficulty)
        except Exception as e:
            logger.error(f"生成题目失败: {str(e)}")
            return self.generate_default_question(subject, difficulty)
    
    def generate_japanese_question(self, difficulty: str) -> dict:
        """生成日语题目"""
        vocab_level = '初级'
        if difficulty == 'high':
            vocab_level = '高级'
        elif difficulty == 'medium':
            vocab_level = '中级'
        
        vocab_list = self.japanese_vocabulary.get(vocab_level, self.japanese_vocabulary['初级'])
        item = random.choice(vocab_list)
        
        options = item['confusions'][:3]
        options.append(item['word'])
        random.shuffle(options)
        
        return {
            'type': 'single_choice',
            'language': 'japanese',
            'difficulty': difficulty,
            'content': f"「{item['word']}」({item['kana']}) の意味は?",
            'options': [f"{chr(65+i)}. {opt}" for i, opt in enumerate(options)],
            'correct_answer': chr(65 + options.index(item['word'])),
            'explanation': f"「{item['word']}」は「{item['meaning']}」という意味です."
        }
    
    def generate_english_question(self, difficulty: str) -> dict:
        """生成英语题目"""
        vocab_level = '初级'
        if difficulty == 'high':
            vocab_level = '高级'
        elif difficulty == 'medium':
            vocab_level = '中级'
        
        vocab_list = self.english_vocabulary.get(vocab_level, self.english_vocabulary['初级'])
        item = random.choice(vocab_list)
        
        options = item['confusions'][:3]
        options.append(item['word'])
        random.shuffle(options)
        
        return {
            'type': 'single_choice',
            'language': 'english',
            'difficulty': difficulty,
            'content': f"What is the meaning of '{item['word']}'?",
            'options': [f"{chr(65+i)}. {opt}" for i, opt in enumerate(options)],
            'correct_answer': chr(65 + options.index(item['word'])),
            'explanation': f"'{item['word']}' means '{item['meaning']}'."
        }
    
    def generate_math_question(self, difficulty: str) -> dict:
        """生成数学题目"""
        if difficulty == 'high':
            a = random.randint(10, 50)
            b = random.randint(10, 50)
            c = random.randint(10, 50)
            answer = a + b + c
            content = f"计算: {a} + {b} + {c} = ?"
        elif difficulty == 'medium':
            a = random.randint(10, 30)
            b = random.randint(1, 10)
            answer = a * b
            content = f"计算: {a} × {b} = ?"
        else:
            a = random.randint(1, 20)
            b = random.randint(1, 20)
            answer = a + b
            content = f"计算: {a} + {b} = ?"
        
        options = [answer, answer + random.randint(1, 10), 
                   answer - random.randint(1, 10), 
                   answer * random.randint(2, 3)]
        random.shuffle(options)
        
        return {
            'type': 'single_choice',
            'language': 'math',
            'difficulty': difficulty,
            'content': content,
            'options': [f"{chr(65+i)}. {opt}" for i, opt in enumerate(options)],
            'correct_answer': chr(65 + options.index(answer)),
            'explanation': f"正确答案是 {answer}."
        }
    
    def generate_default_question(self, subject: str, difficulty: str) -> dict:
        """生成默认题目"""
        subjects = {'math': '数学', 'chinese': '语文', 'english': '英语', 
                    'physics': '物理', 'chemistry': '化学', 'japanese': '日语'}
        
        return {
            'type': 'single_choice',
            'language': subject,
            'difficulty': difficulty,
            'content': f"{subjects.get(subject, subject)}题目示例",
            'options': ['A. 选项1', 'B. 选项2', 'C. 选项3', 'D. 选项4'],
            'correct_answer': 'A',
            'explanation': '题目解析'
        }


question_generator = QuestionGenerator()
