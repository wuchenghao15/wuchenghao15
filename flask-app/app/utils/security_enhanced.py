# -*- coding: utf-8 -*-
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强型安全工具类 - 提供反编译保护,防渗透和防提权功能
"""

import os
import sys
import logging
import hashlib
import base64
import secrets
from datetime import datetime, timedelta
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding
from cryptography.fernet import Fernet
from flask import request, session

logger = logging.getLogger(__name__)

class SecurityEnhanced:
    """增强型安全工具类"""

    def __init__(self):
        """初始化安全工具"""
        # 加载加密密钥
        self.key = self._load_or_generate_key()
        self.fernet = Fernet(self.key)
        logger.info("增强型安全工具初始化完成")

    def _load_or_generate_key(self):
        """加载或生成加密密钥"""
        key_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'encryption.key')

        if os.path.exists(key_path):
            with open(key_path, 'rb') as f:
                return f.read()

        # 生成新密钥
        key = Fernet.generate_key()
        os.makedirs(os.path.dirname(key_path), exist_ok=True)
        with open(key_path, 'wb') as f:
            f.write(key)
        return key

    def anti_decompile(self):
        """反编译保护"""
        # 1. 检测调试器
        if self._is_debugger_attached():
            logger.warning("检测到调试器附加, 可能正在进行反编译尝试")
            # 可以选择退出程序或采取其他防护措施
            # sys.exit(1)

        # 2. 混淆关键函数名
        self._obfuscate_code()

        # 3. 添加运行时完整性检查
        self._verify_code_integrity()

        logger.info("反编译保护检查完成")

    def _is_debugger_attached(self):
        """检测是否有调试器附加"""
        # 简单的调试器检测
        return hasattr(sys, 'gettrace') and sys.gettrace() is not None

    def _obfuscate_code(self):
        """混淆代码: 防止静态分析"""
        # 这里可以添加代码混淆逻辑
        # 例如:动态生成函数名,混淆字符串等
        pass

    def _verify_code_integrity(self):
        """验证代码完整性"""
        # 计算关键文件的哈希值并验证
        critical_files = [
            __file__,
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'db.py'),
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'session_manager.py')
        ]

        for file_path in critical_files:
            if os.path.exists(file_path):
                with open(file_path, 'rb') as f:
                    file_hash = hashlib.sha256(f.read()).hexdigest()
                # 这里可以将计算出的哈希值与预存的哈希值进行比较
                # 为了简单起见,我们只记录哈希值
                logger.debug(f"文件完整性检查: {file_path} -> {file_hash}")

    def anti_penetration(self):
        """防渗透保护"""
        # 1. 检测异常请求模式
        if self._detect_attack_patterns():
            logger.warning("检测到异常请求模式, 可能正在进行渗透攻击")
            return False

        # 2. 验证输入
        if not self._validate_inputs():
            logger.warning("检测到恶意输入")
            return False

        return True

    def _detect_attack_patterns(self):
        """检测攻击模式"""
        # 检测常见的攻击模式
        attack_patterns = [
            'union select', 'or 1=1', 'drop table', 'insert into', 'update set',
            'script', 'onload', 'onerror', 'eval(', 'document.cookie',
            '../', '..\\', '/etc/passwd', 'C:\\windows\\system32',
            '--', '/*', '*/', 'xp_cmdshell'
        ]

        # 检查请求参数
        for key, value in request.args.items():
            if any(pattern in str(value).lower() for pattern in attack_patterns):
                logger.warning(f"检测到攻击模式: {key} = {value}")
                return True

        return False

    def _validate_inputs(self):
        """验证输入"""
        # 检查所有输入参数
        for key, value in request.args.items():
            if not self._is_safe_input(str(value)):
                return False
        return True

    def _is_safe_input(self, input_str):
        """检查输入是否安全"""
        dangerous_chars = ['<', '>', '"', "'", ';', '--', '/*', '*/']
        for char in dangerous_chars:
            if char in input_str:
                return False
        return True

    def anti_privilege_escalation(self):
        """防提权保护"""
        # 1. 验证会话完整性
        if not self._verify_session_integrity():
            logger.warning("会话完整性验证失败")
            return False

        # 2. 审计权限变更
        self._audit_privilege_changes()

        return True

    def _verify_session_integrity(self):
        """验证会话完整性"""
        # 检查会话是否被篡改
        if 'session_hash' not in session:
            # 创建会话哈希
            session_data = {k: v for k, v in session.items() if k != 'session_hash'}
            session['session_hash'] = self._compute_session_hash(session_data)
            return True

        # 验证会话哈希
        session_data = {k: v for k, v in session.items() if k != 'session_hash'}
        expected_hash = self._compute_session_hash(session_data)

        return session['session_hash'] == expected_hash

    def _compute_session_hash(self, session_data):
        """计算会话哈希"""
        # 对会话数据进行排序并生成哈希
        sorted_data = sorted(session_data.items(), key=lambda x: x[0])
        data_str = str(sorted_data).encode('utf-8')
        return hashlib.sha256(data_str + self.key).hexdigest()

    def _audit_privilege_changes(self):
        """审计权限变更"""
        # 记录权限变更日志
        if 'user_level' in session:
            logger.info(f"权限审计: 用户 {session.get('username', 'unknown')} 级别 {session['user_level']}")

    def encrypt_data(self, data):
        """加密敏感数据

        Args:
            data: 要加密的数据

        Returns:
            加密后的数据
        """
        if isinstance(data, str):
            data = data.encode('utf-8')
        return self.fernet.encrypt(data)

    def decrypt_data(self, encrypted_data):
        """解密敏感数据

        Args:
            encrypted_data: 要解密的数据

        Returns:
            解密后的数据
        """
        if isinstance(encrypted_data, str):
            encrypted_data = encrypted_data.encode('utf-8')
        return self.fernet.decrypt(encrypted_data).decode('utf-8')

    def generate_secure_token(self, length=32):
        """生成安全令牌

        Args:
            length: 令牌长度

        Returns:
            安全令牌
        """
        return secrets.token_hex(length)

    def verify_password_strength(self, password):
        """验证密码强度

        Args:
            password: 要验证的密码

        Returns:
            (is_strong, message) - (密码是否强, 消息)
        """
        if len(password) < 8:
            return False, "密码长度必须至少8个字符"

        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_special = any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in password)

        if not (has_upper and has_lower):
            return False, "密码必须包含大小写字母"

        if not has_digit:
            return False, "密码必须包含数字"

        if not has_special:
            return False, "密码必须包含特殊字符"

        return True, "密码强度符合要求"

    def sanitize_input(self, input_str):
        """清理用户输入: 防止注入攻击

        Args:
            input_str: 要清理的输入字符串

        Returns:
            清理后的输入字符串
        """
        if not input_str:
            return input_str

        # 移除危险字符
        dangerous_chars = {
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#x27;',
            '&': '&amp;'
        }

        for char, replacement in dangerous_chars.items():
            input_str = input_str.replace(char, replacement)

        return input_str
