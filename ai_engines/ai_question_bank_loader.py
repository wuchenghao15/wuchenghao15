# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
AI题库载录模块
使用AI生成题目和选项,并将它们正确存储到数据库中
"""

import os
import sys
import json
import time
import logging
from datetime import datetime

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import get_db_connection, init_db
from ai_service import ai_service_manager
from intelligent_option_generator import IntelligentOptionGenerator

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ai_question_bank_loader.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('ai_question_bank_loader')


class AIQuestionBankLoader:
    """AI题库载录器"""

    def __init__(self):
        """初始化AI题库载录器"""
        self.db_conn = get_db_connection()
        self.option_generator = IntelligentOptionGenerator()
        self.languages = ['japanese', 'english']
        self.categories = ['词汇', '语法', '阅读', '听力']
        self.difficulties = [1, 2, 3, 4, 5]

        logger.info("初始化AI题库载录器")

    def _generate_question_content(self, language, category, difficulty):
        """使用AI生成题目内容

        Args:
            language: 语言 (japanese/english)
            category: 类别 (词汇/语法/阅读/听力)
            difficulty: 难度 (1-5)

        Returns:
            生成的题目内容和正确答案
        """
        prompt = f"生成一个{language}的{category}题,难度为{difficulty}级,格式清晰,包含题目内容和正确答案."

        result = ai_service_manager.infer('default_text_gen', prompt)

        if not result['success']:
            logger.error(f"AI生成题目失败: {result['error']}")
            return None, None

        generated_text = result['result']
        logger.info(f"AI生成题目: {generated_text[:50]}...")

        lines = generated_text.split('\n')
        question_content = ""
        correct_answer = ""

        for line in lines:
            if "题目:" in line or "问题:" in line:
                question_content = line.replace("题目:", "").replace("问题:", "").strip()
            elif "正确答案:" in line or "答案:" in line:
                correct_answer = line.replace("正确答案:", "").replace("答案:", "").strip()

        if not question_content or not correct_answer:
            logger.warning(f"无法解析AI生成的题目格式: {generated_text}")
            return None, None

        return question_content, correct_answer

    def _generate_listening_question(self, language, difficulty):
        """生成听力题目

        Args:
            language: 语言 (japanese/english)
            difficulty: 难度 (1-5)

        Returns:
            生成的听力题目内容和正确答案
        """
        difficulty_map = {
            1: 'beginner',
            2: 'beginner',
            3: 'intermediate',
            4: 'advanced',
            5: 'expert'
        }

        result = ai_service_manager.infer('default_text_gen',
                                         f"生成{language}听力文本",
                                         subject=language,
                                         difficulty=difficulty_map.get(difficulty, 'intermediate'))

        if not result['success']:
            logger.error(f"AI生成听力文本失败: {result['error']}")
            return None, None

        listening_text = result['result']
        logger.info(f"AI生成听力文本: {listening_text[:50]}...")

        question_prompt = f"根据以下听力材料生成一道{language}听力题目,包含问题和正确答案:\n{listening_text}"
        question_result = ai_service_manager.infer('default_text_gen', question_prompt)

        if not question_result['success']:
            logger.error(f"AI生成听力问题失败: {question_result['error']}")
            return None, None

        question_content = question_result['result']

        lines = question_content.split('\n')
        final_question = f"听力材料:\n{listening_text}\n\n"
        correct_answer = ""

        for line in lines:
            if "题目:" in line or "问题:" in line:
                final_question += line.replace("题目:", "").replace("问题:", "").strip() + "\n"
            elif "正确答案:" in line or "答案:" in line:
                correct_answer = line.replace("正确答案:", "").replace("答案:", "").strip()

        if not correct_answer:
            return None, None

        return final_question.strip(), correct_answer

    def _generate_options(self, question_content, category, language, correct_answer):
        """生成选项

        Args:
            question_content: 题目内容
            category: 类别
            language: 语言
            correct_answer: 正确答案

        Returns:
            生成的选项列表
        """
        question_info = {
            'content': question_content,
            'category': category,
            'language': language
        }

        options = self.option_generator.generate_options(question_info, correct_answer, 6)
        logger.info(f"生成选项数量: {len(options)}")

        return options

    def _save_to_database(self, language, category, difficulty, content, options, correct_answer, explanation=""):
        """将题目保存到数据库

        Args:
            language: 语言
            category: 类别
            difficulty: 难度
            content: 题目内容
            options: 选项列表
            correct_answer: 正确答案
            explanation: 解析

        Returns:
            保存是否成功
        """
        try:
            options_json = json.dumps(options)

            correct_answer_id = ""
            for option in options:
                if option['content'] == correct_answer:
                    correct_answer_id = option['id']
                    break

            if not correct_answer_id:
                if options:
                    correct_answer_id = options[0]['id']

            cursor = self.db_conn.cursor()
            cursor.execute('''
                INSERT INTO question_bank (language, category, difficulty, content, options, correct_answer, explanation)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (language, category, difficulty, content, options_json, correct_answer_id, explanation))

            self.db_conn.commit()
            logger.info(f"成功保存题目到数据库,ID: {cursor.lastrowid}")
            return True

        except Exception as e:
            logger.error(f"保存题目到数据库失败: {str(e)}")
            self.db_conn.rollback()
            return False

    def load_question_bank(self, num_questions=10):
        """载录题库

        Args:
            num_questions: 要生成的题目数量
        """
        logger.info(f"开始载录题库,计划生成{num_questions}道题目")

        init_db()

        generated_count = 0
        attempts = 0
        max_attempts = num_questions * 2

        while generated_count < num_questions and attempts < max_attempts:
            attempts += 1

            import random
            language = random.choice(self.languages)
            category = random.choice(self.categories)
            difficulty = random.choice(self.difficulties)

            logger.info(f"正在生成第{generated_count+1}道题目: {language} {category} 难度{difficulty}")

            if category == '听力':
                question_content, correct_answer = self._generate_listening_question(language, difficulty)
            else:
                question_content, correct_answer = self._generate_question_content(language, category, difficulty)

            if not question_content or not correct_answer:
                logger.warning("跳过生成失败的题目")
                continue

            options = self._generate_options(question_content, category, language, correct_answer)

            if not options or len(options) < 4:
                logger.warning("选项生成失败或数量不足,跳过该题目")
                continue

            if self._save_to_database(language, category, difficulty, question_content, options, correct_answer):
                generated_count += 1

            time.sleep(1)

        logger.info(f"题库载录完成,成功生成{generated_count}道题目")

        self.db_conn.close()

    def verify_question_bank(self):
        """验证题库中的题目和选项对应关系"""
        logger.info("开始验证题库")

        init_db()

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT id, content, options, correct_answer FROM question_bank')
        questions = cursor.fetchall()

        logger.info(f"共查询到{len(questions)}道题目")

        invalid_questions = []

        for question in questions:
            question_id = question[0]
            content = question[1]
            options_json = question[2]
            correct_answer = question[3]

            try:
                options = json.loads(options_json) if isinstance(options_json, str) else options_json

                option_ids = [opt['id'] for opt in options]
                if correct_answer not in option_ids:
                    invalid_questions.append({
                        'id': question_id,
                        'content': content,
                        'option_ids': option_ids,
                        'error': f"正确答案ID {correct_answer} 不在选项中"
                    })
                    logger.warning(f"题目ID {question_id} 验证失败: 正确答案ID {correct_answer} 不在选项中")
                else:
                    logger.info(f"题目ID {question_id} 验证通过")

            except Exception as e:
                invalid_questions.append({
                    'id': question_id,
                    'content': content,
                    'error': str(e)
                })
                logger.error(f"题目ID {question_id} 解析失败: {str(e)}")

        conn.close()

        logger.info(f"题库验证完成,共发现{len(invalid_questions)}道无效题目")

        if invalid_questions:
            for q in invalid_questions:
                logger.info(f"  题目ID: {q['id']}, 错误: {q.get('error', '未知错误')}")

        return invalid_questions


if __name__ == "__main__":
    loader = AIQuestionBankLoader()

    loader.load_question_bank(num_questions=20)

    loader.verify_question_bank()
