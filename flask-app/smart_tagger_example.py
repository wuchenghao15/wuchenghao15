# -*- coding: utf-8 -*-
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能题库标记服务示例 - 三维标记系统
"""

import time
from app.services.smart_question_tagger import smart_question_tagger


def example_manual_tag():
    """手动标记"""
    print("=" * 60)
    print("智能题库标记 - 手动标记")
    print("=" * 60)
    
    questions = [
        {
            'id': 'Q-001',
            'content': 'Python中用于定义函数的关键字是什么?',
            'subject': 'programming',
            'type': 'single_choice',
            'difficulty': 'easy',
            'knowledge': ['Python', '函数'],
            'category': 'must_know'
        },
        {
            'id': 'Q-002',
            'content': '计算:已知函数f(x)=x^2+2x+1,求f(3)的值',
            'subject': 'math',
            'type': 'calculation',
            'difficulty': 'medium',
            'knowledge': ['函数', '求值'],
            'category': 'calculation'
        },
        {
            'id': 'Q-003',
            'content': '关于TCP协议的说法正确的是?',
            'subject': 'network',
            'type': 'single_choice',
            'difficulty': 'hard',
            'knowledge': ['TCP', '协议'],
            'category': 'final'
        },
        {
            'id': 'Q-004',
            'content': '分析分布式系统中CAP定理的含义',
            'subject': 'computer',
            'type': 'essay',
            'difficulty': 'expert',
            'knowledge': ['分布式', 'CAP'],
            'category': 'final'
        }
    ]
    
    for q in questions:
        smart_question_tagger.tag_question(
            question_id=q['id'],
            content=q['content'],
            subject=q['subject'],
            question_type=q['type'],
            difficulty=q['difficulty'],
            knowledge_points=q['knowledge'],
            category=q['category']
        )


def example_auto_tag():
    """自动标记"""
    print("\n" + "=" * 60)
    print("智能题库标记 - 自动标记")
    print("=" * 60)
    
    auto_questions = [
        ('Q-AUTO-001', 'Python中列表的append方法用于在末尾添加元素'),
        ('Q-AUTO-002', '计算这道数学题:求函数y=2x+3在x=5时的导数值'),
        ('Q-AUTO-003', '关于计算机网络TCP三次握手过程的说法'),
        ('Q-AUTO-004', '一道困难的算法题:实现快速排序算法'),
        ('Q-AUTO-005', '数据库中索引的作用是什么?')
    ]
    
    for qid, content in auto_questions:
        smart_question_tagger.auto_tag(qid, content)


def example_3d_search():
    """三维搜索"""
    print("\n" + "=" * 60)
    print("智能题库标记 - 三维搜索")
    print("=" * 60)
    
    results = smart_question_tagger.get_by_3d('programming', 'single_choice', 'easy')
    print(f"编程-单选-简单: {len(results)} 道")
    
    results = smart_question_tagger.get_by_3d('math', 'calculation', 'medium')
    print(f"数学-计算-中等: {len(results)} 道")


def example_quick_search():
    """快速搜索"""
    print("\n" + "=" * 60)
    print("智能题库标记 - 快速搜索")
    print("=" * 60)
    
    results = smart_question_tagger.search(subject='programming', limit=5)
    print(f"编程科目: {len(results)} 道")
    
    results = smart_question_tagger.search(subject='math', difficulty='hard', limit=5)
    print(f"数学-困难: {len(results)} 道")
    
    results = smart_question_tagger.search(question_type='calculation', limit=5)
    print(f"计算题: {len(results)} 道")


def example_generate_paper():
    """快速组卷"""
    print("\n" + "=" * 60)
    print("智能题库标记 - 快速组卷")
    print("=" * 60)
    
    paper = smart_question_tagger.generate_paper(
        subject='programming',
        question_type='single_choice',
        diff_distribution={'easy': 0.3, 'medium': 0.4, 'hard': 0.2, 'expert': 0.1},
        count=5
    )
    print(f"生成的试卷包含 {len(paper)} 道题目")
    for q in paper:
        print(f"  - {q.question_id}: {q.content[:30]}...")


def example_statistics():
    """统计信息"""
    print("\n" + "=" * 60)
    print("智能题库标记 - 统计信息")
    print("=" * 60)
    
    stats = smart_question_tagger.get_stats()
    print(f"总题目数: {stats['total']}")
    print(f"总使用次数: {stats['total_usages']}")
    print(f"三维组合数: {stats['3d_combinations']}")
    
    print("\n按科目分布:")
    for k, v in stats['by_subject'].items():
        print(f"  {k}: {v}")
    
    print("\n按题型分布:")
    for k, v in stats['by_type'].items():
        print(f"  {k}: {v}")
    
    print("\n按难度分布:")
    for k, v in stats['by_difficulty'].items():
        print(f"  {k}: {v}")


def example_maintain():
    """题库维护"""
    print("\n" + "=" * 60)
    print("智能题库标记 - 题库维护")
    print("=" * 60)
    
    result = smart_question_tagger.maintain()
    print(f"维护结果: {result}")


def run_all():
    """运行所有示例"""
    example_manual_tag()
    example_auto_tag()
    example_3d_search()
    example_quick_search()
    example_generate_paper()
    example_statistics()
    example_maintain()
    
    print("\n" + "=" * 60)
    print("智能题库标记服务示例执行完成")
    print("=" * 60)


if __name__ == "__main__":
    run_all()
