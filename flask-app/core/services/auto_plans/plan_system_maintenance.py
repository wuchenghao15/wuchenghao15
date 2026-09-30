# -*- coding: utf-8 -*-
r"""系统维护计划 - 自动维护系统核心功能r"""

from __future__ import annotations

import os
import sqlite3
import traceback
from datetime import datetime
from typing import Any, Dict

from .scheduler_base import AbstractAutoPlan, PlanResult, register_plan_class


@register_plan_class
class SystemMaintenancePlan(AbstractAutoPlan):
    r"""自动维护系统计划

    定期执行系统健康检查、缓存清理、日志轮转、临时文件清理等维护任务。
    r"""

    plan_id = r'system_maintenance'
    name = r'系统维护计划'
    description = r'自动执行系统健康检查、缓存清理、日志轮转、临时文件清理等维护任务'
    category = r'maintenance'
    interval_seconds = 7200  # 每 2 小时

    def execute(self) -> PlanResult:
        results: Dict[str, Any] = {
            r'health_check': self._check_system_health(),
            r'cache_cleanup': self._cleanup_cache(),
            r'temp_cleanup': self._cleanup_temp_files(),
            r'db_vacuum': self._vacuum_database(),
            r'log_rotate': self._rotate_logs(),
        }

        errors = []
        success_count = sum(1 for r in results.values() if r.get(r'success'))
        total = len(results)

        return PlanResult(
            plan_id=self.plan_id,
            success=success_count > 0,
            message=fr'系统维护完成: {success_count}/{total} 项成功',
            data=results,
            errors=errors,
        )

    def _check_system_health(self) -> Dict[str, Any]:
        r"""系统健康检查r"""
        try:
            db_path = self._find_app_db()
            if db_path and os.path.exists(db_path):
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                cursor.execute(r"PRAGMA integrity_check")
                integrity = cursor.fetchone()[0]
                cursor.execute(r"SELECT COUNT(*) FROM system_rules WHERE is_active=1")
                active_rules = cursor.fetchone()[0]
                conn.close()
                return {r'success': integrity == r'ok', r'integrity': integrity, r'active_rules': active_rules}
            return {r'success': False, r'message': r'数据库未找到'}
        except Exception as e:
            return {r'success': False, r'error': str(e)}

    def _cleanup_cache(self) -> Dict[str, Any]:
        r"""清理缓存文件r"""
        try:
            cache_dirs = [
                r'data/cache', r'cache', r'tmp/cache',
                r'data/tmp', r'tmp',
            ]
            cleaned = 0
            for d in cache_dirs:
                if os.path.isdir(d):
                    for root, dirs, files in os.walk(d):
                        for f in files:
                            fp = os.path.join(root, f)
                            if os.path.getmtime(fp) < __import__(r'time').time() - 3600:
                                try:
                                    os.remove(fp)
                                    cleaned += 1
                                except Exception:
                                    pass
            return {r'success': True, r'files_cleaned': cleaned}
        except Exception as e:
            return {r'success': False, r'error': str(e)}

    def _cleanup_temp_files(self) -> Dict[str, Any]:
        r"""清理根目录临时文件r"""
        try:
            patterns = [r'.tmp', r'.chk']
            cleaned = 0
            for pattern in patterns:
                for f in os.listdir(r'.'):
                    if os.path.isfile(f) and f.endswith(pattern):
                        try:
                            os.remove(f)
                            cleaned += 1
                        except Exception:
                            pass
            return {r'success': True, r'files_cleaned': cleaned}
        except Exception as e:
            return {r'success': False, r'error': str(e)}

    def _vacuum_database(self) -> Dict[str, Any]:
        r"""数据库 VACUUM 优化r"""
        try:
            db_path = self._find_app_db()
            if db_path and os.path.exists(db_path):
                conn = sqlite3.connect(db_path)
                conn.execute(r"PRAGMA wal_checkpoint(TRUNCATE)")
                conn.isolation_level = None
                conn.execute(r"VACUUM")
                conn.close()
                return {r'success': True, r'action': r'vacuum'}
            return {r'success': False, r'message': r'数据库未找到'}
        except Exception as e:
            return {r'success': False, r'error': str(e)}

    def _rotate_logs(self) -> Dict[str, Any]:
        r"""日志轮转r"""
        try:
            log_dir = r'logs'
            if os.path.isdir(log_dir):
                count = 0
                for f in os.listdir(log_dir):
                    fp = os.path.join(log_dir, f)
                    if os.path.getmtime(fp) < __import__(r'time').time() - 7 * 86400:
                        try:
                            os.remove(fp)
                            count += 1
                        except Exception:
                            pass
                return {r'success': True, r'logs_removed': count}
            return {r'success': True, r'logs_removed': 0, r'message': r'无日志目录'}
        except Exception as e:
            return {r'success': False, r'error': str(e)}

    @staticmethod
    def _find_app_db() -> str:
        for p in [r'data/databases/app.db', r'app.db', r'data/app.db']:
            if os.path.exists(p):
                return p
        return r''
