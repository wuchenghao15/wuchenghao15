#!/usr/bin/env python3
# 测试题目选项数量

import sys
import os

# 添加Flask应用目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'flask-app'))

from app import AIPaperGenerator

# 创建测试用户ID
TEST_USER_ID = 1

# 测试日语题目生成
generator = AIPaperGenerator()
paper = generator.generate_paper(TEST_USER_ID, 'japanese', 'level', 5)

print("\n=== 日语测试试卷 ===")
print(f"试卷ID: {paper['paper_id']}")
print(f"语言: {paper['language']}")
print(f"总题目数: {paper['total_questions']}")
print()

# 检查每个题目的选项数量
all_have_six_options = True
for i, question in enumerate(paper['questions'], 1):
    options_count = len(question['options'])
    status = "✓" if options_count == 6 else "✗"
    print(f"题目 {i} ({status}): 选项数量 = {options_count}")
    print(f"  内容: {question['content']}")
    print(f"  类型: {question.get('question_type', 'single')}")
    print("  选项:")
    for opt in question['options']:
        print(f"    {opt['id']}. {opt['content']}")

    if options_count != 6:
        all_have_six_options = False

print("=== 测试结果 ===")
if all_have_six_options:
    print("✅ 所有题目都有6个选项，符合要求！")
else:
    print("❌ 部分题目选项数量不符合要求！")
    sys.exit(1)
