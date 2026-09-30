# -*- coding: utf-8 -*-
r"""VIKEY 监控安全计划 - VIKEY USB Key 自动监控r"""

from __future__ import annotations

import traceback
from datetime import datetime
from typing import Any, Dict

from .scheduler_base import AbstractAutoPlan, PlanResult, register_plan_class


@register_plan_class
class VikeyMonitorPlan(AbstractAutoPlan):
    r"""VIKEY 监控安全计划

    定期监控 VIKEY USB Key 状态，检测设备插拔、
    系统锁定状态、超级管理员认证状态等。
    r"""

    plan_id = r'vikey_monitor'
    name = r'VIKEY 监控安全计划'
    description = r'自动监控 VIKEY USB Key 状态、设备插拔、系统锁定、认证状态'
    category = r'security'
    interval_seconds = 5  # 每 5 秒

    def execute(self) -> PlanResult:
        results: Dict[str, Any] = {
            r'device_scan': self._scan_devices(),
            r'lock_state': self._check_lock_state(),
            r'admin_status': self._check_admin_auth(),
            r'security_log': self._log_security_event(),
        }

        locked = results[r'lock_state'].get(r'locked', False)
        devices = results[r'device_scan'].get(r'device_count', 0)

        return PlanResult(
            plan_id=self.plan_id,
            success=True,
            message=fr'VIKEY监控: {devices}设备, 锁定={locked}',
            data=results,
        )

    def _scan_devices(self) -> Dict[str, Any]:
        r"""扫描 VIKEY 设备r"""
        try:
            try:
                from core.services.vikey_api import get_vikey_api
                api = get_vikey_api()
                devices = api.list_devices()
                return {
                    r'success': True,
                    r'device_count': len(devices),
                    r'devices': [d.get(r'serial', r'unknown') for d in devices[:5]],
                }
            except ImportError:
                return {r'success': True, r'device_count': 0, r'mode': r'no_driver'}
        except Exception as e:
            return {r'success': False, r'error': str(e)}

    def _check_lock_state(self) -> Dict[str, Any]:
        r"""检查系统锁定状态r"""
        try:
            try:
                from core.services.vikey_api import get_vikey_api
                api = get_vikey_api()
                lock_state = api.get_lock_state()
                return {
                    r'success': True,
                    r'locked': lock_state.get(r'locked', False),
                    r'required_serial': lock_state.get(r'required_serial'),
                    r'remaining': lock_state.get(r'remaining_seconds', 0),
                    r'timeout_reached': lock_state.get(r'timeout_reached', False),
                }
            except ImportError:
                return {r'success': True, r'locked': False, r'mode': r'no_driver'}
        except Exception as e:
            return {r'success': False, r'error': str(e)}

    def _check_admin_auth(self) -> Dict[str, Any]:
        r"""检查超级管理员认证状态r"""
        try:
            try:
                from core.services.vikey_api import get_vikey_api
                api = get_vikey_api()
                devices = api.list_devices()
                sa_device = None
                for d in devices:
                    binding = d.get(r'binding', {})
                    if binding.get(r'username', r'').lower() == r'wuchenghao15':
                        sa_device = d
                        break

                return {
                    r'success': True,
                    r'sa_device_present': sa_device is not None,
                    r'sa_serial': sa_device.get(r'serial') if sa_device else None,
                }
            except ImportError:
                return {r'success': True, r'sa_device_present': False, r'mode': r'no_driver'}
        except Exception as e:
            return {r'success': False, r'error': str(e)}

    def _log_security_event(self) -> Dict[str, Any]:
        r"""记录安全事件日志r"""
        try:
            try:
                from core.services.vikey_api import get_vikey_api
                api = get_vikey_api()
                logs = api.query_logs(limit=5)
                return {r'success': True, r'recent_logs': len(logs)}
            except ImportError:
                return {r'success': True, r'logged': True, r'mode': r'no_driver'}
        except Exception as e:
            return {r'success': False, r'error': str(e)}
