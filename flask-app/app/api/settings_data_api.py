#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Settings 页面数据加载API
提供 settings.html 所有面板所需的真实数据库数据
"""
import sqlite3
import psutil
import time
import json
import logging
from datetime import datetime, timedelta
from flask import Blueprint, jsonify, request

logger = logging.getLogger('settings_data_api')

DB_PATH = '/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/flask-app/app.db'
settings_data_bp = Blueprint('settings_data', __name__, url_prefix='/api/settings-data')


def get_db():
    """获取数据库连接"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# ==================== AI员工管理 ====================

@settings_data_bp.route('/employees', methods=['GET'])
def get_employees():
    """获取所有AI员工真实数据"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, name, employee_code, description, capabilities, specialties,
                   status, accuracy, total_tasks, successful_fixes, failed_fixes,
                   is_enabled, priority, skill_level, created_at, updated_at
            FROM ai_employees
            ORDER BY priority DESC, id ASC
        """)
        employees = [dict(row) for row in cursor.fetchall()]

        # 统计
        total = len(employees)
        running = sum(1 for e in employees if e['status'] == 'active' and e['is_enabled'])
        avg_accuracy = sum(e['accuracy'] for e in employees) / total if total > 0 else 0

        # 加载每个员工的技能和模块
        for emp in employees:
            cursor.execute("""
                SELECT skill_name, proficiency FROM ai_specialized_skills
                WHERE employee_id = ? ORDER BY proficiency DESC LIMIT 3
            """, (emp['id'],))
            emp['top_skills'] = [dict(row) for row in cursor.fetchall()]

            cursor.execute("""
                SELECT module_id, role FROM ai_employee_module
                WHERE employee_id = ? LIMIT 1
            """, (emp['id'],))
            mod = cursor.fetchone()
            emp['module'] = dict(mod) if mod else None

        conn.close()
        return jsonify({
            'success': True,
            'total': total,
            'running': running,
            'avg_accuracy': round(avg_accuracy, 2),
            'employees': employees
        })
    except Exception as e:
        logger.error(f'获取AI员工数据失败: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500


@settings_data_bp.route('/employees/<int:emp_id>', methods=['GET'])
def get_employee(emp_id):
    """获取单个AI员工详情"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM ai_employees WHERE id = ?", (emp_id,))
        emp = cursor.fetchone()
        if not emp:
            return jsonify({'success': False, 'error': '员工不存在'}), 404

        result = dict(emp)

        cursor.execute("SELECT * FROM ai_specialized_skills WHERE employee_id = ?", (emp_id,))
        result['skills'] = [dict(row) for row in cursor.fetchall()]

        cursor.execute("SELECT * FROM ai_employee_module WHERE employee_id = ?", (emp_id,))
        result['modules'] = [dict(row) for row in cursor.fetchall()]

        cursor.execute("""
            SELECT * FROM ai_employee_tasks WHERE employee_code = ?
            ORDER BY created_at DESC LIMIT 10
        """, (result['employee_code'],))
        result['recent_tasks'] = [dict(row) for row in cursor.fetchall()]

        conn.close()
        return jsonify({'success': True, 'employee': result})
    except Exception as e:
        logger.error(f'获取员工详情失败: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500


# ==================== 用户管理 ====================

@settings_data_bp.route('/users', methods=['GET'])
def get_users():
    """获取所有用户真实数据"""
    try:
        conn = get_db()
        cursor = conn.cursor()

        # 获取用户基本信息
        cursor.execute("""
            SELECT id, username, email, role, is_active, created_at, super_admin_approved, hardware_admin_approved
            FROM users
            ORDER BY id ASC
        """)
        users = [dict(row) for row in cursor.fetchall()]

        # 加载每个用户的角色
        for user in users:
            # 使用user_roles关联表
            try:
                cursor.execute("""
                    SELECT r.name FROM roles r
                    JOIN user_roles ur ON r.id = ur.role_id
                    WHERE ur.user_id = ?
                """, (user['id'],))
                user['roles'] = [row[0] for row in cursor.fetchall()]
            except Exception:
                user['roles'] = [user.get('role', 'user')] if user.get('role') else []

        conn.close()
        return jsonify({
            'success': True,
            'total': len(users),
            'users': users
        })
    except Exception as e:
        logger.error(f'获取用户数据失败: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500


# ==================== 角色权限管理 ====================

@settings_data_bp.route('/roles', methods=['GET'])
def get_roles():
    """获取所有角色"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM roles ORDER BY id ASC")
        roles = [dict(row) for row in cursor.fetchall()]

        for role in roles:
            cursor.execute("""
                SELECT p.* FROM permissions p
                JOIN role_permissions rp ON p.id = rp.permission_id
                WHERE rp.role_id = ?
            """, (role['id'],))
            role['permissions'] = [dict(row) for row in cursor.fetchall()]

        conn.close()
        return jsonify({'success': True, 'roles': roles})
    except Exception as e:
        logger.error(f'获取角色数据失败: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500


@settings_data_bp.route('/permissions', methods=['GET'])
def get_permissions():
    """获取所有权限"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM permissions ORDER BY id ASC")
        permissions = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return jsonify({'success': True, 'permissions': permissions})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ==================== 系统状态 ====================

@settings_data_bp.route('/system-status', methods=['GET'])
def get_system_status():
    """获取真实系统状态"""
    try:
        cpu = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')

        # 检查数据库连接
        db_status = 'connected'
        try:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            conn.close()
        except Exception:
            db_status = 'disconnected'

        return jsonify({
            'success': True,
            'status': {
                'cpu_usage': cpu,
                'memory_usage': memory.percent,
                'memory_total': round(memory.total / (1024**3), 2),
                'memory_used': round(memory.used / (1024**3), 2),
                'disk_usage': disk.percent,
                'disk_total': round(disk.total / (1024**3), 2),
                'disk_used': round(disk.used / (1024**3), 2),
                'database_status': db_status,
                'network_status': 'normal',
                'uptime': str(timedelta(seconds=int(time.time() - psutil.boot_time()))),
                'last_check': datetime.now().isoformat()
            }
        })
    except Exception as e:
        logger.error(f'获取系统状态失败: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500


# ==================== 告警和活动 ====================

@settings_data_bp.route('/alerts', methods=['GET'])
def get_alerts():
    """获取系统告警"""
    try:
        limit = request.args.get('limit', 10, type=int)
        resolved = request.args.get('resolved', 'false')

        conn = get_db()
        cursor = conn.cursor()

        # 尝试从monitor_alerts表获取
        try:
            if resolved == 'false':
                cursor.execute("""
                    SELECT id, alert_level, message, created_at, is_resolved
                    FROM monitor_alerts
                    WHERE is_resolved = 0
                    ORDER BY created_at DESC LIMIT ?
                """, (limit,))
            else:
                cursor.execute("""
                    SELECT id, alert_level, message, created_at, is_resolved
                    FROM monitor_alerts
                    ORDER BY created_at DESC LIMIT ?
                """, (limit,))
            alerts = [dict(row) for row in cursor.fetchall()]
        except sqlite3.OperationalError:
            alerts = []

        conn.close()
        return jsonify({
            'success': True,
            'count': len(alerts),
            'alerts': alerts
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@settings_data_bp.route('/recent-activity', methods=['GET'])
def get_recent_activity():
    """获取最近活动"""
    try:
        limit = request.args.get('limit', 10, type=int)
        conn = get_db()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT id, activity_type, description, username, created_at
                FROM page_navigation_logs
                ORDER BY created_at DESC LIMIT ?
            """, (limit,))
            activities = [dict(row) for row in cursor.fetchall()]
        except sqlite3.OperationalError:
            activities = []

        conn.close()
        return jsonify({
            'success': True,
            'count': len(activities),
            'activities': activities
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ==================== 日志 ====================

@settings_data_bp.route('/logs', methods=['GET'])
def get_logs():
    """获取系统日志"""
    try:
        limit = request.args.get('limit', 50, type=int)
        conn = get_db()
        cursor = conn.cursor()

        logs = []
        try:
            cursor.execute("""
                SELECT id, level, module, message, ip_address, created_at
                FROM system_operation_logs
                ORDER BY created_at DESC LIMIT ?
            """, (limit,))
            logs = [dict(row) for row in cursor.fetchall()]
        except sqlite3.OperationalError:
            pass

        # 如果没数据，从ai_repair_logs读取
        if not logs:
            try:
                cursor.execute("""
                    SELECT id, error_type as level, file_path as module,
                           error_message as message, '' as ip_address, repair_time as created_at
                    FROM ai_repair_logs
                    ORDER BY repair_time DESC LIMIT ?
                """, (limit,))
                logs = [dict(row) for row in cursor.fetchall()]
            except sqlite3.OperationalError:
                pass

        conn.close()
        return jsonify({
            'success': True,
            'count': len(logs),
            'logs': logs
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ==================== 审计 ====================

@settings_data_bp.route('/audit', methods=['GET'])
def get_audit():
    """获取审计记录"""
    try:
        limit = request.args.get('limit', 50, type=int)
        conn = get_db()
        cursor = conn.cursor()

        audit = []
        try:
            cursor.execute("""
                SELECT id, username, action, ip_address, created_at
                FROM security_audit_logs
                ORDER BY created_at DESC LIMIT ?
            """, (limit,))
            audit = [dict(row) for row in cursor.fetchall()]
        except sqlite3.OperationalError:
            pass

        if not audit:
            try:
                cursor.execute("""
                    SELECT id, username, operation as action, ip_address, created_at
                    FROM auth_session_logs
                    ORDER BY created_at DESC LIMIT ?
                """, (limit,))
                audit = [dict(row) for row in cursor.fetchall()]
            except sqlite3.OperationalError:
                pass

        conn.close()
        return jsonify({
            'success': True,
            'count': len(audit),
            'audit': audit
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ==================== 系统配置 ====================

@settings_data_bp.route('/system-config', methods=['GET'])
def get_system_config():
    """获取系统配置"""
    try:
        conn = get_db()
        cursor = conn.cursor()

        config = {}
        try:
            cursor.execute("SELECT key, value, description FROM system_config")
            for row in cursor.fetchall():
                config[row['key']] = {
                    'value': row['value'],
                    'description': row['description']
                }
        except sqlite3.OperationalError:
            pass

        conn.close()
        return jsonify({
            'success': True,
            'config': config
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ==================== 数据库信息 ====================

@settings_data_bp.route('/database-info', methods=['GET'])
def get_database_info():
    """获取数据库信息"""
    try:
        conn = get_db()
        cursor = conn.cursor()

        # 获取所有表
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]

        # 获取数据库文件大小
        import os
        db_size = os.path.getsize(DB_PATH) if os.path.exists(DB_PATH) else 0

        # 统计各表行数
        table_stats = []
        for table in tables[:20]:  # 限制20个表
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                table_stats.append({'name': table, 'rows': count})
            except Exception:
                pass

        conn.close()
        return jsonify({
            'success': True,
            'database': {
                'type': 'SQLite',
                'path': DB_PATH,
                'size': db_size,
                'size_mb': round(db_size / (1024*1024), 2),
                'total_tables': len(tables),
                'tables': table_stats
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ==================== AI维修统计 ====================

@settings_data_bp.route('/ai-repair-stats', methods=['GET'])
def get_ai_repair_stats():
    """获取AI维修统计"""
    try:
        conn = get_db()
        cursor = conn.cursor()

        stats = {
            'total_repairs': 0,
            'successful': 0,
            'failed': 0,
            'by_type': [],
            'recent': []
        }

        try:
            cursor.execute("SELECT COUNT(*) FROM ai_repair_logs")
            stats['total_repairs'] = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM ai_repair_logs WHERE fix_status = 'success'")
            stats['successful'] = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM ai_repair_logs WHERE fix_status = 'failed'")
            stats['failed'] = cursor.fetchone()[0]

            cursor.execute("""
                SELECT error_type, COUNT(*) as count
                FROM ai_repair_logs
                GROUP BY error_type
                ORDER BY count DESC LIMIT 10
            """)
            stats['by_type'] = [dict(row) for row in cursor.fetchall()]

            cursor.execute("""
                SELECT * FROM ai_repair_logs
                ORDER BY repair_time DESC LIMIT 20
            """)
            stats['recent'] = [dict(row) for row in cursor.fetchall()]
        except sqlite3.OperationalError:
            pass

        conn.close()
        return jsonify({'success': True, 'stats': stats})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ==================== 规则管理 ====================

@settings_data_bp.route('/rules', methods=['GET'])
def get_rules():
    """获取系统规则"""
    try:
        rule_type = request.args.get('type', None)
        is_active = request.args.get('active', None)
        limit = request.args.get('limit', 200, type=int)

        conn = get_db()
        cursor = conn.cursor()

        sql = "SELECT * FROM system_rules WHERE 1=1"
        params = []

        if rule_type:
            sql += " AND rule_type = ?"
            params.append(rule_type)

        if is_active is not None:
            sql += " AND is_active = ?"
            params.append(1 if is_active in ('true', '1', 'yes') else 0)

        sql += " ORDER BY priority ASC, id ASC LIMIT ?"
        params.append(limit)

        cursor.execute(sql, params)
        rules = [dict(row) for row in cursor.fetchall()]

        # 统计
        cursor.execute("SELECT COUNT(*) FROM system_rules")
        total = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM system_rules WHERE is_active = 1")
        active_count = cursor.fetchone()[0]

        # 按类型分组
        cursor.execute("""
            SELECT rule_type, COUNT(*) as count
            FROM system_rules
            GROUP BY rule_type
            ORDER BY count DESC
        """)
        type_stats = [dict(row) for row in cursor.fetchall()]

        conn.close()
        return jsonify({
            'success': True,
            'total': total,
            'active_count': active_count,
            'type_stats': type_stats,
            'rules': rules
        })
    except Exception as e:
        logger.error(f'获取规则数据失败: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500


@settings_data_bp.route('/rules/<int:rule_id>', methods=['GET'])
def get_rule(rule_id):
    """获取单个规则详情"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM system_rules WHERE id = ?", (rule_id,))
        rule = cursor.fetchone()
        if not rule:
            return jsonify({'success': False, 'error': '规则不存在'}), 404

        result = dict(rule)

        # 加载相关约束
        try:
            cursor.execute("""
                SELECT * FROM rule_constraints
                WHERE apply_to LIKE ? OR constraint_key = ?
            """, (f'%{result["rule_code"]}%', result['rule_code']))
            result['constraints'] = [dict(row) for row in cursor.fetchall()]
        except Exception:
            result['constraints'] = []

        # 加载相关访问控制
        try:
            cursor.execute("""
                SELECT * FROM access_control_rules
                WHERE role_name = ? OR description LIKE ?
            """, (result['rule_code'], f'%{result["rule_code"]}%'))
            result['access_control'] = [dict(row) for row in cursor.fetchall()]
        except Exception:
            result['access_control'] = []

        conn.close()
        return jsonify({'success': True, 'rule': result})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@settings_data_bp.route('/rule-constraints', methods=['GET'])
def get_rule_constraints():
    """获取规则约束"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM rule_constraints ORDER BY priority ASC, id ASC")
        constraints = [dict(row) for row in cursor.fetchall()]

        # 按分类分组
        cursor.execute("""
            SELECT category, COUNT(*) as count
            FROM rule_constraints
            GROUP BY category
        """)
        category_stats = [dict(row) for row in cursor.fetchall()]

        conn.close()
        return jsonify({
            'success': True,
            'total': len(constraints),
            'category_stats': category_stats,
            'constraints': constraints
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@settings_data_bp.route('/access-control-rules', methods=['GET'])
def get_access_control_rules():
    """获取访问控制规则"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM access_control_rules ORDER BY priority ASC, id ASC")
        rules = [dict(row) for row in cursor.fetchall()]

        # 按角色分组
        cursor.execute("""
            SELECT role_name, COUNT(*) as count
            FROM access_control_rules
            GROUP BY role_name
        """)
        role_stats = [dict(row) for row in cursor.fetchall()]

        conn.close()
        return jsonify({
            'success': True,
            'total': len(rules),
            'role_stats': role_stats,
            'rules': rules
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
