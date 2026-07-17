#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS错误监控服务
捕获和管理系统错误，提供错误报告和告警
"""

import os
import sys
import json
import time
import threading
import sqlite3
import traceback
from datetime import datetime
from typing import Dict, Any, Optional, List

logger = print

class ErrorMonitor:
    """错误监控服务"""
    
    def __init__(self):
        self.errors: List[Dict[str, Any]] = []
        self.is_running = False
        self.report_thread = None
        self.lock = threading.Lock()
        
        self.config = self._load_config()
        self._init_database()
    
    def _load_config(self) -> Dict[str, Any]:
        """加载配置"""
        config_path = os.path.join(os.path.dirname(__file__), 'error_monitor_config.json')
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        return {
            'enabled': True,
            'report_interval': 60,
            'max_errors_per_report': 100,
            'alert_threshold': {
                'error': 10,
                'critical': 1,
                'rate': 60
            },
            'auto_notify': True,
            'retention_days': 30
        }
    
    def _save_config(self):
        """保存配置"""
        config_path = os.path.join(os.path.dirname(__file__), 'error_monitor_config.json')
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)
    
    def _init_database(self):
        """初始化数据库"""
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS error_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    level TEXT NOT NULL,
                    source TEXT,
                    message TEXT,
                    traceback TEXT,
                    error_type TEXT,
                    user_id TEXT,
                    user_ip TEXT,
                    request_info TEXT,
                    resolved INTEGER DEFAULT 0,
                    resolved_at TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_error_timestamp ON error_logs(timestamp)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_error_level ON error_logs(level)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_error_resolved ON error_logs(resolved)
            ''')
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[监控] 初始化数据库失败: {e}")
    
    def _report_loop(self):
        """报告循环"""
        while self.is_running:
            try:
                time.sleep(self.config['report_interval'])
                
                if self.errors:
                    with self.lock:
                        errors_to_report = self.errors[:self.config['max_errors_per_report']]
                        self.errors = self.errors[self.config['max_errors_per_report']:]
                
                    self._save_errors(errors_to_report)
                    self._check_alerts(errors_to_report)
            except Exception as e:
                logger(f"[监控] 报告循环错误: {e}")
    
    def _save_errors(self, errors: List[Dict[str, Any]]):
        """保存错误到数据库"""
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            
            for error in errors:
                cursor.execute('''
                    INSERT INTO error_logs 
                    (timestamp, level, source, message, traceback, error_type, user_id, user_ip, request_info)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    error.get('timestamp'),
                    error.get('level'),
                    error.get('source'),
                    error.get('message'),
                    error.get('traceback'),
                    error.get('error_type'),
                    error.get('user_id'),
                    error.get('user_ip'),
                    error.get('request_info')
                ))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[监控] 保存错误失败: {e}")
    
    def _check_alerts(self, errors: List[Dict[str, Any]]):
        """检查告警条件"""
        critical_count = sum(1 for e in errors if e.get('level') == 'critical')
        error_count = sum(1 for e in errors if e.get('level') == 'error')
        
        if critical_count >= self.config['alert_threshold']['critical']:
            self._send_alert('CRITICAL', f"检测到 {critical_count} 个严重错误")
        
        if error_count >= self.config['alert_threshold']['error']:
            self._send_alert('ERROR', f"检测到 {error_count} 个错误")
    
    def _send_alert(self, level: str, message: str):
        """发送告警"""
        if self.config['auto_notify']:
            logger(f"[监控] 🚨 {level}: {message}")
    
    def capture_error(self, exception: Exception, source: str = None, 
                     user_id: str = None, user_ip: str = None, 
                     request_info: str = None, level: str = 'error'):
        """捕获错误"""
        error_info = {
            'timestamp': datetime.now().isoformat(),
            'level': level,
            'source': source,
            'message': str(exception),
            'traceback': traceback.format_exc(),
            'error_type': type(exception).__name__,
            'user_id': user_id,
            'user_ip': user_ip,
            'request_info': request_info
        }
        
        with self.lock:
            self.errors.append(error_info)
        
        logger(f"[监控] 捕获错误: {type(exception).__name__} - {exception}")
        
        if level == 'critical':
            self._send_alert('CRITICAL', f"{source}: {exception}")
    
    def log_error(self, message: str, source: str = None, error_type: str = None,
                  user_id: str = None, user_ip: str = None, level: str = 'error'):
        """记录错误"""
        error_info = {
            'timestamp': datetime.now().isoformat(),
            'level': level,
            'source': source,
            'message': message,
            'traceback': None,
            'error_type': error_type,
            'user_id': user_id,
            'user_ip': user_ip,
            'request_info': None
        }
        
        with self.lock:
            self.errors.append(error_info)
        
        logger(f"[监控] 记录错误: {level} - {message}")
    
    def log_critical(self, message: str, source: str = None, **kwargs):
        """记录严重错误"""
        self.log_error(message, source, level='critical', **kwargs)
    
    def log_warning(self, message: str, source: str = None, **kwargs):
        """记录警告"""
        self.log_error(message, source, level='warning', **kwargs)
    
    def resolve_error(self, error_id: int):
        """标记错误已解决"""
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE error_logs SET resolved = 1, resolved_at = ? WHERE id = ?
            ''', (datetime.now().isoformat(), error_id))
            
            conn.commit()
            conn.close()
            
            logger(f"[监控] 错误已标记为已解决: {error_id}")
        except Exception as e:
            logger(f"[监控] 标记错误失败: {e}")
    
    def resolve_all_errors(self):
        """标记所有错误已解决"""
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE error_logs SET resolved = 1, resolved_at = ? WHERE resolved = 0
            ''', (datetime.now().isoformat(),))
            
            conn.commit()
            conn.close()
            
            logger(f"[监控] 所有错误已标记为已解决")
        except Exception as e:
            logger(f"[监控] 标记所有错误失败: {e}")
    
    def query_errors(self, level: str = None, source: str = None, 
                     resolved: bool = None, start_time: str = None, 
                     end_time: str = None, limit: int = 100) -> List[Dict[str, Any]]:
        """查询错误"""
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            
            query = 'SELECT * FROM error_logs WHERE 1=1'
            params = []
            
            if level:
                query += ' AND level = ?'
                params.append(level)
            if source:
                query += ' AND source LIKE ?'
                params.append(f'%{source}%')
            if resolved is not None:
                query += ' AND resolved = ?'
                params.append(1 if resolved else 0)
            if start_time:
                query += ' AND timestamp >= ?'
                params.append(start_time)
            if end_time:
                query += ' AND timestamp <= ?'
                params.append(end_time)
            
            query += ' ORDER BY timestamp DESC LIMIT ?'
            params.append(limit)
            
            cursor.execute(query, params)
            
            columns = [desc[0] for desc in cursor.description]
            errors = []
            
            for row in cursor.fetchall():
                errors.append(dict(zip(columns, row)))
            
            conn.close()
            return errors
        except Exception as e:
            logger(f"[监控] 查询错误失败: {e}")
            return []
    
    def get_error_summary(self) -> Dict[str, Any]:
        """获取错误摘要"""
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*) FROM error_logs')
            total = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM error_logs WHERE resolved = 0')
            unresolved = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM error_logs WHERE level = "critical" AND resolved = 0')
            critical = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM error_logs WHERE level = "error" AND resolved = 0')
            errors = cursor.fetchone()[0]
            
            cursor.execute('SELECT timestamp FROM error_logs ORDER BY timestamp DESC LIMIT 1')
            last_error = cursor.fetchone()[0] if cursor.fetchone() else None
            
            conn.close()
            
            return {
                'total_errors': total,
                'unresolved_errors': unresolved,
                'critical_errors': critical,
                'error_errors': errors,
                'last_error_time': last_error
            }
        except Exception as e:
            logger(f"[监控] 获取摘要失败: {e}")
            return {}
    
    def start(self):
        """启动监控服务"""
        if self.is_running:
            return
        
        self.is_running = True
        self.report_thread = threading.Thread(target=self._report_loop, daemon=True)
        self.report_thread.start()
        logger(f"[监控] 错误监控服务已启动")
    
    def stop(self):
        """停止监控服务"""
        self.is_running = False
        if self.report_thread:
            self.report_thread.join()
        
        with self.lock:
            if self.errors:
                self._save_errors(self.errors)
        
        logger(f"[监控] 错误监控服务已停止")
    
    def get_status(self) -> Dict[str, Any]:
        """获取服务状态"""
        return {
            'status': 'running' if self.is_running else 'stopped',
            'pending_errors': len(self.errors),
            'report_interval': self.config['report_interval'],
            'alert_threshold': self.config['alert_threshold'],
            'auto_notify': self.config['auto_notify'],
            'error_summary': self.get_error_summary()
        }

error_monitor = ErrorMonitor()

def capture_exception(source: str = None):
    """装饰器：捕获函数异常"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                error_monitor.capture_error(e, source)
                raise
        return wrapper
    return decorator
