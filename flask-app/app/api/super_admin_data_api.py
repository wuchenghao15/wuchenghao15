# -*- coding: utf-8 -*-
"""
超级管理员数据API
提供仪表盘所需的实时统计数据
"""

from flask import Blueprint, jsonify, session, current_app
import sqlite3
import logging
import os
import sys
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

super_admin_data_api = Blueprint('super_admin_data_api', __name__)

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'app.db')


def get_db_connection():
    """获取数据库连接"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def get_system_resources():
    """获取系统资源使用率"""
    try:
        import psutil
        
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        memory_percent = round(memory.percent, 1)
        disk = psutil.disk_usage('/')
        disk_percent = round(disk.percent, 1)
        
        return {
            'cpu_percent': round(cpu_percent, 1),
            'memory_percent': memory_percent,
            'disk_percent': disk_percent,
            'memory_total': round(memory.total / (1024**3), 2),
            'memory_used': round(memory.used / (1024**3), 2),
            'disk_total': round(disk.total / (1024**3), 2),
            'disk_used': round(disk.used / (1024**3), 2)
        }
    except ImportError:
        return {
            'cpu_percent': 0,
            'memory_percent': 0,
            'disk_percent': 0,
            'memory_total': 0,
            'memory_used': 0,
            'disk_total': 0,
            'disk_used': 0
        }


@super_admin_data_api.route('/admin/dashboard_stats', methods=['GET'])
def get_dashboard_stats():
    """获取仪表盘统计数据"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 用户总数
        cursor.execute('SELECT COUNT(*) FROM users')
        user_count = cursor.fetchone()[0]
        
        # 路由总数
        route_count = len(list(current_app.url_map.iter_rules()))
        
        # 系统状态
        system_status = '正常运行'
        
        # 今日活跃用户数
        cursor.execute('''
        SELECT COUNT(DISTINCT user_id) FROM access_logs 
        WHERE DATE(access_time) = DATE('now')
        ''')
        active_users = cursor.fetchone()[0] or 0
        
        # 考试总数
        cursor.execute('SELECT COUNT(*) FROM exams')
        exams_count = cursor.fetchone()[0] or 0
        
        # 题目总数
        cursor.execute('SELECT COUNT(*) FROM questions')
        questions_count = cursor.fetchone()[0] or 0
        
        # 今日登录数
        cursor.execute('''
        SELECT COUNT(*) FROM access_logs 
        WHERE DATE(access_time) = DATE('now') 
        AND path LIKE '%login%'
        AND result = 'success'
        ''')
        today_logins = cursor.fetchone()[0] or 0
        
        # 今日注册数
        cursor.execute('''
        SELECT COUNT(*) FROM users 
        WHERE DATE(created_at) = DATE('now')
        ''')
        today_registers = cursor.fetchone()[0] or 0
        
        # 完成考试数
        cursor.execute('''
        SELECT COUNT(*) FROM exam_records 
        WHERE status = 'completed'
        ''')
        completed_exams = cursor.fetchone()[0] or 0
        
        # 备份数量
        cursor.execute('SELECT COUNT(*) FROM backup_history')
        backup_count = cursor.fetchone()[0] or 0
        
        # 通知数量
        cursor.execute('SELECT COUNT(*) FROM notifications')
        notification_count = cursor.fetchone()[0] or 0
        
        # 未读通知数
        cursor.execute('''
        SELECT COUNT(*) FROM notifications 
        WHERE status != 'read'
        ''')
        unread_notifications = cursor.fetchone()[0] or 0
        
        # 系统资源
        system_resources = get_system_resources()
        
        # 最近活动日志
        cursor.execute('''
        SELECT path, username, role, result, access_time 
        FROM access_logs 
        ORDER BY access_time DESC 
        LIMIT 10
        ''')
        recent_logs = []
        for row in cursor.fetchall():
            recent_logs.append({
                'path': row[0],
                'username': row[1] or 'guest',
                'role': row[2] or 'guest',
                'result': row[3] or '',
                'access_time': row[4] or '',
                'action': get_action_description(row[0]),
                'created_at': row[4] or ''
            })
        
        # 角色分布统计
        cursor.execute('''
        SELECT role, COUNT(*) as count 
        FROM users 
        GROUP BY role 
        ORDER BY count DESC
        ''')
        role_distribution = []
        for row in cursor.fetchall():
            role_distribution.append({
                'role': row[0],
                'count': row[1]
            })
        
        # 最近7天用户注册趋势
        seven_days_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        cursor.execute('''
        SELECT DATE(created_at) as date, COUNT(*) as count
        FROM users
        WHERE created_at >= ?
        GROUP BY DATE(created_at)
        ORDER BY date
        ''', (seven_days_ago,))
        registration_trend = []
        for row in cursor.fetchall():
            registration_trend.append({
                'date': row[0],
                'count': row[1]
            })
        
        conn.close()
        
        # AI系统统计
        ai_stats = get_ai_system_stats()
        
        return jsonify({
            'success': True,
            'data': {
                'user_count': user_count,
                'route_count': route_count,
                'system_status': system_status,
                'active_users': active_users,
                'exams_count': exams_count,
                'questions_count': questions_count,
                'today_logins': today_logins,
                'today_registers': today_registers,
                'completed_exams': completed_exams,
                'backup_count': backup_count,
                'notification_count': notification_count,
                'unread_notifications': unread_notifications,
                'system_resources': system_resources,
                'recent_logs': recent_logs,
                'role_distribution': role_distribution,
                'registration_trend': registration_trend,
                'ai_system': ai_stats,
                'timestamp': datetime.now().isoformat()
            }
        })
    
    except Exception as e:
        logger.error(f"获取仪表盘统计数据失败: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e),
            'data': {
                'user_count': 0,
                'route_count': 0,
                'system_status': '获取失败',
                'active_users': 0,
                'exams_count': 0,
                'questions_count': 0,
                'today_logins': 0,
                'today_registers': 0,
                'system_resources': {
                    'cpu_percent': 0,
                    'memory_percent': 0,
                    'disk_percent': 0
                },
                'recent_logs': []
            }
        })


