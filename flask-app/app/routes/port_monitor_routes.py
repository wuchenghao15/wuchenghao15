#!/usr/bin/env python3
"""
端口监控API路由 - 提供端口状态监控和修复接口
"""

from flask import Blueprint, jsonify, request
from ..services.port_monitor_service import (
    init_port_monitor,
    create_port_monitor_employee,
    get_port_monitor_employee,
    scan_all_ports,
    get_port_status,
    check_port_config_params,
    fix_port_mismatch,
    fix_port_not_running,
    auto_fix_port_issues,
    get_port_stats,
    get_port_status_list,
    get_port_params,
    get_fix_logs,
    sync_port_configs,
    sync_port_params
)

port_monitor_bp = Blueprint('port_monitor', __name__, url_prefix='/api/port-monitor')


@port_monitor_bp.route('/employee', methods=['GET'])
def employee_info():
    """获取端口监控AI员工信息"""
    employee = get_port_monitor_employee()
    if employee:
        return jsonify({
            'status': 'success',
            'data': employee
        })
    return jsonify({
        'status': 'error',
        'message': '端口监控员工不存在'
    }), 404


@port_monitor_bp.route('/scan', methods=['POST'])
def scan_ports():
    """扫描所有端口状态"""
    results = scan_all_ports()
    return jsonify({
        'status': 'success',
        'data': results,
        'count': len(results)
    })


@port_monitor_bp.route('/status', methods=['GET'])
def ports_status():
    """获取所有端口状态"""
    results = get_port_status_list()
    return jsonify({
        'status': 'success',
        'data': results,
        'count': len(results)
    })


@port_monitor_bp.route('/status/<int:port>', methods=['GET'])
def port_status_detail(port):
    """获取单个端口状态"""
    status = get_port_status(port)
    params = get_port_params(port)
    
    return jsonify({
        'status': 'success',
        'data': {
            'port': port,
            **status,
            'params': params
        }
    })


@port_monitor_bp.route('/params/<int:port>', methods=['GET'])
def port_params_detail(port):
    """获取端口参数"""
    params = get_port_params(port)
    return jsonify({
        'status': 'success',
        'data': params,
        'count': len(params),
        'port': port
    })


@port_monitor_bp.route('/params/check/<int:port>', methods=['POST'])
def check_params(port):
    """检查端口参数匹配"""
    params = check_port_config_params(port)
    
    matched = [p for p in params if p['match_status'] == 'matched']
    mismatched = [p for p in params if p['match_status'] == 'mismatched']
    
    return jsonify({
        'status': 'success',
        'data': params,
        'matched_count': len(matched),
        'mismatched_count': len(mismatched),
        'port': port
    })


@port_monitor_bp.route('/fix/mismatch/<int:port>', methods=['POST'])
def fix_mismatch(port):
    """修复端口参数不匹配"""
    fix_id, result, fixes = fix_port_mismatch(port)
    
    return jsonify({
        'status': 'success' if result == 'success' else 'error',
        'fix_id': fix_id,
        'port': port,
        'result': result,
        'fixes': fixes
    })


@port_monitor_bp.route('/fix/start/<int:port>', methods=['POST'])
def fix_start(port):
    """启动端口服务"""
    fix_id, result, action = fix_port_not_running(port)
    
    return jsonify({
        'status': 'success' if result == 'success' else 'error',
        'fix_id': fix_id,
        'port': port,
        'result': result,
        'action': action
    })


@port_monitor_bp.route('/fix/auto', methods=['POST'])
def fix_auto():
    """自动修复所有端口问题"""
    results = auto_fix_port_issues()
    
    success_count = sum(1 for r in results if r['result'] == 'success')
    failed_count = sum(1 for r in results if r['result'] == 'failed')
    
    return jsonify({
        'status': 'success',
        'data': results,
        'summary': {
            'total_issues': len(results),
            'success': success_count,
            'failed': failed_count
        }
    })


@port_monitor_bp.route('/stats', methods=['GET'])
def stats():
    """获取端口监控统计"""
    result = get_port_stats()
    return jsonify({
        'status': 'success',
        'data': result
    })


@port_monitor_bp.route('/logs', methods=['GET'])
def logs():
    """获取修复日志"""
    limit = int(request.args.get('limit', 50))
    logs = get_fix_logs(limit)
    return jsonify({
        'status': 'success',
        'data': logs,
        'count': len(logs)
    })


@port_monitor_bp.route('/sync', methods=['POST'])
def sync_config():
    """同步端口配置"""
    sync_port_configs()
    sync_port_params()
    
    return jsonify({
        'status': 'success',
        'message': '端口配置同步完成'
    })
