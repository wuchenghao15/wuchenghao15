# -*- coding: utf-8 -*-
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
后台维护AI服务示例和使用说明
"""

import time
import threading
from app.services.backend_maintenance_ai import (
    backend_maintenance_ai,
    MaintenanceStatus,
    MaintenanceTaskType,
    start_maintenance_ai,
    stop_maintenance_ai
)
from app.services.error_report_service import (
    error_report_service,
    ErrorLevel,
    ErrorCategory
)


def example_start_and_monitor():
    """启动和监控示例"""
    print("=" * 60)
    print("后台维护AI - 启动和监控")
    print("=" * 60)
    
    # 启动维护AI
    print("启动后台维护AI...")
    backend_maintenance_ai.start()
    
    # 等待启动
    time.sleep(2)
    
    # 检查状态
    status = backend_maintenance_ai.get_status()
    print(f"当前状态: {status.value}")
    
    # 运行一个测试错误
    print("\n生成测试错误...")
    for i in range(3):
        try:
            raise ValueError(f"测试错误 {i+1}")
        except Exception as e:
            error_report_service.capture_error(
                e,
                level=ErrorLevel.WARNING,
                category=ErrorCategory.SYSTEM
            )
    
    # 等待维护任务执行
    print("\n等待维护任务执行...")
    time.sleep(10)
    
    # 获取摘要
    summary = backend_maintenance_ai.get_summary()
    print("\n维护摘要:")
    print(f"  状态: {summary['status']}")
    print(f"  总错误数: {summary['error_stats']['total_errors']}")
    print(f"  已解决: {summary['error_stats']['resolved_count']}")
    print(f"  未解决: {summary['error_stats']['unresolved_count']}")
    print(f"  脑库知识数: {summary['brain_stats']['total_knowledge']}")
    print(f"  脑库平均成功率: {summary['brain_stats']['avg_success_rate']}")
    
    # 获取最后报告
    last_report = backend_maintenance_ai.get_last_report()
    if last_report:
        print(f"\n最后报告: {last_report.report_id}")
        print(f"  发现错误: {last_report.errors_found}")
        print(f"  修复错误: {last_report.errors_fixed}")
        print(f"  新增知识: {last_report.knowledge_added}")
        
        print("\n任务详情:")
        for task in last_report.tasks:
            print(f"  - {task.task_type.value}: {task.status} ({task.message})")


def example_pause_resume():
    """暂停和恢复示例"""
    print("\n" + "=" * 60)
    print("后台维护AI - 暂停和恢复")
    print("=" * 60)
    
    # 暂停
    print("暂停维护AI...")
    backend_maintenance_ai.pause()
    status = backend_maintenance_ai.get_status()
    print(f"当前状态: {status.value}")
    
    # 恢复
    print("\n恢复维护AI...")
    backend_maintenance_ai.resume()
    status = backend_maintenance_ai.get_status()
    print(f"当前状态: {status.value}")


def example_run_single_task():
    """运行单个任务示例"""
    print("\n" + "=" * 60)
    print("后台维护AI - 运行单个任务")
    print("=" * 60)
    
    # 运行健康检查任务
    print("运行系统健康检查任务...")
    task = backend_maintenance_ai.run_single_task(MaintenanceTaskType.SYSTEM_HEALTH)
    print(f"任务ID: {task.task_id}")
    print(f"状态: {task.status}")
    print(f"消息: {task.message}")
    
    # 运行错误监控任务
    print("\n运行错误监控任务...")
    task = backend_maintenance_ai.run_single_task(MaintenanceTaskType.ERROR_MONITORING)
    print(f"任务ID: {task.task_id}")
    print(f"状态: {task.status}")
    print(f"消息: {task.message}")


def example_stop():
    """停止示例"""
    print("\n" + "=" * 60)
    print("后台维护AI - 停止")
    print("=" * 60)
    
    print("停止维护AI...")
    backend_maintenance_ai.stop()
    
    # 验证停止
    status = backend_maintenance_ai.get_status()
    print(f"当前状态: {status.value}")


def example_integration_with_app():
    """与应用集成示例"""
    print("\n" + "=" * 60)
    print("后台维护AI - 与Flask应用集成")
    print("=" * 60)
    
    # 模拟Flask应用启动
    print("模拟Flask应用启动...")
    
    def simulate_app_start():
        """模拟应用启动时启动维护AI"""
        print("Flask应用启动中...")
        start_maintenance_ai()
        print("后台维护AI已自动启动")
    
    # 启动应用
    simulate_app_start()
    
    # 运行一段时间后停止
    print("\n模拟应用运行中...")
    time.sleep(5)
    
    # 获取摘要
    summary = backend_maintenance_ai.get_summary()
    print(f"运行摘要:")
    print(f"  状态: {summary['status']}")
    print(f"  总错误数: {summary['error_stats']['total_errors']}")


def run_all_examples():
    """运行所有示例"""
    example_start_and_monitor()
    example_pause_resume()
    example_run_single_task()
    example_integration_with_app()
    example_stop()
    
    print("\n" + "=" * 60)
    print("所有示例执行完成")
    print("=" * 60)


if __name__ == "__main__":
    run_all_examples()
