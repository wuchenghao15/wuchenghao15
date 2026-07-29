# -*- coding: utf-8 -*-
"""VIKEY 监控安全计划 - VIKEY USB Key 自动监控"""

from __future__ import annotations

import traceback
from datetime import datetime
from typing import Any, Dict

from .scheduler_base import AbstractAutoPlan, PlanResult, register_plan_class


@register_plan_class
class VikeyMonitorPlan(AbstractAutoPlan):
    """VIKEY 监控安全计划

    定期监控 VIKEY USB Key 状态，检测设备插拔、
    系统锁定状态、超级管理员认证状态等。
    """

    plan_id = 'vikey_monitor'
    name = 'VIKEY 监控安全计划'
    description = '自动监控 VIKEY USB Key 状态、设备插拔、系统锁定、认证状态'
    category = 'security'
    interval_seconds = 5  # 每 5 秒

    def execute(self) -> PlanResult:
        results: Dict[str, Any] = {
            'device_scan': self._scan_devices(),
            'lock_state': self._check_lock_state(),
            'admin_status': self._check_admin_auth(),
            'security_log': self._log_security_event(),
        }

        locked = results['lock_state'].get('locked', False)
        devices = results['device_scan'].get('device_count', 0)

        return PlanResult(
            plan_id=self.plan_id,
            success=True,
            message=f'VIKEY监控: {devices}设备, 锁定={locked}',
            data=results,
        )

    def _scan_devices(self) -> Dict[str, Any]:
        """扫描 VIKEY 设备"""
        try:
            try:
                from core.services.vikey_api import get_vikey_api
                api = get_vikey_api()
                devices = api.list_devices()
                return {
                    'success': True,
                    'device_count': len(devices),
                    'devices': [d.get('serial', 'unknown') for d in devices[:5]],
                }
            except ImportError:
                return {'success': True, 'device_count': 0, 'mode': 'no_driver'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _check_lock_state(self) -> Dict[str, Any]:
        """检查系统锁定状态"""
        try:
            try:
                from core.services.vikey_api import get_vikey_api
                api = get_vikey_api()
                lock_state = api.get_lock_state()
                return {
                    'success': True,
                    'locked': lock_state.get('locked', False),
                    'required_serial': lock_state.get('required_serial'),
                    'remaining': lock_state.get('remaining_seconds', 0),
                    'timeout_reached': lock_state.get('timeout_reached', False),
                }
            except ImportError:
                return {'success': True, 'locked': False, 'mode': 'no_driver'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _check_admin_auth(self) -> Dict[str, Any]:
        """检查超级管理员认证状态"""
        try:
            try:
                from core.services.vikey_api import get_vikey_api
                api = get_vikey_api()
                devices = api.list_devices()
                sa_device = None
                for d in devices:
                    binding = d.get('binding', {})
                    if binding.get('username', '').lower() == 'wuchenghao15':
                        sa_device = d
                        break

                return {
                    'success': True,
                    'sa_device_present': sa_device is not None,
                    'sa_serial': sa_device.get('serial') if sa_device else None,
                }
            except ImportError:
                return {'success': True, 'sa_device_present': False, 'mode': 'no_driver'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _log_security_event(self) -> Dict[str, Any]:
        """记录安全事件日志"""
        try:
            try:
                from core.services.vikey_api import get_vikey_api
                api = get_vikey_api()
                logs = api.query_logs(limit=5)
                return {'success': True, 'recent_logs': len(logs)}
            except ImportError:
                return {'success': True, 'logged': True, 'mode': 'no_driver'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
