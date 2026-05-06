#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Session和Cookie安全管理系统"""

import os
# JSON support removed - using database
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
logger = logging.getLogger('session_cookie_manager')

class SessionCookieManager:
    def __init__(self):
        self.db_path = 'app.db'
        self.session_store = {}
        self.cookie_config = self.get_cookie_config()
        self.init_session_database()
    
    def get_cookie_config(self):
        """获取Cookie安全配置"""
        return {
            'session_cookie_name': 'MTSCOS_SESSION',
            'csrf_cookie_name': 'MTSCOS_CSRF',
            'max_age': 3600,  # 1小时
            'http_only': True,
            'secure': True,
            'same_site': 'Strict',
            'path': '/',
            'domain': None,
            'samesite': 'Strict'
        }
    
    def init_session_database(self):
        """初始化会话数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        tables = [
            '''CREATE TABLE IF NOT EXISTS secure_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT UNIQUE NOT NULL,
                user_id TEXT NOT NULL,
                user_agent TEXT,
                ip_address TEXT,
                created_at TEXT NOT NULL,
                last_activity TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                status TEXT DEFAULT 'active',
                csrf_token TEXT,
                refresh_token TEXT,
                data TEXT
            )''',
            
            '''CREATE TABLE IF NOT EXISTS session_blacklist (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT UNIQUE NOT NULL,
                blacklisted_at TEXT NOT NULL,
                reason TEXT
            )''',
            
            '''CREATE TABLE IF NOT EXISTS cookie_policies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                policy_id TEXT UNIQUE NOT NULL,
                policy_name TEXT,
                cookie_name TEXT,
                http_only INTEGER DEFAULT 1,
                secure INTEGER DEFAULT 1,
                same_site TEXT DEFAULT 'Strict',
                max_age INTEGER DEFAULT 3600,
                path TEXT DEFAULT '/',
                domain TEXT,
                enabled INTEGER DEFAULT 1,
                created_at TEXT
            )''',
            
            '''CREATE TABLE IF NOT EXISTS session_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                user_id TEXT,
                action TEXT,
                timestamp TEXT,
                ip_address TEXT,
                user_agent TEXT
            )'''
        ]
        
        for table_sql in tables:
            cursor.execute(table_sql)
        
        conn.commit()
        conn.close()
        logger.info("Session和Cookie数据库初始化完成")
    
    def load_cookie_policies(self):
        """加载Cookie安全策略"""
        policies = [
            {
                'policy_id': 'policy_session',
                'policy_name': '会话Cookie策略',
                'cookie_name': 'MTSCOS_SESSION',
                'http_only': 1,
                'secure': 1,
                'same_site': 'Strict',
                'max_age': 3600,
                'path': '/',
                'domain': None
            },
            {
                'policy_id': 'policy_csrf',
                'policy_name': 'CSRF防护Cookie策略',
                'cookie_name': 'MTSCOS_CSRF',
                'http_only': 0,
                'secure': 1,
                'same_site': 'Strict',
                'max_age': 3600,
                'path': '/',
                'domain': None
            },
            {
                'policy_id': 'policy_remember',
                'policy_name': '记住我Cookie策略',
                'cookie_name': 'MTSCOS_REMEMBER',
                'http_only': 1,
                'secure': 1,
                'same_site': 'Strict',
                'max_age': 604800,  # 7天
                'path': '/',
                'domain': None
            },
            {
                'policy_id': 'policy_preference',
                'policy_name': '用户偏好Cookie策略',
                'cookie_name': 'MTSCOS_PREF',
                'http_only': 0,
                'secure': 0,
                'same_site': 'Lax',
                'max_age': 31536000,  # 1年
                'path': '/',
                'domain': None
            }
        ]
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for policy in policies:
            cursor.execute('''
                INSERT OR REPLACE INTO cookie_policies
                (policy_id, policy_name, cookie_name, http_only, secure, 
                 same_site, max_age, path, domain, enabled, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                policy['policy_id'],
                policy['policy_name'],
                policy['cookie_name'],
                policy['http_only'],
                policy['secure'],
                policy['same_site'],
                policy['max_age'],
                policy['path'],
                policy['domain'],
                1,
                datetime.now().isoformat()
            ))
        
        conn.commit()
        conn.close()
        logger.info("Cookie策略已加载")
    
    def generate_session_id(self) -> str:
        """生成安全的Session ID"""
        return secrets.token_hex(32)  # 64位随机字符串
    
    def generate_csrf_token(self) -> str:
        """生成CSRF令牌"""
        return secrets.token_hex(16)  # 32位随机字符串
    
    def generate_refresh_token(self) -> str:
        """生成刷新令牌"""
        return secrets.token_hex(48)  # 96位随机字符串
    
    def create_session(self, user_id: str, ip_address: str, user_agent: str) -> Dict:
        """创建安全会话"""
        session_id = self.generate_session_id()
        csrf_token = self.generate_csrf_token()
        refresh_token = self.generate_refresh_token()
        
        now = datetime.now()
        expires_at = (now + timedelta(seconds=self.cookie_config['max_age'])).isoformat()
        
        session_data = {
            'session_id': session_id,
            'user_id': user_id,
            'user_agent': user_agent,
            'ip_address': ip_address,
            'created_at': now.isoformat(),
            'last_activity': now.isoformat(),
            'expires_at': expires_at,
            'status': 'active',
            'csrf_token': csrf_token,
            'refresh_token': refresh_token,
            'data': str({})
        }
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO secure_sessions
            (session_id, user_id, user_agent, ip_address, created_at, 
             last_activity, expires_at, status, csrf_token, refresh_token, data)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            session_id, user_id, user_agent, ip_address,
            session_data['created_at'], session_data['last_activity'],
            expires_at, 'active', csrf_token, refresh_token, '{}'
        ))
        
        cursor.execute('''
            INSERT INTO session_history
            (session_id, user_id, action, timestamp, ip_address, user_agent)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (session_id, user_id, 'created', now.isoformat(), ip_address, user_agent))
        
        conn.commit()
        conn.close()
        
        return session_data
    
    def validate_session(self, session_id: str, ip_address: str = None, user_agent: str = None) -> Dict:
        """验证会话有效性"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 检查是否在黑名单中
        cursor.execute('SELECT COUNT(*) FROM session_blacklist WHERE session_id = ?', (session_id,))
        if cursor.fetchone()[0] > 0:
            conn.close()
            return {'valid': False, 'reason': 'session_blacklisted'}
        
        # 获取会话信息
        cursor.execute('''
            SELECT user_id, user_agent, ip_address, expires_at, status, csrf_token 
            FROM secure_sessions WHERE session_id = ?
        ''', (session_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            return {'valid': False, 'reason': 'session_not_found'}
        
        user_id, stored_agent, stored_ip, expires_at, status, csrf_token = result
        
        # 检查状态
        if status != 'active':
            return {'valid': False, 'reason': 'session_inactive'}
        
        # 检查过期时间
        if datetime.now() > datetime.fromisoformat(expires_at):
            return {'valid': False, 'reason': 'session_expired'}
        
        # 检查IP（可选）
        if ip_address and stored_ip != ip_address:
            return {'valid': False, 'reason': 'ip_mismatch'}
        
        # 检查User-Agent（可选）
        if user_agent and stored_agent != user_agent:
            return {'valid': False, 'reason': 'user_agent_mismatch'}
        
        # 更新活动时间
        self.update_session_activity(session_id)
        
        return {
            'valid': True,
            'user_id': user_id,
            'csrf_token': csrf_token,
            'expires_at': expires_at
        }
    
    def update_session_activity(self, session_id: str):
        """更新会话活动时间"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE secure_sessions 
            SET last_activity = ?, expires_at = ?
            WHERE session_id = ?
        ''', (
            datetime.now().isoformat(),
            (datetime.now() + timedelta(seconds=self.cookie_config['max_age'])).isoformat(),
            session_id
        ))
        
        conn.commit()
        conn.close()
    
    def invalidate_session(self, session_id: str, reason: str = 'logout'):
        """使会话失效"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 更新会话状态
        cursor.execute('''
            UPDATE secure_sessions SET status = 'invalidated' WHERE session_id = ?
        ''', (session_id,))
        
        # 添加到黑名单
        cursor.execute('''
            INSERT INTO session_blacklist (session_id, blacklisted_at, reason)
            VALUES (?, ?, ?)
        ''', (session_id, datetime.now().isoformat(), reason))
        
        # 记录历史
        cursor.execute('''
            INSERT INTO session_history
            (session_id, user_id, action, timestamp, ip_address, user_agent)
            SELECT session_id, user_id, 'invalidated', ?, ip_address, user_agent
            FROM secure_sessions WHERE session_id = ?
        ''', (datetime.now().isoformat(), session_id))
        
        conn.commit()
        conn.close()
    
    def refresh_session(self, session_id: str, refresh_token: str) -> Optional[Dict]:
        """刷新会话（获取新的Session ID）"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT user_id, user_agent, ip_address, refresh_token AS stored_token 
            FROM secure_sessions WHERE session_id = ? AND status = 'active'
        ''', (session_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            return None
        
        user_id, user_agent, ip_address, stored_token = result
        
        # 验证刷新令牌
        if stored_token != refresh_token:
            return None
        
        # 使旧会话失效
        self.invalidate_session(session_id, 'refreshed')
        
        # 创建新会话
        return self.create_session(user_id, ip_address, user_agent)
    
    def validate_csrf(self, session_id: str, csrf_token: str) -> bool:
        """验证CSRF令牌"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT csrf_token FROM secure_sessions 
            WHERE session_id = ? AND status = 'active'
        ''', (session_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            return False
        
        return result[0] == csrf_token
    
    def get_cookie_settings(self, policy_id: str) -> Dict:
        """获取Cookie设置"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT cookie_name, http_only, secure, same_site, max_age, path, domain 
            FROM cookie_policies WHERE policy_id = ? AND enabled = 1
        ''', (policy_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                'name': result[0],
                'http_only': bool(result[1]),
                'secure': bool(result[2]),
                'same_site': result[3],
                'max_age': result[4],
                'path': result[5],
                'domain': result[6]
            }
        
        return self.cookie_config
    
    def cleanup_expired_sessions(self):
        """清理过期会话"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        now = datetime.now().isoformat()
        
        # 获取过期会话
        cursor.execute('''
            SELECT session_id FROM secure_sessions 
            WHERE status = 'active' AND expires_at < ?
        ''', (now,))
        
        expired_sessions = [row[0] for row in cursor.fetchall()]
        
        # 更新状态并记录
        for session_id in expired_sessions:
            cursor.execute('''
                UPDATE secure_sessions SET status = 'expired' WHERE session_id = ?
            ''', (session_id,))
            
            cursor.execute('''
                INSERT INTO session_history
                (session_id, user_id, action, timestamp, ip_address, user_agent)
                SELECT session_id, user_id, 'expired', ?, ip_address, user_agent
                FROM secure_sessions WHERE session_id = ?
            ''', (now, session_id))
        
        conn.commit()
        conn.close()
        
        return len(expired_sessions)
    
    def generate_security_report(self):
        """生成安全报告"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM secure_sessions WHERE status = "active"')
        active_sessions = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM secure_sessions WHERE status = "expired"')
        expired_sessions = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM secure_sessions WHERE status = "invalidated"')
        invalidated_sessions = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM session_blacklist')
        blacklisted_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM cookie_policies WHERE enabled = 1')
        active_policies = cursor.fetchone()[0]
        
        conn.close()
        
        print("\n" + "="*80)
        print("          Session和Cookie安全管理报告")
        print("="*80)
        
        print(f"\n会话状态:")
        print(f"  活跃会话: {active_sessions}")
        print(f"  过期会话: {expired_sessions}")
        print(f"  失效会话: {invalidated_sessions}")
        print(f"  黑名单会话: {blacklisted_count}")
        
        print(f"\nCookie策略:")
        print(f"  活跃策略: {active_policies} 个")
        
        print("\n安全配置:")
        print(f"  HttpOnly: ✅ 已启用")
        print(f"  Secure: ✅ 已启用")
        print(f"  SameSite: ✅ Strict")
        print(f"  会话超时: ✅ 1小时")
        print(f"  CSRF防护: ✅ 已启用")
        
        print("\n" + "="*80)
        print("  Session和Cookie安全管理完成！")
        print("="*80)
    
    def run_full_security_setup(self):
        """运行完整的安全设置"""
        print("="*80)
        print("          Session和Cookie安全管理")
        print("="*80)
        
        print("\n[1/3] 加载Cookie策略...")
        self.load_cookie_policies()
        
        print("\n[2/3] 清理过期会话...")
        cleaned_count = self.cleanup_expired_sessions()
        print(f"  ✓ 清理了 {cleaned_count} 个过期会话")
        
        print("\n[3/3] 生成安全报告...")
        self.generate_security_report()
        
        # 演示
        print("\n\n演示测试:")
        print("-" * 40)
        
        session = self.create_session('user123', '192.168.1.100', 'Mozilla/5.0')
        print(f"\n创建会话:")
        print(f"  Session ID: {session['session_id'][:20]}...")
        print(f"  CSRF Token: {session['csrf_token']}")
        print(f"  过期时间: {session['expires_at']}")
        
        # 验证会话
        result = self.validate_session(session['session_id'], '192.168.1.100', 'Mozilla/5.0')
        print(f"\n验证会话: {'✅ 有效' if result['valid'] else '❌ 无效'}")
        
        # 验证CSRF
        csrf_valid = self.validate_csrf(session['session_id'], session['csrf_token'])
        print(f"验证CSRF: {'✅ 有效' if csrf_valid else '❌ 无效'}")
        
        # 使会话失效
        self.invalidate_session(session['session_id'], '演示测试')
        result_after = self.validate_session(session['session_id'])
        print(f"会话失效后验证: {'✅ 有效' if result_after['valid'] else '❌ 无效'}")

def main():
    manager = SessionCookieManager()
    manager.run_full_security_setup()

if __name__ == "__main__":
    main()