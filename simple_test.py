#!/usr/bin/env python3
"""
简单测试脚本，用于测试批量生成和数据库上传功能

import sys
import os

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from multi_ai_learning_system import MultiAILearningSystem

def test_simple_batch_generation():
    """简单测试批量生成和数据库上传功能"""
    print("简单测试批量生成和数据库上传功能...")

    # 创建AI系统，只使用1个AI代理
    ai_system = MultiAILearningSystem(num_agents=1)

    print("\n=== 测试：批量生成词汇题 ===")
    # 批量生成10个词汇题
    vocab_content = ai_system.batch_generate_content(task_type="vocabulary", total_count=10)
    print(f"生成了 {len(vocab_content)} 个词汇题")

    # 上传内容到数据库
    if ai_system.export_content(vocab_content):
        print("词汇题成功上传到数据库")
    else:
        print("词汇题上传到数据库失败")

    print("\n=== 测试完成 ===")

if __name__ == "__main__":
    test_simple_batch_generation()
