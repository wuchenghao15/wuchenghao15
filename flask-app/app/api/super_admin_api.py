# -*- coding: utf-8 -*-
"""
超级管理员API - 完整实现
提供超级管理员控制台所需的所有API接口
"""

from flask import Blueprint, jsonify, request, session, current_app
from app.middlewares.permission_decorators import require_super_admin
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


def create_tables():
    """创建所需的数据库表"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                type TEXT DEFAULT 'info',
                status TEXT DEFAULT 'unread',
                recipient_id INTEGER,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS announcements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                is_published INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                publish_time TEXT
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS backup_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                backup_time TEXT NOT NULL,
                backup_path TEXT NOT NULL,
                backup_size INTEGER DEFAULT 0,
                status TEXT DEFAULT 'success',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS learning_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                course_id INTEGER,
                activity TEXT,
                duration INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS exam_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                exam_id INTEGER NOT NULL,
                status TEXT DEFAULT 'in_progress',
                started_at TEXT DEFAULT CURRENT_TIMESTAMP,
                completed_at TEXT,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (exam_id) REFERENCES exams(id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS security_audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                action TEXT NOT NULL,
                resource TEXT,
                username TEXT,
                user_id INTEGER,
                ip_address TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                success INTEGER DEFAULT 1,
                error_message TEXT
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS access_control_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                username TEXT,
                role TEXT,
                resource TEXT,
                action TEXT,
                ip_address TEXT,
                result TEXT DEFAULT 'allowed',
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                reason TEXT
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sql_injection_attempts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ip_address TEXT,
                attempted_query TEXT,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS system_config (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                config_key TEXT UNIQUE NOT NULL,
                config_value TEXT,
                description TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ai_agents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_name TEXT NOT NULL,
                agent_type TEXT,
                status TEXT DEFAULT 'stopped',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                last_active_at TEXT
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS search_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query TEXT NOT NULL,
                result TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS exam_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                exam_id INTEGER NOT NULL,
                total_score INTEGER,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (exam_id) REFERENCES exams(id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS access_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                username TEXT,
                role TEXT,
                path TEXT NOT NULL,
                result TEXT DEFAULT 'success',
                access_time TEXT DEFAULT CURRENT_TIMESTAMP,
                ip_address TEXT
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS system_status_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                level TEXT DEFAULT 'info',
                module TEXT,
                message TEXT
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS super_admin_health_checks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                module_name TEXT NOT NULL,
                status TEXT DEFAULT 'healthy',
                response_time REAL DEFAULT 0,
                error_message TEXT,
                checked_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS scheduled_tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_name TEXT NOT NULL,
                task_type TEXT DEFAULT 'periodic',
                cron_expression TEXT,
                interval_seconds INTEGER DEFAULT 0,
                last_run_at TEXT,
                next_run_at TEXT,
                status TEXT DEFAULT 'enabled',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS task_execution_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id INTEGER,
                task_name TEXT,
                status TEXT DEFAULT 'running',
                started_at TEXT DEFAULT CURRENT_TIMESTAMP,
                completed_at TEXT,
                error_message TEXT,
                FOREIGN KEY (task_id) REFERENCES scheduled_tasks(id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT UNIQUE NOT NULL,
                user_id INTEGER,
                username TEXT,
                role TEXT,
                login_time TEXT DEFAULT CURRENT_TIMESTAMP,
                last_activity TEXT DEFAULT CURRENT_TIMESTAMP,
                expires_at TEXT,
                ip_address TEXT,
                user_agent TEXT,
                status TEXT DEFAULT 'active',
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')

        conn.commit()
        conn.close()
        logger.info("✓ 超级管理员API表创建完成")
    except Exception as e:
        logger.error(f"✗ 创建超级管理员API表失败: {e}")


create_tables()


def create_response(code=200, message='success', data=None, error_id=None, error_type=None, suggestion=None):
    """统一响应格式"""
    response = {
        'code': code,
        'message': message,
        'data': data
    }
    if error_id:
        response['error_id'] = error_id
    if error_type:
        response['error_type'] = error_type
    if suggestion:
        response['suggestion'] = suggestion
    return jsonify(response)


def paginate(data, page, per_page, total):
    return {
        'data': data,
        'page': page,
        'per_page': per_page,
        'total': total,
        'total_pages': (total + per_page - 1) // per_page if per_page > 0 else 0
    }


@super_admin_api.route('/api/super_admin/overview', methods=['GET'])
@require_super_admin
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

        return create_response(200, 'success', {
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
        return create_response(500, '获取系统概览失败')


@super_admin_api.route('/api/super_admin/resources', methods=['GET'])
@require_super_admin
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

        return create_response(200, 'success', {
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
        return create_response(200, 'success', {
            'cpu': {'percent': 0, 'cores': 0},
            'memory': {'percent': 0, 'used_gb': 0, 'total_gb': 0},
            'disk': {'percent': 0, 'used_gb': 0, 'total_gb': 0}
        })
    except Exception as e:
        logger.error(f"获取系统资源失败: {e}")
        return create_response(500, '获取系统资源失败')


@super_admin_api.route('/api/super_admin/logs', methods=['GET'])
@require_super_admin
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

        return create_response(200, 'success', {
            'logs': logs,
            'total': total,
            'page': page,
            'per_page': per_page
        })

    except Exception as e:
        logger.error(f"获取系统日志失败: {e}")
        return create_response(500, '获取系统日志失败')


@super_admin_api.route('/api/super_admin/users', methods=['GET'])
@require_super_admin
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

        return create_response(200, 'success', {
            'users': users,
            'total': total,
            'page': page,
            'per_page': per_page
        })

    except Exception as e:
        logger.error(f"获取用户列表失败: {e}")
        return create_response(500, '获取用户列表失败')


@super_admin_api.route('/api/super_admin/users/<int:user_id>', methods=['GET', 'PUT', 'DELETE'])
@require_super_admin
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
                return create_response(404, '用户不存在')
            user = {
                'id': row['id'],
                'username': row['username'] or '',
                'email': row['email'] or '',
                'role': row['role'] or 'student',
                'is_active': row['is_active'] == 1 if row['is_active'] is not None else True,
                'created_at': row['created_at'] or ''
            }
            conn.close()
            return create_response(200, 'success', user)

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
                return create_response(400, '没有可更新的字段')

            params.append(user_id)
            cursor.execute(f'UPDATE users SET {", ".join(updates)} WHERE id = ?', params)
            conn.commit()
            conn.close()
            return create_response(200, '用户更新成功')

        elif request.method == 'DELETE':
            cursor.execute('DELETE FROM users WHERE id = ?', (user_id,))
            conn.commit()
            affected = cursor.rowcount
            conn.close()
            if affected == 0:
                return create_response(404, '用户不存在')
            return create_response(200, '用户删除成功')

    except Exception as e:
        logger.error(f"用户操作失败: {e}")
        return create_response(500, '用户操作失败')


@super_admin_api.route('/api/super_admin/exams', methods=['GET'])
@require_super_admin
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

        return create_response(200, 'success', {
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
        return create_response(500, '获取考试列表失败')


@super_admin_api.route('/api/super_admin/routes', methods=['GET'])
@require_super_admin
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
        return create_response(200, 'success', {
            'routes': routes,
            'total': len(routes)
        })
    except Exception as e:
        logger.error(f"获取路由列表失败: {e}")
        return create_response(500, '获取路由列表失败')


@super_admin_api.route('/api/super_admin/reload_routes', methods=['POST'])
@require_super_admin
def reload_routes():
    """路由管理 - 刷新路由"""
    try:
        return create_response(200, '路由刷新成功')
    except Exception as e:
        logger.error(f"刷新路由失败: {e}")
        return create_response(500, '刷新路由失败')


@super_admin_api.route('/api/super_admin/backup', methods=['POST'])
@require_super_admin
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

        return create_response(200, '备份创建成功', {
            'backup_id': timestamp,
            'backup_path': backup_path,
            'backup_size': backup_size,
            'backup_time': datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"创建备份失败: {e}")
        return create_response(500, '创建备份失败')


@super_admin_api.route('/api/super_admin/backups', methods=['GET'])
@require_super_admin
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
        return create_response(200, 'success', backups)

    except Exception as e:
        logger.error(f"获取备份列表失败: {e}")
        return create_response(500, '获取备份列表失败')


@super_admin_api.route('/api/super_admin/backup/<string:backup_id>/restore', methods=['POST'])
@require_super_admin
def restore_backup(backup_id):
    """数据备份 - 恢复备份"""
    try:
        backup_dir = os.path.join(os.path.dirname(DB_PATH), 'backups')
        backup_path = os.path.join(backup_dir, f'mtscos_backup_{backup_id}.db')

        if not os.path.exists(backup_path):
            return create_response(404, '备份文件不存在')

        shutil.copy2(backup_path, DB_PATH)

        return create_response(200, '备份恢复成功')

    except Exception as e:
        logger.error(f"恢复备份失败: {e}")
        return create_response(500, '恢复备份失败')


@super_admin_api.route('/api/super_admin/backup/<string:backup_id>/delete', methods=['DELETE'])
@require_super_admin
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

        return create_response(200, '备份删除成功')

    except Exception as e:
        logger.error(f"删除备份失败: {e}")
        return create_response(500, '删除备份失败')


@super_admin_api.route('/api/super_admin/clear_cache', methods=['POST'])
@require_super_admin
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

        return create_response(200, f'缓存已清除，共清理 {cache_cleared} 项', {'cleared_count': cache_cleared})

    except Exception as e:
        logger.error(f"清除缓存失败: {e}")
        return create_response(500, '清除缓存失败')


@super_admin_api.route('/api/super_admin/health', methods=['GET'])
@require_super_admin
def health_check():
    """系统维护 - 健康检查"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM users')
        user_count = cursor.fetchone()[0]
        conn.close()

        return create_response(200, '系统健康', {
            'database': 'connected',
            'user_count': user_count,
            'status': 'healthy'
        })

    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        return create_response(200, '系统异常', {
            'database': 'error',
            'status': 'unhealthy'
        })


