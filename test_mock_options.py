#!/usr/bin/env python3
# 直接测试模拟题目生成功能

import sys
import os
# JSON import removed - using database
# 添加Flask应用目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'flask-app'))

# 直接复制generate_mock_questions方法的核心逻辑进行测试
def test_mock_question_generation():
    """测试模拟题目生成"""
    import random

    # 日语题目内容（按类别和难度）
    japanese_questions = {
        '词汇': {
            1: [
                {
                    'content': '「こんにちは」の正しい意味はどれですか？',
                    'options': [
                        {'id': 'A', 'content': '你好'},
                        {'id': 'B', 'content': '再见'},
                        {'id': 'C', 'content': '谢谢'},
                        {'id': 'D', 'content': '对不起'}
                    ],
                    'correct_answer': 'A'
                }
            ]

    print("=== 测试模拟题目选项数量 ===")

    # 模拟题目生成过程
    count = 3
    categories = list(japanese_questions.keys())

    for i in range(count):
        # 随机选择题目类型（70%单选题，30%多选题）
        question_type = 'single' if i % 10 < 7 else 'multiple'

        # 随机选择类别
        category = categories[i % len(categories)]

        # 选择难度1的题目
        question_set = japanese_questions[category].get(1, [])

        # 获取题目模板
        question_template = question_set[i % len(question_set)]

        # 处理阅读题
        if 'question' in question_template:
            content = question_template['content'] + '\n' + question_template['question']
        else:
            content = question_template['content']

        print(f"\n原始题目模板:")
        print(f"  内容: {content}")
        print(f"  原始选项数量: {len(question_template['options'])}")

        # 创建包含6个选项的题目（符合用户要求）
        base_options = question_template['options']

        # 确保选项数量足够
        while len(base_options) < 6:
            # 添加更多相似的干扰选项
            last_option = base_options[-1]
            new_id = chr(ord(last_option['id']) + 1)
            # 根据题目类型生成相似干扰项
            if '意味' in content:  # 词汇题
                # 生成意思相近的干扰项
                similar_options = ['相似词1', '相似词2', '相似词3', '相似词4', '相似词5']
                new_content = random.choice(similar_options)
            elif '読み方' in content:  # 发音题
                # 生成相似发音的干扰项
                similar_pronunciations = ['ほん', 'ぼん', 'ほ', 'ぼ', 'こん', 'くん']
                new_content = random.choice(similar_pronunciations)
            else:  # 语法题或阅读题
                # 生成相似的语法干扰项
                similar_particles = ['は', 'を', 'に', 'が', 'で', 'も']
                new_content = random.choice(similar_particles)

            base_options.append({'id': new_id, 'content': new_content})

        # 限制选项数量为6个
        base_options = base_options[:6]

        status = "✓" if len(base_options) == 6 else "✗"
        print(f"生成后题目 ({status}):")
        print(f"  选项数量: {len(base_options)}")
        print("  选项:")
        for opt in base_options:
            print(f"    {opt['id']}. {opt['content']}")

    print("\n=== 测试完成 ===")

if __name__ == "__main__":
    test_mock_question_generation()
