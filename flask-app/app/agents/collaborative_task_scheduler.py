# -*- coding: utf-8 -*-
"""
协作任务调度器
负责协调Agent和AI员工之间的任务分配和执行
"""

import json
import logging
import threading
import time
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional, Callable

logger = logging.getLogger(__name__)


class CollaborativeTaskScheduler:
    """协作任务调度器"""
    
    def __init__(self):
        self._lock = threading.Lock()
        self._task_queue = []
        self._active_tasks = {}
        self._completed_tasks = {}
        self._task_counter = 0
        self._running = False
        self._scheduler_thread = None
        self._max_concurrent_tasks = 10
        
        self._task_routing = {
            'code_fix': ['ai_employee', 'agent'],
            'data_analysis': ['ai_employee', 'agent'],
            'security_scan': ['ai_employee'],
            'performance': ['ai_employee'],
            'quality_assurance': ['ai_employee'],
            'knowledge_management': ['ai_employee'],
            'task_coordination': ['agent'],
            'system_maintenance': ['ai_employee', 'agent'],
            'general': ['agent', 'ai_employee']
        }
        
        self._execution_stats = {
            'total_tasks': 0,
            'completed_tasks': 0,
            'failed_tasks': 0,
            'avg_execution_time': 0,
            'task_type_distribution': {}
        }
    
    def start(self):
        """启动调度器"""
        if self._running:
            return
        
        self._running = True
        self._scheduler_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self._scheduler_thread.start()
        logger.info("[协作调度器] 协作任务调度器已启动")
    
    def stop(self):
        """停止调度器"""
        self._running = False
        if self._scheduler_thread:
            self._scheduler_thread.join(timeout=5)
        logger.info("[协作调度器] 协作任务调度器已停止")
    
    def _scheduler_loop(self):
        """调度循环"""
        while self._running:
            try:
                self._process_task_queue()
                self._cleanup_completed_tasks()
                time.sleep(0.5)
            except Exception as e:
                logger.error(f"调度循环异常: {e}")
                time.sleep(1)
    
    def submit_task(self, task_type: str, task_data: Dict = None, 
                     priority: int = 0, callback: Callable = None) -> str:
        """提交协作任务"""
        task_data = task_data or {}
        
        task = {
            'task_id': f'collab_task_{self._task_counter:06d}',
            'task_type': task_type,
            'task_data': task_data,
            'priority': priority,
            'callback': callback,
            'status': 'queued',
            'created_at': datetime.now().isoformat(),
            'assigned_to': None,
            'execution_start': None,
            'execution_end': None,
            'result': None,
            'error': None
        }
        
        self._task_counter += 1
        
        with self._lock:
            self._task_queue.append(task)
            self._task_queue.sort(key=lambda x: (-x['priority'], x['created_at']))
            self._execution_stats['total_tasks'] += 1
            self._execution_stats['task_type_distribution'][task_type] = \
                self._execution_stats['task_type_distribution'].get(task_type, 0) + 1
        
        logger.info(f"[协作调度器] 任务已提交: {task['task_id']} ({task_type})")
        
        return task['task_id']
    
    def _process_task_queue(self):
        """处理任务队列"""
        with self._lock:
            active_count = sum(1 for t in self._active_tasks.values() if t['status'] == 'executing')
            
            while self._task_queue and active_count < self._max_concurrent_tasks:
                task = self._task_queue.pop(0)
                self._assign_task(task)
                active_count += 1
    
    def _assign_task(self, task: Dict):
        """分配任务"""
        task_type = task['task_type']
        available_routes = self._task_routing.get(task_type, ['agent', 'ai_employee'])
        
        try:
            from app.agents.agent_ai_employee_integration import get_integration
            
            integration = get_integration()
            
            route = available_routes[0]
            
            if route == 'ai_employee':
                result = integration.dispatch_task_to_employee(
                    'collaborative_scheduler',
                    task,
                    self._get_employee_template(task_type)
                )
                
                if result.get('success'):
                    task['status'] = 'executing'
                    task['assigned_to'] = 'ai_employee'
                    task['session_id'] = result.get('session_id')
                    task['employee_id'] = result.get('employee_id')
                    task['execution_start'] = datetime.now().isoformat()
                else:
                    if len(available_routes) > 1:
                        route = available_routes[1]
                    else:
                        task['status'] = 'failed'
                        task['error'] = result.get('error', '分配失败')
            
            if route == 'agent':
                result = integration.delegate_task_to_agent(
                    'collaborative_scheduler',
                    task
                )
                
                if result.get('success'):
                    task['status'] = 'executing'
                    task['assigned_to'] = 'agent'
                    task['execution_start'] = datetime.now().isoformat()
                else:
                    task['status'] = 'failed'
                    task['error'] = result.get('error', '分配失败')
            
            with self._lock:
                self._active_tasks[task['task_id']] = task
            
            logger.info(f"[协作调度器] 任务已分配: {task['task_id']} -> {task['assigned_to']}")
        
        except Exception as e:
            logger.error(f"[协作调度器] 任务分配失败: {e}")
            task['status'] = 'failed'
            task['error'] = str(e)
            with self._lock:
                self._active_tasks[task['task_id']] = task
    
    def _get_employee_template(self, task_type: str) -> str:
        """根据任务类型获取员工模板"""
        mapping = {
            'code_fix': 'code_fixer',
            'data_analysis': 'data_analyzer',
            'security_scan': 'security_guard',
            'performance': 'performance_optimizer',
            'quality_assurance': 'qa_validator',
            'knowledge_management': 'knowledge_manager',
            'system_maintenance': 'system_maintenance',
            'general': 'code_fixer'
        }
        return mapping.get(task_type, 'code_fixer')
    
    def _cleanup_completed_tasks(self):
        """清理已完成的任务"""
        completed_ids = []
        
        with self._lock:
            for task_id, task in self._active_tasks.items():
                if task['status'] in ['completed', 'failed']:
                    completed_ids.append(task_id)
                    self._completed_tasks[task_id] = task
        
        for task_id in completed_ids:
            with self._lock:
                del self._active_tasks[task_id]
            
            logger.info(f"[协作调度器] 任务已清理: {task_id}")
    
    def complete_task(self, task_id: str, result: Dict = None, error: str = None):
        """完成任务"""
        with self._lock:
            task = self._active_tasks.get(task_id)
        
        if not task:
            logger.warning(f"[协作调度器] 任务不存在: {task_id}")
            return
        
        if error:
            task['status'] = 'failed'
            task['error'] = error
            self._execution_stats['failed_tasks'] += 1
        else:
            task['status'] = 'completed'
            task['result'] = result
            self._execution_stats['completed_tasks'] += 1
        
        task['execution_end'] = datetime.now().isoformat()
        
        if task['callback']:
            try:
                task['callback'](task)
            except Exception as e:
                logger.error(f"[协作调度器] 回调执行失败: {e}")
        
        with self._lock:
            self._active_tasks[task_id] = task
        
        logger.info(f"[协作调度器] 任务完成: {task_id} ({task['status']})")
    
    def get_task_status(self, task_id: str) -> Dict:
        """获取任务状态"""
        with self._lock:
            task = self._active_tasks.get(task_id) or self._completed_tasks.get(task_id)
        
        if not task:
            return {'success': False, 'error': '任务不存在'}
        
        return {
            'success': True,
            'task': task
        }
    
    def get_active_tasks(self) -> Dict:
        """获取所有活跃任务"""
        with self._lock:
            tasks = list(self._active_tasks.values())
        
        return {
            'success': True,
            'tasks': tasks,
            'total': len(tasks)
        }
    
    def get_completed_tasks(self, limit: int = 100) -> Dict:
        """获取已完成任务"""
        with self._lock:
            tasks = list(self._completed_tasks.values())[-limit:]
        
        return {
            'success': True,
            'tasks': tasks,
            'total': len(tasks)
        }
    
    def get_scheduler_stats(self) -> Dict:
        """获取调度器统计信息"""
        with self._lock:
            stats = dict(self._execution_stats)
            stats['active_tasks'] = len(self._active_tasks)
            stats['queued_tasks'] = len(self._task_queue)
            stats['completed_tasks_count'] = len(self._completed_tasks)
            
            if stats['completed_tasks'] > 0:
                total_time = 0
                count = 0
                for task in self._completed_tasks.values():
                    if task['execution_start'] and task['execution_end']:
                        start = datetime.fromisoformat(task['execution_start'])
                        end = datetime.fromisoformat(task['execution_end'])
                        total_time += (end - start).total_seconds()
                        count += 1
                if count > 0:
                    stats['avg_execution_time'] = round(total_time / count, 2)
        
        return {
            'success': True,
            'stats': stats
        }
    
    def cancel_task(self, task_id: str) -> Dict:
        """取消任务"""
        with self._lock:
            if task_id in self._task_queue:
                task = self._task_queue.pop(self._task_queue.index(next(t for t in self._task_queue if t['task_id'] == task_id)))
                task['status'] = 'cancelled'
                self._completed_tasks[task_id] = task
                return {'success': True, 'message': '任务已取消'}
            
            elif task_id in self._active_tasks:
                task = self._active_tasks[task_id]
                task['status'] = 'cancelled'
                task['execution_end'] = datetime.now().isoformat()
                self._completed_tasks[task_id] = task
                del self._active_tasks[task_id]
                return {'success': True, 'message': '任务已取消'}
        
        return {'success': False, 'error': '任务不存在'}


_scheduler_instance = None

def get_task_scheduler():
    """获取协作任务调度器实例"""
    global _scheduler_instance
    if _scheduler_instance is None:
        _scheduler_instance = CollaborativeTaskScheduler()
    return _scheduler_instance

def init_task_scheduler():
    """初始化协作任务调度器"""
    scheduler = get_task_scheduler()
    scheduler.start()
    logger.info("[协作调度器] 协作任务调度器初始化完成")
    return scheduler