# -*- coding: utf-8 -*-
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
任务中心系统
Task Center System

特性:
- 任务认领和执行
"""

import os
import sys
import json
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from enum import Enum
from collections import defaultdict
import threading
import logging

logger = logging.getLogger('task_center')


class TaskPriority(Enum):
    """任务优先级"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class TaskStatus(Enum):
    """任务状态"""
    PENDING = "pending"           # 待处理
    ASSIGNED = "assigned"         # 已分配
    CLAIMED = "claimed"           # 已认领
    PROCESSING = "processing"     # 处理中
    COMPLETED = "completed"       # 已完成
    FAILED = "failed"             # 失败
    CANCELLED = "cancelled"       # 已取消


class TaskType(Enum):
    """任务类型"""
    DATA_ANALYSIS = "data_analysis"
    BACKUP = "backup"
    RECOVERY = "recovery"
    MAINTENANCE = "maintenance"
    HEALTH_CHECK = "health_check"
    PERFORMANCE_ANALYSIS = "performance_analysis"
    ANOMALY_DETECTION = "anomaly_detection"
    REPORT_GENERATION = "report_generation"
    SECURITY_SCAN = "security_scan"
    INTEGRATION = "integration"
    CUSTOM = "custom"


class Task:
    """任务定义"""
    
    def __init__(self, task_id: str, name: str, task_type: TaskType):
        self.id = task_id
        self.name = name
        self.type = task_type
        self.description = ""
        self.priority = TaskPriority.NORMAL
        self.status = TaskStatus.PENDING
        
        self.inputs = {}
        self.outputs = {}
        
        self.assigned_ai = None
        self.claimed_by = None
        
        self.created_at = datetime.now().isoformat()
        self.assigned_at = None
        self.claimed_at = None
        self.started_at = None
        self.completed_at = None
        
        self.execution_time = 0
        self.error_message = None
        
        self.required_skills = []
        self.preferred_ais = []
        
        self.metadata = {}
        self.tags = []
    
    def assign(self, ai_id: str):
        """分配任务"""
        self.assigned_ai = ai_id
        self.status = TaskStatus.ASSIGNED
        self.assigned_at = datetime.now().isoformat()
    
    def claim(self, ai_id: str):
        """认领任务"""
        self.claimed_by = ai_id
        self.status = TaskStatus.CLAIMED
        self.claimed_at = datetime.now().isoformat()
    
    def start(self):
        """开始执行"""
        self.status = TaskStatus.PROCESSING
        self.started_at = datetime.now().isoformat()
    
    def complete(self, outputs: Dict = None):
        """完成任务"""
        self.status = TaskStatus.COMPLETED
        self.completed_at = datetime.now().isoformat()
        if outputs:
            self.outputs = outputs
        
        if self.started_at:
            start = datetime.fromisoformat(self.started_at)
            end = datetime.fromisoformat(self.completed_at)
            self.execution_time = (end - start).total_seconds()
    
    def fail(self, error_message: str):
        """任务失败"""
        self.status = TaskStatus.FAILED
        self.completed_at = datetime.now().isoformat()
        self.error_message = error_message
        
        if self.started_at:
            start = datetime.fromisoformat(self.started_at)
            end = datetime.fromisoformat(self.completed_at)
            self.execution_time = (end - start).total_seconds()
    
    def cancel(self):
        """取消任务"""
        self.status = TaskStatus.CANCELLED
        self.completed_at = datetime.now().isoformat()
    
    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'name': self.name,
            'type': self.type.value,
            'description': self.description,
            'priority': self.priority.value,
            'status': self.status.value,
            'inputs': self.inputs,
            'outputs': self.outputs,
            'assigned_ai': self.assigned_ai,
            'claimed_by': self.claimed_by,
            'created_at': self.created_at,
            'assigned_at': self.assigned_at,
            'claimed_at': self.claimed_at,
            'started_at': self.started_at,
            'completed_at': self.completed_at,
            'execution_time': self.execution_time,
            'error_message': self.error_message,
            'required_skills': self.required_skills,
            'preferred_ais': self.preferred_ais,
            'metadata': self.metadata,
            'tags': self.tags
        }


