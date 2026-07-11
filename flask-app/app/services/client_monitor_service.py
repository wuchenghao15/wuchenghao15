import logging
logger = logging.getLogger(__name__)

#!/usr/bin/env python3
"""
客户端监控服务 - AI员工模块
监控远程客户端接入信息和异常记录
"""

import os
import time
import json
import sqlite3
from datetime import datetime
from contextlib import contextmanager
from flask import request, g

DATABASE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'mtscos.db')


@contextmanager
def get_db():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def init_monitor_tables():
    """初始化监控表"""
    with get_db() as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS client_access_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id TEXT NOT NULL,
                ip_address TEXT NOT NULL,
                user_agent TEXT,
                access_time INTEGER NOT NULL,
                endpoint TEXT NOT NULL,
                method TEXT NOT NULL,
                status_code INTEGER,
                response_time REAL,
                request_size INTEGER,
                response_size INTEGER,
                username TEXT,
                session_id TEXT,
                device_info TEXT,
                os_info TEXT,
                browser_info TEXT,
                network_info TEXT,
                location TEXT,
                is_ssl INTEGER DEFAULT 0
            )
        ''')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_client_access_ip ON client_access_logs(ip_address)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_client_access_time ON client_access_logs(access_time)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_client_access_client ON client_access_logs(client_id)')
        
        conn.execute('''
            CREATE TABLE IF NOT EXISTS client_anomalies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                anomaly_id TEXT UNIQUE NOT NULL,
                client_id TEXT,
                ip_address TEXT NOT NULL,
                anomaly_type TEXT NOT NULL,
                severity TEXT DEFAULT 'medium',
                message TEXT NOT NULL,
                details TEXT,
                timestamp INTEGER NOT NULL,
                resolved INTEGER DEFAULT 0,
                resolved_at INTEGER,
                resolver TEXT,
                action_taken TEXT
            )
        ''')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_client_anomalies_type ON client_anomalies(anomaly_type)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_client_anomalies_ip ON client_anomalies(ip_address)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_client_anomalies_resolved ON client_anomalies(resolved)')
        
        conn.execute('''
            CREATE TABLE IF NOT EXISTS client_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT UNIQUE NOT NULL,
                client_id TEXT NOT NULL,
                ip_address TEXT NOT NULL,
                username TEXT,
                login_time INTEGER NOT NULL,
                last_activity_time INTEGER,
                logout_time INTEGER,
                total_requests INTEGER DEFAULT 0,
                status TEXT DEFAULT 'active'
            )
        ''')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_client_sessions_id ON client_sessions(session_id)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_client_sessions_client ON client_sessions(client_id)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_client_sessions_status ON client_sessions(status)')
        
        conn.commit()
    print("[INFO] 客户端监控表初始化完成")


def generate_client_id():
    """生成客户端ID"""
    ip = request.remote_addr if request else 'unknown'
    ua = request.user_agent.string[:50] if request else 'unknown'
    return f"cli_{hash(f'{ip}_{ua}_{int(time.time())}') % 1000000:06d}"


def log_access(client_id=None, endpoint=None, method=None, status_code=200, 
               response_time=0, request_size=0, response_size=0):
    """记录客户端接入日志"""
    if not request:
        return
    
    ip_address = request.remote_addr
    user_agent = request.user_agent.string
    endpoint = endpoint or request.path
    method = method or request.method
    
    device_info = ''
    os_info = ''
    browser_info = ''
    
    if 'Mobile' in user_agent:
        device_info = 'mobile'
    elif 'Tablet' in user_agent:
        device_info = 'tablet'
    else:
        device_info = 'desktop'
    
    if 'Windows' in user_agent:
        os_info = 'Windows'
    elif 'Mac' in user_agent:
        os_info = 'macOS'
    elif 'Linux' in user_agent:
        os_info = 'Linux'
    elif 'Android' in user_agent:
        os_info = 'Android'
    elif 'iPhone' in user_agent or 'iPad' in user_agent:
        os_info = 'iOS'
    
    if 'Chrome' in user_agent:
        browser_info = 'Chrome'
    elif 'Safari' in user_agent:
        browser_info = 'Safari'
    elif 'Firefox' in user_agent:
        browser_info = 'Firefox'
    elif 'Edge' in user_agent:
        browser_info = 'Edge'
    
    username = request.cookies.get('username', '')
    session_id = request.cookies.get('session_id', '')
    
    is_ssl = 1 if request.is_secure else 0
    
    client_id = client_id or generate_client_id()
    
    try:
        with get_db() as conn:
            conn.execute('''
                INSERT INTO client_access_logs (
                    client_id, ip_address, user_agent, access_time, endpoint, method,
                    status_code, response_time, request_size, response_size,
                    username, session_id, device_info, os_info, browser_info, is_ssl
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                client_id, ip_address, user_agent, int(time.time()), endpoint, method,
                status_code, response_time, request_size, response_size,
                username, session_id, device_info, os_info, browser_info, is_ssl
            ))
            conn.commit()
    except Exception as e:
        print(f"[ERROR] 记录接入日志失败: {e}")
    
    return client_id


