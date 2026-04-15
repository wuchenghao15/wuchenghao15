#!/usr/bin/env python3
# 测试学生使用偏向性分析和优化功能

import sys
import json
from ai_employee_system import TestSystemAIEmployee

def test_student_preferences():
    """测试学生使用偏向性分析和优化功能"""
    print("=== 测试学生使用偏向性分析和优化功能 ===")
    ai_employee = TestSystemAIEmployee("test_001", "测试员工")
    
    # 测试1：分析学生使用偏向性
    print("\n1. 测试分析学生使用偏向性：")
    result = ai_employee.analyze_student_preferences({
        "user_id": 1,  # 假设用户ID为1
        "language": "japanese",
        "time_range": "30d"
    })
    
    if result["success"]:
        print(f"   成功分析学生使用偏向性")
        preferences = result["preferences"]
        print(f"   题型偏好: {json.dumps(preferences['preferences']['question_types'], ensure_ascii=False)}")
        print(f"   难度偏好: {json.dumps(preferences['preferences']['difficulty_levels'], ensure_ascii=False)}")
    else:
        print(f"   分析失败: {result['message']}")
    
    # 测试2：优化学习路径
    print("\n2. 测试优化学习路径：")
    result = ai_employee.optimize_learning_path({
        "user_id": 1,
        "language": "japanese",
        "current_level": "N5"
    })
    
    if result["success"]:
        print(f"   成功优化学习路径")
        print(f"   学习目标数量: {len(result['optimized_path']['learning_goals'])}")
        for goal in result['optimized_path']['learning_goals']:
            print(f"   - {goal['goal']} (优先级: {goal['priority']})")
    else:
        print(f"   优化失败: {result['message']}")
    
    # 测试3：生成个性化推荐
    print("\n3. 测试生成个性化推荐：")
    result = ai_employee.personalize_recommendations({
        "user_id": 1,
        "language": "japanese",
        "recommendation_type": "all"
    })
    
    if result["success"]:
        print(f"   成功生成个性化推荐")
        recommendations = result["recommendations"]
        print(f"   推荐题目数量: {len(recommendations['recommendations']['questions'])}")
        print(f"   推荐练习集数量: {len(recommendations['recommendations']['practice_sets'])}")
        print(f"   推荐学习资源数量: {len(recommendations['recommendations']['learning_resources'])}")
    else:
        print(f"   生成失败: {result['message']}")

if __name__ == "__main__":
    print("开始测试学生使用偏向性分析和优化功能...")
    
    try:
        test_student_preferences()
        print("\n=== 所有测试完成 ===")
    except Exception as e:
        print(f"测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)