class AIWorker:
    """AI工作者"""
    
    def __init__(self, ai_id: str, name: str):
        self.id = ai_id
        self.name = name
        self.status = "idle"  # idle, busy, offline
        self.specialties = []
        self.skills = []
        self.current_task = None
        self.task_history = []
        
        self.created_at = datetime.now().isoformat()
        self.last_active_at = datetime.now().isoformat()
        
        self.total_tasks = 0
        self.completed_tasks = 0
        self.failed_tasks = 0
        self.average_response_time = 0
        
        self.metadata = {}
    
    def is_available(self) -> bool:
        """检查是否可用"""
        return self.status == "idle"
    
    def assign_task(self, task_id: str):
        """分配任务"""
        self.current_task = task_id
        self.status = "busy"
        self.last_active_at = datetime.now().isoformat()
    
    def complete_task(self, success: bool):
        """完成任务"""
        self.total_tasks += 1
        if success:
            self.completed_tasks += 1
        else:
            self.failed_tasks += 1
        
        self.current_task = None
        self.status = "idle"
        self.last_active_at = datetime.now().isoformat()
    
    def add_skill(self, skill_id: str):
        """添加技能"""
        if skill_id not in self.skills:
            self.skills.append(skill_id)
    
    def has_skill(self, skill_id: str) -> bool:
        """检查是否有技能"""
        return skill_id in self.skills
    
    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'name': self.name,
            'status': self.status,
            'specialties': self.specialties,
            'skills': self.skills,
            'current_task': self.current_task,
            'total_tasks': self.total_tasks,
            'completed_tasks': self.completed_tasks,
            'failed_tasks': self.failed_tasks,
            'success_rate': (self.completed_tasks / self.total_tasks * 100) if self.total_tasks > 0 else 0,
            'created_at': self.created_at,
            'last_active_at': self.last_active_at,
            'metadata': self.metadata
        }


class TaskAssignment:
    """任务分配记录"""
    
    def __init__(self, task_id: str, ai_id: str):
        self.id = f"assign_{uuid.uuid4().hex[:12]}"
        self.task_id = task_id
        self.ai_id = ai_id
        self.assigned_at = datetime.now().isoformat()
        self.claimed_at = None
        self.completed_at = None
        self.success = None
        self.score = 0
    
    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'task_id': self.task_id,
            'ai_id': self.ai_id,
            'assigned_at': self.assigned_at,
            'claimed_at': self.claimed_at,
            'completed_at': self.completed_at,
            'success': self.success,
            'score': self.score
        }


