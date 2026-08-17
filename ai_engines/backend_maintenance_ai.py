#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
后台维护AI服务 - 自动监控、修复、上报和学习
"""

import os
import time
import threading
import traceback
from typing import Dict, List, Optional, Any
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime

from app.utils.logging import logger


class MaintenanceStatus(Enum):
    """维护状态"""
    RUNNING = "running"
    PAUSED = "paused"
    STOPPED = "stopped"
    ERROR = "error"


class MaintenanceTaskType(Enum):
    """维护任务类型"""
    ERROR_MONITORING = "error_monitoring"
    AUTO_FIX = "auto_fix"
    DB_REPORTING = "db_reporting"
    BRAIN_LEARNING = "brain_learning"
    SYSTEM_HEALTH = "system_health"


@dataclass
class MaintenanceTask:
    """维护任务"""
    task_id: str
    task_type: MaintenanceTaskType
    status: str = "pending"
    progress: int = 0
    message: str = ""
    started_at: Optional[float] = None
    completed_at: Optional[float] = None

    def to_dict(self) -> Dict:
        return {
            'task_id': self.task_id,
            'task_type': self.task_type.value,
            'status': self.status,
            'progress': self.progress,
            'message': self.message,
            'started_at': self.started_at,
            'completed_at': self.completed_at
        }


@dataclass
class MaintenanceReport:
    """维护报告"""
    report_id: str
    generated_at: float = field(default_factory=lambda: time.time())
    errors_found: int = 0
    errors_fixed: int = 0
    errors_pending: int = 0
    knowledge_added: int = 0
    knowledge_updated: int = 0
    tasks: List[MaintenanceTask] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            'report_id': self.report_id,
            'generated_at': self.generated_at,
            'errors_found': self.errors_found,
            'errors_fixed': self.errors_fixed,
            'errors_pending': self.errors_pending,
            'knowledge_added': self.knowledge_added,
            'knowledge_updated': self.knowledge_updated,
            'tasks': [t.to_dict() for t in self.tasks]
        }


class BackendMaintenanceAI:
    """后台维护AI服务"""

    def __init__(self):
        self._status = MaintenanceStatus.STOPPED
        self._tasks: Dict[str, MaintenanceTask] = {}
        self._lock = threading.RLock()
        self._monitor_thread = None
        self._monitor_interval = 60  # 监控间隔(秒)
        self._last_report: Optional[MaintenanceReport] = None
        self._error_report_service = None
        self._ai_auto_fix_service = None
        
        logger.info("后台维护AI服务初始化完成")

    def _init_services(self):
        """延迟初始化服务"""
        if self._error_report_service is None:
            from app.services.error_report_service import error_report_service
            self._error_report_service = error_report_service
        
        if self._ai_auto_fix_service is None:
            from app.services.ai_auto_fix_service import ai_auto_fix_service
            self._ai_auto_fix_service = ai_auto_fix_service

    def start(self):
        """启动维护AI"""
        with self._lock:
            if self._status == MaintenanceStatus.RUNNING:
                logger.warning("后台维护AI已在运行")
                return
            
            self._status = MaintenanceStatus.RUNNING
            
        self._init_services()
        
        # 启动监控线程
        self._monitor_thread = threading.Thread(
            target=self._monitor_loop,
            daemon=True,
            name="MaintenanceMonitor"
        )
        self._monitor_thread.start()
        
        logger.info("后台维护AI已启动")

    def stop(self):
        """停止维护AI"""
        with self._lock:
            self._status = MaintenanceStatus.STOPPED
        
        logger.info("后台维护AI已停止")

    def pause(self):
        """暂停维护AI"""
        with self._lock:
            if self._status == MaintenanceStatus.RUNNING:
                self._status = MaintenanceStatus.PAUSED
                logger.info("后台维护AI已暂停")

    def resume(self):
        """恢复维护AI"""
        with self._lock:
            if self._status == MaintenanceStatus.PAUSED:
                self._status = MaintenanceStatus.RUNNING
                logger.info("后台维护AI已恢复")

    def get_status(self) -> MaintenanceStatus:
        """获取状态"""
        return self._status

    def _monitor_loop(self):
        """监控循环"""
        while self._status == MaintenanceStatus.RUNNING:
            try:
                self._perform_maintenance()
            except Exception as e:
                logger.error(f"维护任务执行失败: {str(e)}")
            
            # 等待下一次执行
            for _ in range(self._monitor_interval):
                if self._status != MaintenanceStatus.RUNNING:
                    break
                time.sleep(1)

    def _perform_maintenance(self):
        """执行维护任务"""
        logger.debug("执行后台维护任务...")
        
        tasks = []
        
        # 1. 监控错误
        task = self._monitor_errors()
        tasks.append(task)
        
        # 2. 自动修复
        task = self._auto_fix_errors()
        tasks.append(task)
        
        # 3. 上报数据库
        task = self._report_to_database()
        tasks.append(task)
        
        # 4. 更新脑库
        task = self._update_brain_knowledge()
        tasks.append(task)
        
        # 5. 系统健康检查
        task = self._check_system_health()
        tasks.append(task)
        
        # 生成报告
        self._generate_report(tasks)

    def _monitor_errors(self) -> MaintenanceTask:
        """监控错误"""
        task = MaintenanceTask(
            task_id=f"TASK-MONITOR-{int(time.time())}",
            task_type=MaintenanceTaskType.ERROR_MONITORING,
            status="running",
            started_at=time.time()
        )
        
        try:
            stats = self._error_report_service.get_statistics()
            task.progress = 100
            task.status = "completed"
            task.message = f"发现 {stats.total_errors} 个错误,{stats.unresolved_count} 个未解决"
        except Exception as e:
            task.status = "failed"
            task.message = f"监控失败: {str(e)}"
        
        task.completed_at = time.time()
        return task

    def _auto_fix_errors(self) -> MaintenanceTask:
        """自动修复错误"""
        task = MaintenanceTask(
            task_id=f"TASK-FIX-{int(time.time())}",
            task_type=MaintenanceTaskType.AUTO_FIX,
            status="running",
            started_at=time.time()
        )
        
        try:
            unresolved_errors = self._error_report_service.list_errors(resolved=False, limit=10)
            fixed_count = 0
            
            for error_report in unresolved_errors:
                if 'ai_fix' in error_report.context:
                    continue
                
                try:
                    # 创建异常对象用于分析
                    exec(f"raise {error_report.error_type}('{error_report.message}')", globals(), locals())
                except Exception as e:
                    fix_result = self._error_report_service.auto_fix_error(
                        e,
                        error_report.file_path,
                        error_report.context
                    )
                    
                    if fix_result and fix_result['solution']['confidence'] > 0.7:
                        fixed_count += 1
                        # 标记为已解决
                        self._error_report_service.resolve_error(
                            error_report.error_id,
                            resolved_by="MaintenanceAI"
                        )
            
            task.progress = 100
            task.status = "completed"
            task.message = f"自动修复 {fixed_count} 个错误"
        except Exception as e:
            task.status = "failed"
            task.message = f"自动修复失败: {str(e)}"
        
        task.completed_at = time.time()
        return task

    def _report_to_database(self) -> MaintenanceTask:
        """上报数据库"""
        task = MaintenanceTask(
            task_id=f"TASK-REPORT-{int(time.time())}",
            task_type=MaintenanceTaskType.DB_REPORTING,
            status="running",
            started_at=time.time()
        )
        
        try:
            # 错误报告已经自动保存到数据库
            stats = self._error_report_service.get_statistics()
            task.progress = 100
            task.status = "completed"
            task.message = f"数据库同步完成,共 {stats.total_errors} 条记录"
        except Exception as e:
            task.status = "failed"
            task.message = f"上报失败: {str(e)}"
        
        task.completed_at = time.time()
        return task

    def _update_brain_knowledge(self) -> MaintenanceTask:
        """更新脑库知识"""
        task = MaintenanceTask(
            task_id=f"TASK-BRAIN-{int(time.time())}",
            task_type=MaintenanceTaskType.BRAIN_LEARNING,
            status="running",
            started_at=time.time()
        )
        
        try:
            # 获取所有未解决的错误并学习
            unresolved_errors = self._error_report_service.list_errors(resolved=False, limit=20)
            learned_count = 0
            
            for error_report in unresolved_errors:
                try:
                    exec(f"raise {error_report.error_type}('{error_report.message}')", globals(), locals())
                except Exception as e:
                    # 分析并学习
                    analysis, solution = self._ai_auto_fix_service.auto_fix_and_learn(
                        e,
                        error_report.file_path,
                        error_report.context
                    )
                    if solution.confidence > 0.7:
                        learned_count += 1
            
            task.progress = 100
            task.status = "completed"
            task.message = f"脑库学习完成,新增 {learned_count} 条知识"
        except Exception as e:
            task.status = "failed"
            task.message = f"脑库更新失败: {str(e)}"
        
        task.completed_at = time.time()
        return task

    def _check_system_health(self) -> MaintenanceTask:
        """系统健康检查"""
        task = MaintenanceTask(
            task_id=f"TASK-HEALTH-{int(time.time())}",
            task_type=MaintenanceTaskType.SYSTEM_HEALTH,
            status="running",
            started_at=time.time()
        )
        
        try:
            # 检查错误上报服务
            er_stats = self._error_report_service.get_statistics()
            
            # 检查脑库服务
            brain_stats = self._ai_auto_fix_service.get_knowledge_base_stats()
            
            health_status = []
            if er_stats.total_errors > 100:
                health_status.append(f"错误数过多: {er_stats.total_errors}")
            if er_stats.unresolved_count > 50:
                health_status.append(f"未解决错误过多: {er_stats.unresolved_count}")
            
            task.progress = 100
            task.status = "completed"
            task.message = "; ".join(health_status) if health_status else "系统健康"
        except Exception as e:
            task.status = "failed"
            task.message = f"健康检查失败: {str(e)}"
        
        task.completed_at = time.time()
        return task

    def _generate_report(self, tasks: List[MaintenanceTask]):
        """生成维护报告"""
        errors_fixed = 0
        errors_pending = 0
        knowledge_added = 0
        
        for task in tasks:
            if task.task_type == MaintenanceTaskType.AUTO_FIX:
                if '修复' in task.message:
                    import re
                    match = re.search(r'修复 (\d+) 个错误', task.message)
                    if match:
                        errors_fixed = int(match.group(1))
            elif task.task_type == MaintenanceTaskType.BRAIN_LEARNING:
                if '新增' in task.message:
                    match = re.search(r'新增 (\d+) 条知识', task.message)
                    if match:
                        knowledge_added = int(match.group(1))
        
        er_stats = self._error_report_service.get_statistics()
        
        report = MaintenanceReport(
            report_id=f"REPORT-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            errors_found=er_stats.total_errors,
            errors_fixed=errors_fixed,
            errors_pending=er_stats.unresolved_count,
            knowledge_added=knowledge_added,
            tasks=tasks
        )
        
        self._last_report = report
        
        logger.info(f"维护报告生成: {report.report_id}")

    def get_last_report(self) -> Optional[MaintenanceReport]:
        """获取最后一次报告"""
        return self._last_report

    def get_recent_tasks(self, limit: int = 10) -> List[MaintenanceTask]:
        """获取最近的任务"""
        return list(self._tasks.values())[-limit:]

    def run_single_task(self, task_type: MaintenanceTaskType) -> MaintenanceTask:
        """运行单个任务"""
        task_handlers = {
            MaintenanceTaskType.ERROR_MONITORING: self._monitor_errors,
            MaintenanceTaskType.AUTO_FIX: self._auto_fix_errors,
            MaintenanceTaskType.DB_REPORTING: self._report_to_database,
            MaintenanceTaskType.BRAIN_LEARNING: self._update_brain_knowledge,
            MaintenanceTaskType.SYSTEM_HEALTH: self._check_system_health,
        }
        
        handler = task_handlers.get(task_type)
        if handler:
            return handler()
        return None

    def get_summary(self) -> Dict:
        """获取维护摘要"""
        self._init_services()
        
        er_stats = self._error_report_service.get_statistics()
        brain_stats = self._ai_auto_fix_service.get_knowledge_base_stats()
        
        return {
            'status': self._status.value,
            'error_stats': {
                'total_errors': er_stats.total_errors,
                'resolved_count': er_stats.resolved_count,
                'unresolved_count': er_stats.unresolved_count,
                'errors_by_level': er_stats.errors_by_level,
                'errors_by_category': er_stats.errors_by_category
            },
            'brain_stats': {
                'total_knowledge': brain_stats['total_knowledge'],
                'avg_success_rate': brain_stats['avg_success_rate'],
                'total_usage': brain_stats['total_usage'],
                'patterns': brain_stats['patterns']
            },
            'last_report': self._last_report.to_dict() if self._last_report else None
        }


# 创建全局实例
backend_maintenance_ai = BackendMaintenanceAI()


def start_maintenance_ai():
    """启动后台维护AI"""
    backend_maintenance_ai.start()


def stop_maintenance_ai():
    """停止后台维护AI"""
    backend_maintenance_ai.stop()
