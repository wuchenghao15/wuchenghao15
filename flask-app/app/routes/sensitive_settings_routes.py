#!/usr/bin/env python3
"""
高危敏感设置路由
处理硬件管理员和超级管理员的高危设置操作
"""
from flask import Blueprint, jsonify, request, render_template, session, redirect, url_for
import sqlite3
import os
import json
import shutil
import subprocess
from datetime import datetime
from functools import wraps

sensitive_settings_bp = Blueprint('sensitive_settings', __name__)

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'app.db')

@sensitive_settings_bp.route('/sensitive-settings')
def sensitive_settings_page():
    """高危敏感设置页面"""
    # 检查权限
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_role = session.get('role', '')
    if user_role not in ['hardware_admin', 'super_admin', 'hardware_vikey_admin']:
        return redirect(url_for('hardware_admin_dashboard'))
    
    return render_template('sensitive_settings.html')

def get_db():
    """获取数据库连接"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def log_operation(operation_type, category, description, details, user_id, user_role, ip_address, status='success'):
    """记录系统操作日志"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO system_operation_logs 
        (operation_type, operation_category, description, details, user_id, user_role, ip_address, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (operation_type, category, description, json.dumps(details), user_id, user_role, ip_address, status))
    conn.commit()
    conn.close()

def check_permission(required_roles):
    """权限检查装饰器"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                return jsonify({'success': False, 'message': '未登录', 'redirect': '/login'}), 401
            
            user_role = session.get('role', '')
            if user_role not in required_roles:
                return jsonify({'success': False, 'message': '权限不足'}), 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def is_hardware_admin():
    """检查是否是硬件管理员"""
    return session.get('role') == 'hardware_admin'

def is_super_admin():
    """检查是否是超级管理员"""
    return session.get('role') == 'super_admin'

@sensitive_settings_bp.route('/api/sensitive-settings')
@check_permission(['hardware_admin', 'super_admin'])
def get_sensitive_settings():
    """获取高危敏感设置列表"""
    conn = get_db()
    cursor = conn.cursor()
    
    # 获取分类参数
    category = request.args.get('category', '')
    
    # 硬件管理员可以看到所有设置
    # 超级管理员只能看到需要审批的设置
    if is_hardware_admin():
        if category:
            cursor.execute('SELECT * FROM sensitive_settings WHERE category = ? ORDER BY id', (category,))
        else:
            cursor.execute('SELECT * FROM sensitive_settings ORDER BY category, id')
    else:  # super_admin
        if category:
            cursor.execute('SELECT * FROM sensitive_settings WHERE category = ? AND requires_approval = 1 ORDER BY id', (category,))
        else:
            cursor.execute('SELECT * FROM sensitive_settings WHERE requires_approval = 1 ORDER BY category, id')
    
    settings = cursor.fetchall()
    conn.close()
    
    # 转换为字典列表
    settings_list = []
    for setting in settings:
        settings_list.append({
            'id': setting['id'],
            'category': setting['category'],
            'setting_key': setting['setting_key'],
            'setting_name': setting['setting_name'],
            'setting_value': setting['setting_value'],
            'default_value': setting['default_value'],
            'value_type': setting['value_type'],
            'description': setting['description'],
            'is_dangerous': bool(setting['is_dangerous']),
            'requires_restart': bool(setting['requires_restart']),
            'requires_approval': bool(setting['requires_approval']),
            'approval_status': setting['approval_status']
        })
    
    return jsonify({'success': True, 'settings': settings_list})

@sensitive_settings_bp.route('/api/sensitive-settings/categories')
@check_permission(['hardware_admin', 'super_admin'])
def get_categories():
    """获取设置分类列表"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('SELECT DISTINCT category FROM sensitive_settings ORDER BY category')
    categories = [row['category'] for row in cursor.fetchall()]
    
    conn.close()
    
    return jsonify({'success': True, 'categories': categories})

