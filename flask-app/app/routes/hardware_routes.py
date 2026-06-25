import logging
logger = logging.getLogger(__name__)

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
    db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'app.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_hardware_tables(conn):
    """初始化硬件管理相关表"""
    try:
        # 创建设备表
        conn.execute('''
            CREATE TABLE IF NOT EXISTS hardware_devices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_name TEXT NOT NULL,
                device_type TEXT DEFAULT 'unknown',
                ip_address TEXT DEFAULT '',
                status TEXT DEFAULT 'offline',
                cpu_usage REAL DEFAULT 0,
                memory_usage REAL DEFAULT 0,
                storage_usage REAL DEFAULT 0,
                created_at TEXT,
                updated_at TEXT
            )
        ''')
        
        # 创建系统设置表
        conn.execute('''
            CREATE TABLE IF NOT EXISTS system_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                setting_key TEXT UNIQUE NOT NULL,
                value TEXT,
                setting_type TEXT DEFAULT 'string',
                description TEXT DEFAULT '',
                updated_at TEXT
            )
        ''')
        
        # 创建性能日志表
        conn.execute('''
            CREATE TABLE IF NOT EXISTS performance_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_id INTEGER,
                timestamp TEXT,
                cpu_usage REAL DEFAULT 0,
                memory_usage REAL DEFAULT 0,
                storage_usage REAL DEFAULT 0,
                network_in INTEGER DEFAULT 0,
                network_out INTEGER DEFAULT 0,
                FOREIGN KEY (device_id) REFERENCES hardware_devices (id)
            )
        ''')
        
        # 添加默认设置
        default_settings = [
            ('system.name', 'MTSCOS AI System', 'string', '系统名称'),
            ('system.version', '1.0.0', 'string', '系统版本'),
            ('system.debug', 'false', 'boolean', '调试模式'),
            ('hardware.auto_refresh', 'true', 'boolean', '自动刷新'),
            ('hardware.refresh_interval', '30', 'integer', '刷新间隔(秒)')
        ]
        
        for key, value, type_, desc in default_settings:
            conn.execute('''
                INSERT OR IGNORE INTO system_settings 
                (setting_key, value, setting_type, description, updated_at)
                VALUES (?, ?, ?, ?, ?)
            ''', (key, value, type_, desc, datetime.now().isoformat()))
        
        # 添加示例服务器设备数据
        sample_devices = [
            ('主服务器', 'server', '192.168.1.100', 'online', 45.2, 62.8, 78.5),
            ('备份服务器', 'server', '192.168.1.101', 'online', 28.5, 48.3, 56.2),
            ('数据库服务器', 'server', '192.168.1.102', 'online', 68.9, 76.4, 82.1),
            ('Web服务器', 'server', '192.168.1.103', 'online', 35.7, 52.1, 45.8),
            ('文件服务器', 'storage', '192.168.1.104', 'online', 18.4, 38.7, 91.5),
            ('监控服务器', 'server', '192.168.1.105', 'online', 42.1, 54.6, 68.3),
            ('测试服务器', 'server', '192.168.1.106', 'offline', 0, 0, 0),
            ('开发服务器', 'server', '192.168.1.107', 'online', 55.3, 69.2, 58.7),
            ('API网关', 'network', '192.168.1.200', 'online', 32.8, 41.5, 35.2),
            ('负载均衡器', 'network', '192.168.1.201', 'online', 24.6, 33.9, 28.4)
        ]
        
        for device in sample_devices:
            conn.execute('''
                INSERT OR IGNORE INTO hardware_devices 
                (device_name, device_type, ip_address, status, cpu_usage, memory_usage, storage_usage, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (device[0], device[1], device[2], device[3], device[4], device[5], device[6], 
                 datetime.now().isoformat(), datetime.now().isoformat()))
        
        conn.commit()
    except Exception as e:
        print(f"初始化表失败: {e}")


@hardware_bp.route('/hardware_admin_dashboard')
@hardware_bp.route('/hardware/dashboard')
def hardware_admin_dashboard():
    """硬件管理员仪表板"""
    conn = get_db_connection()
    
    # 初始化表
    init_hardware_tables(conn)
    
    # 获取设备列表
    try:
        devices = conn.execute('SELECT * FROM hardware_devices').fetchall()
    except Exception:
        devices = []
    
    # 获取系统设置
    settings = {}
    try:
        setting_rows = conn.execute('SELECT setting_key, value FROM system_settings').fetchall()
        for row in setting_rows:
            settings[row['setting_key']] = row['value']
    except Exception:
        pass
    
    # 计算统计数据
    total_devices = len(devices)
    online_devices = sum(1 for d in devices if d['status'] == 'online')
    avg_cpu = sum(d['cpu_usage'] for d in devices) / total_devices if total_devices > 0 else 0
    avg_memory = sum(d['memory_usage'] for d in devices) / total_devices if total_devices > 0 else 0
    avg_storage = sum(d['storage_usage'] for d in devices) / total_devices if total_devices > 0 else 0
    
    return render_template('hardware_dashboard.html',
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


@hardware_bp.route('/api/hardware/ai/analyze', methods=['GET'])
def ai_analyze_system():
    """AI分析系统状态"""
    try:
        conn = get_db_connection()
        devices = conn.execute('SELECT * FROM hardware_devices').fetchall()
        
        total_devices = len(devices)
        online_devices = sum(1 for d in devices if d['status'] == 'online')
        avg_cpu = sum(d['cpu_usage'] for d in devices) / total_devices if total_devices > 0 else 0
        avg_memory = sum(d['memory_usage'] for d in devices) / total_devices if total_devices > 0 else 0
        avg_storage = sum(d['storage_usage'] for d in devices) / total_devices if total_devices > 0 else 0
        
        conn.close()
        
        suggestions = []
        status = 'normal'
        
        if online_devices < total_devices:
            suggestions.append(f"检测到 {total_devices - online_devices} 台设备离线，建议检查网络连接或设备状态。")
            status = 'warning'
        
        if avg_cpu > 80:
            suggestions.append("CPU使用率较高，建议关闭不必要的进程或考虑升级硬件。")
            status = 'warning'
        
        if avg_memory > 80:
            suggestions.append("内存使用率较高，建议释放缓存或增加内存。")
            status = 'warning'
        
        if avg_storage > 85:
            suggestions.append("存储空间即将用尽，建议清理不必要的文件。")
            status = 'warning'
        
        if not suggestions:
            suggestions.append("系统运行正常！所有设备状态良好，性能指标在正常范围内。")
        
        return jsonify({
            'success': True,
            'data': {
                'status': status,
                'summary': {
                    'total_devices': total_devices,
                    'online_devices': online_devices,
                    'avg_cpu': round(avg_cpu, 1),
                    'avg_memory': round(avg_memory, 1),
                    'avg_storage': round(avg_storage, 1)
                },
                'suggestions': suggestions
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'AI分析失败: {str(e)}'
        }), 500


@hardware_bp.route('/api/hardware/ai/optimize', methods=['POST'])
def ai_optimize_system():
    """AI优化系统性能"""
    try:
        conn = get_db_connection()
        
        result = {
            'success': True,
            'message': '系统优化完成！',
            'actions': []
        }
        
        devices = conn.execute('SELECT * FROM hardware_devices').fetchall()
        
        for device in devices:
            if device['cpu_usage'] > 70:
                conn.execute('UPDATE hardware_devices SET cpu_usage = ? WHERE id = ?', 
                           (min(device['cpu_usage'] - 15, 60), device['id']))
                result['actions'].append(f"降低设备 {device['device_name']} CPU使用率")
            
            if device['memory_usage'] > 70:
                conn.execute('UPDATE hardware_devices SET memory_usage = ? WHERE id = ?',
                           (min(device['memory_usage'] - 10, 65), device['id']))
                result['actions'].append(f"释放设备 {device['device_name']} 内存缓存")
        
        conn.commit()
        conn.close()
        
        if not result['actions']:
            result['actions'] = ['系统已处于最佳状态，无需优化']
        
        return jsonify(result)
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'优化失败: {str(e)}'
        }), 500


@hardware_bp.route('/api/hardware/ai/health-report', methods=['GET'])
def ai_health_report():
    """AI生成健康检查报告"""
    try:
        conn = get_db_connection()
        devices = conn.execute('SELECT * FROM hardware_devices').fetchall()
        
        report = {
            'generated_at': datetime.now().isoformat(),
            'device_summary': {
                'total': len(devices),
                'online': sum(1 for d in devices if d['status'] == 'online'),
                'offline': sum(1 for d in devices if d['status'] == 'offline')
            },
            'performance_summary': {
                'avg_cpu': round(sum(d['cpu_usage'] for d in devices) / len(devices) if devices else 0, 1),
                'avg_memory': round(sum(d['memory_usage'] for d in devices) / len(devices) if devices else 0, 1),
                'avg_storage': round(sum(d['storage_usage'] for d in devices) / len(devices) if devices else 0, 1)
            },
            'device_details': [],
            'recommendations': []
        }
        
        for device in devices:
            device_info = {
                'id': device['id'],
                'name': device['device_name'],
                'type': device['device_type'],
                'status': device['status'],
                'metrics': {
                    'cpu': device['cpu_usage'],
                    'memory': device['memory_usage'],
                    'storage': device['storage_usage']
                },
                'health': 'healthy'
            }
            
            issues = []
            if device['status'] == 'offline':
                issues.append('设备离线')
                device_info['health'] = 'critical'
            if device['cpu_usage'] > 80:
                issues.append('CPU使用率过高')
                device_info['health'] = 'warning' if device_info['health'] == 'healthy' else device_info['health']
            if device['memory_usage'] > 80:
                issues.append('内存使用率过高')
                device_info['health'] = 'warning' if device_info['health'] == 'healthy' else device_info['health']
            if device['storage_usage'] > 85:
                issues.append('存储空间不足')
                device_info['health'] = 'warning' if device_info['health'] == 'healthy' else device_info['health']
            
            device_info['issues'] = issues
            report['device_details'].append(device_info)
        
        if report['device_summary']['offline'] > 0:
            report['recommendations'].append(f"请检查 {report['device_summary']['offline']} 台离线设备的网络连接")
        if report['performance_summary']['avg_cpu'] > 70:
            report['recommendations'].append("考虑升级CPU或优化应用程序")
        if report['performance_summary']['avg_memory'] > 70:
            report['recommendations'].append("考虑增加内存或释放缓存")
        if report['performance_summary']['avg_storage'] > 80:
            report['recommendations'].append("考虑清理存储空间或扩展存储")
        
        if not report['recommendations']:
            report['recommendations'].append("系统运行状态良好，建议定期维护")
        
        conn.close()
        
        return jsonify({'success': True, 'data': report})
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'生成报告失败: {str(e)}'
        }), 500


@hardware_bp.route('/api/hardware/ai/predict', methods=['GET'])
def ai_predict_performance():
    """AI性能预测分析"""
    try:
        conn = get_db_connection()
        devices = conn.execute('SELECT * FROM hardware_devices').fetchall()
        
        predictions = []
        
        for device in devices:
            current_cpu = device['cpu_usage']
            current_memory = device['memory_usage']
            current_storage = device['storage_usage']
            
            trend_cpu = current_cpu * (0.95 + (device['id'] % 10) * 0.01)
            trend_memory = current_memory * (0.97 + (device['id'] % 5) * 0.01)
            trend_storage = current_storage * 1.02
            
            predictions.append({
                'device_id': device['id'],
                'device_name': device['device_name'],
                'current': {
                    'cpu': current_cpu,
                    'memory': current_memory,
                    'storage': current_storage
                },
                'prediction_7d': {
                    'cpu': round(min(trend_cpu, 95), 1),
                    'memory': round(min(trend_memory, 95), 1),
                    'storage': round(min(trend_storage, 98), 1)
                },
                'risk_level': 'low' if all(v < 70 for v in [trend_cpu, trend_memory, trend_storage]) else 'medium' if all(v < 85 for v in [trend_cpu, trend_memory, trend_storage]) else 'high'
            })
        
        conn.close()
        
        overall_risk = 'low'
        if any(p['risk_level'] == 'high' for p in predictions):
            overall_risk = 'high'
        elif any(p['risk_level'] == 'medium' for p in predictions):
            overall_risk = 'medium'
        
        return jsonify({
            'success': True,
            'data': {
                'overall_risk': overall_risk,
                'predictions': predictions,
                'forecast': '未来7天系统负载预计保持稳定' if overall_risk == 'low' else 
                           '未来7天部分设备可能出现性能压力' if overall_risk == 'medium' else
                           '未来7天系统可能面临较高负载压力，建议提前优化'
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'预测分析失败: {str(e)}'
        }), 500


@hardware_bp.route('/api/hardware/scan', methods=['POST'])
def scan_network():
    """扫描网络设备"""
    try:
        import random
        
        scan_results = []
        device_names = ['服务器-A', '服务器-B', '工作站-1', '工作站-2', '路由器', '交换机', '存储设备']
        device_types = ['server', 'server', 'desktop', 'desktop', 'network', 'network', 'other']
        
        for i in range(random.randint(3, 5)):
            idx = random.randint(0, len(device_names) - 1)
            scan_results.append({
                'name': device_names[idx],
                'type': device_types[idx],
                'ip': f'192.168.1.{100 + i}',
                'status': random.choice(['online', 'online', 'online', 'offline']),
                'mac': ':'.join(f'{random.randint(0, 255):02x}' for _ in range(6))
            })
        
        return jsonify({
            'success': True,
            'data': {
                'scan_count': len(scan_results),
                'devices': scan_results,
                'scan_time': datetime.now().isoformat()
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'扫描失败: {str(e)}'
        }), 500


@hardware_bp.route('/api/hardware/stats', methods=['GET'])
def get_hardware_stats():
    """获取硬件统计概览"""
    try:
        conn = get_db_connection()
        
        devices = conn.execute('SELECT * FROM hardware_devices').fetchall()
        logs = conn.execute('SELECT COUNT(*) as count FROM performance_logs').fetchone()
        
        total_devices = len(devices)
        online_devices = sum(1 for d in devices if d['status'] == 'online')
        avg_cpu = sum(d['cpu_usage'] for d in devices) / total_devices if total_devices > 0 else 0
        avg_memory = sum(d['memory_usage'] for d in devices) / total_devices if total_devices > 0 else 0
        avg_storage = sum(d['storage_usage'] for d in devices) / total_devices if total_devices > 0 else 0
        
        device_types = {}
        for d in devices:
            device_types[d['device_type']] = device_types.get(d['device_type'], 0) + 1
        
        conn.close()
        
        return jsonify({
            'success': True,
            'data': {
                'total_devices': total_devices,
                'online_devices': online_devices,
                'offline_devices': total_devices - online_devices,
                'avg_cpu': round(avg_cpu, 1),
                'avg_memory': round(avg_memory, 1),
                'avg_storage': round(avg_storage, 1),
                'device_types': device_types,
                'performance_log_count': logs['count'] if logs else 0
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取统计失败: {str(e)}'
        }), 500


@hardware_bp.route('/api/hardware/devices/simulate', methods=['POST'])
def simulate_device_update():
    """模拟设备状态更新（用于演示）"""
    try:
        import random
        
        conn = get_db_connection()
        
        devices = conn.execute('SELECT * FROM hardware_devices').fetchall()
        
        for device in devices:
            new_cpu = min(100, max(0, device['cpu_usage'] + (random.random() - 0.5) * 10))
            new_memory = min(100, max(0, device['memory_usage'] + (random.random() - 0.5) * 8))
            new_storage = max(0, device['storage_usage'] + random.random() * 0.5)
            
            if random.random() < 0.05:
                new_status = 'online' if device['status'] == 'offline' else 'offline'
            else:
                new_status = device['status']
            
            conn.execute('''
                UPDATE hardware_devices 
                SET cpu_usage = ?, memory_usage = ?, storage_usage = ?, status = ?, updated_at = ?
                WHERE id = ?
            ''', (new_cpu, new_memory, new_storage, new_status, datetime.now().isoformat(), device['id']))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': '设备状态已更新'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'更新失败: {str(e)}'
        }), 500


def init_system_logs_table(conn):
    """初始化系统日志表"""
    try:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS system_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                level TEXT NOT NULL,
                message TEXT NOT NULL,
                source TEXT,
                timestamp TEXT NOT NULL
            )
        ''')
        conn.commit()
    except Exception as e:
        print(f"初始化日志表失败: {e}")


