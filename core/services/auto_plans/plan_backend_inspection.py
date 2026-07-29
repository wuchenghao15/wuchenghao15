# -*- coding: utf-8 -*-
"""后端巡检计划 - 自动巡检后端服务疾患"""

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
    """后端巡检疾患计划

    定期巡检后端服务健康状态，包括：
    - 端口可达性检查
    - 数据库连接池状态
    - 磁盘空间监控
    - Python 进程监控
    - 异常日志扫描
    """

    plan_id = 'backend_inspection'
    name = '后端巡检计划'
    description = '自动巡检后端服务健康状态、端口、数据库、磁盘、进程'
    category = 'maintenance'
    interval_seconds = 300  # 每 5 分钟

    def execute(self) -> PlanResult:
        results: Dict[str, Any] = {
            'port_check': self._check_port(),
            'db_pool': self._check_database(),
            'disk_space': self._check_disk_space(),
            'process_monitor': self._check_processes(),
            'error_scan': self._scan_error_logs(),
        }

        alerts = []
        for name, result in results.items():
            if not result.get('success', True):
                alerts.append(f'{name}: {result.get("error", "unknown")}')

        return PlanResult(
            plan_id=self.plan_id,
            success=len(alerts) == 0,
            message=f'后端巡检完成: {len(alerts)} 项告警',
            data=results,
            errors=alerts,
        )

    def _check_port(self) -> Dict[str, Any]:
        """检查服务端口可达性"""
        try:
            port = 8888
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3)
            result = sock.connect_ex(('127.0.0.1', port))
            sock.close()
            return {
                'success': result == 0,
                'port': port,
                'reachable': result == 0,
                'latency_ms': result,
            }
        except Exception as e:
            return {'success': False, 'error': str(e), 'port': 8888}

    def _check_database(self) -> Dict[str, Any]:
        """检查数据库状态"""
        try:
            db_path = self._find_app_db()
            if not db_path:
                return {'success': False, 'error': '数据库未找到'}

            conn = sqlite3.connect(db_path, timeout=5)
            cursor = conn.cursor()
            cursor.execute("PRAGMA integrity_check")
            integrity = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM system_rules WHERE is_active=1")
            active_rules = cursor.fetchone()[0]

            conn.close()

            return {
                'success': integrity == 'ok',
                'integrity': integrity,
                'active_rules': active_rules,
                'db_size_mb': round(os.path.getsize(db_path) / 1024 / 1024, 2),
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _check_disk_space(self) -> Dict[str, Any]:
        """检查磁盘空间"""
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
                'success': not critical,
                'total_gb': round(total / 1024**3, 2),
                'free_gb': round(free / 1024**3, 2),
                'used_percent': used_pct,
                'warning': warning,
                'critical': critical,
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _check_processes(self) -> Dict[str, Any]:
        """检查 Python 进程"""
        try:
            result = subprocess.run(
                ['ps', 'aux'],
                capture_output=True, text=True, timeout=10
            )
            lines = result.stdout.strip().split('\n')
            python_procs = [l for l in lines if 'python' in l.lower() and 'MTSCOS' in l]

            return {
                'success': True,
                'mtscos_processes': len(python_procs),
                'total_python': len([l for l in lines if 'python' in l.lower()]),
                'details': python_procs[:10],
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _scan_error_logs(self) -> Dict[str, Any]:
        """扫描最近错误日志"""
        try:
            log_dir = 'logs'
            recent_errors: List[str] = []
            if os.path.isdir(log_dir):
                for fname in sorted(os.listdir(log_dir), reverse=True)[:3]:
                    fp = os.path.join(log_dir, fname)
                    try:
                        with open(fp, 'r', encoding='utf-8') as f:
                            for line in f:
                                if 'ERROR' in line or 'CRITICAL' in line:
                                    recent_errors.append(line.strip()[:200])
                                    if len(recent_errors) >= 5:
                                        break
                        if len(recent_errors) >= 5:
                            break
                    except Exception:
                        pass

            return {
                'success': True,
                'recent_errors': recent_errors,
                'error_count': len(recent_errors),
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}

    @staticmethod
    def _find_app_db() -> str:
        for p in ['data/databases/app.db', 'app.db', 'data/app.db']:
            if os.path.exists(p):
                return p
        return ''
