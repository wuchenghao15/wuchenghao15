#!/usr/bin/env python3
import sqlite3
import os
import psutil
import time
from datetime import datetime, timedelta

DATABASE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '..', 'app.db')

class AISystemMonitor:
    """AI系统监控仪表板 - 监控系统运行状态"""
    
    def __init__(self):
        self.conn = sqlite3.connect(DATABASE_PATH)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()
        self._create_tables()
    
    def _create_tables(self):
        """创建监控相关表"""
        self.cursor.execute(''' CREATE TABLE IF NOT EXISTS system_metrics ( id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp TEXT DEFAULT CURRENT_TIMESTAMP, cpu_usage REAL, memory_usage REAL, disk_usage REAL, network_bytes_sent INTEGER, network_bytes_recv INTEGER, active_users INTEGER, requests_per_second REAL, error_rate REAL ) ''')
        
        self.cursor.execute(''' CREATE TABLE IF NOT EXISTS process_logs ( id INTEGER PRIMARY KEY AUTOINCREMENT, process_name TEXT, status TEXT, pid INTEGER, started_at TEXT, stopped_at TEXT, restart_count INTEGER DEFAULT 0, last_error TEXT ) ''')
        
        self.conn.commit()
    
    def collect_system_metrics(self):
        """收集系统指标"""
        cpu_usage = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        network = psutil.net_io_counters()
        
        self.cursor.execute(''' INSERT INTO system_metrics (cpu_usage, memory_usage, disk_usage, network_bytes_sent, network_bytes_recv) VALUES (?, ?, ?, ?, ?) ''', (cpu_usage, memory.percent, disk.percent, network.bytes_sent, network.bytes_recv))
        
        self.conn.commit()
    
    def get_system_status(self):
        """获取系统状态"""
        cpu_usage = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        network = psutil.net_io_counters()
        boot_time = datetime.fromtimestamp(psutil.boot_time())
        
        return {
            'cpu': {
                'usage': cpu_usage,
                'cores': psutil.cpu_count(logical=True),
                'status': 'healthy' if cpu_usage < 80 else 'warning' if cpu_usage < 95 else 'critical'
            },
            'memory': {
                'usage': memory.percent,
                'total': round(memory.total / (1024**3), 2),
                'used': round(memory.used / (1024**3), 2),
                'available': round(memory.available / (1024**3), 2),
                'status': 'healthy' if memory.percent < 80 else 'warning' if memory.percent < 95 else 'critical'
            },
            'disk': {
                'usage': disk.percent,
                'total': round(disk.total / (1024**3), 2),
                'used': round(disk.used / (1024**3), 2),
                'free': round(disk.free / (1024**3), 2),
                'status': 'healthy' if disk.percent < 80 else 'warning' if disk.percent < 95 else 'critical'
            },
            'network': {
                'bytes_sent': round(network.bytes_sent / (1024**2), 2),
                'bytes_recv': round(network.bytes_recv / (1024**2), 2),
                'packets_sent': network.packets_sent,
                'packets_recv': network.packets_recv
            },
            'uptime': str(datetime.now() - boot_time),
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    
    def get_recent_metrics(self, minutes=60):
        """获取最近的系统指标"""
        cutoff_time = (datetime.now() - timedelta(minutes=minutes)).strftime('%Y-%m-%d %H:%M:%S')
        
        self.cursor.execute(''' SELECT * FROM system_metrics WHERE timestamp >= ? ORDER BY timestamp DESC LIMIT 60 ''', (cutoff_time,))
        
        metrics = [dict(row) for row in self.cursor.fetchall()]
        return metrics[::-1]
    
    def get_alert_summary(self):
        """获取告警摘要"""
        recent_metrics = self.get_recent_metrics(30)
        alerts = []
        
        for metric in recent_metrics:
            if metric['cpu_usage'] >= 95:
                alerts.append({
                    'type': 'critical',
                    'message': f'CPU使用率过高: {metric["cpu_usage"]}%',
                    'timestamp': metric['timestamp']
                })
            elif metric['cpu_usage'] >= 80:
                alerts.append({
                    'type': 'warning',
                    'message': f'CPU使用率偏高: {metric["cpu_usage"]}%',
                    'timestamp': metric['timestamp']
                })
            
            if metric['memory_usage'] >= 95:
                alerts.append({
                    'type': 'critical',
                    'message': f'内存使用率过高: {metric["memory_usage"]}%',
                    'timestamp': metric['timestamp']
                })
            elif metric['memory_usage'] >= 80:
                alerts.append({
                    'type': 'warning',
                    'message': f'内存使用率偏高: {metric["memory_usage"]}%',
                    'timestamp': metric['timestamp']
                })
            
            if metric['disk_usage'] >= 95:
                alerts.append({
                    'type': 'critical',
                    'message': f'磁盘使用率过高: {metric["disk_usage"]}%',
                    'timestamp': metric['timestamp']
                })
            elif metric['disk_usage'] >= 80:
                alerts.append({
                    'type': 'warning',
                    'message': f'磁盘使用率偏高: {metric["disk_usage"]}%',
                    'timestamp': metric['timestamp']
                })
        
        return {
            'total_alerts': len(alerts),
            'critical_alerts': len([a for a in alerts if a['type'] == 'critical']),
            'warning_alerts': len([a for a in alerts if a['type'] == 'warning']),
            'recent_alerts': alerts[:10]
        }
    
    def log_process_status(self, process_name, status, pid=None, error=None):
        """记录进程状态"""
        self.cursor.execute(''' INSERT INTO process_logs (process_name, status, pid, last_error) VALUES (?, ?, ?, ?) ''', (process_name, status, pid, error))
        
        if status == 'restarted':
            self.cursor.execute(''' UPDATE process_logs SET restart_count = restart_count + 1 WHERE process_name = ? ''', (process_name,))
        
        self.conn.commit()
    
    def get_process_status(self, process_name=None):
        """获取进程状态"""
        query = 'SELECT * FROM process_logs WHERE 1=1'
        params = []
        
        if process_name:
            query += ' AND process_name = ?'
            params.append(process_name)
        
        query += ' ORDER BY id DESC LIMIT 20'
        
        self.cursor.execute(query, params)
        return [dict(row) for row in self.cursor.fetchall()]
    
    def get_database_stats(self):
        """获取数据库统计"""
        self.cursor.execute(''' SELECT name FROM sqlite_master WHERE type='table' ''')
        tables = [row['name'] for row in self.cursor.fetchall()]
        
        table_stats = {}
        for table in tables:
            try:
                self.cursor.execute(f'SELECT COUNT(*) FROM {table}')
                count = self.cursor.fetchone()[0]
                table_stats[table] = count
            except Exception as e:
                pass
        
        return {
            'tables_count': len(tables),
            'tables': table_stats,
            'total_records': sum(table_stats.values())
        }
    
    def get_health_summary(self):
        """获取健康检查摘要"""
        status = self.get_system_status()
        alerts = self.get_alert_summary()
        db_stats = self.get_database_stats()
        
        overall_status = 'healthy'
        if alerts['critical_alerts'] > 0:
            overall_status = 'critical'
        elif alerts['warning_alerts'] > 0:
            overall_status = 'warning'
        
        return {
            'overall_status': overall_status,
            'cpu_status': status['cpu']['status'],
            'memory_status': status['memory']['status'],
            'disk_status': status['disk']['status'],
            'total_alerts': alerts['total_alerts'],
            'critical_alerts': alerts['critical_alerts'],
            'warning_alerts': alerts['warning_alerts'],
            'database_tables': db_stats['tables_count'],
            'database_records': db_stats['total_records'],
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    
    def close(self):
        """关闭数据库连接"""
        self.conn.close()

if __name__ == '__main__':
    monitor = AISystemMonitor()
    
    logger.info("=== AI系统监控仪表板 ===")
    
    logger.info("\n=== 系统状态 ===")
    status = monitor.get_system_status()
    logger.info(f"CPU: {status['cpu']['usage']}% ({status['cpu']['cores']}核) - {status['cpu']['status']}")
    logger.info(f"内存: {status['memory']['usage']}% ( {status['memory']['used']}/{status['memory']['total']}GB) - {status['memory']['status']}")
    logger.info(f"磁盘: {status['disk']['usage']}% ( {status['disk']['used']}/{status['disk']['total']}GB) - {status['disk']['status']}")
    logger.info(f"网络发送: {status['network']['bytes_sent']}MB")
    logger.info(f"网络接收: {status['network']['bytes_recv']}MB")
    logger.info(f"系统运行时间: {status['uptime']}")
    
    logger.info("\n=== 告警摘要 ===")
    alerts = monitor.get_alert_summary()
    logger.info(f"总告警数: {alerts['total_alerts']}")
    logger.info(f"严重告警: {alerts['critical_alerts']}")
    logger.info(f"警告告警: {alerts['warning_alerts']}")
    
    logger.info("\n=== 数据库统计 ===")
    db_stats = monitor.get_database_stats()
    logger.info(f"表数量: {db_stats['tables_count']}")
    logger.info(f"总记录数: {db_stats['total_records']}")
    
    logger.info("\n=== 健康检查摘要 ===")
    health = monitor.get_health_summary()
    logger.info(f"整体状态: {health['overall_status']}")
    logger.info(f"CPU状态: {health['cpu_status']}")
    logger.info(f"内存状态: {health['memory_status']}")
    logger.info(f"磁盘状态: {health['disk_status']}")
    
    monitor.collect_system_metrics()
    logger.info("\n已收集系统指标")
    
    monitor.close()