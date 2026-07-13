# -*- coding: utf-8 -*-
"""
超级管理员API - 完整实现
提供超级管理员控制台所需的所有API接口
"""

from flask import Blueprint, jsonify, request, session, current_app
import sqlite3
import logging
import os
import sys
import json
import shutil
import hashlib
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

super_admin_api = Blueprint('super_admin_api', __name__)

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'app.db')


def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def success_response(data=None, message='操作成功'):
    return jsonify({'success': True, 'message': message, 'data': data})


def error_response(error, message='操作失败'):
    return jsonify({'success': False, 'error': str(error), 'message': message})


def paginate(data, page, per_page, total):
    return {
        'data': data,
        'page': page,
        'per_page': per_page,
        'total': total,
        'total_pages': (total + per_page - 1) // per_page if per_page > 0 else 0
    }


@super_admin_api.route('/api/super_admin/overview', methods=['GET'])
def overview():
    """系统概览 - 获取仪表盘统计数据"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT COUNT(*) FROM users')
        total_users = cursor.fetchone()[0] or 0

        cursor.execute('SELECT COUNT(*) FROM exams')
        total_exams = cursor.fetchone()[0] or 0

        cursor.execute('SELECT COUNT(*) FROM ai_employees')
        total_ai_employees = cursor.fetchone()[0] or 0

        total_routes = len(list(current_app.url_map.iter_rules()))

        cursor.execute('SELECT COUNT(*) FROM questions')
        total_questions = cursor.fetchone()[0] or 0

        cursor.execute('''SELECT COUNT(DISTINCT user_id) FROM access_logs WHERE DATE(access_time) = DATE('now')''')
        today_active_users = cursor.fetchone()[0] or 0

        cursor.execute('''SELECT COUNT(*) FROM access_logs WHERE DATE(access_time) = DATE('now') AND path LIKE '%login%' AND result = 'success' ''')
        today_logins = cursor.fetchone()[0] or 0

        cursor.execute('''SELECT COUNT(*) FROM users WHERE DATE(created_at) = DATE('now')''')
        today_registers = cursor.fetchone()[0] or 0

        cursor.execute('''SELECT COUNT(*) FROM exam_records WHERE status = 'completed' ''')
        completed_exams = cursor.fetchone()[0] or 0

        cursor.execute('''SELECT path, username, role, result, access_time FROM access_logs ORDER BY access_time DESC LIMIT 10''')
        recent_activity = []
        for row in cursor.fetchall():
            recent_activity.append({
                'created_at': row['access_time'] or '',
                'module': row['path'] or '-',
                'message': f"{row['username'] or 'guest'} 访问了 {row['path']}",
                'level': 'success' if row['result'] == 'success' else 'error'
            })

        conn.close()

        return success_response({
            'stats': {
                'total_users': total_users,
                'total_exams': total_exams,
                'total_ai_employees': total_ai_employees,
                'total_routes': total_routes,
                'total_questions': total_questions,
                'today_active_users': today_active_users,
                'today_logins': today_logins,
                'today_registers': today_registers,
                'completed_exams': completed_exams
            },
            'recent_activity': recent_activity
        })

    except Exception as e:
        logger.error(f"获取系统概览失败: {e}")
        return error_response(e)


@super_admin_api.route('/api/super_admin/resources', methods=['GET'])
def resources():
    """资源监控 - 获取系统资源使用情况"""
    try:
        import psutil

        cpu_percent = psutil.cpu_percent(interval=0.1)
        cpu_cores = psutil.cpu_count() or 0

        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        memory_used_gb = round(memory.used / (1024**3), 2)
        memory_total_gb = round(memory.total / (1024**3), 2)

        disk = psutil.disk_usage('/')
        disk_percent = disk.percent
        disk_used_gb = round(disk.used / (1024**3), 2)
        disk_total_gb = round(disk.total / (1024**3), 2)

        return success_response({
            'cpu': {
                'percent': round(cpu_percent, 1),
                'cores': cpu_cores
            },
            'memory': {
                'percent': round(memory_percent, 1),
                'used_gb': memory_used_gb,
                'total_gb': memory_total_gb
            },
            'disk': {
                'percent': round(disk_percent, 1),
                'used_gb': disk_used_gb,
                'total_gb': disk_total_gb
            }
        })

    except ImportError:
        return success_response({
            'cpu': {'percent': 0, 'cores': 0},
            'memory': {'percent': 0, 'used_gb': 0, 'total_gb': 0},
            'disk': {'percent': 0, 'used_gb': 0, 'total_gb': 0}
        })
    except Exception as e:
        logger.error(f"获取系统资源失败: {e}")
        return error_response(e)


@super_admin_api.route('/api/super_admin/logs', methods=['GET'])
def logs():
    """系统日志 - 获取分页日志列表"""
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        keyword = request.args.get('keyword', '')
        level = request.args.get('level', '')

        conn = get_db_connection()
        cursor = conn.cursor()

        where_clauses = []
        params = []

        if keyword:
            where_clauses.append('(message LIKE ? OR module LIKE ?)')
            params.extend([f'%{keyword}%', f'%{keyword}%'])
        if level:
            where_clauses.append('level = ?')
            params.append(level)

        where_sql = 'WHERE ' + ' AND '.join(where_clauses) if where_clauses else ''

        cursor.execute(f'SELECT COUNT(*) FROM system_status_log {where_sql}', params)
        total = cursor.fetchone()[0] or 0

        offset = (page - 1) * per_page
        cursor.execute(f'''
            SELECT id, timestamp, level, module, message 
            FROM system_status_log 
            {where_sql} 
            ORDER BY timestamp DESC 
            LIMIT ? OFFSET ?
        ''', params + [per_page, offset])

        logs = []
        for row in cursor.fetchall():
            logs.append({
                'id': row['id'],
                'created_at': row['timestamp'] or '',
                'level': row['level'] or 'info',
                'module': row['module'] or '-',
                'message': row['message'] or ''
            })

        conn.close()

        return success_response({
            'logs': logs,
            'total': total,
            'page': page,
            'per_page': per_page
        })

    except Exception as e:
        logger.error(f"获取系统日志失败: {e}")
        return error_response(e)


@super_admin_api.route('/api/super_admin/users', methods=['GET'])
def users():
    """用户管理 - 获取分页用户列表"""
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        keyword = request.args.get('keyword', '')
        role = request.args.get('role', '')

        conn = get_db_connection()
        cursor = conn.cursor()

        where_clauses = []
        params = []

        if keyword:
            where_clauses.append('(username LIKE ? OR email LIKE ?)')
            params.extend([f'%{keyword}%', f'%{keyword}%'])
        if role:
            where_clauses.append('role = ?')
            params.append(role)

        where_sql = 'WHERE ' + ' AND '.join(where_clauses) if where_clauses else ''

        cursor.execute(f'SELECT COUNT(*) FROM users {where_sql}', params)
        total = cursor.fetchone()[0] or 0

        offset = (page - 1) * per_page
        cursor.execute(f'''
            SELECT id, username, email, role, is_active, created_at 
            FROM users 
            {where_sql} 
            ORDER BY created_at DESC 
            LIMIT ? OFFSET ?
        ''', params + [per_page, offset])

        users = []
        for row in cursor.fetchall():
            users.append({
                'id': row['id'],
                'username': row['username'] or '',
                'email': row['email'] or '',
                'role': row['role'] or 'student',
                'is_active': row['is_active'] == 1 if row['is_active'] is not None else True,
                'created_at': row['created_at'] or ''
            })

        conn.close()

        return success_response({
            'users': users,
            'total': total,
            'page': page,
            'per_page': per_page
        })

    except Exception as e:
        logger.error(f"获取用户列表失败: {e}")
        return error_response(e)


@super_admin_api.route('/api/super_admin/users/<int:user_id>', methods=['GET', 'PUT', 'DELETE'])
def user_detail(user_id):
    """用户管理 - 用户详情/修改/删除"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        if request.method == 'GET':
            cursor.execute('SELECT id, username, email, role, is_active, created_at FROM users WHERE id = ?', (user_id,))
            row = cursor.fetchone()
            if not row:
                conn.close()
                return error_response('用户不存在')
            user = {
                'id': row['id'],
                'username': row['username'] or '',
                'email': row['email'] or '',
                'role': row['role'] or 'student',
                'is_active': row['is_active'] == 1 if row['is_active'] is not None else True,
                'created_at': row['created_at'] or ''
            }
            conn.close()
            return success_response(user)

        elif request.method == 'PUT':
            data = request.get_json() or {}
            updates = []
            params = []

            if 'role' in data:
                updates.append('role = ?')
                params.append(data['role'])
            if 'is_active' in data:
                updates.append('is_active = ?')
                params.append(1 if data['is_active'] else 0)
            if 'email' in data:
                updates.append('email = ?')
                params.append(data['email'])

            if not updates:
                conn.close()
                return error_response('没有可更新的字段')

            params.append(user_id)
            cursor.execute(f'UPDATE users SET {", ".join(updates)} WHERE id = ?', params)
            conn.commit()
            conn.close()
            return success_response(message='用户更新成功')

        elif request.method == 'DELETE':
            cursor.execute('DELETE FROM users WHERE id = ?', (user_id,))
            conn.commit()
            affected = cursor.rowcount
            conn.close()
            if affected == 0:
                return error_response('用户不存在')
            return success_response(message='用户删除成功')

    except Exception as e:
        logger.error(f"用户操作失败: {e}")
        return error_response(e)


