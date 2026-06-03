# -*- coding: utf-8 -*-
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
系统监控和日志记录模块
用于统一监控影子系统、快照系统、备份系统和同步系统的状态和性能
"""

import time
import threading
import json
import logging
from datetime import datetime
from enum import Enum
from collections import defaultdict, deque
import sys

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('system_monitor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('SystemMonitor')

class SystemType(Enum):
    """系统类型枚举"""
    SHADOW = "shadow"
    SNAPSHOT = "snapshot"
    BACKUP = "backup"
    SYNC = "sync"
    OTHER = "other"

class SystemStatus(Enum):
    """系统状态枚举"""
    RUNNING = "running"
    PAUSED = "paused"
    ERROR = "error"
    STOPPED = "stopped"
    UNKNOWN = "unknown"

class SystemMonitor:
    """系统监控类"""

    def __init__(self):
        self.systems = {}
        self.performance_metrics = defaultdict(dict)
        self.status_history = defaultdict(lambda: deque(maxlen=100))
        self.lock = threading.Lock()
        self.is_running = False
        self.monitor_thread = None
        self.monitor_interval = 60

        logger.info("初始化系统监控")

    def register_system(self, system_id, system_type, system_instance=None):
        """注册一个系统到监控中"""
        with self.lock:
            self.systems[system_id] = {
                "type": system_type,
                "instance": system_instance,
                "last_status": SystemStatus.UNKNOWN,
                "last_update": time.time()
            }
            logger.info(f"注册系统: {system_id}, 类型: {system_type}")

    def unregister_system(self, system_id):
        """从监控中注销一个系统"""
        with self.lock:
            if system_id in self.systems:
                del self.systems[system_id]
                del self.performance_metrics[system_id]
                del self.status_history[system_id]
                logger.info(f"注销系统: {system_id}")

    def update_system_status(self, system_id, status, metrics=None):
        """更新系统状态和性能指标"""
        with self.lock:
            if system_id not in self.systems:
                logger.warning(f"更新状态失败: 系统 {system_id} 未注册")
                return False

            self.systems[system_id]["last_status"] = status
            self.systems[system_id]["last_update"] = time.time()

            if metrics:
                self.performance_metrics[system_id].update(metrics)

            self.status_history[system_id].append({
                "timestamp": time.time(),
                "status": status,
                "metrics": metrics
            })

            logger.debug(f"更新系统状态: {system_id}, 状态: {status}, 指标: {metrics}")
            return True

    def get_system_status(self, system_id):
        """获取系统状态"""
        with self.lock:
            if system_id not in self.systems:
                return None

            return {
                "type": self.systems[system_id]["type"],
                "status": self.systems[system_id]["last_status"],
                "last_update": self.systems[system_id]["last_update"],
                "metrics": self.performance_metrics.get(system_id, {})
            }

    def get_all_system_status(self):
        """获取所有系统状态"""
        with self.lock:
            all_status = {}
            for system_id in self.systems:
                all_status[system_id] = self.get_system_status(system_id)
            return all_status

    def get_system_history(self, system_id, limit=20):
        """获取系统历史状态"""
        with self.lock:
            if system_id not in self.status_history:
                return []
            return list(self.status_history[system_id])[-limit:]

    def start(self):
        """启动系统监控"""
        if self.is_running:
            logger.warning("系统监控已在运行")
            return

        self.is_running = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()

        logger.info("启动系统监控")

    def stop(self):
        """停止系统监控"""
        if not self.is_running:
            logger.warning("系统监控未在运行")
            return

        self.is_running = False
        if self.monitor_thread:
            self.monitor_thread.join()

        logger.info("停止系统监控")

    def _monitor_loop(self):
        """监控循环"""
        while self.is_running:
            try:
                with self.lock:
                    for system_id, system_info in self.systems.items():
                        if system_info["instance"]:
                            try:
                                if hasattr(system_info["instance"], "get_status"):
                                    status = system_info["instance"].get_status()
                                    self.update_system_status(system_id, SystemStatus.RUNNING, status)

                                if hasattr(system_info["instance"], "get_performance_metrics"):
                                    metrics = system_info["instance"].get_performance_metrics()
                                    self.performance_metrics[system_id].update(metrics)
                            except Exception as e:
                                logger.error(f"获取系统状态失败: {system_id}, 错误: {str(e)}")
                                self.update_system_status(system_id, SystemStatus.ERROR, {"error": str(e)})
            except Exception as e:
                logger.error(f"监控循环出错: {str(e)}")

            self._save_monitor_data()

            time.sleep(self.monitor_interval)

    def _save_monitor_data(self):
        """保存监控数据到文件"""
        try:
            with open('system_monitor_data.json', 'w', encoding='utf-8') as f:
                data = {
                    "timestamp": time.time(),
                    "systems": self.get_all_system_status(),
                    "status_history": {}
                }
                for system_id in self.status_history:
                    data["status_history"][system_id] = list(self.status_history[system_id])[-10:]

                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存监控数据失败: {str(e)}")

    def generate_report(self, report_type="summary"):
        """生成系统监控报告"""
        with self.lock:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            if report_type == "summary":
                report = {
                    "timestamp": timestamp,
                    "total_systems": len(self.systems),
                    "system_status": {},
                    "performance_summary": {}
                }

                status_counts = defaultdict(int)
                for system_id, system_info in self.systems.items():
                    status = system_info["last_status"]
                    status_counts[status] += 1
                    report["system_status"][system_id] = {
                        "type": system_info["type"],
                        "status": system_info["last_status"].value if isinstance(system_info["last_status"], SystemStatus) else system_info["last_status"],
                        "last_update": system_info["last_update"]
                    }

                report["status_counts"] = {k.value if isinstance(k, SystemStatus) else k: v for k, v in status_counts.items()}

                for system_id, metrics in self.performance_metrics.items():
                    if metrics:
                        report["performance_summary"][system_id] = {
                            "total_processed": metrics.get("total_processed", 0),
                        }

            elif report_type == "detailed":
                report = {
                    "timestamp": timestamp,
                    "systems": self.get_all_system_status(),
                    "status_history": {}
                }
                for system_id in self.status_history:
                    report["status_history"][system_id] = list(self.status_history[system_id])

            return report

    def export_report(self, report_type="summary", file_path=None):
        """导出监控报告到文件"""
        report = self.generate_report(report_type)

        if not file_path:
            file_path = f"system_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            logger.info(f"导出报告成功: {file_path}")
            return file_path
        except Exception as e:
            logger.error(f"导出报告失败: {str(e)}")
            return None

_system_monitor = None

def get_system_monitor():
    """获取全局系统监控实例"""
    global _system_monitor
    if _system_monitor is None:
        _system_monitor = SystemMonitor()
    return _system_monitor

if __name__ == "__main__":
    monitor = SystemMonitor()

    monitor.register_system("shadow_1", SystemType.SHADOW)
    monitor.register_system("snapshot_1", SystemType.SNAPSHOT)
    monitor.register_system("backup_1", SystemType.BACKUP)
    monitor.register_system("sync_1", SystemType.SYNC)

    monitor.update_system_status("shadow_1", SystemStatus.RUNNING, {"shadow_count": 10, "average_size": 512})
    monitor.update_system_status("snapshot_1", SystemStatus.RUNNING, {"snapshot_count": 50, "average_size": 1024})
    monitor.update_system_status("backup_1", SystemStatus.PAUSED)
    monitor.update_system_status("sync_1", SystemStatus.RUNNING, {"sync_rate": 1000, "conflicts": 0})

    summary_report = monitor.generate_report("summary")
    print("摘要报告:")
    print(json.dumps(summary_report, ensure_ascii=False, indent=2))

    monitor.export_report("detailed")

    monitor.start()
    try:
        time.sleep(10)
    except KeyboardInterrupt:
        pass

    monitor.stop()
    print("系统监控已停止")
