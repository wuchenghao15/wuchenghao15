#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS用户认证服务
提供用户注册、登录、权限管理功能
"""

import os
import sys
import json
import time
import hashlib
import uuid
import threading
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List

logger = print

class UserInfo:
    """用户信息"""
    
    def __init__(self, user_id: str, username: str, email: str, 
                 password_hash: str, role: str = 'user', 
                 enabled: bool = True, created_at: str = None):
        self.user_id = user_id
        self.username = username
        self.email = email
        self.password_hash = password_hash
        self.role = role
        self.enabled = enabled
        self.created_at = created_at or datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'user_id': self.user_id,
            'username': self.username,
            'email': self.email,
            'role': self.role,
            'enabled': self.enabled,
            'created_at': self.created_at
        }

class AuthManager:
    """认证管理器"""
    
    def __init__(self):
        self.users: Dict[str, UserInfo] = {}
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.is_running = False
        self.session_cleanup_thread = None
        self.lock = threading.Lock()
        
        self.config = self._load_config()
        self._init_database()
        self._load_users()
    
    def _load_config(self) -> Dict[str, Any]:
        """加载配置"""
        config_path = os.path.join(os.path.dirname(__file__), 'auth_config.json')
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        return {
            'enabled': True,
            'session_timeout': 3600,
            'max_login_attempts': 5,
            'lockout_duration': 300,
            'min_password_length': 6,
            'password_require_special_char': False,
            'auto_create_admin': True
        }
    
    def _save_config(self):
        """保存配置"""
        config_path = os.path.join(os.path.dirname(__file__), 'auth_config.json')
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)
    
    def _init_database(self):
        """初始化数据库"""
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL UNIQUE,
                    username TEXT NOT NULL UNIQUE,
                    email TEXT NOT NULL UNIQUE,
                    password_hash TEXT NOT NULL,
                    role TEXT DEFAULT 'user',
                    enabled INTEGER DEFAULT 1,
                    failed_login_attempts INTEGER DEFAULT 0,
                    last_login_attempt TEXT,
                    locked_until TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL UNIQUE,
                    user_id TEXT NOT NULL,
                    user_ip TEXT,
                    user_agent TEXT,
                    expires_at TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS roles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    role_name TEXT NOT NULL UNIQUE,
                    permissions TEXT,
                    description TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_permissions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    permission TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
            conn.close()
            
            self._init_default_roles()
            self._init_admin_user()
        except Exception as e:
            logger(f"[认证] 初始化数据库失败: {e}")
    
    def _init_default_roles(self):
        """初始化默认角色"""
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            
            roles = [
                ('admin', json.dumps(['*']), '管理员，拥有所有权限'),
                ('user', json.dumps(['read', 'write']), '普通用户，拥有基本读写权限'),
                ('viewer', json.dumps(['read']), '查看者，只拥有只读权限'),
                ('guest', json.dumps([]), '访客，无权限')
            ]
            
            for role_name, permissions, description in roles:
                cursor.execute('INSERT OR IGNORE INTO roles (role_name, permissions, description) VALUES (?, ?, ?)',
                              (role_name, permissions, description))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[认证] 初始化角色失败: {e}")
    
    def _init_admin_user(self):
        """初始化管理员用户"""
        if not self.config['auto_create_admin']:
            return
        
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*) FROM users WHERE username = "admin"')
            count = cursor.fetchone()[0]
            
            if count == 0:
                admin_password = 'admin123'
                password_hash = self._hash_password(admin_password)
                
                cursor.execute('''
                    INSERT INTO users (user_id, username, email, password_hash, role, enabled)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', ('admin', 'admin', 'admin@mtscos.com', password_hash, 'admin', 1))
                
                logger(f"[认证] 创建默认管理员用户: admin/admin123")
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[认证] 初始化管理员失败: {e}")
    
    def _hash_password(self, password: str) -> str:
        """哈希密码"""
        return hashlib.sha256(password.encode('utf-8')).hexdigest()
    
    def _generate_session_id(self) -> str:
        """生成会话ID"""
        return str(uuid.uuid4())
    
    def _load_users(self):
        """加载用户"""
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            
            cursor.execute('SELECT user_id, username, email, password_hash, role, enabled, created_at FROM users')
            
            for row in cursor.fetchall():
                user_id, username, email, password_hash, role, enabled, created_at = row
                
                user = UserInfo(
                    user_id=user_id,
                    username=username,
                    email=email,
                    password_hash=password_hash,
                    role=role,
                    enabled=bool(enabled),
                    created_at=created_at
                )
                
                self.users[user_id] = user
            
            conn.close()
            logger(f"[认证] 加载了 {len(self.users)} 个用户")
        except Exception as e:
            logger(f"[认证] 加载用户失败: {e}")
    
    def register(self, username: str, password: str, email: str, 
                 role: str = 'user') -> Optional[str]:
        """注册用户"""
        if len(password) < self.config['min_password_length']:
            logger(f"[认证] 密码长度不足")
            return None
        
        if username in [user.username for user in self.users.values()]:
            logger(f"[认证] 用户名已存在: {username}")
            return None
        
        if email in [user.email for user in self.users.values()]:
            logger(f"[认证] 邮箱已存在: {email}")
            return None
        
        user_id = str(uuid.uuid4())
        password_hash = self._hash_password(password)
        
        user = UserInfo(
            user_id=user_id,
            username=username,
            email=email,
            password_hash=password_hash,
            role=role
        )
        
        with self.lock:
            self.users[user_id] = user
        
        self._save_user_to_db(user)
        
        logger(f"[认证] 用户注册成功: {username}")
        return user_id
    
    def _save_user_to_db(self, user: UserInfo):
        """保存用户到数据库"""
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO users (user_id, username, email, password_hash, role, enabled, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                user.user_id, user.username, user.email, user.password_hash,
                user.role, 1 if user.enabled else 0, user.created_at
            ))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[认证] 保存用户失败: {e}")
    
    def login(self, username: str, password: str, user_ip: str = None, 
              user_agent: str = None) -> Optional[str]:
        """登录"""
        user = None
        
        with self.lock:
            for u in self.users.values():
                if u.username == username:
                    user = u
                    break
        
        if not user:
            logger(f"[认证] 用户不存在: {username}")
            return None
        
        if not user.enabled:
            logger(f"[认证] 用户已禁用: {username}")
            return None
        
        if self._is_account_locked(user.username):
            logger(f"[认证] 账户已锁定: {username}")
            return None
        
        password_hash = self._hash_password(password)
        
        if user.password_hash != password_hash:
            self._record_failed_login(user.username)
            logger(f"[认证] 密码错误: {username}")
            return None
        
        self._reset_login_attempts(user.username)
        
        session_id = self._generate_session_id()
        expires_at = (datetime.now() + timedelta(seconds=self.config['session_timeout'])).isoformat()
        
        session = {
            'session_id': session_id,
            'user_id': user.user_id,
            'username': user.username,
            'role': user.role,
            'user_ip': user_ip,
            'user_agent': user_agent,
            'expires_at': expires_at,
            'created_at': datetime.now().isoformat()
        }
        
        with self.lock:
            self.sessions[session_id] = session
        
        self._save_session_to_db(session)
        
        logger(f"[认证] 用户登录成功: {username}")
        return session_id
    
    def _save_session_to_db(self, session: Dict[str, Any]):
        """保存会话到数据库"""
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO sessions (session_id, user_id, user_ip, user_agent, expires_at)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                session['session_id'], session['user_id'],
                session['user_ip'], session['user_agent'],
                session['expires_at']
            ))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[认证] 保存会话失败: {e}")
    
    def _record_failed_login(self, username: str):
        """记录登录失败"""
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE users 
                SET failed_login_attempts = failed_login_attempts + 1,
                    last_login_attempt = ?
                WHERE username = ?
            ''', (datetime.now().isoformat(), username))
            
            cursor.execute('SELECT failed_login_attempts FROM users WHERE username = ?', (username,))
            attempts = cursor.fetchone()[0]
            
            if attempts >= self.config['max_login_attempts']:
                locked_until = (datetime.now() + timedelta(seconds=self.config['lockout_duration'])).isoformat()
                cursor.execute('UPDATE users SET locked_until = ? WHERE username = ?',
                              (locked_until, username))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[认证] 记录登录失败失败: {e}")
    
    def _reset_login_attempts(self, username: str):
        """重置登录尝试次数"""
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE users 
                SET failed_login_attempts = 0, 
                    last_login_attempt = NULL, 
                    locked_until = NULL
                WHERE username = ?
            ''', (username,))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[认证] 重置登录尝试失败: {e}")
    
    def _is_account_locked(self, username: str) -> bool:
        """检查账户是否被锁定"""
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            
            cursor.execute('SELECT locked_until FROM users WHERE username = ?', (username,))
            result = cursor.fetchone()
            
            conn.close()
            
            if result and result[0]:
                return datetime.now().isoformat() < result[0]
            
            return False
        except Exception as e:
            logger(f"[认证] 检查账户锁定失败: {e}")
            return False
    
    def logout(self, session_id: str):
        """登出"""
        with self.lock:
            if session_id in self.sessions:
                del self.sessions[session_id]
        
        self._delete_session_from_db(session_id)
        
        logger(f"[认证] 用户登出: {session_id}")
    
    def _delete_session_from_db(self, session_id: str):
        """从数据库删除会话"""
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM sessions WHERE session_id = ?', (session_id,))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[认证] 删除会话失败: {e}")
    
    def validate_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """验证会话"""
        with self.lock:
            session = self.sessions.get(session_id)
            
            if not session:
                return None
            
            if datetime.now().isoformat() > session['expires_at']:
                del self.sessions[session_id]
                return None
            
            session['expires_at'] = (datetime.now() + timedelta(seconds=self.config['session_timeout'])).isoformat()
        
        return session
    
    def get_user(self, user_id: str) -> Optional[UserInfo]:
        """获取用户"""
        return self.users.get(user_id)
    
    def get_user_by_username(self, username: str) -> Optional[UserInfo]:
        """通过用户名获取用户"""
        for user in self.users.values():
            if user.username == username:
                return user
        return None
    
    def get_users(self, role: str = None, enabled_only: bool = False) -> List[UserInfo]:
        """获取用户列表"""
        result = []
        
        with self.lock:
            for user in self.users.values():
                if role and user.role != role:
                    continue
                if enabled_only and not user.enabled:
                    continue
                result.append(user)
        
        result.sort(key=lambda x: x.created_at, reverse=True)
        return result
    
    def update_user(self, user_id: str, **kwargs) -> bool:
        """更新用户"""
        with self.lock:
            if user_id not in self.users:
                logger(f"[认证] 用户不存在: {user_id}")
                return False
            
            user = self.users[user_id]
            
            if 'username' in kwargs:
                user.username = kwargs['username']
            if 'email' in kwargs:
                user.email = kwargs['email']
            if 'role' in kwargs:
                user.role = kwargs['role']
            if 'enabled' in kwargs:
                user.enabled = kwargs['enabled']
            if 'password' in kwargs:
                user.password_hash = self._hash_password(kwargs['password'])
        
        self._update_user_in_db(user_id, kwargs)
        
        logger(f"[认证] 更新用户成功: {user_id}")
        return True
    
    def _update_user_in_db(self, user_id: str, updates: Dict[str, Any]):
        """更新数据库中的用户"""
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            
            set_clause = []
            params = []
            
            for key, value in updates.items():
                if key == 'enabled':
                    set_clause.append(f"{key} = ?")
                    params.append(1 if value else 0)
                elif key == 'password':
                    set_clause.append("password_hash = ?")
                    params.append(self._hash_password(value))
                else:
                    set_clause.append(f"{key} = ?")
                    params.append(value)
            
            params.append(user_id)
            
            cursor.execute(f'UPDATE users SET {", ".join(set_clause)} WHERE user_id = ?', params)
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[认证] 更新用户数据库失败: {e}")
    
    def delete_user(self, user_id: str) -> bool:
        """删除用户"""
        with self.lock:
            if user_id not in self.users:
                logger(f"[认证] 用户不存在: {user_id}")
                return False
            
            del self.users[user_id]
        
        self._delete_user_from_db(user_id)
        
        logger(f"[认证] 删除用户成功: {user_id}")
        return True
    
    def _delete_user_from_db(self, user_id: str):
        """从数据库删除用户"""
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM users WHERE user_id = ?', (user_id,))
            cursor.execute('DELETE FROM sessions WHERE user_id = ?', (user_id,))
            cursor.execute('DELETE FROM user_permissions WHERE user_id = ?', (user_id,))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[认证] 删除用户数据库失败: {e}")
    
    def check_permission(self, user_id: str, permission: str) -> bool:
        """检查权限"""
        user = self.users.get(user_id)
        
        if not user:
            return False
        
        if user.role == 'admin':
            return True
        
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            
            cursor.execute('SELECT permissions FROM roles WHERE role_name = ?', (user.role,))
            result = cursor.fetchone()
            
            if result and result[0]:
                permissions = json.loads(result[0])
                
                if '*' in permissions:
                    return True
                if permission in permissions:
                    return True
            
            cursor.execute('SELECT permission FROM user_permissions WHERE user_id = ?', (user_id,))
            user_permissions = [row[0] for row in cursor.fetchall()]
            
            if permission in user_permissions:
                return True
            
            conn.close()
        except Exception as e:
            logger(f"[认证] 检查权限失败: {e}")
        
        return False
    
    def grant_permission(self, user_id: str, permission: str):
        """授予权限"""
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            
            cursor.execute('INSERT OR IGNORE INTO user_permissions (user_id, permission) VALUES (?, ?)',
                          (user_id, permission))
            
            conn.commit()
            conn.close()
            
            logger(f"[认证] 授予权限: {user_id} - {permission}")
        except Exception as e:
            logger(f"[认证] 授予权限失败: {e}")
    
    def revoke_permission(self, user_id: str, permission: str):
        """撤销权限"""
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM user_permissions WHERE user_id = ? AND permission = ?',
                          (user_id, permission))
            
            conn.commit()
            conn.close()
            
            logger(f"[认证] 撤销权限: {user_id} - {permission}")
        except Exception as e:
            logger(f"[认证] 撤销权限失败: {e}")
    
    def _session_cleanup_loop(self):
        """会话清理循环"""
        while self.is_running:
            try:
                time.sleep(60)
                
                now = datetime.now().isoformat()
                
                with self.lock:
                    expired_sessions = [sid for sid, session in self.sessions.items() 
                                       if session['expires_at'] < now]
                    
                    for sid in expired_sessions:
                        del self.sessions[sid]
                
                if expired_sessions:
                    logger(f"[认证] 清理过期会话: {len(expired_sessions)}个")
            except Exception as e:
                logger(f"[认证] 会话清理错误: {e}")
    
    def start(self):
        """启动认证服务"""
        if self.is_running:
            return
        
        self.is_running = True
        self.session_cleanup_thread = threading.Thread(target=self._session_cleanup_loop, daemon=True)
        self.session_cleanup_thread.start()
        logger(f"[认证] 用户认证服务已启动")
    
    def stop(self):
        """停止认证服务"""
        self.is_running = False
        if self.session_cleanup_thread:
            self.session_cleanup_thread.join()
        
        logger(f"[认证] 用户认证服务已停止")
    
    def get_status(self) -> Dict[str, Any]:
        """获取服务状态"""
        with self.lock:
            enabled_users = sum(1 for user in self.users.values() if user.enabled)
            disabled_users = len(self.users) - enabled_users
            
            return {
                'status': 'running' if self.is_running else 'stopped',
                'total_users': len(self.users),
                'enabled_users': enabled_users,
                'disabled_users': disabled_users,
                'active_sessions': len(self.sessions),
                'session_timeout': self.config['session_timeout'],
                'max_login_attempts': self.config['max_login_attempts']
            }

auth_manager = AuthManager()
