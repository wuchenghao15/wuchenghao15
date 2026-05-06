#!/usr/bin/env python3
"""
增强型安全工具类，提供反编译保护、防渗透和防提权功能

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
        else:
            key = Fernet.generate_key()
            with open(key_path, 'wb') as f:
                f.write(key)
            logger.info(f"生成新的加密密钥并保存到: {key_path}")
            return key

    def anti_decompile(self):
        """反编译保护"""
        # 1. 检测调试器
        if self._is_debugger_attached():
            logger.warning("检测到调试器附加，可能正在进行反编译尝试")
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
        """混淆代码，防止静态分析"""
        # 这里可以添加代码混淆逻辑
        # 例如：动态生成函数名、混淆字符串等
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
                # 为了简单起见，我们只记录哈希值
                logger.debug(f"文件完整性检查: {file_path} -> {file_hash}")

    def anti_penetration(self):
        """防渗透保护"""
        # 1. 检测异常请求模式
        if self._detect_attack_patterns():
            logger.warning("检测到异常请求模式，可能正在进行渗透攻击")
            return False

        # 2. 实施请求限流
        if not self._rate_limit():
            logger.warning("请求频率超过限制")
            return False
        # 3. 输入验证和过滤
        if not self._validate_inputs():
            logger.warning("输入验证失败")
            return False
        logger.info("防渗透保护检查通过")
        return True

    def _detect_attack_patterns(self):
        """检测攻击模式"""
        # 检测常见的攻击模式
        attack_patterns = [
            'union select', 'or 1=1', 'drop table', 'insert into', 'update set',
            'script', 'onload', 'onerror', 'eval(', 'document.cookie',
            '../', '..\', '/etc/passwd', 'C:\\windows\\system32',
            '--', '/*', '*/', 'xp_cmdshell'
        ]
        # 检查请求参数
        for key, value in request.args.items():
            if any(pattern in str(value).lower() for pattern in attack_patterns):
                logger.warning(f"检测到攻击模式: {key} = {value}")
                return True

        for key, value in request.form.items():
            if any(pattern in str(value).lower() for pattern in attack_patterns):
                return True

        return False
        # 简单的IP限流，每分钟最多100个请求
        current_time = datetime.now()

        # 使用session存储请求计数
        if 'rate_limit' not in session:
            session['rate_limit'] = {}

        if ip not in session['rate_limit']:
            session['rate_limit'][ip] = {
                'count': 1,
                'last_request': current_time
            }
            return True

        # 检查时间窗口
        time_diff = (current_time - session['rate_limit'][ip]['last_request']).total_seconds()
        if time_diff > 60:
            session['rate_limit'][ip] = {
                'count': 1,
                'last_request': current_time
            }
            return True

        # 检查请求计数
        if session['rate_limit'][ip]['count'] > 100:
            return False
        session['rate_limit'][ip]['count'] += 1
        return True
    def _validate_inputs(self):
        # 这里可以添加更详细的输入验证逻辑

    def anti_privilege_escalation(self):
        """防提权保护"""
        # 1. 验证会话完整性
        if not self._verify_session_integrity():
            return False

        if not self._check_least_privilege():
            logger.warning("最小权限原则检查失败")
            return False

        self._audit_privilege_changes()

        logger.info("防提权保护检查通过")
        return True

    def _verify_session_integrity(self):
        """验证会话完整性"""
        # 检查会话是否被篡改
        if 'session_hash' not in session:
            # 创建会话哈希
            session_data = {k: v for k, v in session.items() if k != 'session_hash'}
            return True

        # 验证会话哈希
        session_data = {k: v for k, v in session.items() if k != 'session_hash'}
        expected_hash = self._compute_session_hash(session_data)
        if session['session_hash'] != expected_hash:
            logger.warning("会话哈希验证失败，会话可能被篡改")
            return False

    def _compute_session_hash(self, session_data):
        """计算会话哈希"""
        # 对会话数据进行排序并生成哈希
        sorted_data = sorted(session_data.items(), key=lambda x: x[0])
        data_str = str(sorted_data).encode('utf-8')
        return hashlib.sha256(data_str + self.key).hexdigest()

        """检查最小权限原则"""
        # 验证用户是否只拥有必要的权限
        # 这里可以添加具体的权限检查逻辑
        return True

    def _audit_privilege_changes(self):
        """审计权限变更"""
        # 记录权限变更日志
        pass
    def encrypt_data(self, data):
        """加密敏感数据"""

        Args:
            data: 要加密的数据

        Returns:
            加密后的数据
        if isinstance(data, str):
            data = data.encode('utf-8')
        return self.fernet.encrypt(data)

    def decrypt_data(self, encrypted_data):
        """解密敏感数据"""
        解密敏感数据

        Args:
            encrypted_data: 要解密的数据

        Returns:
            解密后的数据
        if isinstance(encrypted_data, str):
            encrypted_data = encrypted_data.encode('utf-8')
        return self.fernet.decrypt(encrypted_data).decode('utf-8')

    def generate_secure_token(self, length=32):
        """生成安全令牌"""
        生成安全令牌

        Args:
            length: 令牌长度

        Returns:
            安全令牌
        return secrets.token_hex(length)

    def verify_password_strength(self, password):
        """验证密码强度"""
        验证密码强度

        Args:
            password: 要验证的密码

        Returns:
            (is_strong, message) - (密码是否强, 消息)
        if len(password) < 8:
            return False, "密码长度必须至少8个字符"
        if not any(c.isupper() for c in password):
            return False, "密码必须包含至少一个大写字母"
        if not any(c.islower() for c in password):
            return False, "密码必须包含至少一个小写字母"
        if not any(c.isdigit() for c in password):
            return False, "密码必须包含至少一个数字"
        if not any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?`~' for c in password):
            return False, "密码必须包含至少一个特殊字符"
        return True, "密码强度符合要求"

    def sanitize_input(self, input_str):
        """清理用户输入，防止注入攻击"""
        清理用户输入，防止注入攻击

        Args:
            input_str: 要清理的输入字符串

        Returns:
            清理后的输入字符串
        if not input_str:
            return input_str

        # 简单的HTML转义
        input_str = input_str.replace('<', '&lt;')
        input_str = input_str.replace('>', '&gt;')
        input_str = input_str.replace('"', '&quot;')
        input_str = input_str.replace("'", '&#x27;')
        input_str = input_str.replace('/', '&#x2F;')

        return input_str

# 创建增强型安全工具实例
security_enhanced = SecurityEnhanced()

# 全局反编译保护
security_enhanced.anti_decompile()
