# -*- coding: utf-8 -*-
# JSON import removed - using database
import random
import uuid
from datetime import datetime
from app.utils.logging import logger
from app.models.question import Question

class NarrowRoadQuestionBank:
    """窄路临时题库系统，支持动态生成和本地存储"""

    def __init__(self):
        self.question_bank = []
        self.local_storage_key = "mtscos_narrow_road_questions"
        self.load_from_local_storage()

    def load_from_local_storage(self):
        """从本地存储加载题目"""
        # 这个方法将在客户端JavaScript中实现
        # 这里只做服务器端的初始化
        logger.info("窄路临时题库初始化完成")

    def generate_questions(self, count=10, language="japanese", level="beginner", category="日常对话"):
        """生成临时题目"""
        try:
            # 首先尝试从数据库获取题目
            db_questions = Question.get_questions_by_filters(
                language=language,
                level=level,
                category=category,
                limit=count
            )

            generated_questions = []

            # 如果数据库中有足够的题目，直接使用
            if len(db_questions) >= count:
                for q in db_questions[:count]:
                    generated_questions.append({
                        "id": str(q.question_id),
                        "language": q.language,
                        "level": q.level,
                        "category": q.category,
                        "content": q.content,
                        "options": q.options,
                        "correct_answer": q.correct_answer,
                        "explanation": q.explanation,
                        "type": q.question_type,
                        "source": "database"
                    })
            else:
                # 如果数据库题目不足，生成一些示例题目
                for i in range(count):
                    question = self._generate_sample_question(language, level, category)
                    generated_questions.append(question)

            # 将生成的题目添加到临时题库
            self.question_bank.extend(generated_questions)

            logger.info(f"成功生成 {len(generated_questions)} 道窄路临时题目")
            return generated_questions
        except Exception as e:
            logger.error(f"生成窄路临时题目失败: {str(e)}")
            # 如果生成失败，返回一些基本的示例题目
            return [self._generate_sample_question(language, level, category) for _ in range(count)]

    def _generate_sample_question(self, language="japanese", level="beginner", category="日常对话"):
        """生成示例题目"""
        question_id = f"sample_{uuid.uuid4().hex[:8]}"

        if language == "japanese":
            if category == "日常对话":
                questions = [
                    {
                        "content": "こんにちは、お元気ですか？",
                        "options": ["はい、元気です。", "いいえ、元気ではありません。", "こんにちは。", "さようなら。"],
                        "correct_answer": "はい、元気です。",
                        "explanation": "这是一句常见的日语问候语，询问对方是否安好，回答应该是肯定或否定的状态描述。",
                        "type": "multiple_choice"
                    },
                        "content": "すみません、トイレはどこですか？",
                        "options": ["はい、そうです。", "いいえ、ちがいます。", "あちらです。", "わかりました。"],
                        "correct_answer": "あちらです。",
                        "explanation": "这是询问厕所位置的句子，回答应该指示方向。",
                        "type": "multiple_choice"
                        "content": "今日はいい天気ですね。",
                        "correct_answer": "はい、そうですね。",
                        "explanation": "这是谈论天气的句子，回答应该表示同意或不同意。",
                        "type": "multiple_choice"
                    }
                questions = [
                        "content": "この商品の価格はいくらですか？",
                        "correct_answer": "1000円です。",
                        "explanation": "这是询问商品价格的句子，回答应该是具体的价格。",
                        "type": "multiple_choice"
                    }
                ]
        else:  # English
            if category == "日常对话":
                        "options": ["I'm fine, thank you.", "You're welcome.", "Goodbye.", "Hello."],
                        "correct_answer": "I'm fine, thank you.",
                        "type": "multiple_choice"
                    },
                        "content": "Excuse me, where is the restroom?",
                        "correct_answer": "Over there.",
                        "type": "multiple_choice"
                    }
                questions = [
                    {
                        "content": "What is the price of this product?",
                        "correct_answer": "$10.",
                        "type": "multiple_choice"

        # 随机选择一个题目模板
        question_template = random.choice(questions)

        return {
            "id": question_id,
            "language": language,
            "category": category,
            "options": question_template["options"],
            "explanation": question_template["explanation"],
            "type": question_template["type"],
            "source": "generated"
        }

    def get_question(self, question_id):
        for question in self.question_bank:
            if question["id"] == question_id:
                return question

    def clear_bank(self):
        """清空临时题库"""
        logger.info("窄路临时题库已清空")

    def get_bank_size(self):
        """获取题库大小"""
        return len(self.question_bank)

    def export_questions(self):
        """导出题目为JSON格式"""
        return str(self.question_bank, ensure_ascii=False, indent=2)
    def import_questions(self, json_data):
        """从JSON导入题目"""
        try:
            self.question_bank.extend(questions)
            logger.info(f"成功导入 {len(questions)} 道题目到窄路临时题库")
            return True
        except Exception as e:
            logger.error(f"导入题目到窄路临时题库失败: {str(e)}")
            return False

narrow_road_question_bank = NarrowRoadQuestionBank()