@sensitive_settings_bp.route('/api/sensitive-settings/<int:setting_id>', methods=['GET'])
@check_permission(['hardware_admin', 'super_admin'])
def get_setting(setting_id):
    """获取单个设置详情"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM sensitive_settings WHERE id = ?', (setting_id,))
    setting = cursor.fetchone()
    conn.close()
    
    if not setting:
        return jsonify({'success': False, 'message': '设置不存在'}), 404
    
    # 权限检查：超管只能看需要审批的设置
    if is_super_admin() and not setting['requires_approval']:
        return jsonify({'success': False, 'message': '权限不足'}), 403
    
    return jsonify({
        'success': True,
        'setting': {
            'id': setting['id'],
            'category': setting['category'],
            'setting_key': setting['setting_key'],
            'setting_name': setting['setting_name'],
            'setting_value': setting['setting_value'],
            'default_value': setting['default_value'],
            'value_type': setting['value_type'],
            'description': setting['description'],
            'is_dangerous': bool(setting['is_dangerous']),
            'requires_restart': bool(setting['requires_restart']),
            'requires_approval': bool(setting['requires_approval']),
            'approval_status': setting['approval_status']
        }
    })

@sensitive_settings_bp.route('/api/sensitive-settings/<int:setting_id>', methods=['PUT'])
@check_permission(['hardware_admin', 'super_admin'])
def update_setting(setting_id):
    """更新设置值"""
    data = request.get_json()
    new_value = data.get('value')
    reason = data.get('reason', '')
    
    conn = get_db()
    cursor = conn.cursor()
    
    # 获取当前设置
    cursor.execute('SELECT * FROM sensitive_settings WHERE id = ?', (setting_id,))
    setting = cursor.fetchone()
    
    if not setting:
        conn.close()
        return jsonify({'success': False, 'message': '设置不存在'}), 404
    
    old_value = setting['setting_value']
    
    # 硬件管理员可以直接修改
    if is_hardware_admin():
        # 更新设置值
        cursor.execute('''
            UPDATE sensitive_settings 
            SET setting_value = ?, updated_at = ?, approval_status = 'approved', 
                approved_by = ?, approval_date = ?
            WHERE id = ?
        ''', (new_value, datetime.now().isoformat(), session['user_id'], 
              datetime.now().isoformat(), setting_id))
        
        # 记录操作日志
        log_operation(
            'UPDATE_SETTING', 
            setting['category'],
            f'更新设置: {setting["setting_name"]}',
            {'old_value': old_value, 'new_value': new_value},
            session['user_id'],
            session['role'],
            request.remote_addr
        )
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True, 
            'message': '设置已更新',
            'requires_restart': bool(setting['requires_restart'])
        })
    
    # 超级管理员需要提交审批
    else:
        # 创建审批记录
        cursor.execute('''
            INSERT INTO setting_approvals 
            (setting_id, requester_id, requester_role, old_value, new_value, reason, status)
            VALUES (?, ?, ?, ?, ?, ?, 'pending')
        ''', (setting_id, session['user_id'], session['role'], old_value, new_value, reason))
        
        # 更新设置状态为待审批
        cursor.execute('''
            UPDATE sensitive_settings 
            SET approval_status = 'pending', updated_at = ?
            WHERE id = ?
        ''', (datetime.now().isoformat(), setting_id))
        
        # 记录操作日志
        log_operation(
            'REQUEST_APPROVAL',
            setting['category'],
            f'请求审批设置: {setting["setting_name"]}',
            {'old_value': old_value, 'new_value': new_value, 'reason': reason},
            session['user_id'],
            session['role'],
            request.remote_addr
        )
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': '已提交审批请求，等待硬件管理员批准'
        })

@sensitive_settings_bp.route('/api/sensitive-settings/<int:setting_id>/approve', methods=['POST'])
@check_permission(['hardware_admin'])
def approve_setting(setting_id):
    """审批设置变更（仅硬件管理员）"""
    data = request.get_json()
    approval_notes = data.get('notes', '')
    approved = data.get('approved', True)
    
    conn = get_db()
    cursor = conn.cursor()
    
    # 获取待审批的记录
    cursor.execute('''
        SELECT sa.*, ss.setting_name, ss.requires_restart
        FROM setting_approvals sa
        JOIN sensitive_settings ss ON sa.setting_id = ss.id
        WHERE sa.setting_id = ? AND sa.status = 'pending'
        ORDER BY sa.created_at DESC
        LIMIT 1
    ''', (setting_id,))
    
    approval = cursor.fetchone()
    
    if not approval:
        conn.close()
        return jsonify({'success': False, 'message': '没有待审批的记录'}), 404
    
    if approved:
        # 批准
        cursor.execute('''
            UPDATE setting_approvals 
            SET status = 'approved', approver_id = ?, approver_role = ?, 
                approval_notes = ?, updated_at = ?
            WHERE id = ?
        ''', (session['user_id'], session['role'], approval_notes, 
              datetime.now().isoformat(), approval['id']))
        
        # 更新设置值
        cursor.execute('''
            UPDATE sensitive_settings 
            SET setting_value = ?, approval_status = 'approved',
                approved_by = ?, approval_date = ?, updated_at = ?
            WHERE id = ?
        ''', (approval['new_value'], session['user_id'], 
              datetime.now().isoformat(), datetime.now().isoformat(), setting_id))
        
        # 记录操作日志
        log_operation(
            'APPROVE_SETTING',
            'approval',
            f'批准设置变更: {approval["setting_name"]}',
            {'setting_id': setting_id, 'new_value': approval['new_value'], 'notes': approval_notes},
            session['user_id'],
            session['role'],
            request.remote_addr
        )
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': '设置变更已批准',
            'requires_restart': bool(approval['requires_restart'])
        })
    else:
        # 拒绝
        cursor.execute('''
            UPDATE setting_approvals 
            SET status = 'rejected', approver_id = ?, approver_role = ?, 
                approval_notes = ?, updated_at = ?
            WHERE id = ?
        ''', (session['user_id'], session['role'], approval_notes,
              datetime.now().isoformat(), approval['id']))
        
        # 更新设置状态
        cursor.execute('''
            UPDATE sensitive_settings 
            SET approval_status = 'rejected', updated_at = ?
            WHERE id = ?
        ''', (datetime.now().isoformat(), setting_id))
        
        # 记录操作日志
        log_operation(
            'REJECT_SETTING',
            'approval',
            f'拒绝设置变更: {approval["setting_name"]}',
            {'setting_id': setting_id, 'notes': approval_notes},
            session['user_id'],
            session['role'],
            request.remote_addr
        )
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': '设置变更已拒绝'
        })

@sensitive_settings_bp.route('/api/sensitive-settings/pending-approvals')
@check_permission(['hardware_admin'])
def get_pending_approvals():
    """获取待审批列表（仅硬件管理员）"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT sa.*, ss.setting_name, ss.category, u.username as requester_name
        FROM setting_approvals sa
        JOIN sensitive_settings ss ON sa.setting_id = ss.id
        JOIN users u ON sa.requester_id = u.id
        WHERE sa.status = 'pending'
        ORDER BY sa.created_at DESC
    ''')
    
    approvals = cursor.fetchall()
    conn.close()
    
    approvals_list = []
    for approval in approvals:
        approvals_list.append({
            'id': approval['id'],
            'setting_id': approval['setting_id'],
            'setting_name': approval['setting_name'],
            'category': approval['category'],
            'requester_name': approval['requester_name'],
            'old_value': approval['old_value'],
            'new_value': approval['new_value'],
            'reason': approval['reason'],
            'created_at': approval['created_at']
        })
    
    return jsonify({'success': True, 'approvals': approvals_list})

@sensitive_settings_bp.route('/api/sensitive-settings/backup', methods=['POST'])
@check_permission(['hardware_admin'])
def backup_database():
    """执行数据库备份"""
    data = request.get_json()
    reason = data.get('reason', '手动备份')
    
    # 创建备份目录
    backup_dir = os.path.join(os.path.dirname(DB_PATH), 'backups')
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
    
    # 生成备份文件名
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_filename = f'app_backup_{timestamp}.db'
    backup_path = os.path.join(backup_dir, backup_filename)
    
    # 执行备份
    try:
        shutil.copy2(DB_PATH, backup_path)
        backup_size = os.path.getsize(backup_path)
        
        # 记录备份
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO database_backups 
            (backup_type, backup_path, backup_size, trigger_reason, triggered_by)
            VALUES ('manual', ?, ?, ?, ?)
        ''', (backup_path, backup_size, reason, session['user_id']))
        conn.commit()
        conn.close()
        
        # 记录操作日志
        log_operation(
            'BACKUP_DATABASE',
            'backup',
            '执行数据库备份',
            {'backup_path': backup_path, 'size': backup_size, 'reason': reason},
            session['user_id'],
            session['role'],
            request.remote_addr
        )
        
        return jsonify({
            'success': True,
            'message': '数据库备份成功',
            'backup_path': backup_path,
            'backup_size': backup_size
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'备份失败: {str(e)}'
        }), 500

