# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""硬件管理员路由 - 设备管理和系统设置"""

from flask import Blueprint, render_template, request, jsonify, redirect, url_for
import sqlite3
from contextlib import contextmanager
from datetime import datetime
import json
import sys
import os

hardware_bp = Blueprint('hardware', __name__)

def get_db_connection():
    """获取数据库连接"""
    conn = sqlite3.connect('flask-app/app.db')
    conn.row_factory = sqlite3.Row
    return conn


@hardware_bp.route('/hardware_admin_dashboard')
def hardware_admin_dashboard():
    """硬件管理员仪表板"""
    conn = get_db_connection()
    
    # 获取设备列表
    devices = conn.execute('SELECT * FROM hardware_devices').fetchall()
    
    # 获取系统设置
    settings = {}
    setting_rows = conn.execute('SELECT setting_key, value FROM system_settings').fetchall()
    for row in setting_rows:
        settings[row['setting_key']] = row['value']
    
    # 计算统计数据
    total_devices = len(devices)
    online_devices = sum(1 for d in devices if d['status'] == 'online')
    avg_cpu = sum(d['cpu_usage'] for d in devices) / total_devices if total_devices > 0 else 0
    avg_memory = sum(d['memory_usage'] for d in devices) / total_devices if total_devices > 0 else 0
    avg_storage = sum(d['storage_usage'] for d in devices) / total_devices if total_devices > 0 else 0
    
    return render_template('hardware_admin_dashboard.html',
                         devices=devices,
                         settings=settings,
                         total_devices=total_devices,
                         online_devices=online_devices,
                         avg_cpu=round(avg_cpu, 1),
                         avg_memory=round(avg_memory, 1),
                         avg_storage=round(avg_storage, 0))

@hardware_bp.route('/api/hardware/devices', methods=['GET'])
def get_devices():
    """获取所有设备列表"""
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

@hardware_bp.route('/api/hardware/devices/<int:device_id>', methods=['GET'])
def get_device(device_id):
    """获取单个设备信息"""
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

@hardware_bp.route('/api/hardware/devices', methods=['POST'])
def add_device():
    """添加新设备"""
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

@hardware_bp.route('/api/hardware/devices/<int:device_id>', methods=['PUT'])
def update_device(device_id):
    """更新设备信息"""
    data = request.get_json()
    
    conn = get_db_connection()
    
    # 构建更新字段
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

@hardware_bp.route('/api/hardware/devices/<int:device_id>', methods=['DELETE'])
def delete_device(device_id):
    """删除设备"""
    conn = get_db_connection()
    conn.execute('DELETE FROM hardware_devices WHERE id = ?', (device_id,))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': '设备删除成功'})

@hardware_bp.route('/api/hardware/settings', methods=['GET'])
def get_settings():
    """获取所有系统设置"""
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

@hardware_bp.route('/api/hardware/settings', methods=['PUT'])
def update_settings():
    """更新系统设置"""
    data = request.get_json()
    
    if not data:
        return jsonify({'success': False, 'message': '缺少设置数据'}), 400
    
    conn = get_db_connection()
    
    for key, value in data.items():
        conn.execute('''
            UPDATE system_settings 
            SET value = ?, updated_at = ? 
            WHERE setting_key = ?
        ''', (str(value), datetime.now().isoformat(), key))
    
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': '设置更新成功'})

@hardware_bp.route('/api/hardware/settings/<string:setting_key>', methods=['GET'])
def get_setting(setting_key):
    """获取单个设置"""
    conn = get_db_connection()
    setting = conn.execute('SELECT * FROM system_settings WHERE setting_key = ?', (setting_key,)).fetchone()
    conn.close()
    
    if setting:
        return jsonify({
            'success': True,
            'data': {
                'key': setting['setting_key'],
                'value': setting['value'],
                'type': setting['setting_type'],
                'description': setting['description']
            }
        })
    else:
        return jsonify({'success': False, 'message': '设置不存在'}), 404

@hardware_bp.route('/api/hardware/settings/<string:setting_key>', methods=['PUT'])
def update_setting(setting_key):
    """更新单个设置"""
    data = request.get_json()
    
    if 'value' not in data:
        return jsonify({'success': False, 'message': '缺少设置值'}), 400
    
    conn = get_db_connection()
    conn.execute('''
        UPDATE system_settings 
        SET value = ?, updated_at = ? 
        WHERE setting_key = ?
    ''', (str(data['value']), datetime.now().isoformat(), setting_key))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': '设置更新成功'})

@hardware_bp.route('/api/hardware/performance', methods=['POST'])
def log_performance():
    """记录性能日志"""
    data = request.get_json()
    
    if not data or 'device_id' not in data:
        return jsonify({'success': False, 'message': '缺少设备ID'}), 400
    
    conn = get_db_connection()
    conn.execute('''
        INSERT INTO performance_logs 
        (device_id, timestamp, cpu_usage, memory_usage, storage_usage, network_in, network_out)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        data['device_id'],
        datetime.now().isoformat(),
        data.get('cpu_usage', 0),
        data.get('memory_usage', 0),
        data.get('storage_usage', 0),
        data.get('network_in', 0),
        data.get('network_out', 0)
    ))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': '性能日志记录成功'})

@hardware_bp.route('/api/hardware/performance/<int:device_id>', methods=['GET'])
def get_performance_history(device_id):
    """获取设备性能历史"""
    conn = get_db_connection()
    logs = conn.execute('''
        SELECT * FROM performance_logs 
        WHERE device_id = ? 
        ORDER BY timestamp DESC LIMIT 24
    ''', (device_id,)).fetchall()
    conn.close()
    
    result = []
    for log in logs:
        result.append({
            'timestamp': log['timestamp'],
            'cpu_usage': log['cpu_usage'],
            'memory_usage': log['memory_usage'],
            'storage_usage': log['storage_usage'],
            'network_in': log['network_in'],
            'network_out': log['network_out']
        })
    
    return jsonify({'success': True, 'data': result})