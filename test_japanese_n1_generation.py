#!/usr/bin/env python3
"""
测试日语N1级别题目生成功能

from exam_generator import ExamGenerator

# 创建试卷生成器实例
generator = ExamGenerator()

# 设置语言为日语
generator.exam_config["language"] = "ja-JP"

print("=== 测试日语N1级别题目生成 ===")

# 测试生成词汇题
print("\n1. 测试生成日语N1词汇题:")
vocab_question = generator._generate_sample_question("vocabulary", 1)
print(f"题型: {vocab_question['type']}")
print(f"子题型: {vocab_question['subtype']}")
print(f"题目: {vocab_question['question']}")
print(f"选项: {vocab_question['options']}")
print(f"正确答案: {vocab_question['correct_answer']}")
print(f"来源: {vocab_question['source']}")

# 测试生成语法题
print("\n2. 测试生成日语N1语法题:")
grammar_question = generator._generate_sample_question("grammar", 2)
print(f"题型: {grammar_question['type']}")
print(f"子题型: {grammar_question['subtype']}")
print(f"题目: {grammar_question['question']}")
print(f"选项: {grammar_question['options']}")
print(f"正确答案: {grammar_question['correct_answer']}")
print(f"来源: {grammar_question['source']}")

# 测试生成阅读题
print("\n3. 测试生成日语N1阅读题:")
reading_question = generator._generate_sample_question("reading", 3)
print(f"题型: {reading_question['type']}")
print(f"子题型: {reading_question['subtype']}")
print(f"文章: {reading_question['passage']}")
print(f"题目: {reading_question['question']}")
print(f"选项: {reading_question['options']}")
print(f"正确答案: {reading_question['correct_answer']}")
print(f"来源: {reading_question['source']}")

# 测试生成完整的N1试卷
print("\n4. 测试生成完整的日语N1试卷:")
n1_exam_config = {
    "language": "ja-JP",
    "difficulty_level": "N1",
    "adaptive_difficulty": 5,
    "total_questions": 3,  # 每个题型1道题
    "duration": 30,
    "total_score": 100
}

exam = generator.generate_exam(n1_exam_config)
print(f"生成的试卷包含{sum(len(s['questions']) for s in exam['sections'])}道题")
print(f"试卷结构: {[s['title'] for s in exam['sections']]}")

# 打印生成的题目
for section in exam['sections']:
    print(f"\n{section['title']}:")
    for i, question in enumerate(section['questions'], 1):
        print(f"  第{i}题:")
        print(f"    题型: {question['subtype']}")
        print(f"    来源: {question['source']}")
        print(f"    题目: {question['question'][:50]}...")
        print(f"    正确答案: {question['correct_answer']}")

"""