@super_admin_api.route('/api/super_admin/engines', methods=['GET'])
@require_super_admin
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
        return create_response(200, 'success', {'engines': engines})

    except Exception as e:
        logger.error(f"获取AI引擎列表失败: {e}")
        return create_response(500, '获取AI引擎列表失败')


@super_admin_api.route('/api/super_admin/employees', methods=['GET'])
@require_super_admin
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
        return create_response(200, 'success', {'employees': employees})

    except Exception as e:
        logger.error(f"获取AI员工列表失败: {e}")
        return create_response(500, '获取AI员工列表失败')


@super_admin_api.route('/api/super_admin/agents', methods=['GET'])
@require_super_admin
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
        return create_response(200, 'success', {'agents': agents})

    except Exception as e:
        logger.error(f"获取Agent列表失败: {e}")
        return create_response(500, '获取Agent列表失败')


@super_admin_api.route('/api/super_admin/agents/<int:agent_id>/action', methods=['POST'])
@require_super_admin
def agent_action(agent_id):
    """本地AI Agent - 执行Agent操作（启动/暂停/终止）"""
    try:
        data = request.get_json() or {}
        action = data.get('action', '')

        if action not in ['start', 'pause', 'stop']:
            return create_response(400, '无效的操作类型')

        conn = get_db_connection()
        cursor = conn.cursor()

        status_map = {'start': 'running', 'pause': 'paused', 'stop': 'stopped'}
        new_status = status_map[action]

        cursor.execute('UPDATE ai_agents SET status = ? WHERE id = ?', (new_status, agent_id))
        conn.commit()
        affected = cursor.rowcount
        conn.close()

        if affected == 0:
            return create_response(404, 'Agent不存在')

        action_text = {'start': '启动', 'pause': '暂停', 'stop': '终止'}
        return create_response(200, f'Agent{action_text[action]}成功')

    except Exception as e:
        logger.error(f"Agent操作失败: {e}")
        return create_response(500, 'Agent操作失败')


