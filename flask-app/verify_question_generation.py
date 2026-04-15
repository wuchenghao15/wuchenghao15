#!/usr/bin/env python3
"""
验证题库扩展系统能够生成不重复的题目
"""

import sys
import os

# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.ai.question_bank_expander import QuestionBankExpander
from app.models.question import Question

def verify_unique_question_generation():
    """
    验证题库扩展系统能够生成不重复的题目
    """
    print("================================================================================")
    print("验证题库扩展系统能够生成不重复的题目")
    print("================================================================================")
    
    try:
        # 初始化题目模型
        question_model = Question()
        
        # 获取当前题库中的题目数量
        initial_questions = question_model.get_questions()
        initial_count = len(initial_questions)
        print(f"初始题库题目数量: {initial_count}")
        
        # 初始化题库扩展系统
        expander = QuestionBankExpander()
        print("题库扩展系统初始化成功")
        
        # 生成 10 道题目
        generated_questions = []
        for i in range(10):
            print(f"\n生成第 {i+1} 道题目:")
            
            # 随机选择参数
            language_id = 2  # 英语
            level_id = 1  # 入门级
            category_id = 2  # 英语分类
            question_type = "single_choice"
            difficulty = "easy"
            
            # 生成题目
            question = expander._generate_question(
                language_id=language_id,
                level_id=level_id,
                category_id=category_id,
                question_type=question_type,
                difficulty=difficulty
            )
            
            if question:
                print(f"  成功生成题目: {question.content}")
                generated_questions.append(question)
            else:
                print(f"  生成失败")
        
        # 获取生成后的题目数量
        final_questions = question_model.get_questions()
        final_count = len(final_questions)
        print(f"\n生成后题库题目数量: {final_count}")
        print(f"成功生成题目数量: {len(generated_questions)}")
        
        # 检查生成的题目是否重复
        content_set = set()
        duplicate_count = 0
        
        for question in generated_questions:
            if question.content in content_set:
                duplicate_count += 1
                print(f"  重复题目: {question.content}")
            else:
                content_set.add(question.content)
        
        print(f"\n重复题目数量: {duplicate_count}")
        
        if duplicate_count == 0:
            print("\n✅ 验证成功: 生成的题目都是不重复的")
        else:
            print("\n❌ 验证失败: 生成的题目存在重复")
        
    except Exception as e:
        print(f"\n❌ 验证失败: {str(e)}")
    finally:
        print("\n================================================================================")
        print("验证完成！")
        print("================================================================================")

if __name__ == "__main__":
    verify_unique_question_generation()