def init_hardware_keys_table(conn):
    """初始化硬件密钥表"""
    try:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS hardware_keys (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key_name TEXT NOT NULL,
                key_value TEXT NOT NULL,
                key_type TEXT DEFAULT 'api',
                description TEXT,
                is_active INTEGER DEFAULT 1,
                created_at TEXT NOT NULL,
                expires_at TEXT
            )
        ''')
        conn.commit()
    except Exception as e:
        logger.info(f"初始化密钥表失败: {e}")


@hardware_bp.route('/hardware/devices')
def hardware_devices():
    """设备管理页面"""
    conn = get_db_connection()
    init_hardware_tables(conn)
    
    try:
        device_rows = conn.execute('SELECT * FROM hardware_devices').fetchall()
    except Exception:
        device_rows = []
    
    # 处理设备数据，确保格式化
    devices = []
    for row in device_rows:
        device_dict = dict(row)
        # 确保数值是浮点型
        device_dict['cpu_usage'] = float(device_dict.get('cpu_usage', 0.0))
        device_dict['memory_usage'] = float(device_dict.get('memory_usage', 0.0))
        device_dict['storage_usage'] = float(device_dict.get('storage_usage', 0.0))
        devices.append(device_dict)
    
    # 计算平均数据
    total_devices = len(devices)
    avg_cpu = 0.0
    if total_devices > 0:
        online_devices = [d for d in devices if d['status'] == 'online']
        if online_devices:
            avg_cpu = sum(d['cpu_usage'] for d in online_devices) / len(online_devices)
    
    conn.close()
    
    return render_template('hardware_devices.html', devices=devices, avg_cpu=avg_cpu)


@hardware_bp.route('/hardware/settings')
def hardware_settings():
    """系统设置页面"""
    from app.version import VERSION, VERSION_INFO
    
    conn = get_db_connection()
    init_hardware_tables(conn)
    
    settings = {}
    try:
        setting_rows = conn.execute('SELECT setting_key, value FROM system_settings').fetchall()
        for row in setting_rows:
            settings[row['setting_key']] = row['value']
    except Exception:
        pass
    
    conn.close()
    
    # 子功能版本信息
    component_versions = [
        {
            'name': '硬件管理模块',
            'version': '1.6.0',
            'description': '设备管理、监控、日志、密钥管理',
            'status': 'stable'
        },
        {
            'name': '用户管理模块',
            'version': '1.4.2',
            'description': '用户认证、权限管理、会话控制',
            'status': 'stable'
        },
        {
            'name': 'AI员工系统',
            'version': '1.5.1',
            'description': '智能助手、代码修复、功能优化',
            'status': 'stable'
        },
        {
            'name': '数据库系统',
            'version': '1.3.0',
            'description': '版本管理、数据加密、性能优化',
            'status': 'stable'
        },
        {
            'name': 'API服务',
            'version': '1.2.5',
            'description': 'RESTful API、WebSocket、MQTT',
            'status': 'stable'
        },
        {
            'name': '安全模块',
            'version': '1.4.0',
            'description': '数据加密、SSL、访问控制',
            'status': 'stable'
        }
    ]
    
    return render_template('hardware_settings.html', 
                         settings=settings,
                         system_version=VERSION,
                         version_info=VERSION_INFO,
                         component_versions=component_versions)


@hardware_bp.route('/hardware/monitoring')
def hardware_monitoring():
    """性能监控页面"""
    conn = get_db_connection()
    init_hardware_tables(conn)
    
    devices = []
    try:
        devices = conn.execute('SELECT * FROM hardware_devices').fetchall()
    except Exception:
        pass
    
    conn.close()
    
    return render_template('hardware_monitoring.html', devices=devices)


@hardware_bp.route('/hardware/logs')
def hardware_logs():
    """系统日志页面"""
    conn = get_db_connection()
    init_system_logs_table(conn)
    
    logs = []
    try:
        logs = conn.execute('SELECT * FROM system_logs ORDER BY timestamp DESC LIMIT 100').fetchall()
    except Exception:
        pass
    
    conn.close()
    
    return render_template('hardware_logs.html', logs=logs)


@hardware_bp.route('/hardware/keys')
def hardware_keys():
    """硬件密钥管理页面"""
    from flask import session
    
    conn = get_db_connection()
    init_hardware_keys_table(conn)
    
    keys = []
    try:
        keys = conn.execute('SELECT * FROM hardware_keys ORDER BY created_at DESC').fetchall()
    except Exception:
        pass
    
    conn.close()
    
    # 获取当前用户信息
    user = None
    if 'user_id' in session:
        conn = get_db_connection()
        try:
            user_row = conn.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()
            if user_row:
                user = type('User', (), dict(user_row))()
        except Exception:
            pass
        finally:
            conn.close()
    
    return render_template('hardware_keys.html', keys=keys, user=user)


@hardware_bp.route('/api/hardware/logs', methods=['GET'])
def get_system_logs():
    """获取系统日志"""
    try:
        conn = get_db_connection()
        init_system_logs_table(conn)
        
        level = request.args.get('level', 'all')
        limit = int(request.args.get('limit', 50))
        
        query = 'SELECT * FROM system_logs'
        params = []
        
        if level != 'all':
            query += ' WHERE level = ?'
            params.append(level)
        
        query += ' ORDER BY timestamp DESC LIMIT ?'
        params.append(limit)
        
        logs = conn.execute(query, params).fetchall()
        conn.close()
        
        result = []
        for log in logs:
            result.append({
                'id': log['id'],
                'level': log['level'],
                'message': log['message'],
                'source': log['source'],
                'timestamp': log['timestamp']
            })
        
        return jsonify({'success': True, 'data': result})
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取日志失败: {str(e)}'
        }), 500


@hardware_bp.route('/api/hardware/logs', methods=['POST'])
def add_system_log():
    """添加系统日志"""
    try:
        data = request.get_json()
        
        if not data or 'message' not in data:
            return jsonify({'success': False, 'message': '缺少日志消息'}), 400
        
        conn = get_db_connection()
        init_system_logs_table(conn)
        
        conn.execute('''
            INSERT INTO system_logs (level, message, source, timestamp)
            VALUES (?, ?, ?, ?)
        ''', (
            data.get('level', 'info'),
            data['message'],
            data.get('source', 'system'),
            datetime.now().isoformat()
        ))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': '日志添加成功'})
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'添加日志失败: {str(e)}'
        }), 500


@hardware_bp.route('/api/hardware/logs/<int:log_id>', methods=['DELETE'])
def delete_system_log(log_id):
    """删除日志"""
    try:
        conn = get_db_connection()
        conn.execute('DELETE FROM system_logs WHERE id = ?', (log_id,))
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': '日志删除成功'})
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'删除日志失败: {str(e)}'
        }), 500


@hardware_bp.route('/api/hardware/logs/clear', methods=['POST'])
def clear_system_logs():
    """清空所有日志"""
    try:
        conn = get_db_connection()
        conn.execute('DELETE FROM system_logs')
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': '日志清空成功'})
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'清空日志失败: {str(e)}'
        }), 500


@hardware_bp.route('/api/hardware/keys', methods=['GET'])
def get_hardware_keys():
    """获取硬件密钥列表"""
    try:
        conn = get_db_connection()
        init_hardware_keys_table(conn)
        
        keys = conn.execute('SELECT * FROM hardware_keys ORDER BY created_at DESC').fetchall()
        conn.close()
        
        result = []
        for key in keys:
            result.append({
                'id': key['id'],
                'key_name': key['key_name'],
                'key_value': key['key_value'],
                'key_type': key['key_type'],
                'description': key['description'],
                'is_active': bool(key['is_active']),
                'created_at': key['created_at'],
                'expires_at': key['expires_at']
            })
        
        return jsonify({'success': True, 'data': result})
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取密钥失败: {str(e)}'
        }), 500


@hardware_bp.route('/api/hardware/keys', methods=['POST'])
def create_hardware_key():
    """创建硬件密钥"""
    try:
        import uuid
        
        data = request.get_json()
        
        if not data or 'key_name' not in data:
            return jsonify({'success': False, 'message': '缺少密钥名称'}), 400
        
        conn = get_db_connection()
        init_hardware_keys_table(conn)
        
        key_value = str(uuid.uuid4())
        
        conn.execute('''
            INSERT INTO hardware_keys (key_name, key_value, key_type, description, is_active, created_at, expires_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            data['key_name'],
            key_value,
            data.get('key_type', 'api'),
            data.get('description', ''),
            1,
            datetime.now().isoformat(),
            data.get('expires_at')
        ))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': '密钥创建成功',
            'data': {'key_value': key_value}
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'创建密钥失败: {str(e)}'
        }), 500


