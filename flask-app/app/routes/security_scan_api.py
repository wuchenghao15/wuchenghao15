# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
安全扫描API路由
提供安全监控、漏洞扫描、安全评分等功能
"""

from flask import Blueprint, jsonify, request
from app.services.security_monitor_service import security_monitor_service
from app.utils.api_response import success_response, error_response
from app.decorators.auth import login_required, require_admin

security_scan_api = Blueprint('security_scan_api', __name__, url_prefix='/api/security')


@security_scan_api.route('/status', methods=['GET'])
@login_required
@require_admin
def get_security_status():
    """获取安全状态"""
    status = security_monitor_service.get_security_status()
    return success_response(data=status)


@security_scan_api.route('/scan', methods=['POST'])
@login_required
@require_admin
def run_scan():
    """执行安全扫描"""
    result = security_monitor_service.run_manual_scan()
    return success_response(data=result)


@security_scan_api.route('/scan/start', methods=['POST'])
@login_required
@require_admin
def start_scanner():
    """启动安全扫描器"""
    security_monitor_service.start_scanner()
    return success_response(message='安全扫描器已启动')


@security_scan_api.route('/scan/stop', methods=['POST'])
@login_required
@require_admin
def stop_scanner():
    """停止安全扫描器"""
    security_monitor_service.stop_scanner()
    return success_response(message='安全扫描器已停止')


@security_scan_api.route('/vulnerabilities', methods=['GET'])
@login_required
@require_admin
def get_vulnerabilities():
    """获取漏洞列表"""
    limit = request.args.get('limit', 50, type=int)
    vulnerabilities = security_monitor_service.get_recent_vulnerabilities(limit=limit)
    return success_response(data=vulnerabilities)


@security_scan_api.route('/alerts', methods=['GET'])
@login_required
@require_admin
def get_alerts():
    """获取安全警报"""
    status = request.args.get('status')
    alerts = security_monitor_service.get_alerts(status=status)
    return success_response(data=alerts)


@security_scan_api.route('/alerts/<int:alert_id>/acknowledge', methods=['POST'])
@login_required
@require_admin
def acknowledge_alert(alert_id):
    """确认警报"""
    security_monitor_service.acknowledge_alert(alert_id)
    return success_response(message='警报已确认')


@security_scan_api.route('/history', methods=['GET'])
@login_required
@require_admin
def get_scan_history():
    """获取扫描历史"""
    limit = request.args.get('limit', 20, type=int)
    history = security_monitor_service.get_scan_history(limit=limit)
    return success_response(data=history)


@security_scan_api.route('/config', methods=['GET'])
@login_required
@require_admin
def get_config():
    """获取安全监控配置"""
    status = security_monitor_service.get_security_status()
    config = {
        'scan_interval': status.get('scan_interval', 3600),
        'auto_fix_enabled': status.get('auto_fix_enabled', True),
        'alerts_enabled': status.get('alerts_enabled', True)
    }
    return success_response(data=config)


@security_scan_api.route('/config', methods=['PUT'])
@login_required
@require_admin
def update_config():
    """更新安全监控配置"""
    data = request.get_json()
    if not data:
        return error_response('配置数据不能为空')

    security_monitor_service.update_config(data)
    return success_response(message='配置已更新')


@security_scan_api.route('/enable', methods=['POST'])
@login_required
@require_admin
def enable_monitor():
    """启用安全监控"""
    security_monitor_service.enable()
    return success_response(message='安全监控已启用')


@security_scan_api.route('/disable', methods=['POST'])
@login_required
@require_admin
def disable_monitor():
    """禁用安全监控"""
    security_monitor_service.disable()
    return success_response(message='安全监控已禁用')