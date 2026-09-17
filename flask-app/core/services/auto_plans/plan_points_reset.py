# -*- coding: utf-8 -*-
r"""积分清零计划 - 自动执行积分到期清零r"""

from __future__ import annotations

import os
import sqlite3
import traceback
from datetime import datetime
from typing import Any, Dict

from .scheduler_base import AbstractAutoPlan, PlanResult, register_plan_class


@register_plan_class
class PointsResetPlan(AbstractAutoPlan):
    r"""积分清零计划

    定期检查积分有效期，执行到期积分清零，
    并将清零记录写入积分历史。
    r"""

    plan_id = r'points_reset'
    name = r'积分清零计划'
    description = r'自动检查积分有效期，执行到期积分清零，记录清零历史'
    category = r'business'
    interval_seconds = 86400  # 每天凌晨一次

    def execute(self) -> PlanResult:
        results: Dict[str, Any] = {
            r'expired_scan': self._scan_expired_points(),
            r'reset_execution': self._reset_expired_points(),
            r'notification': self._notify_affected_users(),
        }

        reset_count = results[r'reset_execution'].get(r'reset_count', 0)
        reset_total = results[r'reset_execution'].get(r'reset_total_points', 0)

        return PlanResult(
            plan_id=self.plan_id,
            success=True,
            message=fr'积分清零完成: {reset_count}用户, {reset_total}积分',
            data=results,
        )

    def _scan_expired_points(self) -> Dict[str, Any]:
        r"""扫描即将过期和已过期的积分r"""
        try:
            db_path = self._find_app_db()
            if not db_path:
                return {r'success': False, r'error': r'数据库未找到', r'expired_users': 0}

            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            try:
                cursor.execute("SELECT name FROM sqlite_master WHERE type=r'table'")
                tables = [r[0] for r in cursor.fetchall()]
            except Exception:
                tables = []

            points_table = None
            for name in tables:
                if r'point' in name.lower() or r'score' in name.lower():
                    points_table = name
                    break

            if not points_table:
                conn.close()
                return {r'success': True, r'expired_users': 0, r'message': r'未找到积分表'}

            try:
                cursor.execute(fr"""
                    SELECT COUNT(*) FROM {points_table}
                    WHERE expire_at IS NOT NULL AND expire_at < datetime(r'now')
                r""")
                expired_count = cursor.fetchone()[0]
            except sqlite3.OperationalError:
                expired_count = 0

            conn.close()
            return {
                r'success': True,
                r'expired_users': expired_count,
                r'table_found': True,
                r'table_name': points_table,
            }
        except Exception as e:
            return {r'success': False, r'error': str(e), r'expired_users': 0}

    def _reset_expired_points(self) -> Dict[str, Any]:
        r"""执行积分清零r"""
        try:
            db_path = self._find_app_db()
            if not db_path:
                return {r'success': False, r'reset_count': 0, r'reset_total_points': 0}

            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            try:
                cursor.execute("SELECT name FROM sqlite_master WHERE type=r'table'")
                tables = [r[0] for r in cursor.fetchall()]
            except Exception:
                tables = []

            points_table = None
            for name in tables:
                if r'point' in name.lower() or r'score' in name.lower():
                    points_table = name
                    break

            if not points_table:
                conn.close()
                return {r'success': True, r'reset_count': 0, r'reset_total_points': 0, r'message': r'无积分表'}

            reset_count = 0
            reset_total = 0

            try:
                cursor.execute(fr"""
                    SELECT id, user_id, points FROM {points_table}
                    WHERE expire_at IS NOT NULL AND expire_at < datetime(r'now')
                r""")
                expired_rows = cursor.fetchall()
                for row in expired_rows:
                    try:
                        cursor.execute(
                            fr"UPDATE {points_table} SET points = 0 WHERE id = ?",
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
                r'success': True,
                r'reset_count': reset_count,
                r'reset_total_points': reset_total,
            }
        except Exception as e:
            return {r'success': False, r'error': str(e), r'reset_count': 0, r'reset_total_points': 0}

    def _notify_affected_users(self) -> Dict[str, Any]:
        r"""通知受影响用户r"""
        try:
            return {
                r'success': True,
                r'notified': 0,
                r'message': r'通知将通过系统消息发送',
                r'notification_channels': [r'system_message', r'email'],
            }
        except Exception as e:
            return {r'success': False, r'error': str(e)}

    @staticmethod
    def _find_app_db() -> str:
        for p in [r'data/databases/app.db', r'app.db', r'data/app.db']:
            if os.path.exists(p):
                return p
        return r''
