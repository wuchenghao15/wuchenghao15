#!/usr/bin/env python3
import os
import sys
import time
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

logger.info("="*60)
logger.info("启动所有自动化计划和进程")
logger.info("="*60)

logger.info("\n[1/5] 初始化VersionAgentAI...")
try:
    from ai_engines.version_agent_ai import version_agent_ai
    status = version_agent_ai.get_status()
    logger.info(f"  ✓ VersionAgentAI状态: {status['status']}")
    logger.info(f"  ✓ 当前版本: {status['current_version']}")
    logger.info(f"  ✓ 维护计划数: {status['maintenance_plans_count']}")
except Exception as e:
    logger.info(f"  ✗ VersionAgentAI初始化失败: {e}")

logger.info("\n[2/5] 初始化AutomationPlanAgent...")
try:
    from ai_engines.automation_plan_agent import automation_plan_agent
    status = automation_plan_agent.get_status()
    logger.info(f"  ✓ AutomationPlanAgent状态: {status['status']}")
    logger.info(f"  ✓ 当前计划数: {status['total_plans']}")
    logger.info(f"  ✓ 调度器运行中: {status['scheduler_running']}")
except Exception as e:
    logger.info(f"  ✗ AutomationPlanAgent初始化失败: {e}")

logger.info("\n[3/5] 执行计划分析...")
try:
    analysis = automation_plan_agent.analyze_plans()
    logger.info(f"  ✓ 计划总数: {analysis['total_plans']}")
    logger.info(f"  ✓ 完全覆盖: {len(analysis['fully_covered_areas'])} 个功能区域")
    logger.info(f"  ✓ 部分覆盖: {len(analysis['partial_function_areas'])} 个功能区域")
    logger.info(f"  ✓ 缺失功能: {len(analysis['missing_function_areas'])} 个功能区域")
except Exception as e:
    logger.info(f"  ✗ 计划分析失败: {e}")

logger.info("\n[4/5] 拓展缺失功能...")
try:
    expansion = automation_plan_agent.expand_features()
    logger.info(f"  ✓ 新增计划数: {expansion['new_plans_created']}")
    if expansion['plan_details']:
        logger.info("  ✓ 新增计划:")
        for plan in expansion['plan_details'][:5]:
            logger.info(f"    - {plan['name']} ({plan['plan_type']}, {plan['priority']})")
except Exception as e:
    logger.info(f"  ✗ 拓展功能失败: {e}")

logger.info("\n[5/5] 优化现有计划...")
try:
    optimization = automation_plan_agent.optimize_plans()
    logger.info(f"  ✓ 优化计划数: {optimization['total_plans']}")
    logger.info(f"  ✓ 优化项数: {optimization['total_optimizations']}")
    logger.info(f"  ✓ 预期整体提升: {optimization['expected_overall_improvement']:.1%}")
except Exception as e:
    logger.info(f"  ✗ 优化计划失败: {e}")

logger.info("\n[6/5] 执行每日健康检查...")
try:
    from ai_engines.version_agent_ai import version_agent_ai
    result = version_agent_ai.execute_maintenance_plan('daily_health_check')
    logger.info(f"  ✓ 健康检查状态: {'成功' if result['success'] else '失败'}")
    logger.info(f"  ✓ 任务总数: {result['total_tasks']}")
    logger.info(f"  ✓ 成功任务: {result['success_tasks']}")
    logger.info(f"  ✓ 失败任务: {result['failed_tasks']}")
except Exception as e:
    logger.info(f"  ✗ 健康检查执行失败: {e}")

logger.info("\n" + "="*60)
logger.info("所有自动化计划和进程已启动！")
logger.info("="*60)
logger.info("\n运行中的Agent:")
logger.info("  - VersionAgentAI (系统版本管理)")
logger.info("  - AutomationPlanAgent (自动化计划拓展)")
logger.info("\n定时任务:")
logger.info("  - VersionAgentAI调度器: 每分钟检查维护计划")
logger.info("  - AutomationPlanAgent调度器: 每小时自动分析拓展")
logger.info("\n访问API:")
logger.info("  - http://localhost:8888/version-agent/status")
logger.info("  - http://localhost:8888/automation-plan-agent/status")