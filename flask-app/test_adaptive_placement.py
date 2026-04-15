#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试自适应初次等级评测功能
"""

import sys
import json
import random
from app.services.adaptive_placement_test_service import get_adaptive_placement_test_service


def test_placement_service():
    """测试自适应初次等级评测服务"""
    print("=" * 60)
    print("开始测试自适应初次等级评测服务")
    print("=" * 60)
    
    try:
        service = get_adaptive_placement_test_service()
        
        # 1. 测试生成初始测试
        print("\n[1] 测试生成初始测试...")
        result = service.generate_initial_test('japanese')
        
        if not result.get('success'):
            print(f"✗ 生成初始测试失败: {result.get('error')}")
            return False
        
        print("✓ 生成初始测试成功")
        print(f"  - 测试ID: {result.get('test_id')}")
        print(f"  - 题目数量: {len(result.get('questions', []))}")
        print(f"  - 总题数: {result.get('total_questions')}")
        
        # 保存测试状态
        test_state = {
            'test_id': result['test_id'],
            'language': 'japanese',
            'current_difficulty': result['current_difficulty'],
            'current_question': result['current_question'],
            'adaptive_state': result['adaptive_state']
        }
        
        # 2. 模拟用户答题过程
        print("\n[2] 模拟用户答题过程...")
        total_questions = result.get('total_questions', 30)
        questions_answered = 0
        current_questions = result.get('questions', [])
        
        while questions_answered < total_questions:
            # 模拟用户答案
            answers = {}
            for question in current_questions:
                # 随机生成答案（正确率约70%）
                if random.random() < 0.7:
                    # 假设正确答案是'A'（简化测试）
                    answers[str(question['id'])] = question.get('answer', 'A')
                else:
                    answers[str(question['id'])] = 'B'
            
            print(f"  - 已答题: {questions_answered}/{total_questions}, 当前难度: {test_state['current_difficulty']}")
            
            # 获取下一组题目
            next_result = service.get_next_questions(test_state, answers, 'japanese')
            
            if not next_result.get('success'):
                print(f"✗ 获取下一组题目失败: {next_result.get('error')}")
                return False
            
            # 更新状态
            test_state['current_difficulty'] = next_result['current_difficulty']
            test_state['current_question'] = next_result['current_question']
            test_state['adaptive_state'] = next_result['adaptive_state']
            
            questions_answered = next_result['current_question']
            current_questions = next_result.get('questions', [])
            
            # 检查是否完成
            if next_result.get('is_complete'):
                final_level = next_result.get('final_level')
                level_name = next_result.get('level_name')
                print(f"\n✓ 测试完成！")
                print(f"  - 最终等级: {final_level} ({level_name})")
                break
        
        # 3. 显示自适应状态
        print("\n[3] 自适应状态详情:")
        adaptive_state = test_state.get('adaptive_state', {})
        scores_by_difficulty = adaptive_state.get('scores_by_difficulty', {})
        
        for difficulty, scores in scores_by_difficulty.items():
            avg_score = sum(scores) / len(scores) * 100 if scores else 0
            print(f"  - 难度 {difficulty}: 平均正确率 {avg_score:.1f}% ({len(scores)} 组题目)")
        
        # 4. 测试保存结果（模拟用户ID 1）
        print("\n[4] 测试保存结果...")
        success = service.save_test_result(
            user_id=1,
            language='japanese',
            final_level=final_level if 'final_level' in locals() else 2,
            test_data=test_state
        )
        
        if success:
            print("✓ 保存结果成功")
        else:
            print("✗ 保存结果失败")
        
        print("\n" + "=" * 60)
        print("自适应初次等级评测服务测试完成！")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n✗ 测试过程中发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = test_placement_service()
    sys.exit(0 if success else 1)
