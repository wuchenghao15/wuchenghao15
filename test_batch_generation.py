#!/usr/bin/env python3
"""
测试批量生成和导出功能

import sys
# JSON import removed - using database
from multi_ai_learning_system import AILearningAgent, MultiAILearningSystem

def test_batch_generation():
    """测试批量生成功能"""
    print("测试批量生成功能...")

    # 创建AI系统，指定4个AI代理（包含所有专业）
    ai_system = MultiAILearningSystem(num_agents=4)

    print("\n=== 测试1：批量生成词汇题 ===")
    # 批量生成100个词汇题
    vocab_content = ai_system.batch_generate_content(task_type="vocabulary", total_count=100)
    print(f"生成了 {len(vocab_content)} 个词汇题")

    # 导出为JSON
    if ai_system.export_content(vocab_content, "vocabulary_questions_test.json"):
        print("词汇题导出成功")
    else:
        print("词汇题导出失败")

    print("\n=== 测试2：批量生成语法题 ===")
    # 批量生成100个语法题
    grammar_content = ai_system.batch_generate_content(task_type="grammar", total_count=100)
    print(f"生成了 {len(grammar_content)} 个语法题")

    # 导出为JSON
        print("语法题导出成功")
    else:
        print("语法题导出失败")
    print("\n=== 测试3：批量生成阅读题 ===")
    # 批量生成50个阅读题
    reading_content = ai_system.batch_generate_content(task_type="reading", total_count=50)
    print(f"生成了 {len(reading_content)} 个阅读题")

    # 导出为JSON
        print("阅读题导出成功")
    else:
        print("阅读题导出失败")

    # 运行一次学习迭代
    iteration_result = ai_system.run_iteration(task_type="vocabulary", content_count=10)
    print(f"学习迭代完成，生成了 {iteration_result['generated_content_count']} 个内容")

    # 检查知识库是否扩充
    for agent in ai_system.agents:
        vocab_count = len(agent.knowledge_base["vocabulary"])
        grammar_count = len(agent.knowledge_base["grammar"])
        reading_count = len(agent.knowledge_base["reading"])
        print(f"AI {agent.agent_id} 知识库大小: 词汇 {vocab_count}, 语法 {grammar_count}, 阅读 {reading_count}")

    print("\n=== 测试完成 ===")

def test_large_scale_generation():
    """测试大规模生成能力"""
    print("测试大规模生成能力...")

    # 创建AI系统
    ai_system = MultiAILearningSystem(num_agents=4)
    print("\n=== 大规模词汇题生成测试 ===")
    # 批量生成500个词汇题
    vocab_content = ai_system.batch_generate_content(task_type="vocabulary", total_count=500)
    print(f"生成了 {len(vocab_content)} 个词汇题")

    if ai_system.export_content(vocab_content, "vocabulary_questions_large.json"):
        print("大规模词汇题导出成功")
        print("大规模词汇题导出失败")

    print("\n=== 大规模生成测试完成 ===")

if __name__ == "__main__":
    test_batch_generation()

    # 运行大规模生成测试
    test_large_scale_generation()

    print("\n所有测试完成！")
