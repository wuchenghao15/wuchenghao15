import logging
logger = logging.getLogger(__name__)

#!/usr/bin/env python3
"""
用户行为记录系统 - AI员工模块
记录用户行为，检测异常行为，生成警报并上报数据库
"""

import os
import re
import json
import time
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


def init_behavior_tables():
    """初始化用户行为表"""
    with get_db() as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS user_behavior (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                behavior_id TEXT UNIQUE NOT NULL,
                user_id TEXT,
                username TEXT,
                ip_address TEXT NOT NULL,
                action TEXT NOT NULL,
                action_type TEXT NOT NULL,
                target TEXT,
                details TEXT,
                timestamp INTEGER NOT NULL,
                session_id TEXT,
                user_agent TEXT,
                device_info TEXT,
                os_info TEXT,
                browser_info TEXT,
                location TEXT,
                is_ssl INTEGER DEFAULT 0,
                response_time REAL DEFAULT 0,
                status_code INTEGER DEFAULT 200
            )
        ''')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_behavior_user ON user_behavior(user_id)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_behavior_ip ON user_behavior(ip_address)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_behavior_time ON user_behavior(timestamp)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_behavior_action ON user_behavior(action_type)')
        
        conn.execute('''
            CREATE TABLE IF NOT EXISTS behavior_alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                alert_id TEXT UNIQUE NOT NULL,
                user_id TEXT,
                username TEXT,
                ip_address TEXT NOT NULL,
                alert_type TEXT NOT NULL,
                alert_level TEXT DEFAULT 'medium',
                alert_message TEXT NOT NULL,
                behavior_pattern TEXT,
                threshold_value INTEGER,
                actual_value INTEGER,
                details TEXT,
                timestamp INTEGER NOT NULL,
                acknowledged INTEGER DEFAULT 0,
                acknowledged_by TEXT,
                acknowledged_at INTEGER,
                resolved INTEGER DEFAULT 0,
                resolved_at INTEGER,
                resolution_action TEXT,
                auto_blocked INTEGER DEFAULT 0,
                block_expiry INTEGER
            )
        ''')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_alerts_user ON behavior_alerts(user_id)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_alerts_ip ON behavior_alerts(ip_address)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_alerts_type ON behavior_alerts(alert_type)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_alerts_level ON behavior_alerts(alert_level)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_alerts_acknowledged ON behavior_alerts(acknowledged)')
        
        conn.execute('''
            CREATE TABLE IF NOT EXISTS behavior_patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pattern_id TEXT UNIQUE NOT NULL,
                pattern_name TEXT NOT NULL,
                pattern_type TEXT NOT NULL,
                threshold INTEGER NOT NULL,
                time_window INTEGER DEFAULT 3600,
                alert_level TEXT DEFAULT 'medium',
                description TEXT,
                enabled INTEGER DEFAULT 1,
                created_at INTEGER NOT NULL,
                updated_at INTEGER NOT NULL
            )
        ''')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_patterns_type ON behavior_patterns(pattern_type)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_patterns_enabled ON behavior_patterns(enabled)')
        
        conn.execute('''
            CREATE TABLE IF NOT EXISTS blocked_ips (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ip_address TEXT UNIQUE NOT NULL,
                reason TEXT,
                block_level TEXT DEFAULT 'temporary',
                blocked_at INTEGER NOT NULL,
                block_expiry INTEGER,
                blocked_by TEXT DEFAULT 'system',
                is_active INTEGER DEFAULT 1,
                unblocked_at INTEGER,
                unblocked_by TEXT
            )
        ''')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_blocked_ip ON blocked_ips(ip_address)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_blocked_active ON blocked_ips(is_active)')
        
        conn.commit()
    print("[INFO] 用户行为记录表初始化完成")


def generate_behavior_id():
    """生成行为ID"""
    return f"beh_{int(time.time())}_{hash(str(time.time())) % 1000000:06d}"


def generate_alert_id():
    """生成警报ID"""
    return f"alt_{int(time.time())}_{hash(str(time.time())) % 1000000:06d}"


def get_default_patterns():
    """获取默认行为模式"""
    patterns = [
        {'pattern_id': 'p001', 'pattern_name': '登录失败次数过多', 'pattern_type': 'login_failures',
         'threshold': 5, 'time_window': 300, 'alert_level': 'high', 'description': '短时间内登录失败超过5次'},
        {'pattern_id': 'p002', 'pattern_name': '请求频率超限', 'pattern_type': 'rate_limit',
         'threshold': 1000, 'time_window': 3600, 'alert_level': 'medium', 'description': '1小时内请求超过1000次'},
        {'pattern_id': 'p003', 'pattern_name': '批量数据访问', 'pattern_type': 'batch_access',
         'threshold': 100, 'time_window': 60, 'alert_level': 'high', 'description': '1分钟内访问超过100条数据'},
        {'pattern_id': 'p004', 'pattern_name': '敏感操作频繁', 'pattern_type': 'sensitive_actions',
         'threshold': 10, 'time_window': 600, 'alert_level': 'high', 'description': '10分钟内敏感操作超过10次'},
        {'pattern_id': 'p005', 'pattern_name': '异地登录', 'pattern_type': 'geo_change',
         'threshold': 1, 'time_window': 3600, 'alert_level': 'high', 'description': '1小时内从不同地理位置登录'},
        {'pattern_id': 'p006', 'pattern_name': '异常时间访问', 'pattern_type': 'off_hours',
         'threshold': 1, 'time_window': 7200, 'alert_level': 'medium', 'description': '凌晨2-6点访问系统'},
        {'pattern_id': 'p007', 'pattern_name': 'API滥用', 'pattern_type': 'api_abuse',
         'threshold': 500, 'time_window': 3600, 'alert_level': 'medium', 'description': '1小时内API调用超过500次'},
        {'pattern_id': 'p008', 'pattern_name': '数据导出频繁', 'pattern_type': 'data_export',
         'threshold': 10, 'time_window': 3600, 'alert_level': 'high', 'description': '1小时内数据导出超过10次'},
    ]
    return patterns


def sync_patterns():
    """同步行为模式到数据库"""
    patterns = get_default_patterns()
    
    with get_db() as conn:
        for pattern in patterns:
            conn.execute('''
                INSERT OR REPLACE INTO behavior_patterns (
                    pattern_id, pattern_name, pattern_type, threshold,
                    time_window, alert_level, description, enabled,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                pattern['pattern_id'], pattern['pattern_name'], pattern['pattern_type'],
                pattern['threshold'], pattern['time_window'], pattern['alert_level'],
                pattern['description'], 1, int(time.time()), int(time.time())
            ))
        conn.commit()


