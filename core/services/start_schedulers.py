#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
启动所有自动化计划策略
"""

import sys
import os
import logging
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def start_all_schedulers():
    """启动所有调度器"""
    results = []
    
    logger.info("="*60)
    logger.info("开始启动所有自动化计划策略...")
    logger.info("="*60)
    
    # 1. 启动核心调度器
    try:
        from core.scheduler import scheduler
        scheduler.start()
        results.append({
            'name': '核心调度器',
            'module': 'core/scheduler.py',
            'status': 'success',
            'message': '核心调度器已启动'
        })
        logger.info("✅ 核心调度器启动成功")
    except Exception as e:
        results.append({
            'name': '核心调度器',
            'module': 'core/scheduler.py',
            'status': 'failed',
            'message': str(e)
        })
        logger.error(f"❌ 核心调度器启动失败: {e}")
    
    # 2. 启动自动计划调度器
    try:
        import schedule
        schedule.clear()
        
        from ai_engines.auto_scheduler import AutoScheduler
        auto_scheduler = AutoScheduler()
        auto_scheduler.load_default_tasks()
        auto_scheduler.start_scheduler()
        results.append({
            'name': '自动计划调度器',
            'module': 'ai_engines/auto_scheduler.py',
            'status': 'success',
            'message': f'自动计划调度器已启动，加载了 {len(auto_scheduler.scheduled_tasks)} 个任务'
        })
        logger.info(f"✅ 自动计划调度器启动成功，加载了 {len(auto_scheduler.scheduled_tasks)} 个任务")
        
        for task_id, task in auto_scheduler.scheduled_tasks.items():
            logger.info(f"   └─ {task_id}: {task.get('name')}")
    except Exception as e:
        results.append({
            'name': '自动计划调度器',
            'module': 'ai_engines/auto_scheduler.py',
            'status': 'failed',
            'message': str(e)
        })
        logger.error(f"❌ 自动计划调度器启动失败: {e}")
    
    # 3. 启动AI任务调度器
    try:
        from app.ai.ai_task_scheduler import AITaskScheduler
        ai_task_scheduler = AITaskScheduler()
        result = ai_task_scheduler.start_scheduler()
        if result['success']:
            results.append({
                'name': 'AI任务调度器',
                'module': 'app/ai/ai_task_scheduler.py',
                'status': 'success',
                'message': result['message']
            })
            logger.info(f"✅ AI任务调度器启动成功")
            logger.info(f"   └─ 预生成AI员工数: {len(ai_task_scheduler._active_employees)}")
            logger.info(f"   └─ 待处理任务数: {len(ai_task_scheduler._task_queue)}")
        else:
            results.append({
                'name': 'AI任务调度器',
                'module': 'app/ai/ai_task_scheduler.py',
                'status': 'failed',
                'message': result['message']
            })
            logger.error(f"❌ AI任务调度器启动失败: {result['message']}")
    except Exception as e:
        results.append({
            'name': 'AI任务调度器',
            'module': 'app/ai/ai_task_scheduler.py',
            'status': 'failed',
            'message': str(e)
        })
        logger.error(f"❌ AI任务调度器启动失败: {e}")
    
    # 4. 启动协作任务调度器
    try:
        from app.agents.collaborative_task_scheduler import init_task_scheduler
        collab_scheduler = init_task_scheduler()
        results.append({
            'name': '协作任务调度器',
            'module': 'app/agents/collaborative_task_scheduler.py',
            'status': 'success',
            'message': '协作任务调度器已启动'
        })
        logger.info("✅ 协作任务调度器启动成功")
    except Exception as e:
        results.append({
            'name': '协作任务调度器',
            'module': 'app/agents/collaborative_task_scheduler.py',
            'status': 'failed',
            'message': str(e)
        })
        logger.error(f"❌ 协作任务调度器启动失败: {e}")
    
    # 5. 初始化AI题库维护系统
    try:
        from ai_engines.ai_question_maintenance import ai_question_maintenance
        stats = ai_question_maintenance.get_integrated_statistics()
        results.append({
            'name': 'AI题库维护系统',
            'module': 'ai_engines/ai_question_maintenance.py',
            'status': 'success',
            'message': f'AI题库维护系统已初始化，当前题库共 {stats.get("total_questions", 0)} 道题目'
        })
        logger.info(f"✅ AI题库维护系统初始化成功")
        logger.info(f"   └─ 当前题目数: {stats.get('total_questions', 0)}")
        logger.info(f"   └─ 听力题目数: {stats.get('listening_questions', 0)}")
    except Exception as e:
        results.append({
            'name': 'AI题库维护系统',
            'module': 'ai_engines/ai_question_maintenance.py',
            'status': 'failed',
            'message': str(e)
        })
        logger.error(f"❌ AI题库维护系统初始化失败: {e}")
    
    logger.info("="*60)
    logger.info("所有自动化计划策略启动完成")
    logger.info("="*60)
    
    # 输出汇总
    success_count = sum(1 for r in results if r['status'] == 'success')
    failed_count = len(results) - success_count
    
    logger.info(f"\n启动结果汇总:")
    logger.info(f"  成功: {success_count}/{len(results)}")
    logger.info(f"  失败: {failed_count}/{len(results)}")
    
    for result in results:
        status = "✅" if result['status'] == 'success' else "❌"
        logger.info(f"  {status} {result['name']}: {result['message']}")
    
    return {
        'success': failed_count == 0,
        'results': results,
        'success_count': success_count,
        'failed_count': failed_count
    }

def run_demo_tasks():
    """运行演示任务验证调度器"""
    logger.info("\n" + "="*60)
    logger.info("执行演示任务验证调度器...")
    logger.info("="*60)
    
    try:
        from core.scheduler import scheduler
        
        def demo_maintenance_task():
            logger.info("[演示任务] 执行定时维护检查...")
        
        def demo_data_cleanup():
            logger.info("[演示任务] 执行数据清理...")
        
        scheduler.add_task(
            task_id="demo_maintenance",
            func=demo_maintenance_task,
            schedule_type="interval",
            minutes=1
        )
        logger.info("✅ 已添加演示任务: 维护检查 (每1分钟)")
        
        scheduler.add_task(
            task_id="demo_cleanup",
            func=demo_data_cleanup,
            schedule_type="interval",
            minutes=2
        )
        logger.info("✅ 已添加演示任务: 数据清理 (每2分钟)")
        
        logger.info("当前调度器任务列表:")
        tasks = scheduler.get_all_tasks()
        for task_id, info in tasks.items():
            logger.info(f"   └─ {task_id}: {info}")
    
    except Exception as e:
        logger.error(f"❌ 添加演示任务失败: {e}")

if __name__ == "__main__":
    result = start_all_schedulers()
    
    if result['success']:
        run_demo_tasks()
        
        logger.info("\n" + "="*60)
        logger.info("所有自动化计划策略已成功启动！")
        logger.info("系统将持续运行定时任务...")
        logger.info("按 Ctrl+C 退出")
        logger.info("="*60)
        
        try:
            while True:
                time.sleep(5)
        except KeyboardInterrupt:
            logger.info("\n收到停止信号，正在关闭调度器...")
    else:
        logger.error("\n部分调度器启动失败，请检查日志")
        sys.exit(1)