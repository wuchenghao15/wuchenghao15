#!/usr/bin/env python3
"""
生成真实的日语N1级别的题目

import random

# 日语N1级别题目数据库
japanese_n1_questions = [
    {
        "type": "vocabulary",
        "subtype": "collocation",
        "question": "「この計画は、実行に移す前に再三（　）必要がある。」下線に適切な言葉を入れなさい。",
        "options": [
            "吟味する",
            "吟醸する",
            "吟味になる",
            "吟醸になる"
        ],
        "correct_answer": "吟味する",
        "explanation": "「吟味する」は「十分に考えて判断する」という意味で、計画や提案などに使われます。「吟醸する」は「じっくり考えて作り上げる」という意味で、酒や詩文などの创作に使われます。",
        "difficulty": 5
    },
    {
        "subtype": "structure",
        "question": "「彼は、長年の研究（　）、難しい問題を解決した。」下線に適切な助詞を入れなさい。",
        "options": [
            "をもって",
            "を通じて",
            "に基づいて"
        ],
        "correct_answer": "をもって",
        "explanation": "「～をもって」は「手段・方法・資格などを示す」という意味で、特に努力や能力を手段として成果を上げる場合に使われます。",
    },
    {
        "subtype": "inference",
        "question": "文章によると、情報技術の発展はどのような影響を与えているか。",
            "生活が便利になるだけで、悪影響はない。",
            "情報入手とコミュニケーションが進歩し、集中力が向上する。",
            "睡眠の質が向上するが、コミュニケーションが悪化する。"
        ],
        "correct_answer": "情報入手とコミュニケーションが進歩するが、集中力が低下する。",
        "explanation": "文章では、「情報技術の発展により、人々の生活スタイルは大きく変わってきています。特にスマートフォンの普及により、情報の入手やコミュニケーションの方法は飛躍的に進歩しました。しかし、これらの技術は便利である一方で、人々の注意力を分散させる原因ともなっています。」と述べられているため、正解は3番です。",
        "difficulty": 5
    }

# 随机选择一道题目
question = random.choice(japanese_n1_questions)

print("=== 日语N1级别题目 ===")

# 获取题型中文名称
type_mapping = {
    "vocabulary": "词汇部分",
    "grammar": "语法部分",
    "reading": "阅读部分"
}

print(f"题型: {type_mapping.get(question['type'], question['type'])}")
print(f"子题型: {question['subtype']}")
print(f"题目内容:")

# 如果是阅读题，显示文章
if 'passage' in question and question['passage']:
    print(f"\n文章:\n{question['passage']}\n")


# 显示选项
if question['options']:
    print(f"\n选项:")
    for i, option in enumerate(question['options'], 1):
        print(f"{i}. {option}")

print(f"\n正确答案: {question['correct_answer']}")
print(f"解析: {question.get('explanation', '无解析')}")
print(f"难度: {'★' * question['difficulty']}")

"""