def log_behavior(user_id=None, username=None, action=None, action_type=None, target=None, details=None):
    """记录用户行为"""
    if not request:
        return None
    
    behavior_id = generate_behavior_id()
    ip_address = request.remote_addr
    user_agent = request.user_agent.string
    session_id = request.cookies.get('session_id', '')
    
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
    
    is_ssl = 1 if request.is_secure else 0
    
    try:
        with get_db() as conn:
            conn.execute('''
                INSERT INTO user_behavior (
                    behavior_id, user_id, username, ip_address, action, action_type,
                    target, details, timestamp, session_id, user_agent, device_info,
                    os_info, browser_info, is_ssl
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                behavior_id, user_id, username, ip_address, action, action_type,
                target, json.dumps(details) if details else '', int(time.time()),
                session_id, user_agent, device_info, os_info, browser_info, is_ssl
            ))
            conn.commit()
    except Exception as e:
        print(f"[ERROR] 记录用户行为失败: {e}")
    
    detect_anomalies(user_id, username, ip_address, action_type, target)
    
    return behavior_id


def detect_anomalies(user_id, username, ip_address, action_type, target):
    """检测异常行为"""
    with get_db() as conn:
        patterns = conn.execute(
            'SELECT * FROM behavior_patterns WHERE enabled = 1'
        ).fetchall()
        
        for pattern in patterns:
            pattern_type = pattern['pattern_type']
            threshold = pattern['threshold']
            time_window = pattern['time_window']
            alert_level = pattern['alert_level']
            cutoff = int(time.time()) - time_window
            actual_value = 0
            
            if pattern_type == 'login_failures':
                actual_value = conn.execute('''
                    SELECT COUNT(*) FROM user_behavior 
                    WHERE ip_address = ? AND action_type = 'login' 
                    AND target = 'failure' AND timestamp > ?
                ''', (ip_address, cutoff)).fetchone()[0]
            
            elif pattern_type == 'rate_limit':
                actual_value = conn.execute('''
                    SELECT COUNT(*) FROM user_behavior 
                    WHERE ip_address = ? AND timestamp > ?
                ''', (ip_address, cutoff)).fetchone()[0]
            
            elif pattern_type == 'batch_access':
                actual_value = conn.execute('''
                    SELECT COUNT(*) FROM user_behavior 
                    WHERE ip_address = ? AND action_type = 'data_access' 
                    AND timestamp > ?
                ''', (ip_address, cutoff)).fetchone()[0]
            
            elif pattern_type == 'sensitive_actions':
                sensitive_actions = ['delete', 'update', 'export', 'admin']
                actual_value = conn.execute('''
                    SELECT COUNT(*) FROM user_behavior 
                    WHERE ip_address = ? AND action_type IN ('delete', 'update', 'export', 'admin') 
                    AND timestamp > ?
                ''', (ip_address, cutoff)).fetchone()[0]
            
            elif pattern_type == 'off_hours':
                hour = datetime.now().hour
                if 2 <= hour < 6:
                    actual_value = conn.execute('''
                        SELECT COUNT(*) FROM user_behavior 
                        WHERE ip_address = ? AND timestamp > ?
                    ''', (ip_address, cutoff)).fetchone()[0]
            
            elif pattern_type == 'api_abuse':
                actual_value = conn.execute('''
                    SELECT COUNT(*) FROM user_behavior 
                    WHERE ip_address = ? AND action_type = 'api_call' 
                    AND timestamp > ?
                ''', (ip_address, cutoff)).fetchone()[0]
            
            elif pattern_type == 'data_export':
                actual_value = conn.execute('''
                    SELECT COUNT(*) FROM user_behavior 
                    WHERE ip_address = ? AND action_type = 'export' 
                    AND timestamp > ?
                ''', (ip_address, cutoff)).fetchone()[0]
            
            if actual_value >= threshold:
                create_alert(
                    user_id=user_id,
                    username=username,
                    ip_address=ip_address,
                    alert_type=pattern_type,
                    alert_level=alert_level,
                    alert_message=pattern['description'],
                    behavior_pattern=pattern['pattern_name'],
                    threshold_value=threshold,
                    actual_value=actual_value
                )


def create_alert(user_id, username, ip_address, alert_type, alert_level,
                 alert_message, behavior_pattern, threshold_value, actual_value, details=None):
    """创建警报"""
    alert_id = generate_alert_id()
    
    try:
        with get_db() as conn:
            existing = conn.execute('''
                SELECT * FROM behavior_alerts 
                WHERE ip_address = ? AND alert_type = ? AND acknowledged = 0 
                AND resolved = 0
            ''', (ip_address, alert_type)).fetchone()
            
            if existing:
                return None
            
            conn.execute('''
                INSERT INTO behavior_alerts (
                    alert_id, user_id, username, ip_address, alert_type,
                    alert_level, alert_message, behavior_pattern,
                    threshold_value, actual_value, details, timestamp
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                alert_id, user_id, username, ip_address, alert_type,
                alert_level, alert_message, behavior_pattern,
                threshold_value, actual_value, json.dumps(details) if details else '',
                int(time.time())
            ))
            conn.commit()
        
        if alert_level == 'high':
            auto_block_ip(ip_address, reason=f'检测到{behavior_pattern}')
        
        return alert_id
    except Exception as e:
        print(f"[ERROR] 创建警报失败: {e}")
        return None


