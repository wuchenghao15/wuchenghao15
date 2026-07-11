# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""线程和进程管理API - 增强版"""
import os
import sys
import time
import uuid
import json
import signal
import subprocess
import threading
import multiprocessing
import enum
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
from threading import Thread, Lock
from multiprocessing import Process
from flask import Blueprint, jsonify, request
import psutil

thread_process_manager_api_bp = Blueprint('thread_process_manager_api', __name__)


class TaskStatus(enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ThreadManager:
    def __init__(self, max_workers: int = 10):
        self.thread_pool = ThreadPoolExecutor(max_workers=max_workers)
        self.tasks = {}
        self.task_lock = Lock()
        self.max_workers = max_workers
        self._update_config()
        
        self.monitor_thread = Thread(target=self._monitor_threads, daemon=True)
        self.monitor_thread.start()

    def _update_config(self):
        """更新配置"""
        self.config = {
            'max_workers': self.max_workers,
            'queue_timeout': 300,
            'keep_alive': 60,
            'shutdown_timeout': 30,
            'max_retries': 3
        }

    def submit_task(self, func, *args, task_id=None, callback=None, **kwargs) -> str:
        """提交任务到线程池"""
        if task_id is None:
            task_id = f"task_{uuid.uuid4().hex[:8]}"
        
        future = self.thread_pool.submit(func, *args, **kwargs)
        
        with self.task_lock:
            self.tasks[task_id] = {
                'task_id': task_id,
                'status': 'running',
                'future': future,
                'callback': callback,
                'submitted_at': time.time(),
                'result': None,
                'error': None
            }
        
        future.add_done_callback(lambda f, tid=task_id: self._handle_completion(tid, f))
        
        return task_id

    def _handle_completion(self, task_id, future):
        """处理任务完成"""
        with self.task_lock:
            if task_id in self.tasks:
                try:
                    result = future.result()
                    self.tasks[task_id]['status'] = 'completed'
                    self.tasks[task_id]['result'] = result
                    
                    if self.tasks[task_id]['callback']:
                        self.tasks[task_id]['callback'](task_id, result)
                except Exception as e:
                    self.tasks[task_id]['status'] = 'failed'
                    self.tasks[task_id]['error'] = str(e)
                    self.tasks[task_id]['result'] = None

    def get_task_status(self, task_id: str) -> dict:
        """获取任务状态"""
        with self.task_lock:
            if task_id in self.tasks:
                task = self.tasks[task_id]
                return {
                    'task_id': task['task_id'],
                    'status': task['status'],
                    'submitted_at': task['submitted_at'],
                    'result': task.get('result'),
                    'error': task.get('error')
                }
            return {'error': '任务不存在'}

    def cancel_task(self, task_id: str) -> bool:
        """取消任务"""
        with self.task_lock:
            if task_id in self.tasks:
                future = self.tasks[task_id]['future']
                cancelled = future.cancel()
                if cancelled:
                    self.tasks[task_id]['status'] = 'cancelled'
                return cancelled
            return False

    def list_tasks(self) -> list:
        """列出所有任务"""
        with self.task_lock:
            return [{
                'task_id': task['task_id'],
                'status': task['status'],
                'submitted_at': task['submitted_at']
            } for task in self.tasks.values()]

    def shutdown(self, wait: bool = True):
        """关闭线程池"""
        self.thread_pool.shutdown(wait=wait)
        with self.task_lock:
            self.tasks.clear()

    def _monitor_threads(self):
        """监控线程状态"""
        while True:
            time.sleep(10)
            with self.task_lock:
                completed_tasks = [tid for tid, task in self.tasks.items() 
                                  if task['status'] in ['completed', 'failed', 'cancelled']]
                for tid in completed_tasks:
                    if time.time() - self.tasks[tid]['submitted_at'] > 300:
                        del self.tasks[tid]

    def get_thread_info(self) -> dict:
        """获取线程信息"""
        threads = []
        for thread_id in threading.enumerate():
            threads.append({
                'name': thread_id.name,
                'ident': thread_id.ident,
                'is_alive': thread_id.is_alive(),
                'daemon': thread_id.daemon
            })
        
        return {
            'total_threads': len(threads),
            'active_threads': sum(1 for t in threads if t['is_alive']),
            'daemon_threads': sum(1 for t in threads if t['daemon']),
            'threads': threads
        }

    def get_pool_stats(self) -> dict:
        """获取线程池统计信息"""
        return {
            'max_workers': self.max_workers,
            'active_tasks': sum(1 for t in self.tasks.values() if t['status'] == 'running'),
            'pending_tasks': sum(1 for t in self.tasks.values() if t['status'] == 'pending'),
            'completed_tasks': sum(1 for t in self.tasks.values() if t['status'] == 'completed'),
            'failed_tasks': sum(1 for t in self.tasks.values() if t['status'] == 'failed')
        }


class ProcessManager:
    def __init__(self):
        self.processes = {}
        self.process_groups = {}
        self.process_lock = Lock()
        
        self.monitor_thread = Thread(target=self._monitor_processes, daemon=True)
        self.monitor_thread.start()

    def create_process(self, target, args=(), name=None, daemon=False) -> str:
        """创建进程"""
        process_id = f"proc_{uuid.uuid4().hex[:8]}"
        
        process = Process(target=target, args=args, name=name, daemon=daemon)
        process.start()
        
        with self.process_lock:
            self.processes[process_id] = {
                'process_id': process_id,
                'name': name or f"Process-{process_id}",
                'pid': process.pid,
                'process': process,
                'status': 'running',
                'created_at': time.time()
            }
        
        return process_id

    def get_process_status(self, process_id: str) -> dict:
        """获取进程状态"""
        with self.process_lock:
            if process_id in self.processes:
                proc_info = self.processes[process_id]
                proc_info['status'] = 'running' if proc_info['process'].is_alive() else 'terminated'
                return proc_info
            return {'error': '进程不存在'}

    def terminate_process(self, process_id: str) -> bool:
        """终止进程"""
        with self.process_lock:
            if process_id in self.processes:
                proc_info = self.processes[process_id]
                try:
                    proc_info['process'].terminate()
                    proc_info['process'].join(timeout=5)
                    proc_info['status'] = 'terminated'
                    return True
                except Exception as e:
                    return False
            return False

    def kill_process(self, process_id: str) -> bool:
        """强制杀死进程"""
        with self.process_lock:
            if process_id in self.processes:
                proc_info = self.processes[process_id]
                try:
                    proc_info['process'].kill()
                    proc_info['status'] = 'killed'
                    return True
                except Exception as e:
                    return False
            return False

    def list_processes(self) -> list:
        """列出所有进程"""
        with self.process_lock:
            return [{
                'process_id': proc['process_id'],
                'name': proc['name'],
                'pid': proc['pid'],
                'status': 'running' if proc['process'].is_alive() else 'terminated',
                'created_at': proc['created_at']
            } for proc in self.processes.values()]

    def create_process_group(self, name: str) -> str:
        """创建进程组"""
        group_id = f"group_{uuid.uuid4().hex[:8]}"
        
        with self.process_lock:
            self.process_groups[group_id] = {
                'group_id': group_id,
                'name': name,
                'process_ids': [],
                'created_at': time.time()
            }
        
        return group_id

    def add_to_group(self, group_id: str, process_id: str) -> bool:
        """将进程添加到组"""
        with self.process_lock:
            if group_id in self.process_groups and process_id in self.processes:
                if process_id not in self.process_groups[group_id]['process_ids']:
                    self.process_groups[group_id]['process_ids'].append(process_id)
                    return True
            return False

    def terminate_group(self, group_id: str) -> bool:
        """终止进程组"""
        with self.process_lock:
            if group_id in self.process_groups:
                for process_id in self.process_groups[group_id]['process_ids']:
                    self.terminate_process(process_id)
                return True
            return False

    def list_groups(self) -> list:
        """列出所有进程组"""
        with self.process_lock:
            return [{
                'group_id': group['group_id'],
                'name': group['name'],
                'process_count': len(group['process_ids']),
                'created_at': group['created_at']
            } for group in self.process_groups.values()]

    def _monitor_processes(self):
        """监控进程状态"""
        while True:
            time.sleep(5)
            with self.process_lock:
                for proc_info in self.processes.values():
                    if not proc_info['process'].is_alive() and proc_info['status'] == 'running':
                        proc_info['status'] = 'terminated'

    def get_system_process_info(self) -> dict:
        """获取系统进程信息"""
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'status', 'cpu_percent', 'memory_percent']):
            try:
                processes.append({
                    'pid': proc.info['pid'],
                    'name': proc.info['name'],
                    'status': proc.info['status'],
                    'cpu_percent': proc.info['cpu_percent'],
                    'memory_percent': proc.info['memory_percent']
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        return {
            'total_processes': len(processes),
            'running_processes': sum(1 for p in processes if p['status'] == 'running'),
            'processes': processes[:50]
        }


thread_manager = ThreadManager()
process_manager = ProcessManager()


@thread_process_manager_api_bp.route('/', methods=['GET'])
def index():
    return jsonify({
        'message': '线程和进程管理API',
        'endpoints': {
            'threads': '/threads',
            'tasks': '/tasks',
            'processes': '/processes',
            'process_groups': '/process_groups'
        }
    })


@thread_process_manager_api_bp.route('/threads', methods=['GET'])
def get_threads():
    info = thread_manager.get_thread_info()
    return jsonify(info)


@thread_process_manager_api_bp.route('/tasks', methods=['GET'])
def get_tasks():
    tasks = thread_manager.list_tasks()
    return jsonify({'tasks': tasks})


@thread_process_manager_api_bp.route('/tasks/<task_id>', methods=['GET'])
def get_task(task_id):
    status = thread_manager.get_task_status(task_id)
    return jsonify(status)


@thread_process_manager_api_bp.route('/tasks', methods=['POST'])
def submit_task():
    data = request.get_json()
    func_name = data.get('function')
    args = data.get('args', [])
    kwargs = data.get('kwargs', {})
    
    task_id = thread_manager.submit_task(eval(func_name), *args, **kwargs)
    return jsonify({'task_id': task_id, 'message': '任务已提交'})


@thread_process_manager_api_bp.route('/tasks/<task_id>/cancel', methods=['POST'])
def cancel_task(task_id):
    cancelled = thread_manager.cancel_task(task_id)
    return jsonify({'cancelled': cancelled})


@thread_process_manager_api_bp.route('/processes', methods=['GET'])
def get_processes():
    processes = process_manager.list_processes()
    return jsonify({'processes': processes})


@thread_process_manager_api_bp.route('/processes/system', methods=['GET'])
def get_system_processes():
    info = process_manager.get_system_process_info()
    return jsonify(info)


@thread_process_manager_api_bp.route('/processes/<process_id>/terminate', methods=['POST'])
def terminate_process(process_id):
    result = process_manager.terminate_process(process_id)
    return jsonify({'success': result})


@thread_process_manager_api_bp.route('/process_groups', methods=['GET'])
def get_process_groups():
    groups = process_manager.list_groups()
    return jsonify({'groups': groups})


@thread_process_manager_api_bp.route('/process_groups', methods=['POST'])
def create_process_group():
    data = request.get_json()
    name = data.get('name', 'unnamed')
    group_id = process_manager.create_process_group(name)
    return jsonify({'group_id': group_id, 'message': '进程组已创建'})


@thread_process_manager_api_bp.route('/stats', methods=['GET'])
def get_stats():
    thread_stats = thread_manager.get_pool_stats()
    process_count = len(process_manager.list_processes())
    
    return jsonify({
        'thread_pool': thread_stats,
        'process_count': process_count
    })
