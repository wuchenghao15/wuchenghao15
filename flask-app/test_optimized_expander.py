#!/usr/bin/env python3
"""
测试优化后的题库扩充系统
"""

import sys
import os
import time

# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.ai.question_bank_expander import QuestionBankExpander
from app.models.question import QuestionManager

def test_question_bank_expander():
    """
    测试题库扩充系统
    """
    print("================================================================================")
    print("测试优化后的题库扩充系统")
    print("================================================================================")
    
    try:
        # 初始化题库扩充系统
        expander = QuestionBankExpander()
        print("题库扩充系统初始化成功")
        
        # 初始化题目管理器
        question_manager = QuestionManager()
        
        # 获取初始题库状态
        initial_questions = question_manager.get_questions()
        initial_count = len(initial_questions)
        print(f"初始题库题目数量: {initial_count}")
        
        # 测试1: 测试扩充功能
        print("\n测试1: 测试扩充功能")
        start_time = time.time()
        result = expander.expand_question_bank(count=50)  # 生成50道题目
        end_time = time.time()
        
        print(f"扩充结果: {result}")
        print(f"扩充耗时: {end_time - start_time:.2f} 秒")
        print(f"成功生成题目数量: {result.get('questions_generated', 0)}")
        print(f"失败生成题目数量: {result.get('questions_failed', 0)}")
        
        # 获取扩充后的题库状态
        final_questions = question_manager.get_questions()
        final_count = len(final_questions)
        print(f"扩充后题库题目数量: {final_count}")
        print(f"净增加题目数量: {final_count - initial_count}")
        
        # 测试2: 测试智能参数选择
        print("\n测试2: 测试智能参数选择")
        bank_status = expander._analyze_question_bank()
        print(f"当前题库状态: {bank_status}")
        
        # 测试参数选择
        for i in range(5):
            params = expander._determine_question_params(bank_status)
            print(f"第 {i+1} 次选择的参数: {params}")
        
        # 测试3: 测试不同学科的题目生成
        print("\n测试3: 测试不同学科的题目生成")
        
        # 测试数学题目
        math_question = expander._generate_math_question(
            language_id=3,  # 中文
            level_id=1,     # 初级
            category_id=1,  # 数学分类
            question_type="single_choice",
            difficulty="easy"
        )
        if math_question:
            print(f"生成的数学题目: {math_question.content}")
        
        # 测试英语题目
        english_question = expander._generate_english_question(
            language_id=2,  # 英语
            level_id=1,     # 初级
            category_id=2,  # 英语分类
            question_type="single_choice",
            difficulty="easy"
        )
        if english_question:
            print(f"生成的英语题目: {english_question.content}")
        
        # 测试日语题目
        japanese_question = expander._generate_japanese_question(
            language_id=1,  # 日语
            level_id=1,     # 初级
            category_id=3,  # 日语分类
            question_type="single_choice",
            difficulty="easy"
        )
        if japanese_question:
            print(f"生成的日语题目: {japanese_question.content}")
        
        # 测试语文题目
        chinese_question = expander._generate_chinese_question(
            language_id=3,  # 中文
            level_id=1,     # 初级
            category_id=4,  # 语文分类
            question_type="single_choice",
            difficulty="easy"
        )
        if chinese_question:
            print(f"生成的语文题目: {chinese_question.content}")
        
        print("\n✅ 测试完成！")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        print("\n================================================================================")
        print("测试完成！")
        print("================================================================================")

if __name__ == "__main__":
    test_question_bank_expander()
