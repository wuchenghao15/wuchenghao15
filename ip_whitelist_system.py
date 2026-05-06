#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""IP白名单管理系统 - 常用登录设备和异常检测"""

import os
# import json removed - using database storage
import sqlite3
import logging
import hashlib
import secrets
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('ip_whitelist_system')

class IPWhitelistSystem:
    def __init__(self):
        self.db_path = 'app.db'
        self.init_whitelist_database()
    
    def init_whitelist_database(self):
        """初始化IP白名单数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        tables = [
            '''CREATE TABLE IF NOT EXISTS user_ip_whitelist (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                ip_address TEXT NOT NULL,
                ip_range TEXT,
                device_name TEXT,
                device_type TEXT,
                os TEXT,
                browser TEXT,
                is_trusted INTEGER DEFAULT 1,
                usage_count INTEGER DEFAULT 1,
                last_used TEXT,
                first_used TEXT,
                created_at TEXT
            )''',
            
            '''CREATE TABLE IF NOT EXISTS ip_blacklist (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ip_address TEXT UNIQUE NOT NULL,
                reason TEXT,
                blocked_at TEXT,
                expires_at TEXT,
                created_by TEXT
            )''',
            
            '''CREATE TABLE IF NOT EXISTS login_attempts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                username TEXT,
                ip_address TEXT,
                device_info TEXT,
                success INTEGER,
                is_vpn INTEGER DEFAULT 0,
                is_whitelisted INTEGER DEFAULT 0,
                risk_level TEXT DEFAULT 'low',
                timestamp TEXT,
                warning_message TEXT
            )''',
            
            '''CREATE TABLE IF NOT EXISTS ip_warnings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                ip_address TEXT,
                warning_type TEXT,
                warning_message TEXT,
                timestamp TEXT,
                acknowledged INTEGER DEFAULT 0
            )'''
        ]
        
        for table_sql in tables:
            cursor.execute(table_sql)
        
        conn.commit()
        conn.close()
        logger.info("IP白名单数据库初始化完成")
    
    def is_ip_vpn(self, ip_address: str) -> bool:
        """检测IP是否为VPN/代理"""
        vpn_indicators = [
            '10.', '172.16.', '192.168.',
            '.1.', '.2.', '.3.',
            '-', '_', 'vpn', 'proxy', 'tor'
        ]
        
        ip_lower = ip_address.lower()
        for indicator in vpn_indicators:
            if indicator in ip_lower:
                return True
        
        return False
    
    def add_ip_to_whitelist(self, user_id: str, ip_address: str, device_info: Dict):
        """添加IP到白名单"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, usage_count, first_used FROM user_ip_whitelist 
            WHERE user_id = ? AND ip_address = ?
        ''', (user_id, ip_address))
        
        existing = cursor.fetchone()
        
        if existing:
            cursor.execute('''
                UPDATE user_ip_whitelist 
                SET usage_count = usage_count + 1, 
                    last_used = ?,
                    device_name = COALESCE(NULLIF(?, ''), device_name),
                    device_type = COALESCE(NULLIF(?, ''), device_type),
                    os = COALESCE(NULLIF(?, ''), os),
                    browser = COALESCE(NULLIF(?, ''), browser)
                WHERE id = ?
            ''', (
                datetime.now().isoformat(),
                device_info.get('device_name', ''),
                device_info.get('device_type', ''),
                device_info.get('os', ''),
                device_info.get('browser', ''),
                existing[0]
            ))
        else:
            cursor.execute('''
                INSERT INTO user_ip_whitelist
                (user_id, ip_address, device_name, device_type, os, browser, 
                 last_used, first_used, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                user_id,
                ip_address,
                device_info.get('device_name', 'Unknown'),
                device_info.get('device_type', 'Desktop'),
                device_info.get('os', 'Unknown'),
                device_info.get('browser', 'Unknown'),
                datetime.now().isoformat(),
                datetime.now().isoformat(),
                datetime.now().isoformat()
            ))
        
        conn.commit()
        conn.close()
    
    def is_ip_whitelisted(self, user_id: str, ip_address: str) -> bool:
        """检查IP是否在白名单中"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT COUNT(*) FROM user_ip_whitelist 
            WHERE user_id = ? AND ip_address = ? AND is_trusted = 1
        ''', (user_id, ip_address))
        
        count = cursor.fetchone()[0]
        conn.close()
        
        return count > 0
    
    def get_user_whitelist(self, user_id: str) -> List:
        """获取用户白名单列表"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT ip_address, device_name, device_type, os, browser, 
                   usage_count, last_used, is_trusted 
            FROM user_ip_whitelist WHERE user_id = ? ORDER BY usage_count DESC
        ''', (user_id,))
        
        whitelist = []
        for row in cursor.fetchall():
            whitelist.append({
                'ip_address': row[0],
                'device_name': row[1],
                'device_type': row[2],
                'os': row[3],
                'browser': row[4],
                'usage_count': row[5],
                'last_used': row[6],
                'is_trusted': bool(row[7])
            })
        
        conn.close()
        return whitelist
    
    def remove_ip_from_whitelist(self, user_id: str, ip_address: str):
        """从白名单中移除IP"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE user_ip_whitelist SET is_trusted = 0 WHERE user_id = ? AND ip_address = ?
        ''', (user_id, ip_address))
        
        conn.commit()
        conn.close()
    
    def add_ip_to_blacklist(self, ip_address: str, reason: str, expires_hours: int = 24):
        """添加IP到黑名单"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        expires_at = (datetime.now() + timedelta(hours=expires_hours)).isoformat()
        
        cursor.execute('''
            INSERT OR REPLACE INTO ip_blacklist
            (ip_address, reason, blocked_at, expires_at, created_by)
            VALUES (?, ?, ?, ?, ?)
        ''', (ip_address, reason, datetime.now().isoformat(), expires_at, 'system'))
        
        conn.commit()
        conn.close()
    
    def is_ip_blacklisted(self, ip_address: str) -> bool:
        """检查IP是否在黑名单中"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT COUNT(*) FROM ip_blacklist 
            WHERE ip_address = ? AND expires_at > ?
        ''', (ip_address, datetime.now().isoformat()))
        
        count = cursor.fetchone()[0]
        conn.close()
        
        return count > 0
    
    def check_login_security(self, user_id: str, ip_address: str, device_info: Dict = None) -> Dict:
        """检查登录安全性"""
        result = {
            'is_allowed': True,
            'is_whitelisted': False,
            'is_vpn': False,
            'is_blacklisted': False,
            'risk_level': 'low',
            'warning_message': None,
            'action': 'allow'
        }
        
        # 检查黑名单
        if self.is_ip_blacklisted(ip_address):
            result['is_allowed'] = False
            result['is_blacklisted'] = True
            result['risk_level'] = 'critical'
            result['warning_message'] = '您的IP地址已被封禁'
            result['action'] = 'block'
            return result
        
        # 检查VPN
        is_vpn = self.is_ip_vpn(ip_address)
        result['is_vpn'] = is_vpn
        
        # 检查白名单
        is_whitelisted = self.is_ip_whitelisted(user_id, ip_address)
        result['is_whitelisted'] = is_whitelisted
        
        # 如果不在白名单中
        if not is_whitelisted:
            result['risk_level'] = 'medium'
            result['warning_message'] = '检测到异常登录IP地址'
            result['action'] = 'warn'
            
            if is_vpn:
                result['risk_level'] = 'high'
                result['warning_message'] = '检测到VPN登录，请确认是否为本人操作'
        
        return result
    
    def log_login_attempt(self, user_id: str, username: str, ip_address: str, 
                          device_info: Dict, success: bool, is_vpn: bool, 
                          is_whitelisted: bool, risk_level: str, warning_message: str = None):
        """记录登录尝试"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO login_attempts
            (user_id, username, ip_address, attempt_time, success, failure_reason)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            user_id,
            username,
            ip_address,
            datetime.now().isoformat(),
            1 if success else 0,
            warning_message if warning_message else ''
        ))
        
        conn.commit()
        conn.close()
    
    def create_warning(self, user_id: str, ip_address: str, warning_type: str, warning_message: str):
        """创建警告记录"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO ip_warnings
            (user_id, ip_address, warning_type, warning_message, timestamp)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, ip_address, warning_type, warning_message, datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
    
    def get_user_warnings(self, user_id: str) -> List:
        """获取用户警告记录"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT ip_address, warning_type, warning_message, timestamp, acknowledged 
            FROM ip_warnings WHERE user_id = ? ORDER BY timestamp DESC
        ''', (user_id,))
        
        warnings = []
        for row in cursor.fetchall():
            warnings.append({
                'ip_address': row[0],
                'warning_type': row[1],
                'warning_message': row[2],
                'timestamp': row[3],
                'acknowledged': bool(row[4])
            })
        
        conn.close()
        return warnings
    
    def acknowledge_warning(self, warning_id: int):
        """确认警告"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE ip_warnings SET acknowledged = 1 WHERE id = ?
        ''', (warning_id,))
        
        conn.commit()
        conn.close()
    
    def generate_security_report(self):
        """生成安全报告"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM user_ip_whitelist')
        whitelist_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM ip_blacklist WHERE expires_at > ?', (datetime.now().isoformat(),))
        blacklist_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM login_attempts')
        total_attempts = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM login_attempts WHERE failure_reason LIKE ? OR failure_reason LIKE ?', ('%VPN%', '%异常%'))
        suspicious_attempts = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM ip_warnings WHERE acknowledged = 0')
        unacknowledged_warnings = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(DISTINCT user_id) FROM user_ip_whitelist')
        users_with_whitelist = cursor.fetchone()[0]
        
        conn.close()
        
        print("\n" + "="*80)
        print("          IP白名单安全系统报告")
        print("="*80)
        
        print(f"\n白名单统计:")
        print(f"  白名单条目: {whitelist_count}")
        print(f"  有白名单用户: {users_with_whitelist}")
        
        print(f"\n黑名单统计:")
        print(f"  黑名单IP: {blacklist_count}")
        
        print(f"\n登录安全统计:")
        print(f"  登录总次数: {total_attempts}")
        print(f"  可疑登录: {suspicious_attempts}")
        print(f"  未确认警告: {unacknowledged_warnings}")
        
        print("\n安全功能:")
        print(f"  ✅ IP白名单管理")
        print(f"  ✅ IP黑名单管理")
        print(f"  ✅ VPN检测")
        print(f"  ✅ 异常IP警告")
        print(f"  ✅ 登录记录追踪")
        print(f"  ✅ 风险等级评估")
        
        print("\n" + "="*80)
        print("  IP白名单安全系统完成！")
        print("="*80)
    
    def run_security_demo(self):
        """运行安全演示"""
        print("="*80)
        print("          IP白名单安全系统")
        print("="*80)
        
        user_id = 'test_user_123'
        
        print("\n[1/3] 添加常用设备到白名单...")
        devices = [
            {'ip': '192.168.1.100', 'name': '家庭电脑', 'type': 'Desktop', 'os': 'Windows 11', 'browser': 'Chrome'},
            {'ip': '192.168.1.101', 'name': '办公室电脑', 'type': 'Desktop', 'os': 'macOS', 'browser': 'Safari'},
            {'ip': '10.0.0.5', 'name': '手机', 'type': 'Mobile', 'os': 'iOS', 'browser': 'Safari'}
        ]
        
        for device in devices:
            self.add_ip_to_whitelist(user_id, device['ip'], {
                'device_name': device['name'],
                'device_type': device['type'],
                'os': device['os'],
                'browser': device['browser']
            })
            print(f"  ✓ 添加设备: {device['name']} ({device['ip']})")
        
        print("\n[2/3] 测试登录安全检查...")
        
        test_cases = [
            ('192.168.1.100', '家庭网络', False),
            ('10.0.0.5', '手机网络', False),
            ('203.0.113.50', '陌生IP', False),
            ('vpn.example.com', 'VPN连接', True)
        ]
        
        for ip, desc, is_vpn in test_cases:
            result = self.check_login_security(user_id, ip)
            status = '✅ 允许' if result['action'] == 'allow' else '⚠️ 警告' if result['action'] == 'warn' else '❌ 阻止'
            print(f"  {status} - {desc} ({ip})")
            if result['warning_message']:
                print(f"     提示: {result['warning_message']}")
            
            # 记录登录尝试
            self.log_login_attempt(user_id, 'testuser', ip, {}, True, result['is_vpn'], result['is_whitelisted'], result['risk_level'], result['warning_message'])
            
            # 创建警告（如果有风险）
            if result['risk_level'] in ['medium', 'high']:
                self.create_warning(user_id, ip, 'ip_alert', result['warning_message'])
        
        print("\n[3/3] 查看用户白名单和警告...")
        whitelist = self.get_user_whitelist(user_id)
        print(f"\n  用户白名单 ({len(whitelist)} 条):")
        for item in whitelist:
            print(f"    • {item['ip_address']} - {item['device_name']} ({item['usage_count']}次)")
        
        warnings = self.get_user_warnings(user_id)
        print(f"\n  安全警告 ({len(warnings)} 条):")
        for warning in warnings:
            print(f"    ⚠️ {warning['warning_message']}")
        
        self.generate_security_report()

def main():
    system = IPWhitelistSystem()
    system.run_security_demo()

if __name__ == "__main__":
    main()