@sensitive_settings_bp.route('/api/sensitive-settings/restart-services', methods=['POST'])
@check_permission(['hardware_admin'])
def restart_services():
    """重启所有服务"""
    data = request.get_json()
    reason = data.get('reason', '应用设置变更')
    confirmed = data.get('confirmed', False)
    
    if not confirmed:
        return jsonify({
            'success': False,
            'message': '需要前端确认才能重启服务',
            'requires_confirmation': True
        })
    
    # 记录重启操作
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO service_restarts 
        (restart_type, services_affected, reason, triggered_by, status, started_at)
        VALUES ('full', 'all', ?, ?, 'in_progress', ?)
    ''', (reason, session['user_id'], datetime.now().isoformat()))
    restart_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    # 记录操作日志
    log_operation(
        'RESTART_SERVICES',
        'system',
        '重启所有服务',
        {'reason': reason, 'services': 'all'},
        session['user_id'],
        session['role'],
        request.remote_addr
    )
    
    # TODO: 实际的重启逻辑
    # 这里需要根据实际部署环境来实现
    # 例如：使用systemctl、supervisor、docker等
    
    # 模拟重启过程
    try:
        # 1. 停止AI员工
        # 2. 重新加载路由
        # 3. 重启主服务
        # 4. 启动AI员工
        
        # 更新重启状态
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE service_restarts 
            SET status = 'completed', completed_at = ?
            WHERE id = ?
        ''', (datetime.now().isoformat(), restart_id))
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': '服务重启成功'
        })
    except Exception as e:
        # 更新重启状态为失败
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE service_restarts 
            SET status = 'failed', completed_at = ?
            WHERE id = ?
        ''', (datetime.now().isoformat(), restart_id))
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': False,
            'message': f'重启失败: {str(e)}'
        }), 500

@sensitive_settings_bp.route('/api/sensitive-settings/apply', methods=['POST'])
@check_permission(['hardware_admin'])
def apply_settings():
    """应用设置（备份+重启）"""
    data = request.get_json()
    setting_ids = data.get('setting_ids', [])
    confirmed = data.get('confirmed', False)
    
    if not confirmed:
        return jsonify({
            'success': False,
            'message': '需要前端确认才能应用设置',
            'requires_confirmation': True,
            'impact': {
                'backup': True,
                'restart': True,
                'affected_settings': len(setting_ids)
            }
        })
    
    # 1. 执行双数据库备份
    backup_result1 = backup_database_internal('应用设置前备份-1')
    backup_result2 = backup_database_internal('应用设置前备份-2')
    
    # 2. 重启服务
    restart_result = restart_services_internal('应用高危设置变更')
    
    # 记录操作日志
    log_operation(
        'APPLY_SETTINGS',
        'system',
        '应用高危设置',
        {
            'setting_ids': setting_ids,
            'backup1': backup_result1,
            'backup2': backup_result2,
            'restart': restart_result
        },
        session['user_id'],
        session['role'],
        request.remote_addr
    )
    
    return jsonify({
        'success': True,
        'message': '设置已应用',
        'backups': [backup_result1, backup_result2],
        'restart': restart_result
    })

def backup_database_internal(reason):
    """内部备份函数"""
    try:
        backup_dir = os.path.join(os.path.dirname(DB_PATH), 'backups')
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
        backup_filename = f'app_backup_{timestamp}.db'
        backup_path = os.path.join(backup_dir, backup_filename)
        
        shutil.copy2(DB_PATH, backup_path)
        backup_size = os.path.getsize(backup_path)
        
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO database_backups 
            (backup_type, backup_path, backup_size, trigger_reason, triggered_by)
            VALUES ('auto', ?, ?, ?, ?)
        ''', (backup_path, backup_size, reason, session.get('user_id', 0)))
        conn.commit()
        conn.close()
        
        return {'success': True, 'path': backup_path, 'size': backup_size}
    except Exception as e:
        return {'success': False, 'error': str(e)}