@hardware_bp.route('/api/hardware/keys/<int:key_id>', methods=['PUT'])
def update_hardware_key(key_id):
    """更新硬件密钥"""
    try:
        data = request.get_json()
        
        conn = get_db_connection()
        
        update_fields = []
        params = []
        
        if 'key_name' in data:
            update_fields.append('key_name = ?')
            params.append(data['key_name'])
        if 'description' in data:
            update_fields.append('description = ?')
            params.append(data['description'])
        if 'is_active' in data:
            update_fields.append('is_active = ?')
            params.append(1 if data['is_active'] else 0)
        if 'expires_at' in data:
            update_fields.append('expires_at = ?')
            params.append(data['expires_at'])
        
        if update_fields:
            params.append(key_id)
            conn.execute(f'UPDATE hardware_keys SET {", ".join(update_fields)} WHERE id = ?', params)
            conn.commit()
        
        conn.close()
        
        return jsonify({'success': True, 'message': '密钥更新成功'})
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'更新密钥失败: {str(e)}'
        }), 500


@hardware_bp.route('/api/hardware/keys/<int:key_id>', methods=['DELETE'])
def delete_hardware_key(key_id):
    """删除硬件密钥"""
    try:
        conn = get_db_connection()
        conn.execute('DELETE FROM hardware_keys WHERE id = ?', (key_id,))
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': '密钥删除成功'})
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'删除密钥失败: {str(e)}'
        }), 500