def log_anomaly(client_id, ip_address, anomaly_type, message, details=None, severity='medium'):
    """记录异常"""
    anomaly_id = f"ano_{int(time.time())}_{hash(f'{ip_address}_{anomaly_type}') % 10000}"
    
    try:
        with get_db() as conn:
            conn.execute('''
                INSERT INTO client_anomalies (
                    anomaly_id, client_id, ip_address, anomaly_type, severity,
                    message, details, timestamp
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                anomaly_id, client_id, ip_address, anomaly_type, severity,
                message, json.dumps(details) if details else '', int(time.time())
            ))
            conn.commit()
    except Exception as e:
        print(f"[ERROR] 记录异常失败: {e}")
    
    return anomaly_id


def resolve_anomaly(anomaly_id, resolver='system', action_taken=''):
    """标记异常已解决"""
    try:
        with get_db() as conn:
            conn.execute('''
                UPDATE client_anomalies 
                SET resolved = 1, resolved_at = ?, resolver = ?, action_taken = ?
                WHERE anomaly_id = ?
            ''', (int(time.time()), resolver, action_taken, anomaly_id))
            conn.commit()
            return conn.execute('SELECT changes()').fetchone()[0] > 0
    except Exception as e:
        print(f"[ERROR] 解决异常失败: {e}")
        return False


def get_access_stats(hours=24):
    """获取接入统计"""
    cutoff = int(time.time()) - hours * 3600
    
    try:
        with get_db() as conn:
            total_requests = conn.execute(
                'SELECT COUNT(*) FROM client_access_logs WHERE access_time > ?', (cutoff,)
            ).fetchone()[0]
            
            unique_clients = conn.execute(
                'SELECT COUNT(DISTINCT client_id) FROM client_access_logs WHERE access_time > ?', (cutoff,)
            ).fetchone()[0]
            
            unique_ips = conn.execute(
                'SELECT COUNT(DISTINCT ip_address) FROM client_access_logs WHERE access_time > ?', (cutoff,)
            ).fetchone()[0]
            
            status_dist = conn.execute('''
                SELECT status_code, COUNT(*) as count 
                FROM client_access_logs 
                WHERE access_time > ? 
                GROUP BY status_code
            ''', (cutoff,)).fetchall()
            
            top_endpoints = conn.execute('''
                SELECT endpoint, COUNT(*) as count 
                FROM client_access_logs 
                WHERE access_time > ? 
                GROUP BY endpoint 
                ORDER BY count DESC LIMIT 10
            ''', (cutoff,)).fetchall()
            
            return {
                'total_requests': total_requests,
                'unique_clients': unique_clients,
                'unique_ips': unique_ips,
                'status_distribution': [dict(r) for r in status_dist],
                'top_endpoints': [dict(r) for r in top_endpoints],
                'period': f'{hours}小时',
                'updated_at': int(time.time())
            }
    except Exception as e:
        print(f"[ERROR] 获取接入统计失败: {e}")
        return {}


def get_anomalies(limit=50, resolved=False):
    """获取异常列表"""
    try:
        with get_db() as conn:
            query = '''
                SELECT * FROM client_anomalies 
                WHERE resolved = ? 
                ORDER BY timestamp DESC LIMIT ?
            '''
            rows = conn.execute(query, (1 if resolved else 0, limit)).fetchall()
            return [dict(r) for r in rows]
    except Exception as e:
        print(f"[ERROR] 获取异常列表失败: {e}")
        return []


def get_recent_access(limit=50):
    """获取最近接入记录"""
    try:
        with get_db() as conn:
            rows = conn.execute('''
                SELECT * FROM client_access_logs 
                ORDER BY access_time DESC LIMIT ?
            ''', (limit,)).fetchall()
            return [dict(r) for r in rows]
    except Exception as e:
        print(f"[ERROR] 获取最近接入记录失败: {e}")
        return []


def check_brute_force(ip_address, max_attempts=10, time_window=3600):
    """检测暴力破解"""
    cutoff = int(time.time()) - time_window
    
    try:
        with get_db() as conn:
            attempts = conn.execute('''
                SELECT COUNT(*) FROM login_attempts 
                WHERE ip_address = ? AND success = 0 AND attempt_time > ?
            ''', (ip_address, datetime.fromtimestamp(cutoff))).fetchone()[0]
            
            if attempts >= max_attempts:
                log_anomaly(
                    client_id='',
                    ip_address=ip_address,
                    anomaly_type='brute_force_attack',
                    message=f'检测到暴力破解尝试，IP: {ip_address}，失败次数: {attempts}',
                    details={'ip': ip_address, 'attempts': attempts, 'max_attempts': max_attempts},
                    severity='high'
                )
                return True, attempts
            return False, attempts
    except Exception as e:
        print(f"[ERROR] 检测暴力破解失败: {e}")
        return False, 0


def check_rate_limit(ip_address, max_requests=1000, time_window=3600):
    """检测请求频率限制"""
    cutoff = int(time.time()) - time_window
    
    try:
        with get_db() as conn:
            requests = conn.execute('''
                SELECT COUNT(*) FROM client_access_logs 
                WHERE ip_address = ? AND access_time > ?
            ''', (ip_address, cutoff)).fetchone()[0]
            
            if requests >= max_requests:
                log_anomaly(
                    client_id='',
                    ip_address=ip_address,
                    anomaly_type='rate_limit_exceeded',
                    message=f'请求频率超限，IP: {ip_address}，请求次数: {requests}',
                    details={'ip': ip_address, 'requests': requests, 'max_requests': max_requests},
                    severity='medium'
                )
                return True, requests
            return False, requests
    except Exception as e:
        print(f"[ERROR] 检测请求频率失败: {e}")
        return False, 0


def check_session_hijacking(session_id):
    """检测会话劫持"""
    try:
        with get_db() as conn:
            ips = conn.execute('''
                SELECT DISTINCT ip_address FROM client_access_logs 
                WHERE session_id = ? AND session_id != ''
            ''', (session_id,)).fetchall()
            
            if len(ips) > 1:
                ip_list = [r['ip_address'] for r in ips]
                log_anomaly(
                    client_id='',
                    ip_address=ip_list[0],
                    anomaly_type='session_hijacking',
                    message=f'检测到会话在多个IP间切换，SessionID: {session_id}',
                    details={'session_id': session_id, 'ips': ip_list},
                    severity='high'
                )
                return True, ip_list
            return False, []
    except Exception as e:
        print(f"[ERROR] 检测会话劫持失败: {e}")
        return False, []


def create_monitor_employee():
    """创建监控AI员工"""
    employee_id = 'emp_monitor_client_access'
    
    try:
        with get_db() as conn:
            conn.execute('''
                INSERT OR IGNORE INTO ai_employees (
                    employee_id, name, title, description, category,
                    capabilities, efficiency, workload, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                employee_id,
                '客户端监控员',
                '远程客户端接入监控专家',
                '负责监控远程客户端接入信息，记录异常行为，实时检测安全威胁',
                'security',
                json.dumps([
                    '客户端接入日志记录',
                    '异常行为检测',
                    '暴力破解防护',
                    '请求频率监控',
                    '会话安全检测',
                    '实时告警通知',
                    '接入统计分析',
                    '异常报告生成'
                ]),
                100,
                0,
                int(time.time()),
                int(time.time())
            ))
            conn.commit()
        print("[INFO] 客户端监控AI员工创建完成")
        return True
    except Exception as e:
        print(f"[ERROR] 创建监控AI员工失败: {e}")
        return False


def get_monitor_employee():
    """获取监控AI员工信息"""
    try:
        with get_db() as conn:
            row = conn.execute(
                'SELECT * FROM ai_employees WHERE employee_id = ?', ('emp_monitor_client_access',)
            ).fetchone()
            return dict(row) if row else None
    except Exception as e:
        print(f"[ERROR] 获取监控AI员工失败: {e}")
        return None


if __name__ == '__main__':
    init_monitor_tables()
    create_monitor_employee()
    logger.info("客户端监控服务初始化完成")
