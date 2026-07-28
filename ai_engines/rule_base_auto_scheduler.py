#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
规则库自动调度器 - RuleBaseAutoScheduler
负责定期执行规则库维护任务，包括：
- 自动扩充规则库
- 规则整理分类
- 质量检查和去重
- 自动适配系统
- 自动增派AI员工
- 上传数据库
"""

import os
import sys
import time
import json
import sqlite3
import logging
import threading
import schedule
from datetime import datetime
from typing import Dict, List, Any, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logger = logging.getLogger('rule_base_auto_scheduler')


class RuleBaseAutoScheduler:
    """规则库自动调度器"""
    
    def __init__(self):
        self._running = False
        self._scheduler_thread = None
        self._lock = threading.RLock()
        self._db_path = self._find_db_path()
        self._ensure_tables()
        self._scheduled_tasks = []
        
        logger.info("[规则库调度器] 初始化完成")
    
    def _find_db_path(self) -> str:
        search_paths = [
            os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'app.db'),
            os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'instance', 'mtscos.db'),
        ]
        for p in search_paths:
            if os.path.exists(p):
                return p
        return search_paths[0]
    
    def _get_db_connection(self):
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def _ensure_tables(self):
        try:
            with self._get_db_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS rule_maintenance_schedules (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        schedule_id TEXT UNIQUE NOT NULL,
                        task_type TEXT NOT NULL,
                        cron_expression TEXT,
                        interval_type TEXT,
                        interval_value INTEGER,
                        params TEXT,
                        is_active INTEGER DEFAULT 1,
                        last_run REAL,
                        next_run REAL,
                        run_count INTEGER DEFAULT 0,
                        success_count INTEGER DEFAULT 0,
                        failure_count INTEGER DEFAULT 0,
                        created_at REAL DEFAULT (strftime('%s','now'))
                    )
                ''')
                
                conn.commit()
        except Exception as e:
            logger.error(f"[规则库调度器] 初始化数据库失败: {e}")
    
    def start(self):
        """启动调度器"""
        with self._lock:
            if self._running:
                return {"success": False, "message": "调度器已在运行中"}
            
            self._running = True
            
            self._load_scheduled_tasks()
            self._setup_default_schedules()
            
            self._scheduler_thread = threading.Thread(target=self._run_scheduler, daemon=True)
            self._scheduler_thread.start()
            
            logger.info("[规则库调度器] 已启动")
            return {"success": True, "message": "规则库自动调度器已启动"}
    
    def stop(self):
        """停止调度器"""
        with self._lock:
            self._running = False
            schedule.clear()
            
            if self._scheduler_thread:
                self._scheduler_thread.join(timeout=5)
            
            logger.info("[规则库调度器] 已停止")
            return {"success": True, "message": "规则库自动调度器已停止"}
    
    def _run_scheduler(self):
        """运行调度器主循环"""
        while self._running:
            try:
                schedule.run_pending()
                time.sleep(1)
            except Exception as e:
                logger.error(f"[规则库调度器] 调度循环异常: {e}")
                time.sleep(5)
    
    def _load_scheduled_tasks(self):
        """加载已保存的调度任务"""
        try:
            with self._get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM rule_maintenance_schedules WHERE is_active = 1')
                rows = cursor.fetchall()
                
                for row in rows:
                    task_type = row['task_type']
                    interval_type = row['interval_type']
                    interval_value = row['interval_value']
                    params = json.loads(row['params']) if row['params'] else {}
                    
                    self._schedule_task(task_type, interval_type, interval_value, params)
                    self._scheduled_tasks.append({
                        "schedule_id": row['schedule_id'],
                        "task_type": task_type,
                        "interval_type": interval_type,
                        "interval_value": interval_value
                    })
                
                logger.info(f"[规则库调度器] 已加载 {len(self._scheduled_tasks)} 个调度任务")
        except Exception as e:
            logger.error(f"[规则库调度器] 加载调度任务失败: {e}")
    
    def _setup_default_schedules(self):
        """设置默认调度任务"""
        default_schedules = [
            {"task_type": "full_maintenance", "interval_type": "daily", "interval_value": 1, "params": {}},
            {"task_type": "expand_rules", "interval_type": "hourly", "interval_value": 6, "params": {"source_type": "all", "target_count": 50}},
            {"task_type": "quality_check", "interval_type": "daily", "interval_value": 1, "params": {"check_type": "all"}},
            {"task_type": "duplicate_removal", "interval_type": "daily", "interval_value": 1, "params": {}},
            {"task_type": "system_adapt", "interval_type": "hourly", "interval_value": 4, "params": {}},
            {"task_type": "deploy_employees", "interval_type": "weekly", "interval_value": 1, "params": {}}
        ]
        
        for schedule_info in default_schedules:
            if not self._schedule_exists(schedule_info['task_type']):
                self.add_schedule(
                    schedule_info['task_type'],
                    schedule_info['interval_type'],
                    schedule_info['interval_value'],
                    schedule_info['params']
                )
    
    def _schedule_exists(self, task_type: str) -> bool:
        """检查调度是否已存在"""
        try:
            with self._get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT COUNT(*) FROM rule_maintenance_schedules WHERE task_type = ? AND is_active = 1', (task_type,))
                return cursor.fetchone()[0] > 0
        except Exception:
            return False
    
    def _schedule_task(self, task_type: str, interval_type: str, interval_value: int, params: Dict):
        """内部调度任务"""
        job_func = lambda t=task_type, p=params: self._execute_scheduled_task(t, p)
        
        if interval_type == "hourly":
            schedule.every(interval_value).hours.do(job_func)
        elif interval_type == "daily":
            schedule.every(interval_value).days.do(job_func)
        elif interval_type == "weekly":
            schedule.every(interval_value).weeks.do(job_func)
        elif interval_type == "minutes":
            schedule.every(interval_value).minutes.do(job_func)
        elif interval_type == "seconds":
            schedule.every(interval_value).seconds.do(job_func)
    
    def add_schedule(self, task_type: str, interval_type: str, interval_value: int, params: Dict = None) -> Dict:
        """添加调度任务"""
        if params is None:
            params = {}
        
        try:
            schedule_id = f"RBS-{int(time.time())}"
            
            with self._get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO rule_maintenance_schedules (
                        schedule_id, task_type, interval_type, interval_value, params
                    ) VALUES (?, ?, ?, ?, ?)
                ''', (schedule_id, task_type, interval_type, interval_value, json.dumps(params)))
                conn.commit()
            
            self._schedule_task(task_type, interval_type, interval_value, params)
            self._scheduled_tasks.append({
                "schedule_id": schedule_id,
                "task_type": task_type,
                "interval_type": interval_type,
                "interval_value": interval_value
            })
            
            logger.info(f"[规则库调度器] 添加调度任务: {task_type} ({interval_type} {interval_value})")
            return {
                "success": True,
                "message": f"调度任务已添加: {task_type}",
                "schedule_id": schedule_id,
                "task_type": task_type
            }
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def remove_schedule(self, schedule_id: str) -> Dict:
        """移除调度任务"""
        try:
            with self._get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM rule_maintenance_schedules WHERE schedule_id = ?', (schedule_id,))
                conn.commit()
            
            self._scheduled_tasks = [t for t in self._scheduled_tasks if t['schedule_id'] != schedule_id]
            
            logger.info(f"[规则库调度器] 移除调度任务: {schedule_id}")
            return {
                "success": True,
                "message": f"调度任务已移除: {schedule_id}"
            }
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def list_schedules(self) -> Dict:
        """列出所有调度任务"""
        try:
            with self._get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM rule_maintenance_schedules')
                rows = cursor.fetchall()
                
                schedules = []
                for row in rows:
                    schedules.append({
                        "schedule_id": row['schedule_id'],
                        "task_type": row['task_type'],
                        "interval_type": row['interval_type'],
                        "interval_value": row['interval_value'],
                        "params": json.loads(row['params']) if row['params'] else {},
                        "is_active": bool(row['is_active']),
                        "last_run": datetime.fromtimestamp(row['last_run']).isoformat() if row['last_run'] else None,
                        "run_count": row['run_count'],
                        "success_count": row['success_count'],
                        "failure_count": row['failure_count'],
                        "created_at": datetime.fromtimestamp(row['created_at']).isoformat()
                    })
                
                return {
                    "success": True,
                    "schedules": schedules,
                    "total": len(schedules)
                }
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _execute_scheduled_task(self, task_type: str, params: Dict):
        """执行调度任务"""
        logger.info(f"[规则库调度器] 执行调度任务: {task_type}")
        
        try:
            from ai_engines.ai_employee_manager import AIEmployeeManager
            
            manager = AIEmployeeManager()
            
            task_data = {
                "task_type": task_type,
                **params
            }
            
            result = manager.auto_assign_task(task_data)
            
            self._update_schedule_status(task_type, result.get("success", False))
            
            if result.get("success", False):
                logger.info(f"[规则库调度器] 任务执行成功: {task_type}")
            else:
                logger.error(f"[规则库调度器] 任务执行失败: {task_type}, 错误: {result.get('message', '')}")
        
        except Exception as e:
            logger.error(f"[规则库调度器] 执行任务异常: {task_type}, 错误: {e}")
            self._update_schedule_status(task_type, False)
    
    def _update_schedule_status(self, task_type: str, success: bool):
        """更新调度状态"""
        try:
            with self._get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE rule_maintenance_schedules 
                    SET last_run = ?, run_count = run_count + 1,
                        success_count = success_count + ?, failure_count = failure_count + ?
                    WHERE task_type = ? AND is_active = 1
                ''', (time.time(), 1 if success else 0, 0 if success else 1, task_type))
                conn.commit()
        except Exception as e:
            logger.error(f"[规则库调度器] 更新调度状态失败: {e}")
    
    def run_task_now(self, task_type: str, params: Dict = None) -> Dict:
        """立即运行任务"""
        if params is None:
            params = {}
        
        try:
            from ai_engines.ai_employee_manager import AIEmployeeManager
            
            manager = AIEmployeeManager()
            
            task_data = {
                "task_type": task_type,
                **params
            }
            
            result = manager.auto_assign_task(task_data)
            
            if result.get("success", False):
                self._update_schedule_status(task_type, True)
            
            return result
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_status(self) -> Dict:
        """获取调度器状态"""
        return {
            "running": self._running,
            "scheduled_tasks": len(self._scheduled_tasks),
            "current_time": datetime.now().isoformat()
        }


_scheduler_instance = None


def get_scheduler() -> RuleBaseAutoScheduler:
    """获取调度器单例"""
    global _scheduler_instance
    if _scheduler_instance is None:
        _scheduler_instance = RuleBaseAutoScheduler()
    return _scheduler_instance


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    scheduler = get_scheduler()
    
    print("规则库自动调度器测试")
    print(f"调度器状态: {scheduler.get_status()}")
    
    print("\n列出调度任务:")
    result = scheduler.list_schedules()
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    print("\n启动调度器:")
    result = scheduler.start()
    print(f"启动结果: {result}")
    
    print("\n立即运行任务:")
    result = scheduler.run_task_now("expand_rules", {"source_type": "all", "target_count": 20})
    print(f"执行结果: {result}")
    
    print("\n等待5秒...")
    time.sleep(5)
    
    print("\n停止调度器:")
    result = scheduler.stop()
    print(f"停止结果: {result}")