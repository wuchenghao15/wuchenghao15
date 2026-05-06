#!/usr/bin/env python3
"""
Test script to verify paper generation follows exam conventions

import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'flask-app'))

# Import the module directly instead of using from...import with hyphen
from app import AIPaperGenerator

def test_paper_generation():
    """测试试卷生成功能"""
    print("Testing paper generation...")

    # 初始化生成器
    generator = AIPaperGenerator()

    # 生成日语试卷
    print("\n1. Generating Japanese test paper...")
    paper = generator.generate_paper(1, 'japanese', 'level', 10)

    # 验证试卷基本信息
    print(f"   Paper ID: {paper['paper_id']}")
    print(f"   Language: {paper['language']}")
    print(f"   Test Type: {paper['test_type']}")
    print(f"   User Level: {paper['user_level']}")
    print(f"   Total Questions: {paper['total_questions']}")

    # 验证试卷说明
    print("\n2. Verifying paper instructions...")
    if 'instructions' in paper:
        print(f"   Instructions included: Yes")
        print(f"   Suggested Time: {paper['instructions']['suggested_time']}")
        print(f"   Question Order Reminder: {paper['instructions']['question_order_reminder']}")
        print(f"   Test Type Reminder: {paper['instructions']['test_type_reminder']}")
    else:
        print("   ERROR: Instructions not included!")
        return False

    # 验证题目排序
    print("\n3. Verifying question order...")
    questions = paper['questions']

    # 检查题目分类
    categories = [q['category'] for q in questions]
    print(f"   Question categories: {categories}")

    # 验证排序规则：词汇 -> 语法 -> 阅读，同类难度递增
    category_order = {'词汇': 1, '语法': 2, '阅读': 3, '其他': 99}
    prev_category_rank = 0
    prev_difficulty = 0

    for i, question in enumerate(questions):
        current_category = question['category']
        current_difficulty = question['difficulty']
        current_category_rank = category_order.get(current_category, 99)

        # 检查类别顺序
        if current_category_rank < prev_category_rank:
            print(f"   ERROR: Question {i+1} ({current_category}) is out of order. Should come after {categories[i-1]}")
            return False

        if current_category_rank == prev_category_rank:
            if current_difficulty < prev_difficulty:
                print(f"   ERROR: Question {i+1} ({current_category}) has lower difficulty than previous question in same category")
                return False

        prev_difficulty = current_difficulty

    print("   Question order: PASS")

    # 验证题目选项数量
    print("\n4. Verifying option count...")
    for i, question in enumerate(questions):
        if len(question['options']) != 6:
            print(f"   ERROR: Question {i+1} has {len(question['options'])} options, should have 6")
            return False
    # 打印最终试卷结构
    print("\n5. Final paper structure:")
    print(f"   Paper includes: {len(questions)} questions")
    print(f"   Categories present: {set(categories)}")
    print(f"   Instructions: Yes")
    print(f"   Suggested time: {paper['suggested_time']} minutes")
    print(f"   Question order: Vocabulary -> Grammar -> Reading")
    print(f"   Difficulty progression: Increasing within each category")

    print("\n✅ All tests passed! Paper generation follows exam conventions.")
    return True

if __name__ == "__main__":
    test_paper_generation()
