#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""增强版超时锁定机制"""

import os
# import json removed - using database storage
import sqlite3
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any

logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('timeout_lock_system')

class EnhancedTimeoutLockSystem:
    def __init__(self):
        self.db_path = 'app.db'
        self.login_attempts = {}
        self.locked_accounts = {}
        self.locked_ips = {}
        self.init_lock_database()
    
    def init_lock_database(self):
        """初始化锁定数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        tables = [
            '''CREATE TABLE IF NOT EXISTS login_attempts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                username TEXT,
                ip_address TEXT,
                attempt_time TEXT,
                success INTEGER,
                failure_reason TEXT
            )''',
            
            '''CREATE TABLE IF NOT EXISTS account_locks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                username TEXT,
                lock_type TEXT,
                lock_reason TEXT,
                lock_time TEXT,
                unlock_time TEXT,
                attempts_before_lock INTEGER,
                lock_duration_seconds INTEGER,
                status TEXT DEFAULT 'locked'
            )''',
            
            '''CREATE TABLE IF NOT EXISTS ip_locks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ip_address TEXT,
                lock_type TEXT,
                lock_reason TEXT,
                lock_time TEXT,
                unlock_time TEXT,
                attempts_before_lock INTEGER,
                lock_duration_seconds INTEGER,
                status TEXT DEFAULT 'locked'
            )''',
            
            '''CREATE TABLE IF NOT EXISTS session_timeouts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                user_id TEXT,
                login_time TEXT,
                last_activity TEXT,
                timeout_duration_seconds INTEGER,
                status TEXT DEFAULT 'active'
            )''',
            
            '''CREATE TABLE IF NOT EXISTS lock_policies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                policy_id TEXT UNIQUE NOT NULL,
                policy_name TEXT,
                policy_type TEXT,
                max_attempts INTEGER,
                lock_duration_seconds INTEGER,
                cooldown_period_seconds INTEGER,
                escalate_lock BOOLEAN,
                enabled INTEGER DEFAULT 1,
                created_at TEXT
            )'''
        ]
        
        for table_sql in tables:
            cursor.execute(table_sql)
        
        conn.commit()
        conn.close()
        logger.info("超时锁定数据库表初始化完成")
    
    def load_lock_policies(self):
        """加载锁定策略"""
        policies = [
            {
                'policy_id': 'policy_login_basic',
                'policy_name': '基础登录锁定',
                'policy_type': 'login',
                'max_attempts': 5,
                'lock_duration_seconds': 300,
                'cooldown_period_seconds': 3600,
                'escalate_lock': False
            },
            {
                'policy_id': 'policy_login_escalating',
                'policy_name': '递增锁定策略',
                'policy_type': 'login',
                'max_attempts': 5,
                'lock_duration_seconds': 600,
                'cooldown_period_seconds': 7200,
                'escalate_lock': True
            },
            {
                'policy_id': 'policy_ip_rate_limit',
                'policy_name': 'IP速率限制',
                'policy_type': 'ip',
                'max_attempts': 100,
                'lock_duration_seconds': 3600,
                'cooldown_period_seconds': 86400,
                'escalate_lock': True
            },
            {
                'policy_id': 'policy_session_timeout',
                'policy_name': '会话超时策略',
                'policy_type': 'session',
                'max_attempts': 0,
                'lock_duration_seconds': 3600,
                'cooldown_period_seconds': 0,
                'escalate_lock': False
            },
            {
                'policy_id': 'policy_admin_protection',
                'policy_name': '管理员账户保护',
                'policy_type': 'login',
                'max_attempts': 3,
                'lock_duration_seconds': 900,
                'cooldown_period_seconds': 3600,
                'escalate_lock': True
            },
            {
                'policy_id': 'policy_suspicious_activity',
                'policy_name': '可疑活动检测',
                'policy_type': 'ip',
                'max_attempts': 20,
                'lock_duration_seconds': 7200,
                'cooldown_period_seconds': 86400,
                'escalate_lock': True
            }
        ]
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for policy in policies:
            cursor.execute('''
                INSERT OR REPLACE INTO lock_policies
                (policy_id, policy_name, policy_type, max_attempts, 
                 lock_duration_seconds, cooldown_period_seconds, escalate_lock, enabled, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                policy['policy_id'],
                policy['policy_name'],
                policy['policy_type'],
                policy['max_attempts'],
                policy['lock_duration_seconds'],
                policy['cooldown_period_seconds'],
                policy['escalate_lock'],
                1,
                datetime.now().isoformat()
            ))
        
        conn.commit()
        conn.close()
        logger.info("锁定策略已加载")
    
    def record_login_attempt(self, username, ip_address, success, failure_reason=''):
        """记录登录尝试"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO login_attempts
            (user_id, username, ip_address, attempt_time, success, failure_reason)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            '',
            username,
            ip_address,
            datetime.now().isoformat(),
            1 if success else 0,
            failure_reason
        ))
        
        conn.commit()
        conn.close()
    
    def get_login_attempts_count(self, username, ip_address, window_seconds=3600):
        """获取登录尝试次数"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        window_start = (datetime.now() - timedelta(seconds=window_seconds)).isoformat()
        
        cursor.execute('''
            SELECT COUNT(*) FROM login_attempts 
            WHERE username = ? AND ip_address = ? AND attempt_time >= ? AND success = 0
        ''', (username, ip_address, window_start))
        
        count = cursor.fetchone()[0]
        conn.close()
        return count
    
    def check_account_lock(self, username):
        """检查账户是否被锁定"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT unlock_time, status FROM account_locks 
            WHERE username = ? AND status = 'locked'
            ORDER BY lock_time DESC LIMIT 1
        ''', (username,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            unlock_time = datetime.fromisoformat(result[0])
            if datetime.now() < unlock_time:
                remaining = (unlock_time - datetime.now()).total_seconds()
                return {'locked': True, 'remaining_seconds': remaining}
            else:
                self.unlock_account(username)
        
        return {'locked': False}
    
    def check_ip_lock(self, ip_address):
        """检查IP是否被锁定"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT unlock_time, status FROM ip_locks 
            WHERE ip_address = ? AND status = 'locked'
            ORDER BY lock_time DESC LIMIT 1
        ''', (ip_address,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            unlock_time = datetime.fromisoformat(result[0])
            if datetime.now() < unlock_time:
                remaining = (unlock_time - datetime.now()).total_seconds()
                return {'locked': True, 'remaining_seconds': remaining}
            else:
                self.unlock_ip(ip_address)
        
        return {'locked': False}
    
    def lock_account(self, username, attempts_before_lock, lock_duration_seconds, reason='多次登录失败'):
        """锁定账户"""
        unlock_time = (datetime.now() + timedelta(seconds=lock_duration_seconds)).isoformat()
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO account_locks
            (user_id, username, lock_type, lock_reason, lock_time, 
             unlock_time, attempts_before_lock, lock_duration_seconds, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            '',
            username,
            'login_failure',
            reason,
            datetime.now().isoformat(),
            unlock_time,
            attempts_before_lock,
            lock_duration_seconds,
            'locked'
        ))
        
        conn.commit()
        conn.close()
        
        print(f"  ✓ 账户 {username} 已锁定，锁定时长: {lock_duration_seconds/60:.1f}分钟")
    
    def lock_ip(self, ip_address, attempts_before_lock, lock_duration_seconds, reason='异常访问'):
        """锁定IP"""
        unlock_time = (datetime.now() + timedelta(seconds=lock_duration_seconds)).isoformat()
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO ip_locks
            (ip_address, lock_type, lock_reason, lock_time, 
             unlock_time, attempts_before_lock, lock_duration_seconds, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            ip_address,
            'rate_limit',
            reason,
            datetime.now().isoformat(),
            unlock_time,
            attempts_before_lock,
            lock_duration_seconds,
            'locked'
        ))
        
        conn.commit()
        conn.close()
        
        print(f"  ✓ IP {ip_address} 已锁定，锁定时长: {lock_duration_seconds/60:.1f}分钟")
    
    def unlock_account(self, username):
        """解锁账户"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE account_locks SET status = 'unlocked' WHERE username = ? AND status = 'locked'
        ''', (username,))
        
        conn.commit()
        conn.close()
    
    def unlock_ip(self, ip_address):
        """解锁IP"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE ip_locks SET status = 'unlocked' WHERE ip_address = ? AND status = 'locked'
        ''', (ip_address,))
        
        conn.commit()
        conn.close()
    
    def handle_login_attempt(self, username, ip_address, is_admin=False):
        """处理登录尝试"""
        # 检查IP锁定
        ip_check = self.check_ip_lock(ip_address)
        if ip_check['locked']:
            print(f"  ✗ IP {ip_address} 已锁定，剩余时间: {ip_check['remaining_seconds']/60:.1f}分钟")
            return {'success': False, 'reason': 'ip_locked', 'remaining': ip_check['remaining_seconds']}
        
        # 检查账户锁定
        account_check = self.check_account_lock(username)
        if account_check['locked']:
            print(f"  ✗ 账户 {username} 已锁定，剩余时间: {account_check['remaining_seconds']/60:.1f}分钟")
            return {'success': False, 'reason': 'account_locked', 'remaining': account_check['remaining_seconds']}
        
        # 获取策略
        policy = 'policy_admin_protection' if is_admin else 'policy_login_escalating'
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT max_attempts, lock_duration_seconds, escalate_lock 
            FROM lock_policies WHERE policy_id = ?
        ''', (policy,))
        
        policy_data = cursor.fetchone()
        conn.close()
        
        if not policy_data:
            max_attempts = 5
            lock_duration = 300
            escalate = False
        else:
            max_attempts, lock_duration, escalate = policy_data
        
        # 获取尝试次数
        attempts = self.get_login_attempts_count(username, ip_address)
        
        if attempts >= max_attempts:
            # 计算递增锁定时长
            if escalate:
                escalation_factor = min((attempts // max_attempts), 10)
                lock_duration *= escalation_factor
            
            self.lock_account(username, attempts, lock_duration)
            self.record_login_attempt(username, ip_address, False, '账户已锁定')
            return {'success': False, 'reason': 'lock_triggered', 'attempts': attempts}
        
        # 记录尝试（失败）
        self.record_login_attempt(username, ip_address, False, '密码错误')
        remaining = max_attempts - attempts
        return {'success': False, 'reason': 'password_error', 'remaining_attempts': remaining}
    
    def handle_successful_login(self, username, ip_address):
        """处理成功登录"""
        self.record_login_attempt(username, ip_address, True)
        
        # 检查是否需要解锁（如果之前被锁定）
        account_check = self.check_account_lock(username)
        if account_check['locked']:
            self.unlock_account(username)
        
        # 创建会话
        session_id = f"session_{username}_{int(time.time())}"
        login_time = datetime.now().isoformat()
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO session_timeouts
            (session_id, user_id, login_time, last_activity, timeout_duration_seconds, status)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            session_id,
            username,
            login_time,
            login_time,
            3600,
            'active'
        ))
        
        conn.commit()
        conn.close()
        
        return {'success': True, 'session_id': session_id}
    
    def check_session_timeout(self, session_id):
        """检查会话是否超时"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT last_activity, timeout_duration_seconds, status 
            FROM session_timeouts WHERE session_id = ?
        ''', (session_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            return {'valid': False, 'reason': 'session_not_found'}
        
        last_activity, timeout_duration, status = result
        
        if status != 'active':
            return {'valid': False, 'reason': 'session_inactive'}
        
        last_time = datetime.fromisoformat(last_activity)
        timeout_time = last_time + timedelta(seconds=timeout_duration)
        
        if datetime.now() > timeout_time:
            self.invalidate_session(session_id)
            return {'valid': False, 'reason': 'session_timeout'}
        
        # 更新活动时间
        self.update_session_activity(session_id)
        return {'valid': True}
    
    def update_session_activity(self, session_id):
        """更新会话活动时间"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE session_timeouts SET last_activity = ? WHERE session_id = ?
        ''', (datetime.now().isoformat(), session_id))
        
        conn.commit()
        conn.close()
    
    def invalidate_session(self, session_id):
        """使会话失效"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE session_timeouts SET status = 'expired' WHERE session_id = ?
        ''', (session_id,))
        
        conn.commit()
        conn.close()
    
    def cleanup_expired_locks(self):
        """清理过期的锁定记录"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        now = datetime.now().isoformat()
        
        cursor.execute('''
            UPDATE account_locks SET status = 'expired' 
            WHERE status = 'locked' AND unlock_time < ?
        ''', (now,))
        
        cursor.execute('''
            UPDATE ip_locks SET status = 'expired' 
            WHERE status = 'locked' AND unlock_time < ?
        ''', (now,))
        
        conn.commit()
        conn.close()
    
    def generate_lock_report(self):
        """生成锁定报告"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM account_locks WHERE status = "locked"')
        active_account_locks = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM ip_locks WHERE status = "locked"')
        active_ip_locks = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM login_attempts WHERE success = 0 AND attempt_time >= ?', 
                      ((datetime.now() - timedelta(hours=24)).isoformat(),))
        failed_attempts_24h = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM session_timeouts WHERE status = "active"')
        active_sessions = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM lock_policies WHERE enabled = 1')
        active_policies = cursor.fetchone()[0]
        
        conn.close()
        
        print("\n" + "="*80)
        print("          超时锁定机制报告")
        print("="*80)
        
        print(f"\n当前锁定状态:")
        print(f"  锁定账户: {active_account_locks} 个")
        print(f"  锁定IP: {active_ip_locks} 个")
        print(f"  活跃会话: {active_sessions} 个")
        
        print(f"\n安全统计 (24小时):")
        print(f"  登录失败次数: {failed_attempts_24h} 次")
        
        print(f"\n锁定策略:")
        print(f"  活跃策略: {active_policies} 个")
        
        print("\n" + "="*80)
        print("  超时锁定机制增强完成！")
        print("="*80)
    
    def run_full_enhancement(self):
        """运行完整的增强流程"""
        print("="*80)
        print("          增强超时锁定机制")
        print("="*80)
        
        print("\n[1/3] 加载锁定策略...")
        self.load_lock_policies()
        
        print("\n[2/3] 清理过期锁定...")
        self.cleanup_expired_locks()
        
        print("\n[3/3] 生成报告...")
        self.generate_lock_report()
        
        # 演示测试
        print("\n\n演示测试:")
        print("-" * 40)
        
        # 模拟多次登录失败
        username = 'test_user'
        ip = '192.168.1.100'
        
        print(f"\n模拟登录尝试 ({username}@{ip}):")
        for i in range(6):
            result = self.handle_login_attempt(username, ip)
            if result['success']:
                print(f"  尝试 {i+1}: 登录成功")
            elif result['reason'] == 'lock_triggered':
                print(f"  尝试 {i+1}: 账户已锁定")
                break
            else:
                print(f"  尝试 {i+1}: 失败，剩余尝试: {result.get('remaining_attempts', 0)}")
        
        # 测试IP锁定
        print(f"\n模拟IP访问 ({ip}):")
        ip_result = self.check_ip_lock(ip)
        if ip_result['locked']:
            print(f"  IP已锁定")
        else:
            print(f"  IP正常")

def main():
    lock_system = EnhancedTimeoutLockSystem()
    lock_system.run_full_enhancement()

if __name__ == "__main__":
    main()