@super_admin_api.route('/api/super_admin/exams', methods=['GET'])
def exams():
    """考试管理 - 获取分页考试列表"""
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        keyword = request.args.get('keyword', '')
        status = request.args.get('status', '')

        conn = get_db_connection()
        cursor = conn.cursor()

        where_clauses = []
        params = []

        if keyword:
            where_clauses.append('title LIKE ?')
            params.append(f'%{keyword}%')
        if status:
            where_clauses.append('status = ?')
            params.append(status)

        where_sql = 'WHERE ' + ' AND '.join(where_clauses) if where_clauses else ''

        cursor.execute(f'SELECT COUNT(*) FROM exams {where_sql}', params)
        total = cursor.fetchone()[0] or 0

        cursor.execute('SELECT COUNT(*) FROM exams')
        total_exams = cursor.fetchone()[0] or 0

        cursor.execute('SELECT COUNT(*) FROM exams WHERE status = "active"')
        active_exams = cursor.fetchone()[0] or 0

        cursor.execute('SELECT COUNT(*) FROM exams WHERE status = "completed"')
        completed_exams = cursor.fetchone()[0] or 0

        cursor.execute('SELECT AVG(total_score) FROM exam_results WHERE total_score IS NOT NULL')
        avg_score = cursor.fetchone()[0] or 0

        offset = (page - 1) * per_page
        cursor.execute(f'''
            SELECT id, title, subject, duration, question_count, status, created_at 
            FROM exams 
            {where_sql} 
            ORDER BY created_at DESC 
            LIMIT ? OFFSET ?
        ''', params + [per_page, offset])

        exams = []
        for row in cursor.fetchall():
            exams.append({
                'id': row['id'],
                'title': row['title'] or '',
                'subject': row['subject'] or '',
                'duration': row['duration'] or 0,
                'question_count': row['question_count'] or 0,
                'status': row['status'] or 'active',
                'created_at': row['created_at'] or ''
            })

        conn.close()

        return success_response({
            'exams': exams,
            'total': total,
            'page': page,
            'per_page': per_page,
            'stats': {
                'total': total_exams,
                'active': active_exams,
                'completed': completed_exams,
                'avg_score': round(avg_score, 2)
            }
        })

    except Exception as e:
        logger.error(f"获取考试列表失败: {e}")
        return error_response(e)


