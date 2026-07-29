# -*- coding: utf-8 -*-
"""
自动计划验证脚本 - 运行所有计划并生成报告
============================================

运行方式:
    python scripts/python/auto_plans_test.py

将执行所有已注册的自动化计划并生成汇总报告。
"""

from __future__ import annotations

import json
import os
import sys
import time
import traceback
from datetime import datetime


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))
sys.path.insert(0, PROJECT_ROOT)


def main():
    print('=' * 70)
    print('  MTSCOS AI 自动计划验证与运行')
    print(f'  时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    print('=' * 70)

    # 1. 初始化调度器
    print('\n[1] 初始化计划调度器...')
    from core.services.auto_plans import (
        create_all_plans_and_register,
        get_plan_scheduler,
        list_all_plans,
        get_dynamic_generator,
    )

    scheduler = create_all_plans_and_register()
    plans_info = list_all_plans()
    print(f'    已注册计划: {len(plans_info)} 个')
    for p in plans_info:
        print(f'      [{p.category:>12}] {p.name} ({p.plan_id}) - 间隔 {p.interval_seconds}s')

    # 2. AI 自动延展
    print('\n[2] AI 自动延展新计划...')
    try:
        generator = get_dynamic_generator()
        auto_generated = generator.scan_and_generate()
        print(f'    AI 生成新计划: {len(auto_generated)} 个')
        for ag in auto_generated[:5]:
            print(f'      + {ag["name"]} ({ag["plan_id"]})')
        if len(auto_generated) > 5:
            print(f'      ... 及其他 {len(auto_generated) - 5} 个')
    except Exception as e:
        print(f'    AI 延展跳过: {e}')

    # 3. 运行所有计划
    print('\n[3] 执行所有计划...')
    results = scheduler.run_all()
    success_count = sum(1 for r in results.values() if r.success)
    fail_count = len(results) - success_count

    print(f'    总计: {len(results)} 个计划')
    print(f'    成功: {success_count} 个')
    print(f'    失败: {fail_count} 个')

    # 4. 详细结果
    print('\n[4] 详细执行结果:')
    print('-' * 70)
    for pid, result in sorted(results.items()):
        status = '✅' if result.success else '❌'
        duration = result.duration_ms
        msg = result.message[:80]
        print(f'    {status} {pid:<35} {duration:>5}ms  {msg}')
        if result.errors:
            for err in result.errors[:2]:
                print(f'       ⚠️  {err[:100]}')

    # 5. 分类统计
    print('\n[5] 分类统计:')
    print('-' * 70)
    category_stats = {}
    for pid, result in results.items():
        plan = scheduler.get_plan(pid)
        if plan:
            cat = plan.category
            if cat not in category_stats:
                category_stats[cat] = {'total': 0, 'success': 0}
            category_stats[cat]['total'] += 1
            if result.success:
                category_stats[cat]['success'] += 1

    for cat, stats in sorted(category_stats.items()):
        rate = round(stats['success'] / stats['total'] * 100, 1) if stats['total'] > 0 else 0
        print(f'    {cat:>12}: {stats["success"]}/{stats["total"]} 成功 ({rate}%)')

    # 6. 启动定时调度
    print('\n[6] 启动定时调度器...')
    scheduler.start_all()
    status = scheduler.get_overall_status()
    print(f'    总计划: {status["total_plans"]}')
    print(f'    活跃中: {status["active_plans"]}')
    print(f'    运行状态: {"运行中" if status["running"] else "已停止"}')

    # 7. 最终报告
    print('\n' + '=' * 70)
    print('  验证报告汇总')
    print('=' * 70)
    print(f'  时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    print(f'  已注册计划: {status["total_plans"]} 个')
    print(f'  本次执行: {len(results)} 个计划')
    print(f'  成功: {success_count} 个')
    print(f'  失败: {fail_count} 个')
    print(f'  AI 延展生成: {len(auto_generated) if "auto_generated" in dir() else 0} 个')
    print(f'  定时调度: 已启动')

    # 8. 保存报告
    report = {
        'timestamp': datetime.now().isoformat(),
        'total_plans': status['total_plans'],
        'executed': len(results),
        'success': success_count,
        'failed': fail_count,
        'ai_generated': len(auto_generated) if 'auto_generated' in dir() else 0,
        'results': {
            pid: {
                'success': r.success,
                'message': r.message,
                'duration_ms': r.duration_ms,
                'errors': r.errors,
            }
            for pid, r in results.items()
        },
        'category_stats': category_stats,
    }

    report_dir = os.path.join(PROJECT_ROOT, 'logs')
    os.makedirs(report_dir, exist_ok=True)
    report_path = os.path.join(report_dir, f'auto_plans_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f'\n  报告已保存: {report_path}')
    print('\n  ✅ 所有计划验证完成！')

    # 9. 展示 API 端点
    print('\n' + '=' * 70)
    print('  API 端点 (需服务器运行)')
    print('=' * 70)
    print('  GET  /api/auto_plans/status        - 查看所有计划状态')
    print('  POST /api/auto_plans/run_all        - 执行所有计划')
    print('  POST /api/auto_plans/run/<plan_id>  - 执行指定计划')
    print('  POST /api/auto_plans/toggle/<plan_id> - 启用/禁用计划')
    print('=' * 70)


if __name__ == '__main__':
    main()
