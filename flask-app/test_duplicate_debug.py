#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试题库扩展系统的重复检测功能
"""

import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.models.question import QuestionManager
from app.ai.question_bank_expander import QuestionBankExpander


def test_duplicate_debug():
    """调试重复检测功能"""
    print("=" * 80)
    print("调试题库扩展系统的重复检测功能")
    print("=" * 80)
    
    try:
        # 初始化 QuestionManager
        question_manager = QuestionManager()
        
        # 初始化题库扩展系统
        expander = QuestionBankExpander()
        expander.initialize()
        
        # 测试生成题目并检查重复
        print("\n[1] 测试生成题目和重复检测...")
        
        # 尝试生成10个题目
        for i in range(10):
            print(f"\n尝试生成第 {i+1} 个题目:")
            
            # 确定题目参数
            bank_status = expander._analyze_question_bank()
            question_params = expander._determine_question_params(bank_status)
            
            # 生成题目
            question = expander._generate_question(**question_params)
            
            if question:
                print(f"  生成成功: {question.content}")
                print(f"  语言: {question.language_id}, 等级: {question.level_id}, 类型: {question.question_type}")
                
                # 检查是否重复
                is_duplicate = question_manager.check_question_duplicate(
                    question.content, question.language_id, question.level_id
                )
                print(f"  是否重复: {is_duplicate}")
                
                if not is_duplicate:
                    print("  ✓ 题目不重复，可以添加到题库")
                else:
                    print("  ✗ 题目重复，需要重新生成")
            else:
                print("  ✗ 生成失败")
        
        # 查看当前题库中的部分题目
        print("\n[2] 查看当前题库中的题目...")
        questions = question_manager.get_questions(limit=10)
        print(f"当前题库共有 {len(questions)} 道题目")
        
        for i, q in enumerate(questions[:5]):
            print(f"\n题目 {i+1}:")
            print(f"  内容: {q.content}")
            print(f"  语言: {q.language_id}, 等级: {q.level_id}, 类型: {q.question_type}")
        
        print("\n" + "=" * 80)
        print("调试完成！")
        print("=" * 80)
        
        return True
        
    except Exception as e:
        print(f"\n✗ 测试过程中发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_duplicate_debug()
    sys.exit(0 if success else 1)