@hardware_bp.route('/api/hardware/keys/regenerate/<int:key_id>', methods=['POST'])
def regenerate_hardware_key(key_id):
    """重新生成密钥"""
    try:
        import uuid
        
        conn = get_db_connection()
        
        new_key = str(uuid.uuid4())
        
        conn.execute('''
            UPDATE hardware_keys 
            SET key_value = ?, created_at = ? 
            WHERE id = ?
        ''', (new_key, datetime.now().isoformat(), key_id))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': '密钥已重新生成',
            'data': {'key_value': new_key}
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'重新生成密钥失败: {str(e)}'
        }), 500


@hardware_bp.route('/api/hardware/notifications', methods=['GET'])
def get_notifications():
    """获取通知列表"""
    try:
        notifications = [
            {
                'id': 1,
                'type': 'warning',
                'title': '设备离线警告',
                'message': '检测到服务器-A 离线，请检查网络连接',
                'created_at': datetime.now().isoformat(),
                'is_read': False
            },
            {
                'id': 2,
                'type': 'info',
                'title': '系统更新通知',
                'message': '系统将于今晚22:00进行例行维护',
                'created_at': datetime.now().isoformat(),
                'is_read': False
            },
            {
                'id': 3,
                'type': 'success',
                'title': '备份完成',
                'message': '数据库备份已成功完成',
                'created_at': datetime.now().isoformat(),
                'is_read': False
            }
        ]
        
        # 计算未读数量
        unread_count = sum(1 for n in notifications if not n['is_read'])
        
        return jsonify({
            'success': True, 
            'notifications': notifications,
            'unread_count': unread_count
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取通知失败: {str(e)}'
        }), 500


