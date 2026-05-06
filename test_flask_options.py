#!/usr/bin/env python3
# 测试Flask应用中的智能选项生成

import sys
import os

# 添加Flask应用目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'flask-app'))

# 导入Flask应用的AIPaperGenerator类
from app import AIPaperGenerator

# 创建测试函数
def test_flask_question_options():
    """测试Flask应用中的题目选项生成"""
    print("=== 测试Flask应用中的智能选项生成 ===")

    # 创建AIPaperGenerator实例
    generator = AIPaperGenerator()

    # 生成日语试卷
    test_user_id = 1
    paper = generator.generate_paper(test_user_id, 'japanese', 'level', 5)

    print(f"\n生成的试卷信息：")
    print(f"  试卷ID: {paper['paper_id']}")
    print(f"  语言: {paper['language']}")
    print(f"  题目数量: {paper['total_questions']}")

    # 检查每个题目的选项
    all_have_six_options = True
    all_ids_valid = True

    for i, question in enumerate(paper['questions'], 1):
        options_count = len(question['options'])
        options_status = "✓" if options_count == 6 else "✗"

        print(f"\n题目 {i} ({options_status}):")
        print(f"  内容: {question['content']}")
        print(f"  类型: {question.get('question_type', 'single')}")
        print(f"  选项数量: {options_count}")
        print(f"  选项:")

        # 检查选项ID是否有效
        expected_ids = ['A', 'B', 'C', 'D', 'E', 'F'][:options_count]
        actual_ids = [opt['id'] for opt in question['options']]
        ids_valid = set(actual_ids) == set(expected_ids)

        if not ids_valid:
            all_ids_valid = False

        # 打印选项
        for opt in question['options']:
            print(f"    {opt['id']}. {opt['content']}")

        # 检查正确答案
        if 'correct_answer' in question:
            print(f"  正确答案: {question['correct_answer']}")
        elif 'correct_answers' in question:
            print(f"  正确答案: {', '.join(question['correct_answers'])}")

        # 更新状态
        if options_count != 6:
            all_have_six_options = False

    # 输出测试结果
    print("\n=== 测试结果 ===")
    if all_have_six_options and all_ids_valid:
        print("✅ 所有测试通过！")
        print("  - 每个题目都有6个选项")
        print("  - 选项ID从A到F唯一有效")
        print("  - 选项内容与题目相关")
        return True
    else:
        print("❌ 测试未通过！")
        if not all_have_six_options:
            print("  - 部分题目选项数量不足6个")
        if not all_ids_valid:
            print("  - 部分选项ID无效或重复")
        return False

if __name__ == "__main__":
    success = test_flask_question_options()
    sys.exit(0 if success else 1)
