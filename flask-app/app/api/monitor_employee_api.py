# -*- coding: utf-8 -*-
"""AI监控员工API - 智能监控系统所有监控点和功能"""

import logging
logger = logging.getLogger(__name__)

from flask import Blueprint, request, jsonify
from ai_engines.ai_monitor_employee import ai_monitor_employee

monitor_employee_api_bp = Blueprint("monitor_employee_api", __name__)

@monitor_employee_api.route('/api/monitor/employee/info', methods=['GET'])
def get_monitor_employee_info():
    """获取AI监控员工信息"""
    info = {
        'employee_id': ai_monitor_employee.employee_id,
        'name': ai_monitor_employee.name,
        'type': ai_monitor_employee.type,
        'skills': ai_monitor_employee.skills,
        'responsibilities': ai_monitor_employee.responsibilities,
        'status': ai_monitor_employee.status,
        'is_running': ai_monitor_employee.is_running
    }
    return jsonify({'success': True, 'data': info})

@monitor_employee_api.route('/api/monitor/employee/start', methods=['POST'])
def start_monitoring():
    """启动监控"""
    ai_monitor_employee.start_monitoring()
    return jsonify({'success': True, 'message': 'AI监控员工已启动'})

@monitor_employee_api.route('/api/monitor/employee/stop', methods=['POST'])
def stop_monitoring():
    """停止监控"""
    ai_monitor_employee.stop_monitoring()
    return jsonify({'success': True, 'message': 'AI监控员工已停止'})

@monitor_employee_api.route('/api/monitor/employee/status', methods=['GET'])
def get_monitor_status():
    """获取监控状态摘要"""
    status = ai_monitor_employee.get_monitor_status()
    return jsonify({'success': True, 'data': status})

@monitor_employee_api.route('/api/monitor/employee/points', methods=['GET'])
def get_monitor_points():
    """获取所有监控点"""
    point_type = request.args.get('type')
    points = ai_monitor_employee.get_monitor_points(point_type)
    return jsonify({'success': True, 'data': points})

@monitor_employee_api.route('/api/monitor/employee/points/<point_id>', methods=['GET'])
def get_monitor_point(point_id):
    """获取单个监控点详情"""
    point = ai_monitor_employee.get_monitor_point(point_id)
    if not point:
        return jsonify({'success': False, 'message': '监控点不存在'}), 404
    return jsonify({'success': True, 'data': point})

@monitor_employee_api.route('/api/monitor/employee/alerts', methods=['GET'])
def get_alerts():
    """获取告警列表"""
    level = request.args.get('level')
    limit = int(request.args.get('limit', 50))
    alerts = ai_monitor_employee.get_alerts(level, limit)
    return jsonify({'success': True, 'data': alerts})

@monitor_employee_api.route('/api/monitor/employee/alert_stats', methods=['GET'])
def get_alert_stats():
    """获取告警统计"""
    stats = ai_monitor_employee.get_alert_stats()
    return jsonify({'success': True, 'data': stats})

@monitor_employee_api.route('/api/monitor/employee/report', methods=['GET'])
def generate_report():
    """生成监控报告"""
    duration = request.args.get('duration', '1h')
    report = ai_monitor_employee.generate_report(duration)
    return jsonify({'success': True, 'data': report})

@monitor_employee_api.route('/api/monitor/employee/heal', methods=['POST'])
def auto_heal():
    """自动修复问题"""
    result = ai_monitor_employee.auto_heal()
    return jsonify(result)

@monitor_employee_api.route('/api/monitor/employee/trends', methods=['GET'])
def analyze_trends():
    """分析趋势"""
    trends = ai_monitor_employee.analyze_trends()
    return jsonify({'success': True, 'data': trends})

@monitor_employee_api.route('/api/monitor/employee/check', methods=['POST'])
def check_all_points():
    """手动触发检查所有监控点"""
    try:
        ai_monitor_employee._check_all_monitor_points()
        status = ai_monitor_employee.get_monitor_status()
        return jsonify({'success': True, 'message': '检查完成', 'data': status})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@monitor_employee_api.route('/api/monitor/employee/point_types', methods=['GET'])
def get_point_types():
    """获取监控点类型列表"""
    from ai_engines.ai_monitor_employee import MonitorPointType
    types = [pt.value for pt in MonitorPointType]
    return jsonify({'success': True, 'data': types})