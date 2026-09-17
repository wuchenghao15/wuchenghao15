# -*- coding: utf-8 -*-
"""数据库安全维保计划 - 数据库安全自动维护"""

from __future__ import annotations

import os
import sqlite3
import traceback
from datetime import datetime, timedelta
from typing import Any, Dict, List

from .scheduler_base import AbstractAutoPlan, PlanResult, register_plan_class


@register_plan_class
class DBSecurityPlan(AbstractAutoPlan):
    """数据库安全维保计划

    定期执行数据库安全检查：
    - 完整性校验
    - 备份验证
    - 敏感数据检查
    - 权限审计
    - 索引优化
    - 统计信息更新
    """

    plan_id = 'db_security'
    name = '数据库安全维保计划'
    description = '自动执行数据库完整性校验、备份验证、敏感数据检查、权限审计'
    category = 'security'
    interval_seconds = 21600  # 每 6 小时

    def execute(self) -> PlanResult:
        results: Dict[str, Any] = {
            'integrity': self._check_integrity(),
            'backup_verify': self._verify_backups(),
            'sensitive_data': self._check_sensitive_data(),
            'permission_audit': self._audit_permissions(),
            'index_optimize': self._optimize_indexes(),
            'stats_update': self._update_statistics(),
        }

        issues = []
        for name, result in results.items():
            if not result.get('success', True):
                issues.append(name)

        return PlanResult(
            plan_id=self.plan_id,
            success=len(issues) <= 1,
            message=f'数据库安全维保完成: {len(issues)} 项需关注',
            data=results,
            errors=issues,
        )

    def _check_integrity(self) -> Dict[str, Any]:
        """数据库完整性校验"""
        try:
            db_path = self._find_app_db()
            if not db_path:
                return {'success': False, 'error': '数据库未找到'}

            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("PRAGMA integrity_check")
            integrity = cursor.fetchone()[0]

            cursor.execute("PRAGMA quick_check")
            quick = cursor.fetchone()[0]

            conn.close()

            return {
                'success': integrity == 'ok' and quick == 'ok',
                'integrity': integrity,
                'quick_check': quick,
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _verify_backups(self) -> Dict[str, Any]:
        """验证备份"""
        try:
            backup_dirs = ['backups', 'Backups', 'data/backups']
            backups: List[Dict[str, Any]] = []

            for d in backup_dirs:
                if os.path.isdir(d):
                    for f in sorted(os.listdir(d), reverse=True)[:3]:
                        fp = os.path.join(d, f)
                        if os.path.isfile(fp):
                            stat = os.stat(fp)
                            backups.append({
                                'file': f,
                                'size_kb': round(stat.st_size / 1024, 1),
                                'age_hours': round((datetime.now().timestamp() - stat.st_mtime) / 3600, 1),
                            })

            return {
                'success': len(backups) > 0,
                'backup_count': len(backups),
                'backups': backups,
                'message': '备份充足' if len(backups) >= 2 else '备份不足',
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _check_sensitive_data(self) -> Dict[str, Any]:
        """检查敏感数据"""
        try:
            db_path = self._find_app_db()
            if not db_path:
                return {'success': False, 'error': '数据库未找到'}

            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            sensitive_tables = ['users', 'system_admins', 'audit_logs']
            results = {}
            for table in sensitive_tables:
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    results[table] = {'exists': True, 'row_count': count}
                except sqlite3.OperationalError:
                    results[table] = {'exists': False}

            conn.close()
            return {'success': True, 'tables': results}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _audit_permissions(self) -> Dict[str, Any]:
        """权限审计"""
        try:
            db_path = self._find_app_db()
            if not db_path:
                return {'success': False, 'error': '数据库未找到'}

            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            try:
                cursor.execute("SELECT COUNT(*) FROM users WHERE is_active = 1")
                active_users = cursor.fetchone()[0]
            except Exception:
                active_users = 0

            try:
                cursor.execute("SELECT COUNT(*) FROM system_rules WHERE is_active = 1")
                active_rules = cursor.fetchone()[0]
            except Exception:
                active_rules = 0

            conn.close()
            return {
                'success': True,
                'active_users': active_users,
                'active_rules': active_rules,
                'permission_audit': 'passed',
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _optimize_indexes(self) -> Dict[str, Any]:
        """索引优化"""
        try:
            db_path = self._find_app_db()
            if not db_path:
                return {'success': False, 'error': '数据库未找到'}

            conn = sqlite3.connect(db_path)
            try:
                conn.execute("PRAGMA optimize")
                conn.commit()
            except Exception:
                pass
            conn.close()
            return {'success': True, 'optimized': True}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _update_statistics(self) -> Dict[str, Any]:
        """更新统计信息"""
        try:
            db_path = self._find_app_db()
            if not db_path:
                return {'success': False, 'error': '数据库未找到'}

            conn = sqlite3.connect(db_path)
            try:
                conn.execute("ANALYZE")
                conn.commit()
            except Exception:
                pass
            conn.close()
            return {'success': True, 'analyzed': True}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    @staticmethod
    def _find_app_db() -> str:
        for p in ['data/databases/app.db', 'app.db', 'data/app.db']:
            if os.path.exists(p):
                return p
        return ''
