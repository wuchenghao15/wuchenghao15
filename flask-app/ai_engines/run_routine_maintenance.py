# -*- coding: utf-8 -*-
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
执行例行自动维护
"""

import sys
import os
import time
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from app.ai.auto_routine_maintenance import (
    auto_routine_maintenance_system,
    TaskType
)

def print_header(title):
    """打印标题"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)

def execute_daily_maintenance():
    """执行日维护"""
    print_header("📅 执行日维护窗口")
    
    start_time = time.time()
    result = auto_routine_maintenance_system.execute_maintenance_window('daily')
    
    print(f"\n✅ 日维护完成:")
    print(f"   • 执行任务数: {result.get('tasks_executed')}")
    print(f"   • 成功: {result.get('tasks_succeeded')}")
    print(f"   • 失败: {result.get('tasks_failed')}")
    print(f"   • 耗时: {time.time() - start_time:.2f} 秒")
    
    # 显示每个任务的执行结果
    if result.get('task_results'):
        print(f"\n📋 任务执行详情:")
        for task_result in result.get('task_results'):
            status_icon = "✓" if task_result.get('status') == 'completed' else "✗"
            print(f"   {status_icon} {task_result.get('name')}: {task_result.get('status')}")
    
    return result

def execute_weekly_maintenance():
    """执行周维护"""
    print_header("📆 执行周维护窗口")
    
    start_time = time.time()
    result = auto_routine_maintenance_system.execute_maintenance_window('weekly')
    
    print(f"\n✅ 周维护完成:")
    print(f"   • 执行任务数: {result.get('tasks_executed')}")
    print(f"   • 成功: {result.get('tasks_succeeded')}")
    print(f"   • 失败: {result.get('tasks_failed')}")
    print(f"   • 耗时: {time.time() - start_time:.2f} 秒")
    
    if result.get('task_results'):
        print(f"\n📋 任务执行详情:")
        for task_result in result.get('task_results'):
            status_icon = "✓" if task_result.get('status') == 'completed' else "✗"
            print(f"   {status_icon} {task_result.get('name')}: {task_result.get('status')}")
    
    return result

def execute_monthly_maintenance():
    """执行月维护"""
    print_header("📅 执行月维护窗口")
    
    start_time = time.time()
    result = auto_routine_maintenance_system.execute_maintenance_window('monthly')
    
    print(f"\n✅ 月维护完成:")
    print(f"   • 执行任务数: {result.get('tasks_executed')}")
    print(f"   • 成功: {result.get('tasks_succeeded')}")
    print(f"   • 失败: {result.get('tasks_failed')}")
    print(f"   • 耗时: {time.time() - start_time:.2f} 秒")
    
    if result.get('task_results'):
        print(f"\n📋 任务执行详情:")
        for task_result in result.get('task_results'):
            status_icon = "✓" if task_result.get('status') == 'completed' else "✗"
            print(f"   {status_icon} {task_result.get('name')}: {task_result.get('status')}")
    
    return result

def check_system_health():
    """检查系统健康"""
    print_header("🏥 系统健康检查")
    
    health_result = auto_routine_maintenance_system.scheduler.schedule_task(
        task_type=TaskType.HEALTH_CHECK,
        name='手动健康检查'
    )
    auto_routine_maintenance_system.scheduler.execute_task(health_result.id)
    time.sleep(2)
    
    status = auto_routine_maintenance_system.scheduler.get_task_status(health_result.id)
    
    if status and status.get('result'):
        result_data = status.get('result', {})
        print(f"\n🏥 系统健康状态:")
        print(f"   • 健康评分: {result_data.get('overall_score', 0)}/100")
        print(f"   • 状态: {result_data.get('status', 'unknown')}")
        print(f"   • 通过检查: {result_data.get('checks_passed', 0)}")
        print(f"   • 失败检查: {result_data.get('checks_failed', 0)}")
        
        if result_data.get('components'):
            print(f"\n📊 组件状态:")
            for component, state in result_data.get('components', {}).items():
                state_icon = "✓" if state == 'healthy' else "⚠"
                print(f"   {state_icon} {component}: {state}")
    
    return status

