# -*- coding: utf-8 -*-
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强版AI拓展题库服务示例 - 海量题库管理与专家AI出题
"""

from app.services.enhanced_question_bank_service import (
    enhanced_question_bank_service,
    init_mass_question_bank
)


def example_init_mass_bank():
    """初始化海量题库"""
    print("=" * 60)
    print("增强版AI拓展题库 - 初始化海量题库")
    print("=" * 60)
    
    # 初始化海量题库
    init_mass_question_bank()
    
    # 获取统计
    stats = enhanced_question_bank_service.get_statistics()
    print(f"\n题库统计:")
    print(f"  总题目数: {stats.total_questions}")
    print(f"  按类别分布:")
    for cat, count in stats.by_category.items():
        print(f"    {cat}: {count}")


def example_add_specialized_questions():
    """添加各类专项题目"""
    print("\n" + "=" * 60)
    print("增强版AI拓展题库 - 添加专项题目")
    print("=" * 60)
    
    # 添加历年真题
    print("添加历年真题...")
    real_exam_data = [
        {
            'type': 'single_choice',
            'difficulty': 'medium',
            'content': 'TCP/IP协议中,HTTP协议工作在OSI模型的哪一层?',
            'options': [
                {'key': 'A', 'value': '传输层'},
                {'key': 'B', 'value': '应用层'},
                {'key': 'C', 'value': '网络层'},
                {'key': 'D', 'value': '数据链路层'}
            ],
            'correct_answer': 'B',
            'knowledge_points': ['TCP/IP', 'OSI模型', 'HTTP'],
            'tags': ['网络', '真题']
        },
        {
            'type': 'calculation',
            'difficulty': 'hard',
            'content': '计算时间复杂度:快速排序的平均时间复杂度是多少?',
            'correct_answer': 'O(n log n)',
            'knowledge_points': ['算法', '时间复杂度', '排序'],
            'tags': ['算法', '真题']
        }
    ]
    enhanced_question_bank_service.add_real_exam_questions(2024, real_exam_data)
    print("✓ 2024年真题已添加")
    
    # 添加必考题
    print("\n添加必考题...")
    must_know_data = [
        {
            'type': 'single_choice',
            'difficulty': 'medium',
            'content': 'Python中,__init__方法的作用是什么?',
            'options': [
                {'key': 'A', 'value': '定义类'},
                {'key': 'B', 'value': '初始化实例'},
                {'key': 'C', 'value': '创建方法'},
                {'key': 'D', 'value': '导入模块'}
            ],
            'correct_answer': 'B',
            'knowledge_points': ['Python', '面向对象', '构造函数']
        },
        {
            'type': 'fill_blank',
            'difficulty': 'easy',
            'content': 'SQL中,____关键字用于从表中查询数据.',
            'correct_answer': 'SELECT',
            'knowledge_points': ['SQL', '查询']
        }
    ]
    enhanced_question_bank_service.add_must_know_questions(must_know_data)
    print("✓ 必考题已添加")
    
    # 添加压轴题
    print("\n添加压轴题...")
    final_data = [
        {
            'type': 'essay',
            'difficulty': 'expert',
            'content': '请详细说明分布式系统中CAP定理的含义及其应用场景.',
            'correct_answer': 'CAP定理指出,分布式系统无法同时满足一致性(Consistency)、可用性(Availability)和分区容错性(Partition tolerance)...',
            'knowledge_points': ['分布式系统', 'CAP定理', '一致性'],
            'score': 20.0
        }
    ]
    enhanced_question_bank_service.add_final_challenge_questions(final_data)
    print("✓ 压轴题已添加")
    
    # 添加加分题
    print("\n添加加分题...")
    bonus_data = [
        {
            'type': 'code_analysis',
            'difficulty': 'hard',
            'content': '分析以下代码的时间复杂度并提出优化方案:\n```python\ndef fibonacci(n):\n    if n <= 1:\n        return n\n    return fibonacci(n-1) + fibonacci(n-2)\n```',
            'correct_answer': '时间复杂度O(2^n),可通过动态规划优化到O(n)',
            'knowledge_points': ['算法', '动态规划', '递归']
        }
    ]
    enhanced_question_bank_service.add_bonus_questions(bonus_data)
    print("✓ 加分题已添加")
    
    # 添加专项专题
    print("\n添加专项专题...")
    topic_data = [
        {
            'type': 'multiple_choice',
            'difficulty': 'medium',
            'content': '以下哪些是机器学习中的监督学习算法?',
            'options': [
                {'key': 'A', 'value': '线性回归'},
                {'key': 'B', 'value': 'K-means'},
                {'key': 'C', 'value': '决策树'},
                {'key': 'D', 'value': 'PCA'}
            ],
            'correct_answer': ['A', 'C'],
            'knowledge_points': ['机器学习', '监督学习']
        },
        {
            'type': 'calculation',
            'difficulty': 'hard',
            'content': '已知线性回归模型 y = 2x + 3,当x=5时,y的值是多少?',
            'correct_answer': '13',
            'knowledge_points': ['机器学习', '线性回归'],
            'formula_used': ['y = mx + b']
        }
    ]
    enhanced_question_bank_service.add_special_topic_questions('机器学习专题', topic_data)
    print("✓ 机器学习专题已添加")


def example_mass_generate():
    """批量生成海量题目"""
    print("\n" + "=" * 60)
    print("增强版AI拓展题库 - 批量生成题目")
    print("=" * 60)
    
    # 批量生成50道题目
    print("批量生成50道题目...")
    generated = enhanced_question_bank_service.generate_mass_questions(
        count=50,
        categories=['must_know', 'special_topic', 'calculation', 'logic', 'error_prone'],
        types=['single_choice', 'multiple_choice', 'true_false', 'fill_blank'],
        difficulties=['easy', 'medium', 'hard']
    )
    print(f"✓ 成功生成 {generated} 道题目")
    
    # 统计
    stats = enhanced_question_bank_service.get_statistics()
    print(f"\n当前题库总量: {stats.total_questions}")


def example_search_and_filter():
    """搜索和筛选"""
    print("\n" + "=" * 60)
    print("增强版AI拓展题库 - 搜索和筛选")
    print("=" * 60)
    
    # 搜索历年真题
    real_exam = enhanced_question_bank_service.search_questions(category='real_exam')
    print(f"历年真题数量: {len(real_exam)}")
    
    # 搜索必考题
    must_know = enhanced_question_bank_service.search_questions(category='must_know')
    print(f"必考题数量: {len(must_know)}")
    
    # 搜索压轴题
    final = enhanced_question_bank_service.search_questions(category='final')
    print(f"压轴题数量: {len(final)}")
    
    # 搜索计算题
    calculation = enhanced_question_bank_service.search_questions(category='calculation')
    print(f"计算题数量: {len(calculation)}")
    
    # 搜索易错题
    error_prone = enhanced_question_bank_service.search_questions(category='error_prone')
    print(f"易错题数量: {len(error_prone)}")
    
    # 按关键词搜索
    python_qs = enhanced_question_bank_service.search_questions(keyword='Python')
    print(f"\n包含Python的题目: {len(python_qs)}")
    
    # 按知识点搜索
    ml_qs = enhanced_question_bank_service.search_questions(knowledge_point='机器学习')
    print(f"机器学习专题题目: {len(ml_qs)}")


def example_generate_exam_paper():
    """智能生成试卷"""
    print("\n" + "=" * 60)
    print("增强版AI拓展题库 - 智能生成试卷")
    print("=" * 60)
    
    paper = enhanced_question_bank_service.generate_exam_paper(
        title="2024年综合能力测试(专家级)",
        total_score=150.0,
        question_counts={
            'single_choice': 20,
            'multiple_choice': 10,
            'true_false': 10,
            'fill_blank': 10,
            'calculation': 5,
            'essay': 3
        },
        difficulty_distribution={
            'easy': 0.15,
            'medium': 0.35,
            'hard': 0.35,
            'expert': 0.15
        },
        categories=['must_know', 'special_topic', 'calculation', 'logic', 'final']
    )
    
    print(f"试卷标题: {paper['title']}")
    print(f"总分: {paper['total_score']}分")
    print(f"题目数量: {paper['question_count']}道")
    
    # 统计题型分布
    type_counts = {}
    diff_counts = {}
    for q in paper['questions']:
        type_counts[q['type']] = type_counts.get(q['type'], 0) + 1
        diff_counts[q['difficulty']] = diff_counts.get(q['difficulty'], 0) + 1
    
    print("\n题型分布:")
    for q_type, count in type_counts.items():
        print(f"  {q_type}: {count}道")
    
    print("\n难度分布:")
    for diff, count in diff_counts.items():
        print(f"  {diff}: {count}道")


def example_statistics():
    """统计信息"""
    print("\n" + "=" * 60)
    print("增强版AI拓展题库 - 统计信息")
    print("=" * 60)
    
    stats = enhanced_question_bank_service.get_statistics()
    
    print(f"总题目数: {stats.total_questions}")
    
    print("\n按题型分布:")
    for q_type, count in stats.by_type.items():
        print(f"  {q_type}: {count}")
    
    print("\n按类别分布:")
    for cat, count in stats.by_category.items():
        print(f"  {cat}: {count}")
    
    print("\n按难度分布:")
    for diff, count in stats.by_difficulty.items():
        print(f"  {diff}: {count}")
    
    print(f"\n总使用次数: {stats.total_usage}")


def run_all_examples():
    """运行所有示例"""
    example_init_mass_bank()
    example_add_specialized_questions()
    example_mass_generate()
    example_search_and_filter()
    example_generate_exam_paper()
    example_statistics()
    
    print("\n" + "=" * 60)
    print("增强版AI拓展题库所有示例执行完成")
    print("=" * 60)


if __name__ == "__main__":
    run_all_examples()
