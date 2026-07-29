# -*- coding: utf-8 -*-
"""
自动计划调度框架 - 基类与调度管理器
====================================

所有自动计划必须继承 AbstractAutoPlan 并实现 execute() 方法。
CentralPlanScheduler 负责计划注册、调度执行、错误隔离。
"""

from __future__ import annotations

import json
import logging
import sqlite3
import threading
import time
import traceback
from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional


logger = logging.getLogger('AutoPlans')
logger.setLevel(logging.INFO)


class PlanStatus(str, Enum):
    IDLE = 'idle'
    RUNNING = 'running'
    SUCCESS = 'success'
    FAILED = 'failed'
    DISABLED = 'disabled'


@dataclass
class PlanResult:
    plan_id: str
    success: bool
    message: str = ''
    data: Dict[str, Any] = field(default_factory=dict)
    duration_ms: int = 0
    timestamp: str = ''
    errors: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class PlanInfo:
    plan_id: str
    name: str
    description: str
    category: str
    interval_seconds: int
    status: PlanStatus
    last_run: Optional[str] = None
    next_run: Optional[str] = None
    last_result: Optional[Dict[str, Any]] = None
    total_runs: int = 0
    success_rate: float = 0.0
    enabled: bool = True


class AbstractAutoPlan(ABC):
    """自动计划抽象基类

    所有计划必须继承此类并实现 execute() 方法。
    提供统一的生命周期管理、错误隔离、日志记录。
    """

    plan_id: str = ''
    name: str = ''
    description: str = ''
    category: str = 'maintenance'
    interval_seconds: int = 3600
    enabled: bool = True

    def __init__(self):
        self._status: PlanStatus = PlanStatus.IDLE
        self._last_run: Optional[datetime] = None
        self._last_result: Optional[PlanResult] = None
        self._total_runs: int = 0
        self._success_count: int = 0
        self._failure_count: int = 0
        self._lock = threading.Lock()
        self._callbacks: List[Callable] = []

    @abstractmethod
    def execute(self) -> PlanResult:
        """执行计划核心逻辑，子类必须实现"""
        ...

    def run_once(self) -> PlanResult:
        """安全执行一次计划，含错误隔离"""
        if not self.enabled:
            return PlanResult(
                plan_id=self.plan_id,
                success=False,
                message='计划已禁用',
                errors=['plan_disabled'],
            )

        with self._lock:
            self._status = PlanStatus.RUNNING
            start = time.time()
            errors: List[str] = []
            data: Dict[str, Any] = {}
            success = False
            message = ''

            try:
                result = self.execute()
                if isinstance(result, PlanResult):
                    success = result.success
                    message = result.message
                    data = result.data
                    errors = result.errors
                elif isinstance(result, dict):
                    success = result.get('success', False)
                    message = result.get('message', '')
                    data = result.get('data', {})
                    errors = result.get('errors', [])
                else:
                    success = bool(result)
                    message = str(result) if result else '执行完成'

            except Exception as exc:
                success = False
                message = f'计划异常: {exc}'
                errors.append(str(exc))
                logger.error(f'[AutoPlan:{self.plan_id}] 执行异常: {exc}')
                logger.error(traceback.format_exc())

            duration_ms = int((time.time() - start) * 1000)
            self._last_run = datetime.now()
            self._total_runs += 1
            if success:
                self._success_count += 1
                self._status = PlanStatus.SUCCESS
            else:
                self._failure_count += 1
                self._status = PlanStatus.FAILED

            plan_result = PlanResult(
                plan_id=self.plan_id,
                success=success,
                message=message,
                data=data,
                duration_ms=duration_ms,
                timestamp=datetime.now().isoformat(),
                errors=errors,
            )
            self._last_result = plan_result

            self._log_execution(plan_result)
            self._fire_callbacks(plan_result)

            return plan_result

    def get_status(self) -> PlanInfo:
        """获取计划当前状态"""
        total = self._total_runs
        success_rate = (self._success_count / total * 100) if total > 0 else 0.0
        return PlanInfo(
            plan_id=self.plan_id,
            name=self.name,
            description=self.description,
            category=self.category,
            interval_seconds=self.interval_seconds,
            status=self._status,
            last_run=self._last_run.isoformat() if self._last_run else None,
            last_result=self._last_result.to_dict() if self._last_result else None,
            total_runs=total,
            success_rate=round(success_rate, 2),
            enabled=self.enabled,
        )

    def toggle(self, enabled: Optional[bool] = None) -> bool:
        """启用/禁用计划"""
        if enabled is not None:
            self.enabled = enabled
        else:
            self.enabled = not self.enabled
        return self.enabled

    def on_complete(self, callback: Callable[[PlanResult], None]) -> None:
        """注册完成回调"""
        self._callbacks.append(callback)

    def _fire_callbacks(self, result: PlanResult) -> None:
        for cb in self._callbacks:
            try:
                cb(result)
            except Exception as exc:
                logger.warning(f'[AutoPlan:{self.plan_id}] 回调异常: {exc}')

    def _log_execution(self, result: PlanResult) -> None:
        level = logging.INFO if result.success else logging.WARNING
        logger.log(level,
            f'[AutoPlan:{self.plan_id}] {"成功" if result.success else "失败"} '
            f'耗时={result.duration_ms}ms | {result.message}'
        )


