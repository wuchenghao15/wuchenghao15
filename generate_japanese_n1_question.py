#!/usr/bin/env python3
"""
生成日语N1级别的题目

import sys
import os
import random
from exam_generator import ExamGenerator

# 创建试卷生成器实例
generator = ExamGenerator()

# 直接生成日语N1级别的题目
def generate_japanese_n1_question():
    """生成日语N1级别的题目"""
    # 选择随机题型
    question_types = ["vocabulary", "grammar", "reading"]
    question_type = random.choice(question_types)

    # 生成题目配置
    config = {
        "min_difficulty": 4,  # N1难度范围
        "max_difficulty": 5
    }

    # 生成题目
    questions = generator._generate_section_questions(question_type, 1, config)

    if questions:
        return question_types, questions[0]
    return None, None

# 直接生成日语N1题目
type_list, question = generate_japanese_n1_question()

if question:
    # 打印题目信息
    print("=== 日语N1级别题目 ===")

    # 获取题型中文名称
    type_mapping = {
        "vocabulary": "词汇部分",
        "grammar": "语法部分",
        "reading": "阅读部分"
    }
    print(f"题型: {type_mapping.get(question['type'], question['type'])}")
    print(f"子题型: {question['subtype']}")
    print(f"题目内容:")

    # 如果是阅读题，显示文章
    if 'passage' in question and question['passage']:
        print(f"\n文章:\n{question['passage']}\n")

    print(f"问题: {question['question']}")

    # 显示选项
    if question['options']:
        print(f"\n选项:")
        for i, option in enumerate(question['options'], 1):
            print(f"{i}. {option}")

    print(f"\n正确答案: {question['correct_answer']}")
    print(f"解析: {question.get('explanation', '无解析')}")
    print(f"难度: {'★' * int(question['difficulty'])}")
else:
    print("无法生成日语N1级别题目，将使用试卷生成器生成")

    # 使用试卷生成器生成
    n1_exam_config = {
        "language": "ja-JP",
        "difficulty_level": "N1",
        "adaptive_difficulty": 5,  # N1对应最高难度
        "total_questions": 5,  # 生成5道题，增加选择范围
        "duration": 10,
        "total_score": 100
    }
    # 生成试卷
    exam = generator.generate_exam(n1_exam_config)

    # 提取题目
    if exam["sections"]:
        # 只选择词汇、语法或阅读部分
        valid_sections = [s for s in exam["sections"] if s['type'] in ["vocabulary", "grammar", "reading"]]
        if valid_sections:
            # 随机选择一个题型
            section = random.choice(valid_sections)
            if section["questions"]:
                # 随机选择一道题
                question = random.choice(section["questions"])

                # 打印题目信息
                print("=== 日语N1级别题目 ===")
                print(f"题型: {section['title']}")
                print(f"题目内容:")
                # 如果是阅读题，显示文章
                if 'passage' in question and question['passage']:


                # 显示选项
                    print(f"\n选项:")
                        print(f"{i}. {option}")
                print(f"\n正确答案: {question['correct_answer']}")
                print(f"解析: {question.get('explanation', '无解析')}")
            else:
                print("未生成题目")
            print("无有效题型")
        print("未生成试卷")
