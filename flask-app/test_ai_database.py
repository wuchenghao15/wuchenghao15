#!/usr/bin/env python3
"""
测试 AI 功能是否能够正确使用数据库存储

import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.ai.teacher_ai import teacher_ai_map
from app.models.error_question import error_question_manager
from app.utils.logging import logger

def test_teacher_ai_database():
    """测试老师 AI 是否能够正确使用数据库存储"""
    print("\n=== 测试老师 AI 功能 ===")

    # 获取数学老师 AI
    math_teacher = teacher_ai_map.get('math')
    if not math_teacher:
        print("   无法获取数学老师 AI")
        return False

    print(f"1. 初始化老师 AI: {math_teacher.name}")

    # 先添加一个错题用于测试
    print("2. 添加测试错题...")
    error_question_id = error_question_manager.add_error_question(
        user_id=1,
        question_id=1,  # 使用之前测试创建的题目
        exam_record_id=1,
        user_answer="3",
        correct_answer="4",
        error_reason="计算错误",
        error_type="calculation",
        tags=["数学", "计算错误"],
        knowledge_point="加法",
        difficulty_level=1
    )

    if error_question_id > 0:
        print(f"   添加成功，错题ID: {error_question_id}")
    else:
        print("   添加错题失败")
        return False
    # 测试分析错题
    print("3. 分析错题...")
    analysis_result = math_teacher.analyze_error_question(error_question_id, user_id=1)
    if analysis_result:
        print(f"   分析成功")
        print(f"   题目内容: {analysis_result.get('question_content')}")
        print(f"   错误原因: {analysis_result.get('error_reason')}")
        print(f"   知识点: {analysis_result.get('knowledge_points')}")
        print(f"   错误模式: {analysis_result.get('error_pattern')}")
        print(f"   建议: {analysis_result.get('suggestions')[:2]}...")  # 只显示前两个建议
    else:
        print("   分析失败")
        return False
    # 测试提供反馈
    print("4. 提供反馈...")
    feedback = math_teacher.provide_feedback(1, error_question_id, analysis_result)
    if feedback:
        print(f"   反馈成功")
        print(f"   反馈内容: {feedback.get('content')}")
        print(f"   建议行动: {feedback.get('suggested_actions')[:2]}...")  # 只显示前两个建议
    else:
        print("   提供反馈失败")
        return False
    # 测试生成练习题目
    print("5. 生成练习题目...")
    practice_questions = math_teacher.generate_practice_questions(
        user_id=1,
        knowledge_points=["加法", "数学"],
        difficulty="medium",
        count=3
    if practice_questions:
        print(f"   生成成功，共 {len(practice_questions)} 道题目")
        for i, q in enumerate(practice_questions, 1):
            print(f"   题目 {i}: {q.get('content')}")
        print("   生成练习题目失败")
        return False
    # 测试跟踪学生进度
    print("6. 跟踪学生进度...")
    progress_report = math_teacher.track_student_progress(user_id=1)
    if progress_report:
        print(f"   跟踪成功")
        print(f"   总错题数: {progress_report.get('statistics', {}).get('total_count')}")
        print(f"   学习趋势: {progress_report.get('learning_trend', {}).get('improvement_rate')}%")
        print(f"   掌握程度: {progress_report.get('mastery_levels', {})}")
    else:
        print("   跟踪学生进度失败")
        return False
    return True

def main():
    """主测试函数"""
    print("开始测试 AI 功能是否能够正确使用数据库存储...")

    # 测试老师 AI
    teacher_ai_test = test_teacher_ai_database()

    if teacher_ai_test:
        print("\n✅ 所有 AI 功能测试通过！AI 能够正确使用数据库存储。")
    else:
        print("\n❌ AI 功能测试失败！")
        sys.exit(1)

if __name__ == "__main__":
    main()
