# -*- coding: utf-8 -*-
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
窄路临时题库 - 用于临时存储和管理考试题目
支持多语言题目生成和管理
"""

import logging
logger = logging.getLogger(__name__)
import random
import json
import os


class NarrowRoadQuestionBank:
    """窄路临时题库管理器"""
    
    def __init__(self):
        logger.info("窄路临时题库初始化完成")
    
    def generate_questions(self, count=10, language="japanese", level="beginner", category="日常对话"):
        """生成临时题目"""
        generated_questions = []
        
        try:
            from app.models.question import Question
            db_questions = Question.get_questions_by_filters(
                language=language,
                level=level,
                category=category,
                limit=count
            )
            
            if len(db_questions) >= count:
                for q in db_questions[:count]:
                    generated_questions.append({
                        "id": str(q.question_id),
                        "content": q.content,
                        "options": json.loads(q.options) if q.options else [],
                        "correct_answer": q.correct_answer,
                        "explanation": q.explanation,
                        "type": q.type,
                        "difficulty": q.difficulty
                    })
                return generated_questions
        except Exception as e:
            logger.warning(f"从数据库获取题目失败,使用默认题目: {str(e)}")
        
        for i in range(count):
            question = self._generate_single_question(language, level)
            question["id"] = str(i + 1)
            generated_questions.append(question)
        
        return generated_questions
    
    def _generate_single_question(self, language, level):
        """生成单个题目"""
        if language == "japanese":
            return self._generate_japanese_question(level)
        elif language == "english":
            return self._generate_english_question(level)
        else:
            return self._generate_math_question(level)
    
    def _generate_japanese_question(self, level):
        """生成日语题目"""
        vocab = {
            "beginner": [
                {"word": "猫", "kana": "ねこ", "meaning": "猫", "confusions": ["犬", "鳥", "魚"]},
                {"word": "犬", "kana": "いぬ", "meaning": "狗", "confusions": ["猫", "馬", "牛"]},
                {"word": "本", "kana": "ほん", "meaning": "书", "confusions": ["雑誌", "新聞", "辞書"]},
                {"word": "水", "kana": "みず", "meaning": "水", "confusions": ["お茶", "コーヒー", "ジュース"]},
                {"word": "食べる", "kana": "たべる", "meaning": "吃", "confusions": ["飲む", "話す", "見る"]},
            ],
            "intermediate": [
                {"word": "勉強", "kana": "べんきょう", "meaning": "学习", "confusions": ["仕事", "働く", "研究"]},
                {"word": "研究", "kana": "けんきゅう", "meaning": "研究", "confusions": ["勉強", "調査", "開発"]},
            ],
            "advanced": [
                {"word": "認識", "kana": "にんしき", "meaning": "认识", "confusions": ["認知", "意識", "理解"]},
                {"word": "意識", "kana": "いしき", "meaning": "意识", "confusions": ["認識", "認知", "知識"]},
            ]
        }
        
        vocab_list = vocab.get(level, vocab["beginner"])
        item = random.choice(vocab_list)
        
        options = item["confusions"][:3]
        options.append(item["word"])
        random.shuffle(options)
        
        return {
            "type": "single_choice",
            "language": "japanese",
            "difficulty": level,
            "content": f"「{item['word']}」({item['kana']}) の意味は?",
            "options": [f"{chr(65+i)}. {opt}" for i, opt in enumerate(options)],
            "correct_answer": chr(65 + options.index(item["word"])),
            "explanation": f"「{item['word']}」は「{item['meaning']}」という意味です."
        }
    
    def _generate_english_question(self, level):
        """生成英语题目"""
        vocab = {
            "beginner": [
                {"word": "apple", "meaning": "苹果", "confusions": ["orange", "banana", "grape"]},
                {"word": "book", "meaning": "书", "confusions": ["notebook", "magazine", "dictionary"]},
            ],
            "intermediate": [
                {"word": "knowledge", "meaning": "知识", "confusions": ["information", "intelligence", "wisdom"]},
            ],
            "advanced": [
                {"word": "comprehensive", "meaning": "综合的", "confusions": ["comprehensible", "complicative", "complementary"]},
            ]
        }
        
        vocab_list = vocab.get(level, vocab["beginner"])
        item = random.choice(vocab_list)
        
        options = item["confusions"][:3]
        options.append(item["word"])
        random.shuffle(options)
        
        return {
            "type": "single_choice",
            "language": "english",
            "difficulty": level,
            "content": f"What is the meaning of '{item['word']}'?",
            "options": [f"{chr(65+i)}. {opt}" for i, opt in enumerate(options)],
            "correct_answer": chr(65 + options.index(item["word"])),
            "explanation": f"'{item['word']}' means '{item['meaning']}'."
        }
    
    def _generate_math_question(self, level):
        """生成数学题目"""
        if level == "advanced":
            a = random.randint(10, 50)
            b = random.randint(10, 50)
            c = random.randint(10, 50)
            answer = a + b + c
            content = f"计算: {a} + {b} + {c} = ?"
        elif level == "intermediate":
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
            "type": "single_choice",
            "language": "math",
            "difficulty": level,
            "content": content,
            "options": [f"{chr(65+i)}. {opt}" for i, opt in enumerate(options)],
            "correct_answer": chr(65 + options.index(answer)),
            "explanation": f"正确答案是 {answer}."
        }
    
    def save_questions(self, questions, exam_id):
        """保存题目到数据库"""
        try:
            from app.models.question import Question
            for q in questions:
                Question.create(
                    exam_id=exam_id,
                    content=q["content"],
                    options=json.dumps(q["options"]),
                    correct_answer=q["correct_answer"],
                    explanation=q.get("explanation", ""),
                    type=q.get("type", "single_choice"),
                    difficulty=q.get("difficulty", "medium")
                )
            logger.info(f"保存了 {len(questions)} 道题目到数据库")
            return True
        except Exception as e:
            logger.error(f"保存题目失败: {str(e)}")
            return False


narrow_road_question_bank = NarrowRoadQuestionBank()
