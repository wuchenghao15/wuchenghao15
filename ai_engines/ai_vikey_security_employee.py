#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VIKEY安全专家AI员工 - 负责VIKEY设备安全监控、诊断、策略管理和异常预警

功能模块：
  1. VIKEY设备健康监控 - 实时监测设备状态、性能指标
  2. VIKEY安全策略管理 - 制定和执行安全策略
  3. VIKEY密钥生命周期管理 - 密钥生成、轮换、吊销
  4. VIKEY认证审计 - 分析认证日志，检测异常行为
  5. VIKEY异常预警 - 实时检测并预警安全威胁
  6. VIKEY自动修复 - 自动检测并修复设备问题
"""

import os
import sys
import json
import time
import logging
import threading
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai_engines.ai_employee_system import AIEmployee
from core.services.vikey_driver import get_vikey_manager, VikeyError, VIKEY_DRIVER_VERSION

logger = logging.getLogger(__name__)


class AI_VIKEY_Security_Employee(AIEmployee):
    """
    VIKEY安全专家AI员工 - 专业的VIKEY设备安全管理和监控

    核心能力：
    - 设备健康监控：实时监测VIKEY设备状态、性能、存储
    - 安全策略管理：制定访问控制策略、密钥使用策略
    - 密钥生命周期：密钥生成、轮换、备份、吊销
    - 认证审计分析：分析认证日志，检测异常行为模式
    - 异常预警系统：实时检测安全威胁并预警
    - 自动修复能力：检测并自动修复常见问题
    - 智能优化建议：基于数据分析提供优化建议
    """

    def __init__(self, employee_id: str, name: str, employee_type: str = "vikey_security", level: int = 9):
        super().__init__(employee_id, name, employee_type, level)
        self.type = "vikey_security"
        self._running = False
        self._lock = threading.RLock()
        self._monitoring_thread = None
        self._last_health_check = None
        self._health_history: List[Dict] = []
        self._security_alerts: List[Dict] = []
        self._policy_rules: Dict[str, Any] = self._load_default_policies()
        self._monitor_interval = 30
        self._max_alerts = 100
        self._max_history = 500

    def _load_default_policies(self) -> Dict[str, Any]:
        """加载默认安全策略"""
        return {
            'min_pin_length': 6,
            'max_pin_length': 32,
            'pin_retry_limit': 5,
            'puk_retry_limit': 10,
            'session_timeout_seconds': 300,
            'max_bindings_per_user': 5,
            'auto_lock_after_failed_attempts': True,
            'require_vikey_for_super_admin': True,
            'vikey_check_interval_ms': 2000,
            'lock_timeout_seconds': 300,
            'enable_real_time_monitoring': True,
            'enable_auto_repair': True,
            'enable_security_audit': True,
            'max_security_events_per_hour': 1000,
            'alert_on_unauthorized_access': True,
            'alert_on_multiple_failed_attempts': True,
            'alert_on_device_removal': True,
            'key_rotation_days': 90,
            'certificate_expiry_warning_days': 30,
            'storage_warning_percent': 80,
        }

    def start(self):
        """启动VIKEY安全监控"""
        with self._lock:
            if self._running:
                return {'success': True, 'message': 'VIKEY安全专家已在运行'}
            
            self._running = True
            self._monitoring_thread = threading.Thread(
                target=self._monitoring_loop,
                daemon=True,
                name=f'vikey-security-{self.employee_id}'
            )
            self._monitoring_thread.start()
            logger.info(f"VIKEY安全专家 {self.name} 已启动")
            return {'success': True, 'message': f'VIKEY安全专家 {self.name} 已启动'}

    def stop(self):
        """停止VIKEY安全监控"""
        with self._lock:
            self._running = False
        
        if self._monitoring_thread:
            self._monitoring_thread.join(timeout=5)
        
        logger.info(f"VIKEY安全专家 {self.name} 已停止")
        return {'success': True, 'message': f'VIKEY安全专家 {self.name} 已停止'}

    def _monitoring_loop(self):
        """监控主循环"""
        while self._running:
            try:
                self._perform_health_check()
                self._detect_anomalies()
                self._cleanup_old_records()
            except Exception as e:
                logger.error(f"VIKEY安全监控循环错误: {e}")
            
            time.sleep(self._monitor_interval)

    def _perform_health_check(self):
        """执行VIKEY设备健康检查"""
        try:
            mgr = get_vikey_manager()
            devices = mgr.enumerate_devices()
            
            health_data = {
                'timestamp': datetime.now().isoformat(),
                'device_count': len(devices),
                'devices': [],
                'overall_status': 'healthy',
                'issues': [],
            }
            
            for dev in devices:
                device_health = {
                    'serial': dev.get('serial'),
                    'label': dev.get('label'),
                    'role_hint': dev.get('role_hint'),
                    'firmware_version': dev.get('firmware_version'),
                    'pin_retry_left': dev.get('pin_retry_left', 0),
                    'storage_total_kb': dev.get('storage_total_kb', 0),
                    'storage_free_kb': dev.get('storage_free_kb', 0),
                    'status': 'healthy',
                    'warnings': [],
                }
                
                if device_health['pin_retry_left'] <= 2:
                    device_health['status'] = 'warning'
                    device_health['warnings'].append(f'PIN重试次数不足: {device_health["pin_retry_left"]}')
                    health_data['issues'].append({
                        'level': 'warning',
                        'message': f"设备 {dev.get('serial')} PIN重试次数不足",
                        'device_serial': dev.get('serial'),
                    })
                
                if device_health['storage_total_kb'] > 0:
                    used_percent = (1 - device_health['storage_free_kb'] / device_health['storage_total_kb']) * 100
                    if used_percent > self._policy_rules['storage_warning_percent']:
                        device_health['status'] = 'warning'
                        device_health['warnings'].append(f'存储使用率过高: {used_percent:.1f}%')
                
                health_data['devices'].append(device_health)
            
            if len(devices) == 0:
                health_data['overall_status'] = 'critical'
                health_data['issues'].append({
                    'level': 'critical',
                    'message': '未检测到任何VIKEY设备',
                })
            
            self._last_health_check = health_data
            self._health_history.append(health_data)
            
            if len(self._health_history) > self._max_history:
                self._health_history = self._health_history[-self._max_history:]
            
        except Exception as e:
            logger.error(f"VIKEY健康检查失败: {e}")

    def _detect_anomalies(self):
        """检测异常行为"""
        try:
            mgr = get_vikey_manager()
            recent_ops = mgr.list_operations(limit=100)
            
            failed_login_count = sum(1 for op in recent_ops if op.get('operation') == 'login' and not op.get('success'))
            if failed_login_count >= 3:
                self._add_alert({
                    'level': 'warning',
                    'type': 'brute_force_attempt',
                    'message': f'检测到多次登录失败 ({failed_login_count}次)',
                    'timestamp': datetime.now().isoformat(),
                })
            
        except Exception as e:
            logger.error(f"异常检测失败: {e}")

    def _add_alert(self, alert: Dict[str, Any]):
        """添加安全预警"""
        with self._lock:
            self._security_alerts.append(alert)
            if len(self._security_alerts) > self._max_alerts:
                self._security_alerts = self._security_alerts[-self._max_alerts:]
            
        logger.warning(f"VIKEY安全预警 [{alert['level']}]: {alert['message']}")

    def _cleanup_old_records(self):
        """清理旧记录"""
        cutoff_time = datetime.now() - timedelta(hours=24)
        self._health_history = [
            h for h in self._health_history 
            if datetime.fromisoformat(h['timestamp']) > cutoff_time
        ]
        
        self._security_alerts = [
            a for a in self._security_alerts 
            if datetime.fromisoformat(a['timestamp']) > cutoff_time
        ]

    def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """处理请求"""
        self.last_active = datetime.now().isoformat()
        request_type = data.get("type", "")
        
        handlers = {
            'health_check': self.handle_health_check,
            'get_alerts': self.handle_get_alerts,
            'get_policy': self.handle_get_policy,
            'update_policy': self.handle_update_policy,
            'key_rotation': self.handle_key_rotation,
            'audit_logs': self.handle_audit_logs,
            'anomaly_detection': self.handle_anomaly_detection,
            'auto_repair': self.handle_auto_repair,
            'generate_report': self.handle_generate_report,
            'device_info': self.handle_device_info,
            'certificate_check': self.handle_certificate_check,
            'binding_audit': self.handle_binding_audit,
        }
        
        handler = handlers.get(request_type)
        if handler:
            return handler(data)
        else:
            return super().execute_task(data)

    def handle_health_check(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理VIKEY健康检查任务"""
        self._perform_health_check()
        
        if self._last_health_check:
            return {
                "success": True,
                "message": "VIKEY健康检查完成",
                "data": self._last_health_check,
                "engine_version": VIKEY_DRIVER_VERSION,
            }
        return {
            "success": False,
            "message": "健康检查数据不可用",
        }

    def handle_get_alerts(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理获取安全预警任务"""
        limit = task_data.get('limit', 20)
        level = task_data.get('level', '')
        
        alerts = self._security_alerts
        if level:
            alerts = [a for a in alerts if a.get('level') == level]
        
        alerts = alerts[-limit:]
        
        return {
            "success": True,
            "message": f"获取到 {len(alerts)} 条安全预警",
            "alerts": alerts,
            "total_alerts": len(self._security_alerts),
        }

    def handle_get_policy(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理获取安全策略任务"""
        return {
            "success": True,
            "message": "获取安全策略成功",
            "policy": self._policy_rules,
        }

    def handle_update_policy(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理更新安全策略任务"""
        new_policy = task_data.get('policy', {})
        
        for key, value in new_policy.items():
            if key in self._policy_rules:
                self._policy_rules[key] = value
        
        return {
            "success": True,
            "message": "安全策略已更新",
            "policy": self._policy_rules,
        }

    def handle_key_rotation(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理密钥轮换任务"""
        serial = task_data.get('serial', '')
        key_id = task_data.get('key_id', '')
        algo = task_data.get('algo', 'SM2')
        
        if not serial:
            return {"success": False, "message": "缺少设备序列号"}
        
        try:
            mgr = get_vikey_manager()
            
            if key_id:
                mgr.open_device(serial)
                
                new_key = mgr.generate_keypair(serial, f"{key_id}_new", algo)
                
                old_keys = mgr.list_keys(serial)
                old_key_info = next((k for k in old_keys if k.get('key_id') == key_id), None)
                
                mgr.close_device(serial)
                
                return {
                    "success": True,
                    "message": "密钥轮换成功",
                    "old_key": old_key_info,
                    "new_key": new_key,
                }
            else:
                mgr.open_device(serial)
                keys = mgr.list_keys(serial)
                rotated_count = 0
                
                for key in keys:
                    if key.get('algo') in ('SM2', 'RSA2048', 'RSA4096'):
                        mgr.generate_keypair(serial, f"{key['key_id']}_rotated_{int(time.time())}", algo)
                        rotated_count += 1
                
                mgr.close_device(serial)
                
                return {
                    "success": True,
                    "message": f"成功轮换 {rotated_count} 个密钥",
                    "rotated_count": rotated_count,
                }
                
        except VikeyError as e:
            return {"success": False, "message": f"密钥轮换失败: {e}"}
        except Exception as e:
            return {"success": False, "message": f"密钥轮换异常: {e}"}

    def handle_audit_logs(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理审计日志任务"""
        limit = task_data.get('limit', 100)
        serial = task_data.get('serial', '')
        operation = task_data.get('operation', '')
        
        try:
            mgr = get_vikey_manager()
            logs = mgr.list_operations(limit=limit, serial=serial, operation=operation)
            
            success_count = sum(1 for log in logs if log.get('success'))
            fail_count = len(logs) - success_count
            
            analysis = {
                'total_operations': len(logs),
                'success_rate': (success_count / len(logs)) * 100 if logs else 0,
                'operation_types': {},
            }
            
            for log in logs:
                op_type = log.get('operation', 'unknown')
                analysis['operation_types'][op_type] = analysis['operation_types'].get(op_type, 0) + 1
            
            return {
                "success": True,
                "message": "审计日志分析完成",
                "logs": logs,
                "analysis": analysis,
            }
            
        except Exception as e:
            return {"success": False, "message": f"审计日志获取失败: {e}"}

    def handle_anomaly_detection(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理异常检测任务"""
        self._detect_anomalies()
        
        alerts = self._security_alerts
        critical_alerts = [a for a in alerts if a.get('level') == 'critical']
        warning_alerts = [a for a in alerts if a.get('level') == 'warning']
        
        return {
            "success": True,
            "message": "异常检测完成",
            "critical_alerts": critical_alerts,
            "warning_alerts": warning_alerts,
            "total_alerts": len(alerts),
        }

    def handle_auto_repair(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理自动修复任务"""
        serial = task_data.get('serial', '')
        repair_type = task_data.get('repair_type', 'all')
        
        try:
            mgr = get_vikey_manager()
            devices = mgr.enumerate_devices()
            
            if serial:
                device = next((d for d in devices if d.get('serial') == serial), None)
                if not device:
                    return {"success": False, "message": f"未找到设备: {serial}"}
                
                return self._repair_device(serial, device, repair_type)
            else:
                results = []
                for device in devices:
                    result = self._repair_device(device['serial'], device, repair_type)
                    results.append(result)
                
                success_count = sum(1 for r in results if r.get('success'))
                
                return {
                    "success": True,
                    "message": f"批量修复完成: {success_count}/{len(devices)} 成功",
                    "results": results,
                }
                
        except Exception as e:
            return {"success": False, "message": f"自动修复失败: {e}"}

    def _repair_device(self, serial: str, device: Dict[str, Any], repair_type: str) -> Dict[str, Any]:
        """修复单个设备"""
        mgr = get_vikey_manager()
        repairs = []
        
        try:
            if repair_type in ('all', 'reset'):
                mgr.reset_device(serial)
                repairs.append('重置设备状态')
            
            if repair_type in ('all', 'health'):
                mgr.open_device(serial)
                keys = mgr.list_keys(serial)
                mgr.close_device(serial)
                repairs.append(f'检查密钥状态: {len(keys)} 个密钥')
            
            return {
                "success": True,
                "serial": serial,
                "repairs": repairs,
                "message": f"设备 {serial} 修复完成",
            }
        except VikeyError as e:
            return {
                "success": False,
                "serial": serial,
                "message": f"修复失败: {e}",
            }

    def handle_generate_report(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理生成安全报告任务"""
        report_type = task_data.get('report_type', 'daily')
        
        report = {
            'generated_at': datetime.now().isoformat(),
            'report_type': report_type,
            'driver_version': VIKEY_DRIVER_VERSION,
            'employee_id': self.employee_id,
            'employee_name': self.name,
            'sections': [],
        }
        
        try:
            mgr = get_vikey_manager()
            devices = mgr.enumerate_devices()
            
            report['sections'].append({
                'title': '设备概览',
                'data': {
                    'total_devices': len(devices),
                    'online_devices': len(devices),
                    'device_details': devices,
                },
            })
            
            bindings = mgr.list_bindings()
            bound_count = sum(1 for b in bindings if b.get('binding_status') == 'bound')
            
            report['sections'].append({
                'title': '绑定管理',
                'data': {
                    'total_bindings': len(bindings),
                    'bound_count': bound_count,
                    'revoked_count': len(bindings) - bound_count,
                },
            })
            
            recent_ops = mgr.list_operations(limit=100)
            success_count = sum(1 for op in recent_ops if op.get('success'))
            
            report['sections'].append({
                'title': '操作统计',
                'data': {
                    'total_operations': len(recent_ops),
                    'success_count': success_count,
                    'failure_count': len(recent_ops) - success_count,
                    'success_rate': (success_count / len(recent_ops)) * 100 if recent_ops else 0,
                },
            })
            
            report['sections'].append({
                'title': '安全策略',
                'data': self._policy_rules,
            })
            
            report['sections'].append({
                'title': '安全预警',
                'data': {
                    'total_alerts': len(self._security_alerts),
                    'recent_alerts': self._security_alerts[-10:],
                },
            })
            
            return {
                "success": True,
                "message": "安全报告生成完成",
                "report": report,
            }
            
        except Exception as e:
            return {"success": False, "message": f"生成报告失败: {e}"}

    def handle_device_info(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理获取设备信息任务"""
        serial = task_data.get('serial', '')
        
        try:
            mgr = get_vikey_manager()
            
            if serial:
                devices = mgr.enumerate_devices()
                device = next((d for d in devices if d.get('serial') == serial), None)
                
                if not device:
                    return {"success": False, "message": f"未找到设备: {serial}"}
                
                mgr.open_device(serial)
                keys = mgr.list_keys(serial)
                certs = mgr.list_certificates(serial)
                mgr.close_device(serial)
                
                return {
                    "success": True,
                    "message": f"获取设备 {serial} 信息成功",
                    "device": device,
                    "keys": keys,
                    "certificates": certs,
                }
            else:
                devices = mgr.enumerate_devices()
                device_details = []
                
                for device in devices:
                    mgr.open_device(device['serial'])
                    keys = mgr.list_keys(device['serial'])
                    certs = mgr.list_certificates(device['serial'])
                    mgr.close_device(device['serial'])
                    
                    device_details.append({
                        'device': device,
                        'keys': keys,
                        'certificates': certs,
                    })
                
                return {
                    "success": True,
                    "message": f"获取 {len(devices)} 个设备信息",
                    "devices": device_details,
                }
                
        except VikeyError as e:
            return {"success": False, "message": f"获取设备信息失败: {e}"}
        except Exception as e:
            return {"success": False, "message": f"获取设备信息异常: {e}"}

    def handle_certificate_check(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理证书检查任务"""
        serial = task_data.get('serial', '')
        
        try:
            mgr = get_vikey_manager()
            
            if serial:
                certs = mgr.list_certificates(serial)
            else:
                certs = []
                devices = mgr.enumerate_devices()
                for device in devices:
                    device_certs = mgr.list_certificates(device['serial'])
                    certs.extend(device_certs)
            
            expiring_soon = []
            expired = []
            valid = []
            
            for cert in certs:
                not_after = cert.get('not_after', '')
                if not_after:
                    try:
                        expiry_date = datetime.strptime(not_after, "%Y-%m-%d %H:%M:%S")
                        days_until_expiry = (expiry_date - datetime.now()).days
                        
                        if days_until_expiry < 0:
                            expired.append(cert)
                        elif days_until_expiry <= self._policy_rules['certificate_expiry_warning_days']:
                            expiring_soon.append(cert)
                        else:
                            valid.append(cert)
                    except:
                        valid.append(cert)
                else:
                    valid.append(cert)
            
            return {
                "success": True,
                "message": "证书检查完成",
                "total_certificates": len(certs),
                "valid": valid,
                "expiring_soon": expiring_soon,
                "expired": expired,
            }
            
        except Exception as e:
            return {"success": False, "message": f"证书检查失败: {e}"}

    def handle_binding_audit(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理绑定审计任务"""
        try:
            mgr = get_vikey_manager()
            bindings = mgr.list_bindings()
            
            audit_results = {
                'total_bindings': len(bindings),
                'bound': [],
                'revoked': [],
                'issues': [],
            }
            
            user_binding_counts = {}
            
            for binding in bindings:
                status = binding.get('binding_status', '')
                username = binding.get('username', '')
                
                if status == 'bound':
                    audit_results['bound'].append(binding)
                    user_binding_counts[username] = user_binding_counts.get(username, 0) + 1
                    
                    if user_binding_counts[username] > self._policy_rules['max_bindings_per_user']:
                        audit_results['issues'].append({
                            'level': 'warning',
                            'message': f"用户 {username} 绑定设备过多 ({user_binding_counts[username]}个)",
                            'binding': binding,
                        })
                else:
                    audit_results['revoked'].append(binding)
            
            return {
                "success": True,
                "message": "绑定审计完成",
                "audit": audit_results,
            }
            
        except Exception as e:
            return {"success": False, "message": f"绑定审计失败: {e}"}

    def get_status(self) -> Dict[str, Any]:
        """获取员工状态"""
        return {
            "employee_id": self.employee_id,
            "name": self.name,
            "type": self.type,
            "level": self.level,
            "status": "running" if self._running else "stopped",
            "last_active": self.last_active,
            "last_health_check": self._last_health_check.get('timestamp') if self._last_health_check else None,
            "device_count": self._last_health_check.get('device_count', 0) if self._last_health_check else 0,
            "overall_status": self._last_health_check.get('overall_status', 'unknown') if self._last_health_check else 'unknown',
            "alert_count": len(self._security_alerts),
            "history_count": len(self._health_history),
            "engine_version": VIKEY_DRIVER_VERSION,
        }

    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "employee_id": self.employee_id,
            "name": self.name,
            "type": self.type,
            "health_checks": len(self._health_history),
            "alerts": len(self._security_alerts),
            "policy_rules_count": len(self._policy_rules),
            "monitor_interval": self._monitor_interval,
            "is_running": self._running,
        }