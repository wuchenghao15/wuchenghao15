#!/usr/bin/env python3
"""
测试听力题生成功能

import os
import sys
# JSON import removed - using database
from datetime import datetime

# 添加项目根目录和flask-app目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'flask-app'))

from exam_generator import ExamGenerator

def test_listening_generation():
    """测试听力题生成功能"""
    print("=" * 60)
    print("测试听力题生成功能")
    print("=" * 60)
    # 初始化试卷生成器
    generator = ExamGenerator()

    # 测试生成英语听力题
    print("\n1. 测试生成英语听力题...")
    english_listening_questions = generator.generate_listening_question(
        subject="english",
        difficulty="intermediate",
        count=2,
        auto_save=True
    )

    print(f"   成功生成 {len(english_listening_questions)} 道英语听力题")
    for i, question in enumerate(english_listening_questions, 1):
        print(f"   听力题 {i}: {question['audio_content']['title']}")
        print(f"      场景: {question['audio_content']['scenario']}")
        print(f"      口音: {question['audio_content']['accent']}")
        print(f"      理解题数量: {len(question['comprehension_questions'])}")
        print(f"      题目ID: {question['question_id']}")

    # 测试生成日语听力题
    print("\n2. 测试生成日语听力题...")
    japanese_listening_questions = generator.generate_listening_question(
        subject="japanese",
        difficulty="beginner",
        count=2,
        auto_save=True

    for i, question in enumerate(japanese_listening_questions, 1):
        print(f"      场景: {question['audio_content']['scenario']}")
        print(f"      口音: {question['audio_content']['accent']}")
        print(f"      理解题数量: {len(question['comprehension_questions'])}")
        print(f"      题目ID: {question['question_id']}")
    # 测试根据反馈更新听力题
    if english_listening_questions:
        feedback = {
            "accuracy": 0.9,  # 答对率90%
            "suggestions": ["增加听力材料长度", "提高理解题难度"]
        }

        print(f"   更新听力题: {test_question_id}")
        print(f"   反馈内容: {str(feedback)}")

        update_result = generator.update_listening_question_based_on_feedback(
            question_id=test_question_id,
            feedback=feedback
        )

        if update_result['success']:
            print(f"   更新成功!")
            print(f"   新听力题场景: {update_result['improved_question']['audio_content']['scenario']}")
            print(f"   新听力题口音: {update_result['improved_question']['audio_content']['accent']}")
        else:
            print(f"   更新失败: {update_result['message']}")

    print("\n" + "=" * 60)
    print("听力题生成测试完成!")
    print("=" * 60)
if __name__ == "__main__":
    test_listening_generation()