class TaskCenter:
    """任务中心"""
    
    def __init__(self, storage_dir: str = None):
        self.storage_dir = storage_dir or os.path.join(
            os.path.dirname(__file__), '..', '..', 'tasks'
        )
        
        self.tasks_dir = os.path.join(self.storage_dir, 'tasks')
        self.workers_dir = os.path.join(self.storage_dir, 'workers')
        self.assignments_dir = os.path.join(self.storage_dir, 'assignments')
        self.metadata_dir = os.path.join(self.storage_dir, '.metadata')
        
        self.tasks_file = os.path.join(self.metadata_dir, 'tasks.json')
        self.workers_file = os.path.join(self.metadata_dir, 'workers.json')
        self.assignments_file = os.path.join(self.metadata_dir, 'assignments.json')
        
        self.tasks = {}
        self.workers = {}
        self.assignments = {}
        
        self.lock = threading.Lock()
        
        self._ensure_directories()
        self._load_data()
        self._register_default_workers()
        
        # AI管家
        self.ai_butler = AIButler(self)
    
    def _ensure_directories(self):
        """确保目录结构存在"""
        directories = [
            self.storage_dir,
            self.tasks_dir,
            self.workers_dir,
            self.assignments_dir,
            self.metadata_dir
        ]
        
        for directory in directories:
            if not os.path.exists(directory):
                os.makedirs(directory, exist_ok=True)
    
    def _load_data(self):
        """加载数据"""
        # 加载任务
        if os.path.exists(self.tasks_file):
            try:
                with open(self.tasks_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for task_id, task_data in data.items():
                        task = Task(task_id, task_data['name'], TaskType(task_data['type']))
                        task.__dict__.update(task_data)
                        task.type = TaskType(task.type)
                        task.priority = TaskPriority(task.priority)
                        task.status = TaskStatus(task.status)
                        self.tasks[task_id] = task
            except Exception as e:
                logger.error(f"加载任务失败: {str(e)}")
        
        # 加载工作者
        if os.path.exists(self.workers_file):
            try:
                with open(self.workers_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for ai_id, worker_data in data.items():
                        worker = AIWorker(ai_id, worker_data['name'])
                        worker.__dict__.update(worker_data)
                        self.workers[ai_id] = worker
            except Exception as e:
                logger.error(f"加载工作者失败: {str(e)}")
        
        # 加载分配记录
        if os.path.exists(self.assignments_file):
            try:
                with open(self.assignments_file, 'r', encoding='utf-8') as f:
                    self.assignments = json.load(f)
            except Exception as e:
                logger.error(f"加载分配记录失败: {str(e)}")
    
    def _save_data(self):
        """保存数据"""
        # 保存任务
        try:
            with open(self.tasks_file, 'w', encoding='utf-8') as f:
                data = {task_id: task.to_dict() for task_id, task in self.tasks.items()}
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"保存任务失败: {str(e)}")
        
        # 保存工作者
        try:
            with open(self.workers_file, 'w', encoding='utf-8') as f:
                data = {ai_id: worker.to_dict() for ai_id, worker in self.workers.items()}
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"保存工作者失败: {str(e)}")
        
        # 保存分配记录
        try:
            with open(self.assignments_file, 'w', encoding='utf-8') as f:
                json.dump(self.assignments, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"保存分配记录失败: {str(e)}")
    
    def _register_default_workers(self):
        """注册默认AI工作者"""
        default_workers = [
            {'id': 'ai_data_analyst', 'name': '数据分析AI', 'specialties': ['data_analysis', 'performance_analysis']},
            {'id': 'ai_backup_specialist', 'name': '备份专家AI', 'specialties': ['backup', 'recovery']},
            {'id': 'ai_maintenance_engineer', 'name': '维护工程师AI', 'specialties': ['maintenance', 'health_check']},
            {'id': 'ai_security_expert', 'name': '安全专家AI', 'specialties': ['security_scan', 'anomaly_detection']},
            {'id': 'ai_report_generator', 'name': '报告生成AI', 'specialties': ['report_generation']},
            {'id': 'ai_integration_master', 'name': '集成大师AI', 'specialties': ['integration']},
        ]
        
        for worker in default_workers:
            if worker['id'] not in self.workers:
                ai_worker = AIWorker(worker['id'], worker['name'])
                ai_worker.specialties = worker['specialties']
                self.workers[worker['id']] = ai_worker
                logger.info(f"注册AI工作者: {worker['name']}")
        
        self._save_data()
    
    def create_task(self, name: str, task_type: TaskType, **kwargs) -> Optional[str]:
        """创建任务"""
        task_id = f"task_{int(time.time())}_{uuid.uuid4().hex[:8]}"
        
        task = Task(task_id, name, task_type)
        
        # 设置可选参数
        if 'description' in kwargs:
            task.description = kwargs['description']
        if 'priority' in kwargs:
            task.priority = kwargs['priority']
        if 'inputs' in kwargs:
            task.inputs = kwargs['inputs']
        if 'required_skills' in kwargs:
            task.required_skills = kwargs['required_skills']
        if 'preferred_ais' in kwargs:
            task.preferred_ais = kwargs['preferred_ais']
        if 'metadata' in kwargs:
            task.metadata = kwargs['metadata']
        if 'tags' in kwargs:
            task.tags = kwargs['tags']
        
        self.tasks[task_id] = task
        self._save_data()
        
        logger.info(f"创建任务: {task_id} -> {name}")
        
        # 自动分配任务
        self.ai_butler.auto_assign_task(task_id)
        
        return task_id
    
    def get_task(self, task_id: str) -> Optional[Task]:
        """获取任务"""
        return self.tasks.get(task_id)
    
    def update_task(self, task_id: str, **kwargs) -> bool:
        """更新任务"""
        if task_id not in self.tasks:
            return False
        
        task = self.tasks[task_id]
        
        if 'name' in kwargs:
            task.name = kwargs['name']
        if 'description' in kwargs:
            task.description = kwargs['description']
        if 'priority' in kwargs:
            task.priority = kwargs['priority']
        if 'inputs' in kwargs:
            task.inputs = kwargs['inputs']
        
        self._save_data()
        logger.info(f"更新任务: {task_id}")
        return True
    
    def delete_task(self, task_id: str) -> bool:
        """删除任务"""
        if task_id not in self.tasks:
            return False
        
        del self.tasks[task_id]
        self._save_data()
        logger.info(f"删除任务: {task_id}")
        return True
    
    def list_tasks(self, status: TaskStatus = None, priority: TaskPriority = None,
                  task_type: TaskType = None) -> List[Dict]:
        """列出任务"""
        results = []
        
        for task in self.tasks.values():
            if status and task.status != status:
                continue
            if priority and task.priority != priority:
                continue
            if task_type and task.type != task_type:
                continue
            
            results.append(task.to_dict())
        
        return sorted(results, key=lambda x: (x['priority'], x['created_at']), reverse=True)
    
    def register_worker(self, ai_id: str, name: str, **kwargs) -> bool:
        """注册AI工作者"""
        if ai_id in self.workers:
            return False
        
        worker = AIWorker(ai_id, name)
        
        if 'specialties' in kwargs:
            worker.specialties = kwargs['specialties']
        if 'skills' in kwargs:
            worker.skills = kwargs['skills']
        if 'metadata' in kwargs:
            worker.metadata = kwargs['metadata']
        
        self.workers[ai_id] = worker
        self._save_data()
        
        logger.info(f"注册AI工作者: {ai_id} -> {name}")
        return True
    
    def get_worker(self, ai_id: str) -> Optional[AIWorker]:
        """获取AI工作者"""
        return self.workers.get(ai_id)
    
    def list_workers(self, status: str = None) -> List[Dict]:
        """列出AI工作者"""
        results = []
        
        for worker in self.workers.values():
            if status and worker.status != status:
                continue
            
            results.append(worker.to_dict())
        
        return sorted(results, key=lambda x: x['name'])
    
    def assign_task(self, task_id: str, ai_id: str) -> bool:
        """分配任务给AI"""
        task = self.get_task(task_id)
        worker = self.get_worker(ai_id)
        
        if not task or not worker:
            return False
        
        if task.status != TaskStatus.PENDING:
            return False
        
        task.assign(ai_id)
        worker.assign_task(task_id)
        
        # 记录分配
        assignment = TaskAssignment(task_id, ai_id)
        self.assignments[assignment.id] = assignment.to_dict()
        
        self._save_data()
        logger.info(f"分配任务: {task_id} -> {ai_id}")
        return True
    
    def claim_task(self, task_id: str, ai_id: str) -> bool:
        """AI认领任务"""
        task = self.get_task(task_id)
        worker = self.get_worker(ai_id)
        
        if not task or not worker:
            return False
        
        if task.status != TaskStatus.ASSIGNED or task.assigned_ai != ai_id:
            return False
        
        task.claim(ai_id)
        
        # 更新分配记录
        for assignment in self.assignments.values():
            if assignment['task_id'] == task_id and assignment['ai_id'] == ai_id:
                assignment['claimed_at'] = datetime.now().isoformat()
                break
        
        self._save_data()
        logger.info(f"认领任务: {task_id} by {ai_id}")
        return True
    
    def start_task(self, task_id: str) -> bool:
        """开始执行任务"""
        task = self.get_task(task_id)
        
        if not task:
            return False
        
        if task.status not in [TaskStatus.CLAIMED, TaskStatus.ASSIGNED]:
            return False
        
        task.start()
        self._save_data()
        logger.info(f"开始任务: {task_id}")
        return True
    
    def complete_task(self, task_id: str, outputs: Dict = None) -> bool:
        """完成任务"""
        task = self.get_task(task_id)
        
        if not task:
            return False
        
        if task.status != TaskStatus.PROCESSING:
            return False
        
        task.complete(outputs)
        
        # 更新工作者统计
        if task.claimed_by:
            worker = self.get_worker(task.claimed_by)
            if worker:
                worker.complete_task(True)
        
        # 更新分配记录
        for assignment in self.assignments.values():
            if assignment['task_id'] == task_id:
                assignment['completed_at'] = datetime.now().isoformat()
                assignment['success'] = True
                break
        
        self._save_data()
        logger.info(f"完成任务: {task_id}")
        return True
    
    def fail_task(self, task_id: str, error_message: str) -> bool:
        """任务失败"""
        task = self.get_task(task_id)
        
        if not task:
            return False
        
        if task.status != TaskStatus.PROCESSING:
            return False
        
        task.fail(error_message)
        
        # 更新工作者统计
        if task.claimed_by:
            worker = self.get_worker(task.claimed_by)
            if worker:
                worker.complete_task(False)
        
        # 更新分配记录
        for assignment in self.assignments.values():
            if assignment['task_id'] == task_id:
                assignment['completed_at'] = datetime.now().isoformat()
                assignment['success'] = False
                break
        
        self._save_data()
        logger.info(f"任务失败: {task_id} - {error_message}")
        return True
    
    def cancel_task(self, task_id: str) -> bool:
        """取消任务"""
        task = self.get_task(task_id)
        
        if not task:
            return False
        
        task.cancel()
        
        # 释放工作者
        if task.claimed_by:
            worker = self.get_worker(task.claimed_by)
            if worker and worker.current_task == task_id:
                worker.current_task = None
                worker.status = "idle"
        
        self._save_data()
        logger.info(f"取消任务: {task_id}")
        return True
    
    def get_task_history(self, ai_id: str = None, limit: int = 10) -> List[Dict]:
        """获取任务历史"""
        records = list(self.assignments.values())
        
        if ai_id:
            records = [r for r in records if r['ai_id'] == ai_id]
        
        records.sort(key=lambda x: x['assigned_at'], reverse=True)
        return records[:limit]
    
    def get_system_status(self) -> Dict:
        """获取系统状态"""
        total_tasks = len(self.tasks)
        pending_tasks = sum(1 for t in self.tasks.values() if t.status == TaskStatus.PENDING)
        processing_tasks = sum(1 for t in self.tasks.values() if t.status == TaskStatus.PROCESSING)
        completed_tasks = sum(1 for t in self.tasks.values() if t.status == TaskStatus.COMPLETED)
        failed_tasks = sum(1 for t in self.tasks.values() if t.status == TaskStatus.FAILED)
        
        total_workers = len(self.workers)
        available_workers = sum(1 for w in self.workers.values() if w.status == "idle")
        busy_workers = sum(1 for w in self.workers.values() if w.status == "busy")
        
        return {
            'total_tasks': total_tasks,
            'pending_tasks': pending_tasks,
            'processing_tasks': processing_tasks,
            'completed_tasks': completed_tasks,
            'failed_tasks': failed_tasks,
            'total_workers': total_workers,
            'available_workers': available_workers,
            'busy_workers': busy_workers,
            'tasks_by_status': {
                'pending': pending_tasks,
                'assigned': sum(1 for t in self.tasks.values() if t.status == TaskStatus.ASSIGNED),
                'claimed': sum(1 for t in self.tasks.values() if t.status == TaskStatus.CLAIMED),
                'processing': processing_tasks,
                'completed': completed_tasks,
                'failed': failed_tasks,
                'cancelled': sum(1 for t in self.tasks.values() if t.status == TaskStatus.CANCELLED)
            },
            'workers_by_status': {
                'idle': available_workers,
                'busy': busy_workers,
                'offline': total_workers - available_workers - busy_workers
            }
        }