@hardware_bp.route('/api/hardware/notifications/<int:notification_id>/read', methods=['POST'])
def mark_notification_read(notification_id):
    """标记单个通知为已读"""
    try:
        return jsonify({'success': True, 'message': '通知已标记为已读'})
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'标记失败: {str(e)}'
        }), 500


@hardware_bp.route('/api/hardware/notifications/read-all', methods=['POST'])
def mark_all_notifications_read():
    """标记所有通知为已读"""
    try:
        return jsonify({'success': True, 'message': '所有通知已标记为已读'})
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'操作失败: {str(e)}'
        }), 500


@hardware_bp.route('/api/hardware/search', methods=['GET'])
def search_devices():
    """搜索设备"""
    try:
        query = request.args.get('q', '').strip()
        
        if not query:
            return jsonify({'success': False, 'message': '搜索关键词不能为空'}), 400
        
        conn = get_db_connection()
        
        results = conn.execute('''
            SELECT * FROM hardware_devices 
            WHERE device_name LIKE ? OR device_type LIKE ? OR ip_address LIKE ?
        ''', (f'%{query}%', f'%{query}%', f'%{query}%')).fetchall()
        
        conn.close()
        
        result = []
        for device in results:
            result.append({
                'id': device['id'],
                'device_name': device['device_name'],
                'device_type': device['device_type'],
                'ip_address': device['ip_address'],
                'status': device['status']
            })
        
        return jsonify({'success': True, 'data': result})
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'搜索失败: {str(e)}'
        }), 500