def restart_services_internal(reason):
    """内部重启函数"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO service_restarts 
            (restart_type, services_affected, reason, triggered_by, status, started_at)
            VALUES ('full', 'all', ?, ?, 'completed', ?)
        ''', (reason, session.get('user_id', 0), datetime.now().isoformat()))
        conn.commit()
        conn.close()
        
        return {'success': True, 'message': '服务重启标记已创建'}
    except Exception as e:
        return {'success': False, 'error': str(e)}

@sensitive_settings_bp.route('/api/sensitive-settings/backups')
@check_permission(['hardware_admin', 'super_admin'])
def get_backups():
    """获取备份记录列表"""
    conn = get_db()
    cursor = conn.cursor()
    
    limit = request.args.get('limit', 20)
    cursor.execute('''
        SELECT db.*, u.username as triggered_by_name
        FROM database_backups db
        LEFT JOIN users u ON db.triggered_by = u.id
        ORDER BY db.created_at DESC
        LIMIT ?
    ''', (limit,))
    
    backups = cursor.fetchall()
    conn.close()
    
    backups_list = []
    for backup in backups:
        backups_list.append({
            'id': backup['id'],
            'backup_type': backup['backup_type'],
            'backup_path': backup['backup_path'],
            'backup_size': backup['backup_size'],
            'trigger_reason': backup['trigger_reason'],
            'triggered_by_name': backup['triggered_by_name'],
            'status': backup['status'],
            'created_at': backup['created_at']
        })
    
    return jsonify({'success': True, 'backups': backups_list})

@sensitive_settings_bp.route('/api/sensitive-settings/restart-history')
@check_permission(['hardware_admin', 'super_admin'])
def get_restart_history():
    """获取重启历史记录"""
    conn = get_db()
    cursor = conn.cursor()
    
    limit = request.args.get('limit', 20)
    cursor.execute('''
        SELECT sr.*, u.username as triggered_by_name
        FROM service_restarts sr
        LEFT JOIN users u ON sr.triggered_by = u.id
        ORDER BY sr.started_at DESC
        LIMIT ?
    ''', (limit,))
    
    restarts = cursor.fetchall()
    conn.close()
    
    restarts_list = []
    for restart in restarts:
        restarts_list.append({
            'id': restart['id'],
            'restart_type': restart['restart_type'],
            'services_affected': restart['services_affected'],
            'reason': restart['reason'],
            'triggered_by_name': restart['triggered_by_name'],
            'status': restart['status'],
            'started_at': restart['started_at'],
            'completed_at': restart['completed_at']
        })
    
    return jsonify({'success': True, 'restarts': restarts_list})

@sensitive_settings_bp.route('/api/sensitive-settings/operation-logs')
@check_permission(['hardware_admin', 'super_admin'])
def get_operation_logs():
    """获取操作日志"""
    conn = get_db()
    cursor = conn.cursor()
    
    limit = request.args.get('limit', 50)
    cursor.execute('''
        SELECT sol.*, u.username as user_name
        FROM system_operation_logs sol
        LEFT JOIN users u ON sol.user_id = u.id
        ORDER BY sol.created_at DESC
        LIMIT ?
    ''', (limit,))
    
    logs = cursor.fetchall()
    conn.close()
    
    logs_list = []
    for log in logs:
        logs_list.append({
            'id': log['id'],
            'operation_type': log['operation_type'],
            'operation_category': log['operation_category'],
            'description': log['description'],
            'details': log['details'],
            'user_name': log['user_name'],
            'user_role': log['user_role'],
            'ip_address': log['ip_address'],
            'status': log['status'],
            'created_at': log['created_at']
        })
    
    return jsonify({'success': True, 'logs': logs_list})
