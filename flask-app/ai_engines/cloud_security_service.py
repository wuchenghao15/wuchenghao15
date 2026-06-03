# -*- coding: utf-8 -*-
"""
MTSCOS 云端安全服务
提供数据加密、访问控制、安全审计、数据脱敏等安全功能
"""

import os
import json
import logging
import hashlib
import secrets
from datetime import datetime
from typing import Dict, List, Any, Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('cloud_security_service.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('cloud_security_service')

class DataEncryptor:
    """数据加密器"""
    
    def __init__(self):
        self.key_store = {}
        self._generate_master_key()
    
    def _generate_master_key(self):
        """生成主密钥"""
        master_key = secrets.token_hex(32)
        self.master_key = master_key
        logger.info("主密钥已生成")
    
    def generate_user_key(self, user_id: str, password: str = None) -> str:
        """为用户生成加密密钥"""
        salt = secrets.token_hex(16)
        
        if password:
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt.encode(),
                iterations=480000
            )
            key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        else:
            key = Fernet.generate_key()
        
        self.key_store[user_id] = {
            'key': key.decode() if isinstance(key, bytes) else key,
            'salt': salt,
            'created_at': datetime.now().isoformat()
        }
        
        logger.info(f"用户 {user_id} 密钥已生成")
        return self.key_store[user_id]['key']
    
    def encrypt_data(self, user_id: str, data: str) -> str:
        """加密数据"""
        if user_id not in self.key_store:
            self.generate_user_key(user_id)
        
        key = self.key_store[user_id]['key']
        fernet = Fernet(key)
        encrypted = fernet.encrypt(data.encode())
        return encrypted.decode()
    
    def decrypt_data(self, user_id: str, encrypted_data: str) -> str:
        """解密数据"""
        if user_id not in self.key_store:
            logger.error(f"用户 {user_id} 密钥不存在")
            return None
        
        try:
            key = self.key_store[user_id]['key']
            fernet = Fernet(key)
            decrypted = fernet.decrypt(encrypted_data.encode())
            return decrypted.decode()
        except Exception as e:
            logger.error(f"解密失败: {e}")
            return None
    
    def encrypt_file(self, user_id: str, input_path: str, output_path: str) -> bool:
        """加密文件"""
        try:
            with open(input_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            encrypted = self.encrypt_data(user_id, content)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(encrypted)
            
            logger.info(f"文件加密成功: {input_path} -> {output_path}")
            return True
        except Exception as e:
            logger.error(f"文件加密失败: {e}")
            return False
    
    def decrypt_file(self, user_id: str, input_path: str, output_path: str) -> bool:
        """解密文件"""
        try:
            with open(input_path, 'r', encoding='utf-8') as f:
                encrypted = f.read()
            
            decrypted = self.decrypt_data(user_id, encrypted)
            if decrypted is None:
                return False
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(decrypted)
            
            logger.info(f"文件解密成功: {input_path} -> {output_path}")
            return True
        except Exception as e:
            logger.error(f"文件解密失败: {e}")
            return False

class AccessControl:
    """访问控制管理器"""
    
    def __init__(self):
        self.api_keys = {}
        self.user_tokens = {}
        self.permissions = {}
        self._load_default_permissions()
    
    def _load_default_permissions(self):
        """加载默认权限配置"""
        self.permission_groups = {
            'admin': ['read', 'write', 'delete', 'manage', 'backup', 'restore'],
            'user': ['read', 'write', 'backup'],
            'guest': ['read']
        }
    
    def generate_api_key(self, user_id: str, role: str = 'user') -> str:
        """生成API密钥"""
        api_key = secrets.token_urlsafe(32)
        self.api_keys[api_key] = {
            'user_id': user_id,
            'role': role,
            'permissions': self.permission_groups.get(role, ['read']),
            'created_at': datetime.now().isoformat(),
            'last_used': None,
            'enabled': True
        }
        
        logger.info(f"用户 {user_id} API密钥已生成")
        return api_key
    
    def validate_api_key(self, api_key: str) -> Optional[Dict[str, Any]]:
        """验证API密钥"""
        if api_key not in self.api_keys:
            logger.warning("无效的API密钥")
            return None
        
        if not self.api_keys[api_key]['enabled']:
            logger.warning("API密钥已禁用")
            return None
        
        self.api_keys[api_key]['last_used'] = datetime.now().isoformat()
        return self.api_keys[api_key]
    
    def check_permission(self, api_key: str, permission: str) -> bool:
        """检查权限"""
        key_info = self.validate_api_key(api_key)
        if not key_info:
            return False
        
        return permission in key_info['permissions']
    
    def generate_token(self, user_id: str, expires_in_hours: int = 24) -> str:
        """生成访问令牌"""
        token = secrets.token_urlsafe(64)
        expires_at = (datetime.now() + timedelta(hours=expires_in_hours)).isoformat()
        
        self.user_tokens[token] = {
            'user_id': user_id,
            'expires_at': expires_at,
            'created_at': datetime.now().isoformat(),
            'valid': True
        }
        
        return token
    
    def validate_token(self, token: str) -> Optional[Dict[str, Any]]:
        """验证访问令牌"""
        if token not in self.user_tokens:
            return None
        
        token_info = self.user_tokens[token]
        
        if not token_info['valid']:
            return None
        
        if datetime.now() > datetime.fromisoformat(token_info['expires_at']):
            token_info['valid'] = False
            return None
        
        return token_info
    
    def revoke_token(self, token: str) -> bool:
        """吊销令牌"""
        if token in self.user_tokens:
            self.user_tokens[token]['valid'] = False
            logger.info(f"令牌已吊销")
            return True
        return False
    
    def disable_api_key(self, api_key: str) -> bool:
        """禁用API密钥"""
        if api_key in self.api_keys:
            self.api_keys[api_key]['enabled'] = False
            logger.info(f"API密钥已禁用")
            return True
        return False

class SecurityAudit:
    """安全审计日志"""
    
    def __init__(self):
        self.audit_logs = []
        self.alert_thresholds = {
            'failed_login': 5,
            'suspicious_activity': 3,
            'data_access': 100
        }
        self.user_alert_counts = {}
    
    def log_event(self, event_type: str, user_id: str, details: Dict[str, Any]):
        """记录安全事件"""
        event = {
            'event_id': f"audit_{int(datetime.now().timestamp())}_{secrets.token_hex(8)}",
            'event_type': event_type,
            'user_id': user_id,
            'details': details,
            'timestamp': datetime.now().isoformat(),
            'severity': self._get_severity(event_type)
        }
        
        self.audit_logs.append(event)
        self._check_alerts(event)
        
        logger.info(f"安全事件记录: {event_type} - {user_id}")
    
    def _get_severity(self, event_type: str) -> str:
        """获取事件严重级别"""
        severity_map = {
            'login_success': 'info',
            'login_failed': 'warning',
            'api_access': 'info',
            'data_access': 'info',
            'data_modification': 'warning',
            'backup': 'info',
            'restore': 'warning',
            'permission_denied': 'warning',
            'suspicious_activity': 'critical',
            'security_breach': 'critical'
        }
        return severity_map.get(event_type, 'info')
    
    def _check_alerts(self, event: Dict[str, Any]):
        """检查告警阈值"""
        user_id = event['user_id']
        event_type = event['event_type']
        
        if user_id not in self.user_alert_counts:
            self.user_alert_counts[user_id] = {}
        
        if event_type not in self.user_alert_counts[user_id]:
            self.user_alert_counts[user_id][event_type] = 0
        
        self.user_alert_counts[user_id][event_type] += 1
        
        threshold = self.alert_thresholds.get(event_type)
        if threshold and self.user_alert_counts[user_id][event_type] >= threshold:
            self._trigger_alert(user_id, event_type)
    
    def _trigger_alert(self, user_id: str, event_type: str):
        """触发告警"""
        alert = {
            'alert_id': f"alert_{int(datetime.now().timestamp())}",
            'user_id': user_id,
            'event_type': event_type,
            'message': f"用户 {user_id} 触发 {event_type} 告警",
            'timestamp': datetime.now().isoformat(),
            'status': 'active'
        }
        
        logger.critical(f"安全告警: {alert['message']}")
    
    def get_logs(self, user_id: str = None, event_type: str = None, limit: int = 100) -> List[Dict[str, Any]]:
        """获取审计日志"""
        logs = self.audit_logs
        
        if user_id:
            logs = [log for log in logs if log['user_id'] == user_id]
        
        if event_type:
            logs = [log for log in logs if log['event_type'] == event_type]
        
        return logs[-limit:]
    
    def get_alerts(self, status: str = None) -> List[Dict[str, Any]]:
        """获取告警列表"""
        return []

class DataMasking:
    """数据脱敏工具"""
    
    def __init__(self):
        self.masking_rules = {
            'phone': {'pattern': r'(\d{3})\d{4}(\d{4})', 'replace': r'\1****\2'},
            'email': {'pattern': r'(.{2})[^@]*(@.*)', 'replace': r'\1****\2'},
            'id_card': {'pattern': r'(\d{4})\d{10}(\d{4})', 'replace': r'\1**********\2'},
            'address': {'pattern': r'(.{3}).*', 'replace': r'\1***'}
        }
    
    def mask_phone(self, phone: str) -> str:
        """脱敏手机号"""
        import re
        return re.sub(self.masking_rules['phone']['pattern'], 
                      self.masking_rules['phone']['replace'], phone)
    
    def mask_email(self, email: str) -> str:
        """脱敏邮箱"""
        import re
        return re.sub(self.masking_rules['email']['pattern'], 
                      self.masking_rules['email']['replace'], email)
    
    def mask_id_card(self, id_card: str) -> str:
        """脱敏身份证号"""
        import re
        return re.sub(self.masking_rules['id_card']['pattern'], 
                      self.masking_rules['id_card']['replace'], id_card)
    
    def mask_address(self, address: str) -> str:
        """脱敏地址"""
        import re
        return re.sub(self.masking_rules['address']['pattern'], 
                      self.masking_rules['address']['replace'], address)
    
    def mask_data(self, data: Dict[str, Any], fields: List[str]) -> Dict[str, Any]:
        """批量脱敏数据"""
        masked = data.copy()
        
        for field in fields:
            if field in masked:
                value = masked[field]
                
                if field == 'phone':
                    masked[field] = self.mask_phone(value)
                elif field == 'email':
                    masked[field] = self.mask_email(value)
                elif field == 'id_card':
                    masked[field] = self.mask_id_card(value)
                elif field == 'address':
                    masked[field] = self.mask_address(value)
        
        return masked

class CloudSecurityService:
    """云端安全服务"""
    
    def __init__(self):
        self.encryptor = DataEncryptor()
        self.access_control = AccessControl()
        self.audit = SecurityAudit()
        self.data_masking = DataMasking()
        logger.info("云端安全服务初始化完成")
    
    def encrypt_user_data(self, user_id: str, data: str) -> str:
        """加密用户数据"""
        result = self.encryptor.encrypt_data(user_id, data)
        self.audit.log_event('data_access', user_id, {'action': 'encrypt'})
        return result
    
    def decrypt_user_data(self, user_id: str, encrypted_data: str) -> str:
        """解密用户数据"""
        result = self.encryptor.decrypt_data(user_id, encrypted_data)
        if result:
            self.audit.log_event('data_access', user_id, {'action': 'decrypt'})
        return result
    
    def encrypt_user_file(self, user_id: str, input_path: str, output_path: str) -> bool:
        """加密用户文件"""
        result = self.encryptor.encrypt_file(user_id, input_path, output_path)
        self.audit.log_event('data_access', user_id, {'action': 'encrypt_file', 'file': input_path})
        return result
    
    def decrypt_user_file(self, user_id: str, input_path: str, output_path: str) -> bool:
        """解密用户文件"""
        result = self.encryptor.decrypt_file(user_id, input_path, output_path)
        if result:
            self.audit.log_event('data_access', user_id, {'action': 'decrypt_file', 'file': input_path})
        return result
    
    def create_api_key(self, user_id: str, role: str = 'user') -> str:
        """创建API密钥"""
        key = self.access_control.generate_api_key(user_id, role)
        self.audit.log_event('api_access', user_id, {'action': 'create_api_key', 'role': role})
        return key
    
    def validate_api_key(self, api_key: str) -> Optional[Dict[str, Any]]:
        """验证API密钥"""
        result = self.access_control.validate_api_key(api_key)
        if result:
            self.audit.log_event('api_access', result['user_id'], {'action': 'validate_api_key'})
        else:
            self.audit.log_event('login_failed', 'unknown', {'action': 'invalid_api_key'})
        return result
    
    def check_permission(self, api_key: str, permission: str) -> bool:
        """检查权限"""
        result = self.access_control.check_permission(api_key, permission)
        if not result:
            user_info = self.access_control.validate_api_key(api_key)
            self.audit.log_event('permission_denied', user_info['user_id'] if user_info else 'unknown', 
                               {'permission': permission})
        return result
    
    def generate_access_token(self, user_id: str, expires_in_hours: int = 24) -> str:
        """生成访问令牌"""
        token = self.access_control.generate_token(user_id, expires_in_hours)
        self.audit.log_event('api_access', user_id, {'action': 'generate_token'})
        return token
    
    def validate_access_token(self, token: str) -> Optional[Dict[str, Any]]:
        """验证访问令牌"""
        result = self.access_control.validate_token(token)
        if result:
            self.audit.log_event('api_access', result['user_id'], {'action': 'validate_token'})
        return result
    
    def mask_sensitive_data(self, user_id: str, data: Dict[str, Any], fields: List[str]) -> Dict[str, Any]:
        """脱敏敏感数据"""
        masked = self.data_masking.mask_data(data, fields)
        self.audit.log_event('data_access', user_id, {'action': 'data_masking', 'fields': fields})
        return masked
    
    def log_login(self, user_id: str, success: bool, ip_address: str = None):
        """记录登录事件"""
        event_type = 'login_success' if success else 'login_failed'
        self.audit.log_event(event_type, user_id, {'ip_address': ip_address})
    
    def log_data_access(self, user_id: str, action: str, resource: str):
        """记录数据访问事件"""
        self.audit.log_event('data_access', user_id, {'action': action, 'resource': resource})
    
    def get_audit_logs(self, user_id: str = None, event_type: str = None, limit: int = 100) -> List[Dict[str, Any]]:
        """获取审计日志"""
        return self.audit.get_logs(user_id, event_type, limit)
    
    def get_system_status(self) -> Dict[str, Any]:
        """获取系统状态"""
        return {
            'version': '1.0.0',
            'components': {
                'encryptor': 'active',
                'access_control': 'active',
                'audit': 'active',
                'data_masking': 'active'
            },
            'audit_log_count': len(self.audit.audit_logs),
            'api_keys_count': len(self.access_control.api_keys),
            'tokens_count': len(self.access_control.user_tokens)
        }

cloud_security_service = CloudSecurityService()

if __name__ == '__main__':
    import base64
    from datetime import timedelta
    
    service = CloudSecurityService()
    
    print("=== 云端安全服务测试 ===")
    print(json.dumps(service.get_system_status(), indent=2, ensure_ascii=False))
    
    print("\n=== 数据加密测试 ===")
    original_data = '这是一段需要加密的敏感数据，包含用户信息：张三，13812345678，zhangsan@example.com'
    encrypted = service.encrypt_user_data('user_001', original_data)
    print(f"原始数据: {original_data}")
    print(f"加密后: {encrypted[:50]}...")
    
    decrypted = service.decrypt_user_data('user_001', encrypted)
    print(f"解密后: {decrypted}")
    print(f"解密验证: {'成功' if original_data == decrypted else '失败'}")
    
    print("\n=== API密钥测试 ===")
    api_key = service.create_api_key('user_001', 'user')
    print(f"生成的API密钥: {api_key}")
    
    validated = service.validate_api_key(api_key)
    print(f"密钥验证: {'成功' if validated else '失败'}")
    
    has_permission = service.check_permission(api_key, 'read')
    print(f"读取权限: {'有' if has_permission else '无'}")
    
    has_permission = service.check_permission(api_key, 'delete')
    print(f"删除权限: {'有' if has_permission else '无'}")
    
    print("\n=== 访问令牌测试 ===")
    token = service.generate_access_token('user_001', 1)
    print(f"生成的访问令牌: {token[:30]}...")
    
    token_validated = service.validate_access_token(token)
    print(f"令牌验证: {'成功' if token_validated else '失败'}")
    
    print("\n=== 数据脱敏测试 ===")
    sensitive_data = {
        'name': '张三',
        'phone': '13812345678',
        'email': 'zhangsan@example.com',
        'id_card': '110101199001011234',
        'address': '北京市朝阳区某某街道123号'
    }
    print(f"原始数据: {json.dumps(sensitive_data, ensure_ascii=False)}")
    
    masked = service.mask_sensitive_data('user_001', sensitive_data, ['phone', 'email', 'id_card', 'address'])
    print(f"脱敏后: {json.dumps(masked, ensure_ascii=False)}")
    
    print("\n=== 安全审计测试 ===")
    service.log_login('user_001', True, '192.168.1.100')
    service.log_data_access('user_001', 'read', '/api/data')
    
    logs = service.get_audit_logs('user_001')
    print(f"审计日志数量: {len(logs)}")
    print(f"最后一条日志: {json.dumps(logs[-1], ensure_ascii=False)}")
    
    print("\n=== 文件加密测试 ===")
    test_file = '/tmp/test_secure.txt'
    encrypted_file = '/tmp/test_secure.encrypted'
    decrypted_file = '/tmp/test_secure_decrypted.txt'
    
    with open(test_file, 'w') as f:
        f.write('测试文件内容，包含敏感信息')
    
    encrypt_success = service.encrypt_user_file('user_001', test_file, encrypted_file)
    print(f"文件加密: {'成功' if encrypt_success else '失败'}")
    
    decrypt_success = service.decrypt_user_file('user_001', encrypted_file, decrypted_file)
    print(f"文件解密: {'成功' if decrypt_success else '失败'}")
    
    with open(decrypted_file, 'r') as f:
        content = f.read()
    print(f"解密文件内容: {content}")
    
    print("\n=== 系统状态 ===")
    print(json.dumps(service.get_system_status(), indent=2, ensure_ascii=False))
    
    print("\n=== 测试完成 ===")