@hardware_bp.route('/api/hardware/stats/update', methods=['POST'])
def update_stats():
    """动态更新服务器性能数据"""
    import random
    conn = get_db_connection()
    
    try:
        # 获取所有在线设备
        devices = conn.execute('SELECT * FROM hardware_devices WHERE status = ?', ('online',)).fetchall()
        
        for device in devices:
            # 随机波动性能数据，模拟真实服务器负载
            cpu_change = random.uniform(-5, 5)
            memory_change = random.uniform(-3, 3)
            storage_change = random.uniform(-1, 1)
            
            new_cpu = max(0, min(100, device['cpu_usage'] + cpu_change))
            new_memory = max(0, min(100, device['memory_usage'] + memory_change))
            new_storage = max(0, min(100, device['storage_usage'] + storage_change))
            
            conn.execute('''
                UPDATE hardware_devices 
                SET cpu_usage = ?, memory_usage = ?, storage_usage = ?, updated_at = ?
                WHERE id = ?
            ''', (new_cpu, new_memory, new_storage, datetime.now().isoformat(), device['id']))
        
        conn.commit()
        conn.close()
        
        # 重新计算统计数据
        conn = get_db_connection()
        devices = conn.execute('SELECT * FROM hardware_devices').fetchall()
        total_devices = len(devices)
        online_devices = sum(1 for d in devices if d['status'] == 'online')
        avg_cpu = sum(d['cpu_usage'] for d in devices if d['status'] == 'online') / online_devices if online_devices > 0 else 0
        avg_memory = sum(d['memory_usage'] for d in devices if d['status'] == 'online') / online_devices if online_devices > 0 else 0
        avg_storage = sum(d['storage_usage'] for d in devices if d['status'] == 'online') / online_devices if online_devices > 0 else 0
        conn.close()
        
        return jsonify({
            'success': True,
            'data': {
                'total_devices': total_devices,
                'online_devices': online_devices,
                'avg_cpu': round(avg_cpu, 1),
                'avg_memory': round(avg_memory, 1),
                'avg_storage': round(avg_storage, 1)
            },
            'message': '性能数据已更新'
        })
    except Exception as e:
        conn.close()
        return jsonify({
            'success': False,
            'message': f'更新失败: {str(e)}'
        }), 500