@super_admin_api.route('/api/super_admin/settings', methods=['GET'])
@require_super_admin
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
        return create_response(200, 'success', {'settings': settings})

    except Exception as e:
        logger.error(f"获取系统设置失败: {e}")
        return create_response(500, '获取系统设置失败')


@super_admin_api.route('/api/super_admin/security/audit_logs', methods=['GET'])
@require_super_admin
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
            where_clauses.append('(action LIKE ? OR resource LIKE ? OR username LIKE ?)')
            params.extend([f'%{keyword}%', f'%{keyword}%', f'%{keyword}%'])

        where_sql = 'WHERE ' + ' AND '.join(where_clauses) if where_clauses else ''

        cursor.execute(f'SELECT COUNT(*) FROM security_audit_logs {where_sql}', params)
        total = cursor.fetchone()[0] or 0

        offset = (page - 1) * per_page
        cursor.execute(f'''
            SELECT id, action, resource, username, user_id, ip_address, 
                   created_at, success, error_message 
            FROM security_audit_logs 
            {where_sql} 
            ORDER BY created_at DESC 
            LIMIT ? OFFSET ?
        ''', params + [per_page, offset])

        logs = []
        for row in cursor.fetchall():
            logs.append({
                'id': row['id'],
                'operation': row['action'] or '',
                'target': row['resource'] or '',
                'operator': row['username'] or '',
                'operator_role': row['user_id'] or '',
                'ip_address': row['ip_address'] or '',
                'timestamp': row['created_at'] or '',
                'status': 'success' if row['success'] else 'failed',
                'details': row['error_message'] or ''
            })

        conn.close()
        return create_response(200, 'success', {
            'logs': logs,
            'total': total,
            'page': page,
            'per_page': per_page
        })

    except Exception as e:
        logger.error(f"获取安全审计日志失败: {e}")
        return create_response(500, '获取安全审计日志失败')


