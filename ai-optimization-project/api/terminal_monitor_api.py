#!/usr/bin/env python3
"""
终端监控API接口

from flask import Blueprint, jsonify, request
from services.terminal_monitor import terminal_monitor
from utils.logging import logger

terminal_monitor_bp = Blueprint('terminal_monitor', __name__, url_prefix='/api/terminal')

@terminal_monitor_bp.route('/terminals', methods=['GET'])
def get_terminals():
    """获取所有终端信息"""
    try:
        terminals = terminal_monitor.get_terminals()
        return jsonify({
            'success': True,
            'data': terminals,
            'count': len(terminals)
        })
    except Exception as e:
        logger.error(f"获取终端列表失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@terminal_monitor_bp.route('/terminals/<terminal_id>', methods=['GET'])
def get_terminal(terminal_id):
    """获取指定终端信息"""
    try:
        terminal = next((t for t in terminals if t['terminal_id'] == terminal_id), None)
        if not terminal:
            return jsonify({
                'success': False,
                'error': '终端不存在'
            }), 404

        return jsonify({
            'success': True,
            'data': terminal
        })
    except Exception as e:
        logger.error(f"获取终端信息失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@terminal_monitor_bp.route('/errors', methods=['GET'])
def get_errors():
    """获取所有错误信息"""
    try:
        errors = terminal_monitor.get_errors(limit)
        return jsonify({
            'success': True,
            'data': errors,
            'count': len(errors)
        })
    except Exception as e:
        logger.error(f"获取错误列表失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@terminal_monitor_bp.route('/stats', methods=['GET'])
def get_stats():
    """获取访问统计"""
    try:
        return jsonify({
            'success': True,
            'data': stats
        })
    except Exception as e:
        logger.error(f"获取统计信息失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@terminal_monitor_bp.route('/blacklist', methods=['POST'])
def add_to_blacklist():
    """添加IP到黑名单"""
    try:
        ip_address = data.get('ip_address')
        reason = data.get('reason', '手动阻止')

        if not ip_address:
            return jsonify({
                'success': False,
                'error': 'IP地址不能为空'
            }), 400

        success = terminal_monitor.block_ip(ip_address, reason)

        return jsonify({
            'success': success,
            'message': f'IP {ip_address} 已添加到黑名单' if success else '添加失败'
        })
    except Exception as e:
        logger.error(f"添加黑名单失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@terminal_monitor_bp.route('/blacklist/<ip_address>', methods=['DELETE'])
def remove_from_blacklist(ip_address):
    """从黑名单移除IP"""
    try:

        return jsonify({
            'success': success,
            'message': f'IP {ip_address} 已从黑名单移除' if success else '移除失败'
        })
    except Exception as e:
        logger.error(f"移除黑名单失败: {str(e)}")
        return jsonify({
            'success': False,
        }), 500

@terminal_monitor_bp.route('/whitelist', methods=['POST'])
def add_to_whitelist():
    """添加IP到白名单"""
    try:
        ip_address = data.get('ip_address')
        reason = data.get('reason', '手动白名单')

        if not ip_address:
            return jsonify({
                'success': False,
                'error': 'IP地址不能为空'


        return jsonify({
            'success': success,
        })
    except Exception as e:
        logger.error(f"添加白名单失败: {str(e)}")
            'success': False,
        }), 500

@terminal_monitor_bp.route('/block/<ip_address>', methods=['POST'])
def block_ip(ip_address):
    """阻止指定IP"""
        reason = data.get('reason', '手动阻止')

        success = terminal_monitor.block_ip(ip_address, reason)

        return jsonify({
            'success': success,
            'message': f'IP {ip_address} 已阻止' if success else '阻止失败'
        })
    except Exception as e:
        logger.error(f"阻止IP失败: {str(e)}")
        return jsonify({
            'error': str(e)
        }), 500

@terminal_monitor_bp.route('/unblock/<ip_address>', methods=['POST'])
def unblock_ip(ip_address):
    try:

        return jsonify({
            'message': f'IP {ip_address} 已解除阻止' if success else '解除失败'
        })
    except Exception as e:
        logger.error(f"解除IP阻止失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@terminal_monitor_bp.route('/record-error', methods=['POST'])
def record_error():
    """记录错误"""
    try:

        error_type = data.get('error_type', 'unknown')
        error_message = data.get('error_message', '')

        terminal_monitor.record_error(
            error_type=error_type,
            error_message=error_message,
            severity=severity,
            request=request
        )

        return jsonify({
            'success': True,
            'message': '错误记录成功'
        })
    except Exception as e:
        logger.error(f"记录错误失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@terminal_monitor_bp.route('/record-client-error', methods=['POST'])
def record_client_error():
    """记录客户端错误"""
    try:

        terminal_monitor.record_error(
            error_type='client_exception',
            error_message=data.get('exception_message', ''),
            severity=data.get('severity', 'medium'),
            source='client',
            request=request,
            exception_type=data.get('exception_type'),
            stack_trace=data.get('stack_trace'),
            console_logs=data.get('console_logs'),
            browser_info=data.get('browser_info'),
        )

        return jsonify({
            'success': True,
            'message': '客户端错误记录成功'
        })
    except Exception as e:
        logger.error(f"记录客户端错误失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@terminal_monitor_bp.route('/monitoring-status', methods=['GET'])
def get_monitoring_status():
    try:

        return jsonify({
            'success': True,
            'data': {
                'monitoring_enabled': True,
                'stats': stats
            }
        })
    except Exception as e:
        logger.error(f"获取监控状态失败: {str(e)}")
            'success': False,
        }), 500