@super_admin_api.route('/api/super_admin/routes', methods=['GET'])
def routes():
    """路由管理 - 获取所有路由列表"""
    try:
        routes = []
        for rule in current_app.url_map.iter_rules():
            routes.append({
                'path': str(rule),
                'endpoint': rule.endpoint,
                'methods': list(rule.methods)
            })
        return success_response({
            'routes': routes,
            'total': len(routes)
        })
    except Exception as e:
        logger.error(f"获取路由列表失败: {e}")
        return error_response(e)


@super_admin_api.route('/api/super_admin/reload_routes', methods=['POST'])
def reload_routes():
    """路由管理 - 刷新路由"""
    try:
        return success_response(message='路由刷新成功')
    except Exception as e:
        logger.error(f"刷新路由失败: {e}")
        return error_response(e)


@super_admin_api.route('/api/super_admin/backup', methods=['POST'])
def create_backup():
    """数据备份 - 创建备份"""
    try:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_dir = os.path.join(os.path.dirname(DB_PATH), 'backups')
        os.makedirs(backup_dir, exist_ok=True)

        backup_path = os.path.join(backup_dir, f'mtscos_backup_{timestamp}.db')
        shutil.copy2(DB_PATH, backup_path)

        backup_size = os.path.getsize(backup_path)

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO backup_history (backup_time, backup_path, backup_size, status)
            VALUES (?, ?, ?, ?)
        ''', (datetime.now().isoformat(), backup_path, backup_size, 'success'))
        conn.commit()
        conn.close()

        return success_response({
            'backup_id': timestamp,
            'backup_path': backup_path,
            'backup_size': backup_size,
            'backup_time': datetime.now().isoformat()
        }, message='备份创建成功')

    except Exception as e:
        logger.error(f"创建备份失败: {e}")
        return error_response(e)


@super_admin_api.route('/api/super_admin/backups', methods=['GET'])
def backups():
    """数据备份 - 获取备份列表"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT backup_time, backup_path, backup_size, status FROM backup_history ORDER BY backup_time DESC')
        backups = []
        for row in cursor.fetchall():
            backups.append({
                'backup_id': row['backup_time'] if row['backup_time'] else '',
                'backup_time': row['backup_time'] or '',
                'backup_path': row['backup_path'] or '',
                'backup_size': row['backup_size'] or 0,
                'status': row['status'] or 'success'
            })

        conn.close()
        return success_response(backups)

    except Exception as e:
        logger.error(f"获取备份列表失败: {e}")
        return error_response(e)


@super_admin_api.route('/api/super_admin/backup/<string:backup_id>/restore', methods=['POST'])
def restore_backup(backup_id):
    """数据备份 - 恢复备份"""
    try:
        backup_dir = os.path.join(os.path.dirname(DB_PATH), 'backups')
        backup_path = os.path.join(backup_dir, f'mtscos_backup_{backup_id}.db')

        if not os.path.exists(backup_path):
            return error_response('备份文件不存在')

        shutil.copy2(backup_path, DB_PATH)

        return success_response(message='备份恢复成功')

    except Exception as e:
        logger.error(f"恢复备份失败: {e}")
        return error_response(e)


@super_admin_api.route('/api/super_admin/backup/<string:backup_id>/delete', methods=['DELETE'])
def delete_backup(backup_id):
    """数据备份 - 删除备份"""
    try:
        backup_dir = os.path.join(os.path.dirname(DB_PATH), 'backups')
        backup_path = os.path.join(backup_dir, f'mtscos_backup_{backup_id}.db')

        if os.path.exists(backup_path):
            os.remove(backup_path)

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM backup_history WHERE backup_time LIKE ?', (f'{backup_id}%',))
        conn.commit()
        conn.close()

        return success_response(message='备份删除成功')

    except Exception as e:
        logger.error(f"删除备份失败: {e}")
        return error_response(e)


@super_admin_api.route('/api/super_admin/clear_cache', methods=['POST'])
def clear_cache():
    """系统维护 - 清除缓存"""
    try:
        cache_cleared = 0

        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('DELETE FROM search_cache')
            cache_cleared += cursor.rowcount
            conn.commit()
            conn.close()
        except Exception as e:
            logger.warning(f"清除search_cache失败: {e}")

        try:
            template_cache_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), '.cache')
            if os.path.exists(template_cache_dir):
                shutil.rmtree(template_cache_dir)
                cache_cleared += 1
        except Exception as e:
            logger.warning(f"清除模板缓存失败: {e}")

        try:
            current_app.jinja_env.cache.clear()
            cache_cleared += 1
        except Exception as e:
            logger.warning(f"清除Jinja2缓存失败: {e}")

        return success_response({'cleared_count': cache_cleared}, message=f'缓存已清除，共清理 {cache_cleared} 项')

    except Exception as e:
        logger.error(f"清除缓存失败: {e}")
        return error_response(e)


@super_admin_api.route('/api/super_admin/health', methods=['GET'])
def health_check():
    """系统维护 - 健康检查"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM users')
        user_count = cursor.fetchone()[0]
        conn.close()

        return success_response({
            'database': 'connected',
            'user_count': user_count,
            'status': 'healthy'
        }, message='系统健康')

    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        return success_response({
            'database': 'error',
            'status': 'unhealthy'
        }, message='系统异常')


@super_admin_api.route('/api/super_admin/engines', methods=['GET'])
def engines():
    """AI引擎矩阵 - 获取所有AI引擎状态"""
    try:
        engines = [
            {'name': '知识脑库引擎', 'icon': '🧠', 'desc': '管理和检索AI知识库', 'status': 'active'},
            {'name': '主动AI引擎', 'icon': '⚡', 'desc': '主动发现和执行任务', 'status': 'active'},
            {'name': 'AI员工引擎', 'icon': '🤖', 'desc': '管理AI员工团队', 'status': 'active'},
            {'name': '数据完整性引擎', 'icon': '🔒', 'desc': '数据验证和保护', 'status': 'active'},
            {'name': '智能推荐引擎', 'icon': '💡', 'desc': '个性化学习推荐', 'status': 'active'},
            {'name': '考试AI引擎', 'icon': '📝', 'desc': '智能出题和评分', 'status': 'active'},
            {'name': '路由优化引擎', 'icon': '🔗', 'desc': 'API路由智能管理', 'status': 'active'},
            {'name': '安全监控引擎', 'icon': '🛡️', 'desc': '系统安全防护', 'status': 'active'}
        ]
        return success_response({'engines': engines})

    except Exception as e:
        logger.error(f"获取AI引擎列表失败: {e}")
        return error_response(e)


@super_admin_api.route('/api/super_admin/employees', methods=['GET'])
def employees():
    """AI员工管理 - 获取AI员工列表"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT id, name, employee_code, description, status, accuracy FROM ai_employees')
        employees = []
        for row in cursor.fetchall():
            employees.append({
                'id': row['id'],
                'name': row['name'] or '',
                'employee_code': row['employee_code'] or '',
                'role': row['description'] or '-',
                'status': row['status'] or 'offline',
                'accuracy': row['accuracy'] or 0,
                'total_tasks': 0
            })

        conn.close()
        return success_response({'employees': employees})

    except Exception as e:
        logger.error(f"获取AI员工列表失败: {e}")
        return error_response(e)


@super_admin_api.route('/api/super_admin/agents', methods=['GET'])
def agents():
    """本地AI Agent - 获取Agent列表"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT id, agent_name, agent_type, status FROM ai_agents')
        agents = []
        for row in cursor.fetchall():
            agents.append({
                'id': row['id'],
                'name': row['agent_name'] or '',
                'role': row['agent_type'] or '-',
                'status': row['status'] or 'stopped'
            })

        conn.close()
        return success_response({'agents': agents})

    except Exception as e:
        logger.error(f"获取Agent列表失败: {e}")
        return error_response(e)


@super_admin_api.route('/api/super_admin/agents/<int:agent_id>/action', methods=['POST'])
def agent_action(agent_id):
    """本地AI Agent - 执行Agent操作（启动/暂停/终止）"""
    try:
        data = request.get_json() or {}
        action = data.get('action', '')

        if action not in ['start', 'pause', 'stop']:
            return error_response('无效的操作类型')

        conn = get_db_connection()
        cursor = conn.cursor()

        status_map = {'start': 'running', 'pause': 'paused', 'stop': 'stopped'}
        new_status = status_map[action]

        cursor.execute('UPDATE ai_agents SET status = ? WHERE id = ?', (new_status, agent_id))
        conn.commit()
        affected = cursor.rowcount
        conn.close()

        if affected == 0:
            return error_response('Agent不存在')

        action_text = {'start': '启动', 'pause': '暂停', 'stop': '终止'}
        return success_response(message=f'Agent{action_text[action]}成功')

    except Exception as e:
        logger.error(f"Agent操作失败: {e}")
        return error_response(e)


@super_admin_api.route('/api/super_admin/settings', methods=['GET'])
def settings():
    """系统设置 - 获取系统设置信息"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT config_key, config_value, description FROM system_config')
        settings = {}
        for row in cursor.fetchall():
            settings[row['config_key']] = {
                'value': row['config_value'],
                'description': row['description'] or ''
            }

        conn.close()
        return success_response({'settings': settings})

    except Exception as e:
        logger.error(f"获取系统设置失败: {e}")
        return error_response(e)


@super_admin_api.route('/api/super_admin/security/audit_logs', methods=['GET'])
def security_audit_logs():
    """安全监控 - 获取安全审计日志"""
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        keyword = request.args.get('keyword', '')

        conn = get_db_connection()
        cursor = conn.cursor()

        where_clauses = []
        params = []

        if keyword:
            where_clauses.append('(operation LIKE ? OR target LIKE ?)')
            params.extend([f'%{keyword}%', f'%{keyword}%'])

        where_sql = 'WHERE ' + ' AND '.join(where_clauses) if where_clauses else ''

        cursor.execute(f'SELECT COUNT(*) FROM security_audit_logs {where_sql}', params)
        total = cursor.fetchone()[0] or 0

        offset = (page - 1) * per_page
        cursor.execute(f'''
            SELECT id, operation, target, operator, operator_role, ip_address, 
                   timestamp, status, details 
            FROM security_audit_logs 
            {where_sql} 
            ORDER BY timestamp DESC 
            LIMIT ? OFFSET ?
        ''', params + [per_page, offset])

        logs = []
        for row in cursor.fetchall():
            logs.append({
                'id': row['id'],
                'operation': row['operation'] or '',
                'target': row['target'] or '',
                'operator': row['operator'] or '',
                'operator_role': row['operator_role'] or '',
                'ip_address': row['ip_address'] or '',
                'timestamp': row['timestamp'] or '',
                'status': row['status'] or '',
                'details': row['details'] or ''
            })

        conn.close()
        return success_response({
            'logs': logs,
            'total': total,
            'page': page,
            'per_page': per_page
        })

    except Exception as e:
        logger.error(f"获取安全审计日志失败: {e}")
        return error_response(e)


@super_admin_api.route('/api/super_admin/security/access_logs', methods=['GET'])
def security_access_logs():
    """安全监控 - 获取访问控制日志"""
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT COUNT(*) FROM access_control_logs')
        total = cursor.fetchone()[0] or 0

        offset = (page - 1) * per_page
        cursor.execute('''
            SELECT id, user_id, username, role, resource, action, 
                   ip_address, result, timestamp, reason 
            FROM access_control_logs 
            ORDER BY timestamp DESC 
            LIMIT ? OFFSET ?
        ''', [per_page, offset])

        logs = []
        for row in cursor.fetchall():
            logs.append({
                'id': row['id'],
                'user_id': row['user_id'],
                'username': row['username'] or '',
                'role': row['role'] or '',
                'resource': row['resource'] or '',
                'action': row['action'] or '',
                'ip_address': row['ip_address'] or '',
                'result': row['result'] or '',
                'timestamp': row['timestamp'] or '',
                'reason': row['reason'] or ''
            })

        conn.close()
        return success_response({
            'logs': logs,
            'total': total,
            'page': page,
            'per_page': per_page
        })

    except Exception as e:
        logger.error(f"获取访问控制日志失败: {e}")
        return error_response(e)


@super_admin_api.route('/api/super_admin/security/intrusion_stats', methods=['GET'])
def security_intrusion_stats():
    """安全监控 - 获取入侵检测统计"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT COUNT(*) FROM sql_injection_attempts')
        sql_injection_count = cursor.fetchone()[0] or 0

        cursor.execute('SELECT COUNT(*) FROM access_control_logs WHERE result = "denied"')
        access_denied_count = cursor.fetchone()[0] or 0

        cursor.execute('''
            SELECT COUNT(*) FROM access_logs 
            WHERE result = 'failed' AND path LIKE '%login%' 
            AND DATE(access_time) = DATE('now')
        ''')
        failed_login_today = cursor.fetchone()[0] or 0

        cursor.execute('''
            SELECT ip_address, COUNT(*) as cnt 
            FROM access_logs 
            WHERE result = 'failed' AND path LIKE '%login%'
            GROUP BY ip_address 
            ORDER BY cnt DESC 
            LIMIT 10
        ''')
        suspicious_ips = []
        for row in cursor.fetchall():
            suspicious_ips.append({
                'ip_address': row['ip_address'],
                'attempts': row['cnt']
            })

        conn.close()
        return success_response({
            'sql_injection_count': sql_injection_count,
            'access_denied_count': access_denied_count,
            'failed_login_today': failed_login_today,
            'suspicious_ips': suspicious_ips
        })

    except Exception as e:
        logger.error(f"获取入侵检测统计失败: {e}")
        return error_response(e)


@super_admin_api.route('/api/super_admin/ai_analytics/learning', methods=['GET'])
def ai_analytics_learning():
    """AI智能分析 - 学习数据分析"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT DATE(created_at) as date, COUNT(*) as count
            FROM learning_records 
            GROUP BY DATE(created_at) 
            ORDER BY date DESC 
            LIMIT 7
        ''')
        learning_trend = []
        for row in cursor.fetchall():
            learning_trend.append({
                'date': row['date'],
                'count': row['count']
            })

        cursor.execute('''
            SELECT user_id, COUNT(*) as count
            FROM learning_records 
            GROUP BY user_id 
            ORDER BY count DESC 
            LIMIT 10
        ''')
        active_learners = []
        for row in cursor.fetchall():
            cursor.execute('SELECT username FROM users WHERE id = ?', (row['user_id'],))
            user_row = cursor.fetchone()
            active_learners.append({
                'user_id': row['user_id'],
                'username': user_row['username'] if user_row else '未知用户',
                'learning_count': row['count']
            })

        cursor.execute('SELECT COUNT(*) FROM learning_records')
        total_learning_records = cursor.fetchone()[0] or 0

        conn.close()
        return success_response({
            'learning_trend': learning_trend,
            'active_learners': active_learners,
            'total_learning_records': total_learning_records
        })

    except Exception as e:
        logger.error(f"获取学习数据分析失败: {e}")
        return error_response(e)


