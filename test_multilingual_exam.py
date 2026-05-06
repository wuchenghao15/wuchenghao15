#!/usr/bin/env python3
"""
测试多语言试卷生成

from exam_generator import ExamGenerator

def test_multilingual_exam():
    """测试生成不同语言的试卷"""
    # 创建试卷生成器
    generator = ExamGenerator()

    # 测试生成中文试卷
    print("=== 测试生成中文试卷 ===")
    zh_exam = generator.generate_exam({
        "total_questions": 10,
        "language": "zh-CN",
        "title": "中文测试试卷"
    })
    print(f"中文试卷标题: {zh_exam['title']}")
    print(f"中文试卷语言: {zh_exam['language']}")
    print(f"中文试卷包含{sum(len(s['questions']) for s in zh_exam['sections'])}道题")
    print()

    # 测试生成英文试卷
    print("=== 测试生成英文试卷 ===")
    en_exam = generator.generate_exam({
        "total_questions": 10,
        "title": "English Test Paper"
    })
    print(f"英文试卷标题: {en_exam['title']}")
    print(f"英文试卷包含{sum(len(s['questions']) for s in en_exam['sections'])}道题")
    print()

    # 测试生成日文试卷
    ja_exam = generator.generate_exam({
        "total_questions": 10,
        "title": "日本語テスト用紙"
    })
    print(f"日文试卷标题: {ja_exam['title']}")
    print(f"日文试卷语言: {ja_exam['language']}")
    print()

    print("多语言试卷生成测试完成！")

if __name__ == "__main__":
