# -*- coding: utf-8 -*-
"""
测试题库管理器功能

from app.models.question import question_manager

def test_get_questions():
    """测试获取题目功能"""
    print("开始测试获取题目...")

    # 获取日语题目（language_id=1）
    questions = question_manager.get_questions(language_id=1, limit=1)

    print(f"获取到的题目数量: {len(questions)}")

    if questions:
        q = questions[0]
        print(f"题目ID: {q.id}")
        print(f"内容: {q.content}")
        print(f"选项: {q.options}")
        print(f"类型: {q.question_type}")
        print(f"答案: {q.answer}")
    else:
        print("未获取到题目，可能题库为空")

        # 尝试创建一些测试题目
        print("尝试创建测试题目...")
        # 创建日语题目
        q = question_manager.create_question(
            content="これは何ですか？",
            answer="A",
            explanation="これはりんごです。",
            category_id=None,
            language_id=1,
            level_id=2,
            question_type="single_choice",
            options=["りんご", "みかん", "ばなな", "ぶどう"]
        )
        print(f"创建的题目ID: {q.id}")

        # 再次尝试获取
        questions = question_manager.get_questions(language_id=1, limit=1)
        if questions:
            q = questions[0]
            print(f"内容: {q.content}")

    test_get_questions()