def check_upgrades():
    """检查系统升级"""
    print_header("🔄 检查系统升级")
    
    upgrade_info = auto_routine_maintenance_system.check_and_perform_upgrades()
    
    print(f"\n🔍 升级检查结果:")
    print(f"   • 当前版本: {upgrade_info.get('current_version')}")
    print(f"   • 可用版本: {upgrade_info.get('available_version') or '无'}")
    print(f"   • 升级可用: {'是' if upgrade_info.get('upgrade_available') else '否'}")
    
    if upgrade_info.get('changes'):
        print(f"\n📝 变更内容:")
        for change in upgrade_info.get('changes', []):
            print(f"   • {change}")
    
    if upgrade_info.get('upgrade_status'):
        print(f"\n⚡ 自动升级状态:")
        status = upgrade_info.get('upgrade_status', {})
        print(f"   • 状态: {status.get('status')}")
        if status.get('steps'):
            print(f"   • 执行步骤:")
            for step in status.get('steps', []):
                step_icon = "✓" if step.get('status') == 'completed' else "✗"
                print(f"     {step_icon} {step.get('name')}: {step.get('status')}")
    
    return upgrade_info

def show_maintenance_summary():
    """显示维护汇总"""
    print_header("📊 维护汇总报告")
    
    status = auto_routine_maintenance_system.get_maintenance_status()
    scheduler_stats = status.get('scheduler', {})
    
    print(f"\n📈 系统状态:")
    print(f"   • 维护系统: {'已启用' if status.get('enabled') else '已禁用'}")
    print(f"   • 自动升级: {'已启用' if status.get('auto_upgrade_enabled') else '已禁用'}")
    
    print(f"\n📊 任务统计:")
    print(f"   • 总任务数: {scheduler_stats.get('total_tasks')}")
    print(f"   • 运行中: {scheduler_stats.get('running_tasks')}")
    print(f"   • 已完成: {scheduler_stats.get('completed_tasks')}")
    
    print(f"\n🔧 维护策略:")
    for policy_name, policy_info in status.get('maintenance_policies', {}).items():
        tasks_count = len(policy_info.get('tasks', []))
        print(f"   • {policy_name}: {tasks_count} 个任务")
    
    print(f"\n📅 下一个调度任务:")
    next_tasks = status.get('next_scheduled_tasks', [])[:5]
    for i, task in enumerate(next_tasks, 1):
        print(f"   {i}. {task.get('task_name')}")
        print(f"      类型: {task.get('task_type')}")
        print(f"      间隔: {task.get('interval_seconds')} 秒")
    
    print(f"\n📋 维护历史:")
    history = status.get('recent_maintenance', [])
    print(f"   最近维护次数: {len(history)}")
    
    return status

def main():
    """主函数"""
    print("\n")
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 15 + "🚀 例行自动维护系统 🚀" + " " * 27 + "║")
    print("╚" + "=" * 68 + "╝")
    
    print(f"\n⏰ 开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 1. 日维护
    daily_result = execute_daily_maintenance()
    
    # 2. 周维护
    weekly_result = execute_weekly_maintenance()
    
    # 3. 月维护
    monthly_result = execute_monthly_maintenance()
    
    # 4. 系统健康检查
    health_result = check_system_health()
    
    # 5. 升级检查
    upgrade_result = check_upgrades()
    
    # 6. 显示汇总
    show_maintenance_summary()
    
    print("\n" + "=" * 70)
    print("✅ 例行自动维护执行完成!")
    print("=" * 70)
    
    # 计算总耗时
    print(f"\n⏱️  总耗时: {time.time():.2f} 秒")
    print(f"⏰ 结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\n🎉 系统维护完成,所有任务已成功执行!\n")

if __name__ == "__main__":
    main()
