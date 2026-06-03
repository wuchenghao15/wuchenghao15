# -*- coding: utf-8 -*-
from app.services.deep_optimization_service import deep_optimization_service, OptimizationLevel

# 优化AI引擎
deep_optimization_service.optimize_ai_engine(OptimizationLevel.ADVANCED)

# 优化数据库
deep_optimization_service.optimize_database(OptimizationLevel.ADVANCED)

# 优化缓存系统
deep_optimization_service.optimize_cache(OptimizationLevel.ADVANCED)#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
深度优化服务示例 - 全面优化项目主功能、AI功能和子系统
"""

from app.services.deep_optimization_service import (
    deep_optimization_service,
    run_deep_optimization,
    OptimizationLevel
)


def example_optimize_ai_engine():
    """优化AI引擎"""
    print("=" * 60)
    print("深度优化 - AI引擎优化")
    print("=" * 60)
    
    task = deep_optimization_service.optimize_ai_engine(OptimizationLevel.ADVANCED)
    
    print(f"任务ID: {task.task_id}")
    print(f"状态: {task.status}")
    print(f"优化指标:")
    for metric, improvement in task.metrics.items():
        print(f"  {metric}: +{improvement}%")
    print(f"建议:")
    for rec in task.recommendations[:3]:
        print(f"  - {rec}")


def example_optimize_database():
    """优化数据库"""
    print("\n" + "=" * 60)
    print("深度优化 - 数据库优化")
    print("=" * 60)
    
    task = deep_optimization_service.optimize_database(OptimizationLevel.ADVANCED)
    
    print(f"任务ID: {task.task_id}")
    print(f"状态: {task.status}")
    print(f"优化指标:")
    for metric, improvement in task.metrics.items():
        print(f"  {metric}: +{improvement}%")


def example_optimize_cache():
    """优化缓存系统"""
    print("\n" + "=" * 60)
    print("深度优化 - 缓存系统优化")
    print("=" * 60)
    
    task = deep_optimization_service.optimize_cache(OptimizationLevel.ADVANCED)
    
    print(f"任务ID: {task.task_id}")
    print(f"状态: {task.status}")
    print(f"优化指标:")
    for metric, improvement in task.metrics.items():
        print(f"  {metric}: +{improvement}%")


def example_optimize_network():
    """优化网络层"""
    print("\n" + "=" * 60)
    print("深度优化 - 网络层优化")
    print("=" * 60)
    
    task = deep_optimization_service.optimize_network(OptimizationLevel.ADVANCED)
    
    print(f"任务ID: {task.task_id}")
    print(f"状态: {task.status}")
    print(f"优化指标:")
    for metric, improvement in task.metrics.items():
        print(f"  {metric}: +{improvement}%")


def example_optimize_code():
    """优化代码质量"""
    print("\n" + "=" * 60)
    print("深度优化 - 代码优化")
    print("=" * 60)
    
    task = deep_optimization_service.optimize_code(OptimizationLevel.ADVANCED)
    
    print(f"任务ID: {task.task_id}")
    print(f"状态: {task.status}")
    print(f"优化指标:")
    for metric, improvement in task.metrics.items():
        print(f"  {metric}: +{improvement}%")


def example_full_optimization():
    """全面优化"""
    print("\n" + "=" * 60)
    print("深度优化 - 全面优化")
    print("=" * 60)
    
    report = run_deep_optimization("advanced")
    
    print(f"\n优化报告ID: {report.report_id}")
    print(f"任务总数: {report.total_tasks}")
    print(f"完成任务: {report.completed_tasks}")
    print(f"失败任务: {report.failed_tasks}")
    
    print("\n性能提升:")
    for area, improvement in report.performance_improvements.items():
        print(f"  {area}: +{improvement}%")
    
    print(f"\n内存节省: {report.memory_savings}%")
    
    print("\nAI优化:")
    for area, improvement in report.ai_improvements.items():
        print(f"  {area}: +{improvement}%")
    
    print("\n优化建议:")
    for i, rec in enumerate(report.recommendations[:5], 1):
        print(f"  {i}. {rec}")


def example_show_history():
    """显示优化历史"""
    print("\n" + "=" * 60)
    print("深度优化 - 优化历史")
    print("=" * 60)
    
    history = deep_optimization_service.get_optimization_history()
    print(f"优化记录数: {len(history)}")
    
    if history:
        print("\n最近优化记录:")
        for record in history[-3:]:
            print(f"  类型: {record['type']}")
            print(f"  级别: {record['level']}")
            print(f"  提升: {record['improvements']}")


def run_all():
    """运行所有示例"""
    example_optimize_ai_engine()
    example_optimize_database()
    example_optimize_cache()
    example_optimize_network()
    example_optimize_code()
    example_full_optimization()
    example_show_history()
    
    print("\n" + "=" * 60)
    print("深度优化服务示例执行完成")
    print("=" * 60)


if __name__ == "__main__":
    run_all()
