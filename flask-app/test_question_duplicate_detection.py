#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试题库扩展系统的重复检测功能

import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.models.question import QuestionManager
from app.ai.question_bank_expander import QuestionBankExpander


def test_duplicate_detection():
    """测试重复检测功能"""
    print("=" * 60)
    print("测试题库扩展系统的重复检测功能")
    print("=" * 60)
    try:
        # 初始化 QuestionManager
        question_manager = QuestionManager()

        # 测试 1: 完全相同的题目
        print("\n[1] 测试完全相同的题目...")
        test_content = "1 + 1 = ?"
        is_duplicate = question_manager.check_question_duplicate(test_content, 1, 1)
        print(f"  题目: '{test_content}'")
        print(f"  是否重复: {is_duplicate}")

        # 测试 2: 相似度高的题目
        print("\n[2] 测试相似度高的题目...")
        similar_content = "1 + 1 等于多少?"
        is_duplicate = question_manager.check_question_duplicate(similar_content, 1, 1)
        print(f"  题目: '{similar_content}'")
        print(f"  是否重复: {is_duplicate}")

        print("\n[3] 测试完全不同的题目...")
        different_content = "2 + 2 = ?"
        is_duplicate = question_manager.check_question_duplicate(different_content, 1, 1)
        print(f"  题目: '{different_content}'")
        print(f"  是否重复: {is_duplicate}")

        print("\n[4] 测试不同等级的相同题目...")
        same_content = "1 + 1 = ?"
        is_duplicate = question_manager.check_question_duplicate(same_content, 1, 2)  # 等级2
        print(f"  题目: '{same_content}' (等级2)")
        print(f"  是否重复: {is_duplicate}")

        print("\n[5] 测试不同语言的相同题目...")
        same_content = "1 + 1 = ?"
        is_duplicate = question_manager.check_question_duplicate(same_content, 2, 1)  # 英语
        print(f"  题目: '{same_content}' (英语)")
        print(f"  是否重复: {is_duplicate}")

        str1 = "1 + 1 = ?"
        str2 = "1 + 1 等于多少?"
        str3 = "2 + 2 = ?"

        similarity1 = question_manager._calculate_similarity(str1, str2)
        similarity2 = question_manager._calculate_similarity(str1, str3)

        print(f"  相似度 1: '{str1}' vs '{str2}' = {similarity1:.2f}")
        print(f"  相似度 2: '{str1}' vs '{str3}' = {similarity2:.2f}")

        # 测试 7: 测试题库扩展系统的重复检测
        print("\n[7] 测试题库扩展系统...")
        expander = QuestionBankExpander()
        expander.initialize()

        # 生成一些题目并检查是否重复
        expansion_result = expander.expand_question_bank(count=5)
        print(f"  拓展结果: {expansion_result}")
        print(f"  成功生成: {expansion_result.get('questions_generated', 0)}")
        print(f"  失败: {expansion_result.get('questions_failed', 0)}")

        print("\n" + "=" * 60)
        print("重复检测功能测试完成！")
        print("=" * 60)
        return True

    except Exception as e:
        print(f"\n✗ 测试过程中发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_duplicate_detection()
    sys.exit(0 if success else 1)