class AIButler:
    """AI管家 - 统一管理和分配任务"""
    
    def __init__(self, task_center: TaskCenter):
        self.task_center = task_center
        self.task_type_mapping = {
            TaskType.DATA_ANALYSIS: ['ai_data_analyst'],
            TaskType.BACKUP: ['ai_backup_specialist'],
            TaskType.RECOVERY: ['ai_backup_specialist'],
            TaskType.MAINTENANCE: ['ai_maintenance_engineer'],
            TaskType.HEALTH_CHECK: ['ai_maintenance_engineer'],
            TaskType.PERFORMANCE_ANALYSIS: ['ai_data_analyst'],
            TaskType.ANOMALY_DETECTION: ['ai_security_expert'],
            TaskType.REPORT_GENERATION: ['ai_report_generator'],
            TaskType.SECURITY_SCAN: ['ai_security_expert'],
            TaskType.INTEGRATION: ['ai_integration_master'],
            TaskType.CUSTOM: ['ai_data_analyst', 'ai_maintenance_engineer'],
        }
    
    def auto_assign_task(self, task_id: str):
        """自动分配任务"""
        task = self.task_center.get_task(task_id)
        if not task:
            return
        
        # 获取适合的AI列表
        preferred_ais = task.preferred_ais
        if not preferred_ais:
            preferred_ais = self.task_type_mapping.get(task.type, [])
        
        # 找到可用的AI
        available_workers = []
        for ai_id in preferred_ais:
            worker = self.task_center.get_worker(ai_id)
            if worker and worker.is_available():
                available_workers.append(worker)
        
        if available_workers:
            # 选择最优的AI(基于成功率和负载)
            best_worker = self._select_best_worker(available_workers, task)
            
            # 分配任务
            if self.task_center.assign_task(task_id, best_worker.id):
                logger.info(f"AI管家自动分配任务: {task_id} -> {best_worker.id}")
                
                # 自动认领(模拟)
                self.task_center.claim_task(task_id, best_worker.id)
                
                # 自动开始执行(模拟)
                self.task_center.start_task(task_id)
                
                # 模拟执行完成
                self._simulate_task_execution(task_id)
    
    def _select_best_worker(self, workers: List[AIWorker], task: Task) -> AIWorker:
        """选择最佳工作者"""
        best_score = -1
        best_worker = workers[0]
        
        for worker in workers:
            score = 0
            
            # 成功率评分
            if worker.total_tasks > 0:
                score += worker.completed_tasks / worker.total_tasks * 100
            
            # 技能匹配评分
            for skill in task.required_skills:
                if worker.has_skill(skill):
                    score += 10
            
            # 专业匹配评分
            if task.type.value in worker.specialties:
                score += 20
            
            # 优先级加分
            if task.priority == TaskPriority.URGENT:
                score += 10
            elif task.priority == TaskPriority.HIGH:
                score += 5
            
            if score > best_score:
                best_score = score
                best_worker = worker
        
        # 更新分配评分
        for assignment in self.task_center.assignments.values():
            if assignment['task_id'] == task.id:
                assignment['score'] = best_score
                break
        
        return best_worker
    
    def _simulate_task_execution(self, task_id: str):
        """模拟任务执行"""
        def execute():
            time.sleep(1)  # 模拟执行时间
            
            task = self.task_center.get_task(task_id)
            if task and task.status == TaskStatus.PROCESSING:
                # 随机决定成功或失败(90%成功率)
                import random
                if random.random() < 0.9:
                    outputs = {
                        'result': 'success',
                        'message': f'任务 {task_id} 执行完成',
                        'processed': True
                    }
                    self.task_center.complete_task(task_id, outputs)
                else:
                    self.task_center.fail_task(task_id, '模拟失败')
        
        # 异步执行
        thread = threading.Thread(target=execute, daemon=True)
        thread.start()
    
    def get_unassigned_tasks(self) -> List[Dict]:
        """获取未分配的任务"""
        return self.task_center.list_tasks(status=TaskStatus.PENDING)
    
    def reassign_failed_tasks(self):
        """重新分配失败的任务"""
        failed_tasks = self.task_center.list_tasks(status=TaskStatus.FAILED)
        
        for task_data in failed_tasks:
            task_id = task_data['id']
            
            # 重置任务状态
            task = self.task_center.get_task(task_id)
            if task:
                task.status = TaskStatus.PENDING
                task.assigned_ai = None
                task.claimed_by = None
                task.error_message = None
                
                # 重新分配
                self.auto_assign_task(task_id)
    
    def balance_load(self):
        """负载均衡"""
        # 统计每个工作者的任务数
        worker_load = {}
        for worker in self.task_center.workers.values():
            worker_load[worker.id] = worker.total_tasks
        
        # 找到负载最高和最低的工作者
        if not worker_load:
            return
        
        max_load = max(worker_load.values())
        min_load = min(worker_load.values())
        
        # 如果负载差异大于阈值,进行调整
        if max_load - min_load > 2:
            logger.info(f"负载均衡: 最高{max_load}, 最低{min_load}")
    
    def get_overview(self) -> Dict:
        """获取概览"""
        status = self.task_center.get_system_status()
        
        return {
            'status': status,
            'unassigned_tasks': len(self.get_unassigned_tasks()),
            'recommendations': self._generate_recommendations()
        }
    
    def _generate_recommendations(self) -> List[str]:
        """生成推荐"""
        recommendations = []
        status = self.task_center.get_system_status()
        
        if status['pending_tasks'] > 5:
            recommendations.append('待处理任务过多,建议增加AI工作者或提高处理速度')
        
        if status['failed_tasks'] > 3:
            recommendations.append('存在较多失败任务,建议检查AI工作者配置')
        
        if status['busy_workers'] == status['total_workers']:
            recommendations.append('所有AI工作者都在忙碌,可能需要扩展')
        
        return recommendations


# 全局实例
task_center = TaskCenter()
