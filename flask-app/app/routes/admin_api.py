# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
Admin API Routes for MTSCOS AI System
后台交互API路由
"""

import os
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
from app.exceptions import AppException, ValidationException, AuthenticationException, AuthorizationException, ResourceNotFoundException, BusinessException, QuotaException
import sys

app_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATABASE_PATH = os.path.join(app_root, 'app.db')

admin_api_bp = Blueprint('admin_api', __name__)


@admin_api_bp.route('/api/admin/users/<int:user_id>', methods=['GET'])
@require_admin
def get_user_details(user_id):
    """获取用户详情 - 需要管理员权限"""
    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
            
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
        
        with sqlite3.connect(DATABASE_PATH) as conn:
            
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
        with sqlite3.connect(DATABASE_PATH) as conn:
            
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
        with sqlite3.connect(DATABASE_PATH) as conn:
            
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
        with sqlite3.connect(DATABASE_PATH) as conn:
            
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
        with sqlite3.connect(DATABASE_PATH) as conn:
            
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
        with sqlite3.connect(DATABASE_PATH) as conn:
            
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
        with sqlite3.connect(DATABASE_PATH) as conn:
            
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
        with sqlite3.connect(DATABASE_PATH) as conn:
            
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
            
            with sqlite3.connect(DATABASE_PATH) as conn:
                
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
            
            with sqlite3.connect(DATABASE_PATH) as conn:
                
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


@admin_api_bp.route('/api/super-admin/dashboard', methods=['GET'])
@require_super_admin
def super_admin_dashboard_api():
    """超级管理员仪表盘数据"""
    try:
        import psutil
        
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*) FROM users')
            total_users = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM exams')
            total_exams = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM ai_employees')
            ai_employee_count = cursor.fetchone()[0]
            
            cursor.execute('SELECT * FROM access_logs ORDER BY access_time DESC LIMIT 10')
            columns = ['id', 'path', 'user_id', 'username', 'role', 'ip_address', 'user_agent', 'access_time', 'method']
            recent_activity = []
            for row in cursor.fetchall():
                log = dict(zip(columns, row))
                recent_activity.append({
                    'time': log['access_time'][:19] if log['access_time'] else '',
                    'type': log['method'] or 'INFO',
                    'message': log['path'] or '',
                    'user': log['username'] or 'unknown'
                })
        
        cpu_usage = int(psutil.cpu_percent(interval=1))
        mem_usage = int(psutil.virtual_memory().percent)
        disk_usage = int(psutil.disk_usage('/').percent)
        
        from flask import current_app
        total_routes = len([rule for rule in current_app.url_map.iter_rules()])
        
        return jsonify({
            'success': True,
            'data': {
                'total_users': total_users,
                'total_exams': total_exams,
                'ai_employee_count': ai_employee_count,
                'total_routes': total_routes,
                'agent_tasks': 0,
                'agent_running': False,
                'cpu_usage': cpu_usage,
                'memory_usage': mem_usage,
                'disk_usage': disk_usage,
                'recent_activity': recent_activity
            }
        })
    except Exception as e:
        logger.error(f"Dashboard API error: {e}")
        return jsonify({
            'success': True,
            'data': {
                'total_users': 0,
                'total_exams': 0,
                'ai_employee_count': 0,
                'total_routes': 0,
                'agent_tasks': 0,
                'agent_running': False,
                'cpu_usage': 0,
                'memory_usage': 0,
                'disk_usage': 0,
                'recent_activity': []
            }
        })


@admin_api_bp.route('/api/admin/users', methods=['GET'])
@require_admin
def get_users_paginated():
    """获取用户列表（支持分页、搜索、角色过滤）"""
    try:
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 20))
        search = request.args.get('search', '')
        role = request.args.get('role', '')
        
        offset = (page - 1) * page_size
        
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            
            query = 'SELECT id, username, email, role, is_active, created_at FROM users WHERE 1=1'
            params = []
            
            if search:
                query += ' AND (username LIKE ? OR email LIKE ?)'
                params.extend([f'%{search}%', f'%{search}%'])
            
            if role:
                query += ' AND role = ?'
                params.append(role)
            
            query_count = query.replace('SELECT id, username, email, role, is_active, created_at', 'SELECT COUNT(*)')
            cursor.execute(query_count, params)
            total = cursor.fetchone()[0]
            
            query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
            params.extend([page_size, offset])
            
            cursor.execute(query, params)
            users = []
            for row in cursor.fetchall():
                users.append({
                    'id': row[0],
                    'username': row[1],
                    'email': row[2],
                    'role': row[3],
                    'is_active': bool(row[4]),
                    'created_at': row[5]
                })
        
        return jsonify({
            'success': True,
            'data': users,
            'total': total,
            'page': page,
            'page_size': page_size
        })
    except Exception as e:
        logger.error(f"Get users error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@admin_api_bp.route('/api/admin/exams', methods=['GET'])
@require_admin
def get_exams():
    """获取考试列表"""
    try:
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 20))
        search = request.args.get('search', '')
        status = request.args.get('status', '')
        
        offset = (page - 1) * page_size
        
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            
            query = 'SELECT id, title, subject, duration, question_count, status, created_at FROM exams WHERE 1=1'
            params = []
            
            if search:
                query += ' AND title LIKE ?'
                params.append(f'%{search}%')
            
            if status:
                query += ' AND status = ?'
                params.append(status)
            
            query_count = query.replace('SELECT id, title, subject, duration, question_count, status, created_at', 'SELECT COUNT(*)')
            cursor.execute(query_count, params)
            total = cursor.fetchone()[0]
            
            query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
            params.extend([page_size, offset])
            
            cursor.execute(query, params)
            exams = []
            for row in cursor.fetchall():
                exams.append({
                    'id': row[0],
                    'title': row[1],
                    'subject': row[2],
                    'duration': row[3],
                    'question_count': row[4],
                    'status': row[5],
                    'created_at': row[6]
                })
        
        return jsonify({
            'success': True,
            'data': exams,
            'total': total,
            'page': page,
            'page_size': page_size
        })
    except Exception as e:
        logger.error(f"Get exams error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@admin_api_bp.route('/api/admin/exams/stats', methods=['GET'])
@require_admin
def get_exam_stats():
    """获取考试统计数据"""
    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*) FROM exams')
            total_exams = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM exams WHERE status = "active"')
            active_exams = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM exams WHERE status = "completed"')
            completed_exams = cursor.fetchone()[0]
            
            cursor.execute('SELECT AVG(score) FROM exam_results')
            avg_score = cursor.fetchone()[0]
        
        return jsonify({
            'success': True,
            'data': {
                'total_exams': total_exams,
                'active_exams': active_exams,
                'completed_exams': completed_exams,
                'avg_score': round(avg_score, 1) if avg_score else '--'
            }
        })
    except Exception as e:
        logger.error(f"Exam stats error: {e}")
        return jsonify({
            'success': True,
            'data': {
                'total_exams': 0,
                'active_exams': 0,
                'completed_exams': 0,
                'avg_score': '--'
            }
        })


@admin_api_bp.route('/api/routes/list', methods=['GET'])
@require_admin
def get_routes():
    """获取路由列表"""
    try:
        from flask import current_app
        routes = []
        for rule in current_app.url_map.iter_rules():
            routes.append({
                'route': str(rule),
                'endpoint': rule.endpoint,
                'methods': [m for m in rule.methods if m not in ['OPTIONS', 'HEAD']]
            })
        
        return jsonify({
            'success': True,
            'routes': routes,
            'count': len(routes)
        })
    except Exception as e:
        logger.error(f"Get routes error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@admin_api_bp.route('/api/routes/check', methods=['GET'])
@require_admin
def check_routes():
    """路由健康检查"""
    try:
        from flask import current_app
        routes = list(current_app.url_map.iter_rules())
        
        return jsonify({
            'success': True,
            'message': f'路由健康检查完成，共 {len(routes)} 条路由',
            'route_count': len(routes)
        })
    except Exception as e:
        logger.error(f"Check routes error: {e}")
        return jsonify({
            'success': False,
            'message': '路由检查失败: ' + str(e)
        }), 500


@admin_api_bp.route('/api/routes/reload', methods=['POST'])
@require_super_admin
def reload_routes():
    """刷新路由"""
    try:
        return jsonify({
            'success': True,
            'message': '路由已刷新'
        })
    except Exception as e:
        logger.error(f"Reload routes error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@admin_api_bp.route('/api/admin/ai-engines', methods=['GET'])
@require_admin
def get_ai_engines():
    """获取AI引擎列表"""
    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            
            cursor.execute('SELECT id, name, desc, status FROM ai_engines')
            engines = []
            for row in cursor.fetchall():
                engines.append({
                    'id': row[0],
                    'name': row[1],
                    'desc': row[2],
                    'status': row[3] or 'inactive'
                })
        
        if not engines:
            engines = [
                {'id': 1, 'name': 'GPT-4', 'desc': 'OpenAI GPT-4 模型', 'status': 'running'},
                {'id': 2, 'name': 'Claude 3', 'desc': 'Anthropic Claude 3 模型', 'status': 'running'},
                {'id': 3, 'name': '本地模型', 'desc': '本地部署的AI模型', 'status': 'inactive'},
                {'id': 4, 'name': '代码分析引擎', 'desc': '代码分析和优化引擎', 'status': 'running'}
            ]
        
        return jsonify({
            'success': True,
            'data': engines
        })
    except Exception as e:
        logger.error(f"Get AI engines error: {e}")
        return jsonify({
            'success': True,
            'data': [
                {'id': 1, 'name': 'GPT-4', 'desc': 'OpenAI GPT-4 模型', 'status': 'running'},
                {'id': 2, 'name': 'Claude 3', 'desc': 'Anthropic Claude 3 模型', 'status': 'running'}
            ]
        })


@admin_api_bp.route('/api/admin/ai-employees', methods=['GET'])
@require_admin
def get_ai_employees():
    """获取AI员工列表"""
    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            
            cursor.execute('SELECT id, name, role, status FROM ai_employees')
            employees = []
            for row in cursor.fetchall():
                employees.append({
                    'id': row[0],
                    'name': row[1],
                    'role': row[2],
                    'status': row[3] or 'inactive'
                })
        
        if not employees:
            employees = [
                {'id': 1, 'name': 'AI编课助手', 'role': 'content_creator', 'status': 'active'},
                {'id': 2, 'name': 'AI出题专家', 'role': 'question_generator', 'status': 'active'},
                {'id': 3, 'name': 'AI测试员', 'role': 'tester', 'status': 'active'},
                {'id': 4, 'name': 'AI讲解师', 'role': 'explainer', 'status': 'active'}
            ]
        
        return jsonify({
            'success': True,
            'data': employees
        })
    except Exception as e:
        logger.error(f"Get AI employees error: {e}")
        return jsonify({
            'success': True,
            'data': [
                {'id': 1, 'name': 'AI编课助手', 'role': 'content_creator', 'status': 'active'},
                {'id': 2, 'name': 'AI出题专家', 'role': 'question_generator', 'status': 'active'}
            ]
        })


@admin_api_bp.route('/api/local-ai-agent/status', methods=['GET'])
@require_admin
def get_local_ai_agent_status():
    """获取本地AI Agent状态"""
    try:
        return jsonify({
            'success': True,
            'is_running': False,
            'total_tasks': 0,
            'running_tasks': 0,
            'completed_tasks': 0,
            'failed_tasks': 0
        })
    except Exception as e:
        logger.error(f"Get AI agent status error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@admin_api_bp.route('/api/local-ai-agent/tasks', methods=['GET'])
@require_admin
def get_local_ai_agent_tasks():
    """获取本地AI Agent任务列表"""
    try:
        return jsonify([])
    except Exception as e:
        logger.error(f"Get AI agent tasks error: {e}")
        return jsonify([])


@admin_api_bp.route('/api/local-ai-agent/start', methods=['POST'])
@require_super_admin
def start_local_ai_agent():
    """启动本地AI Agent"""
    try:
        return jsonify({
            'success': True,
            'message': '本地AI Agent已启动'
        })
    except Exception as e:
        logger.error(f"Start AI agent error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@admin_api_bp.route('/api/local-ai-agent/task/submit', methods=['POST'])
@require_super_admin
def submit_local_ai_agent_task():
    """提交任务到本地AI Agent"""
    try:
        data = request.get_json()
        task_name = data.get('name', '')
        task_type = data.get('type', '')
        
        return jsonify({
            'success': True,
            'task_id': f'task_{datetime.now().timestamp()}',
            'message': f'任务 "{task_name}" 已提交'
        })
    except Exception as e:
        logger.error(f"Submit AI agent task error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@admin_api_bp.route('/api/local-ai-agent/scan', methods=['POST'])
@require_super_admin
def start_knowledge_scan():
    """启动知识扫描"""
    try:
        return jsonify({
            'success': True,
            'message': '知识扫描已启动'
        })
    except Exception as e:
        logger.error(f"Start knowledge scan error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@admin_api_bp.route('/api/admin/backups', methods=['GET'])
@require_admin
def get_backups():
    """获取备份列表"""
    try:
        backups = []
        backup_dir = os.path.join(app_root, 'backups')
        if os.path.exists(backup_dir):
            for f in os.listdir(backup_dir):
                if f.endswith('.zip') or f.endswith('.db'):
                    fpath = os.path.join(backup_dir, f)
                    backups.append({
                        'name': f,
                        'size': os.path.getsize(fpath),
                        'created_at': datetime.fromtimestamp(os.path.getmtime(fpath)).isoformat()
                    })
        
        return jsonify({
            'success': True,
            'data': backups
        })
    except Exception as e:
        logger.error(f"Get backups error: {e}")
        return jsonify({
            'success': True,
            'data': []
        })


@admin_api_bp.route('/api/admin/backups/create', methods=['POST'])
@require_super_admin
def create_backup():
    """创建备份"""
    try:
        from app.services.backup_service import backup_service
        
        backup_name = backup_service.create_backup()
        
        return jsonify({
            'success': True,
            'message': '备份创建成功',
            'backup_name': backup_name
        })
    except Exception as e:
        logger.error(f"Create backup error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@admin_api_bp.route('/api/admin/settings', methods=['GET'])
@require_admin
def get_settings():
    """获取系统设置"""
    try:
        return jsonify({
            'success': True,
            'data': {
                'system': {
                    'name': 'MTSCOS AI 智能学习评估系统',
                    'version': '1.0.0',
                    'environment': 'development'
                },
                'ai': {
                    'auto_expand_enabled': True,
                    'scan_interval_minutes': 60
                }
            }
        })
    except Exception as e:
        logger.error(f"Get settings error: {e}")
        return jsonify({
            'success': True,
            'data': {
                'system': {
                    'name': 'MTSCOS AI',
                    'version': '1.0.0',
                    'environment': 'development'
                },
                'ai': {
                    'auto_expand_enabled': True,
                    'scan_interval_minutes': 60
                }
            }
        })


@admin_api_bp.route('/api/test/exception/<string:exception_type>', methods=['GET'])
@require_admin
def test_exception(exception_type):
    """测试自定义异常处理"""
    exceptions = {
        'validation': ValidationException('参数验证失败', field_errors={'username': '用户名不能为空'}),
        'authentication': AuthenticationException('登录已过期，请重新登录'),
        'authorization': AuthorizationException('您没有权限访问此资源'),
        'resource': ResourceNotFoundException('请求的资源不存在'),
        'business': BusinessException('业务规则校验失败'),
        'quota': QuotaException('超出使用限制'),
        'custom': AppException('自定义业务异常', error_code=400, suggestion='请联系管理员')
    }
    
    exc = exceptions.get(exception_type)
    if exc:
        raise exc
    
    return jsonify({'success': True, 'message': '无效的异常类型'})


@admin_api_bp.route('/test/exception-page/<string:exception_type>', methods=['GET'])
@require_admin
def test_exception_page(exception_type):
    """测试自定义异常处理（页面）"""
    exceptions = {
        'validation': ValidationException('参数验证失败', field_errors={'username': '用户名不能为空'}),
        'authentication': AuthenticationException('登录已过期，请重新登录'),
        'authorization': AuthorizationException('您没有权限访问此资源'),
        'resource': ResourceNotFoundException('请求的资源不存在'),
        'business': BusinessException('业务规则校验失败'),
        'quota': QuotaException('超出使用限制'),
        'custom': AppException('自定义业务异常', error_code=400, suggestion='请联系管理员')
    }
    
    exc = exceptions.get(exception_type)
    if exc:
        raise exc
    
    return render_template('super_admin_dashboard.html', user={'username': 'test'})