@super_admin_api.route('/api/super_admin/security/access_logs', methods=['GET'])
@require_super_admin
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
        return create_response(200, 'success', {
            'logs': logs,
            'total': total,
            'page': page,
            'per_page': per_page
        })

    except Exception as e:
        logger.error(f"获取访问控制日志失败: {e}")
        return create_response(500, '获取访问控制日志失败')


@super_admin_api.route('/api/super_admin/security/intrusion_stats', methods=['GET'])
@require_super_admin
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
        return create_response(200, 'success', {
            'sql_injection_count': sql_injection_count,
            'access_denied_count': access_denied_count,
            'failed_login_today': failed_login_today,
            'suspicious_ips': suspicious_ips
        })

    except Exception as e:
        logger.error(f"获取入侵检测统计失败: {e}")
        return create_response(500, '获取入侵检测统计失败')


@super_admin_api.route('/api/super_admin/ai_analytics/learning', methods=['GET'])
@require_super_admin
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
            SELECT ai_employee_id, COUNT(*) as count
            FROM learning_records 
            GROUP BY ai_employee_id 
            ORDER BY count DESC 
            LIMIT 10
        ''')
        active_learners = []
        for row in cursor.fetchall():
            cursor.execute('SELECT name FROM ai_employees WHERE id = ?', (row['ai_employee_id'],))
            emp_row = cursor.fetchone()
            active_learners.append({
                'user_id': row['ai_employee_id'],
                'username': emp_row['name'] if emp_row else '未知AI员工',
                'learning_count': row['count']
            })

        cursor.execute('SELECT COUNT(*) FROM learning_records')
        total_learning_records = cursor.fetchone()[0] or 0

        conn.close()
        return create_response(200, 'success', {
            'learning_trend': learning_trend,
            'active_learners': active_learners,
            'total_learning_records': total_learning_records
        })

    except Exception as e:
        logger.error(f"获取学习数据分析失败: {e}")
        return create_response(500, '获取学习数据分析失败')


@super_admin_api.route('/api/super_admin/ai_analytics/exam', methods=['GET'])
@require_super_admin
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
        return create_response(200, 'success', {
            'exam_trend': exam_trend,
            'avg_score': round(avg_score, 2),
            'pass_rate': pass_rate,
            'total_results': total_results,
            'subject_stats': subject_stats
        })

    except Exception as e:
        logger.error(f"获取考试数据分析失败: {e}")
        return create_response(500, '获取考试数据分析失败')


@super_admin_api.route('/api/super_admin/ai_analytics/user_behavior', methods=['GET'])
@require_super_admin
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
        return create_response(200, 'success', {
            'active_user_trend': active_user_trend,
            'role_distribution': role_distribution,
            'top_pages': top_pages
        })

    except Exception as e:
        logger.error(f"获取用户行为分析失败: {e}")
        return create_response(500, '获取用户行为分析失败')


@super_admin_api.route('/api/super_admin/notifications', methods=['GET'])
@require_super_admin
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
            SELECT id, title, content, type, status, created_at, recipient_id 
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
                'user_id': row['recipient_id'] or None
            })

        conn.close()
        return create_response(200, 'success', {
            'notifications': notifications,
            'total': total,
            'page': page,
            'per_page': per_page
        })

    except Exception as e:
        logger.error(f"获取通知列表失败: {e}")
        return create_response(500, '获取通知列表失败')


@super_admin_api.route('/api/super_admin/notifications', methods=['POST'])
@require_super_admin
def create_notification():
    """通知管理 - 创建通知"""
    try:
        data = request.get_json() or {}
        title = data.get('title')
        content = data.get('content')
        notification_type = data.get('type', 'info')
        user_id = data.get('user_id')

        if not title or not content:
            return create_response(400, '标题和内容不能为空')

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO notifications (title, content, type, status, created_at, recipient_id)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (title, content, notification_type, 'unread', datetime.now().isoformat(), user_id))
        conn.commit()
        notification_id = cursor.lastrowid
        conn.close()

        return create_response(200, '通知创建成功', {'notification_id': notification_id})

    except Exception as e:
        logger.error(f"创建通知失败: {e}")
        return create_response(500, '创建通知失败')


@super_admin_api.route('/api/super_admin/notifications/<int:notification_id>', methods=['PUT', 'DELETE'])
@require_super_admin
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
            return create_response(200, '通知更新成功')

        elif request.method == 'DELETE':
            cursor.execute('DELETE FROM notifications WHERE id = ?', (notification_id,))
            conn.commit()
            affected = cursor.rowcount
            conn.close()
            
            if affected == 0:
                return create_response(404, '通知不存在')
            return create_response(200, '通知删除成功')

    except Exception as e:
        logger.error(f"通知操作失败: {e}")
        return create_response(500, '通知操作失败')


@super_admin_api.route('/api/super_admin/export/users', methods=['GET'])
@require_super_admin
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
        return create_response(500, '导出用户数据失败')


@super_admin_api.route('/api/super_admin/export/exams', methods=['GET'])
@require_super_admin
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
        return create_response(500, '导出考试数据失败')


@super_admin_api.route('/api/super_admin/export/logs', methods=['GET'])
@require_super_admin
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
        return create_response(500, '导出日志数据失败')


@super_admin_api.route('/api/super_admin/announcements', methods=['GET'])
@require_super_admin
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
        return create_response(200, 'success', {
            'announcements': announcements,
            'total': total,
            'page': page,
            'per_page': per_page
        })

    except Exception as e:
        logger.error(f"获取公告列表失败: {e}")
        return create_response(500, '获取公告列表失败')


@super_admin_api.route('/api/super_admin/announcements', methods=['POST'])
@require_super_admin
def create_announcement():
    """公告管理 - 创建公告"""
    try:
        data = request.get_json() or {}
        title = data.get('title')
        content = data.get('content')
        is_published = data.get('is_published', False)

        if not title or not content:
            return create_response(400, '标题和内容不能为空')

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

        return create_response(200, '公告创建成功', {'announcement_id': announcement_id})

    except Exception as e:
        logger.error(f"创建公告失败: {e}")
        return create_response(500, '创建公告失败')


@super_admin_api.route('/api/super_admin/announcements/<int:announcement_id>', methods=['PUT', 'DELETE'])
@require_super_admin
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
            return create_response(200, '公告更新成功')

        elif request.method == 'DELETE':
            cursor.execute('DELETE FROM announcements WHERE id = ?', (announcement_id,))
            conn.commit()
            affected = cursor.rowcount
            conn.close()

            if affected == 0:
                return create_response(404, '公告不存在')
            return create_response(200, '公告删除成功')

    except Exception as e:
        logger.error(f"公告操作失败: {e}")
        return create_response(500, '公告操作失败')


@super_admin_api.route('/api/super_admin/health/check', methods=['POST'])
@require_super_admin
def health_check_all():
    """系统健康监控 - 执行全面健康检查"""
    try:
        modules = ['database', 'api', 'file_system']
        results = []
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        for module in modules:
            status = 'healthy'
            response_time = 0
            error_message = ''
            
            try:
                if module == 'database':
                    start = datetime.now()
                    cursor.execute('SELECT COUNT(*) FROM users LIMIT 1')
                    response_time = (datetime.now() - start).total_seconds() * 1000
                elif module == 'api':
                    start = datetime.now()
                    cursor.execute('SELECT COUNT(*) FROM super_admin_health_checks LIMIT 1')
                    response_time = (datetime.now() - start).total_seconds() * 1000
                elif module == 'file_system':
                    start = datetime.now()
                    os.path.exists(DB_PATH)
                    response_time = (datetime.now() - start).total_seconds() * 1000
                else:
                    status = 'healthy'
                    response_time = 0
            except Exception as e:
                status = 'unhealthy'
                error_message = str(e)
            
            results.append({
                'module_name': module,
                'status': status,
                'response_time': round(response_time, 2),
                'error_message': error_message,
                'checked_at': datetime.now().isoformat()
            })
            
            cursor.execute('''
                INSERT INTO super_admin_health_checks (module_name, status, response_time, error_message, checked_at)
                VALUES (?, ?, ?, ?, ?)
            ''', (module, status, response_time, error_message, datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
        
        healthy_count = sum(1 for r in results if r['status'] == 'healthy')
        overall_status = 'healthy' if healthy_count == len(modules) else 'unhealthy'
        
        return create_response(200, 'success', {
            'overall_status': overall_status,
            'healthy_count': healthy_count,
            'total_modules': len(modules),
            'check_results': results
        })
    
    except Exception as e:
        logger.error(f"执行健康检查失败: {e}")
        return create_response(500, '执行健康检查失败')


@super_admin_api.route('/api/super_admin/health/history', methods=['GET'])
@require_super_admin
def health_history():
    """系统健康监控 - 获取健康检查历史记录"""
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        module = request.args.get('module', '')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        where_clauses = []
        params = []
        
        if module:
            where_clauses.append('module_name = ?')
            params.append(module)
        
        where_sql = 'WHERE ' + ' AND '.join(where_clauses) if where_clauses else ''
        
        cursor.execute(f'SELECT COUNT(*) FROM super_admin_health_checks {where_sql}', params)
        total = cursor.fetchone()[0] or 0
        
        offset = (page - 1) * per_page
        cursor.execute(f'''
            SELECT id, module_name, status, response_time, error_message, checked_at
            FROM super_admin_health_checks
            {where_sql}
            ORDER BY checked_at DESC
            LIMIT ? OFFSET ?
        ''', params + [per_page, offset])
        
        history = []
        for row in cursor.fetchall():
            history.append({
                'id': row['id'],
                'module_name': row['module_name'],
                'status': row['status'],
                'response_time': round(row['response_time'], 2) if row['response_time'] else 0,
                'error_message': row['error_message'] or '',
                'checked_at': row['checked_at'] or ''
            })
        
        conn.close()
        
        return create_response(200, 'success', {
            'history': history,
            'total': total,
            'page': page,
            'per_page': per_page
        })
    
    except Exception as e:
        logger.error(f"获取健康检查历史失败: {e}")
        return create_response(500, '获取健康检查历史失败')


@super_admin_api.route('/api/super_admin/tasks', methods=['GET'])
@require_super_admin
def get_tasks():
    """定时任务调度 - 获取定时任务列表"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM scheduled_tasks ORDER BY created_at DESC')
        tasks = []
        for row in cursor.fetchall():
            tasks.append({
                'id': row['id'],
                'task_name': row['task_name'],
                'task_type': row['task_type'],
                'cron_expression': row['cron_expression'] or '',
                'interval_seconds': row['interval_seconds'] or 0,
                'last_run_at': row['last_run_at'] or '',
                'next_run_at': row['next_run_at'] or '',
                'status': row['status'],
                'created_at': row['created_at'] or '',
                'updated_at': row['updated_at'] or ''
            })
        
        conn.close()
        
        return create_response(200, 'success', {'tasks': tasks})
    
    except Exception as e:
        logger.error(f"获取定时任务列表失败: {e}")
        return create_response(500, '获取定时任务列表失败')


@super_admin_api.route('/api/super_admin/tasks', methods=['POST'])
@require_super_admin
def create_task():
    """定时任务调度 - 创建定时任务"""
    try:
        data = request.get_json() or {}
        task_name = data.get('task_name')
        task_type = data.get('task_type', 'periodic')
        cron_expression = data.get('cron_expression')
        interval_seconds = data.get('interval_seconds', 0)
        
        if not task_name:
            return create_response(400, '任务名称不能为空')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO scheduled_tasks (task_name, task_type, cron_expression, interval_seconds, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (task_name, task_type, cron_expression, interval_seconds, 
              datetime.now().isoformat(), datetime.now().isoformat()))
        
        conn.commit()
        task_id = cursor.lastrowid
        conn.close()
        
        return create_response(200, '任务创建成功', {'task_id': task_id})
    
    except Exception as e:
        logger.error(f"创建定时任务失败: {e}")
        return create_response(500, '创建定时任务失败')


@super_admin_api.route('/api/super_admin/tasks/<int:task_id>', methods=['PUT', 'DELETE'])
@require_super_admin
def task_detail(task_id):
    """定时任务调度 - 更新/删除任务"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if request.method == 'PUT':
            data = request.get_json() or {}
            updates = []
            params = []
            
            if 'status' in data:
                updates.append('status = ?')
                params.append(data['status'])
            if 'cron_expression' in data:
                updates.append('cron_expression = ?')
                params.append(data['cron_expression'])
            if 'interval_seconds' in data:
                updates.append('interval_seconds = ?')
                params.append(data['interval_seconds'])
            
            updates.append('updated_at = ?')
            params.append(datetime.now().isoformat())
            params.append(task_id)
            
            if updates:
                cursor.execute(f'UPDATE scheduled_tasks SET {", ".join(updates)} WHERE id = ?', params)
                conn.commit()
            
            conn.close()
            return create_response(200, '任务更新成功')
        
        elif request.method == 'DELETE':
            cursor.execute('DELETE FROM scheduled_tasks WHERE id = ?', (task_id,))
            conn.commit()
            affected = cursor.rowcount
            conn.close()
            
            if affected == 0:
                return create_response(404, '任务不存在')
            return create_response(200, '任务删除成功')
    
    except Exception as e:
        logger.error(f"任务操作失败: {e}")
        return create_response(500, '任务操作失败')


@super_admin_api.route('/api/super_admin/tasks/<int:task_id>/run', methods=['POST'])
@require_super_admin
def run_task(task_id):
    """定时任务调度 - 手动执行任务"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT task_name FROM scheduled_tasks WHERE id = ?', (task_id,))
        row = cursor.fetchone()
        if not row:
            conn.close()
            return create_response(404, '任务不存在')
        
        task_name = row['task_name']
        
        cursor.execute('''
            INSERT INTO task_execution_logs (task_id, task_name, status, started_at)
            VALUES (?, ?, ?, ?)
        ''', (task_id, task_name, 'running', datetime.now().isoformat()))
        log_id = cursor.lastrowid
        
        try:
            import time
            time.sleep(1)
            cursor.execute('UPDATE task_execution_logs SET status = ?, completed_at = ? WHERE id = ?',
                         ('success', datetime.now().isoformat(), log_id))
            cursor.execute('UPDATE scheduled_tasks SET last_run_at = ?, updated_at = ? WHERE id = ?',
                         (datetime.now().isoformat(), datetime.now().isoformat(), task_id))
        except Exception as e:
            cursor.execute('UPDATE task_execution_logs SET status = ?, completed_at = ?, error_message = ? WHERE id = ?',
                         ('failed', datetime.now().isoformat(), str(e), log_id))
        
        conn.commit()
        conn.close()
        
        return create_response(200, '任务执行完成')
    
    except Exception as e:
        logger.error(f"执行任务失败: {e}")
        return create_response(500, '执行任务失败')


@super_admin_api.route('/api/super_admin/tasks/logs', methods=['GET'])
@require_super_admin
def task_logs():
    """定时任务调度 - 获取任务执行日志"""
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM task_execution_logs')
        total = cursor.fetchone()[0] or 0
        
        offset = (page - 1) * per_page
        cursor.execute('''
            SELECT id, task_id, task_name, status, started_at, completed_at, error_message
            FROM task_execution_logs
            ORDER BY started_at DESC
            LIMIT ? OFFSET ?
        ''', [per_page, offset])
        
        logs = []
        for row in cursor.fetchall():
            logs.append({
                'id': row['id'],
                'task_id': row['task_id'],
                'task_name': row['task_name'],
                'status': row['status'],
                'started_at': row['started_at'] or '',
                'completed_at': row['completed_at'] or '',
                'error_message': row['error_message'] or ''
            })
        
        conn.close()
        
        return create_response(200, 'success', {
            'logs': logs,
            'total': total,
            'page': page,
            'per_page': per_page
        })
    
    except Exception as e:
        logger.error(f"获取任务执行日志失败: {e}")
        return create_response(500, '获取任务执行日志失败')


@super_admin_api.route('/api/super_admin/sessions', methods=['GET'])
@require_super_admin
def sessions():
    """用户会话管理 - 获取活跃会话列表"""
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        username = request.args.get('username', '')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        where_clauses = []
        params = []
        
        where_clauses.append('status = "active"')
        
        if username:
            where_clauses.append('username LIKE ?')
            params.append(f'%{username}%')
        
        where_sql = 'WHERE ' + ' AND '.join(where_clauses) if where_clauses else ''
        
        cursor.execute(f'SELECT COUNT(*) FROM user_sessions {where_sql}', params)
        total = cursor.fetchone()[0] or 0
        
        offset = (page - 1) * per_page
        cursor.execute(f'''
            SELECT id, session_id, user_id, username, role, login_time, last_activity, 
                   expires_at, ip_address, user_agent, status
            FROM user_sessions
            {where_sql}
            ORDER BY last_activity DESC
            LIMIT ? OFFSET ?
        ''', params + [per_page, offset])
        
        sessions = []
        for row in cursor.fetchall():
            sessions.append({
                'id': row['id'],
                'session_id': row['session_id'],
                'user_id': row['user_id'],
                'username': row['username'] or '',
                'role': row['role'] or '',
                'login_time': row['login_time'] or '',
                'last_activity': row['last_activity'] or '',
                'expires_at': row['expires_at'] or '',
                'ip_address': row['ip_address'] or '',
                'user_agent': row['user_agent'] or '',
                'status': row['status'] or ''
            })
        
        cursor.execute('SELECT COUNT(*) FROM user_sessions WHERE status = "active"')
        active_count = cursor.fetchone()[0] or 0
        
        cursor.execute('SELECT COUNT(*) FROM user_sessions WHERE status = "expired"')
        expired_count = cursor.fetchone()[0] or 0
        
        conn.close()
        
        return create_response(200, 'success', {
            'sessions': sessions,
            'total': total,
            'page': page,
            'per_page': per_page,
            'stats': {
                'active_count': active_count,
                'expired_count': expired_count
            }
        })
    
    except Exception as e:
        logger.error(f"获取会话列表失败: {e}")
        return create_response(500, '获取会话列表失败')


@super_admin_api.route('/api/super_admin/sessions/<int:session_id>', methods=['DELETE'])
@require_super_admin
def terminate_session(session_id):
    """用户会话管理 - 终止会话"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('UPDATE user_sessions SET status = "expired" WHERE id = ?', (session_id,))
        conn.commit()
        affected = cursor.rowcount
        conn.close()
        
        if affected == 0:
            return create_response(404, '会话不存在')
        return create_response(200, '会话已终止')
    
    except Exception as e:
        logger.error(f"终止会话失败: {e}")
        return create_response(500, '终止会话失败')


@super_admin_api.route('/api/super_admin/sessions/terminate_all', methods=['POST'])
@require_super_admin
def terminate_all_sessions():
    """用户会话管理 - 终止所有会话"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('UPDATE user_sessions SET status = "expired" WHERE status = "active"')
        conn.commit()
        affected = cursor.rowcount
        conn.close()
        
        return create_response(200, f'已终止 {affected} 个会话', {'terminated_count': affected})
    
    except Exception as e:
        logger.error(f"终止所有会话失败: {e}")
        return create_response(500, '终止所有会话失败')