#!/usr/bin/env python3
"""
测试测试生成器

from app.ai.test_generator import test_generator

# 测试日语测试生成
print("=== 测试日语测试生成 ===")
test_paper = test_generator.generate_test_paper(language='japanese', level='intermediate', question_count=5)
print('测试试卷生成成功，包含', len(test_paper['questions']), '道题目')
print('测试试卷ID:', test_paper['id'])
print('语言:', test_paper['language'])
print('难度:', test_paper['level'])
print('题目列表:')
for i, q in enumerate(test_paper['questions'], 1):
    print(f'  {i}. {q['content']}')
    print(f'     选项: {q['options']}')
    print(f'     正确答案: {q['correct_answer']}')

# 测试英语测试生成
print("\n=== 测试英语测试生成 ===")
test_paper = test_generator.generate_test_paper(language='english', level='intermediate', question_count=5)
print('测试试卷生成成功，包含', len(test_paper['questions']), '道题目')
print('语言:', test_paper['language'])
print('题目列表:')
    print(f'  {i}. {q['content']}')
    print(f'     正确答案: {q['correct_answer']}')

"""