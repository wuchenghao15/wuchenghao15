#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
安全模型 - 系统安全防护核心组件
包含认证授权、访问控制、攻击检测、数据加密等安全功能
"""

import logging
import hashlib
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)


class SecurityModel:
    """安全模型核心类"""

    def __init__(self):
        self.auth_manager = AuthenticationManager()
        self.acl_manager = AccessControlManager()
        self.attack_detector = AttackDetector()
        self.data_protector = DataProtectionManager()
        logger.info("安全模型初始化完成")

    def authenticate(self, credentials: Dict[str, str]) -> Optional[str]:
        """认证用户"""
        return self.auth_manager.authenticate(credentials)


class AuthenticationManager:
    """认证管理器"""

    def __init__(self):
        self.user_credentials = {}
        self.tokens = {}
        logger.info("认证管理器初始化完成")

    def register_user(self, username: str, password: str):
        """注册用户"""
        hashed_password = self._hash_password(password)
        self.user_credentials[username] = hashed_password
        logger.info(f"用户注册: {username}")

    def authenticate(self, credentials: Dict[str, str]) -> Optional[str]:
        """认证用户并返回token"""
        username = credentials.get('username')
        password = credentials.get('password')

        if username not in self.user_credentials:
            logger.warning(f"认证失败: 用户不存在 - {username}")
            return None

        if self.user_credentials[username] != self._hash_password(password):
            logger.warning(f"认证失败: 密码错误 - {username}")
            return None

        token = str(uuid.uuid4())
        self.tokens[token] = {
            'username': username,
            'expires_at': datetime.now() + timedelta(hours=24)
        }
        logger.info(f"用户认证成功: {username}")
        return token

    def validate_token(self, token: str) -> Optional[str]:
        """验证token"""
        if token not in self.tokens:
            return None

        token_info = self.tokens[token]
        if datetime.now() > token_info['expires_at']:
            del self.tokens[token]
            return None

        return token_info['username']

    def invalidate_token(self, token: str):
        """使token失效"""
        if token in self.tokens:
            del self.tokens[token]
            logger.info("Token已失效")

    def _hash_password(self, password: str) -> str:
        """哈希密码"""
        return hashlib.sha256(password.encode()).hexdigest()


class AccessControlManager:
    """访问控制管理器"""

    def __init__(self):
        self.roles = {}
        self.permissions = {}
        logger.info("访问控制管理器初始化完成")

    def define_role(self, role_name: str, permissions: List[str]):
        """定义角色"""
        self.roles[role_name] = permissions
        logger.info(f"定义角色: {role_name}")

    def assign_role(self, username: str, role_name: str):
        """分配角色"""
        if role_name not in self.roles:
            raise ValueError(f"角色 {role_name} 不存在")

        if username not in self.permissions:
            self.permissions[username] = []

        self.permissions[username].extend(self.roles[role_name])
        logger.info(f"分配角色 {role_name} 给用户 {username}")

    def check_access(self, token: str, resource: str, action: str) -> bool:
        """检查访问权限"""
        from flask import request
        auth_manager = AuthenticationManager()
        username = auth_manager.validate_token(token)

        if not username:
            return False

        user_permissions = self.permissions.get(username, [])
        required_permission = f"{resource}:{action}"

        return required_permission in user_permissions


class AttackDetector:
    """攻击检测器"""

    def __init__(self):
        self.config = {
            'max_requests_per_minute': 60,
            'max_failed_attempts': 5,
            'max_payload_size': 1024 * 1024
        }
        self.request_tracker = {}
        self.failed_attempts = {}
        logger.info("攻击检测器初始化完成")

    def detect(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """检测攻击"""
        results = {
            'is_attack': False,
            'attack_type': None,
            'risk_level': 'low',
            'details': []
        }

        client_ip = request_data.get('client_ip', 'unknown')
        timestamp = datetime.now()

        # 检测暴力破解
        if self._detect_brute_force(client_ip):
            results['is_attack'] = True
            results['attack_type'] = 'brute_force'
            results['details'].append('检测到暴力破解攻击')

        # 检测SQL注入
        if self._detect_sql_injection(request_data.get('payload', '')):
            results['is_attack'] = True
            results['attack_type'] = 'sql_injection'
            results['risk_level'] = 'critical'
            results['details'].append('检测到SQL注入攻击')

        # 检测XSS攻击
        if self._detect_xss(request_data.get('payload', '')):
            results['is_attack'] = True
            results['attack_type'] = 'xss'
            results['risk_level'] = 'high'
            results['details'].append('检测到XSS攻击')

        if self._detect_ddos(client_ip, timestamp):
            results['is_attack'] = True
            results['attack_type'] = 'ddos'
            results['risk_level'] = 'critical'
            results['details'].append('检测到DDoS攻击')

        if results['is_attack']:
            logger.warning(f"检测到攻击 - {results['attack_type']} - IP: {client_ip}")

        return results

    def _detect_brute_force(self, client_ip: str) -> bool:
        """检测暴力破解"""
        if client_ip not in self.failed_attempts:
            return False
        return self.failed_attempts[client_ip] > self.config['max_failed_attempts']

    def _detect_sql_injection(self, payload: str) -> bool:
        """检测SQL注入"""
        sql_patterns = ["'", "OR 1=1", "UNION SELECT", "--", "; DROP"]
        return any(pattern.lower() in payload.lower() for pattern in sql_patterns)

    def _detect_xss(self, payload: str) -> bool:
        """检测XSS攻击"""
        xss_patterns = ["<script>", "javascript:", "onerror=", "onload="]
        return any(pattern.lower() in payload.lower() for pattern in xss_patterns)

    def _detect_ddos(self, client_ip: str, timestamp: datetime) -> bool:
        """检测DDoS攻击"""
        if client_ip not in self.request_tracker:
            self.request_tracker[client_ip] = []
        
        self.request_tracker[client_ip].append(timestamp)
        
        # 清理超过1分钟的记录
        cutoff = timestamp - timedelta(minutes=1)
        self.request_tracker[client_ip] = [
            t for t in self.request_tracker[client_ip] if t > cutoff
        ]
        
        return len(self.request_tracker[client_ip]) > self.config['max_requests_per_minute']


class DataProtectionManager:
    """数据保护管理器"""

    def __init__(self):
        self.encryption_key = None
        logger.info("数据保护管理器初始化完成")

    def encrypt(self, data: str, key: str) -> str:
        """加密数据"""
        encrypted = ''.join(
            chr((ord(c) + ord(key[i % len(key)])) % 256)
            for i, c in enumerate(data)
        )
        return encrypted

    def decrypt(self, data: str, key: str) -> str:
        """解密数据"""
        decrypted = ''.join(
            chr((ord(c) - ord(key[i % len(key)])) % 256)
            for i, c in enumerate(data)
        )
        return decrypted


def init_security_model():
    """初始化安全模型"""
    logger.info("初始化安全模型...")

    security_model = SecurityModel()

    # 定义角色
    security_model.acl_manager.define_role('admin', [
        'users:read', 'users:write', 'users:delete',
        'system:config', 'system:logs',
        'ai:manage', 'ai:monitor'
    ])

    security_model.acl_manager.define_role('user', [
        'profile:read', 'profile:write',
        'exam:take', 'exam:view_results'
    ])

    security_model.acl_manager.define_role('guest', [
        'content:read', 'exam:preview'
    ])

    logger.info("安全模型初始化完成")
    return security_model


if __name__ == "__main__":
    init_security_model()
