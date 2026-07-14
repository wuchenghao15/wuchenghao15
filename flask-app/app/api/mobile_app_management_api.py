# -*- coding: utf-8 -*-
"""
移动设备管理API
提供设备注册、版本检查、远程配置、推送通知等功能
"""
import os
import json
import uuid
import sqlite3
from datetime import datetime
from flask import Blueprint, jsonify, request, session

mobile_app_management_api = Blueprint('mobile_app_management_api', __name__)

DATABASE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'app.db')

def get_db_connection():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_mobile_device_tables():
    """初始化移动设备相关数据库表"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS mobile_devices (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    device_id TEXT UNIQUE NOT NULL,
                    user_id INTEGER,
                    device_name TEXT,
                    device_type TEXT,
                    os_type TEXT,
                    os_version TEXT,
                    app_version TEXT,
                    screen_size TEXT,
                    model TEXT,
                    manufacturer TEXT,
                    token TEXT,
                    registered_at TEXT,
                    last_seen TEXT,
                    status TEXT DEFAULT 'online',
                    metadata TEXT DEFAULT '{}',
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS mobile_configs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    config_key TEXT UNIQUE NOT NULL,
                    config_value TEXT,
                    description TEXT,
                    platform TEXT DEFAULT 'all',
                    created_at TEXT,
                    updated_at TEXT
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS push_notifications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    device_id TEXT,
                    user_id INTEGER,
                    title TEXT,
                    content TEXT,
                    type TEXT DEFAULT 'info',
                    status TEXT DEFAULT 'pending',
                    sent_at TEXT,
                    created_at TEXT,
                    FOREIGN KEY (device_id) REFERENCES mobile_devices(device_id),
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS app_versions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    platform TEXT NOT NULL,
                    version TEXT NOT NULL,
                    build_number INTEGER,
                    is_active INTEGER DEFAULT 1,
                    is_force INTEGER DEFAULT 0,
                    download_url TEXT,
                    changelog TEXT,
                    min_version TEXT,
                    created_at TEXT
                )
            ''')
            
            conn.commit()
            return True
    except Exception as e:
        print(f"初始化移动设备表失败: {e}")
        return False

init_mobile_device_tables()

@mobile_app_management_api.route('/api/mobile/device/register', methods=['POST'])
def register_device():
    """注册移动设备"""
    try:
        data = request.get_json() or {}
        device_id = data.get('device_id')
        user_id = data.get('user_id') or session.get('user_id')
        
        if not device_id:
            return jsonify({'success': False, 'message': '设备ID不能为空'}), 400
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM mobile_devices WHERE device_id = ?', (device_id,))
            existing = cursor.fetchone()
            
            now = datetime.now().isoformat()
            
            if existing:
                cursor.execute('''
                    UPDATE mobile_devices 
                    SET device_name = ?, device_type = ?, os_type = ?, os_version = ?, 
                        app_version = ?, screen_size = ?, model = ?, manufacturer = ?, 
                        token = ?, last_seen = ?, metadata = ?
                    WHERE device_id = ?
                ''', (
                    data.get('device_name'), data.get('device_type'), data.get('os_type'),
                    data.get('os_version'), data.get('app_version'), data.get('screen_size'),
                    data.get('model'), data.get('manufacturer'), data.get('token'),
                    now, json.dumps(data.get('metadata', {})), device_id
                ))
                message = '设备信息已更新'
            else:
                cursor.execute('''
                    INSERT INTO mobile_devices 
                    (device_id, user_id, device_name, device_type, os_type, os_version, 
                     app_version, screen_size, model, manufacturer, token, registered_at, 
                     last_seen, status, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    device_id, user_id, data.get('device_name'), data.get('device_type'),
                    data.get('os_type'), data.get('os_version'), data.get('app_version'),
                    data.get('screen_size'), data.get('model'), data.get('manufacturer'),
                    data.get('token'), now, now, 'online', json.dumps(data.get('metadata', {}))
                ))
                message = '设备注册成功'
            
            conn.commit()
        
        return jsonify({
            'success': True,
            'message': message,
            'device_id': device_id
        })
    except Exception as e:
        return jsonify({'success': False, 'message': f'注册设备失败: {str(e)}'}), 500

@mobile_app_management_api.route('/api/mobile/device/<device_id>', methods=['GET'])
def get_device_info(device_id):
    """获取设备信息"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM mobile_devices WHERE device_id = ?', (device_id,))
            device = cursor.fetchone()
            
            if not device:
                return jsonify({'success': False, 'message': '设备不存在'}), 404
            
            return jsonify({
                'success': True,
                'device': dict(device)
            })
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取设备信息失败: {str(e)}'}), 500

