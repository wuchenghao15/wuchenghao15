#!/usr/bin/env python3
"""
安全监控路由
"""

from flask import Blueprint, render_template, jsonify, request
from app.services.security_service import get_security_service

# 导入用户状态检查装饰器
from app.views.main import check_user_status

security_bp = Blueprint('security', __name__, url_prefix='/security')

@security_bp.route('/')
@check_user_status
def security_dashboard():
    """安全监控仪表盘"""
    return render_template('security/dashboard.html')

@security_bp.route('/events')
@check_user_status
def security_events():
    """安全事件页面"""
    return render_template('security/events.html')

@security_bp.route('/scans')
@check_user_status
def security_scans():
    """安全扫描页面"""
    return render_template('security/scans.html')

@security_bp.route('/config')
@check_user_status
def security_config():
    """安全配置页面"""
    return render_template('security/config.html')

@security_bp.route('/api/events')
@check_user_status
def api_security_events():
    """获取安全事件API"""
    limit = int(request.args.get('limit', 50))
    offset = int(request.args.get('offset', 0))
    
    service = get_security_service()
    events = service.get_security_events(limit=limit, offset=offset)
    
    return jsonify({
        'events': events,
        'total': len(events)
    })

@security_bp.route('/api/scans')
@check_user_status
def api_security_scans():
    """获取安全扫描API"""
    limit = int(request.args.get('limit', 50))
    offset = int(request.args.get('offset', 0))
    
    service = get_security_service()
    scans = service.get_security_scans(limit=limit, offset=offset)
    
    return jsonify({
        'scans': scans,
        'total': len(scans)
    })

@security_bp.route('/api/scan', methods=['POST'])
@check_user_status
def api_start_scan():
    """开始安全扫描API"""
    data = request.get_json()
    scan_type = data.get('type', 'vulnerability')
    target = data.get('target', 'app')
    
    service = get_security_service()
    scan_id = service.start_scan(scan_type, target)
    
    if scan_id:
        return jsonify({
            'success': True,
            'scan_id': scan_id
        })
    else:
        return jsonify({
            'success': False,
            'message': '扫描启动失败'
        }), 500

@security_bp.route('/api/start-monitoring', methods=['POST'])
@check_user_status
def api_start_monitoring():
    """启动安全监控API"""
    service = get_security_service()
    service.start_monitoring()
    
    return jsonify({
        'success': True,
        'message': '安全监控已启动'
    })

@security_bp.route('/api/stop-monitoring', methods=['POST'])
@check_user_status
def api_stop_monitoring():
    """停止安全监控API"""
    service = get_security_service()
    service.stop_monitoring()
    
    return jsonify({
        'success': True,
        'message': '安全监控已停止'
    })

@security_bp.route('/api/ddos-check', methods=['POST'])
@check_user_status
def api_ddos_check():
    """DDoS攻击检查API"""
    data = request.get_json()
    ip_address = data.get('ip_address', request.remote_addr)
    
    service = get_security_service()
    is_attack, message = service.check_ddos_attack(ip_address)
    
    return jsonify({
        'success': True,
        'is_attack': is_attack,
        'message': message,
        'ip_address': ip_address
    })

@security_bp.route('/api/memory-check')
@check_user_status
def api_memory_check():
    """内存溢出检查API"""
    service = get_security_service()
    is_overflow, message = service.check_memory_overflow()
    
    return jsonify({
        'success': True,
        'is_overflow': is_overflow,
        'message': message
    })

@security_bp.route('/api/ddos-config', methods=['GET', 'POST'])
@check_user_status
def api_ddos_config():
    """DDoS防护配置API"""
    service = get_security_service()
    
    if request.method == 'GET':
        return jsonify({
            'success': True,
            'config': service.ddos_protection
        })
    else:
        data = request.get_json()
        if data:
            service.ddos_protection.update(data)
            return jsonify({
                'success': True,
                'message': 'DDoS防护配置已更新',
                'config': service.ddos_protection
            })
        else:
            return jsonify({
                'success': False,
                'message': '无效的配置数据'
            }), 400

@security_bp.route('/api/memory-config', methods=['GET', 'POST'])
@check_user_status
def api_memory_config():
    """内存监控配置API"""
    service = get_security_service()
    
    if request.method == 'GET':
        return jsonify({
            'success': True,
            'config': service.memory_monitoring
        })
    else:
        data = request.get_json()
        if data:
            service.memory_monitoring.update(data)
            return jsonify({
                'success': True,
                'message': '内存监控配置已更新',
                'config': service.memory_monitoring
            })
        else:
            return jsonify({
                'success': False,
                'message': '无效的配置数据'
            }), 400