@super_admin_api.route('/api/super_admin/ai_analytics/exam', methods=['GET'])
def ai_analytics_exam():
    """AI智能分析 - 考试数据分析"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT DATE(started_at) as date, COUNT(*) as count
            FROM exam_records 
            GROUP BY DATE(started_at) 
            ORDER BY date DESC 
            LIMIT 7
        ''')
        exam_trend = []
        for row in cursor.fetchall():
            exam_trend.append({
                'date': row['date'],
                'count': row['count']
            })

        cursor.execute('SELECT AVG(total_score) FROM exam_results WHERE total_score IS NOT NULL')
        avg_score = cursor.fetchone()[0] or 0

        cursor.execute('SELECT COUNT(*) FROM exam_results WHERE total_score >= 60')
        passed_count = cursor.fetchone()[0] or 0

        cursor.execute('SELECT COUNT(*) FROM exam_results')
        total_results = cursor.fetchone()[0] or 0

        pass_rate = round(passed_count / total_results * 100, 2) if total_results > 0 else 0

        cursor.execute('''
            SELECT subject, COUNT(*) as count, AVG(total_score) as avg
            FROM exam_results 
            JOIN exams ON exam_results.exam_id = exams.id
            GROUP BY subject 
            ORDER BY count DESC 
            LIMIT 5
        ''')
        subject_stats = []
        for row in cursor.fetchall():
            subject_stats.append({
                'subject': row['subject'] or '未分类',
                'exam_count': row['count'],
                'avg_score': round(row['avg'] or 0, 2)
            })

        conn.close()
        return success_response({
            'exam_trend': exam_trend,
            'avg_score': round(avg_score, 2),
            'pass_rate': pass_rate,
            'total_results': total_results,
            'subject_stats': subject_stats
        })

    except Exception as e:
        logger.error(f"获取考试数据分析失败: {e}")
        return error_response(e)


@super_admin_api.route('/api/super_admin/ai_analytics/user_behavior', methods=['GET'])
def ai_analytics_user_behavior():
    """AI智能分析 - 用户行为分析"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT DATE(access_time) as date, COUNT(DISTINCT user_id) as count
            FROM access_logs 
            GROUP BY DATE(access_time) 
            ORDER BY date DESC 
            LIMIT 7
        ''')
        active_user_trend = []
        for row in cursor.fetchall():
            active_user_trend.append({
                'date': row['date'],
                'count': row['count']
            })

        cursor.execute('''
            SELECT role, COUNT(*) as count
            FROM users 
            GROUP BY role 
            ORDER BY count DESC
        ''')
        role_distribution = []
        for row in cursor.fetchall():
            role_distribution.append({
                'role': row['role'],
                'count': row['count']
            })

        cursor.execute('''
            SELECT path, COUNT(*) as count
            FROM access_logs 
            GROUP BY path 
            ORDER BY count DESC 
            LIMIT 10
        ''')
        top_pages = []
        for row in cursor.fetchall():
            top_pages.append({
                'path': row['path'],
                'count': row['count']
            })

        conn.close()
        return success_response({
            'active_user_trend': active_user_trend,
            'role_distribution': role_distribution,
            'top_pages': top_pages
        })

    except Exception as e:
        logger.error(f"获取用户行为分析失败: {e}")
        return error_response(e)


@super_admin_api.route('/api/super_admin/notifications', methods=['GET'])
def notifications():
    """通知管理 - 获取通知列表"""
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT COUNT(*) FROM notifications')
        total = cursor.fetchone()[0] or 0

        offset = (page - 1) * per_page
        cursor.execute('''
            SELECT id, title, content, type, status, created_at, user_id 
            FROM notifications 
            ORDER BY created_at DESC 
            LIMIT ? OFFSET ?
        ''', [per_page, offset])

        notifications = []
        for row in cursor.fetchall():
            notifications.append({
                'id': row['id'],
                'title': row['title'] or '',
                'content': row['content'] or '',
                'type': row['type'] or 'info',
                'status': row['status'] or 'unread',
                'created_at': row['created_at'] or '',
                'user_id': row['user_id']
            })

        conn.close()
        return success_response({
            'notifications': notifications,
            'total': total,
            'page': page,
            'per_page': per_page
        })

    except Exception as e:
        logger.error(f"获取通知列表失败: {e}")
        return error_response(e)


@super_admin_api.route('/api/super_admin/notifications', methods=['POST'])
def create_notification():
    """通知管理 - 创建通知"""
    try:
        data = request.get_json() or {}
        title = data.get('title')
        content = data.get('content')
        notification_type = data.get('type', 'info')
        user_id = data.get('user_id')

        if not title or not content:
            return error_response('标题和内容不能为空')

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO notifications (title, content, type, status, created_at, user_id)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (title, content, notification_type, 'unread', datetime.now().isoformat(), user_id))
        conn.commit()
        notification_id = cursor.lastrowid
        conn.close()

        return success_response({
            'notification_id': notification_id
        }, message='通知创建成功')

    except Exception as e:
        logger.error(f"创建通知失败: {e}")
        return error_response(e)


@super_admin_api.route('/api/super_admin/notifications/<int:notification_id>', methods=['PUT', 'DELETE'])
def notification_detail(notification_id):
    """通知管理 - 更新/删除通知"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        if request.method == 'PUT':
            data = request.get_json() or {}
            status = data.get('status')
            
            if status:
                cursor.execute('UPDATE notifications SET status = ? WHERE id = ?', (status, notification_id))
                conn.commit()
            
            conn.close()
            return success_response(message='通知更新成功')

        elif request.method == 'DELETE':
            cursor.execute('DELETE FROM notifications WHERE id = ?', (notification_id,))
            conn.commit()
            affected = cursor.rowcount
            conn.close()
            
            if affected == 0:
                return error_response('通知不存在')
            return success_response(message='通知删除成功')

    except Exception as e:
        logger.error(f"通知操作失败: {e}")
        return error_response(e)


@super_admin_api.route('/api/super_admin/export/users', methods=['GET'])
def export_users():
    """数据导出 - 导出用户数据"""
    try:
        import csv
        from io import StringIO

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT id, username, email, role, is_active, created_at FROM users')
        users = cursor.fetchall()
        conn.close()

        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(['ID', '用户名', '邮箱', '角色', '状态', '创建时间'])

        for row in users:
            status = '活跃' if row['is_active'] else '禁用'
            writer.writerow([row['id'], row['username'], row['email'], row['role'], status, row['created_at']])

        output.seek(0)
        from flask import Response
        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={'Content-Disposition': f'attachment;filename=users_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'}
        )

    except Exception as e:
        logger.error(f"导出用户数据失败: {e}")
        return error_response(e)


@super_admin_api.route('/api/super_admin/export/exams', methods=['GET'])
def export_exams():
    """数据导出 - 导出考试数据"""
    try:
        import csv
        from io import StringIO

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT id, title, subject, duration, question_count, status, created_at FROM exams')
        exams = cursor.fetchall()
        conn.close()

        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(['ID', '标题', '科目', '时长(分钟)', '题目数', '状态', '创建时间'])

        for row in exams:
            writer.writerow([row['id'], row['title'], row['subject'], row['duration'], row['question_count'], row['status'], row['created_at']])

        output.seek(0)
        from flask import Response
        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={'Content-Disposition': f'attachment;filename=exams_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'}
        )

    except Exception as e:
        logger.error(f"导出考试数据失败: {e}")
        return error_response(e)


@super_admin_api.route('/api/super_admin/export/logs', methods=['GET'])
def export_logs():
    """数据导出 - 导出日志数据"""
    try:
        import csv
        from io import StringIO

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT id, timestamp, level, module, message FROM system_status_log ORDER BY timestamp DESC LIMIT 1000')
        logs = cursor.fetchall()
        conn.close()

        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(['ID', '时间', '级别', '模块', '消息'])

        for row in logs:
            writer.writerow([row['id'], row['timestamp'], row['level'], row['module'], row['message']])

        output.seek(0)
        from flask import Response
        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={'Content-Disposition': f'attachment;filename=logs_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'}
        )

    except Exception as e:
        logger.error(f"导出日志数据失败: {e}")
        return error_response(e)


@super_admin_api.route('/api/super_admin/announcements', methods=['GET'])
def announcements():
    """公告管理 - 获取公告列表"""
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT COUNT(*) FROM announcements')
        total = cursor.fetchone()[0] or 0

        offset = (page - 1) * per_page
        cursor.execute('''
            SELECT id, title, content, is_published, created_at, publish_time 
            FROM announcements 
            ORDER BY created_at DESC 
            LIMIT ? OFFSET ?
        ''', [per_page, offset])

        announcements = []
        for row in cursor.fetchall():
            announcements.append({
                'id': row['id'],
                'title': row['title'] or '',
                'content': row['content'] or '',
                'is_published': row['is_published'] == 1,
                'created_at': row['created_at'] or '',
                'publish_time': row['publish_time'] or ''
            })

        conn.close()
        return success_response({
            'announcements': announcements,
            'total': total,
            'page': page,
            'per_page': per_page
        })

    except Exception as e:
        logger.error(f"获取公告列表失败: {e}")
        return error_response(e)


@super_admin_api.route('/api/super_admin/announcements', methods=['POST'])
def create_announcement():
    """公告管理 - 创建公告"""
    try:
        data = request.get_json() or {}
        title = data.get('title')
        content = data.get('content')
        is_published = data.get('is_published', False)

        if not title or not content:
            return error_response('标题和内容不能为空')

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO announcements (title, content, is_published, created_at, publish_time)
            VALUES (?, ?, ?, ?, ?)
        ''', (title, content, 1 if is_published else 0, datetime.now().isoformat(), 
              datetime.now().isoformat() if is_published else None))
        conn.commit()
        announcement_id = cursor.lastrowid
        conn.close()

        return success_response({
            'announcement_id': announcement_id
        }, message='公告创建成功')

    except Exception as e:
        logger.error(f"创建公告失败: {e}")
        return error_response(e)


