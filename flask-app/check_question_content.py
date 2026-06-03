# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
检查数据库中题目的实际内容

import logging
logger = logging.getLogger(__name__)
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.models.question import QuestionManager

def check_question_content():
    检查数据库中题目的实际内容
    print("================================================================================" )
    print("================================================================================" )

    try:
        # 初始化题目管理器
        question_manager = QuestionManager()
        print("题目管理器初始化成功")

        # 获取前10道题目
        questions = question_manager.get_questions(limit=10)
        print(f"共获取到 {len(questions)} 道题目")

        # 打印每道题目的内容
        for i, question in enumerate(questions, 1):
            print(f"\n题目 {i}:")
            print(f"内容: {question.content}")
            print(f"题目类型: {question.question_type}")
            print(f"等级ID: {question.level_id}")
            print(f"分类ID: {question.category_id}")
            print(f"难度分数: {question.difficulty_score}")
            print(f"答案: {question.answer}")
            print(f"解析: {question.explanation}")
            print("-" * 50)

    except Exception as e:
        print(f"检查失败: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        print("\n================================================================================" )
        print("检查完成!")
        print("================================================================================" )

if __name__ == "__main__":
    check_question_content()

"""