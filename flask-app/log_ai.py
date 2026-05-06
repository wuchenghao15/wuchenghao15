#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日志AI系统 - 全自动记录日志并上报数据库
"""
import os
import sqlite3
import json
import traceback
from datetime import datetime
from typing import Dict, List, Any, Optional
from collections import defaultdict

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
DATABASE_PATH = '/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/flask-app/app.db'

class LogAI:
    """日志AI系统"""
    
    def __init__(self):
        self.db_path = DATABASE_PATH
        self.log_entries = []
        self.log_buffer = []
        self.buffer_size = 10
        self.log_levels = {
            'DEBUG': 0,
            'INFO': 1,
            'WARNING': 2,
            'ERROR': 3,
            'CRITICAL': 4
        }
    
    def log(self, level: str, category: str, message: str, details: Optional[Dict] = None, source: str = 'system'):
        """记录日志"""
        entry = {
            'level': level,
            'category': category,
            'message': message,
            'details': details or {},
            'source': source,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        self.log_entries.append(entry)
        self.log_buffer.append(entry)
        
        if len(self.log_buffer) >= self.buffer_size:
            self.flush_buffer()
        
        self._print_log(entry)
    
    def _print_log(self, entry: Dict):
        """打印日志"""
        level_symbols = {
            'DEBUG': '🔍',
            'INFO': 'ℹ️',
            'WARNING': '⚠️',
            'ERROR': '❌',
            'CRITICAL': '🚨'
        }
        
        symbol = level_symbols.get(entry['level'], '📝')
        print(f"{symbol} [{entry['timestamp']}] [{entry['level']}] [{entry['category']}] {entry['message']}")
    
    def debug(self, category: str, message: str, details: Optional[Dict] = None, source: str = 'system'):
        """记录调试日志"""
        self.log('DEBUG', category, message, details, source)
    
    def info(self, category: str, message: str, details: Optional[Dict] = None, source: str = 'system'):
        """记录信息日志"""
        self.log('INFO', category, message, details, source)
    
    def warning(self, category: str, message: str, details: Optional[Dict] = None, source: str = 'system'):
        """记录警告日志"""
        self.log('WARNING', category, message, details, source)
    
    def error(self, category: str, message: str, details: Optional[Dict] = None, source: str = 'system'):
        """记录错误日志"""
        self.log('ERROR', category, message, details, source)
    
    def critical(self, category: str, message: str, details: Optional[Dict] = None, source: str = 'system'):
        """记录严重错误日志"""
        self.log('CRITICAL', category, message, details, source)
    
    def log_exception(self, category: str, exception: Exception, details: Optional[Dict] = None, source: str = 'system'):
        """记录异常日志"""
        error_details = details or {}
        error_details.update({
            'exception_type': type(exception).__name__,
            'exception_message': str(exception),
            'traceback': traceback.format_exc()
        })
        
        self.log('ERROR', category, f"异常: {str(exception)}", error_details, source)
    
    def flush_buffer(self):
        """刷新缓冲区到数据库"""
        if not self.log_buffer:
            return
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS system_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                level TEXT,
                category TEXT,
                message TEXT,
                details TEXT,
                source TEXT,
                timestamp TEXT,
                session_id TEXT
            )
        ''')
        
        session_id = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        for entry in self.log_buffer:
            cursor.execute('''
                INSERT INTO system_logs (level, category, message, details, source, timestamp, session_id)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                entry['level'],
                entry['category'],
                entry['message'],
                json.dumps(entry['details'], ensure_ascii=False),
                entry['source'],
                entry['timestamp'],
                session_id
            ))
        
        conn.commit()
        conn.close()
        
        print(f"📤 已上传 {len(self.log_buffer)} 条日志到数据库")
        self.log_buffer = []
    
    def get_logs(self, level: Optional[str] = None, category: Optional[str] = None, 
                 limit: int = 100) -> List[Dict]:
        """获取日志"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        query = 'SELECT * FROM system_logs WHERE 1=1'
        params = []
        
        if level:
            query += ' AND level = ?'
            params.append(level)
        
        if category:
            query += ' AND category = ?'
            params.append(category)
        
        query += ' ORDER BY id DESC LIMIT ?'
        params.append(limit)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        logs = []
        for row in rows:
            try:
                details = json.loads(row['details']) if row['details'] else {}
            except:
                details = {'raw': row['details']}
            
            logs.append({
                'id': row['id'],
                'level': row['level'],
                'category': row['category'],
                'message': row['message'],
                'details': details,
                'source': row['source'],
                'timestamp': row['timestamp'],
                'session_id': row['session_id']
            })
        
        return logs
    
    def get_log_stats(self) -> Dict:
        """获取日志统计"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM system_logs')
        total = cursor.fetchone()[0]
        
        stats = {'total': total, 'by_level': {}, 'by_category': {}}
        
        for level in self.log_levels.keys():
            cursor.execute('SELECT COUNT(*) FROM system_logs WHERE level = ?', (level,))
            count = cursor.fetchone()[0]
            if count > 0:
                stats['by_level'][level] = count
        
        cursor.execute('SELECT category, COUNT(*) as count FROM system_logs GROUP BY category')
        for row in cursor.fetchall():
            stats['by_category'][row[0]] = row[1]
        
        conn.close()
        return stats
    
    def clear_old_logs(self, days: int = 30):
        """清理旧日志"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            DELETE FROM system_logs 
            WHERE timestamp < datetime('now', '-' || ? || ' days')
        ''', (days,))
        
        deleted = cursor.rowcount
        conn.commit()
        conn.close()
        
        self.info('日志管理', f'已清理 {deleted} 条 {days} 天前的旧日志')
        return deleted
    
    def export_logs(self, filepath: str, level: Optional[str] = None):
        """导出日志到文件"""
        logs = self.get_logs(level=level, limit=10000)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("日志导出报告\n")
            f.write(f"导出时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"日志总数: {len(logs)}\n")
            f.write("=" * 80 + "\n\n")
            
            for log in logs:
                f.write(f"[{log['timestamp']}] [{log['level']}] [{log['category']}]\n")
                f.write(f"  消息: {log['message']}\n")
                if log['details']:
                    f.write(f"  详情: {json.dumps(log['details'], ensure_ascii=False, indent=2)}\n")
                f.write("\n")
        
        self.info('日志导出', f'已导出 {len(logs)} 条日志到 {filepath}')
        return filepath

class LogReporter:
    """日志上报器 - 将测试异常和修复结果上报到数据库"""
    
    def __init__(self):
        self.db_path = DATABASE_PATH
        self.logger = LogAI()
    
    def report_test_anomaly(self, test_name: str, anomaly_type: str, description: str,
                           severity: str = 'medium', details: Optional[Dict] = None):
        """上报测试异常"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS test_anomalies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                test_name TEXT,
                anomaly_type TEXT,
                description TEXT,
                severity TEXT,
                details TEXT,
                status TEXT DEFAULT 'reported',
                reported_at TEXT,
                resolved_at TEXT,
                resolution TEXT
            )
        ''')
        
        reported_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        cursor.execute('''
            INSERT INTO test_anomalies 
            (test_name, anomaly_type, description, severity, details, status, reported_at)
            VALUES (?, ?, ?, ?, ?, 'reported', ?)
        ''', (
            test_name,
            anomaly_type,
            description,
            severity,
            json.dumps(details or {}, ensure_ascii=False),
            reported_at
        ))
        
        anomaly_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        self.logger.error('测试异常', f'{test_name} - {anomaly_type}: {description}', {
            'anomaly_id': anomaly_id,
            'severity': severity
        })
        
        return anomaly_id
    
    def report_fix_result(self, anomaly_id: int, fix_type: str, fix_description: str,
                          fix_result: str, files_modified: List[str] = None):
        """上报修复结果"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS fix_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                anomaly_id INTEGER,
                fix_type TEXT,
                fix_description TEXT,
                fix_result TEXT,
                files_modified TEXT,
                fixed_at TEXT,
                FOREIGN KEY (anomaly_id) REFERENCES test_anomalies(id)
            )
        ''')
        
        fixed_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        cursor.execute('''
            UPDATE test_anomalies 
            SET status = 'resolved', resolved_at = ?, resolution = ?
            WHERE id = ?
        ''', (fixed_at, fix_description, anomaly_id))
        
        cursor.execute('''
            INSERT INTO fix_results 
            (anomaly_id, fix_type, fix_description, fix_result, files_modified, fixed_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            anomaly_id,
            fix_type,
            fix_description,
            fix_result,
            json.dumps(files_modified or [], ensure_ascii=False),
            fixed_at
        ))
        
        fix_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        self.logger.info('修复结果', f'异常 #{anomaly_id} 已修复: {fix_description}', {
            'fix_id': fix_id,
            'result': fix_result
        })
        
        return fix_id
    
    def report_system_event(self, event_type: str, event_description: str,
                           component: str = 'system', details: Optional[Dict] = None):
        """上报系统事件"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS system_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT,
                description TEXT,
                component TEXT,
                details TEXT,
                occurred_at TEXT
            )
        ''')
        
        occurred_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        cursor.execute('''
            INSERT INTO system_events 
            (event_type, description, component, details, occurred_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            event_type,
            event_description,
            component,
            json.dumps(details or {}, ensure_ascii=False),
            occurred_at
        ))
        
        event_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        self.logger.info('系统事件', f'{component}: {event_description}', {
            'event_id': event_id,
            'event_type': event_type
        })
        
        return event_id
    
    def get_anomaly_report(self) -> Dict:
        """获取异常报告"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM test_anomalies WHERE status = "reported"')
        unresolved = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM test_anomalies WHERE status = "resolved"')
        resolved = cursor.fetchone()[0]
        
        cursor.execute('''
            SELECT * FROM test_anomalies 
            WHERE status = 'reported' 
            ORDER BY reported_at DESC LIMIT 10
        ''')
        recent = cursor.fetchall()
        
        conn.close()
        
        return {
            'unresolved_count': unresolved,
            'resolved_count': resolved,
            'recent_anomalies': [
                {
                    'id': row[0],
                    'test_name': row[1],
                    'anomaly_type': row[2],
                    'description': row[3],
                    'severity': row[4],
                    'reported_at': row[6]
                } for row in recent
            ]
        }

if __name__ == '__main__':
    logger = LogAI()
    
    logger.info('系统', '日志AI系统初始化完成')
    logger.debug('测试', '这是一条调试日志')
    logger.warning('安全', '检测到登录尝试失败')
    logger.error('数据库', '数据库连接超时')
    logger.critical('系统', '系统严重错误需要立即处理')
    
    logger.flush_buffer()
    
    stats = logger.get_log_stats()
    print("\n📊 日志统计:")
    print(json.dumps(stats, ensure_ascii=False, indent=2))
    
    reporter = LogReporter()
    reporter.report_system_event('系统启动', '测试AI系统启动', 'TestAI')
    
    anomaly_report = reporter.get_anomaly_report()
    print("\n📋 异常报告:")
    print(json.dumps(anomaly_report, ensure_ascii=False, indent=2))