def get_action_description(path):
    """根据路径获取动作描述"""
    action_map = {
        '/auth/login': '用户登录',
        '/auth/logout': '用户登出',
        '/auth/register': '用户注册',
        '/super_admin_dashboard': '访问超级管理员控制台',
        '/settings': '访问系统设置',
        '/exam_system': '访问考试系统',
        '/learning_system': '访问学习系统',
        '/teacher': '访问教师后台',
        '/admin_app/users': '管理用户',
        '/api/routes/reload': '刷新路由',
        '/backup_manager': '访问备份管理',
        '/notification_admin': '访问通知中心',
        '/api/brain-bank': '访问AI脑库',
        '/api/proactive-ai': '访问主动AI系统',
        '/api/data-integrity': '访问数据完整性中心',
    }
    
    for key, desc in action_map.items():
        if key in path:
            return desc
    
    return f'访问 {path}'


def get_ai_system_stats():
    """获取AI系统统计数据"""
    stats = {
        'brain_bank': {
            'total_knowledge': 0,
            'total_triggers': 0,
            'knowledge_types': 10,
            'knowledge_domains': 11,
            'trigger_types': 5,
            'status': 'unknown',
            'empowerment_rate': 0
        },
        'proactive_ai': {
            'initiative_level': 'PASSIVE',
            'initiative_level_num': 1,
            'discovery_modules': 0,
            'task_executors': 0,
            'active_tasks': 0,
            'discoveries_total': 0
        },
        'ai_employees': {
            'total_count': 0,
            'active_count': 0,
            'specialties': [],
            'collaboration_rate': 0
        },
        'data_integrity': {
            'validation_rules': 12,
            'total_validations': 0,
            'validation_pass_rate': 0,
            'active_locks': 0,
            'audit_logs': 0
        }
    }
    
    try:
        from app.ai.knowledge_brain_bank import knowledge_brain_bank
        brain_stats = knowledge_brain_bank.get_brain_stats()
        if isinstance(brain_stats, dict):
            knowledge_data = brain_stats.get('knowledge', brain_stats)
            trigger_data = brain_stats.get('triggers', brain_stats)
            stats['brain_bank'] = {
                'total_knowledge': knowledge_data.get('total_knowledge', knowledge_data.get('count', 0)),
                'total_triggers': trigger_data.get('total_triggers', trigger_data.get('trigger_count', 0)),
                'knowledge_types': brain_stats.get('knowledge_types', 10),
                'knowledge_domains': brain_stats.get('knowledge_domains', 11),
                'trigger_types': brain_stats.get('trigger_types', 5),
                'status': brain_stats.get('status', 'active'),
                'empowerment_rate': brain_stats.get('empowerment_rate', 0)
            }
    except Exception as e:
        logger.debug(f"获取脑库统计失败: {e}")
    
    try:
        from app.ai.proactive_ai_system import proactive_ai_center
        pro_stats = proactive_ai_center.get_system_status()
        if isinstance(pro_stats, dict):
            data = pro_stats.get('data', pro_stats)
            discovery = data.get('discovery', {})
            scheduler = data.get('scheduler', {})
            level = data.get('initiative_level', 'passive').upper()
            
            level_map = {
                'PASSIVE': 1,
                'REACTIVE': 2,
                'PROACTIVE': 3,
                'SELF_DRIVEN': 4,
                'AUTONOMOUS': 5
            }
            level_num = level_map.get(level, 1)
            
            stats['proactive_ai'] = {
                'initiative_level': level,
                'initiative_level_num': level_num,
                'discovery_modules': discovery.get('modules_count', len(discovery.get('modules', []))),
                'task_executors': len(scheduler.get('executors', [])),
                'active_tasks': scheduler.get('active', 0),
                'discoveries_total': discovery.get('history_count', 0)
            }
    except Exception as e:
        logger.debug(f"获取主动AI统计失败: {e}")
    
    try:
        from app.ai.ai_employee_enhanced_system import get_enhanced_system
        emp_sys = get_enhanced_system()
        emp_stats = emp_sys.get_system_status() if hasattr(emp_sys, 'get_system_status') else {}
        if isinstance(emp_stats, dict):
            data = emp_stats.get('data', emp_stats)
            stats['ai_employees'] = {
                'total_count': data.get('total_employees', data.get('employee_count', data.get('count', 0))),
                'active_count': data.get('active_employees', data.get('active_count', 0)),
                'specialties': data.get('specialties', []),
                'collaboration_rate': data.get('collaboration_rate', 0)
            }
    except Exception as e:
        logger.debug(f"获取AI员工统计失败: {e}")
    
    try:
        from app.utils.data_integrity_center import data_integrity_center
        di_stats = data_integrity_center.get_status()
        if isinstance(di_stats, dict):
            data = di_stats.get('data', di_stats)
            stats['data_integrity'] = {
                'validation_rules': data.get('validation_rules', data.get('rules_count', 12)),
                'total_validations': data.get('total_validations', data.get('validations', 0)),
                'validation_pass_rate': data.get('validation_pass_rate', data.get('pass_rate', 0)),
                'active_locks': data.get('active_locks', data.get('locks', 0)),
                'audit_logs': data.get('audit_logs', data.get('logs', 0))
            }
    except Exception as e:
        logger.debug(f"获取数据完整性统计失败: {e}")
    
    return stats


