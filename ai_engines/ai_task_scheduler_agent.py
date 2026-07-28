#!/usr/bin/env python3
"""AI智能任务调度Agent"""

import os
import re
import logging
import json
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Any
from ai_engines.ai_employee_system import AIEmployee

logger = logging.getLogger(__name__)

class AITaskSchedulerAgent(AIEmployee):
    """AI任务调度Agent"""
    
    def __init__(self, employee_id: str, name: str = "AI任务调度专家"):
        super().__init__(employee_id, name, 'task_scheduler', 7)
        self.skills = [
            '任务调度', '定时任务', '任务队列',
            '任务分配', '任务优先级', '任务监控',
            '任务重试', '任务取消', '任务统计'
        ]
        self.tasks = []
        self.task_history = []
        self.total_tasks = 0
        self.completed_tasks = 0
        self.failed_tasks = 0
        self._running = False
        self._scheduler_thread = None
    
    def add_task(self, task_name: str, task_function, schedule_type: str = 'immediate', 
                interval: int = 0, cron_expression: str = "", 
                priority: str = 'medium') -> Dict[str, Any]:
        """添加任务"""
        task = {
            'id': f'task_{datetime.now().timestamp()}',
            'name': task_name,
            'function': task_function,
            'schedule_type': schedule_type,
            'interval': interval,
            'cron_expression': cron_expression,
            'priority': priority,
            'status': 'pending',
            'created_at': datetime.now().isoformat(),
            'next_run_time': self._calculate_next_run_time(schedule_type, interval)
        }
        
        self.tasks.append(task)
        self.total_tasks += 1
        
        if schedule_type == 'immediate':
            self._execute_task(task)
        
        return task
    
    def _calculate_next_run_time(self, schedule_type: str, interval: int) -> str:
        """计算下次运行时间"""
        now = datetime.now()
        
        if schedule_type == 'immediate':
            return now.isoformat()
        elif schedule_type == 'interval':
            return (now + timedelta(seconds=interval)).isoformat()
        elif schedule_type == 'daily':
            return (now + timedelta(days=1)).isoformat()
        elif schedule_type == 'hourly':
            return (now + timedelta(hours=1)).isoformat()
        else:
            return now.isoformat()
    
    def _execute_task(self, task: Dict):
        """执行任务"""
        task['status'] = 'running'
        
        try:
            result = task['function']()
            
            task['status'] = 'completed'
            task['result'] = result
            task['completed_at'] = datetime.now().isoformat()
            self.completed_tasks += 1
            
            logger.info(f"任务完成: {task['name']}")
        except Exception as e:
            task['status'] = 'failed'
            task['error'] = str(e)
            task['completed_at'] = datetime.now().isoformat()
            self.failed_tasks += 1
            
            logger.error(f"任务失败: {task['name']} - {e}")
        
        self.task_history.append(task.copy())
    
    def schedule_tasks(self):
        """调度任务"""
        self._running = True
        
        def scheduler_loop():
            while self._running:
                now = datetime.now()
                
                for task in self.tasks:
                    if task['status'] == 'pending':
                        next_run = datetime.fromisoformat(task['next_run_time'])
                        if now >= next_run:
                            self._execute_task(task)
                
                time.sleep(1)
        
        self._scheduler_thread = threading.Thread(target=scheduler_loop, daemon=True)
        self._scheduler_thread.start()
    
    def stop_scheduler(self):
        """停止调度器"""
        self._running = False
        if self._scheduler_thread:
            self._scheduler_thread.join()
    
    def get_pending_tasks(self) -> List[Dict]:
        """获取待执行任务"""
        return [t for t in self.tasks if t['status'] == 'pending']
    
    def get_running_tasks(self) -> List[Dict]:
        """获取运行中任务"""
        return [t for t in self.tasks if t['status'] == 'running']
    
    def get_completed_tasks(self) -> List[Dict]:
        """获取已完成任务"""
        return [t for t in self.task_history if t['status'] == 'completed']
    
    def cancel_task(self, task_id: str) -> bool:
        """取消任务"""
        for task in self.tasks:
            if task['id'] == task_id and task['status'] == 'pending':
                task['status'] = 'cancelled'
                return True
        return False
    
    def retry_task(self, task_id: str) -> bool:
        """重试任务"""
        for task in self.task_history:
            if task['id'] == task_id and task['status'] == 'failed':
                new_task = task.copy()
                new_task['id'] = f'task_{datetime.now().timestamp()}'
                new_task['status'] = 'pending'
                new_task['created_at'] = datetime.now().isoformat()
                new_task['next_run_time'] = datetime.now().isoformat()
                self.tasks.append(new_task)
                return True
        return False
    
    def get_stats(self) -> Dict:
        """获取调度统计"""
        return {
            'total_tasks': self.total_tasks,
            'completed_tasks': self.completed_tasks,
            'failed_tasks': self.failed_tasks,
            'pending_tasks': len(self.get_pending_tasks()),
            'running_tasks': len(self.get_running_tasks()),
            'success_rate': (self.completed_tasks / self.total_tasks) * 100 if self.total_tasks > 0 else 0,
            'recent_tasks': self.task_history[-10:]
        }

task_scheduler_agent = AITaskSchedulerAgent('ai_task_scheduler_001')
