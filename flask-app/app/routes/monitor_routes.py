#!/usr/bin/env python3
"""
监控API路由 - 提供客户端接入监控和异常查询接口
"""

from flask import Blueprint, jsonify, request
from ..services.client_monitor_service import (
    get_access_stats,
    get_anomalies,
    get_recent_access,
    resolve_anomaly,
    get_monitor_employee
)

monitor_bp = Blueprint('monitor', __name__, url_prefix='/api/monitor')


@monitor_bp.route('/stats', methods=['GET'])
def stats():
    """获取接入统计"""
    hours = int(request.args.get('hours', 24))
    result = get_access_stats(hours)
    return jsonify({
        'status': 'success',
        'data': result
    })


@monitor_bp.route('/anomalies', methods=['GET'])
def anomalies():
    """获取异常列表"""
    limit = int(request.args.get('limit', 50))
    resolved = request.args.get('resolved', 'false').lower() == 'true'
    result = get_anomalies(limit, resolved)
    return jsonify({
        'status': 'success',
        'data': result,
        'count': len(result)
    })


@monitor_bp.route('/access', methods=['GET'])
def access_logs():
    """获取最近接入记录"""
    limit = int(request.args.get('limit', 50))
    result = get_recent_access(limit)
    return jsonify({
        'status': 'success',
        'data': result,
        'count': len(result)
    })


@monitor_bp.route('/anomaly/<anomaly_id>/resolve', methods=['POST'])
def resolve_anomaly_endpoint(anomaly_id):
    """标记异常已解决"""
    data = request.get_json() or {}
    resolver = data.get('resolver', 'system')
    action_taken = data.get('action_taken', '')
    
    success = resolve_anomaly(anomaly_id, resolver, action_taken)
    return jsonify({
        'status': 'success' if success else 'error',
        'message': '异常已解决' if success else '解决失败'
    })


@monitor_bp.route('/employee', methods=['GET'])
def employee_info():
    """获取监控AI员工信息"""
    employee = get_monitor_employee()
    if employee:
        return jsonify({
            'status': 'success',
            'data': employee
        })
    return jsonify({
        'status': 'error',
        'message': '监控员工不存在'
    }), 404
