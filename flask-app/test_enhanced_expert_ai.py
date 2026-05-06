#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试优化后的专家AI服务

import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.enhanced_expert_ai_service import EnhancedExpertAIService


def main():
    print("=" * 60)
    print("测试优化后的专家AI服务")
    print("=" * 60)
    service = EnhancedExpertAIService()

    # 1. 测试题库健康分析
    print("\n[1] 测试题库健康分析...")
    health_report = service.analyze_question_bank_health('japanese')
    if health_report:
        print(f"  整体状态: {health_report['overall_health']}")
        print(f"  问题数量: {len(health_report['issues'])}")
        print(f"  总题目数: {health_report['statistics']['total_questions']}")
        if health_report['issues']:
            print("  发现的问题:")
            for issue in health_report['issues'][:3]:
                print(f"    - {issue}")

    # 2. 测试生成提升试卷
    print("\n[2] 测试生成提升试卷...")
    user_id = 1
    questions = service.generate_improvement_exam(user_id, exam_size=10, language='japanese')
    print(f"  生成题目数: {len(questions)}")
    for i, q in enumerate(questions[:3], 1):
        print(f"  题目{i}: 等级{q['level_id']}, 题型{q['question_type']}")
        if 'audio' in q:
            print(f"       - 音频: {q['audio'].get('accent', 'none')}")

    # 3. 测试生成题库需求
    print("\n[3] 测试生成题库需求...")
    requirements = service.generate_question_bank_requirements('japanese')
    if requirements:
        print(f"  高优先级任务: {len(requirements['priority_tasks'])}")
        print(f"  普通任务: {len(requirements['normal_tasks'])}")
        print(f"  长期任务: {len(requirements['long_term_tasks'])}")
        if requirements['priority_tasks']:
            print("  高优先级任务示例:")
            for task in requirements['priority_tasks'][:2]:
                print(f"    - {task}")

    print("\n" + "=" * 60)
    print("优化后的专家AI服务测试完成！")
    print("=" * 60)

if __name__ == "__main__":
    main()

"""