class CentralPlanScheduler:
    """统一计划调度管理器

    负责计划注册、定时调度、状态查询。
    支持手动触发和批量启动。
    """

    def __init__(self):
        self._plans: Dict[str, AbstractAutoPlan] = {}
        self._timers: Dict[str, threading.Timer] = {}
        self._lock = threading.Lock()
        self._running = False
        self._thread: Optional[threading.Thread] = None

    def register(self, plan: AbstractAutoPlan) -> None:
        """注册一个计划"""
        with self._lock:
            if not plan.plan_id:
                raise ValueError('计划必须有 plan_id')
            self._plans[plan.plan_id] = plan
            logger.info(f'[Scheduler] 注册计划: {plan.plan_id} ({plan.name})')

    def unregister(self, plan_id: str) -> None:
        """注销一个计划"""
        with self._lock:
            self._cancel_timer(plan_id)
            self._plans.pop(plan_id, None)

    def get_plan(self, plan_id: str) -> Optional[AbstractAutoPlan]:
        return self._plans.get(plan_id)

    def list_plans(self) -> List[PlanInfo]:
        return [p.get_status() for p in self._plans.values()]

    def run_plan(self, plan_id: str) -> Optional[PlanResult]:
        """手动触发某个计划"""
        plan = self._plans.get(plan_id)
        if not plan:
            return None
        return plan.run_once()

    def run_all(self) -> Dict[str, PlanResult]:
        """手动触发所有计划"""
        results: Dict[str, PlanResult] = {}
        for pid in list(self._plans.keys()):
            results[pid] = self.run_plan(pid)
        return results

    def start_all(self) -> None:
        """启动所有计划的定时调度"""
        self._running = True
        for plan_id, plan in self._plans.items():
            if plan.enabled:
                self._schedule_plan(plan_id, plan.interval_seconds)
        logger.info(f'[Scheduler] 已启动 {len(self._plans)} 个计划')

    def stop_all(self) -> None:
        """停止所有计划"""
        self._running = False
        for plan_id in list(self._timers.keys()):
            self._cancel_timer(plan_id)
        logger.info('[Scheduler] 已停止所有计划')

    def _schedule_plan(self, plan_id: str, interval: int) -> None:
        """调度单个计划"""
        self._cancel_timer(plan_id)
        timer = threading.Timer(interval, self._tick, args=(plan_id,))
        timer.daemon = True
        self._timers[plan_id] = timer
        timer.start()

    def _cancel_timer(self, plan_id: str) -> None:
        timer = self._timers.pop(plan_id, None)
        if timer and timer.is_alive():
            timer.cancel()

    def _tick(self, plan_id: str) -> None:
        """定时器回调"""
        plan = self._plans.get(plan_id)
        if not plan or not self._running:
            return

        plan.run_once()

        if plan.enabled and self._running:
            self._schedule_plan(plan_id, plan.interval_seconds)

    def get_overall_status(self) -> Dict[str, Any]:
        """获取调度器整体状态"""
        return {
            'running': self._running,
            'total_plans': len(self._plans),
            'active_plans': len([p for p in self._plans.values() if p.enabled]),
            'plans': self.list_plans(),
        }


# ---------- 全局单例 ----------
_scheduler_instance: Optional[CentralPlanScheduler] = None
_plan_registry: Dict[str, type] = {}
_registry_lock = threading.Lock()


def get_plan_scheduler() -> CentralPlanScheduler:
    """获取全局调度器单例"""
    global _scheduler_instance
    if _scheduler_instance is None:
        _scheduler_instance = CentralPlanScheduler()
    return _scheduler_instance


def get_plan(plan_id: str) -> Optional[AbstractAutoPlan]:
    """从调度器获取已注册的计划"""
    return get_plan_scheduler().get_plan(plan_id)


def list_all_plans() -> List[PlanInfo]:
    """列出所有计划状态"""
    return get_plan_scheduler().list_plans()


def register_plan_class(cls: type) -> type:
    """装饰器：注册计划类到全局注册表

    Usage:
        @register_plan_class
        class MyPlan(AbstractAutoPlan):
            plan_id = 'my_plan'
            ...
    """
    with _registry_lock:
        _plan_registry[getattr(cls, 'plan_id', '')] = cls
    return cls


def create_all_plans_and_register() -> CentralPlanScheduler:
    """创建所有计划实例并注册到调度器"""
    scheduler = get_plan_scheduler()
    for plan_id, cls in _plan_registry.items():
        try:
            instance = cls()
            scheduler.register(instance)
        except Exception as exc:
            logger.error(f'[Registry] 创建计划 {plan_id} 失败: {exc}')
    return scheduler
