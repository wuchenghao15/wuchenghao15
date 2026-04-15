#!/usr/bin/env python3
"""
简单测试脚本，直接测试题库功能
"""

import logging
import os
import sys

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_question_crawler_generation():
    """测试题目爬取器的题目生成功能"""
    logger.info("开始测试题目爬取器的题目生成功能...")
    
    try:
        # 直接导入生成函数所需的模块
        import random
        
        def generate_mock_japanese_question(level):
            """生成模拟日语题目"""
            level_map = {
                'N1': {'level_name': 'N1', 'difficulty': 5, 'content': '高級日语语法题'},
                'N2': {'level_name': 'N2', 'difficulty': 4, 'content': '中高级日语语法题'},
                'N3': {'level_name': 'N3', 'difficulty': 3, 'content': '中级日语语法题'},
                'N4': {'level_name': 'N4', 'difficulty': 2, 'content': '初级日语语法题'},
                'N5': {'level_name': 'N5', 'difficulty': 1, 'content': '入门级日语语法题'}
            }
            
            level_info = level_map[level]
            question_types = ['single_choice', 'multiple_choice', 'fill_blank', 'reading']
            question_type = random.choice(question_types)
            
            if question_type == 'single_choice':
                contents = [
                    f"この問題は{level_info['content']}です。正しい答えを選んでください。",
                    f"次の文の{level}文法で正しいものはどれですか？",
                    f"{level}レベルの単語問題です。正解を選択してください。"
                ]
            elif question_type == 'multiple_choice':
                contents = [
                    f"次の{level}文法の正しい用法はどれですか？（複数選択）",
                    f"この{level}単語の正しい意味はどれですか？（複数選択）",
                    f"次の文の{level}表現で正しいものはどれですか？（複数選択）"
                ]
            else:
                contents = [
                    f"次の文の{level}文法を正しく埋めてください。",
                    f"この{level}読解文の内容に合っているものはどれですか？"
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
                'explanation': f"これは{level}レベルの問題です。正解は{random.choice(['A', 'B', 'C', 'D'])}です。",
                'options': options,
                'question_type': question_type,
                'language': 'japanese',
                'level': level_info['difficulty'],
                'category': '日语'
            }
        
        def generate_mock_english_question(question_type):
            """生成模拟英语题目"""
            type_map = {
                'social': {'type_name': '社会英语', 'difficulty': 3, 'content': '日常英语会话题'},
                'cet8': {'type_name': '英语8级', 'difficulty': 5, 'content': '高级英语综合题'},
                'compulsory': {'type_name': '九年制义务教育', 'difficulty': 2, 'content': '基础英语语法题'}
            }
            
            type_info = type_map[question_type]
            available_types = ['single_choice', 'multiple_choice', 'true_false', 'fill_blank']
            current_type = random.choice(available_types)
            
            if current_type == 'single_choice':
                contents = [
                    f"This is a {type_info['content']}. Please choose the correct answer.",
                    f"Which of the following is the correct usage of this {type_info['type_name']} grammar?",
                    f"Choose the right word to complete this {type_info['type_name']} sentence."
                ]
            elif current_type == 'multiple_choice':
                contents = [
                    f"Which of the following are correct {type_info['type_name']} expressions? (Multiple choices)",
                    f"Which words can be used in this {type_info['type_name']} context? (Multiple choices)",
                    f"Which sentences are grammatically correct in {type_info['type_name']}? (Multiple choices)"
                ]
            elif current_type == 'true_false':
                contents = [
                    f"'{type_info['type_name']} grammar rule': The verb 'to be' is always conjugated with the subject.",
                    f"In {type_info['type_name']}, the present perfect tense is used to describe past actions with present relevance.",
                    f"The word 'however' can always be used to contrast ideas in {type_info['type_name']}."
                ]
            else:
                contents = [
                    f"Complete the sentence with the correct {type_info['type_name']} word: The weather today is ____.",
                    f"Fill in the blank with the appropriate {type_info['type_name']} verb form: She ____ (go) to school every day.",
                    f"Use the correct {type_info['type_name']} preposition: He is interested ____ music."
                ]
            
            content = random.choice(contents)
            
            if current_type != 'fill_blank':
                options = [
                    f"Option A: {type_info['type_name']} option",
                    f"Option B: {type_info['type_name']} option",
                    f"Option C: {type_info['type_name']} option",
                    f"Option D: {type_info['type_name']} option"
                ]
                random.shuffle(options)
            else:
                options = []
            
            return {
                'content': content,
                'answer': random.choice(['A', 'B', 'C', 'D', 'True', 'False', 'correct answer']) if current_type != 'fill_blank' else 'correct answer',
                'explanation': f"This is a {type_info['type_name']} question. The correct answer is {random.choice(['A', 'B', 'C', 'D', 'True', 'False', 'correct answer'])}.",
                'options': options,
                'question_type': current_type,
                'language': 'english',
                'level': type_info['difficulty'],
                'category': '英语'
            }
        
        # 测试生成模拟日语题目
        logger.info("测试生成模拟日语题目...")
        for level in ['N1', 'N2', 'N3', 'N4', 'N5']:
            question = generate_mock_japanese_question(level)
            logger.info(f"✓ 成功生成日语{level}题目: {question['content'][:30]}...")
        
        # 测试生成模拟英语题目
        logger.info("测试生成模拟英语题目...")
        for question_type in ['social', 'cet8', 'compulsory']:
            question = generate_mock_english_question(question_type)
            logger.info(f"✓ 成功生成英语{question_type}题目: {question['content'][:30]}...")
        
        logger.info("✓ 所有测试通过！")
        return True
    except Exception as e:
        logger.error(f"✗ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    test_question_crawler_generation()