# -*- coding: utf-8 -*-
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
题目爬虫服务示例 - 从网络爬取题目并拓展题库
"""

from app.services.question_crawler_service import (
    question_crawler_service,
    enhance_question_bank
)


def example_crawl_basic():
    """基础爬取示例"""
    print("=" * 60)
    print("题目爬虫服务 - 基础爬取")
    print("=" * 60)
    
    # 爬取Python相关题目
    print("爬取Python相关题目...")
    added, errors = question_crawler_service.crawl_questions(
        keywords=['Python编程题', 'Python面试题', 'Python基础'],
        count=10
    )
    print(f"✓ 成功爬取 {added} 道题目,错误 {errors} 个")
    
    # 爬取数据结构题目
    print("\n爬取数据结构题目...")
    added, errors = question_crawler_service.crawl_questions(
        keywords=['数据结构', '算法', '链表', '树'],
        count=10
    )
    print(f"✓ 成功爬取 {added} 道题目,错误 {errors} 个")


def example_crawl_real_exam():
    """爬取历年真题"""
    print("\n" + "=" * 60)
    print("题目爬虫服务 - 爬取历年真题")
    print("=" * 60)
    
    print("爬取2020-2024年真题...")
    added = question_crawler_service.crawl_real_exam_questions(
        years=[2020, 2021, 2022, 2023, 2024],
        count_per_year=5
    )
    print(f"✓ 成功爬取 {added} 道历年真题")


def example_crawl_must_know():
    """爬取必考题"""
    print("\n" + "=" * 60)
    print("题目爬虫服务 - 爬取必考题")
    print("=" * 60)
    
    print("爬取核心知识点题目...")
    added = question_crawler_service.crawl_must_know_questions(
        topics=['Python', '数据结构', '算法', '数据库', '计算机网络'],
        count_per_topic=8
    )
    print(f"✓ 成功爬取 {added} 道必考题")


def example_crawl_final():
    """爬取压轴题"""
    print("\n" + "=" * 60)
    print("题目爬虫服务 - 爬取压轴题")
    print("=" * 60)
    
    print("爬取难题/压轴题...")
    added = question_crawler_service.crawl_final_challenge_questions(
        topics=['数学', '算法', '编程'],
        count=15
    )
    print(f"✓ 成功爬取 {added} 道压轴题")


def example_crawl_error_prone():
    """爬取易错题"""
    print("\n" + "=" * 60)
    print("题目爬虫服务 - 爬取易错题")
    print("=" * 60)
    
    print("爬取易错题...")
    added = question_crawler_service.crawl_error_prone_questions(
        topics=['Python', '数据库', '网络'],
        count_per_topic=10
    )
    print(f"✓ 成功爬取 {added} 道易错题")


def example_crawl_formula():
    """爬取公式运用题"""
    print("\n" + "=" * 60)
    print("题目爬虫服务 - 爬取公式运用题")
    print("=" * 60)
    
    print("爬取公式运用题...")
    added = question_crawler_service.crawl_formula_questions(
        topics=['数学', '物理', '统计学'],
        count_per_topic=10
    )
    print(f"✓ 成功爬取 {added} 道公式运用题")


def example_batch_enhance():
    """批量增强题库"""
    print("\n" + "=" * 60)
    print("题目爬虫服务 - 批量增强题库")
    print("=" * 60)
    
    print("开始批量增强题库...")
    results = enhance_question_bank()
    
    print("\n爬取结果汇总:")
    print(f"  历年真题: {results['real_exam']} 道")
    print(f"  必考题: {results['must_know']} 道")
    print(f"  压轴题: {results['final']} 道")
    print(f"  易错题: {results['error_prone']} 道")
    print(f"  公式题: {results['formula']} 道")
    print(f"  总计: {results['total']} 道")


def example_check_stats():
    """检查题库统计"""
    print("\n" + "=" * 60)
    print("题目爬虫服务 - 检查题库统计")
    print("=" * 60)
    
    from app.services.enhanced_question_bank_service import enhanced_question_bank_service
    stats = enhanced_question_bank_service.get_statistics()
    
    print(f"题库总题目数: {stats.total_questions}")
    
    print("\n按类别分布:")
    for cat, count in stats.by_category.items():
        print(f"  {cat}: {count} 道")
    
    print("\n按题型分布:")
    for q_type, count in stats.by_type.items():
        print(f"  {q_type}: {count} 道")
    
    print("\n按难度分布:")
    for diff, count in stats.by_difficulty.items():
        print(f"  {diff}: {count} 道")


def run_all_examples():
    """运行所有示例"""
    example_crawl_basic()
    example_crawl_real_exam()
    example_crawl_must_know()
    example_crawl_final()
    example_crawl_error_prone()
    example_crawl_formula()
    example_batch_enhance()
    example_check_stats()
    
    print("\n" + "=" * 60)
    print("题目爬虫服务所有示例执行完成")
    print("=" * 60)


if __name__ == "__main__":
    run_all_examples()