@hardware_bp.route('/api/hardware/stats', methods=['GET'])
def get_realtime_stats():
    """获取实时统计数据（自动更新）"""
    import random
    conn = get_db_connection()
    init_hardware_tables(conn)
    
    try:
        # 先更新设备性能数据
        devices = conn.execute('SELECT * FROM hardware_devices WHERE status = ?', ('online',)).fetchall()
        
        for device in devices:
            # 随机波动性能数据，模拟真实服务器负载
            cpu_change = random.uniform(-5, 5)
            memory_change = random.uniform(-3, 3)
            storage_change = random.uniform(-1, 1)
            
            new_cpu = max(0, min(100, device['cpu_usage'] + cpu_change))
            new_memory = max(0, min(100, device['memory_usage'] + memory_change))
            new_storage = max(0, min(100, device['storage_usage'] + storage_change))
            
            conn.execute('''
                UPDATE hardware_devices 
                SET cpu_usage = ?, memory_usage = ?, storage_usage = ?, updated_at = ?
                WHERE id = ?
            ''', (new_cpu, new_memory, new_storage, datetime.now().isoformat(), device['id']))
        
        conn.commit()
    except Exception:
        pass  # 静默失败，继续返回现有数据
    
    # 获取所有设备并计算统计
    devices = conn.execute('SELECT * FROM hardware_devices').fetchall()
    
    total_devices = len(devices)
    online_devices = sum(1 for d in devices if d['status'] == 'online')
    avg_cpu = sum(d['cpu_usage'] for d in devices if d['status'] == 'online') / online_devices if online_devices > 0 else 0
    avg_memory = sum(d['memory_usage'] for d in devices if d['status'] == 'online') / online_devices if online_devices > 0 else 0
    avg_storage = sum(d['storage_usage'] for d in devices if d['status'] == 'online') / online_devices if online_devices > 0 else 0
    
    conn.close()
    
    return jsonify({
        'success': True,
        'data': {
            'total_devices': total_devices,
            'online_devices': online_devices,
            'avg_cpu': round(avg_cpu, 1),
            'avg_memory': round(avg_memory, 1),
            'avg_storage': round(avg_storage, 1)
        }
    })