#!/usr/bin/env python3
"""
测试数据库替代 JSON 的功能，确保所有 CRUD 操作正常
"""

import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.models.question import question_manager
from app.models.error_question import error_question_manager
from app.utils.logging import logger

def test_question_crud():
    """测试题目 CRUD 操作"""
    print("\n=== 测试题目 CRUD 操作 ===")
    
    # 测试创建题目
    print("1. 创建题目...")
    question = question_manager.create_question(
        content="测试题目：1+1=?",
        answer="2",
        explanation="1+1=2",
        language_id=3,  # 中文
        level_id=1,      # 初级
        question_type="single_choice",
        options=["1", "2", "3", "4"],
        tags=["数学", "基础"]
    )
    if question:
        print(f"   创建成功，题目ID: {question.id}")
    else:
        print("   创建失败")
        return False
    
    # 测试查询题目
    print("2. 查询题目...")
    fetched_question = question_manager.get_question(question.id)
    if fetched_question:
        print(f"   查询成功，题目内容: {fetched_question.content}")
        print(f"   选项: {fetched_question.options}")
        print(f"   标签: {fetched_question.tags}")
    else:
        print("   查询失败")
        return False
    
    # 测试更新题目
    print("3. 更新题目...")
    updated_question = question_manager.update_question(
        question.id,
        content="测试题目：2+2=?",
        answer="4",
        options=["2", "3", "4", "5"],
        tags=["数学", "基础", "加法"]
    )
    if updated_question:
        print(f"   更新成功，新题目内容: {updated_question.content}")
        print(f"   新选项: {updated_question.options}")
        print(f"   新标签: {updated_question.tags}")
    else:
        print("   更新失败")
        return False
    
    # 测试查询题目列表
    print("4. 查询题目列表...")
    questions = question_manager.get_questions(limit=10)
    print(f"   查询到 {len(questions)} 道题目")
    for q in questions[:3]:  # 只显示前3个
        print(f"   - {q.content} (ID: {q.id})")
    
    return True

def test_error_question_crud():
    """测试错题 CRUD 操作"""
    print("\n=== 测试错题 CRUD 操作 ===")
    
    # 先创建一个题目用于测试
    question = question_manager.create_question(
        content="测试错题：3+3=?",
        answer="6",
        explanation="3+3=6",
        language_id=3,
        level_id=1,
        question_type="single_choice",
        options=["5", "6", "7", "8"],
        tags=["数学", "基础"]
    )
    if not question:
        print("   创建测试题目失败")
        return False
    
    # 测试添加错题
    print("1. 添加错题...")
    error_question_id = error_question_manager.add_error_question(
        user_id=1,
        question_id=question.id,
        exam_record_id=1,
        user_answer="5",
        correct_answer="6",
        error_reason="计算错误",
        error_type="calculation",
        tags=["计算错误", "粗心大意"],
        knowledge_point="加法",
        difficulty_level=1
    )
    if error_question_id > 0:
        print(f"   添加成功，错题ID: {error_question_id}")
    else:
        print("   添加失败")
        return False
    
    # 测试获取用户错题列表
    print("2. 获取用户错题列表...")
    error_questions = error_question_manager.get_user_error_questions(user_id=1)
    print(f"   查询到 {len(error_questions)} 条错题")
    for eq in error_questions:
        print(f"   - 题目: {eq['content']}")
        print(f"     用户答案: {eq['user_answer']}")
        print(f"     正确答案: {eq['correct_answer']}")
        print(f"     错误原因: {eq['error_reason']}")
        print(f"     选项: {eq['options']}")
        print(f"     标签: {eq['tags']}")
    
    # 测试更新错题掌握程度
    print("3. 更新错题掌握程度...")
    success = error_question_manager.update_mastery_level(error_question_id, 3)
    if success:
        print("   更新成功")
    else:
        print("   更新失败")
        return False
    
    # 测试复习错题
    print("4. 复习错题...")
    success = error_question_manager.review_error_question(error_question_id, "已理解")
    if success:
        print("   复习成功")
    else:
        print("   复习失败")
        return False
    
    # 测试获取错题统计
    print("5. 获取错题统计...")
    statistics = error_question_manager.get_error_question_statistics(user_id=1)
    print(f"   总错题数: {statistics.get('total_count', 0)}")
    print(f"   错误类型统计: {statistics.get('error_types', {})}")
    print(f"   掌握程度统计: {statistics.get('mastery_levels', {})}")
    
    return True

def main():
    """主测试函数"""
    print("开始测试数据库替代 JSON 的功能...")
    
    # 测试题目 CRUD
    question_test = test_question_crud()
    
    # 测试错题 CRUD
    error_question_test = test_error_question_crud()
    
    if question_test and error_question_test:
        print("\n✅ 所有测试通过！数据库替代 JSON 功能正常。")
    else:
        print("\n❌ 测试失败！")
        sys.exit(1)

if __name__ == "__main__":
    main()
