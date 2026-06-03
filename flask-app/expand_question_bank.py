# -*- coding: utf-8 -*-
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
拓展题库 - 生成100万道题目
"""

import time
from app.services.massive_question_generator import (
    massive_question_generator,
    generate_massive_question_bank,
    Subject
)


def expand_to_1m_questions():
    """扩展题库到100万道题目"""
    print("=" * 60)
    print("拓展题库 - 生成100万道题目")
    print("=" * 60)
    
    # 分配各科目题目数量,总计100万
    subject_allocation = [
        ('math', 150000),       # 数学: 15万
        ('physics', 120000),    # 物理: 12万
        ('chemistry', 100000),  # 化学: 10万
        ('english', 120000),    # 英语: 12万
        ('computer', 150000),   # 计算机: 15万
        ('programming', 150000), # 编程: 15万
        ('database', 100000),   # 数据库: 10万
        ('network', 110000)     # 网络: 11万
    ]
    
    total_target = sum(count for _, count in subject_allocation)
    print(f"目标总数: {total_target:,} 道题目")
    print("-" * 60)
    
    start_time = time.time()
    total_generated = 0
    
    for subject_name, count in subject_allocation:
        print(f"\n正在生成 {subject_name} 科目...")
        print(f"  目标: {count:,} 道")
        
        task_id = massive_question_generator.generate_for_subject(
            Subject[subject_name.upper()],
            count=count
        )
        
        task = massive_question_generator.get_task(task_id)
        total_generated += task.saved_count
        
        print(f"  ✓ 已生成: {task.saved_count:,} 道")
        print(f"  状态: {task.status}")
    
    elapsed = time.time() - start_time
    hours = int(elapsed // 3600)
    minutes = int((elapsed % 3600) // 60)
    seconds = int(elapsed % 60)
    
    print("\n" + "=" * 60)
    print("题库拓展完成!")
    print("=" * 60)
    print(f"总生成题目数: {total_generated:,} 道")
    print(f"耗时: {hours}小时{minutes}分钟{seconds}秒")
    print("=" * 60)
    
    # 显示统计
    from app.services.enhanced_question_bank_service import enhanced_question_bank_service
    stats = enhanced_question_bank_service.get_statistics()
    
    print("\n当前题库统计:")
    print(f"  总题目数: {stats.total_questions:,}")
    print("\n  按类别分布:")
    for cat, cnt in sorted(stats.by_category.items(), key=lambda x: x[1], reverse=True)[:5]:
        print(f"    {cat}: {cnt:,}")
    print("\n  按题型分布:")
    for q_type, cnt in sorted(stats.by_type.items(), key=lambda x: x[1], reverse=True)[:5]:
        print(f"    {q_type}: {cnt:,}")


if __name__ == "__main__":
    expand_to_1m_questions()
