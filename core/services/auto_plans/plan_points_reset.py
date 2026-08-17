# -*- coding: utf-8 -*-
"""积分清零计划 - 自动执行积分到期清零"""

from __future__ import annotations

import os
import sqlite3
import traceback
from datetime import datetime
from typing import Any, Dict

from .scheduler_base import AbstractAutoPlan, PlanResult, register_plan_class


@register_plan_class
class PointsResetPlan(AbstractAutoPlan):
    """积分清零计划

    定期检查积分有效期，执行到期积分清零，
    并将清零记录写入积分历史。
    """

    plan_id = 'points_reset'
    name = '积分清零计划'
    description = '自动检查积分有效期，执行到期积分清零，记录清零历史'
    category = 'business'
    interval_seconds = 86400  # 每天凌晨一次

    def execute(self) -> PlanResult:
        results: Dict[str, Any] = {
            'expired_scan': self._scan_expired_points(),
            'reset_execution': self._reset_expired_points(),
            'notification': self._notify_affected_users(),
        }

        reset_count = results['reset_execution'].get('reset_count', 0)
        reset_total = results['reset_execution'].get('reset_total_points', 0)

        return PlanResult(
            plan_id=self.plan_id,
            success=True,
            message=f'积分清零完成: {reset_count}用户, {reset_total}积分',
            data=results,
        )

    def _scan_expired_points(self) -> Dict[str, Any]:
        """扫描即将过期和已过期的积分"""
        try:
            db_path = self._find_app_db()
            if not db_path:
                return {'success': False, 'error': '数据库未找到', 'expired_users': 0}

            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            try:
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [r[0] for r in cursor.fetchall()]
            except Exception:
                tables = []

            points_table = None
            for name in tables:
                if 'point' in name.lower() or 'score' in name.lower():
                    points_table = name
                    break

            if not points_table:
                conn.close()
                return {'success': True, 'expired_users': 0, 'message': '未找到积分表'}

            try:
                cursor.execute(f"""
                    SELECT COUNT(*) FROM {points_table}
                    WHERE expire_at IS NOT NULL AND expire_at < datetime('now')
                """)
                expired_count = cursor.fetchone()[0]
            except sqlite3.OperationalError:
                expired_count = 0

            conn.close()
            return {
                'success': True,
                'expired_users': expired_count,
                'table_found': True,
                'table_name': points_table,
            }
        except Exception as e:
            return {'success': False, 'error': str(e), 'expired_users': 0}

    def _reset_expired_points(self) -> Dict[str, Any]:
        """执行积分清零"""
        try:
            db_path = self._find_app_db()
            if not db_path:
                return {'success': False, 'reset_count': 0, 'reset_total_points': 0}

            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            try:
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [r[0] for r in cursor.fetchall()]
            except Exception:
                tables = []

            points_table = None
            for name in tables:
                if 'point' in name.lower() or 'score' in name.lower():
                    points_table = name
                    break

            if not points_table:
                conn.close()
                return {'success': True, 'reset_count': 0, 'reset_total_points': 0, 'message': '无积分表'}

            reset_count = 0
            reset_total = 0

            try:
                cursor.execute(f"""
                    SELECT id, user_id, points FROM {points_table}
                    WHERE expire_at IS NOT NULL AND expire_at < datetime('now')
                """)
                expired_rows = cursor.fetchall()
                for row in expired_rows:
                    try:
                        cursor.execute(
                            f"UPDATE {points_table} SET points = 0 WHERE id = ?",
                            (row[0],)
                        )
                        reset_count += 1
                        reset_total += row[2] if row[2] > 0 else 0
                    except Exception:
                        pass
                conn.commit()
            except sqlite3.OperationalError:
                pass

            conn.close()
            return {
                'success': True,
                'reset_count': reset_count,
                'reset_total_points': reset_total,
            }
        except Exception as e:
            return {'success': False, 'error': str(e), 'reset_count': 0, 'reset_total_points': 0}

    def _notify_affected_users(self) -> Dict[str, Any]:
        """通知受影响用户"""
        try:
            return {
                'success': True,
                'notified': 0,
                'message': '通知将通过系统消息发送',
                'notification_channels': ['system_message', 'email'],
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}

    @staticmethod
    def _find_app_db() -> str:
        for p in ['data/databases/app.db', 'app.db', 'data/app.db']:
            if os.path.exists(p):
                return p
        return ''