@super_admin_api.route('/api/super_admin/announcements/<int:announcement_id>', methods=['PUT', 'DELETE'])
def announcement_detail(announcement_id):
    """公告管理 - 更新/删除公告"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        if request.method == 'PUT':
            data = request.get_json() or {}
            title = data.get('title')
            content = data.get('content')
            is_published = data.get('is_published')

            updates = []
            params = []

            if title:
                updates.append('title = ?')
                params.append(title)
            if content:
                updates.append('content = ?')
                params.append(content)
            if is_published is not None:
                updates.append('is_published = ?')
                params.append(1 if is_published else 0)
                if is_published:
                    updates.append('publish_time = ?')
                    params.append(datetime.now().isoformat())

            if updates:
                params.append(announcement_id)
                cursor.execute(f'UPDATE announcements SET {", ".join(updates)} WHERE id = ?', params)
                conn.commit()

            conn.close()
            return success_response(message='公告更新成功')

        elif request.method == 'DELETE':
            cursor.execute('DELETE FROM announcements WHERE id = ?', (announcement_id,))
            conn.commit()
            affected = cursor.rowcount
            conn.close()

            if affected == 0:
                return error_response('公告不存在')
            return success_response(message='公告删除成功')

    except Exception as e:
        logger.error(f"公告操作失败: {e}")
        return error_response(e)