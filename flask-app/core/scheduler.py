# -*- coding: utf-8 -*-
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Task Scheduler Module - Cron-like task scheduling system
"""

import time
import threading
import schedule
from typing import Dict, Any, Callable, Optional
from datetime import datetime
import sys

class ScheduledTask:
    """Represents a scheduled task"""
    
    def __init__(self, task_id: str, func: Callable, schedule_type: str, *args, **kwargs):
        self.task_id = task_id
        self.func = func
        self.schedule_type = schedule_type
        self.args = args
        self.kwargs = kwargs
        self.enabled = True
        self.last_run = None
        self.next_run = None
        self.run_count = 0
    
    def run(self):
        """Execute the task"""
        if self.enabled:
            self.last_run = datetime.now()
            self.run_count += 1
            try:
                return self.func(*self.args, **self.kwargs)
            except Exception:
                return None

class Scheduler:
    """Task scheduler with cron-like scheduling"""
    
    def __init__(self):
        self.tasks: Dict[str, ScheduledTask] = {}
        self._thread: Optional[threading.Thread] = None
        self._running = False
    
    def add_task(self, task_id: str, func: Callable, schedule_type: str, *args, **kwargs):
        """Add a scheduled task"""
        task = ScheduledTask(task_id, func, schedule_type, *args, **kwargs)
        self.tasks[task_id] = task
        
        if schedule_type == "interval":
            minutes = kwargs.get("minutes", 1)
            schedule.every(minutes).minutes.do(self._run_task, task_id)
        elif schedule_type == "hourly":
            schedule.every().hour.do(self._run_task, task_id)
        elif schedule_type == "daily":
            at_time = kwargs.get("at", "00:00")
            schedule.every().day.at(at_time).do(self._run_task, task_id)
        elif schedule_type == "weekly":
            day_of_week = kwargs.get("day", "monday")
            at_time = kwargs.get("at", "00:00")
            getattr(schedule.every(), day_of_week).at(at_time).do(self._run_task, task_id)
        elif schedule_type == "cron":
            cron_expr = kwargs.get("expr", "")
            self._parse_cron(task_id, cron_expr)
    
    def _parse_cron(self, task_id: str, cron_expr: str):
        """Parse cron expression"""
        parts = cron_expr.split()
        if len(parts) == 5:
            minute, hour, day, month, dow = parts
            
            if minute != "*":
                schedule.every().minute.at(f":{minute}").do(self._run_task, task_id)
            elif hour != "*":
                schedule.every().hour.at(f"{hour}:00").do(self._run_task, task_id)
    
    def _run_task(self, task_id: str):
        """Wrapper to run a task"""
        task = self.tasks.get(task_id)
        if task:
            task.run()
    
    def start(self):
        """Start the scheduler"""
        self._running = True
        self._thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self._thread.start()
    
    def _run_scheduler(self):
        """Main scheduler loop"""
        while self._running:
            schedule.run_pending()
            time.sleep(1)
    
    def stop(self):
        """Stop the scheduler"""
        self._running = False
        if self._thread:
            self._thread.join()
    
    def disable_task(self, task_id: str):
        """Disable a task"""
        if task_id in self.tasks:
            self.tasks[task_id].enabled = False
    
    def enable_task(self, task_id: str):
        """Enable a task"""
        if task_id in self.tasks:
            self.tasks[task_id].enabled = True
    
    def remove_task(self, task_id: str):
        """Remove a task"""
        if task_id in self.tasks:
            del self.tasks[task_id]
            schedule.clear()
    
    def get_task_info(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get task information"""
        task = self.tasks.get(task_id)
        if task:
            return {
                "task_id": task.task_id,
                "schedule_type": task.schedule_type,
                "enabled": task.enabled,
                "last_run": task.last_run.isoformat() if task.last_run else None,
                "run_count": task.run_count
            }
        return None
    
    def get_all_tasks(self) -> Dict[str, Dict[str, Any]]:
        """Get all tasks"""
        return {tid: self.get_task_info(tid) for tid in self.tasks}
    
    def run_now(self, task_id: str):
        """Run a task immediately"""
        task = self.tasks.get(task_id)
        if task:
            return task.run()

# Global scheduler instance
scheduler = Scheduler()
