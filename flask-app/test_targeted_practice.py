#!/usr/bin/env python3
# 测试针对性练习和专题讲解功能

import sys
import json
from ai_employee_system import TestSystemAIEmployee

def test_targeted_practice():
    """测试针对性练习和专题讲解功能"""
    print("=== 测试针对性练习和专题讲解功能 ===")
    ai_employee = TestSystemAIEmployee("test_001", "测试员工")
    
    # 测试1：分析用户薄弱环节
    print("\n1. 测试分析用户薄弱环节：")
    result = ai_employee.analyze_user_weaknesses({
        "user_id": 1,  # 假设用户ID为1
        "language": "japanese"
    })
    
    if result["success"]:
        print(f"   成功分析用户薄弱环节")
        print(f"   薄弱环节数量: {len(result['weaknesses'])}")
        print(f"   错误分析结果: {json.dumps(result['error_analysis'], ensure_ascii=False)}")
    else:
        print(f"   分析失败: {result['message']}")
    
    # 测试2：获取推荐专题
    print("\n2. 测试获取推荐专题：")
    result = ai_employee.get_recommended_topics({
        "user_id": 1,
        "language": "japanese",
        "max_topics": 3
    })
    
    if result["success"]:
        print(f"   成功获取推荐专题")
        print(f"   推荐专题数量: {len(result['recommended_topics'])}")
        for topic in result['recommended_topics']:
            print(f"   - {topic['topic_name']} ({topic['priority']})")
    else:
        print(f"   获取失败: {result['message']}")
    
    # 测试3：生成专题讲解
    print("\n3. 测试生成专题讲解：")
    result = ai_employee.generate_topic_explanation({
        "topic_name": "日语语法",
        "language": "japanese",
        "level": "N5",
        "explanation_type": "comprehensive"
    })
    
    if result["success"]:
        print(f"   成功生成专题讲解")
        topic_explanation = result["topic_explanation"]
        print(f"   专题名称: {topic_explanation['topic_name']}")
        print(f"   讲解类型: {topic_explanation['explanation_type']}")
        print(f"   关键点数量: {len(topic_explanation['content']['key_points'])}")
    else:
        print(f"   生成失败: {result['message']}")
    
    # 测试4：生成针对性练习
    print("\n4. 测试生成针对性练习：")
    result = ai_employee.generate_targeted_practice({
        "user_id": 1,
        "language": "japanese",
        "target_section": "语法",
        "question_count": 5,
        "difficulty": "easy"
    })
    
    if result["success"]:
        practice_content = result["practice_content"]
        print(f"   成功生成针对性练习")
        print(f"   练习ID: {practice_content['practice_id']}")
        print(f"   题目数量: {practice_content['question_count']}")
        print(f"   目标章节: {practice_content['target_section']}")
        print(f"   难度: {practice_content['difficulty']}")
    else:
        print(f"   生成失败: {result['message']}")

if __name__ == "__main__":
    print("开始测试针对性练习和专题讲解功能...")
    
    try:
        test_targeted_practice()
        print("\n=== 所有测试完成 ===")
    except Exception as e:
        print(f"测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)