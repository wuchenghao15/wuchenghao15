#!/usr/bin/env python3
"""
AI Collection Manager
"""

import threading
import time
import json
from typing import List, Dict, Any, Optional
from collections import deque

class AICollection:
    """AI集合类，用于管理一组AI员工"""
    def __init__(self, collection_id: str, name: str, description: str = ""):
        self.collection_id = collection_id
        self.name = name
        self.description = description
        self.ai_employees = {}  # employee_id -> AIEmployee信息
        self.created_at = time.time()
        self.updated_at = time.time()
        self.status = "active"  # active, inactive, maintenance
        self.task_queue = deque()
        self.task_history = []
        self.performance_metrics = {
            "total_tasks": 0,
            "completed_tasks": 0,
            "failed_tasks": 0,
            "avg_response_time": 0.0,
            "last_updated": time.time()
        }
    
    def add_ai_employee(self, employee_id: str, employee_info: Dict[str, Any]):
        """添加AI员工到集合"""
        self.ai_employees[employee_id] = {
            **employee_info,
            "joined_at": time.time()
        }
        self.updated_at = time.time()
    
    def remove_ai_employee(self, employee_id: str):
        """从集合中移除AI员工"""
        if employee_id in self.ai_employees:
            del self.ai_employees[employee_id]
            self.updated_at = time.time()
    
    def get_ai_employee(self, employee_id: str) -> Optional[Dict[str, Any]]:
        """获取AI员工信息"""
        return self.ai_employees.get(employee_id)
    
    def get_all_ai_employees(self) -> Dict[str, Dict[str, Any]]:
        """获取所有AI员工"""
        return self.ai_employees
    
    def add_task(self, task: Dict[str, Any]):
        """添加任务到集合的任务队列"""
        task["collection_id"] = self.collection_id
        task["status"] = "pending"
        task["created_at"] = time.time()
        self.task_queue.append(task)
        self.performance_metrics["total_tasks"] += 1
    
    def distribute_task(self) -> Optional[Dict[str, Any]]:
        """将任务分发给集合中的AI员工"""
        if not self.task_queue or not self.ai_employees:
            return None
        
        # 简单的轮询任务分发策略
        task = self.task_queue.popleft()
        employee_ids = list(self.ai_employees.keys())
        
        # 选择下一个员工（基于任务历史中的分配数量）
        employee_task_counts = {}
        for emp_id in employee_ids:
            emp_task_counts[emp_id] = sum(1 for t in self.task_history if t.get("assigned_to") == emp_id)
        
        # 找到任务最少的员工
        min_tasks = min(employee_task_counts.values())
        for emp_id, count in employee_task_counts.items():
            if count == min_tasks:
                task["assigned_to"] = emp_id
                task["status"] = "assigned"
                task["assigned_at"] = time.time()
                self.task_history.append(task)
                return task
        
        # 如果上面的逻辑失败，随机选择一个员工
        import random
        task["assigned_to"] = random.choice(employee_ids)
        task["status"] = "assigned"
        task["assigned_at"] = time.time()
        self.task_history.append(task)
        return task
    
    def update_task_status(self, task_id: str, status: str, result: Any = None):
        """更新任务状态"""
        for task in self.task_history:
            if task.get("id") == task_id:
                task["status"] = status
                task["updated_at"] = time.time()
                if result is not None:
                    task["result"] = result
                
                if status == "completed":
                    task["completed_at"] = time.time()
                    self.performance_metrics["completed_tasks"] += 1
                    # 更新平均响应时间
                    if "assigned_at" in task:
                        response_time = task["completed_at"] - task["assigned_at"]
                        total_completed = self.performance_metrics["completed_tasks"]
                        self.performance_metrics["avg_response_time"] = (
                            (self.performance_metrics["avg_response_time"] * (total_completed - 1)) + response_time
                        ) / total_completed
                elif status == "failed":
                    self.performance_metrics["failed_tasks"] += 1
                
                self.performance_metrics["last_updated"] = time.time()
                break
    
    def get_collection_status(self) -> Dict[str, Any]:
        """获取集合状态"""
        return {
            "collection_id": self.collection_id,
            "name": self.name,
            "description": self.description,
            "status": self.status,
            "employee_count": len(self.ai_employees),
            "pending_tasks": len(self.task_queue),
            "total_tasks": self.performance_metrics["total_tasks"],
            "completed_tasks": self.performance_metrics["completed_tasks"],
            "failed_tasks": self.performance_metrics["failed_tasks"],
            "avg_response_time": self.performance_metrics["avg_response_time"],
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
    
    def update_status(self, status: str):
        """更新集合状态"""
        self.status = status
        self.updated_at = time.time()

class AICollectionManager:
    """AI集合管理器"""
    def __init__(self):
        self.collections = {}  # collection_id -> AICollection
        self.collection_id_counter = 1
    
    def create_collection(self, name: str, description: str = "") -> str:
        """创建AI集合"""
        collection_id = f"collection_{self.collection_id_counter}"
        self.collection_id_counter += 1
        collection = AICollection(collection_id, name, description)
        self.collections[collection_id] = collection
        return collection_id
    
    def get_collection(self, collection_id: str) -> Optional[AICollection]:
        """获取AI集合"""
        return self.collections.get(collection_id)
    
    def get_all_collections(self) -> Dict[str, AICollection]:
        """获取所有AI集合"""
        return self.collections
    
    def remove_collection(self, collection_id: str):
        """移除AI集合"""
        if collection_id in self.collections:
            del self.collections[collection_id]
    
    def add_employee_to_collection(self, collection_id: str, employee_id: str, employee_info: Dict[str, Any]):
        """将AI员工添加到指定集合"""
        if collection_id in self.collections:
            self.collections[collection_id].add_ai_employee(employee_id, employee_info)
    
    def remove_employee_from_collection(self, collection_id: str, employee_id: str):
        """从指定集合中移除AI员工"""
        if collection_id in self.collections:
            self.collections[collection_id].remove_ai_employee(employee_id)
    
    def add_task_to_collection(self, collection_id: str, task: Dict[str, Any]):
        """向指定集合添加任务"""
        if collection_id in self.collections:
            self.collections[collection_id].add_task(task)
    
    def distribute_tasks(self):
        """为所有集合分发任务"""
        distributed_tasks = []
        for collection in self.collections.values():
            if collection.status == "active":
                task = collection.distribute_task()
                if task:
                    distributed_tasks.append(task)
        return distributed_tasks
    
    def get_collection_status_report(self) -> List[Dict[str, Any]]:
        """获取所有集合的状态报告"""
        return [collection.get_collection_status() for collection in self.collections.values()]
    
    def get_employee_collections(self, employee_id: str) -> List[str]:
        """获取AI员工所属的所有集合"""
        collections = []
        for collection_id, collection in self.collections.items():
            if employee_id in collection.get_all_ai_employees():
                collections.append(collection_id)
        return collections
    
    def monitor_collections(self):
        """监控所有集合的状态（后台线程运行）"""
        while True:
            current_time = time.time()
            for collection in self.collections.values():
                # 检查集合的任务队列长度，如果太长，发出警告
                if len(collection.task_queue) > 100:
                    print(f"[WARNING] Collection {collection.collection_id} has {len(collection.task_queue)} pending tasks")
            
            # 每30秒检查一次
            time.sleep(30)

# 创建全局AI集合管理器实例
ai_collection_manager = AICollectionManager()

# 启动集合监控线程
collection_monitor_thread = threading.Thread(target=ai_collection_manager.monitor_collections, daemon=True)
collection_monitor_thread.start()
