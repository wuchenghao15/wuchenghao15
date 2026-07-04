# -*- coding: utf-8 -*-
"""
数据库管理 AI 员工基类
模板方法模式：统一 start/stop/status/_run_loop，子类只需实现 _do_work
"""

import logging
import threading
import time
from datetime import datetime
from typing import Dict, Any, Optional

from ai_engines.ai_employees import AIEmployee

logger = logging.getLogger(__name__)


class BaseDBEmployee(AIEmployee):
    """数据库管理 AI 员工基类（模板方法模式）

    子类只需实现 _do_work() 方法，基类统一管理：
    - daemon 守护线程的启动/停止
    - 任务计数和状态跟踪
    - 异常捕获（避免线程崩溃）
    - 与 AIDistributedDatabaseManager 的关联
    """

    def __init__(self, employee_id: str, name: str, role: str,
                 skills: list, interval: int = 300):
        """
        Args:
            employee_id: 员工ID
            name: 员工名称
            role: 角色
            skills: 技能列表
            interval: 守护线程循环间隔（秒）
        """
        super().__init__(employee_id, name, role, skills)
        self.interval = interval
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._manager = None  # AIDistributedDatabaseManager 引用（延迟注入）
        self._task_count = 0
        self._last_task = None
        self._last_error = None
        self._lock = threading.Lock()

    def set_manager(self, manager):
        """注入 AIDistributedDatabaseManager 引用"""
        self._manager = manager
        logger.info(f"数据库员工 {self.name} 已关联管理器")

    def start(self) -> bool:
        """启动守护线程"""
        if self._running:
            logger.warning(f"数据库员工 {self.name} 已在运行")
            return False

        self._running = True
        self.status = 'running'
        self._thread = threading.Thread(
            target=self._run_loop,
            name=f"db_employee_{self.employee_id}",
            daemon=True  # daemon 线程，主进程退出时自动清理
        )
        self._thread.start()
        logger.info(f"数据库员工 {self.name} 已启动 (间隔 {self.interval}s)")
        return True

    def stop(self) -> bool:
        """停止守护线程"""
        if not self._running:
            return False

        self._running = False
        self.status = 'stopped'
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5)
        logger.info(f"数据库员工 {self.name} 已停止 (共执行 {self._task_count} 次任务)")
        return True

    def _run_loop(self):
        """模板方法：守护线程主循环"""
        logger.info(f"数据库员工 {self.name} 守护线程开始运行")
        while self._running:
            try:
                self._do_work()
                with self._lock:
                    self._task_count += 1
                    self._last_task = datetime.now().isoformat()
            except Exception as e:
                self._last_error = str(e)
                logger.error(f"数据库员工 {self.name} 执行任务出错: {e}", exc_info=True)

            # 分段睡眠，便于快速响应 stop 信号
            slept = 0
            while slept < self.interval and self._running:
                time.sleep(1)
                slept += 1

        logger.info(f"数据库员工 {self.name} 守护线程退出")

    def _do_work(self):
        """子类实现：具体工作逻辑"""
        raise NotImplementedError("子类必须实现 _do_work 方法")

    def get_status(self) -> Dict[str, Any]:
        """返回员工状态"""
        base_status = super().get_status()
        base_status.update({
            'interval': self.interval,
            'task_count': self._task_count,
            'last_task': self._last_task,
            'last_error': self._last_error,
            'has_manager': self._manager is not None,
            'thread_alive': self._thread.is_alive() if self._thread else False
        })
        return base_status

    def execute_task(self, task: str) -> Dict[str, Any]:
        """手动执行一次任务（不依赖守护线程）"""
        result = {'success': False, 'employee_id': self.employee_id,
                  'employee_name': self.name, 'task': task}
        try:
            self._do_work()
            with self._lock:
                self._task_count += 1
                self._last_task = datetime.now().isoformat()
            result['success'] = True
            result['result'] = '任务执行完成'
        except Exception as e:
            result['error'] = str(e)
            self._last_error = str(e)
            logger.error(f"数据库员工 {self.name} 手动任务失败: {e}")
        result['timestamp'] = datetime.now().isoformat()
        return result
