# -*- coding: utf-8 -*-
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI拓展题库服务示例和使用说明
"""

from app.services.ai_question_bank_service import (
    ai_question_bank_service,
    QuestionType,
    QuestionCategory,
    DifficultyLevel
)


def example_add_questions():
    """添加题目示例"""
    print("=" * 60)
    print("AI拓展题库 - 添加题目")
    print("=" * 60)
    
    # 添加单选题
    q1_id = ai_question_bank_service.add_question({
        'type': 'single_choice',
        'category': 'must_know',
        'difficulty': 'medium',
        'content': 'Python中用于定义函数的关键字是什么?',
        'options': [
            {'key': 'A', 'value': 'function'},
            {'key': 'B', 'value': 'def'},
            {'key': 'C', 'value': 'func'},
            {'key': 'D', 'value': 'define'}
        ],
        'correct_answer': 'B',
        'explanation': 'Python中使用def关键字定义函数',
        'analysis': 'def是define的缩写,用于定义函数',
        'knowledge_points': ['Python基础', '函数定义'],
        'tags': ['基础', '高频考点']
    })
    print(f"添加单选题: {q1_id}")
    
    # 添加计算题
    q2_id = ai_question_bank_service.add_question({
        'type': 'calculation',
        'category': 'calculation',
        'difficulty': 'hard',
        'content': '已知 f(x) = x^2 + 3x + 2,求 f(2) 的值',
        'correct_answer': '12',
        'explanation': 'f(2) = 2^2 + 3*2 + 2 = 4 + 6 + 2 = 12',
        'formula_used': ['二次函数求值'],
        'score': 10.0
    })
    print(f"添加计算题: {q2_id}")
    
    # 添加压轴题
    q3_id = ai_question_bank_service.add_question({
        'type': 'essay',
        'category': 'final',
        'difficulty': 'expert',
        'content': '请详细说明TCP三次握手的过程及其作用',
        'correct_answer': 'TCP三次握手包括:1. SYN 2. SYN+ACK 3. ACK...',
        'explanation': '三次握手确保双方都具备收发数据的能力',
        'analysis': '考查网络协议的核心概念',
        'knowledge_points': ['TCP/IP', '网络协议'],
        'score': 15.0
    })
    print(f"添加压轴题: {q3_id}")


def example_ai_generate_questions():
    """AI生成题目示例"""
    print("\n" + "=" * 60)
    print("AI拓展题库 - AI生成题目")
    print("=" * 60)
    
    # AI生成单道题目
    print("AI生成单道题目...")
    question = ai_question_bank_service.ai_generate_question(
        knowledge_points=['数据结构', '算法'],
        question_type='single_choice',
        difficulty='medium',
        category='special_topic'
    )
    print(f"题目类型: {question['type']}")
    print(f"题目内容: {question['content']}")
    print(f"选项: {[opt['key']+'. '+opt['value'] for opt in question['options']]}")
    print(f"正确答案: {question['correct_answer']}")
    print(f"解析: {question['explanation']}")
    
    # AI批量生成题目
    print("\nAI批量生成5道题目...")
    questions = ai_question_bank_service.ai_generate_batch(
        count=5,
        knowledge_points=['数学', '编程', '逻辑'],
        categories=['special_topic', 'must_know', 'error_prone']
    )
    
    for i, q in enumerate(questions, 1):
        print(f"\n{i}. [{q['category']}] {q['type']} - {q['difficulty']}")
        print(f"   {q['content'][:50]}...")


def example_search_and_filter():
    """搜索和筛选示例"""
    print("\n" + "=" * 60)
    print("AI拓展题库 - 搜索和筛选")
    print("=" * 60)
    
    # 搜索必考题目
    must_know = ai_question_bank_service.search_questions(category='must_know')
    print(f"必考题目数量: {len(must_know)}")
    
    # 搜索计算题
    calculations = ai_question_bank_service.search_questions(type='calculation')
    print(f"计算题数量: {len(calculations)}")
    
    # 按关键词搜索
    python_questions = ai_question_bank_service.search_questions(keyword='Python')
    print(f"包含Python的题目: {len(python_questions)}")
    
    # 获取随机题目
    random_qs = ai_question_bank_service.get_random_questions(3, difficulty='medium')
    print(f"\n随机3道中等难度题目:")
    for q in random_qs:
        print(f"  - {q.content[:40]}...")


def example_generate_exam_paper():
    """生成试卷示例"""
    print("\n" + "=" * 60)
    print("AI拓展题库 - 生成试卷")
    print("=" * 60)
    
    paper = ai_question_bank_service.generate_exam_paper(
        title="2024年综合能力测试",
        total_score=100.0,
        question_counts={
            'single_choice': 15,
            'multiple_choice': 5,
            'true_false': 5,
            'fill_blank': 5,
            'calculation': 3
        },
        difficulty_distribution={
            'easy': 0.2,
            'medium': 0.5,
            'hard': 0.2,
            'expert': 0.1
        }
    )
    
    print(f"试卷标题: {paper['title']}")
    print(f"总分: {paper['total_score']}分")
    print(f"题目数量: {paper['question_count']}道")
    print(f"\n题目分布:")
    
    type_counts = {}
    for q in paper['questions']:
        type_counts[q['type']] = type_counts.get(q['type'], 0) + 1
    
    for q_type, count in type_counts.items():
        print(f"  {q_type}: {count}道")


def example_statistics():
    """统计信息示例"""
    print("\n" + "=" * 60)
    print("AI拓展题库 - 统计信息")
    print("=" * 60)
    
    stats = ai_question_bank_service.get_statistics()
    print(f"总题目数: {stats.total_questions}")
    print(f"\n按题型分布:")
    for q_type, count in stats.by_type.items():
        print(f"  {q_type}: {count}")
    
    print(f"\n按类别分布:")
    for cat, count in stats.by_category.items():
        print(f"  {cat}: {count}")
    
    print(f"\n按难度分布:")
    for diff, count in stats.by_difficulty.items():
        print(f"  {diff}: {count}")
    
    print(f"\n平均正确率: {stats.avg_correct_rate:.2%}")
    print(f"总使用次数: {stats.total_usage}")


def example_categories_and_knowledge_points():
    """分类和知识点管理示例"""
    print("\n" + "=" * 60)
    print("AI拓展题库 - 分类和知识点管理")
    print("=" * 60)
    
    categories = ai_question_bank_service.get_categories()
    print("题库分类:")
    for cat, kps in categories.items():
        print(f"  {cat}: {', '.join(kps)}")
    
    # 添加知识点
    ai_question_bank_service.add_knowledge_point('must_know', '深度学习')
    print("\n添加知识点后:")
    print(f"必考知识点: {ai_question_bank_service.get_knowledge_points('must_know')}")
    
    # 获取所有知识点
    all_kps = ai_question_bank_service.get_knowledge_points()
    print(f"\n所有知识点数量: {len(all_kps)}")


def run_all_examples():
    """运行所有示例"""
    example_add_questions()
    example_ai_generate_questions()
    example_search_and_filter()
    example_generate_exam_paper()
    example_statistics()
    example_categories_and_knowledge_points()
    
    print("\n" + "=" * 60)
    print("所有示例执行完成")
    print("=" * 60)


if __name__ == "__main__":
    run_all_examples()
