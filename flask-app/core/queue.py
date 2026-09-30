# -*- coding: utf-8 -*-
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Message Queue Module - Task queue system for async processing
"""

import json
import time
import threading
from typing import Dict, Any, Optional, Callable, List
from datetime import datetime
from collections import deque
import sys

class Task:
    """Task object for queue"""
    
    def __init__(self, task_id: str, task_type: str, payload: Dict[str, Any], priority: int = 0):
        self.task_id = task_id
        self.task_type = task_type
        self.payload = payload
        self.priority = priority
        self.created_at = datetime.now()
        self.status = "pending"
        self.attempts = 0
        self.max_attempts = 3
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert task to dict"""
        return {
            "task_id": self.task_id,
            "task_type": self.task_type,
            "payload": self.payload,
            "priority": self.priority,
            "created_at": self.created_at.isoformat(),
            "status": self.status,
            "attempts": self.attempts
        }

class TaskQueue:
    """Priority task queue"""
    
    def __init__(self, max_size: int = 10000):
        self.queues: Dict[int, deque] = {}
        self.max_size = max_size
        self._lock = threading.Lock()
        self._task_registry: Dict[str, Callable] = {}
    
    def register_task_handler(self, task_type: str, handler: Callable) -> None:
        """Register a handler for a task type"""
        self._task_registry[task_type] = handler
    
    def enqueue(self, task_type: str, payload: Dict[str, Any], priority: int = 0) -> str:
        """Add task to queue"""
        task_id = f"{task_type}_{int(time.time() * 1000)}_{hash(str(payload))}"
        task = Task(task_id, task_type, payload, priority)
        
        with self._lock:
            if priority not in self.queues:
                self.queues[priority] = deque()
            
            if len(self.queues[priority]) < self.max_size:
                self.queues[priority].append(task)
                return task_id
        
        raise ValueError("Queue is full")
    
    def dequeue(self) -> Optional[Task]:
        """Get next task with highest priority"""
        with self._lock:
            for priority in sorted(self.queues.keys(), reverse=True):
                if self.queues[priority]:
                    return self.queues[priority].popleft()
        return None
    
    def get_task_count(self) -> int:
        """Get total number of tasks in queue"""
        with self._lock:
            return sum(len(q) for q in self.queues.values())
    
    def get_task_by_id(self, task_id: str) -> Optional[Task]:
        """Get task by ID"""
        with self._lock:
            for priority_queue in self.queues.values():
                for task in priority_queue:
                    if task.task_id == task_id:
                        return task
        return None
    
    def remove_task(self, task_id: str) -> bool:
        """Remove task from queue"""
        with self._lock:
            for priority_queue in self.queues.values():
                for i, task in enumerate(priority_queue):
                    if task.task_id == task_id:
                        del priority_queue[i]
                        return True
        return False

class QueueWorker:
    """Worker for processing queue tasks"""
    
    def __init__(self, queue: TaskQueue, worker_id: int = 0):
        self.queue = queue
        self.worker_id = worker_id
        self.running = False
        self._thread: Optional[threading.Thread] = None
    
    def start(self):
        """Start the worker"""
        self.running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
    
    def stop(self):
        """Stop the worker"""
        self.running = False
        if self._thread:
            self._thread.join()
    
    def _run(self):
        """Main worker loop"""
        while self.running:
            task = self.queue.dequeue()
            if task:
                self._process_task(task)
            else:
                time.sleep(0.1)
    
    def _process_task(self, task: Task):
        """Process a single task"""
        task.status = "processing"
        task.attempts += 1
        
        try:
            handler = self.queue._task_registry.get(task.task_type)
            if handler:
                result = handler(task.payload)
                task.status = "completed"
                return result
            else:
                task.status = "failed"
                raise ValueError(f"No handler registered for {task.task_type}")
        except Exception as e:
            task.status = "failed"
            if task.attempts < task.max_attempts:
                time.sleep(task.attempts * 2)
                self.queue.enqueue(task.task_type, task.payload, task.priority)

class QueueManager:
    """Central queue manager"""
    
    def __init__(self, num_workers: int = 4):
        self.task_queue = TaskQueue()
        self.workers: List[QueueWorker] = []
        
        for i in range(num_workers):
            worker = QueueWorker(self.task_queue, i)
            self.workers.append(worker)
    
    def start(self):
        """Start all workers"""
        for worker in self.workers:
            worker.start()
    
    def stop(self):
        """Stop all workers"""
        for worker in self.workers:
            worker.stop()
    
    def enqueue(self, task_type: str, payload: Dict[str, Any], priority: int = 0) -> str:
        """Add task to queue"""
        return self.task_queue.enqueue(task_type, payload, priority)
    
    def register_handler(self, task_type: str, handler: Callable) -> None:
        """Register a task handler"""
        self.task_queue.register_task_handler(task_type, handler)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get queue statistics"""
        return {
            "total_tasks": self.task_queue.get_task_count(),
            "num_workers": len(self.workers),
            "running_workers": sum(1 for w in self.workers if w.running)
        }

# Global queue manager instance
queue_manager = QueueManager()
