#!/usr/bin/env python3
"""
测试新功能脚本
测试基于用户等级的出题、答题行为记录和个性化试卷生成
"""

import os
import sys
import json

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.services.level_based_question_generator import get_level_based_generator
from app.services.exam_service import get_exam_service
from app.services.user_answer_analysis_service import get_user_answer_analysis_service
from app.services.expert_ai_analysis_service import get_expert_ai_analysis_service

def test_level_based_question_generation():
    """测试基于用户等级的题目生成"""
    print("=== 测试基于用户等级的题目生成 ===")
    
    generator = get_level_based_generator()
    user_id = 1
    
    # 获取用户等级
    user_level = generator.get_user_level(user_id)
    print(f"用户等级: {user_level}")
    
    # 生成考试题目
    questions = generator.generate_exam(user_id, exam_size=10, language='japanese')
    print(f"生成题目数量: {len(questions)}")
    
    # 分析题目难度分布
    level_counts = {}
    for q in questions:
        level = q['level_id']
        level_counts[level] = level_counts.get(level, 0) + 1
    
    print("题目难度分布:")
    for level, count in level_counts.items():
        print(f"  等级 {level}: {count} 题")
    
    # 打印前几个题目
    print("\n前3个题目:")
    for i, q in enumerate(questions[:3], 1):
        print(f"题目 {i}: 难度等级 {q['level_id']}, 题型 {q['question_type']}")
        print(f"内容: {q['content'][:50]}...")
        print()
    
    return True

def test_exam_behavior_recording():
    """测试答题行为记录"""
    print("=== 测试答题行为记录 ===")
    
    exam_service = get_exam_service()
    user_id = 1
    exam_id = 1
    
    # 模拟记录答题行为
    for question_id in range(1, 6):
        # 记录开始答题
        exam_service.record_exam_behavior(
            user_id=user_id,
            exam_id=exam_id,
            question_id=question_id,
            action_type="start_answer",
            time_spent=0
        )
        
        # 记录回答
        exam_service.record_exam_behavior(
            user_id=user_id,
            exam_id=exam_id,
            question_id=question_id,
            action_type="answer",
            action_data={"selected_option": "A"},
            time_spent=15,
            attempt_count=1,
            difficulty_perceived=3,
            confidence_level=4
        )
        
        # 记录修改答案
        if question_id % 2 == 0:
            exam_service.record_exam_behavior(
                user_id=user_id,
                exam_id=exam_id,
                question_id=question_id,
                action_type="modify_answer",
                action_data={"selected_option": "B"},
                time_spent=5,
                attempt_count=2,
                difficulty_perceived=3,
                confidence_level=3
            )
    
    # 获取答题行为记录
    behaviors = exam_service.get_exam_behavior(user_id, exam_id)
    print(f"记录的行为数量: {len(behaviors)}")
    
    # 分析行为记录
    action_counts = {}
    for behavior in behaviors:
        action_type = behavior['action_type']
        action_counts[action_type] = action_counts.get(action_type, 0) + 1
    
    print("行为类型分布:")
    for action_type, count in action_counts.items():
        print(f"  {action_type}: {count} 次")
    
    # 分析答题行为模式
    behavior_analysis = exam_service.analyze_answer_behavior(user_id, exam_id)
    if behavior_analysis:
        print("\n答题行为分析:")
        print(f"总动作数: {behavior_analysis['total_actions']}")
        print(f"平均每题时间: {behavior_analysis['average_time_per_question']:.2f} 秒")
        print(f"修改次数: {behavior_analysis['modification_count']}")
    
    return True