@mobile_app_management_api.route('/api/mobile/device/<device_id>', methods=['PUT'])
def update_device(device_id):
    """更新设备信息"""
    try:
        data = request.get_json() or {}
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM mobile_devices WHERE device_id = ?', (device_id,))
            
            if not cursor.fetchone():
                return jsonify({'success': False, 'message': '设备不存在'}), 404
            
            update_fields = []
            update_values = []
            
            if 'device_name' in data:
                update_fields.append('device_name = ?')
                update_values.append(data['device_name'])
            if 'device_type' in data:
                update_fields.append('device_type = ?')
                update_values.append(data['device_type'])
            if 'os_type' in data:
                update_fields.append('os_type = ?')
                update_values.append(data['os_type'])
            if 'os_version' in data:
                update_fields.append('os_version = ?')
                update_values.append(data['os_version'])
            if 'app_version' in data:
                update_fields.append('app_version = ?')
                update_values.append(data['app_version'])
            if 'token' in data:
                update_fields.append('token = ?')
                update_values.append(data['token'])
            if 'status' in data:
                update_fields.append('status = ?')
                update_values.append(data['status'])
            if 'metadata' in data:
                update_fields.append('metadata = ?')
                update_values.append(json.dumps(data['metadata']))
            
            update_fields.append('last_seen = ?')
            update_values.append(datetime.now().isoformat())
            update_values.append(device_id)
            
            if update_fields:
                query = f'UPDATE mobile_devices SET {", ".join(update_fields)} WHERE device_id = ?'
                cursor.execute(query, update_values)
                conn.commit()
            
            return jsonify({'success': True, 'message': '设备信息更新成功'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'更新设备信息失败: {str(e)}'}), 500

