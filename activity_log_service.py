#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS活动日志服务
记录系统所有活动和用户操作
"""

import os
import sys
import json
import time
import threading
import sqlite3
from datetime import datetime
from typing import Dict, Any, Optional, List

logger = print

class ActivityLogService:
    """活动日志服务"""
    
    def __init__(self):
        self.log_queue = []
        self.is_running = False
        self.flush_thread = None
        self.lock = threading.Lock()
        
        self.config = self._load_config()
        self._init_database()
    
    def _load_config(self) -> Dict[str, Any]:
        """加载配置"""
        config_path = os.path.join(os.path.dirname(__file__), 'activity_log_config.json')
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        return {
            'enabled': True,
            'flush_interval': 5,
            'max_queue_size': 100,
            'retention_days': 90,
            'log_levels': ['debug', 'info', 'warning', 'error', 'critical'],
            'log_types': ['system', 'user', 'api', 'security', 'performance', 'maintenance']
        }
    
    def _save_config(self):
        """保存配置"""
        config_path = os.path.join(os.path.dirname(__file__), 'activity_log_config.json')
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)
    
    def _init_database(self):
        """初始化数据库"""
        try:
            conn = sqlite3.connect('activity_logs.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS activity_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    level TEXT NOT NULL,
                    type TEXT NOT NULL,
                    source TEXT,
                    user_id TEXT,
                    user_ip TEXT,
                    action TEXT,
                    details TEXT,
                    result TEXT DEFAULT 'success',
                    duration REAL,
                    error_message TEXT
                )
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_logs_timestamp ON activity_logs(timestamp)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_logs_type ON activity_logs(type)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_logs_user ON activity_logs(user_id)
            ''')
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[日志] 初始化数据库失败: {e}")
    
    def _flush_queue(self):
        """刷新日志队列"""
        while self.is_running:
            try:
                time.sleep(self.config['flush_interval'])
                
                with self.lock:
                    if self.log_queue:
                        logs = self.log_queue[:]
                        self.log_queue = []
                
                if logs:
                    self._save_logs(logs)
            except Exception as e:
                logger(f"[日志] 刷新队列错误: {e}")
    
    def _save_logs(self, logs: List[Dict[str, Any]]):
        """保存日志到数据库"""
        try:
            conn = sqlite3.connect('activity_logs.db')
            cursor = conn.cursor()
            
            for log in logs:
                cursor.execute('''
                    INSERT INTO activity_logs 
                    (timestamp, level, type, source, user_id, user_ip, action, details, result, duration, error_message)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    log.get('timestamp'),
                    log.get('level'),
                    log.get('type'),
                    log.get('source'),
                    log.get('user_id'),
                    log.get('user_ip'),
                    log.get('action'),
                    log.get('details'),
                    log.get('result', 'success'),
                    log.get('duration'),
                    log.get('error_message')
                ))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[日志] 保存日志失败: {e}")
    
    def _clean_old_logs(self):
        """清理过期日志"""
        retention_days = self.config['retention_days']
        cutoff_time = (datetime.now() - timedelta(days=retention_days)).isoformat()
        
        try:
            conn = sqlite3.connect('activity_logs.db')
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM activity_logs WHERE timestamp < ?', (cutoff_time,))
            deleted = cursor.rowcount
            
            conn.commit()
            conn.close()
            
            if deleted > 0:
                logger(f"[日志] 清理过期日志: {deleted}条")
        except Exception as e:
            logger(f"[日志] 清理日志失败: {e}")
    
    def log(self, level: str, log_type: str, action: str, details: str = None,
            source: str = None, user_id: str = None, user_ip: str = None,
            result: str = 'success', duration: float = None, 
            error_message: str = None):
        """记录日志"""
        if level not in self.config['log_levels']:
            level = 'info'
        if log_type not in self.config['log_types']:
            log_type = 'system'
        
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'level': level,
            'type': log_type,
            'source': source,
            'user_id': user_id,
            'user_ip': user_ip,
            'action': action,
            'details': details,
            'result': result,
            'duration': duration,
            'error_message': error_message
        }
        
        with self.lock:
            self.log_queue.append(log_entry)
            
            if len(self.log_queue) >= self.config['max_queue_size']:
                logs = self.log_queue[:]
                self.log_queue = []
        
        if len(self.log_queue) >= self.config['max_queue_size']:
            self._save_logs(logs)
    
    def debug(self, log_type: str, action: str, **kwargs):
        """记录调试日志"""
        self.log('debug', log_type, action, **kwargs)
    
    def info(self, log_type: str, action: str, **kwargs):
        """记录信息日志"""
        self.log('info', log_type, action, **kwargs)
    
    def warning(self, log_type: str, action: str, **kwargs):
        """记录警告日志"""
        self.log('warning', log_type, action, **kwargs)
    
    def error(self, log_type: str, action: str, **kwargs):
        """记录错误日志"""
        self.log('error', log_type, action, result='failed', **kwargs)
    
    def critical(self, log_type: str, action: str, **kwargs):
        """记录严重错误日志"""
        self.log('critical', log_type, action, result='failed', **kwargs)
    
    def log_user_action(self, user_id: str, action: str, details: str = None, 
                       user_ip: str = None, result: str = 'success'):
        """记录用户操作"""
        self.info('user', action, user_id=user_id, details=details, user_ip=user_ip, result=result)
    
    def log_api_call(self, endpoint: str, method: str, user_id: str = None, 
                     user_ip: str = None, duration: float = None, 
                     result: str = 'success', error_message: str = None):
        """记录API调用"""
        details = f"{method} {endpoint}"
        self.info('api', 'API调用', source=endpoint, user_id=user_id, 
                  user_ip=user_ip, details=details, duration=duration, 
                  result=result, error_message=error_message)
    
    def log_security_event(self, action: str, details: str = None, 
                          user_ip: str = None, result: str = 'success'):
        """记录安全事件"""
        self.info('security', action, details=details, user_ip=user_ip, result=result)
    
    def log_system_event(self, action: str, details: str = None, 
                        source: str = None, result: str = 'success'):
        """记录系统事件"""
        self.info('system', action, source=source, details=details, result=result)
    
    def query_logs(self, level: str = None, log_type: str = None, 
                   user_id: str = None, start_time: str = None, 
                   end_time: str = None, limit: int = 100) -> List[Dict[str, Any]]:
        """查询日志"""
        try:
            conn = sqlite3.connect('activity_logs.db')
            cursor = conn.cursor()
            
            query = 'SELECT * FROM activity_logs WHERE 1=1'
            params = []
            
            if level:
                query += ' AND level = ?'
                params.append(level)
            if log_type:
                query += ' AND type = ?'
                params.append(log_type)
            if user_id:
                query += ' AND user_id = ?'
                params.append(user_id)
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
            logs = []
            
            for row in cursor.fetchall():
                log = dict(zip(columns, row))
                log['details'] = json.loads(log['details']) if log['details'] else None
                logs.append(log)
            
            conn.close()
            return logs
        except Exception as e:
            logger(f"[日志] 查询日志失败: {e}")
            return []
    
    def get_log_summary(self) -> Dict[str, Any]:
        """获取日志摘要"""
        try:
            conn = sqlite3.connect('activity_logs.db')
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*) FROM activity_logs')
            total = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM activity_logs WHERE level = "error" OR level = "critical"')
            errors = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM activity_logs WHERE type = "user"')
            user_actions = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM activity_logs WHERE type = "api"')
            api_calls = cursor.fetchone()[0]
            
            cursor.execute('SELECT timestamp FROM activity_logs ORDER BY timestamp DESC LIMIT 1')
            last_log = cursor.fetchone()[0] if cursor.fetchone() else None
            
            conn.close()
            
            return {
                'total_logs': total,
                'error_logs': errors,
                'user_actions': user_actions,
                'api_calls': api_calls,
                'last_log_time': last_log
            }
        except Exception as e:
            logger(f"[日志] 获取摘要失败: {e}")
            return {}
    
    def start(self):
        """启动日志服务"""
        if self.is_running:
            return
        
        self.is_running = True
        self.flush_thread = threading.Thread(target=self._flush_queue, daemon=True)
        self.flush_thread.start()
        logger(f"[日志] 活动日志服务已启动")
    
    def stop(self):
        """停止日志服务"""
        self.is_running = False
        if self.flush_thread:
            self.flush_thread.join()
        
        with self.lock:
            if self.log_queue:
                self._save_logs(self.log_queue)
        
        self._clean_old_logs()
        logger(f"[日志] 活动日志服务已停止")
    
    def get_status(self) -> Dict[str, Any]:
        """获取服务状态"""
        return {
            'status': 'running' if self.is_running else 'stopped',
            'queue_size': len(self.log_queue),
            'flush_interval': self.config['flush_interval'],
            'max_queue_size': self.config['max_queue_size'],
            'retention_days': self.config['retention_days'],
            'log_summary': self.get_log_summary()
        }

activity_log_service = ActivityLogService()