def test_user_answer_analysis():
    """测试用户答题习惯分析"""
    print("=== 测试用户答题习惯分析 ===")
    
    analysis_service = get_user_answer_analysis_service()
    user_id = 1
    
    # 分析薄弱环节
    weaknesses = analysis_service.analyze_user_weaknesses(user_id)
    if weaknesses:
        print("薄弱环节分析:")
        print(f"整体准确率: {weaknesses['overall_accuracy']:.2f}")
        print(f"总答题数: {weaknesses['total_answers']}")
        print(f"正确答题数: {weaknesses['correct_answers']}")
        
        print("\n薄弱题型:")
        for weak_type in weaknesses['weak_question_types']:
            print(f"  题型: {weak_type['question_type']}, 准确率: {weak_type['accuracy']:.2f}")
        
        print("\n建议:")
        for recommendation in weaknesses['recommendations']:
            print(f"  - {recommendation}")
    
    # 分析答题模式
    patterns = analysis_service.analyze_answer_patterns(user_id, days=30)
    if patterns:
        print("\n答题模式分析:")
        if patterns['best_time_slot']:
            print(f"最佳答题时间: {patterns['best_time_slot']}")
        
        print("\n建议:")
        for recommendation in patterns['recommendations']:
            print(f"  - {recommendation}")
    
    # 生成个性化学习计划
    study_plan = analysis_service.generate_personalized_study_plan(user_id)
    if study_plan:
        print("\n个性化学习计划:")
        print("薄弱环节:")
        for area in study_plan['weak_areas']:
            print(f"  - {area['area']}: 准确率 {area['accuracy']:.2f}")
            print(f"    建议: {area['recommendation']}")
        
        print("\n学习目标:")
        for goal in study_plan['goals']:
            print(f"  - {goal}")
    
    return True

def test_expert_ai_analysis():
    """测试专家AI分析功能"""
    print("=== 测试专家AI分析功能 ===")
    
    expert_service = get_expert_ai_analysis_service()
    user_id = 1
    
    # 分析用户表现
    performance = expert_service.analyze_user_performance(user_id)
    if performance:
        print("用户表现分析:")
        print(f"整体准确率: {performance['overall_accuracy']:.2f}")
        print(f"总答题数: {performance['total_answers']}")
        
        print("\n薄弱环节:")
        for weak_area in performance['weak_areas']:
            print(f"  题型: {weak_area['question_type']}, 准确率: {weak_area['accuracy']:.2f}")
        
        print("\n优势环节:")
        for strong_area in performance['strong_areas']:
            print(f"  题型: {strong_area['question_type']}, 准确率: {strong_area['accuracy']:.2f}")
    
    # 生成个性化试卷
    exam_questions = expert_service.generate_personalized_exam(user_id, exam_size=10, language='japanese')
    print(f"\n生成个性化试卷题目数量: {len(exam_questions)}")
    
    # 分析题目分布
    level_counts = {}
    type_counts = {}
    for q in exam_questions:
        level = q['level_id']
        level_counts[level] = level_counts.get(level, 0) + 1
        q_type = q['question_type']
        type_counts[q_type] = type_counts.get(q_type, 0) + 1
    
    print("\n题目难度分布:")
    for level, count in level_counts.items():
        print(f"  等级 {level}: {count} 题")
    
    print("\n题目类型分布:")
    for q_type, count in type_counts.items():
        print(f"  {q_type}: {count} 题")
    
    # 打印前几个题目
    print("\n前3个题目:")
    for i, q in enumerate(exam_questions[:3], 1):
        print(f"题目 {i}: 难度等级 {q['level_id']}, 题型 {q['question_type']}")
        print(f"内容: {q['content'][:50]}...")
        print()
    
    return True

def main():
    """主测试函数"""
    print("开始测试新功能...\n")
    
    # 测试基于用户等级的题目生成
    test_level_based_question_generation()
    print()
    
    # 测试答题行为记录
    test_exam_behavior_recording()
    print()
    
    # 测试用户答题习惯分析
    test_user_answer_analysis()
    print()
    
    # 测试专家AI分析功能
    test_expert_ai_analysis()
    print()
    
    print("所有测试完成！")

if __name__ == "__main__":
    main()
