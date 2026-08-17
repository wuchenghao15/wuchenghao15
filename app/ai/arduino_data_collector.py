#!/usr/bin/env python3
import sqlite3
import os
import json
from datetime import datetime
from collections import defaultdict

DATABASE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '..', 'app.db')

_SENSOR_TYPES = {
    'temperature': {'name': '温度传感器', 'unit': '°C', 'min': -40, 'max': 125},
    'humidity': {'name': '湿度传感器', 'unit': '%', 'min': 0, 'max': 100},
    'distance': {'name': '距离传感器', 'unit': 'cm', 'min': 0, 'max': 400},
    'light': {'name': '光线传感器', 'unit': 'lux', 'min': 0, 'max': 1023},
    'sound': {'name': '声音传感器', 'unit': 'dB', 'min': 0, 'max': 1023},
    'motion': {'name': '运动传感器', 'unit': '', 'min': 0, 'max': 1},
    'voltage': {'name': '电压传感器', 'unit': 'V', 'min': 0, 'max': 5},
    'current': {'name': '电流传感器', 'unit': 'mA', 'min': 0, 'max': 5000}
}

class ArduinoDataCollector:
    """Arduino传感器数据采集器 - 收集和管理传感器数据"""
    
    def __init__(self):
        self.conn = sqlite3.connect(DATABASE_PATH)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()
        self._create_tables()
    
    def _create_tables(self):
        """创建传感器数据相关表"""
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS sensor_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_id TEXT NOT NULL,
                sensor_type TEXT NOT NULL,
                value REAL NOT NULL,
                unit TEXT,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'normal'
            )
        ''')
        
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS arduino_devices (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                type TEXT DEFAULT 'arduino_uno',
                status TEXT DEFAULT 'offline',
                last_connect_time TEXT,
                last_data_time TEXT,
                connected_pins TEXT DEFAULT '[]',
                sensor_count INTEGER DEFAULT 0
            )
        ''')
        
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS sensor_alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_id TEXT,
                sensor_type TEXT,
                threshold_type TEXT,
                threshold_value REAL,
                current_value REAL,
                alert_time TEXT DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'active'
            )
        ''')
        
        self.conn.commit()
    
    def add_device(self, device_id, name, type='arduino_uno'):
        """添加设备"""
        try:
            self.cursor.execute('''
                INSERT INTO arduino_devices (id, name, type)
                VALUES (?, ?, ?)
            ''', (device_id, name, type))
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
    
    def update_device_status(self, device_id, status, last_connect_time=None):
        """更新设备状态"""
        updates = ['status = ?']
        params = [status]
        
        if last_connect_time:
            updates.append('last_connect_time = ?')
            params.append(last_connect_time)
        
        params.append(device_id)
        
        query = f'UPDATE arduino_devices SET {", ".join(updates)} WHERE id = ?'
        self.cursor.execute(query, params)
        self.conn.commit()
        return self.cursor.rowcount > 0
    
    def record_sensor_data(self, device_id, sensor_type, value, unit=None):
        """记录传感器数据"""
        if sensor_type in _SENSOR_TYPES:
            unit = unit or _SENSOR_TYPES[sensor_type]['unit']
            
            self.cursor.execute('''
                INSERT INTO sensor_data (device_id, sensor_type, value, unit)
                VALUES (?, ?, ?, ?)
            ''', (device_id, sensor_type, value, unit))
            
            self.cursor.execute('''
                UPDATE arduino_devices 
                SET last_data_time = CURRENT_TIMESTAMP, status = 'online'
                WHERE id = ?
            ''', (device_id,))
            
            self._check_alerts(device_id, sensor_type, value)
            
            self.conn.commit()
    
    def _check_alerts(self, device_id, sensor_type, value):
        """检查告警条件"""
        if sensor_type == 'temperature':
            if value > 80:
                self._create_alert(device_id, sensor_type, 'high', 80, value)
            elif value < -10:
                self._create_alert(device_id, sensor_type, 'low', -10, value)
        elif sensor_type == 'humidity':
            if value > 90:
                self._create_alert(device_id, sensor_type, 'high', 90, value)
            elif value < 10:
                self._create_alert(device_id, sensor_type, 'low', 10, value)
        elif sensor_type == 'distance':
            if value < 10:
                self._create_alert(device_id, sensor_type, 'low', 10, value)
    
    def _create_alert(self, device_id, sensor_type, threshold_type, threshold_value, current_value):
        """创建告警"""
        self.cursor.execute('''
            INSERT INTO sensor_alerts 
            (device_id, sensor_type, threshold_type, threshold_value, current_value)
            VALUES (?, ?, ?, ?, ?)
        ''', (device_id, sensor_type, threshold_type, threshold_value, current_value))
    
    def get_device_data(self, device_id, sensor_type=None, limit=100):
        """获取设备传感器数据"""
        query = 'SELECT * FROM sensor_data WHERE device_id = ?'
        params = [device_id]
        
        if sensor_type:
            query += ' AND sensor_type = ?'
            params.append(sensor_type)
        
        query += ' ORDER BY timestamp DESC LIMIT ?'
        params.append(limit)
        
        self.cursor.execute(query, params)
        return [dict(row) for row in self.cursor.fetchall()]
    
    def get_device_list(self):
        """获取设备列表"""
        self.cursor.execute('SELECT * FROM arduino_devices')
        return [dict(row) for row in self.cursor.fetchall()]
    
    def get_sensor_summary(self, device_id):
        """获取传感器数据摘要"""
        self.cursor.execute('''
            SELECT sensor_type, COUNT(*), AVG(value), MIN(value), MAX(value)
            FROM sensor_data 
            WHERE device_id = ?
            GROUP BY sensor_type
        ''', (device_id,))
        
        summary = {}
        for row in self.cursor.fetchall():
            sensor_type = row[0]
            summary[sensor_type] = {
                'count': row[1],
                'avg': round(row[2], 2),
                'min': round(row[3], 2),
                'max': round(row[4], 2),
                'name': _SENSOR_TYPES.get(sensor_type, {}).get('name', sensor_type),
                'unit': _SENSOR_TYPES.get(sensor_type, {}).get('unit', '')
            }
        
        return summary
    
    def get_recent_alerts(self, limit=20):
        """获取最近告警"""
        self.cursor.execute('''
            SELECT sa.*, ad.name as device_name
            FROM sensor_alerts sa
            LEFT JOIN arduino_devices ad ON sa.device_id = ad.id
            ORDER BY sa.alert_time DESC LIMIT ?
        ''', (limit,))
        
        alerts = []
        for row in self.cursor.fetchall():
            alert = dict(row)
            alert['sensor_name'] = _SENSOR_TYPES.get(row['sensor_type'], {}).get('name', row['sensor_type'])
            alerts.append(alert)
        
        return alerts
    
    def get_sensor_types(self):
        """获取支持的传感器类型"""
        return _SENSOR_TYPES
    
    def export_data(self, device_id, start_time=None, end_time=None):
        """导出传感器数据"""
        query = 'SELECT * FROM sensor_data WHERE device_id = ?'
        params = [device_id]
        
        if start_time:
            query += ' AND timestamp >= ?'
            params.append(start_time)
        if end_time:
            query += ' AND timestamp <= ?'
            params.append(end_time)
        
        query += ' ORDER BY timestamp ASC'
        self.cursor.execute(query, params)
        
        data = []
        for row in self.cursor.fetchall():
            data.append({
                'timestamp': row['timestamp'],
                'sensor_type': row['sensor_type'],
                'value': row['value'],
                'unit': row['unit'],
                'status': row['status']
            })
        
        return {
            'device_id': device_id,
            'count': len(data),
            'data': data,
            'export_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    
    def close(self):
        """关闭数据库连接"""
        self.conn.close()

if __name__ == '__main__':
    collector = ArduinoDataCollector()
    
    logger.info("=== Arduino传感器数据采集器 ===")
    
    collector.add_device('device_001', '智能温湿度监控站', 'arduino_uno')
    logger.info("\n添加设备成功")
    
    collector.record_sensor_data('device_001', 'temperature', 25.5)
    collector.record_sensor_data('device_001', 'humidity', 60)
    collector.record_sensor_data('device_001', 'temperature', 26.0)
    collector.record_sensor_data('device_001', 'humidity', 58)
    collector.record_sensor_data('device_001', 'temperature', 27.2)
    logger.info("\n记录传感器数据成功")
    
    devices = collector.get_device_list()
    logger.info(f"\n设备列表: {len(devices)}个")
    for device in devices:
        logger.info(f"  {device['id']} - {device['name']} ({device['status']})")
    
    summary = collector.get_sensor_summary('device_001')
    logger.info("\n传感器数据摘要:")
    for sensor_type, info in summary.items():
        logger.info(f"  {info['name']}: {info['avg']}{info['unit']} (min: {info['min']}, max: {info['max']},计数: {info['count']})")
    
    data = collector.get_device_data('device_001', 'temperature', 5)
    logger.info(f"\n温度数据: {len(data)}条")
    for d in data:
        logger.info(f"  {d['timestamp']}: {d['value']}{d['unit']}")
    
    sensor_types = collector.get_sensor_types()
    logger.info(f"\n支持的传感器类型: {len(sensor_types)}种")
    for key, info in sensor_types.items():
        logger.info(f"  {key}: {info['name']} ({info['unit']})")
    
    alerts = collector.get_recent_alerts()
    logger.info(f"\n告警数量: {len(alerts)}")
    
    collector.close()