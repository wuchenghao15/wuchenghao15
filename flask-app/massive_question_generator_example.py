# -*- coding: utf-8 -*-
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
大规模题库生成示例 - 支持每个科目1000万道题目的高效生成
"""

from app.services.massive_question_generator import (
    massive_question_generator,
    generate_massive_question_bank,
    Subject
)


def example_generate_single_subject():
    """生成单个科目题目"""
    print("=" * 60)
    print("大规模题库生成 - 单个科目")
    print("=" * 60)
    
    # 生成数学科目100道题目作为演示(实际使用时改为10000000)
    print("正在生成数学科目题目...")
    task_id = massive_question_generator.generate_for_subject(
        Subject.MATH,
        count=100  # 实际使用时改为 10000000
    )
    
    task = massive_question_generator.get_task(task_id)
    print(f"任务ID: {task.task_id}")
    print(f"状态: {task.status}")
    print(f"生成数量: {task.generated_count}")
    print(f"保存数量: {task.saved_count}")
    print(f"进度: {task.progress:.1f}%")


def example_generate_multiple_subjects():
    """生成多个科目题目"""
    print("\n" + "=" * 60)
    print("大规模题库生成 - 多个科目")
    print("=" * 60)
    
    subjects = [Subject.MATH, Subject.PHYSICS, Subject.COMPUTER]
    
    for subject in subjects:
        print(f"\n正在生成{subject.value}科目...")
        task_id = massive_question_generator.generate_for_subject(
            subject,
            count=50  # 实际使用时改为 10000000
        )
        task = massive_question_generator.get_task(task_id)
        print(f"  ✓ {subject.value}: {task.saved_count} 道题目")


def example_generate_all_subjects():
    """生成所有科目题目"""
    print("\n" + "=" * 60)
    print("大规模题库生成 - 所有科目")
    print("=" * 60)
    
    print("正在为所有科目生成题目...")
    
    # 生成所有科目各100道作为演示
    results = generate_massive_question_bank(
        subjects=['math', 'physics', 'chemistry', 'computer', 'programming'],
        count_per_subject=50  # 实际使用时改为 10000000
    )
    
    print("\n生成结果汇总:")
    for subject, info in results.items():
        print(f"  {subject}: {info['saved']} 道题目 ({info['status']})")


def example_check_progress():
    """检查生成进度"""
    print("\n" + "=" * 60)
    print("大规模题库生成 - 检查进度")
    print("=" * 60)
    
    tasks = massive_question_generator.list_tasks()
    print(f"任务总数: {len(tasks)}")
    
    for task in tasks:
        print(f"\n任务: {task.task_id}")
        print(f"  科目: {task.subject.value}")
        print(f"  目标: {task.target_count:,}")
        print(f"  已生成: {task.generated_count:,}")
        print(f"  已保存: {task.saved_count:,}")
        print(f"  进度: {task.progress:.1f}%")
        print(f"  状态: {task.status}")
        if task.estimated_remaining:
            print(f"  预计剩余: {task.estimated_remaining:.1f} 分钟")


def example_check_stats():
    """检查题库统计"""
    print("\n" + "=" * 60)
    print("大规模题库生成 - 题库统计")
    print("=" * 60)
    
    from app.services.enhanced_question_bank_service import enhanced_question_bank_service
    stats = enhanced_question_bank_service.get_statistics()
    
    print(f"题库总题目数: {stats.total_questions:,}")
    
    print("\n按科目分布(通过类别推断):")
    for cat, count in stats.by_category.items():
        print(f"  {cat}: {count:,} 道")
    
    print("\n按题型分布:")
    for q_type, count in stats.by_type.items():
        print(f"  {q_type}: {count:,} 道")
    
    print("\n按难度分布:")
    for diff, count in stats.by_difficulty.items():
        print(f"  {diff}: {count:,} 道")


def run_all_examples():
    """运行所有示例"""
    example_generate_single_subject()
    example_generate_multiple_subjects()
    example_generate_all_subjects()
    example_check_progress()
    example_check_stats()
    
    print("\n" + "=" * 60)
    print("大规模题库生成示例执行完成")
    print("=" * 60)
    print("\n📌 注意: 实际使用时,请将 count 参数改为 10000000")
    print("示例中使用较小的数字是为了快速验证功能")


if __name__ == "__main__":
    run_all_examples()
