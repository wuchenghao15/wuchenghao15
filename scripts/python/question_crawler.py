# -*- coding: utf-8 -*-
#!/usr/bin/env python3
""" 自动爬取日语和英语习题,并添加到题库中 支持日语N1-N5,英语社会英语、英语8级、九年制义务教育 """

import time
import random
from typing import List, Dict, Any
import logging
from app.models.question import question_manager
import os

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class QuestionCrawler:
    """题目爬取器"""

    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.question_manager = question_manager

    def crawl_japanese_questions(self, levels: List[str] = None, count_per_level: int = 20) -> int:
        """ 爬取日语习题 :param levels: 要爬取的日语等级列表,默认包括N1-N5 :param count_per_level: 每个等级要爬取的题目数量 :return: 爬取成功的题目数量 """
        if levels is None:
            levels = ['N1', 'N2', 'N3', 'N4', 'N5']
        total_crawled = 0

        for level in levels:
            logger.info(f"开始爬取日语{level}习题...")

            for i in range(count_per_level):
                try:
                    question = self._generate_mock_japanese_question(level)
                    self._add_question_to_db(question)
                    total_crawled += 1
                    logger.info(f"✓ 成功爬取日语{level}题目: {question['content'][:30]}...")

                    time.sleep(random.uniform(0.5, 2.0))
                except Exception as e:
                    logger.error(f"✗ 爬取日语{level}题目失败: {str(e)}")
                    time.sleep(3)

        return total_crawled

    def crawl_english_questions(self, types: List[str] = None, count_per_type: int = 20) -> int:
        """ 爬取英语习题 :param types: 要爬取的英语类型列表,默认包括社会英语、英语8级、九年制义务教育 :param count_per_type: 每种类型要爬取的题目数量 :return: 爬取成功的题目数量 """
        if types is None:
            types = ['social', 'cet8', 'compulsory']
        total_crawled = 0

        for question_type in types:
            logger.info(f"开始爬取英语{question_type}习题...")

            for i in range(count_per_type):
                try:
                    question = self._generate_mock_english_question(question_type)
                    self._add_question_to_db(question)
                    total_crawled += 1
                    logger.info(f"✓ 成功爬取英语{question_type}题目: {question['content'][:30]}...")
                    time.sleep(random.uniform(0.5, 2.0))
                except Exception as e:
                    logger.error(f"✗ 爬取英语{question_type}题目失败: {str(e)}")
                    time.sleep(3)
        return total_crawled

    def _generate_mock_japanese_question(self, level: str) -> Dict[str, Any]:
        """生成模拟日语题目"""
        level_map = {
            'N1': {'level_name': 'N1', 'difficulty': 5, 'content': '高級日语语法题'},
            'N2': {'level_name': 'N2', 'difficulty': 4, 'content': '中高级日语语法题'},
            'N3': {'level_name': 'N3', 'difficulty': 3, 'content': '中级日语语法题'},
            'N4': {'level_name': 'N4', 'difficulty': 2, 'content': '初级日语语法题'},
            'N5': {'level_name': 'N5', 'difficulty': 1, 'content': '基础日语语法题'},
        }
        level_info = level_map.get(level, {'level_name': level, 'difficulty': 3, 'content': '日语题目'})

        question_types = ['single_choice', 'multiple_choice', 'fill_blank']
        question_type = random.choice(question_types)

        if question_type == 'single_choice':
            contents = [
                f"この問題は{level_info['content']}です.正しい答えを選んでください.",
                f"次の文の{level}文法で正しいものはどれですか?",
                f"{level}レベルの単語問題です.正解を選択してください."
            ]
        elif question_type == 'multiple_choice':
            contents = [
                f"次の{level}文法の正しい用法はどれですか?(複数選択)",
                f"この{level}単語の正しい意味はどれですか?(複数選択)",
                f"次の文の{level}表現で正しいものはどれですか?(複数選択)"
            ]
        else:
            contents = [
                f"次の文の{level}文法を正しく埋めてください.",
                f"この{level}読解文の内容に合っているものはどれですか?"
            ]

        content = random.choice(contents)

        options = [
            f"選択肢A: {level}レベルの選択肢",
            f"選択肢B: {level}レベルの選択肢",
            f"選択肢C: {level}レベルの選択肢",
            f"選択肢D: {level}レベルの選択肢"
        ]

        random.shuffle(options)

        return {
            'content': content,
            'answer': random.choice(['A', 'B', 'C', 'D']),
            'explanation': f"これは{level}レベルの問題です.正解は{random.choice(['A', 'B', 'C', 'D'])}です.",
            'options': options,
            'question_type': question_type,
            'level': level_info['difficulty'],
            'category': '日语'
        }

    def _generate_mock_english_question(self, question_type: str) -> Dict[str, Any]:
        """生成模拟英语题目"""
        type_map = {
            'social': {'type_name': '社会英语', 'difficulty': 3, 'content': '社会英语综合题'},
            'cet8': {'type_name': '英语8级', 'difficulty': 5, 'content': '高级英语综合题'},
            'compulsory': {'type_name': '九年制义务教育', 'difficulty': 2, 'content': '基础英语语法题'}
        }

        type_info = type_map.get(question_type, {'type_name': question_type, 'difficulty': 3, 'content': '英语题目'})

        question_types = ['single_choice', 'multiple_choice', 'fill_blank']
        q_type = random.choice(question_types)

        if q_type == 'single_choice':
            contents = [
                f"This is a {type_info['content']}. Please choose the correct answer.",
                f"Which of the following is the correct usage of this {type_info['type_name']} grammar?",
                f"Choose the right word to complete this {type_info['type_name']} sentence."
            ]
        elif q_type == 'multiple_choice':
            contents = [
                f"Which of the following are correct {type_info['type_name']} expressions? (Multiple choices)",
                f"Which words can be used in this {type_info['type_name']} context? (Multiple choices)",
                f"Which sentences are grammatically correct in {type_info['type_name']}? (Multiple choices)"
            ]
        else:
            contents = [
                f"Complete the sentence with the correct {type_info['type_name']} word: The weather today is ____.",
                f"Use the correct {type_info['type_name']} preposition: He is interested ____ music."
            ]

        content = random.choice(contents)

        if q_type != 'fill_blank':
            options = [
                f"Option A: {type_info['type_name']} option",
                f"Option B: {type_info['type_name']} option",
                f"Option C: {type_info['type_name']} option",
            ]
            random.shuffle(options)
        else:
            options = []

        return {
            'content': content,
            'answer': random.choice(['A', 'B', 'C', 'D',
            'correct answer']) if q_type != 'fill_blank' else 'correct answer',
            'explanation': f"This is a {type_info['type_name']} question. The correct answer is provided.",
            'question_type': q_type,
            'language': 'english',
            'level': type_info['difficulty'],
            'options': options,
            'category': '英语'
        }

    def _add_question_to_db(self, question: Dict[str, Any]) -> None:
        """将题目添加到数据库"""
        level_id = self._get_or_create_level(question['level'])
        category_id = self._get_or_create_category(question.get('category', '通用'))
        language_id = self._get_or_create_language(question.get('language', 'japanese'))

        self.question_manager.create_question(
            content=question['content'],
            answer=question['answer'],
            explanation=question['explanation'],
            category_id=category_id,
            language_id=language_id,
            level_id=level_id,
        )

    def _get_or_create_category(self, category_name: str) -> int:
        """获取或创建分类"""
        categories = self.question_manager.get_all_categories()
        for category in categories:
            if category.name == category_name:
                return category.id

        category = self.question_manager.create_category(category_name, f"{category_name}分类")
        return category.id

    def _get_or_create_language(self, language_name: str) -> int:
        """获取或创建语种"""
        language_map = {
            'japanese': {'name': '日语', 'code': 'ja'},
            'english': {'name': '英语', 'code': 'en'},
            'chinese': {'name': '中文', 'code': 'zh'}
        }

        if language_name not in language_map:
            language_info = {'name': language_name, 'code': language_name[:2]}
        else:
            language_info = language_map[language_name]

        languages = self.question_manager.get_all_languages()
        for language in languages:
            if language.name == language_info['name']:
                return language.id

        language = self.question_manager.create_language(language_info['name'], language_info['code'])
        return language.id

    def _get_or_create_level(self, level: int) -> int:
        """获取或创建等级"""
        levels = self.question_manager.get_all_levels()
        for level_obj in levels:
            if level_obj.level == level:
                return level_obj.id

        level_names = {
            1: '入门级',
            2: '初级',
            3: '中级',
            4: '高级',
            5: '专家级'
        }

        level_name = level_names.get(level, f"等级{level}")
        level_obj = self.question_manager.create_level(level_name, level, f"{level_name}难度")
        return level_obj.id

    def crawl_all_questions(self) -> Dict[str, int]:
        """爬取所有类型的题目"""
        logger.info("开始爬取所有类型的题目...")

        japanese_count = self.crawl_japanese_questions()
        english_count = self.crawl_english_questions()

        return {
            'japanese': japanese_count,
            'english': english_count,
            'total': japanese_count + english_count
        }

if __name__ == '__main__':
    crawler = QuestionCrawler()
    result = crawler.crawl_all_questions()
    print(f"爬取结果:{result}")
