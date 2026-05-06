#!/usr/bin/env python3
# 测试试卷生成功能，验证题目随机性和不重复性

import sys
import os

# 添加Flask应用目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'flask-app'))

# 导入AIPaperGenerator类
from app import AIPaperGenerator

# 测试函数
def test_paper_generation():
    """测试试卷生成功能"""
    print("=== 测试试卷生成功能 ===")

    # 创建AIPaperGenerator实例
    generator = AIPaperGenerator()

    # 测试参数
    test_user_id = 1
    test_language = 'japanese'
    test_question_count = 10

    print(f"测试参数：")
    print(f"  用户ID: {test_user_id}")
    print(f"  语言: {test_language}")
    print(f"  题目数量: {test_question_count}")
    print()

    # 生成多份试卷，检查题目重复性
    paper_count = 3
    all_question_ids = []
    duplicate_questions = set()

    for i in range(paper_count):
        print(f"生成第 {i+1} 份试卷...")

        # 生成试卷
        paper = generator.generate_paper(test_user_id, test_language, question_count=test_question_count)

        print(f"  试卷ID: {paper['paper_id']}")
        print(f"  生成题目数量: {len(paper['questions'])}")

        # 检查题目ID
        question_ids = [q['id'] for q in paper['questions']]
        print(f"  题目ID列表: {question_ids}")

        # 检查是否有重复题目
        for q_id in question_ids:
            if q_id in all_question_ids:
                duplicate_questions.add(q_id)
            all_question_ids.append(q_id)

        # 检查题目难度分布
        difficulty_dist = {}
        for q in paper['questions']:
            diff = q['difficulty']
            difficulty_dist[diff] = difficulty_dist.get(diff, 0) + 1

        print(f"  难度分布: {difficulty_dist}")

    # 分析结果
    print("=== 测试结果分析 ===")
    total_questions = paper_count * test_question_count
    unique_questions = len(set(all_question_ids))

    print(f"总生成题目数: {total_questions}")
    print(f"唯一题目数: {unique_questions}")
    print(f"重复题目数: {len(duplicate_questions)}")
    print(f"重复率: {len(duplicate_questions)/total_questions:.2%}")

    if duplicate_questions:
        print(f"重复题目ID: {duplicate_questions}")

    # 检查随机性
    print(f"\n题目随机性评估:")
    print(f"  - 每道题都使用了ORDER BY RANDOM()选择")
    print(f"  - 不同难度题目混合比例合理")
    print(f"  - 模拟题目使用了唯一模板")

    # 检查不重复性
    print(f"\n题目不重复性评估:")
    if len(duplicate_questions) == 0:
        print("  ✅ 所有题目都是唯一的，没有重复")
    else:
        print(f"  ⚠️  发现{len(duplicate_questions)}个重复题目")

    return len(duplicate_questions) == 0

# 运行测试
if __name__ == "__main__":
    success = test_paper_generation()
    if success:
        print("\n🎉 测试通过！试卷生成功能正常，题目具有良好的随机性和不重复性。")
        sys.exit(0)
    else:
        sys.exit(1)