@super_admin_data_api.route('/admin/users_list', methods=['GET'])
def get_users_list():
    """获取用户列表"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT id, username, role, email, created_at 
        FROM users 
        ORDER BY created_at DESC 
        LIMIT 50
        ''')
        
        users = []
        for row in cursor.fetchall():
            users.append({
                'id': row[0],
                'username': row[1],
                'role': row[2],
                'email': row[3] or '',
                'created_at': row[4] or ''
            })
        
        conn.close()
        
        return jsonify({
            'success': True,
            'users': users,
            'total': len(users)
        })
    
    except Exception as e:
        logger.error(f"获取用户列表失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'users': []
        })


@super_admin_data_api.route('/admin/exams_stats', methods=['GET'])
def get_exams_stats():
    """获取考试统计数据"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 考试总数
        cursor.execute('SELECT COUNT(*) FROM exams')
        exam_count = cursor.fetchone()[0]
        
        # 题目总数
        cursor.execute('SELECT COUNT(*) FROM questions')
        question_count = cursor.fetchone()[0]
        
        # 今日考试次数
        cursor.execute('''
        SELECT COUNT(*) FROM exam_records 
        WHERE DATE(started_at) = DATE('now')
        ''')
        today_exams = cursor.fetchone()[0] or 0
        
        # 平均分数
        cursor.execute('SELECT AVG(score) FROM exam_records WHERE score IS NOT NULL')
        avg_score = cursor.fetchone()[0] or 0
        
        conn.close()
        
        return jsonify({
            'success': True,
            'data': {
                'exam_count': exam_count,
                'question_count': question_count,
                'today_exams': today_exams,
                'avg_score': round(avg_score, 2)
            }
        })
    
    except Exception as e:
        logger.error(f"获取考试统计数据失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        })


@super_admin_data_api.route('/admin/recent_logs', methods=['GET'])
def get_recent_logs():
    """获取最近的系统日志"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 访问日志
        cursor.execute('''
        SELECT path, username, role, result, access_time 
        FROM access_logs 
        ORDER BY access_time DESC 
        LIMIT 20
        ''')
        
        logs = []
        for row in cursor.fetchall():
            logs.append({
                'path': row[0],
                'username': row[1] or 'guest',
                'role': row[2] or 'guest',
                'result': row[3] or '',
                'access_time': row[4] or ''
            })
        
        conn.close()
        
        return jsonify({
            'success': True,
            'logs': logs,
            'total': len(logs)
        })
    
    except Exception as e:
        logger.error(f"获取系统日志失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'logs': []
        })


@super_admin_data_api.route('/admin/clear_cache', methods=['POST'])
def clear_cache():
    """清除系统缓存"""
    try:
        cache_cleared = 0
        
        # 清除 search_cache 表
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('DELETE FROM search_cache')
            cache_cleared += cursor.rowcount
            conn.commit()
            conn.close()
        except Exception as e:
            logger.warning(f"清除search_cache失败: {e}")
        
        # 清除模板缓存
        try:
            import shutil
            template_cache_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), '.cache')
            if os.path.exists(template_cache_dir):
                shutil.rmtree(template_cache_dir)
                cache_cleared += 1
        except Exception as e:
            logger.warning(f"清除模板缓存失败: {e}")
        
        # 清除 Jinja2 缓存
        try:
            current_app.jinja_env.cache.clear()
            cache_cleared += 1
        except Exception as e:
            logger.warning(f"清除Jinja2缓存失败: {e}")
        
        return jsonify({
            'success': True,
            'message': f'缓存已清除，共清理 {cache_cleared} 项',
            'cleared_count': cache_cleared
        })
    
    except Exception as e:
        logger.error(f"清除缓存失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        })


@super_admin_data_api.route('/admin/system_info', methods=['GET'])
def get_system_info():
    """获取系统详细信息"""
    try:
        system_resources = get_system_resources()
        
        # 获取Python版本
        python_version = sys.version
        
        # 获取Flask版本
        try:
            import flask
            flask_version = flask.__version__
        except:
            flask_version = 'unknown'
        
        # 获取数据库信息
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM sqlite_master WHERE type="table"')
        table_count = cursor.fetchone()[0]
        conn.close()
        
        return jsonify({
            'success': True,
            'data': {
                'python_version': python_version,
                'flask_version': flask_version,
                'table_count': table_count,
                'database_path': DB_PATH,
                'system_resources': system_resources,
                'timestamp': datetime.now().isoformat()
            }
        })
    
    except Exception as e:
        logger.error(f"获取系统信息失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        })
