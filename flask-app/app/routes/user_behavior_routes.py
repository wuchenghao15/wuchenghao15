#!/usr/bin/env python3
"""
用户行为监控API路由 - 提供行为记录和异常警报接口
"""

from flask import Blueprint, jsonify, request
from ..services.user_behavior_service import (
    init_behavior_monitor,
    create_behavior_monitor_employee,
    get_behavior_monitor_employee,
    log_behavior,
    get_behavior_stats,
    get_recent_behaviors,
    get_pending_alerts,
    get_blocked_ips,
    acknowledge_alert,
    resolve_alert,
    unblock_ip,
    is_ip_blocked
)

behavior_bp = Blueprint('behavior', __name__, url_prefix='/api/behavior')


@behavior_bp.route('/employee', methods=['GET'])
def employee_info():
    """获取行为监控AI员工信息"""
    employee = get_behavior_monitor_employee()
    if employee:
        return jsonify({
            'status': 'success',
            'data': employee
        })
    return jsonify({
        'status': 'error',
        'message': '行为监控员工不存在'
    }), 404


@behavior_bp.route('/log', methods=['POST'])
def log_behavior_endpoint():
    """记录用户行为"""
    data = request.get_json() or {}
    
    behavior_id = log_behavior(
        user_id=data.get('user_id'),
        username=data.get('username'),
        action=data.get('action'),
        action_type=data.get('action_type'),
        target=data.get('target'),
        details=data.get('details')
    )
    
    if behavior_id:
        return jsonify({
            'status': 'success',
            'behavior_id': behavior_id
        })
    return jsonify({
        'status': 'error',
        'message': '记录行为失败'
    }), 500


@behavior_bp.route('/stats', methods=['GET'])
def stats():
    """获取行为统计"""
    hours = int(request.args.get('hours', 24))
    result = get_behavior_stats(hours)
    return jsonify({
        'status': 'success',
        'data': result
    })


@behavior_bp.route('/recent', methods=['GET'])
def recent_behaviors():
    """获取最近行为记录"""
    limit = int(request.args.get('limit', 50))
    behaviors = get_recent_behaviors(limit)
    return jsonify({
        'status': 'success',
        'data': behaviors,
        'count': len(behaviors)
    })


@behavior_bp.route('/alerts', methods=['GET'])
def alerts():
    """获取未处理警报"""
    limit = int(request.args.get('limit', 50))
    alert_level = request.args.get('level')
    alerts = get_pending_alerts(limit, alert_level)
    return jsonify({
        'status': 'success',
        'data': alerts,
        'count': len(alerts)
    })


@behavior_bp.route('/alerts/<alert_id>/acknowledge', methods=['POST'])
def acknowledge_alert_endpoint(alert_id):
    """确认警报"""
    data = request.get_json() or {}
    acknowledged_by = data.get('acknowledged_by', 'system')
    
    success = acknowledge_alert(alert_id, acknowledged_by)
    return jsonify({
        'status': 'success' if success else 'error',
        'message': '警报已确认' if success else '确认失败'
    })


@behavior_bp.route('/alerts/<alert_id>/resolve', methods=['POST'])
def resolve_alert_endpoint(alert_id):
    """解决警报"""
    data = request.get_json() or {}
    resolution_action = data.get('resolution_action', '')
    
    success = resolve_alert(alert_id, resolution_action)
    return jsonify({
        'status': 'success' if success else 'error',
        'message': '警报已解决' if success else '解决失败'
    })


@behavior_bp.route('/blocked-ips', methods=['GET'])
def blocked_ips():
    """获取被封禁IP列表"""
    active_only = request.args.get('active_only', 'true').lower() == 'true'
    ips = get_blocked_ips(active_only)
    return jsonify({
        'status': 'success',
        'data': ips,
        'count': len(ips)
    })


@behavior_bp.route('/blocked-ips/<ip_address>/unblock', methods=['POST'])
def unblock_ip_endpoint(ip_address):
    """解封IP"""
    data = request.get_json() or {}
    unblocked_by = data.get('unblocked_by', 'system')
    
    success = unblock_ip(ip_address, unblocked_by)
    return jsonify({
        'status': 'success' if success else 'error',
        'message': 'IP已解封' if success else '解封失败'
    })


@behavior_bp.route('/ip-check/<ip_address>', methods=['GET'])
def ip_check(ip_address):
    """检查IP是否被封禁"""
    blocked, info = is_ip_blocked(ip_address)
    return jsonify({
        'status': 'success',
        'blocked': blocked,
        'info': info
    })