@mobile_app_management_api.route('/api/mobile/device/<device_id>', methods=['DELETE'])
def delete_device(device_id):
    """删除设备"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM mobile_devices WHERE device_id = ?', (device_id,))
            
            if cursor.rowcount == 0:
                return jsonify({'success': False, 'message': '设备不存在'}), 404
            
            conn.commit()
        
        return jsonify({'success': True, 'message': '设备已删除'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'删除设备失败: {str(e)}'}), 500

@mobile_app_management_api.route('/api/mobile/device/list', methods=['GET'])
def get_device_list():
    """获取设备列表"""
    try:
        user_id = request.args.get('user_id') or session.get('user_id')
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            if user_id:
                cursor.execute('SELECT * FROM mobile_devices WHERE user_id = ?', (user_id,))
            else:
                cursor.execute('SELECT * FROM mobile_devices')
            
            devices = [dict(row) for row in cursor.fetchall()]
        
        return jsonify({
            'success': True,
            'devices': devices,
            'count': len(devices)
        })
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取设备列表失败: {str(e)}'}), 500

@mobile_app_management_api.route('/api/mobile/update/check', methods=['POST'])
def check_update():
    """检查应用更新"""
    try:
        data = request.get_json() or {}
        platform = data.get('platform', 'android')
        current_version = data.get('current_version', '0.0.0')
        device_id = data.get('device_id')
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM app_versions 
                WHERE platform = ? AND is_active = 1 
                ORDER BY id DESC LIMIT 1
            ''', (platform,))
            
            latest_version = cursor.fetchone()
            
            if not latest_version:
                return jsonify({
                    'success': True,
                    'has_update': False,
                    'message': '暂无可用更新',
                    'current_version': current_version,
                    'latest_version': current_version
                })
            
            latest_version_str = latest_version['version']
            
            def version_tuple(v):
                return tuple(map(int, v.split('.'))) if v else (0, 0, 0)
            
            has_update = version_tuple(latest_version_str) > version_tuple(current_version)
            
            if has_update:
                return jsonify({
                    'success': True,
                    'has_update': True,
                    'current_version': current_version,
                    'latest_version': latest_version_str,
                    'build_number': latest_version['build_number'],
                    'is_force': bool(latest_version['is_force']),
                    'download_url': latest_version['download_url'],
                    'changelog': latest_version['changelog'],
                    'min_version': latest_version['min_version']
                })
            
            return jsonify({
                'success': True,
                'has_update': False,
                'message': '当前已是最新版本',
                'current_version': current_version,
                'latest_version': latest_version_str
            })
    except Exception as e:
        return jsonify({'success': False, 'message': f'检查更新失败: {str(e)}'}), 500

@mobile_app_management_api.route('/api/mobile/update/list', methods=['GET'])
def get_update_list():
    """获取更新列表"""
    try:
        platform = request.args.get('platform')
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            if platform:
                cursor.execute('SELECT * FROM app_versions WHERE platform = ? ORDER BY id DESC', (platform,))
            else:
                cursor.execute('SELECT * FROM app_versions ORDER BY id DESC')
            
            versions = [dict(row) for row in cursor.fetchall()]
        
        return jsonify({
            'success': True,
            'versions': versions,
            'count': len(versions)
        })
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取更新列表失败: {str(e)}'}), 500

@mobile_app_management_api.route('/api/mobile/update', methods=['POST'])
def add_update():
    """添加新版本"""
    try:
        data = request.get_json() or {}
        platform = data.get('platform')
        version = data.get('version')
        
        if not platform or not version:
            return jsonify({'success': False, 'message': '平台和版本号不能为空'}), 400
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('SELECT MAX(build_number) FROM app_versions WHERE platform = ?', (platform,))
            max_build = cursor.fetchone()[0] or 0
            
            cursor.execute('''
                INSERT INTO app_versions 
                (platform, version, build_number, is_active, is_force, download_url, 
                 changelog, min_version, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                platform, version, max_build + 1,
                data.get('is_active', 1), data.get('is_force', 0),
                data.get('download_url'), data.get('changelog'),
                data.get('min_version'), datetime.now().isoformat()
            ))
            
            conn.commit()
        
        return jsonify({
            'success': True,
            'message': '版本添加成功',
            'version': version,
            'build_number': max_build + 1
        })
    except Exception as e:
        return jsonify({'success': False, 'message': f'添加版本失败: {str(e)}'}), 500

@mobile_app_management_api.route('/api/mobile/config', methods=['GET'])
def get_config():
    """获取远程配置"""
    try:
        platform = request.args.get('platform', 'all')
        keys = request.args.get('keys')
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            if keys:
                key_list = keys.split(',')
                placeholders = ','.join('?' * len(key_list))
                cursor.execute(f'''
                    SELECT config_key, config_value FROM mobile_configs 
                    WHERE (platform = ? OR platform = 'all') AND config_key IN ({placeholders})
                ''', [platform] + key_list)
            else:
                cursor.execute('''
                    SELECT config_key, config_value FROM mobile_configs 
                    WHERE platform = ? OR platform = 'all'
                ''', (platform,))
            
            configs = {row['config_key']: row['config_value'] for row in cursor.fetchall()}
        
        return jsonify({
            'success': True,
            'config': configs
        })
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取配置失败: {str(e)}'}), 500

@mobile_app_management_api.route('/api/mobile/config', methods=['POST'])
def set_config():
    """设置远程配置"""
    try:
        data = request.get_json() or {}
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            for key, value in data.items():
                if key in ['platform', 'description']:
                    continue
                
                platform = data.get('platform', 'all')
                description = data.get('description', '')
                
                cursor.execute('SELECT * FROM mobile_configs WHERE config_key = ?', (key,))
                
                if cursor.fetchone():
                    cursor.execute('''
                        UPDATE mobile_configs SET config_value = ?, platform = ?, 
                            description = ?, updated_at = ? WHERE config_key = ?
                    ''', (value, platform, description, datetime.now().isoformat(), key))
                else:
                    cursor.execute('''
                        INSERT INTO mobile_configs 
                        (config_key, config_value, platform, description, created_at, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (key, value, platform, description, datetime.now().isoformat(), datetime.now().isoformat()))
            
            conn.commit()
        
        return jsonify({'success': True, 'message': '配置更新成功'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'设置配置失败: {str(e)}'}), 500

@mobile_app_management_api.route('/api/mobile/notification', methods=['POST'])
def send_notification():
    """发送推送通知"""
    try:
        data = request.get_json() or {}
        title = data.get('title')
        content = data.get('content')
        
        if not title or not content:
            return jsonify({'success': False, 'message': '标题和内容不能为空'}), 400
        
        device_id = data.get('device_id')
        user_id = data.get('user_id') or session.get('user_id')
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO push_notifications 
                (device_id, user_id, title, content, type, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (device_id, user_id, title, content, data.get('type', 'info'), datetime.now().isoformat()))
            
            conn.commit()
        
        return jsonify({
            'success': True,
            'message': '通知已发送',
            'notification_id': cursor.lastrowid
        })
    except Exception as e:
        return jsonify({'success': False, 'message': f'发送通知失败: {str(e)}'}), 500

@mobile_app_management_api.route('/api/mobile/notification/list', methods=['GET'])
def get_notification_list():
    """获取通知列表"""
    try:
        user_id = request.args.get('user_id') or session.get('user_id')
        device_id = request.args.get('device_id')
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            if device_id:
                cursor.execute('SELECT * FROM push_notifications WHERE device_id = ? ORDER BY created_at DESC', (device_id,))
            elif user_id:
                cursor.execute('SELECT * FROM push_notifications WHERE user_id = ? ORDER BY created_at DESC', (user_id,))
            else:
                cursor.execute('SELECT * FROM push_notifications ORDER BY created_at DESC')
            
            notifications = [dict(row) for row in cursor.fetchall()]
        
        return jsonify({
            'success': True,
            'notifications': notifications,
            'count': len(notifications)
        })
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取通知列表失败: {str(e)}'}), 500

@mobile_app_management_api.route('/api/mobile/notification/<notification_id>', methods=['PUT'])
def update_notification(notification_id):
    """更新通知状态"""
    try:
        data = request.get_json() or {}
        status = data.get('status')
        
        if not status:
            return jsonify({'success': False, 'message': '状态不能为空'}), 400
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM push_notifications WHERE id = ?', (notification_id,))
            
            if not cursor.fetchone():
                return jsonify({'success': False, 'message': '通知不存在'}), 404
            
            cursor.execute('UPDATE push_notifications SET status = ?, sent_at = ? WHERE id = ?',
                          (status, datetime.now().isoformat(), notification_id))
            conn.commit()
        
        return jsonify({'success': True, 'message': '通知状态已更新'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'更新通知状态失败: {str(e)}'}), 500

@mobile_app_management_api.route('/api/mobile/stats', methods=['GET'])
def get_mobile_stats():
    """获取移动端统计数据"""
    try:
        user_id = request.args.get('user_id') or session.get('user_id')
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*) FROM mobile_devices')
            total_devices = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM mobile_devices WHERE status = ?', ('online',))
            online_devices = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM push_notifications WHERE status = ?', ('pending',))
            pending_notifications = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM app_versions')
            total_versions = cursor.fetchone()[0]
            
            if user_id:
                cursor.execute('SELECT COUNT(*) FROM mobile_devices WHERE user_id = ?', (user_id,))
                user_devices = cursor.fetchone()[0]
                
                cursor.execute('SELECT COUNT(*) FROM push_notifications WHERE user_id = ?', (user_id,))
                user_notifications = cursor.fetchone()[0]
            else:
                user_devices = 0
                user_notifications = 0
        
        return jsonify({
            'success': True,
            'stats': {
                'total_devices': total_devices,
                'online_devices': online_devices,
                'pending_notifications': pending_notifications,
                'total_versions': total_versions,
                'user_devices': user_devices,
                'user_notifications': user_notifications
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取统计数据失败: {str(e)}'}), 500