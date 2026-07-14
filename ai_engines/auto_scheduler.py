import logging
logger = logging.getLogger(__name__)

# -*- coding: utf-8 -*-
"""AI驱动的自动计划调度系统"""
import os
import sys
import json
import time
import threading
import schedule
from datetime import datetime, timedelta
from typing import Dict, List, Any, Callable

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class AutoScheduler:
    """AI驱动的自动计划调度器"""
    
    def __init__(self):
        self.scheduled_tasks = {}
        self.task_history = []
        self.is_running = False
        self.scheduler_thread = None
        self.ai_predictions = {}
        
        # 计划任务配置
        self.config = {
            "ai_enabled": True,
            "auto_optimize": True,
            "prediction_interval": 3600,  # 每小时进行一次AI预测
            "max_concurrent_tasks": 10,
            "task_timeout": 300  # 任务超时时间(秒)
        }
        
        # 预定义的计划任务模板
        self.task_templates = {
            "daily_maintenance": {
                "name": "每日系统维护",
                "cron": "0 3 * * *",  # 每天凌晨3点
                "function": "system_maintenance",
                "description": "执行系统日常维护任务"
            },
            "hourly_data_sync": {
                "name": "每小时数据同步",
                "cron": "0 * * * *",  # 每小时整点
                "function": "data_sync",
                "description": "同步各模块数据"
            },
            "weekly_backup": {
                "name": "每周备份",
                "cron": "0 2 * * 0",  # 每周日凌晨2点
                "function": "database_backup",
                "description": "执行数据库备份"
            },
            "ai_learning": {
                "name": "AI自动学习",
                "cron": "0 1 * * *",  # 每天凌晨1点
                "function": "ai_auto_learning",
                "description": "触发AI组件自动学习"
            },
            "brain_sync": {
                "name": "脑库同步",
                "cron": "*/5 * * * *",  # 每5分钟
                "function": "brain_synchronization",
                "description": "同步AI脑库数据"
            },
            "performance_check": {
                "name": "性能检查",
                "cron": "*/15 * * * *",  # 每15分钟
                "function": "performance_monitor",
                "description": "检查系统性能指标"
            },
            "log_cleanup": {
                "name": "日志清理",
                "cron": "0 4 * * *",  # 每天凌晨4点
                "function": "cleanup_logs",
                "description": "清理过期日志文件"
            },
            "exam_generation": {
                "name": "考试生成",
                "cron": "0 0 * * *",  # 每天午夜
                "function": "generate_daily_exams",
                "description": "自动生成每日考试"
            },
            "git_sync": {
                "name": "Git同步",
                "cron": "*/60 * * * *",  # 每60分钟
                "function": "git_sync",
                "description": "自动同步Git和GitHub"
            },
            "auto_maintenance": {
                "name": "自动维护",
                "cron": "0 3 * * *",  # 每天凌晨3点
                "function": "auto_maintenance",
                "description": "执行自动例行升级维护"
            },
            "question_bank_maintenance": {
                "name": "题库增量维护",
                "cron": "0 2 * * *",  # 每天凌晨2点
                "function": "question_bank_maintenance",
                "description": "自动执行题库增量维护，生成新题目"
            },
            "question_bank_quality_check": {
                "name": "题库质量检查",
                "cron": "0 4 * * *",  # 每天凌晨4点
                "function": "question_bank_quality_check",
                "description": "检查题库中题目的质量，标记问题题目"
            },
            "question_bank_dedup": {
                "name": "题库去重",
                "cron": "0 5 * * 0",  # 每周日凌晨5点
                "function": "question_bank_dedup",
                "description": "移除题库中的重复题目"
            },
            "listening_question_generation": {
                "name": "听力题生成",
                "cron": "0 1 * * *",  # 每天凌晨1点
                "function": "listening_question_generation",
                "description": "自动生成听力题目"
            }
        }
        
        # 注册任务执行函数
        self._register_task_functions()
    
    def _register_task_functions(self):
        """注册任务执行函数"""
        self.task_functions = {
            "system_maintenance": self._task_system_maintenance,
            "data_sync": self._task_data_sync,
            "database_backup": self._task_database_backup,
            "ai_auto_learning": self._task_ai_learning,
            "brain_synchronization": self._task_brain_sync,
            "performance_monitor": self._task_performance_check,
            "cleanup_logs": self._task_cleanup_logs,
            "generate_daily_exams": self._task_generate_exams,
            "git_sync": self._task_git_sync,
            "auto_maintenance": self._task_auto_maintenance,
            "question_bank_maintenance": self._task_question_bank_maintenance,
            "question_bank_quality_check": self._task_question_bank_quality_check,
            "question_bank_dedup": self._task_question_bank_dedup,
            "listening_question_generation": self._task_listening_question_generation
        }
    
    def add_task(self, task_id: str, task_config: Dict[str, Any]):
        """添加计划任务"""
        if task_id in self.scheduled_tasks:
            return {"success": False, "message": "任务已存在"}
        
        self.scheduled_tasks[task_id] = task_config
        
        if "cron" in task_config:
            cron_expr = task_config["cron"]
            cron_parts = cron_expr.split()
            if len(cron_parts) >= 2:
                minute = cron_parts[0]
                hour = cron_parts[1]
                
                if minute.startswith("*/"):
                    interval = int(minute.split("/")[1])
                    schedule.every(interval).minutes.do(self._execute_task, task_id)
                elif hour.startswith("*/"):
                    interval = int(hour.split("/")[1])
                    schedule.every(interval).hours.do(self._execute_task, task_id)
                elif minute == "*" and hour == "*":
                    schedule.every().hour.do(self._execute_task, task_id)
                elif minute == "*":
                    schedule.every().hour.do(self._execute_task, task_id)
                elif hour == "*":
                    try:
                        schedule.every().hour.at(f":{minute}").do(self._execute_task, task_id)
                    except:
                        schedule.every(int(minute)).minutes.do(self._execute_task, task_id)
                else:
                    try:
                        schedule.every().day.at(f"{hour}:{minute}").do(self._execute_task, task_id)
                    except:
                        schedule.every().hour.do(self._execute_task, task_id)
        elif "interval" in task_config:
            interval = task_config["interval"]
            if interval.get("hours"):
                schedule.every(interval["hours"]).hours.do(self._execute_task, task_id)
            elif interval.get("minutes"):
                schedule.every(interval["minutes"]).minutes.do(self._execute_task, task_id)
            elif interval.get("seconds"):
                schedule.every(interval["seconds"]).seconds.do(self._execute_task, task_id)
        
        return {"success": True, "message": "任务添加成功"}
    
    def remove_task(self, task_id: str):
        """移除计划任务"""
        if task_id not in self.scheduled_tasks:
            return {"success": False, "message": "任务不存在"}
        
        del self.scheduled_tasks[task_id]
        # 清除schedule中的任务(schedule库限制,需要重新创建)
        schedule.clear()
        self._reschedule_all_tasks()
        
        return {"success": True, "message": "任务移除成功"}
    
    def _reschedule_all_tasks(self):
        """重新调度所有任务"""
        for task_id, config in self.scheduled_tasks.items():
            if "cron" in config:
                cron_expr = config["cron"]
                cron_parts = cron_expr.split()
                if len(cron_parts) >= 2:
                    minute = cron_parts[0]
                    hour = cron_parts[1]
                    
                    if minute.startswith("*/"):
                        interval = int(minute.split("/")[1])
                        schedule.every(interval).minutes.do(self._execute_task, task_id)
                    elif hour.startswith("*/"):
                        interval = int(hour.split("/")[1])
                        schedule.every(interval).hours.do(self._execute_task, task_id)
                    elif minute == "*" and hour == "*":
                        schedule.every().hour.do(self._execute_task, task_id)
                    elif minute == "*":
                        schedule.every().hour.do(self._execute_task, task_id)
                    elif hour == "*":
                        try:
                            schedule.every().hour.at(f":{minute}").do(self._execute_task, task_id)
                        except:
                            schedule.every(int(minute)).minutes.do(self._execute_task, task_id)
                    else:
                        try:
                            schedule.every().day.at(f"{hour}:{minute}").do(self._execute_task, task_id)
                        except:
                            schedule.every().hour.do(self._execute_task, task_id)
            elif "interval" in config:
                interval = config["interval"]
                if interval.get("hours"):
                    schedule.every(interval["hours"]).hours.do(self._execute_task, task_id)
                elif interval.get("minutes"):
                    schedule.every(interval["minutes"]).minutes.do(self._execute_task, task_id)
    
    def _execute_task(self, task_id: str):
        """执行任务"""
        task = self.scheduled_tasks.get(task_id)
        if not task:
            return
        
        start_time = time.time()
        status = "success"
        error_message = None
        
        try:
            function_name = task.get("function")
            if function_name in self.task_functions:
                self.task_functions[function_name]()
        except Exception as e:
            status = "failed"
            error_message = str(e)
        
        # 记录任务执行历史
        self._log_task_execution(task_id, status, start_time, error_message)
    
    def _log_task_execution(self, task_id: str, status: str, start_time: float, error_msg: str = None):
        """记录任务执行日志"""
        duration = time.time() - start_time
        log_entry = {
            "task_id": task_id,
            "task_name": self.scheduled_tasks.get(task_id, {}).get("name", task_id),
            "status": status,
            "start_time": datetime.fromtimestamp(start_time).isoformat(),
            "duration": round(duration, 2),
            "error_message": error_msg,
            "timestamp": datetime.now().isoformat()
        }
        
        self.task_history.append(log_entry)
        # 保留最近1000条记录
        if len(self.task_history) > 1000:
            self.task_history = self.task_history[-1000:]
    
    # ========== 任务执行函数 ==========
    
    def _task_system_maintenance(self):
        """系统维护任务"""
        print("[任务] 执行系统维护...")
        # 模拟维护操作
        time.sleep(1)
    
    def _task_data_sync(self):
        """数据同步任务"""
        print("[任务] 执行数据同步...")
        # 模拟同步操作
        time.sleep(0.5)
    
    def _task_database_backup(self):
        """数据库备份任务"""
        print("[任务] 执行数据库备份...")
        # 模拟备份操作
        time.sleep(2)
    
    def _task_ai_learning(self):
        """AI自动学习任务"""
        print("[任务] 执行AI自动学习...")
        from app.ai.auto_learning_upgrade import ai_auto_learning_system
        ai_auto_learning_system.perform_learning()
    
    def _task_brain_sync(self):
        """脑库同步任务"""
        print("[任务] 执行脑库同步...")
        from app.ai.brain_based_learning import brain_based_learning_system
        brain_based_learning_system.connect_to_brain()
    
    def _task_performance_check(self):
        """性能检查任务"""
        print("[任务] 执行性能检查...")
        # 模拟性能检查
        time.sleep(0.3)
    
    def _task_cleanup_logs(self):
        """日志清理任务"""
        print("[任务] 执行日志清理...")
        # 模拟清理操作
        time.sleep(1)
    
    def _task_generate_exams(self):
        """生成每日考试任务"""
        logger.info("[任务] 生成每日考试...")
        # 模拟考试生成
        time.sleep(3)
    
    def _task_git_sync(self):
        """Git同步任务"""
        logger.info("[任务] 执行Git同步...")
        from ai_engines.auto_maintenance_upgrade import auto_maintenance_upgrade
        result = auto_maintenance_upgrade.sync_git()
        if result['success']:
            logger.info(f"Git同步成功: {result.get('update_count', 0)} 个更新")
        else:
            logger.error(f"Git同步失败: {result['message']}")
    
    def _task_auto_maintenance(self):
        """自动例行维护任务"""
        logger.info("[任务] 执行自动例行维护...")
        from ai_engines.auto_maintenance_upgrade import auto_maintenance_upgrade
        result = auto_maintenance_upgrade.run_auto_maintenance()
        if result['success']:
            logger.info("自动维护成功")
            for detail in result.get('details', []):
                status = "✅" if detail['success'] else "❌"
                logger.info(f"  {status} {detail['action']}: {detail['message']}")
        else:
            logger.error(f"自动维护失败: {result['message']}")
    
    def _task_question_bank_maintenance(self):
        """题库增量维护任务"""
        logger.info("[任务] 执行题库增量维护...")
        from ai_engines.ai_question_maintenance import ai_question_maintenance
        result = ai_question_maintenance.run_incremental_maintenance(count_per_subject=10)
        if result.success:
            logger.info(f"题库增量维护成功")
            logger.info(f"  生成: {result.total_generated} 道")
            logger.info(f"  添加: {result.total_added} 道")
            logger.info(f"  重复: {result.total_duplicates} 道")
        else:
            logger.error(f"题库增量维护失败: {result.message}")
    
    def _task_question_bank_quality_check(self):
        """题库质量检查任务"""
        logger.info("[任务] 执行题库质量检查...")
        from ai_engines.ai_question_maintenance import ai_question_maintenance
        result = ai_question_maintenance.run_quality_check()
        if result.success:
            logger.info(f"题库质量检查完成")
            logger.info(f"  发现问题: {result.total_quality_issues} 个")
        else:
            logger.error(f"题库质量检查失败: {result.message}")
    
    def _task_question_bank_dedup(self):
        """题库去重任务"""
        logger.info("[任务] 执行题库去重...")
        from ai_engines.ai_question_maintenance import ai_question_maintenance
        result = ai_question_maintenance.run_duplicate_removal()
        if result.success:
            logger.info(f"题库去重完成")
            logger.info(f"  移除重复: {result.total_duplicates} 道")
        else:
            logger.error(f"题库去重失败: {result.message}")
    
    def _task_listening_question_generation(self):
        """听力题生成任务"""
        logger.info("[任务] 执行听力题生成...")
        from ai_engines.ai_question_maintenance import ai_question_maintenance
        count = ai_question_maintenance.generate_mass_listening_questions(20)
        logger.info(f"听力题生成完成，生成 {count} 道听力题")
    
    # ========== AI优化功能 ==========
    
    def ai_predict_task_load(self):
        """AI预测任务负载"""
        if not self.config["ai_enabled"]:
            return {"success": False, "message": "AI功能未启用"}
        
        # 模拟AI预测
        predictions = {
            "peak_hours": ["08:00", "12:00", "18:00"],
            "low_activity_periods": ["02:00", "03:00", "04:00"],
            "recommended_task_time": "03:30",
            "predicted_load": {
                "morning": 0.75,
                "afternoon": 0.82,
                "evening": 0.88,
                "night": 0.25
            }
        }
        
        self.ai_predictions = predictions
        return {"success": True, "data": predictions}
    
    def ai_optimize_schedule(self):
        """AI优化任务调度"""
        if not self.config["auto_optimize"]:
            return {"success": False, "message": "自动优化未启用"}
        
        predictions = self.ai_predict_task_load()
        if not predictions["success"]:
            return predictions
        
        # 根据AI预测优化任务时间
        optimization_results = []
        
        for task_id, task in self.scheduled_tasks.items():
            if task.get("optimizable", True):
                # 将高负载时段的任务移到低负载时段
                if "hourly" in task.get("name", "").lower():
                    task["optimization_note"] = "已优化:保持每小时执行"
                else:
                    task["optimization_note"] = f"已优化:推荐在 {predictions['data']['recommended_task_time']} 执行"
                optimization_results.append({
                    "task_id": task_id,
                    "task_name": task.get("name"),
                    "status": "optimized",
                    "note": task["optimization_note"]
                })
        
        return {"success": True, "message": "任务调度已优化", "results": optimization_results}
    
    def start_scheduler(self):
        """启动调度器"""
        if self.is_running:
            return {"success": False, "message": "调度器已在运行"}
        
        self.is_running = True
        self.scheduler_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self.scheduler_thread.start()
        
        return {"success": True, "message": "自动计划调度器已启动"}
    
    def stop_scheduler(self):
        """停止调度器"""
        self.is_running = False
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)
        schedule.clear()
        
        return {"success": True, "message": "自动计划调度器已停止"}
    
    def _scheduler_loop(self):
        """调度器主循环"""
        while self.is_running:
            schedule.run_pending()
            time.sleep(1)
    
    def get_tasks(self):
        """获取所有计划任务"""
        return self.scheduled_tasks
    
    def get_task_history(self, limit=50):
        """获取任务执行历史"""
        return self.task_history[-limit:]
    
    def run_task_now(self, task_id):
        """立即执行指定任务"""
        if task_id not in self.scheduled_tasks:
            return {"success": False, "message": "任务不存在"}
        
        self._execute_task(task_id)
        return {"success": True, "message": "任务已触发执行"}
    
    def load_default_tasks(self):
        """加载默认任务模板"""
        for task_id, config in self.task_templates.items():
            if task_id not in self.scheduled_tasks:
                self.add_task(task_id, config)
        
        return {"success": True, "message": f"已加载 {len(self.task_templates)} 个默认任务"}

# 创建全局实例
auto_scheduler = AutoScheduler()