def auto_block_ip(ip_address, reason='自动封禁', block_level='temporary', duration=3600):
    """自动封禁IP"""
    try:
        with get_db() as conn:
            existing = conn.execute(
                'SELECT * FROM blocked_ips WHERE ip_address = ? AND is_active = 1',
                (ip_address,)
            ).fetchone()
            
            if existing:
                return False
            
            block_expiry = int(time.time()) + duration
            
            conn.execute('''
                INSERT INTO blocked_ips (
                    ip_address, reason, block_level, blocked_at,
                    block_expiry, blocked_by, is_active
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (ip_address, reason, block_level, int(time.time()),
                  block_expiry, 'auto_system', 1))
            conn.commit()
        
        print(f"[ALERT] IP {ip_address} 已自动封禁: {reason}")
        return True
    except Exception as e:
        print(f"[ERROR] 封禁IP失败: {e}")
        return False


def is_ip_blocked(ip_address):
    """检查IP是否被封禁"""
    try:
        with get_db() as conn:
            row = conn.execute('''
                SELECT * FROM blocked_ips 
                WHERE ip_address = ? AND is_active = 1 
                AND (block_expiry IS NULL OR block_expiry > ?)
            ''', (ip_address, int(time.time()))).fetchone()
            
            if row:
                return True, dict(row)
            return False, None
    except Exception as e:
        print(f"[ERROR] 检查IP封禁状态失败: {e}")
        return False, None


def unblock_ip(ip_address, unblocked_by='system'):
    """解封IP"""
    try:
        with get_db() as conn:
            conn.execute('''
                UPDATE blocked_ips 
                SET is_active = 0, unblocked_at = ?, unblocked_by = ?
                WHERE ip_address = ? AND is_active = 1
            ''', (int(time.time()), unblocked_by, ip_address))
            conn.commit()
            return conn.execute('SELECT changes()').fetchone()[0] > 0
    except Exception as e:
        print(f"[ERROR] 解封IP失败: {e}")
        return False


def acknowledge_alert(alert_id, acknowledged_by='system'):
    """确认警报"""
    try:
        with get_db() as conn:
            conn.execute('''
                UPDATE behavior_alerts 
                SET acknowledged = 1, acknowledged_by = ?, acknowledged_at = ?
                WHERE alert_id = ?
            ''', (acknowledged_by, int(time.time()), alert_id))
            conn.commit()
            return conn.execute('SELECT changes()').fetchone()[0] > 0
    except Exception as e:
        print(f"[ERROR] 确认警报失败: {e}")
        return False


def resolve_alert(alert_id, resolution_action=''):
    """解决警报"""
    try:
        with get_db() as conn:
            conn.execute('''
                UPDATE behavior_alerts 
                SET resolved = 1, resolved_at = ?, resolution_action = ?
                WHERE alert_id = ?
            ''', (int(time.time()), resolution_action, alert_id))
            conn.commit()
            return conn.execute('SELECT changes()').fetchone()[0] > 0
    except Exception as e:
        print(f"[ERROR] 解决警报失败: {e}")
        return False


def get_behavior_stats(hours=24):
    """获取行为统计"""
    cutoff = int(time.time()) - hours * 3600
    
    try:
        with get_db() as conn:
            total_actions = conn.execute(
                'SELECT COUNT(*) FROM user_behavior WHERE timestamp > ?', (cutoff,)
            ).fetchone()[0]
            
            unique_users = conn.execute(
                'SELECT COUNT(DISTINCT user_id) FROM user_behavior WHERE user_id IS NOT NULL AND timestamp > ?', (cutoff,)
            ).fetchone()[0]
            
            unique_ips = conn.execute(
                'SELECT COUNT(DISTINCT ip_address) FROM user_behavior WHERE timestamp > ?', (cutoff,)
            ).fetchone()[0]
            
            action_dist = conn.execute('''
                SELECT action_type, COUNT(*) as count 
                FROM user_behavior 
                WHERE timestamp > ? 
                GROUP BY action_type
            ''', (cutoff,)).fetchall()
            
            alert_count = conn.execute('''
                SELECT COUNT(*) FROM behavior_alerts 
                WHERE timestamp > ? AND acknowledged = 0
            ''', (cutoff,)).fetchone()[0]
            
            high_alerts = conn.execute('''
                SELECT COUNT(*) FROM behavior_alerts 
                WHERE timestamp > ? AND alert_level = 'high' AND acknowledged = 0
            ''', (cutoff,)).fetchone()[0]
            
            return {
                'total_actions': total_actions,
                'unique_users': unique_users,
                'unique_ips': unique_ips,
                'action_distribution': [dict(r) for r in action_dist],
                'pending_alerts': alert_count,
                'pending_high_alerts': high_alerts,
                'period': f'{hours}小时',
                'updated_at': int(time.time())
            }
    except Exception as e:
        print(f"[ERROR] 获取行为统计失败: {e}")
        return {}


def get_recent_behaviors(limit=50):
    """获取最近行为记录"""
    try:
        with get_db() as conn:
            rows = conn.execute('''
                SELECT * FROM user_behavior 
                ORDER BY timestamp DESC LIMIT ?
            ''', (limit,)).fetchall()
            return [dict(r) for r in rows]
    except Exception as e:
        print(f"[ERROR] 获取最近行为失败: {e}")
        return []


def get_pending_alerts(limit=50, alert_level=None):
    """获取未处理警报"""
    try:
        with get_db() as conn:
            if alert_level:
                rows = conn.execute('''
                    SELECT * FROM behavior_alerts 
                    WHERE acknowledged = 0 AND alert_level = ?
                    ORDER BY timestamp DESC LIMIT ?
                ''', (alert_level, limit)).fetchall()
            else:
                rows = conn.execute('''
                    SELECT * FROM behavior_alerts 
                    WHERE acknowledged = 0 
                    ORDER BY timestamp DESC LIMIT ?
                ''', (limit,)).fetchall()
            return [dict(r) for r in rows]
    except Exception as e:
        print(f"[ERROR] 获取未处理警报失败: {e}")
        return []


def get_blocked_ips(active_only=True):
    """获取被封禁IP列表"""
    try:
        with get_db() as conn:
            if active_only:
                rows = conn.execute('''
                    SELECT * FROM blocked_ips 
                    WHERE is_active = 1 AND (block_expiry IS NULL OR block_expiry > ?)
                    ORDER BY blocked_at DESC
                ''', (int(time.time()),)).fetchall()
            else:
                rows = conn.execute('SELECT * FROM blocked_ips ORDER BY blocked_at DESC').fetchall()
            return [dict(r) for r in rows]
    except Exception as e:
        print(f"[ERROR] 获取封禁IP列表失败: {e}")
        return []


def create_behavior_monitor_employee():
    """创建行为监控AI员工"""
    employee_id = 'emp_behavior_monitor_ai'
    
    try:
        with get_db() as conn:
            conn.execute('''
                INSERT OR IGNORE INTO ai_employees (
                    employee_id, name, title, description, category,
                    capabilities, efficiency, workload, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                employee_id,
                '行为监控员',
                '用户行为记录与异常警报专家',
                '负责记录用户行为，检测异常行为模式，生成警报并上报数据库，自动封禁恶意IP',
                'security',
                json.dumps([
                    '用户行为记录',
                    '登录失败检测',
                    '请求频率监控',
                    '批量数据访问检测',
                    '敏感操作监控',
                    '异地登录检测',
                    '异常时间访问检测',
                    'API滥用检测',
                    '数据导出监控',
                    '异常警报生成',
                    '自动IP封禁',
                    '警报确认与处理',
                    '行为统计分析',
                    '封禁IP管理'
                ]),
                97,
                0,
                int(time.time()),
                int(time.time())
            ))
            conn.commit()
        print("[INFO] 行为监控AI员工创建完成")
        return True
    except Exception as e:
        print(f"[ERROR] 创建行为监控AI员工失败: {e}")
        return False


def get_behavior_monitor_employee():
    """获取行为监控AI员工信息"""
    try:
        with get_db() as conn:
            row = conn.execute(
                'SELECT * FROM ai_employees WHERE employee_id = ?', ('emp_behavior_monitor_ai',)
            ).fetchone()
            return dict(row) if row else None
    except Exception as e:
        print(f"[ERROR] 获取行为监控AI员工失败: {e}")
        return None


def init_behavior_monitor():
    """初始化行为监控"""
    init_behavior_tables()
    sync_patterns()
    create_behavior_monitor_employee()


if __name__ == '__main__':
    init_behavior_monitor()
    logger.info("用户行为监控服务初始化完成")
