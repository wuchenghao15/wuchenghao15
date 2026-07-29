# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
AI脑库100次轮巡测试脚本
功能：
  1. 加载扩展知识池（200+条，15+知识域）
  2. 每轮执行：知识投喂 → 认知评估 → 跨域推理 → 认知提升
  3. 实时记录认知维度变化
  4. 生成认知提升报告
"""

import os
import sys
import json
import random
import time
import logging
from datetime import datetime
from typing import Dict, List, Any

# 项目根目录 - 脚本在 scripts/python/ 下，向上两级
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))
sys.path.insert(0, PROJECT_ROOT)
os.chdir(PROJECT_ROOT)

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(
            os.path.join(PROJECT_ROOT, 'brain_patrol_test.log'),
            encoding='utf-8'
        )
    ]
)
logger = logging.getLogger('BrainPatrol')


def run_brain_patrol(rounds=100):
    """运行脑库轮巡测试"""
    print("=" * 70)
    print("🧠 AI脑库认知维度提升 - 100次轮巡测试")
    print("=" * 70)
    print()

    # 导入模块
    try:
        from ai_engines.ai_brain import (
            AIBrain, AIBrainKnowledge, COGNITIVE_LEVELS, DOMAIN_RELATIONS
        )
        from core.services.brain_feeding_engine import KNOWLEDGE_POOL
        print("✅ 模块导入成功")
    except Exception as e:
        print(f"❌ 模块导入失败: {e}")
        return None

    # 统计知识池
    domains = set(k['domain'] for k in KNOWLEDGE_POOL)
    domain_counts = {}
    for k in KNOWLEDGE_POOL:
        d = k['domain']
        domain_counts[d] = domain_counts.get(d, 0) + 1

    print(f"\n📚 知识池概览：")
    print(f"   总知识条目: {len(KNOWLEDGE_POOL)}")
    print(f"   知识域数量: {len(domains)}")
    print(f"   知识域列表:")
    for d in sorted(domains):
        print(f"     • {d}: {domain_counts[d]}条")

    # 创建脑库实例
    brain = AIBrain()
    print("\n🧠 脑库实例创建成功")

    # ========== 初始化：注入所有知识 ==========
    print("\n📥 阶段1：知识投喂初始化")
    print("-" * 50)

    injected_count = 0
    knowledge_objects = []

    for kp in KNOWLEDGE_POOL:
        # 创建AIBrainKnowledge对象
        k = AIBrainKnowledge(
            title=kp['topic'],
            content=kp['content'],
            knowledge_type=kp['type'],
            domain=kp['domain'],
            source='knowledge_pool',
            tags=[kp['type'], kp['domain']],
            confidence_score=random.uniform(0.5, 0.9),
            cognitive_level='L1',
            cognitive_score=random.uniform(0.3, 0.6),
        )
        knowledge_objects.append(k)
        brain.add_knowledge(k)
        injected_count += 1

    print(f"   ✅ 已投喂 {injected_count} 条知识")
    print(f"   ✅ 覆盖 {len(brain.get_all_domains())} 个知识域")

    # ========== 构建知识关联图谱 ==========
    print("\n🕸️ 阶段2：构建知识关联图谱")
    print("-" * 50)

    edge_count = brain.auto_build_domain_relations()
    print(f"   ✅ 已构建 {edge_count} 条跨域知识关联")

    # ========== 100次轮巡 ==========
    print(f"\n🔄 阶段3：执行 {rounds} 次轮巡测试")
    print("-" * 50)

    # 轮巡统计
    patrol_stats = {
        'rounds': rounds,
        'cognitive_evaluations': 0,
        'cognitive_promotions': 0,
        'cross_domain_reasonings': 0,
        'knowledge_searches': 0,
        'knowledge_expansions': 0,
        'problems_found': 0,
        'problems_resolved': 0,
    }

    # 记录每10轮的快照
    snapshots = []

    start_time = time.time()

    for round_num in range(1, rounds + 1):
        # 每10轮打印进度
        if round_num % 10 == 0 or round_num == 1:
            print(f"\n   第 {round_num}/{rounds} 轮...")

        # ------ 1. 随机选取知识进行认知评估 ------
        random_kid = random.choice(list(brain._knowledge_store.keys()))
        interactions = random.randint(1, 15)
        feedback = random.uniform(0.3, 1.0)
        cross_links = random.randint(0, 8)

        eval_result = brain.evaluate_knowledge_cognition(
            random_kid, interactions, feedback, cross_links
        )

        if eval_result.get('promoted'):
            patrol_stats['cognitive_promotions'] += 1

        patrol_stats['cognitive_evaluations'] += 1

        # ------ 2. 随机选取两个域进行跨域推理 ------
        all_domains = brain.get_all_domains()
        if len(all_domains) >= 2:
            source_domain = random.choice(all_domains)
            target_domain = random.choice([d for d in all_domains if d != source_domain])

            query = f"从{source_domain}到{target_domain}的知识迁移"
            reasoning_result = brain.cross_domain_reason(
                source_domain, target_domain, query
            )

            if reasoning_result.get('success'):
                patrol_stats['cross_domain_reasonings'] += 1

        # ------ 3. 知识搜索测试 ------
        search_queries = [
            "架构设计",
            "机器学习",
            "安全防护",
            "数据分析",
            "AI架构",
            "前端开发",
            "云原生",
            "大语言模型",
        ]
        search_query = random.choice(search_queries)
        search_results = brain.search_knowledge(search_query, top_k=3)
        patrol_stats['knowledge_searches'] += 1

        # ------ 4. 知识拓展测试 ------
        expand_topics = [
            "微服务",
            "深度学习",
            "DevOps",
            "AI安全",
            "智能教育",
            "企业微信",
            "量子计算",
            "边缘计算",
        ]
        expand_topic = random.choice(expand_topics)
        expanded = brain.expand_knowledge(expand_topic, depth=2)
        patrol_stats['knowledge_expansions'] += 1

        # ------ 5. 发现并解决问题 ------
        if random.random() < 0.1:  # 10%概率发现问题
            problem = brain.add_problem(
                description=f"轮巡{round_num}发现的潜在问题",
                category=random.choice(['performance', 'correctness', 'consistency']),
                severity=random.choice(['low', 'medium', 'high']),
            )
            patrol_stats['problems_found'] += 1

            # 自动生成解决方案
            solution = brain.add_solution(
                problem_id=problem['problem_id'],
                solution=f"轮巡{round_num}自动生成的解决方案",
                confidence=random.uniform(0.5, 0.9),
            )
            result = brain.auto_repair(problem['problem_id'])
            if result.get('success'):
                patrol_stats['problems_resolved'] += 1

        # ------ 记录快照 ------
        if round_num % 10 == 0 or round_num == rounds:
            stats = brain.get_stats()
            snapshot = {
                'round': round_num,
                'total_knowledge': stats['total_knowledge'],
                'total_domains': stats['total_domains'],
                'avg_cognitive_score': stats['avg_cognitive_score'],
                'cognitive_distribution': stats['cognitive_distribution'],
            }
            snapshots.append(snapshot)

    elapsed_time = time.time() - start_time

    # ========== 最终统计 ==========
    print(f"\n\n📊 阶段4：轮巡完成统计")
    print("=" * 70)

    final_stats = brain.get_stats()
    cognitive_report = brain.get_cognitive_report()

    print(f"\n   ⏱️  总耗时: {elapsed_time:.2f} 秒")
    print(f"   📚 知识总量: {final_stats['total_knowledge']} 条")
    print(f"   🌐 知识域: {final_stats['total_domains']} 个")
    print(f"   🕸️ 知识关联: {final_stats['graph_stats']['total_edges']} 条")
    print(f"   📈 平均认知分: {final_stats['avg_cognitive_score']:.3f}")

    print(f"\n   🧠 认知维度分布:")
    for level, count in final_stats['cognitive_distribution'].items():
        level_info = COGNITIVE_LEVELS.get(level, {})
        bar = "█" * (count // 5)
        print(f"     {level} ({level_info.get('name', '')}): {count:4d}条 {bar}")

    print(f"\n   📝 轮巡操作统计:")
    for op, count in patrol_stats.items():
        print(f"     • {op}: {count}")

    print(f"\n   🎯 认知成熟度: {cognitive_report['maturity_level']}")
    print(f"   📊 认知成熟度分: {cognitive_report['cognitive_maturity_score']:.3f}")

    print(f"\n   💡 提升建议:")
    for rec in cognitive_report['recommendations']:
        print(f"     • {rec}")

    # ========== 图谱统计 ==========
    graph_stats = final_stats['graph_stats']
    print(f"\n   🕸️ 知识图谱统计:")
    print(f"     • 节点数: {graph_stats['total_nodes']}")
    print(f"     • 关联数: {graph_stats['total_edges']}")
    print(f"     • 领域数: {graph_stats['total_domains']}")
    print(f"     • 平均认知分: {graph_stats['avg_cognitive_score']:.3f}")

    # ========== 保存报告 ==========
    report = {
        'test_time': datetime.now().isoformat(),
        'elapsed_seconds': round(elapsed_time, 2),
        'patrol_stats': patrol_stats,
        'cognitive_report': cognitive_report,
        'final_stats': final_stats,
        'snapshots': snapshots,
    }

    report_path = os.path.join(PROJECT_ROOT, 'docs', 'brain_patrol_report.json')
    os.makedirs(os.path.dirname(report_path), exist_ok=True)

    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"\n   💾 报告已保存: {report_path}")

    # ========== 验证测试 ==========
    print(f"\n\n✅ 阶段5：功能验证")
    print("-" * 50)

    # 测试1：知识搜索
    test_queries = ["架构设计", "机器学习", "AI"]
    for query in test_queries:
        results = brain.search_knowledge(query, top_k=3)
        print(f"   🔍 搜索'{query}': 找到 {len(results)} 条结果")

    # 测试2：跨域推理
    test_pairs = [
        ("AI架构", "机器学习"),
        ("安全防护", "区块链"),
        ("云计算", "物联网"),
    ]
    for src, tgt in test_pairs:
        result = brain.cross_domain_reason(src, tgt)
        if result.get('success'):
            print(f"   🔗 {src}→{tgt}: 置信度 {result['confidence']:.3f}，关联 {result['cross_relations_count']} 条")
        else:
            print(f"   🔗 {src}→{tgt}: {result.get('reason', '失败')}")

    # 测试3：知识拓展
    test_topics = ["微服务", "深度学习"]
    for topic in test_topics:
        expanded = brain.expand_knowledge(topic, depth=3)
        print(f"   🌱 拓展'{topic}': 生成 {len(expanded)} 条关联知识")

    print(f"\n{'=' * 70}")
    print(f"✅ 脑库100次轮巡测试完成！")
    print(f"{'=' * 70}")

    return report


if __name__ == '__main__':
    # 运行100次轮巡测试（可调整为500次以获得更显著的认知提升）
    report = run_brain_patrol(rounds=100)
