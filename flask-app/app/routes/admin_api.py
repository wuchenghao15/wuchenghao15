# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
Admin API Routes for MTSCOS AI System
后台交互API路由
"""

from flask import Blueprint, request, jsonify, session
import logging
logger = logging.getLogger(__name__)
import sqlite3
from contextlib import contextmanager
import json
from datetime import datetime, timedelta
from app.utils.permission_manager import get_permission_manager
from app.utils.session_manager import get_session_manager
from app.utils.monitor_manager import (
    get_system_status, get_alerts, resolve_alert, get_alert_summary,
    log_page_navigation, get_navigation_logs, get_navigation_anomalies,
    resolve_navigation_anomaly
)
from app.middlewares.access_control import require_admin, require_super_admin, require_login
import sys

admin_api_bp = Blueprint('admin_api', __name__)


@admin_api_bp.route('/api/admin/users', methods=['GET'])
@require_admin
def get_users():
    """获取用户列表 - 需要管理员权限"""
    try:
        with sqlite3.connect('/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/flask-app/app.db') as conn:
            cursor = conn.cursor()
            
            cursor.execute('SELECT id, username, email, role, created_at FROM users ORDER BY created_at DESC')
            users = []
            for row in cursor.fetchall():
                users.append({
                    'id': row[0],
                    'username': row[1],
                    'email': row[2],
                    'role': row[3],
                    'created_at': row[4]
                })
            
        return jsonify({
            'success': True,
            'users': users,
            'count': len(users)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@admin_api_bp.route('/api/admin/users/<int:user_id>', methods=['GET'])
@require_admin
def get_user_details(user_id):
    """获取用户详情 - 需要管理员权限"""
    try:
        with sqlite3.connect('/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/flask-app/app.db') as conn:
            
            cursor = conn.cursor()
            
            cursor.execute('SELECT id, username, email, role, created_at, last_login FROM users WHERE id = ?', (user_id,))
            row = cursor.fetchone()
            
        
        if row:
            return jsonify({
                'success': True,
                'user': {
                    'id': row[0],
                    'username': row[1],
                    'email': row[2],
                    'role': row[3],
                    'created_at': row[4],
                    'last_login': row[5]
                }
            })
        else:
            return jsonify({
                'success': False,
                'error': 'User not found'
            }), 404
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@admin_api_bp.route('/api/admin/users/<int:user_id>/role', methods=['PUT'])
@require_admin
def change_user_role(user_id):
    """修改用户角色 - 需要管理员权限"""
    try:
        data = request.get_json()
        role = data.get('role')
        
        if role not in ['guest', 'user', 'teacher', 'admin', 'super_admin']:
            return jsonify({
                'success': False,
                'error': 'Invalid role'
            }), 400
        
        with sqlite3.connect('/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/flask-app/app.db') as conn:
            
            cursor = conn.cursor()
            
            cursor.execute('UPDATE users SET role = ? WHERE id = ?', (role, user_id))
            conn.commit()
        
        return jsonify({
            'success': True,
            'message': 'User role updated successfully',
            'role': role
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@admin_api_bp.route('/api/admin/users/<int:user_id>', methods=['DELETE'])
@require_super_admin
def delete_user(user_id):
    """删除用户 - 需要超级管理员权限"""
    try:
        with sqlite3.connect('/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/flask-app/app.db') as conn:
            
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM users WHERE id = ?', (user_id,))
            conn.commit()
        
        return jsonify({
            'success': True,
            'message': 'User deleted successfully'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@admin_api_bp.route('/api/admin/sessions', methods=['GET'])
@require_admin
def get_active_sessions():
    """获取活跃会话列表 - 需要管理员权限"""
    try:
        sm = get_session_manager()
        sessions = sm.get_active_sessions()
        
        return jsonify({
            'success': True,
            'sessions': sessions,
            'count': len(sessions)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@admin_api_bp.route('/api/admin/sessions/<string:session_id>', methods=['DELETE'])
@require_admin
def terminate_session(session_id):
    """终止会话 - 需要管理员权限"""
    try:
        sm = get_session_manager()
        sm.invalidate_session(session_id)
        
        return jsonify({
            'success': True,
            'message': 'Session terminated successfully'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@admin_api_bp.route('/api/admin/sessions/user/<int:user_id>', methods=['DELETE'])
@require_admin
def terminate_user_sessions(user_id):
    """终止用户所有会话 - 需要管理员权限"""
    try:
        sm = get_session_manager()
        sm.invalidate_user_sessions(user_id)
        
        return jsonify({
            'success': True,
            'message': 'All user sessions terminated successfully'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@admin_api_bp.route('/api/admin/access_logs', methods=['GET'])
@require_admin
def get_access_logs():
    """获取访问日志 - 需要管理员权限"""
    try:
        with sqlite3.connect('/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/flask-app/app.db') as conn:
            
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM access_logs ORDER BY access_time DESC LIMIT 100')
            columns = ['id', 'path', 'user_id', 'username', 'role', 'ip_address', 'user_agent', 'access_time', 'method']
            logs = []
            for row in cursor.fetchall():
                logs.append(dict(zip(columns, row)))
            
        return jsonify({
            'success': True,
            'logs': logs,
            'count': len(logs)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@admin_api_bp.route('/api/admin/system_logs', methods=['GET'])
@require_admin
def get_system_logs():
    """获取系统日志 - 需要管理员权限"""
    try:
        with sqlite3.connect('/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/flask-app/app.db') as conn:
            
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM system_logs ORDER BY created_at DESC LIMIT 100')
            columns = ['id', 'level', 'module', 'message', 'ip_address', 'created_at']
            logs = []
            for row in cursor.fetchall():
                logs.append(dict(zip(columns, row)))
            
        return jsonify({
            'success': True,
            'logs': logs,
            'count': len(logs)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@admin_api_bp.route('/api/admin/login_attempts', methods=['GET'])
@require_admin
def get_login_attempts():
    """获取登录尝试记录 - 需要管理员权限"""
    try:
        with sqlite3.connect('/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/flask-app/app.db') as conn:
            
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM login_attempts ORDER BY attempt_time DESC LIMIT 100')
            columns = ['id', 'username', 'ip_address', 'success', 'attempt_time']
            attempts = []
            for row in cursor.fetchall():
                attempts.append(dict(zip(columns, row)))
            
        return jsonify({
            'success': True,
            'attempts': attempts,
            'count': len(attempts)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@admin_api_bp.route('/api/admin/locked_users', methods=['GET'])
@require_admin
def get_locked_users():
    """获取被锁定用户列表 - 需要管理员权限"""
    try:
        with sqlite3.connect('/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/flask-app/app.db') as conn:
            
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM user_locks')
            columns = ['username', 'locked_until', 'lock_reason', 'created_at']
            locked_users = []
            for row in cursor.fetchall():
                locked_users.append(dict(zip(columns, row)))
            
        return jsonify({
            'success': True,
            'locked_users': locked_users,
            'count': len(locked_users)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@admin_api_bp.route('/api/admin/unlock_user/<string:username>', methods=['POST'])
@require_admin
def unlock_user(username):
    """解锁用户 - 需要管理员权限"""
    try:
        sm = get_session_manager()
        sm.unlock_user(username)
        
        return jsonify({
            'success': True,
            'message': f'User {username} unlocked successfully'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@admin_api_bp.route('/api/admin/roles', methods=['GET'])
@require_admin
def get_roles():
    """获取所有角色 - 需要管理员权限"""
    try:
        pm = get_permission_manager()
        roles = pm.get_all_roles()
        
        return jsonify({
            'success': True,
            'roles': roles
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@admin_api_bp.route('/api/admin/permissions', methods=['GET'])
@require_admin
def get_all_permissions():
    """获取所有权限 - 需要管理员权限"""
    try:
        pm = get_permission_manager()
        permissions = pm.get_all_permissions()
        
        return jsonify({
            'success': True,
            'permissions': permissions
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@admin_api_bp.route('/api/admin/system/status', methods=['GET'])
@require_login
def get_system_status():
    """获取系统状态 - 需要登录"""
    try:
        with sqlite3.connect('/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/flask-app/app.db') as conn:
            
            cursor = conn.cursor()
            
            # 获取用户数
            cursor.execute('SELECT COUNT(*) FROM users')
            user_count = cursor.fetchone()[0]
            
            # 获取会话数
            cursor.execute('SELECT COUNT(*) FROM sessions')
            session_count = cursor.fetchone()[0]
            
            # 获取问题数
            cursor.execute('SELECT COUNT(*) FROM questions')
            question_count = cursor.fetchone()[0]
            
            # 获取错误数
            cursor.execute('SELECT COUNT(*) FROM ai_learning_errors WHERE resolved = 0')
            error_count = cursor.fetchone()[0]
            
        
        return jsonify({
            'success': True,
            'status': {
                'user_count': user_count,
                'session_count': session_count,
                'question_count': question_count,
                'error_count': error_count,
                'system_time': datetime.now().isoformat(),
                'status': 'running'
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@admin_api_bp.route('/api/admin/cleanup', methods=['POST'])
@require_super_admin
def cleanup_system():
    """清理系统数据 - 需要超级管理员权限"""
    try:
        with sqlite3.connect('/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/flask-app/app.db') as conn:
            
            cursor = conn.cursor()
            
            # 清理过期会话
            cursor.execute('DELETE FROM sessions WHERE expires_at < ?', (datetime.now(),))
            
            # 清理30天前的访问日志
            threshold = datetime.now() - timedelta(days=30)
            cursor.execute('DELETE FROM access_logs WHERE access_time < ?', (threshold,))
            
            # 清理30天前的登录尝试记录
            cursor.execute('DELETE FROM login_attempts WHERE attempt_time < ?', (threshold,))
            
            conn.commit()
        
        return jsonify({
            'success': True,
            'message': 'System cleanup completed successfully'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@admin_api_bp.route('/api/monitor/log', methods=['POST'])
def receive_monitor_log():
    """接收前端监控日志"""
    try:
        data = request.get_json()
        session_id = request.headers.get('X-Session-ID', 'unknown')
        log_type = data.get('type')
        
        if log_type == 'page_navigation':
            user_id = session.get('user_id', 0)
            username = session.get('username', 'anonymous')
            page_from = data.get('from', '')
            page_to = data.get('to', '')
            navigation_type = data.get('navigationType', 'unknown')
            navigation_time = data.get('navigationTime', 0.0)
            
            log_page_navigation(user_id, username, session_id, 
                               page_from, page_to, navigation_type, 
                               navigation_time)
        
        elif log_type == 'anomaly':
            anomaly_type = data.get('anomalyType', '')
            details = data.get('details', {})
            
            with sqlite3.connect('/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/flask-app/app.db') as conn:
                
                cursor = conn.cursor()
                
                cursor.execute('''
                INSERT INTO navigation_anomalies
                (user_id, username, session_id, anomaly_type, page_from, page_to,
                navigation_count, time_window, severity, details)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (session.get('user_id', 0), session.get('username', 'anonymous'), 
                session_id, anomaly_type, data.get('url', ''), '',
                details.get('backCount', 0), details.get('timeWindow', 60000),
                'WARNING', json.dumps(details)))
                
                conn.commit()
        
        elif log_type == 'error':
            error_type = data.get('errorType', '')
            error_details = data.get('details', {})
            
            with sqlite3.connect('/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/flask-app/app.db') as conn:
                
                cursor = conn.cursor()
                
                cursor.execute('''
                INSERT INTO ai_learning_errors (error_type, message, details)
                VALUES (?, ?, ?)
                ''', (error_type, str(error_details.get('message', '')), json.dumps(error_details)))
                
                conn.commit()
        
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"Failed to process monitor log: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@admin_api_bp.route('/api/admin/monitor/system_status', methods=['GET'])
@require_admin
def get_monitor_system_status():
    """获取监控系统状态 - 需要管理员权限"""
    try:
        status = get_system_status()
        
        return jsonify({
            'success': True,
            'status': status
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@admin_api_bp.route('/api/admin/monitor/alerts', methods=['GET'])
@require_admin
def get_monitor_alerts():
    """获取监控告警列表 - 需要管理员权限"""
    try:
        resolved = request.args.get('resolved', 'false').lower() == 'true'
        limit = int(request.args.get('limit', 50))
        
        alerts = get_alerts(limit, resolved)
        
        return jsonify({
            'success': True,
            'alerts': alerts,
            'count': len(alerts)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@admin_api_bp.route('/api/admin/monitor/alerts/<int:alert_id>', methods=['PUT'])
@require_admin
def resolve_monitor_alert(alert_id):
    """解决监控告警 - 需要管理员权限"""
    try:
        success = resolve_alert(alert_id)
        
        return jsonify({
            'success': success,
            'message': 'Alert resolved successfully' if success else 'Failed to resolve alert'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@admin_api_bp.route('/api/admin/monitor/alerts/summary', methods=['GET'])
@require_admin
def get_monitor_alert_summary():
    """获取告警摘要 - 需要管理员权限"""
    try:
        summary = get_alert_summary()
        
        return jsonify({
            'success': True,
            'summary': summary
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@admin_api_bp.route('/api/admin/monitor/navigation_logs', methods=['GET'])
@require_admin
def get_monitor_navigation_logs():
    """获取页面导航日志 - 需要管理员权限"""
    try:
        session_id = request.args.get('session_id')
        user_id = request.args.get('user_id')
        limit = int(request.args.get('limit', 100))
        
        logs = get_navigation_logs(session_id, int(user_id) if user_id else None, limit)
        
        return jsonify({
            'success': True,
            'logs': logs,
            'count': len(logs)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@admin_api_bp.route('/api/admin/monitor/navigation_anomalies', methods=['GET'])
@require_admin
def get_monitor_navigation_anomalies():
    """获取导航异常记录 - 需要管理员权限"""
    try:
        resolved = request.args.get('resolved', 'false').lower() == 'true'
        limit = int(request.args.get('limit', 50))
        
        anomalies = get_navigation_anomalies(resolved, limit)
        
        return jsonify({
            'success': True,
            'anomalies': anomalies,
            'count': len(anomalies)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@admin_api_bp.route('/api/admin/monitor/navigation_anomalies/<int:anomaly_id>', methods=['PUT'])
@require_admin
def resolve_monitor_navigation_anomaly(anomaly_id):
    """解决导航异常 - 需要管理员权限"""
    try:
        success = resolve_navigation_anomaly(anomaly_id)
        
        return jsonify({
            'success': success,
            'message': 'Anomaly resolved successfully' if success else 'Failed to resolve anomaly'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
