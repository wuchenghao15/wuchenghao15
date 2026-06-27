#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
IP安全管理系统 - 包含白名单、黑名单、异常检测和时间同步
MTSCOS AI Project v3.1
"""

import os
import sys
import json
import sqlite3
import logging
import ipaddress
import hashlib
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ip_security.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('ip_security')

class SecurityLevel(Enum):
    """安全级别"""
    SAFE = "safe"
    WARNING = "warning"
    DANGER = "danger"
    BLOCKED = "blocked"

class DatabaseManager:
    """数据库管理器"""
    
    def __init__(self, db_path: str = "ip_security.db"):
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """初始化数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ip_whitelist (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ip_address TEXT NOT NULL UNIQUE,
                description TEXT,
                added_by TEXT,
                added_at TEXT,
                last_used TEXT,
                use_count INTEGER DEFAULT 0,
                enabled INTEGER DEFAULT 1
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ip_blacklist (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ip_address TEXT NOT NULL UNIQUE,
                reason TEXT,
                blocked_by TEXT,
                blocked_at TEXT,
                expires_at TEXT,
                auto_block INTEGER DEFAULT 0,
                severity TEXT DEFAULT 'low'
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS login_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                username TEXT,
                ip_address TEXT NOT NULL,
                login_time TEXT,
                logout_time TEXT,
                status TEXT,
                user_agent TEXT,
                session_id TEXT
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS security_alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                alert_type TEXT NOT NULL,
                ip_address TEXT,
                user_id TEXT,
                severity TEXT,
                message TEXT,
                created_at TEXT,
                resolved INTEGER DEFAULT 0,
                resolved_at TEXT,
                resolved_by TEXT
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS time_sync (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                server_time TEXT,
                client_time TEXT,
                time_diff REAL,
                ip_address TEXT,
                synced_at TEXT
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ip_stats (
                ip_address TEXT PRIMARY KEY,
                first_seen TEXT,
                last_seen TEXT,
                total_logins INTEGER,
                failed_logins INTEGER,
                success_logins INTEGER,
                avg_session_duration REAL,
                last_country TEXT,
                last_city TEXT
            )
        """)
        
        conn.commit()
        conn.close()
        logger.info(f"IP安全数据库初始化完成: {self.db_path}")
    
    def execute(self, query: str, params: tuple = ()) -> sqlite3.Cursor:
        """执行SQL查询"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(query, params)
        conn.commit()
        result = cursor
        conn.close()
        return result

@dataclass
class IPInfo:
    """IP信息"""
    ip_address: str
    security_level: str
    is_whitelisted: bool
    is_blacklisted: bool
    total_logins: int
    failed_logins: int
    last_seen: str
    alerts: List[str]

class IPSecurityManager:
    """IP安全管理器"""
    
    def __init__(self, db_path: str = "ip_security.db"):
        self.db_path = db_path
        self.db = DatabaseManager(db_path)
        self.whitelist = self._load_whitelist()
        self.blacklist = self._load_blacklist()
        self.alert_thresholds = {
            'failed_logins': 5,
            'ip_change_frequency': 3,
            'session_duration_min': 10,
            'unusual_time_window': (2, 6)
        }
    
    def _load_whitelist(self) -> List[str]:
        """加载白名单"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT ip_address FROM ip_whitelist WHERE enabled = 1")
        whitelist = [row[0] for row in cursor.fetchall()]
        conn.close()
        return whitelist
    
    def _load_blacklist(self) -> List[str]:
        """加载黑名单"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT ip_address FROM ip_blacklist")
        blacklist = [row[0] for row in cursor.fetchall()]
        conn.close()
        return blacklist
    
    def add_to_whitelist(self, ip_address: str, description: str = "", 
                        added_by: str = "system") -> bool:
        """添加到白名单"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO ip_whitelist 
                (ip_address, description, added_by, added_at, enabled)
                VALUES (?, ?, ?, ?, 1)
            """, (ip_address, description, added_by, datetime.now().isoformat()))
            conn.commit()
            conn.close()
            
            self.whitelist.append(ip_address)
            self.log_security_event("whitelist_add", ip_address=ip_address, 
                                  message=f"IP {ip_address} 已添加到白名单")
            logger.info(f"IP已添加白名单: {ip_address}")
            return True
        except Exception as e:
            logger.error(f"添加白名单失败: {e}")
            return False
    
    def remove_from_whitelist(self, ip_address: str) -> bool:
        """从白名单移除"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE ip_whitelist SET enabled = 0 WHERE ip_address = ?
            """, (ip_address,))
            conn.commit()
            conn.close()
            
            if ip_address in self.whitelist:
                self.whitelist.remove(ip_address)
            
            self.log_security_event("whitelist_remove", ip_address=ip_address,
                                  message=f"IP {ip_address} 已从白名单移除")
            logger.info(f"IP已从白名单移除: {ip_address}")
            return True
        except Exception as e:
            logger.error(f"移除白名单失败: {e}")
            return False
    
    def add_to_blacklist(self, ip_address: str, reason: str, blocked_by: str = "system",
                        severity: str = "medium", expires_hours: int = None) -> bool:
        """添加到黑名单"""
        try:
            expires_at = None
            if expires_hours:
                expires_at = (datetime.now() + timedelta(hours=expires_hours)).isoformat()
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO ip_blacklist 
                (ip_address, reason, blocked_by, blocked_at, expires_at, severity)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (ip_address, reason, blocked_by, datetime.now().isoformat(), 
                  expires_at, severity))
            conn.commit()
            conn.close()
            
            self.blacklist.append(ip_address)
            self.log_security_event("blacklist_add", ip_address=ip_address,
                                  severity="high",
                                  message=f"IP {ip_address} 已加入黑名单: {reason}")
            logger.warning(f"⚠️ IP已加入黑名单: {ip_address} - {reason}")
            return True
        except Exception as e:
            logger.error(f"添加黑名单失败: {e}")
            return False
    
    def remove_from_blacklist(self, ip_address: str) -> bool:
        """从黑名单移除"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM ip_blacklist WHERE ip_address = ?", (ip_address,))
            conn.commit()
            conn.close()
            
            if ip_address in self.blacklist:
                self.blacklist.remove(ip_address)
            
            self.log_security_event("blacklist_remove", ip_address=ip_address,
                                  message=f"IP {ip_address} 已从黑名单移除")
            logger.info(f"IP已从黑名单移除: {ip_address}")
            return True
        except Exception as e:
            logger.error(f"移除黑名单失败: {e}")
            return False
    
    def is_ip_safe(self, ip_address: str) -> Tuple[bool, str]:
        """检查IP是否安全"""
        if ip_address in self.blacklist:
            return False, "IP已在黑名单中"
        
        if ip_address in self.whitelist:
            return True, "IP在白名单中"
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT total_logins, failed_logins FROM ip_stats WHERE ip_address = ?
        """, (ip_address,))
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            return True, "新IP，首次访问"
        
        total_logins, failed_logins = result
        
        if failed_logins >= self.alert_thresholds['failed_logins']:
            return False, f"登录失败次数过多: {failed_logins}"
        
        return True, "IP正常"
    
    def check_ip_anomaly(self, user_id: str, ip_address: str) -> Dict[str, Any]:
        """检查IP异常"""
        anomalies = []
        severity = "low"
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT COUNT(DISTINCT ip_address), MAX(login_time)
            FROM login_records WHERE user_id = ? AND login_time > datetime('now', '-24 hours')
        """, (user_id,))
        result = cursor.fetchone()
        ip_count, last_login = result or (0, None)
        
        if ip_count > self.alert_thresholds['ip_change_frequency']:
            anomalies.append(f"24小时内IP变化次数过多: {ip_count}")
            severity = "high"
        
        cursor.execute("""
            SELECT ip_address, login_time FROM login_records 
            WHERE user_id = ? ORDER BY login_time DESC LIMIT 5
        """, (user_id,))
        recent_logins = cursor.fetchall()
        
        if len(recent_logins) >= 2:
            last_ips = [login[0] for login in recent_logins[:2]]
            if last_ips[0] != last_ips[1]:
                anomalies.append(f"IP突然变化: {last_ips[1]} -> {last_ips[0]}")
                severity = max(severity, "medium")
        
        cursor.execute("""
            SELECT COUNT(*) FROM login_records 
            WHERE user_id = ? AND status = 'failed'
            AND login_time > datetime('now', '-1 hours')
        """, (user_id,))
        recent_failures = cursor.fetchone()[0]
        
        if recent_failures >= 3:
            anomalies.append(f"1小时内登录失败次数过多: {recent_failures}")
            severity = "high"
        
        cursor.execute("""
            SELECT total_logins, failed_logins FROM ip_stats WHERE ip_address = ?
        """, (ip_address,))
        stats = cursor.fetchone()
        conn.close()
        
        if stats:
            total_logins, failed_logins = stats
            if total_logins > 0 and failed_logins / total_logins > 0.5:
                anomalies.append(f"失败率过高: {failed_logins}/{total_logins}")
                severity = "high"
        
        return {
            'has_anomaly': len(anomalies) > 0,
            'anomalies': anomalies,
            'severity': severity,
            'ip_address': ip_address,
            'user_id': user_id,
            'timestamp': datetime.now().isoformat()
        }
    
    def log_login(self, user_id: str, username: str, ip_address: str,
                 status: str = "success", user_agent: str = "", session_id: str = "") -> bool:
        """记录登录"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO login_records 
                (user_id, username, ip_address, login_time, status, user_agent, session_id)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (user_id, username, ip_address, datetime.now().isoformat(), 
                  status, user_agent, session_id))
            
            cursor.execute("""
                INSERT OR REPLACE INTO ip_stats 
                (ip_address, last_seen, total_logins)
                VALUES (?, ?, COALESCE((SELECT total_logins FROM ip_stats WHERE ip_address = ?), 0) + 1)
            """, (ip_address, datetime.now().isoformat(), ip_address))
            
            if status == "success":
                cursor.execute("""
                    UPDATE ip_stats SET 
                        success_logins = COALESCE(success_logins, 0) + 1,
                        last_seen = ?
                    WHERE ip_address = ?
                """, (datetime.now().isoformat(), ip_address))
                
                if ip_address not in self.whitelist:
                    cursor.execute("""
                        UPDATE ip_whitelist SET last_used = ?, use_count = use_count + 1
                        WHERE ip_address = ?
                    """, (datetime.now().isoformat(), ip_address))
            else:
                cursor.execute("""
                    UPDATE ip_stats SET 
                        failed_logins = COALESCE(failed_logins, 0) + 1,
                        last_seen = ?
                    WHERE ip_address = ?
                """, (datetime.now().isoformat(), ip_address))
                
                cursor.execute("SELECT failed_logins FROM ip_stats WHERE ip_address = ?", (ip_address,))
                result = cursor.fetchone()
                if result and result[0] >= self.alert_thresholds['failed_logins']:
                    self.log_security_event("brute_force", ip_address=ip_address,
                                          severity="high",
                                          message=f"检测到暴力破解尝试: {result[0]}次失败")
            
            conn.commit()
            conn.close()
            
            return True
        except Exception as e:
            logger.error(f"记录登录失败: {e}")
            return False
    
    def get_ip_stats(self, ip_address: str) -> Optional[Tuple]:
        """获取IP统计"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT total_logins, failed_logins, success_logins FROM ip_stats WHERE ip_address = ?
        """, (ip_address,))
        result = cursor.fetchone()
        conn.close()
        return result
    
    def log_security_event(self, event_type: str, ip_address: str = None,
                          user_id: str = None, severity: str = "low",
                          message: str = "") -> bool:
        """记录安全事件"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO security_alerts 
                (alert_type, ip_address, user_id, severity, message, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (event_type, ip_address, user_id, severity, message,
                  datetime.now().isoformat()))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"记录安全事件失败: {e}")
            return False
    
    def get_active_users(self) -> List[Dict[str, Any]]:
        """获取当前活跃用户"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT lr.user_id, lr.username, lr.ip_address, lr.login_time, lr.session_id,
                   lr.user_agent, iw.enabled as is_whitelisted
            FROM login_records lr
            LEFT JOIN ip_whitelist iw ON lr.ip_address = iw.ip_address
            WHERE lr.login_time > datetime('now', '-7 days')
            AND lr.logout_time IS NULL
            AND lr.status = 'success'
            GROUP BY lr.session_id
            ORDER BY lr.login_time DESC
        """)
        
        columns = ['user_id', 'username', 'ip_address', 'login_time', 'session_id',
                  'user_agent', 'is_whitelisted']
        users = [dict(zip(columns, row)) for row in cursor.fetchall()]
        conn.close()
        
        for user in users:
            safe, msg = self.is_ip_safe(user['ip_address'])
            user['is_safe'] = safe
            user['safety_message'] = msg
            user['is_whitelisted'] = user['is_whitelisted'] == 1 if user['is_whitelisted'] is not None else False
        
        return users
    
    def check_user_ip_whitelist(self) -> List[Dict[str, Any]]:
        """检查用户IP白名单"""
        active_users = self.get_active_users()
        alerts = []
        
        for user in active_users:
            anomaly_result = self.check_ip_anomaly(user['user_id'], user['ip_address'])
            
            if anomaly_result['has_anomaly']:
                alert = {
                    'user_id': user['user_id'],
                    'username': user['username'],
                    'ip_address': user['ip_address'],
                    'anomalies': anomaly_result['anomalies'],
                    'severity': anomaly_result['severity'],
                    'login_time': user['login_time']
                }
                alerts.append(alert)
                
                self.log_security_event(
                    "user_anomaly",
                    ip_address=user['ip_address'],
                    user_id=user['user_id'],
                    severity=anomaly_result['severity'],
                    message=f"用户 {user['username']} 存在异常: {', '.join(anomaly_result['anomalies'])}"
                )
                
                if anomaly_result['severity'] == 'high':
                    self.add_to_blacklist(
                        user['ip_address'],
                        reason=f"严重安全异常: {', '.join(anomaly_result['anomalies'])}",
                        severity="high",
                        blocked_by="auto_system"
                    )
                    logger.warning(f"🚨 高危IP已自动加入黑名单: {user['ip_address']}")
        
        return alerts
    
    def sync_time(self, client_timestamp: float, ip_address: str = None) -> Dict[str, Any]:
        """同步时间"""
        server_time = datetime.now()
        time_diff = server_time.timestamp() - client_timestamp
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO time_sync (server_time, client_time, time_diff, ip_address, synced_at)
                VALUES (?, ?, ?, ?, ?)
            """, (server_time.isoformat(), datetime.fromtimestamp(client_timestamp).isoformat(),
                  time_diff, ip_address, server_time.isoformat()))
            conn.commit()
            conn.close()
            
            return {
                'success': True,
                'server_time': server_time.isoformat(),
                'server_timestamp': server_time.timestamp(),
                'client_time': datetime.fromtimestamp(client_timestamp).isoformat(),
                'time_diff': time_diff,
                'recommendation': 'adjust_clock' if abs(time_diff) > 5 else 'no_adjustment_needed'
            }
        except Exception as e:
            logger.error(f"时间同步失败: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_server_info(self) -> Dict[str, Any]:
        """获取服务器信息"""
        try:
            hostname = os.uname().nodename
        except:
            hostname = "unknown"
        
        return {
            'server_time': datetime.now().isoformat(),
            'server_timestamp': datetime.now().timestamp(),
            'timezone': 'Asia/Shanghai',
            'hostname': hostname,
            'platform': sys.platform,
            'python_version': sys.version.split()[0],
            'active_users_count': len(self.get_active_users()),
            'whitelist_count': len(self.whitelist),
            'blacklist_count': len(self.blacklist)
        }
    
    def get_ip_whitelist(self) -> List[Dict[str, Any]]:
        """获取白名单"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT ip_address, description, added_by, added_at, last_used, use_count, enabled
            FROM ip_whitelist ORDER BY added_at DESC
        """)
        columns = ['ip_address', 'description', 'added_by', 'added_at', 'last_used', 'use_count', 'enabled']
        whitelist = [dict(zip(columns, row)) for row in cursor.fetchall()]
        conn.close()
        return whitelist
    
    def get_ip_blacklist(self) -> List[Dict[str, Any]]:
        """获取黑名单"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT ip_address, reason, blocked_by, blocked_at, expires_at, severity
            FROM ip_blacklist ORDER BY blocked_at DESC
        """)
        columns = ['ip_address', 'reason', 'blocked_by', 'blocked_at', 'expires_at', 'severity']
        blacklist = [dict(zip(columns, row)) for row in cursor.fetchall()]
        conn.close()
        return blacklist
    
    def get_security_alerts(self, limit: int = 50) -> List[Dict[str, Any]]:
        """获取安全警报"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT alert_type, ip_address, user_id, severity, message, created_at, resolved
            FROM security_alerts
            WHERE resolved = 0
            ORDER BY created_at DESC
            LIMIT ?
        """, (limit,))
        columns = ['alert_type', 'ip_address', 'user_id', 'severity', 'message', 'created_at', 'resolved']
        alerts = [dict(zip(columns, row)) for row in cursor.fetchall()]
        conn.close()
        return alerts
    
    def resolve_alert(self, alert_id: int, resolved_by: str = "system") -> bool:
        """解决警报"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE security_alerts 
                SET resolved = 1, resolved_at = ?, resolved_by = ?
                WHERE id = ?
            """, (datetime.now().isoformat(), resolved_by, alert_id))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"解决警报失败: {e}")
            return False

