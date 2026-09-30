# -*- coding: utf-8 -*-
r"""后端巡检计划 - 自动巡检后端服务疾患r"""

from __future__ import annotations

import os
import socket
import sqlite3
import subprocess
import traceback
from datetime import datetime
from typing import Any, Dict, List

from .scheduler_base import AbstractAutoPlan, PlanResult, register_plan_class


@register_plan_class
class BackendInspectionPlan(AbstractAutoPlan):
    r"""后端巡检疾患计划

    定期巡检后端服务健康状态，包括：
    - 端口可达性检查
    - 数据库连接池状态
    - 磁盘空间监控
    - Python 进程监控
    - 异常日志扫描
    r"""

    plan_id = r'backend_inspection'
    name = r'后端巡检计划'
    description = r'自动巡检后端服务健康状态、端口、数据库、磁盘、进程'
    category = r'maintenance'
    interval_seconds = 300  # 每 5 分钟

    def execute(self) -> PlanResult:
        results: Dict[str, Any] = {
            r'port_check': self._check_port(),
            r'db_pool': self._check_database(),
            r'disk_space': self._check_disk_space(),
            r'process_monitor': self._check_processes(),
            r'error_scan': self._scan_error_logs(),
        }

        alerts = []
        for name, result in results.items():
            if not result.get(r'success', True):
                alerts.append(f'{name}: {result.get(r"error", r"unknown")}r')

        return PlanResult(
            plan_id=self.plan_id,
            success=len(alerts) == 0,
            message=f'后端巡检完成: {len(alerts)} 项告警',
            data=results,
            errors=alerts,
        )

    def _check_port(self) -> Dict[str, Any]:
        r"""检查服务端口可达性r"""
        try:
            port = 8888
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3)
            result = sock.connect_ex((r'127.0.0.1', port))
            sock.close()
            return {
                r'success': result == 0,
                r'port': port,
                r'reachable': result == 0,
                r'latency_ms': result,
            }
        except Exception as e:
            return {r'success': False, r'error': str(e), r'port': 8888}

    def _check_database(self) -> Dict[str, Any]:
        r"""检查数据库状态r"""
        try:
            db_path = self._find_app_db()
            if not db_path:
                return {r'success': False, r'error': r'数据库未找到'}

            conn = sqlite3.connect(db_path, timeout=5)
            cursor = conn.cursor()
            cursor.execute(r"PRAGMA integrity_check")
            integrity = cursor.fetchone()[0]

            cursor.execute(r"SELECT COUNT(*) FROM system_rules WHERE is_active=1")
            active_rules = cursor.fetchone()[0]

            conn.close()

            return {
                r'success': integrity == r'ok',
                r'integrity': integrity,
                r'active_rules': active_rules,
                r'db_size_mb': round(os.path.getsize(db_path) / 1024 / 1024, 2),
            }
        except Exception as e:
            return {r'success': False, r'error': str(e)}

    def _check_disk_space(self) -> Dict[str, Any]:
        r"""检查磁盘空间r"""
        try:
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(
                os.path.dirname(os.path.abspath(__file__))
            )))
            stat = os.statvfs(project_root)
            total = stat.f_frsize * stat.f_blocks
            free = stat.f_frsize * stat.f_bavail
            used_pct = round((1 - free / total) * 100, 1) if total > 0 else 0

            warning = used_pct > 85
            critical = used_pct > 95

            return {
                r'success': not critical,
                r'total_gb': round(total / 1024**3, 2),
                r'free_gb': round(free / 1024**3, 2),
                r'used_percent': used_pct,
                r'warning': warning,
                r'critical': critical,
            }
        except Exception as e:
            return {r'success': False, r'error': str(e)}

    def _check_processes(self) -> Dict[str, Any]:
        r"""检查 Python 进程r"""
        try:
            result = subprocess.run(
                [r'ps', r'aux'],
                capture_output=True, text=True, timeout=10
            )
            lines = result.stdout.strip().split(r'\n')
            python_procs = [l for l in lines if r'python' in l.lower() and r'MTSCOS' in l]

            return {
                r'success': True,
                r'mtscos_processes': len(python_procs),
                r'total_python': len([l for l in lines if r'python' in l.lower()]),
                r'details': python_procs[:10],
            }
        except Exception as e:
            return {r'success': False, r'error': str(e)}

    def _scan_error_logs(self) -> Dict[str, Any]:
        r"""扫描最近错误日志r"""
        try:
            log_dir = r'logs'
            recent_errors: List[str] = []
            if os.path.isdir(log_dir):
                for fname in sorted(os.listdir(log_dir), reverse=True)[:3]:
                    fp = os.path.join(log_dir, fname)
                    try:
                        with open(fp, r'r', encoding=r'utf-8') as f:
                            for line in f:
                                if r'ERROR' in line or r'CRITICAL' in line:
                                    recent_errors.append(line.strip()[:200])
                                    if len(recent_errors) >= 5:
                                        break
                        if len(recent_errors) >= 5:
                            break
                    except Exception:
                        pass

            return {
                r'success': True,
                r'recent_errors': recent_errors,
                r'error_count': len(recent_errors),
            }
        except Exception as e:
            return {r'success': False, r'error': str(e)}

    @staticmethod
    def _find_app_db() -> str:
        for p in [r'data/databases/app.db', r'app.db', r'data/app.db']:
            if os.path.exists(p):
                return p
        return r''
