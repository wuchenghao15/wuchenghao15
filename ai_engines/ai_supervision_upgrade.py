# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
AI监管和升级维护模块
负责监控AI系统性能, 自动升级和维护
"""

import os
import sys
import logging
import time
import threading
import traceback
from datetime import datetime
from typing import Dict, List, Optional

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger('ai_supervision_upgrade')


class AISupervisionManager:
    """AI监管管理器: 负责监控和管理AI系统"""

    def __init__(self):
        """初始化AI监管管理器"""
        self.status = "active"
        self.monitoring_enabled = True
        self.auto_upgrade_enabled = True
        self.auto_maintenance_enabled = True
        self.system_metrics = {
            "cpu_usage": 0.0,
            "memory_usage": 0.0,
            "disk_usage": 0.0,
            "network_io": 0.0,
            "temperature": 0.0,
            "uptime": 0.0
        }

        self.ai_metrics = {
            "total_ai_employees": 0,
            "active_ai_employees": 0,
            "total_ai_collections": 0,
            "active_ai_collections": 0,
            "total_tasks": 0,
            "completed_tasks": 0,
            "average_task_time": 0.0,
            "system_success_rate": 1.0
        }

        self.upgrade_history = []
        self.maintenance_history = []
        self.alerts = []
        self.logger = logging.getLogger("ai_supervision_manager")
        self.logger.info("✓ AI监管管理器已初始化")

        self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitoring_thread.start()
        self.logger.info("✓ 监控线程已启动")

        self.upgrade_thread = threading.Thread(target=self._upgrade_management_loop, daemon=True)
        self.upgrade_thread.start()
        self.logger.info("✓ 升级管理线程已启动")

        self.maintenance_thread = threading.Thread(target=self._maintenance_loop, daemon=True)
        self.maintenance_thread.start()
        self.logger.info("✓ 维护线程已启动")

    def _monitoring_loop(self) -> None:
        """监控循环: 定期检查系统状态"""
        while True:
            if self.monitoring_enabled:
                self._monitor_system()
            time.sleep(10)

    def _upgrade_management_loop(self) -> None:
        """升级管理循环: 定期检查和执行升级"""
        while True:
            if self.auto_upgrade_enabled:
                self._manage_upgrades()
            time.sleep(600)

    def _maintenance_loop(self) -> None:
        """维护循环: 定期执行维护任务"""
        while True:
            if self.auto_maintenance_enabled:
                self._perform_maintenance()
            time.sleep(1800)

    def _monitor_system(self) -> None:
        """监控系统状态"""
        self.logger.info("执行系统监控...")

        try:
            from app.ai.distributed_ai_employee_manager import get_ai_employee_manager
            ai_employee_manager = get_ai_employee_manager()

            from app.ai.ai_collection_manager import get_collection_manager
            collection_manager = get_collection_manager()

            employees = ai_employee_manager.list_employees()
            collections = collection_manager.list_collections()

            self.ai_metrics["total_ai_employees"] = len(employees)
            self.ai_metrics["active_ai_employees"] = sum(1 for emp in employees if emp["status"] == "idle" or emp["status"] == "working")
            self.ai_metrics["total_ai_collections"] = len(collections)
            self.ai_metrics["active_ai_collections"] = sum(1 for col in collections if col["status"] == "active")

            total_tasks = 0
            completed_tasks = 0
            total_response_time = 0.0

            for emp in employees:
                total_tasks += emp["performance_metrics"]["tasks_completed"]
                completed_tasks += emp["performance_metrics"]["tasks_completed"] * emp["performance_metrics"]["success_rate"]

            self.ai_metrics["total_tasks"] = total_tasks
            self.ai_metrics["completed_tasks"] = completed_tasks

            if total_tasks > 0:
                self.ai_metrics["system_success_rate"] = completed_tasks / total_tasks

            try:
                import psutil
                self.system_metrics["cpu_usage"] = psutil.cpu_percent(interval=1)
                self.system_metrics["memory_usage"] = psutil.virtual_memory().percent
                self.system_metrics["disk_usage"] = psutil.disk_usage('/').percent
                self.system_metrics["uptime"] = time.time() - psutil.boot_time()
            except ImportError:
                self.logger.warning("psutil未安装, 跳过系统资源监控")

            self._check_alerts()

        except Exception as e:
            self.logger.error(f"监控系统时发生异常: {str(e)}")
            self.logger.error(traceback.format_exc())

    def _check_alerts(self) -> None:
        """检查是否需要生成警报"""
        alerts = []

        if self.system_metrics["cpu_usage"] > 90:
            alerts.append({
                "level": "critical",
                "message": f"CPU使用率过高: {self.system_metrics['cpu_usage']:.1f}%",
                "timestamp": datetime.now().isoformat(),
                "category": "system"
            })

        if self.system_metrics["memory_usage"] > 90:
            alerts.append({
                "level": "critical",
                "message": f"内存使用率过高: {self.system_metrics['memory_usage']:.1f}%",
                "timestamp": datetime.now().isoformat(),
                "category": "system"
            })

        if self.system_metrics["disk_usage"] > 90:
            alerts.append({
                "level": "warning",
                "message": f"磁盘使用率过高: {self.system_metrics['disk_usage']:.1f}%",
                "timestamp": datetime.now().isoformat(),
                "category": "system"
            })

        if self.ai_metrics["system_success_rate"] < 0.8:
            alerts.append({
                "level": "warning",
                "message": f"AI系统成功率过低: {self.ai_metrics['system_success_rate']:.2%}",
                "timestamp": datetime.now().isoformat(),
                "category": "ai"
            })

        for alert in alerts:
            self.logger.warning(f"[{alert['level']}] {alert['message']}")

        self.alerts.extend(alerts)
        if len(self.alerts) > 100:
            self.alerts = self.alerts[-100:]

    def _manage_upgrades(self) -> None:
        """管理AI系统升级"""
        self.logger.info("执行升级管理...")

        try:
            from app.ai.distributed_ai_employee_manager import get_ai_employee_manager
            ai_employee_manager = get_ai_employee_manager()

            from app.ai.ai_collection_manager import get_collection_manager
            collection_manager = get_collection_manager()

            upgrade_result = ai_employee_manager.upgrade_all_employees()
            self.upgrade_history.append({
                "timestamp": datetime.now().isoformat(),
                "type": "ai_employees",
                "success_count": upgrade_result["success_count"],
                "total_count": upgrade_result["total_count"],
                "success": upgrade_result["success_count"] > 0
            })

            self.logger.info("开始升级所有AI集...")
            collection_upgrade_result = collection_manager.upgrade_all_collections()

            self.upgrade_history.append({
                "timestamp": datetime.now().isoformat(),
                "type": "ai_collections",
                "success_count": collection_upgrade_result["success_count"],
                "total_count": collection_upgrade_result["total_count"],
                "success": collection_upgrade_result["success_count"] > 0
            })

            if len(self.upgrade_history) > 100:
                self.upgrade_history = self.upgrade_history[-100:]
        except Exception as e:
            self.logger.error(f"升级管理时发生异常: {str(e)}")
            self.logger.error(traceback.format_exc())

    def _perform_maintenance(self) -> None:
        """执行维护任务"""
        self.logger.info("执行系统维护...")

        try:
            self._cleanup_logs()
            self._optimize_database()
            self._cleanup_temp_files()

            self.maintenance_history.append({
                "timestamp": datetime.now().isoformat(),
                "tasks": ["cleanup_logs", "optimize_database", "cleanup_temp_files"],
                "success": True
            })

            if len(self.maintenance_history) > 100:
                self.maintenance_history = self.maintenance_history[-100:]

        except Exception as e:
            self.logger.error(f"执行维护时发生异常: {str(e)}")
            self.logger.error(traceback.format_exc())

            self.maintenance_history.append({
                "timestamp": datetime.now().isoformat(),
                "tasks": ["cleanup_logs", "optimize_database", "cleanup_temp_files"],
                "error": str(e)
            })

    def _cleanup_logs(self) -> None:
        """清理日志文件"""
        self.logger.info("清理日志文件...")

        import glob
        log_files = glob.glob("*.log")

        for log_file in log_files:
            try:
                if os.path.getsize(log_file) > 100 * 1024 * 1024:
                    self.logger.info(f"清理大型日志文件: {log_file}")
                    with open(log_file, 'w') as f:
                        f.write(f"日志清理于 {datetime.now().isoformat()}\n")
            except Exception as e:
                self.logger.error(f"清理日志文件 {log_file} 失败: {str(e)}")

    def _optimize_database(self) -> None:
        """优化数据库"""
        self.logger.info("优化数据库...")

        try:
            import sqlite3
            db_files = ["app.db", "backup.db", "primary.db"]

            for db_file in db_files:
                if os.path.exists(db_file):
                    self.logger.info(f"优化数据库: {db_file}")
                    conn = sqlite3.connect(db_file)
                    conn.execute("VACUUM")
                    conn.execute("ANALYZE")
                    conn.close()
        except Exception as e:
            self.logger.error(f"优化数据库失败: {str(e)}")

    def _cleanup_temp_files(self) -> None:
        """清理临时文件"""
        self.logger.info("清理临时文件...")

        import glob

        for tmp_file in glob.glob("*.pyc"):
            try:
                os.remove(tmp_file)
            except Exception as e:
                self.logger.error(f"清理临时文件 {tmp_file} 失败: {str(e)}")

        for pycache_dir in glob.glob("**/__pycache__", recursive=True):
            try:
                import shutil
                shutil.rmtree(pycache_dir)
            except Exception as e:
                self.logger.error(f"清理__pycache__目录 {pycache_dir} 失败: {str(e)}")

    def get_system_health(self) -> Dict:
        """
        获取系统健康状态

        Returns:
            系统健康状态信息
        """
        return {
            "status": self.status,
            "system_metrics": self.system_metrics,
            "ai_metrics": self.ai_metrics,
            "alerts": self.alerts,
            "upgrade_history": self.upgrade_history,
            "maintenance_history": self.maintenance_history
        }

    def get_ai_employee_status(self) -> List:
        """
        获取AI员工状态

        Returns:
            AI员工状态列表
        """
        try:
            from app.ai.distributed_ai_employee_manager import get_ai_employee_manager
            ai_employee_manager = get_ai_employee_manager()
            return ai_employee_manager.list_employees()
        except Exception as e:
            self.logger.error(f"获取AI员工状态失败: {str(e)}")
            return []


ai_supervision_manager = AISupervisionManager()