def main():
    """测试主函数"""
    print("\n🛡️ IP安全管理系统测试")
    print("=" * 50)
    
    security = IPSecurityManager()
    
    print("\n📊 服务器信息:")
    server_info = security.get_server_info()
    for key, value in server_info.items():
        print(f"  {key}: {value}")
    
    print("\n✅ 白名单管理:")
    security.add_to_whitelist("192.168.1.100", "内部测试IP")
    whitelist = security.get_ip_whitelist()
    print(f"  当前白名单: {len(whitelist)} 个IP")
    
    print("\n🚫 黑名单管理:")
    security.add_to_blacklist("10.0.0.99", "检测到暴力破解", severity="high")
    blacklist = security.get_ip_blacklist()
    print(f"  当前黑名单: {len(blacklist)} 个IP")
    
    print("\n🔍 IP安全检查:")
    test_ips = ["192.168.1.100", "10.0.0.99", "8.8.8.8"]
    for ip in test_ips:
        safe, msg = security.is_ip_safe(ip)
        status = "✅ 安全" if safe else "❌ 危险"
        print(f"  {ip}: {status} - {msg}")
    
    print("\n🔄 时间同步测试:")
    client_time = time.time() - 3600
    sync_result = security.sync_time(client_time)
    print(f"  服务器时间: {sync_result.get('server_time')}")
    print(f"  时间差: {sync_result.get('time_diff'):.2f} 秒")
    print(f"  建议: {sync_result.get('recommendation')}")
    
    print("\n👥 当前活跃用户:")
    active_users = security.get_active_users()
    print(f"  活跃用户: {len(active_users)} 个")
    
    print("\n" + "=" * 50)
    print("✅ IP安全管理系统测试完成")

if __name__ == '__main__':
    main()
