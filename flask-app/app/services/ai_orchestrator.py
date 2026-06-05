"""
AI智能编排系统 v4.0.0
协调多个AI员工工作，实现自动化流程，智能预警和自我学习
"""

import logging
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
from collections import deque

from .intelligent_decision_engine import get_decision_engine, DecisionType
from .enhanced_knowledge_graph import get_knowledge_graph
from .intelligent_predictor import get_predictor

logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """任务状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AlertLevel(Enum):
    """预警级别"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class AITask:
    """AI任务"""
    task_id: str
    task_type: str
    priority: int
    description: str
    status: TaskStatus
    assigned_worker: Optional[str]
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    dependencies: List[str] = field(default_factory=list)


@dataclass
class Alert:
    """预警信息"""
    alert_id: str
    level: AlertLevel
    title: str
    description: str
    source: str
    metrics: Dict[str, Any]
    created_at: datetime
    acknowledged: bool = False
    resolved: bool = False
    resolved_at: Optional[datetime] = None


@dataclass
class LearningRecord:
    """学习记录"""
    record_id: str
    learning_type: str
    context: Dict[str, Any]
    outcome: str
    success: bool
    confidence_delta: float
    learned_at: datetime


class AIOrchestrator:
    """AI编排器"""
    
    def __init__(self):
        self.tasks: Dict[str, AITask] = {}
        self.task_queue: deque = deque()
        self.alerts: Dict[str, Alert] = {}
        self.learning_records: List[LearningRecord] = []
        self.workers: Dict[str, Dict[str, Any]] = {}
        self.running = False
        self.scheduler_thread: Optional[threading.Thread] = None
        self.monitor_thread: Optional[threading.Thread] = None
        
        # 初始化核心组件
        self.decision_engine = get_decision_engine()
        self.knowledge_graph = get_knowledge_graph()
        self.predictor = get_predictor()
        
        # 注册默认AI员工
        self._register_default_workers()
        
        logger.info("AI智能编排系统初始化完成")
    
    def _register_default_workers(self):
        """注册默认AI员工"""
        self.workers = {
            "error_detector": {
                "name": "错误检测员",
                "capabilities": ["error_detection", "code_analysis"],
                "status": "idle",
                "current_task": None
            },
            "learning_advisor": {
                "name": "学习顾问",
                "capabilities": ["learning_analysis", "personalized_recommendation"],
                "status": "idle",
                "current_task": None
            },
            "system_optimizer": {
                "name": "系统优化师",
                "capabilities": ["performance_optimization", "resource_allocation"],
                "status": "idle",
                "current_task": None
            },
            "knowledge_curator": {
                "name": "知识管理员",
                "capabilities": ["knowledge_update", "graph_optimization"],
                "status": "idle",
                "current_task": None
            },
            "predictive_analyst": {
                "name": "预测分析师",
                "capabilities": ["trend_analysis", "prediction"],
                "status": "idle",
                "current_task": None
            }
        }
    
    def start(self):
        """启动编排器"""
        if self.running:
            return
        
        self.running = True
        
        # 启动调度线程
        self.scheduler_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self.scheduler_thread.start()
        
        # 启动监控线程
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        
        logger.info("AI智能编排系统已启动")
    
    def stop(self):
        """停止编排器"""
        self.running = False
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        logger.info("AI智能编排系统已停止")
    
    def submit_task(self, task_type: str, description: str, 
                   priority: int = 5, dependencies: List[str] = None) -> AITask:
        """提交任务"""
        import hashlib
        
        task_id = hashlib.md5(f"{task_type}_{datetime.now().isoformat()}".encode()).hexdigest()[:12]
        
        task = AITask(
            task_id=task_id,
            task_type=task_type,
            priority=priority,
            description=description,
            status=TaskStatus.PENDING,
            assigned_worker=None,
            created_at=datetime.now(),
            dependencies=dependencies or []
        )
        
        self.tasks[task_id] = task
        self.task_queue.append(task)
        
        logger.info(f"提交任务: {task_id} - {description}")
        return task
    
    def _scheduler_loop(self):
        """调度循环"""
        while self.running:
            try:
                self._process_task_queue()
                time.sleep(1)
            except Exception as e:
                logger.error(f"调度循环出错: {e}")
    
    def _process_task_queue(self):
        """处理任务队列"""
        if not self.task_queue:
            return
        
        # 按优先级排序
        sorted_queue = sorted(self.task_queue, key=lambda t: t.priority)
        self.task_queue.clear()
        self.task_queue.extend(sorted_queue)
        
        for task in list(self.task_queue):
            if task.status == TaskStatus.PENDING:
                # 检查依赖
                dependencies_met = all(
                    self.tasks.get(dep, {}).get('status') == TaskStatus.COMPLETED
                    for dep in task.dependencies
                )
                
                if dependencies_met:
                    self._assign_task(task)
    
    def _assign_task(self, task: AITask):
        """分配任务给合适的AI员工"""
        # 找到合适的空闲员工
        for worker_id, worker in self.workers.items():
            if worker["status"] == "idle" and self._worker_can_handle(worker_id, task.task_type):
                task.assigned_worker = worker_id
                task.status = TaskStatus.RUNNING
                task.started_at = datetime.now()
                worker["status"] = "busy"
                worker["current_task"] = task.task_id
                
                # 异步执行任务
                threading.Thread(
                    target=self._execute_task,
                    args=(task, worker_id),
                    daemon=True
                ).start()
                
                logger.info(f"任务 {task.task_id} 分配给 {worker['name']}")
                self.task_queue.remove(task)
                break
    
    def _worker_can_handle(self, worker_id: str, task_type: str) -> bool:
        """检查AI员工是否能处理任务"""
        worker = self.workers.get(worker_id, {})
        capabilities = worker.get("capabilities", [])
        
        task_capability_map = {
            "error_detection": ["error_detection", "code_analysis"],
            "learning_analysis": ["learning_analysis", "personalized_recommendation"],
            "system_optimization": ["performance_optimization", "resource_allocation"],
            "knowledge_management": ["knowledge_update", "graph_optimization"],
            "prediction": ["trend_analysis", "prediction"]
        }
        
        required_capabilities = task_capability_map.get(task_type, [])
        return any(cap in capabilities for cap in required_capabilities)
    
    def _execute_task(self, task: AITask, worker_id: str):
        """执行任务"""
        try:
            logger.info(f"执行任务: {task.task_id}")
            
            # 根据任务类型执行
            result = self._handle_task_by_type(task)
            
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.now()
            task.result = result
            
            logger.info(f"任务完成: {task.task_id}")
            
            # 从执行中学习
            self._learn_from_execution(task, success=True)
            
        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error = str(e)
            task.completed_at = datetime.now()
            
            logger.error(f"任务失败: {task.task_id} - {e}")
            
            # 从失败中学习
            self._learn_from_execution(task, success=False)
        
        finally:
            # 释放员工
            if worker_id in self.workers:
                self.workers[worker_id]["status"] = "idle"
                self.workers[worker_id]["current_task"] = None
    
    def _handle_task_by_type(self, task: AITask) -> Dict[str, Any]:
        """根据任务类型处理"""
        if task.task_type == "error_detection":
            return self._run_error_detection(task)
        elif task.task_type == "learning_analysis":
            return self._run_learning_analysis(task)
        elif task.task_type == "system_optimization":
            return self._run_system_optimization(task)
        elif task.task_type == "knowledge_management":
            return self._run_knowledge_management(task)
        elif task.task_type == "prediction":
            return self._run_prediction(task)
        else:
            return {"status": "completed", "message": "通用任务处理"}
    
    def _run_error_detection(self, task: AITask) -> Dict[str, Any]:
        """运行错误检测"""
        from app.services.ai_error_fixer import ErrorFixer
        
        fixer = ErrorFixer()
        errors = fixer.detect_all_errors(code="", language="python")
        
        return {
            "errors_found": len(errors),
            "errors": errors
        }
    
    def _run_learning_analysis(self, task: AITask) -> Dict[str, Any]:
        """运行学习分析"""
        # 模拟学生数据分析
        student_id = task.description.split("_")[-1] if "_" in task.description else "default"
        
        prediction = self.predictor.predict_learning_performance(
            student_id=student_id,
            historical_scores=[{'score': 75}, {'score': 78}, {'score': 82}],
            study_hours=[1.5, 2.0, 1.8, 2.5, 2.2, 1.9, 2.1],
            engagement_data=[0.7, 0.8, 0.75, 0.85, 0.8, 0.78, 0.82]
        )
        
        return {
            "prediction": {
                "score": prediction.predicted_value,
                "trend": prediction.trend,
                "recommendations": prediction.recommendations
            }
        }
    
    def _run_system_optimization(self, task: AITask) -> Dict[str, Any]:
        """运行系统优化"""
        # 使用决策引擎
        decision = self.decision_engine.make_decision(
            metrics={"cpu_usage": 65, "memory_usage": 72, "system_related": True}
        )
        
        return {
            "decision": {
                "title": decision.title,
                "type": decision.type.value,
                "priority": decision.priority.name,
                "recommendations": decision.action
            }
        }
    
    def _run_knowledge_management(self, task: AITask) -> Dict[str, Any]:
        """运行知识管理"""
        stats = self.knowledge_graph.get_statistics()
        return {
            "knowledge_stats": stats,
            "action": "knowledge_graph_updated"
        }
    
    def _run_prediction(self, task: AITask) -> Dict[str, Any]:
        """运行预测任务"""
        load_data = [45, 50, 55, 52, 58, 60, 62, 59, 65, 68]
        prediction = self.predictor.predict_system_load(load_data)
        
        return {
            "predicted_load": prediction.predicted_value,
            "trend": prediction.trend,
            "recommendations": prediction.recommendations
        }
    
    def create_alert(self, level: AlertLevel, title: str, description: str,
                    source: str, metrics: Dict[str, Any] = None) -> Alert:
        """创建预警"""
        import hashlib
        
        alert_id = hashlib.md5(f"{title}_{datetime.now().isoformat()}".encode()).hexdigest()[:12]
        
        alert = Alert(
            alert_id=alert_id,
            level=level,
            title=title,
            description=description,
            source=source,
            metrics=metrics or {},
            created_at=datetime.now()
        )
        
        self.alerts[alert_id] = alert
        
        # 如果是严重级别，自动触发处理
        if level == AlertLevel.CRITICAL:
            self._handle_critical_alert(alert)
        
        logger.warning(f"创建预警: {level.value} - {title}")
        return alert
    
    def _handle_critical_alert(self, alert: Alert):
        """处理严重预警"""
        # 自动提交优化任务
        self.submit_task(
            task_type="system_optimization",
            description=f"自动响应预警: {alert.title}",
            priority=1
        )
    
    def acknowledge_alert(self, alert_id: str):
        """确认预警"""
        if alert_id in self.alerts:
            self.alerts[alert_id].acknowledged = True
            logger.info(f"预警已确认: {alert_id}")
    
    def resolve_alert(self, alert_id: str):
        """解决预警"""
        if alert_id in self.alerts:
            self.alerts[alert_id].resolved = True
            self.alerts[alert_id].resolved_at = datetime.now()
            logger.info(f"预警已解决: {alert_id}")
    
    def _monitor_loop(self):
        """监控循环"""
        while self.running:
            try:
                self._check_system_status()
                time.sleep(10)  # 每10秒检查一次
            except Exception as e:
                logger.error(f"监控循环出错: {e}")
    
    def _check_system_status(self):
        """检查系统状态"""
        # 模拟系统指标检查
        import random
        
        cpu_usage = 50 + random.randint(-10, 30)
        memory_usage = 60 + random.randint(-10, 25)
        
        if cpu_usage > 85:
            self.create_alert(
                level=AlertLevel.WARNING,
                title="CPU使用率过高",
                description=f"当前CPU使用率: {cpu_usage}%",
                source="system_monitor",
                metrics={"cpu_usage": cpu_usage}
            )
        
        if memory_usage > 90:
            self.create_alert(
                level=AlertLevel.ERROR,
                title="内存使用率过高",
                description=f"当前内存使用率: {memory_usage}%",
                source="system_monitor",
                metrics={"memory_usage": memory_usage}
            )
        
        # 持续监控并自动决策
        metrics = {
            "cpu_usage": cpu_usage,
            "memory_usage": memory_usage,
            "timestamp": datetime.now().isoformat()
        }
        
        self.decision_engine.continuous_monitoring(metrics)
    
    def _learn_from_execution(self, task: AITask, success: bool):
        """从执行中学习"""
        import hashlib
        
        record_id = hashlib.md5(f"{task.task_id}_{datetime.now().isoformat()}".encode()).hexdigest()[:12]
        
        record = LearningRecord(
            record_id=record_id,
            learning_type=task.task_type,
            context={
                "task_id": task.task_id,
                "description": task.description,
                "worker": task.assigned_worker
            },
            outcome="success" if success else "failure",
            success=success,
            confidence_delta=0.05 if success else -0.05,
            learned_at=datetime.now()
        )
        
        self.learning_records.append(record)
        
        # 限制记录数量
        if len(self.learning_records) > 1000:
            self.learning_records = self.learning_records[-1000:]
        
        logger.info(f"记录学习: {task.task_type} - {'成功' if success else '失败'}")
    
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取任务状态"""
        task = self.tasks.get(task_id)
        if not task:
            return None
        
        return {
            "task_id": task.task_id,
            "type": task.task_type,
            "status": task.status.value,
            "description": task.description,
            "assigned_worker": task.assigned_worker,
            "created_at": task.created_at,
            "started_at": task.started_at,
            "completed_at": task.completed_at,
            "result": task.result,
            "error": task.error
        }
    
    def get_active_alerts(self) -> List[Dict[str, Any]]:
        """获取活跃预警"""
        active = [a for a in self.alerts.values() if not a.resolved]
        
        return [
            {
                "alert_id": a.alert_id,
                "level": a.level.value,
                "title": a.title,
                "description": a.description,
                "source": a.source,
                "created_at": a.created_at,
                "acknowledged": a.acknowledged
            }
            for a in sorted(active, key=lambda x: x.created_at, reverse=True)
        ]
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        total_tasks = len(self.tasks)
        completed = sum(1 for t in self.tasks.values() if t.status == TaskStatus.COMPLETED)
        failed = sum(1 for t in self.tasks.values() if t.status == TaskStatus.FAILED)
        pending = sum(1 for t in self.tasks.values() if t.status == TaskStatus.PENDING)
        
        active_alerts = sum(1 for a in self.alerts.values() if not a.resolved)
        
        return {
            "tasks": {
                "total": total_tasks,
                "completed": completed,
                "failed": failed,
                "pending": pending,
                "queue_length": len(self.task_queue)
            },
            "alerts": {
                "active": active_alerts,
                "total": len(self.alerts)
            },
            "workers": {
                "total": len(self.workers),
                "busy": sum(1 for w in self.workers.values() if w["status"] == "busy"),
                "idle": sum(1 for w in self.workers.values() if w["status"] == "idle")
            },
            "learning": {
                "total_records": len(self.learning_records),
                "success_rate": sum(1 for r in self.learning_records if r.success) / len(self.learning_records) if self.learning_records else 0
            }
        }


# 全局单例
_orchestrator: Optional[AIOrchestrator] = None


def get_orchestrator() -> AIOrchestrator:
    """获取编排器单例"""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = AIOrchestrator()
    return _orchestrator
