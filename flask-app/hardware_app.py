# -*- coding: utf-8 -*-
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""独立的硬件管理应用"""

import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify, redirect
import json
import sys

app = Flask(__name__)
app.template_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app.config['JSON_AS_ASCII'] = False

DATABASE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app.db')

def get_db_connection():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# 初始化数据库表
def init_db():
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS hardware_devices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_name TEXT NOT NULL,
            device_type TEXT,
            ip_address TEXT,
            status TEXT DEFAULT 'offline',
            cpu_usage REAL DEFAULT 0,
            memory_usage REAL DEFAULT 0,
            storage_usage REAL DEFAULT 0,
            network_traffic REAL DEFAULT 0,
            last_heartbeat TEXT,
            created_at TEXT,
            updated_at TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS system_settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            setting_key TEXT UNIQUE NOT NULL,
            setting_type TEXT,
            value TEXT,
            description TEXT,
            created_at TEXT,
            updated_at TEXT
        )
    ''')
    
    cursor.execute('''
        INSERT OR IGNORE INTO system_settings (setting_key, setting_type, value, description, created_at, updated_at)
        VALUES 
        ('system_name', 'string', 'MTSCOS AI 硬件管理系统', '系统显示名称', datetime('now'), datetime('now')),
        ('system_description', 'text', '基于人工智能的智能硬件管理系统', '系统描述信息', datetime('now'), datetime('now')),
        ('timezone', 'string', 'Asia/Shanghai', '系统时区设置', datetime('now'), datetime('now')),
        ('auto_save', 'boolean', 'true', '自动保存设置', datetime('now'), datetime('now')),
        ('device_auth', 'boolean', 'true', '设备认证开关', datetime('now'), datetime('now')),
        ('ssl_enabled', 'boolean', 'false', 'SSL加密开关', datetime('now'), datetime('now')),
        ('access_log', 'boolean', 'true', '访问日志开关', datetime('now'), datetime('now')),
        ('auto_lock', 'boolean', 'true', '自动锁定开关', datetime('now'), datetime('now'))
    ''')
    
    cursor.execute('''
        INSERT OR IGNORE INTO hardware_devices (device_name, device_type, ip_address, status, cpu_usage, memory_usage, storage_usage, created_at, updated_at)
        VALUES 
        ('AI服务器-01', 'AI计算节点', '192.168.1.101', 'online', 32, 4.5, 120, datetime('now'), datetime('now')),
        ('数据库服务器', '数据库节点', '192.168.1.102', 'online', 58, 6.2, 245, datetime('now'), datetime('now')),
        ('测试服务器', '测试节点', '192.168.1.103', 'offline', 0, 0, 0, datetime('now'), datetime('now'))
    ''')
    
    conn.commit()
    conn.close()

init_db()

@app.route('/hardware_admin_dashboard')
def hardware_admin_dashboard():
    conn = get_db_connection()
    
    devices = conn.execute('SELECT * FROM hardware_devices').fetchall()
    
    settings = {}
    setting_rows = conn.execute('SELECT setting_key, value FROM system_settings').fetchall()
    for row in setting_rows:
        settings[row['setting_key']] = row['value']
    
    total_devices = len(devices)
    online_devices = sum(1 for d in devices if d['status'] == 'online')
    avg_cpu = sum(d['cpu_usage'] for d in devices) / total_devices if total_devices > 0 else 0
    avg_memory = sum(d['memory_usage'] for d in devices) / total_devices if total_devices > 0 else 0
    avg_storage = sum(d['storage_usage'] for d in devices) / total_devices if total_devices > 0 else 0
    
    conn.close()
    
    return render_template('hardware_admin_dashboard.html',
                         devices=devices,
                         settings=settings,
                         total_devices=total_devices,
                         online_devices=online_devices,
                         avg_cpu=round(avg_cpu, 1),
                         avg_memory=round(avg_memory, 1),
                         avg_storage=round(avg_storage, 0))

@app.route('/api/hardware/devices', methods=['GET'])
def get_devices():
    conn = get_db_connection()
    devices = conn.execute('SELECT * FROM hardware_devices').fetchall()
    conn.close()
    
    result = []
    for device in devices:
        result.append({
            'id': device['id'],
            'device_name': device['device_name'],
            'device_type': device['device_type'],
            'ip_address': device['ip_address'],
            'status': device['status'],
            'cpu_usage': device['cpu_usage'],
            'memory_usage': device['memory_usage'],
            'storage_usage': device['storage_usage'],
            'created_at': device['created_at'],
            'updated_at': device['updated_at']
        })
    
    return jsonify({'success': True, 'data': result})

@app.route('/api/hardware/devices/<int:device_id>', methods=['GET'])
def get_device(device_id):
    conn = get_db_connection()
    device = conn.execute('SELECT * FROM hardware_devices WHERE id = ?', (device_id,)).fetchone()
    conn.close()
    
    if device:
        return jsonify({
            'success': True,
            'data': {
                'id': device['id'],
                'device_name': device['device_name'],
                'device_type': device['device_type'],
                'ip_address': device['ip_address'],
                'status': device['status'],
                'cpu_usage': device['cpu_usage'],
                'memory_usage': device['memory_usage'],
                'storage_usage': device['storage_usage'],
                'created_at': device['created_at'],
                'updated_at': device['updated_at']
            }
        })
    else:
        return jsonify({'success': False, 'message': '设备不存在'}), 404

@app.route('/api/hardware/devices', methods=['POST'])
def add_device():
    data = request.get_json()
    
    if not data or 'device_name' not in data:
        return jsonify({'success': False, 'message': '缺少设备名称'}), 400
    
    conn = get_db_connection()
    conn.execute('''
        INSERT INTO hardware_devices 
        (device_name, device_type, ip_address, status, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (
        data['device_name'],
        data.get('device_type', 'unknown'),
        data.get('ip_address', ''),
        'offline',
        datetime.now().isoformat(),
        datetime.now().isoformat()
    ))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': '设备添加成功'})

@app.route('/api/hardware/devices/<int:device_id>', methods=['PUT'])
def update_device(device_id):
    data = request.get_json()
    
    conn = get_db_connection()
    
    update_fields = []
    params = []
    
    if 'device_name' in data:
        update_fields.append('device_name = ?')
        params.append(data['device_name'])
    if 'device_type' in data:
        update_fields.append('device_type = ?')
        params.append(data['device_type'])
    if 'ip_address' in data:
        update_fields.append('ip_address = ?')
        params.append(data['ip_address'])
    if 'status' in data:
        update_fields.append('status = ?')
        params.append(data['status'])
    if 'cpu_usage' in data:
        update_fields.append('cpu_usage = ?')
        params.append(data['cpu_usage'])
    if 'memory_usage' in data:
        update_fields.append('memory_usage = ?')
        params.append(data['memory_usage'])
    if 'storage_usage' in data:
        update_fields.append('storage_usage = ?')
        params.append(data['storage_usage'])
    
    update_fields.append('updated_at = ?')
    params.append(datetime.now().isoformat())
    params.append(device_id)
    
    if update_fields:
        conn.execute(f'UPDATE hardware_devices SET {", ".join(update_fields)} WHERE id = ?', params)
        conn.commit()
    
    conn.close()
    
    return jsonify({'success': True, 'message': '设备更新成功'})

@app.route('/api/hardware/devices/<int:device_id>', methods=['DELETE'])
def delete_device(device_id):
    conn = get_db_connection()
    conn.execute('DELETE FROM hardware_devices WHERE id = ?', (device_id,))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': '设备删除成功'})

@app.route('/api/hardware/settings', methods=['GET'])
def get_settings():
    conn = get_db_connection()
    settings = conn.execute('SELECT * FROM system_settings').fetchall()
    conn.close()
    
    result = {}
    for setting in settings:
        result[setting['setting_key']] = {
            'value': setting['value'],
            'type': setting['setting_type'],
            'description': setting['description']
        }
    
    return jsonify({'success': True, 'data': result})

@app.route('/api/hardware/settings', methods=['PUT'])
def update_settings():
    data = request.get_json()
    
    if not data:
        return jsonify({'success': False, 'message': '缺少设置数据'}), 400
    
    # 获取当前用户信息(从请求头获取)
    user_role = request.headers.get('X-User-Role', 'admin')
    user_id = int(request.headers.get('X-User-Id', '1'))
    
    conn = get_db_connection()
    result = {'success': True, 'message': '', 'pending_approvals': []}
    
    for key, value in data.items():
        # 获取当前值
        current_setting = conn.execute('SELECT value FROM system_settings WHERE setting_key = ?', (key,)).fetchone()
        old_value = current_setting['value'] if current_setting else ''
        
        if user_role == 'hardware_vikey_admin':
            # 硬件管理员:自动保存并立即生效
            conn.execute('''
                UPDATE system_settings 
                SET value = ?, updated_at = ?, approval_status = 'active' 
                WHERE setting_key = ?
            ''', (str(value), datetime.now().isoformat(), key))
            result['message'] = '设置已自动保存并立即生效'
            
        elif user_role == 'super_admin':
            # 超级管理员:创建审批记录,次日自动生效或可被硬件管理员立即审批
            effective_date = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
            conn.execute('''
                INSERT INTO settings_approval 
                (setting_key, new_value, old_value, requester_id, requester_role, status, effective_date, created_at)
                VALUES (?, ?, ?, ?, ?, 'pending', ?, ?)
            ''', (key, str(value), old_value, user_id, user_role, effective_date, datetime.now().isoformat()))
            result['pending_approvals'].append({
                'setting_key': key,
                'new_value': value,
                'effective_date': effective_date,
                'status': 'pending',
                'message': '设置将在次日自动生效,或可由硬件管理员审批立即生效'
            })
            result['message'] = '设置已提交,将在次日自动生效'
            
        else:
            # 普通管理员:必须等待审批
            conn.execute('''
                INSERT INTO settings_approval 
                (setting_key, new_value, old_value, requester_id, requester_role, status, created_at)
                VALUES (?, ?, ?, ?, ?, 'pending', ?)
            ''', (key, str(value), old_value, user_id, user_role, datetime.now().isoformat()))
            result['pending_approvals'].append({
                'setting_key': key,
                'new_value': value,
                'status': 'pending',
                'message': '设置等待审批中,需超级管理员或硬件管理员批准后生效'
            })
            result['message'] = '设置已提交审批,等待超级管理员或硬件管理员批准'
    
    conn.commit()
    conn.close()
    
    return jsonify(result)

@app.route('/api/hardware/approvals', methods=['GET'])
def get_approvals():
    conn = get_db_connection()
    approvals = conn.execute('SELECT * FROM settings_approval WHERE status = "pending"').fetchall()
    conn.close()
    
    result = []
    for approval in approvals:
        result.append({
            'id': approval['id'],
            'setting_key': approval['setting_key'],
            'new_value': approval['new_value'],
            'old_value': approval['old_value'],
            'requester_id': approval['requester_id'],
            'requester_role': approval['requester_role'],
            'status': approval['status'],
            'effective_date': approval['effective_date'],
            'created_at': approval['created_at']
        })
    
    return jsonify({'success': True, 'data': result})

@app.route('/api/hardware/approvals/<int:approval_id>/approve', methods=['POST'])
def approve_approval(approval_id):
    approver_role = request.headers.get('X-User-Role', 'admin')
    approver_id = int(request.headers.get('X-User-Id', '1'))
    
    if approver_role not in ['hardware_vikey_admin', 'super_admin']:
        return jsonify({'success': False, 'message': '无权审批,需要超级管理员或硬件管理员权限'}), 403
    
    conn = get_db_connection()
    approval = conn.execute('SELECT * FROM settings_approval WHERE id = ?', (approval_id,)).fetchone()
    
    if not approval:
        conn.close()
        return jsonify({'success': False, 'message': '审批记录不存在'}), 404
    
    if approval['status'] != 'pending':
        conn.close()
        return jsonify({'success': False, 'message': '审批记录状态不正确'}), 400
    
    # 立即生效设置
    conn.execute('''
        UPDATE system_settings 
        SET value = ?, updated_at = ?, approval_status = 'active' 
        WHERE setting_key = ?
    ''', (approval['new_value'], datetime.now().isoformat(), approval['setting_key']))
    
    # 更新审批状态
    conn.execute('''
        UPDATE settings_approval 
        SET status = 'approved', approver_id = ?, approver_role = ?, approved_at = ?, effective_date = ? 
        WHERE id = ?
    ''', (approver_id, approver_role, datetime.now().isoformat(), datetime.now().isoformat(), approval_id))
    
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': '设置已批准并立即生效'})

@app.route('/api/hardware/approvals/<int:approval_id>/reject', methods=['POST'])
def reject_approval(approval_id):
    approver_role = request.headers.get('X-User-Role', 'admin')
    
    if approver_role not in ['hardware_vikey_admin', 'super_admin']:
        return jsonify({'success': False, 'message': '无权审批,需要超级管理员或硬件管理员权限'}), 403
    
    conn = get_db_connection()
    approval = conn.execute('SELECT * FROM settings_approval WHERE id = ?', (approval_id,)).fetchone()
    
    if not approval:
        conn.close()
        return jsonify({'success': False, 'message': '审批记录不存在'}), 404
    
    if approval['status'] != 'pending':
        conn.close()
        return jsonify({'success': False, 'message': '审批记录状态不正确'}), 400
    
    conn.execute('''
        UPDATE settings_approval 
        SET status = 'rejected', approver_id = ?, approver_role = ?, approved_at = ? 
        WHERE id = ?
    ''', (request.headers.get('X-User-Id', '1'), approver_role, datetime.now().isoformat(), approval_id))
    
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': '设置变更已拒绝'})

@app.route('/api/hardware/approvals/<int:approval_id>/execute_now', methods=['POST'])
def execute_now(approval_id):
    approver_role = request.headers.get('X-User-Role', 'admin')
    
    if approver_role not in ['hardware_vikey_admin', 'super_admin']:
        return jsonify({'success': False, 'message': '无权执行,需要超级管理员或硬件管理员权限'}), 403
    
    conn = get_db_connection()
    approval = conn.execute('SELECT * FROM settings_approval WHERE id = ?', (approval_id,)).fetchone()
    
    if not approval:
        conn.close()
        return jsonify({'success': False, 'message': '审批记录不存在'}), 404
    
    if approval['status'] not in ['approved', 'executed']:
        conn.close()
        return jsonify({'success': False, 'message': '审批记录状态不正确'}), 400
    
    # 立即生效
    conn.execute('''
        UPDATE system_settings 
        SET value = ?, updated_at = ?, approval_status = 'active' 
        WHERE setting_key = ?
    ''', (approval['new_value'], datetime.now().isoformat(), approval['setting_key']))
    
    conn.execute('''
        UPDATE settings_approval 
        SET status = 'executed', executed_at = ? 
        WHERE id = ?
    ''', (datetime.now().isoformat(), approval_id))
    
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': '设置已立即生效'})

@app.route('/api/hardware/approvals/<int:approval_id>/execute_midnight', methods=['POST'])
def execute_midnight(approval_id):
    approver_role = request.headers.get('X-User-Role', 'admin')
    
    if approver_role not in ['hardware_vikey_admin', 'super_admin']:
        return jsonify({'success': False, 'message': '无权执行,需要超级管理员或硬件管理员权限'}), 403
    
    conn = get_db_connection()
    approval = conn.execute('SELECT * FROM settings_approval WHERE id = ?', (approval_id,)).fetchone()
    
    if not approval:
        conn.close()
        return jsonify({'success': False, 'message': '审批记录不存在'}), 404
    
    if approval['status'] not in ['approved', 'executed']:
        conn.close()
        return jsonify({'success': False, 'message': '审批记录状态不正确'}), 400
    
    # 计算当日零点时间
    midnight = datetime.now().replace(hour=23, minute=59, second=59)
    execute_time = midnight.isoformat()
    
    # 创建定时任务
    conn.execute('''
        INSERT INTO scheduled_tasks 
        (approval_id, setting_key, new_value, execute_time, created_at)
        VALUES (?, ?, ?, ?, ?)
    ''', (approval_id, approval['setting_key'], approval['new_value'], execute_time, datetime.now().isoformat()))
    
    conn.execute('''
        UPDATE settings_approval 
        SET status = 'scheduled', executed_at = ? 
        WHERE id = ?
    ''', (execute_time, approval_id))
    
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': f'设置已安排在 {midnight.strftime("%Y-%m-%d 23:59:59")} 生效'})

@app.route('/api/hardware/approvals/<int:approval_id>/revoke', methods=['POST'])
def revoke_approval(approval_id):
    approver_role = request.headers.get('X-User-Role', 'admin')
    
    if approver_role not in ['hardware_vikey_admin', 'super_admin']:
        return jsonify({'success': False, 'message': '无权撤回,需要超级管理员或硬件管理员权限'}), 403
    
    conn = get_db_connection()
    approval = conn.execute('SELECT * FROM settings_approval WHERE id = ?', (approval_id,)).fetchone()
    
    if not approval:
        conn.close()
        return jsonify({'success': False, 'message': '审批记录不存在'}), 404
    
    if approval['status'] not in ['approved', 'scheduled', 'executed']:
        conn.close()
        return jsonify({'success': False, 'message': '只能撤回已批准的记录'}), 400
    
    # 撤回审批,恢复到待审批状态
    conn.execute('''
        UPDATE settings_approval 
        SET status = 'pending', revoked_at = ?, approver_id = NULL, approver_role = NULL, approved_at = NULL, executed_at = NULL 
        WHERE id = ?
    ''', (datetime.now().isoformat(), approval_id))
    
    # 删除相关定时任务
    conn.execute('DELETE FROM scheduled_tasks WHERE approval_id = ?', (approval_id,))
    
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': '审批已撤回,恢复到待审批状态'})

@app.route('/api/hardware/approvals/all', methods=['GET'])
def get_all_approvals():
    conn = get_db_connection()
    approvals = conn.execute('''
        SELECT * FROM settings_approval 
        ORDER BY created_at DESC
    ''').fetchall()
    conn.close()
    
    result = []
    now = datetime.now()
    
    for approval in approvals:
        # 计算超时状态
        created_at = datetime.fromisoformat(approval['created_at'])
        days_diff = (now - created_at).days
        
        if days_diff > 5:
            status_color = 'expired'
            status_text = '已失效'
        elif days_diff > 3:
            status_color = 'warning'
            status_text = '严重超时'
        elif days_diff > 1:
            status_color = 'attention'
            status_text = '即将超时'
        else:
            status_color = 'normal'
            status_text = '正常'
        
        result.append({
            'id': approval['id'],
            'setting_key': approval['setting_key'],
            'new_value': approval['new_value'],
            'old_value': approval['old_value'],
            'requester_id': approval['requester_id'],
            'requester_role': approval['requester_role'],
            'status': approval['status'],
            'status_color': status_color,
            'status_text': status_text,
            'days_pending': days_diff,
            'approver_id': approval['approver_id'],
            'approver_role': approval['approver_role'],
            'approved_at': approval['approved_at'],
            'expires_at': approval['expires_at'],
            'revoked_at': approval['revoked_at'],
            'executed_at': approval['executed_at'],
            'created_at': approval['created_at']
        })
    
    return jsonify({'success': True, 'data': result})

@app.route('/api/hardware/approvals/check_timeout', methods=['GET'])
def check_timeout():
    conn = get_db_connection()
    approvals = conn.execute('SELECT * FROM settings_approval WHERE status = "pending"').fetchall()
    
    result = {
        'has_critical': False,
        'has_warning': False,
        'critical_approvals': [],
        'warning_approvals': []
    }
    
    now = datetime.now()
    
    for approval in approvals:
        created_at = datetime.fromisoformat(approval['created_at'])
        days_diff = (now - created_at).days
        
        if days_diff > 3:
            result['has_critical'] = True
            result['critical_approvals'].append({
                'id': approval['id'],
                'setting_key': approval['setting_key'],
                'days_pending': days_diff
            })
        elif days_diff > 1:
            result['has_warning'] = True
            result['warning_approvals'].append({
                'id': approval['id'],
                'setting_key': approval['setting_key'],
                'days_pending': days_diff
            })
    
    conn.close()
    
    return jsonify({'success': True, 'data': result})

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/auth/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        try:
            if request.content_type == 'application/json':
                data = request.get_json()
            else:
                data = {
                    'username': request.form.get('username', request.args.get('username', '')),
                    'password': request.form.get('password', request.args.get('password', ''))
                }
            
            username = data.get('username', '').strip()
            password = data.get('password', '').strip()
            
            # 验证用户
            conn = get_db_connection()
            user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
            conn.close()
            
            if user and password == 'LoginMe.1988':
                session_id = f"session_{datetime.now().strftime('%Y%m%d%H%M%S')}_{user['id']}"
                user_info = {
                    'id': user['id'],
                    'username': user['username'],
                    'email': user['email'],
                    'role': user['role']
                }
                return jsonify({
                    'success': True,
                    'message': '登录成功',
                    'session_id': session_id,
                    'user': user_info
                })
            else:
                return jsonify({'success': False, 'message': '用户名或密码错误'}), 401
                
        except Exception as e:
            return jsonify({'success': False, 'message': f'登录失败: {str(e)}'}), 500
    
    return redirect('/')

@app.route('/auth/logout')
def logout():
    return redirect('/')

@app.route('/exam_system')
def exam_system():
    return render_template('exam_system.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8888, debug=True)