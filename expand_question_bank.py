#!/usr/bin/env python3
"""
自动扩充题库脚本
将生成的题目保存到数据库中

import os
import sys
# JSON import removed - using database
import sqlite3
import logging
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.ai.question_bank_ai import QuestionBankAI

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('expand_question_bank.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('expand_question_bank')

class QuestionBankExpander:
    """题库扩充器"""

    def __init__(self):
        """初始化题库扩充器"""
        self.question_bank_ai = QuestionBankAI()
        self.db_path = "flask-app/app.db"
        logger.info("题库扩充器初始化完成")

    def _connect_db(self):
        """连接到数据库

        Returns:
            sqlite3连接对象
        return sqlite3.connect(self.db_path)

    def convert_to_db_format(self, question):
        """将生成的题目转换为数据库格式

        Args:
            question: 生成的题目

        Returns:
            数据库格式的题目
            "question_id": question["id"],
            "question_text": "",
            "question_type": question["type"],
            "subtype": self._get_subtype(question["type"]),
            "options": str([]),
            "correct_answer": "",
            "explanation": "",
            "difficulty": self._get_difficulty(question["level"]),
            "audio_url": "",
            "audio_type": "",
            "audio_duration": 0,
            "audio_speed": "",
            "generated_by": "question_bank_ai",
            "source": "auto_generated",
            "passage": ""
        }

        # 根据题目类型填充具体内容
        content = question.get("content", {})

        if question["type"] == "listening":
            db_question["question_text"] = content.get("dialogue", "")
            db_question["audio_url"] = content.get("audio_url", "")
            db_question["audio_type"] = "dialogue"
            db_question["audio_duration"] = 60  # 默认60秒
            db_question["audio_speed"] = "normal"

            # 处理听力题的问题和选项
            if "questions" in content:
                listening_question = content["questions"][0]
                db_question["question_text"] = listening_question.get("content", "")
                db_question["options"] = str(listening_question.get("options", []))
                db_question["correct_answer"] = str(listening_question.get("correct_answer", 0))

        elif question["type"] == "reading":
            db_question["passage"] = content.get("text", "")
            if "questions" in content:
                reading_question = content["questions"][0]
                db_question["question_text"] = reading_question.get("content", "")
                db_question["options"] = str(reading_question.get("options", []))

        elif question["type"] == "grammar":
            db_question["question_text"] = content.get("question", "")
            # 提取选项（如果有）
            if "question" in content:
                # 简单解析题目文本提取选项
                question_text = content["question"]
                if "A. " in question_text and "B. " in question_text:
                    # 假设选项格式为 A. 选项1 B. 选项2 C. 选项3 D. 选项4
                    options = []
                    for option in ["A", "B", "C", "D"]:
                        start = question_text.find(f"{option}. ")
                        if start != -1:
                            end = question_text.find(f" {chr(ord(option) + 1)}. ", start)
                            if end == -1:
                                end = len(question_text)
                            option_text = question_text[start + 3:end].strip()
                            options.append(f"选项{option}: {option_text}")
                    db_question["options"] = str(options)
            db_question["correct_answer"] = str(content.get("correct_answer", 0))

        elif question["type"] == "vocabulary":
            db_question["question_text"] = content.get("question", "")
            # 提取选项（如果有）
            if "question" in content:
                # 简单解析题目文本提取选项
                question_text = content["question"]
                    # 假设选项格式为 A. 选项1 B. 选项2 C. 选项3 D. 选项4
                    for option in ["A", "B", "C", "D"]:
                        if start != -1:
                            if end == -1:
                            option_text = question_text[start + 3:end].strip()
                    db_question["options"] = str(options)


        """根据题型获取子题型
        Args:

        subtypes = {
            "grammar": "structure",
        }

        """将难度级别转换为数字
        Args:
        Returns:
            难度数字 (1-5)
        difficulty_map = {
            "advanced": 4
        }
        return difficulty_map.get(level, 3)

    def save_to_database(self, questions):
        """将题目保存到数据库

        Args:
            questions: 题目列表

        Returns:
        saved_count = 0

        try:

            for question in questions:
                # 转换为数据库格式
                db_question = self.convert_to_db_format(question)

                # 检查题目是否已存在
                cursor.execute("SELECT COUNT(*) FROM exam_questions WHERE question_id = ?",
                              (db_question["question_id"],))
                if cursor.fetchone()[0] > 0:
                    logger.info(f"题目 {db_question['question_id']} 已存在，跳过")
                    continue

                # 插入题目
                cursor.execute('''
                INSERT INTO exam_questions (
                    question_id, question_text, question_type, subtype,
                    options, correct_answer, explanation, difficulty,
                    audio_url, audio_type, audio_duration, audio_speed,
                    generated_by, source, passage
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    db_question["question_id"],
                    db_question["question_text"],
                    db_question["question_type"],
                    db_question["subtype"],
                    db_question["options"],
                    db_question["correct_answer"],
                    db_question["explanation"],
                    db_question["difficulty"],
                    db_question["audio_url"],
                    db_question["audio_type"],
                    db_question["audio_duration"],
                    db_question["audio_speed"],
                    db_question["generated_by"],
                    db_question["source"],
                    db_question["passage"]
                ))

                saved_count += 1

            conn.commit()
            cursor.close()
            conn.close()

            logger.info(f"成功保存 {saved_count} 道题目到数据库")
            return saved_count
        except Exception as e:
            logger.error(f"保存题目到数据库失败: {str(e)}")
            return 0

    def run(self, count_per_language=50):
        """运行题库扩充

        Args:
            count_per_language: 每种语言生成的题目数量

        Returns:
            扩充成功返回True
        logger.info("开始自动扩充题库")

        try:
            # 生成题目

            for language, config in self.question_bank_ai.languages.items():
                for dialect in config['dialects']:
                    for level in config['levels']:
                        # 生成听力题
                        listening_questions = self.question_bank_ai.generate_listening_questions(
                            language, dialect, level, count_per_language // 4
                        )
                        all_questions.extend(listening_questions)

                        # 保存听力题到文件
                        self.question_bank_ai.save_questions(listening_questions, language)

            # 生成其他类型的题目
                for level in config['levels']:
                    for question_type in ['reading', 'grammar', 'vocabulary']:
                        # 生成其他类型题目
                        other_questions = self.question_bank_ai.generate_other_questions(
                            language, level, question_type, count_per_language // 4
                        )
                        all_questions.extend(other_questions)

                        # 保存其他类型题目到文件
                        self.question_bank_ai.save_questions(other_questions, language)

            # 报告到AI脑库

            # 保存到数据库
            saved_count = self.save_to_database(all_questions)

            logger.info(f"题库扩充完成，共生成 {len(all_questions)} 道题目，成功保存 {saved_count} 道到数据库")
            return True
        except Exception as e:
            return False

if __name__ == "__main__":
    expander = QuestionBankExpander()
    expander.run()
