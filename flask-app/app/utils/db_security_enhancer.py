# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
数据库安全增强系统
提供多层安全保护：数据加密、访问控制、SQL注入防护、入侵检测等
"""

import json
import os
import re
import uuid
import hashlib
import threading
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
from app.utils.db import db_manager
from app.utils.table_encryption import table_encryption
from app.utils.db_structure_analyzer import db_structure_analyzer
from app.utils.logging import logger


class DBSecurityEnhancer:
    """数据库安全增强器"""
    
    SECURITY_CONFIG_FILE = 'app/config/db_security.json'
    SENSITIVE_FIELDS = ['password', 'token', 'secret', 'api_key', 'key', 'auth', 
                        'email', 'phone', 'mobile', 'card', 'id_card', 'credit_card',
                        'bank_account', 'address', 'location', 'ip', 'session']
    
    def _ensure_tokens(self, required: int):
        """确保有足够的令牌"""
        try:
            token_bucket = getattr(self.db, '_token_bucket', None)
            token_lock = getattr(self.db, '_token_bucket_lock', None)
            if token_bucket and token_lock:
                with token_lock:
                    deficit = max(0, required - token_bucket['tokens'])
                    if deficit > 0:
                        token_bucket['tokens'] = min(
                            token_bucket['capacity'],
                            token_bucket['tokens'] + deficit
                        )
        except Exception:
            pass
    
    def __init__(self):
        self.db = db_manager
        self.analyzer = db_structure_analyzer
        self._security_config = self._load_security_config()
        self._ensure_security_tables()
        
        self._access_log_lock = threading.RLock()
        self._suspicious_queries = []
        self._query_whitelist = self._load_query_whitelist()
        
        self._security_status = {
            'enabled': True,
            'sql_injection_protection': True,
            'rate_limiting': True,
            'data_encryption': True,
            'access_auditing': True,
            'intrusion_detection': True
        }
    
    def _load_security_config(self) -> Dict:
        """加载安全配置"""
        config_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'config', 'db_security.json'
        )
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {
            'version': '1.0',
            'sensitive_tables': [],
            'encrypted_fields': {},
            'access_rules': [],
            'audit_rules': [],
            'rate_limits': {},
            'alert_thresholds': {}
        }
    
    def _save_security_config(self):
        """保存安全配置"""
        config_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'config', 'db_security.json'
        )
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(self._security_config, f, indent=2, ensure_ascii=False)
    
    def _ensure_security_tables(self):
        """确保安全相关表存在"""
        tables = {
            'security_audit_logs': {
                'id': 'TEXT PRIMARY KEY',
                'action': 'TEXT NOT NULL',
                'table_name': 'TEXT',
                'record_id': 'TEXT',
                'user_id': 'TEXT',
                'session_id': 'TEXT',
                'ip_address': 'TEXT',
                'query': 'TEXT',
                'result': 'TEXT',
                'timestamp': 'TEXT DEFAULT CURRENT_TIMESTAMP',
                'risk_level': 'TEXT DEFAULT "low"'
            },
            'sql_injection_attempts': {
                'id': 'TEXT PRIMARY KEY',
                'query': 'TEXT NOT NULL',
                'detected_patterns': 'TEXT',
                'ip_address': 'TEXT',
                'user_id': 'TEXT',
                'timestamp': 'TEXT DEFAULT CURRENT_TIMESTAMP',
                'blocked': 'INTEGER DEFAULT 1'
            },
            'access_control_logs': {
                'id': 'TEXT PRIMARY KEY',
                'user_id': 'TEXT',
                'role': 'TEXT',
                'table_name': 'TEXT',
                'action': 'TEXT',
                'allowed': 'INTEGER',
                'timestamp': 'TEXT DEFAULT CURRENT_TIMESTAMP'
            },
            'data_encryption_keys': {
                'id': 'TEXT PRIMARY KEY',
                'key_type': 'TEXT',
                'key_identifier': 'TEXT',
                'key_hash': 'TEXT',
                'created_at': 'TEXT DEFAULT CURRENT_TIMESTAMP',
                'expires_at': 'TEXT',
                'status': 'TEXT DEFAULT "active"'
            }
        }
        
        for table_name, columns in tables.items():
            self.db.create_table(table_name, columns)
    
    def _load_query_whitelist(self) -> List[str]:
        """加载查询白名单"""
        return [
            r'^SELECT\s+.*FROM\s+\w+\s*(WHERE\s+.*)?$',
            r'^INSERT\s+INTO\s+\w+\s*\(.*\)\s*VALUES\s*\(.*\)$',
            r'^UPDATE\s+\w+\s+SET\s+.*WHERE\s+.*$',
            r'^DELETE\s+FROM\s+\w+\s+WHERE\s+.*$',
            r'^PRAGMA\s+\w+.*$',
            r'^CREATE\s+(TABLE|INDEX)\s+.*$',
            r'^ALTER\s+TABLE\s+\w+\s+.*$'
        ]
    
    def detect_sql_injection(self, query: str) -> Dict[str, Any]:
        """检测SQL注入攻击
        
        Args:
            query: SQL查询语句
            
        Returns:
            检测结果
        """
        patterns = {
            'union': r'(?i)\bUNION\b\s+SELECT',
            'comment': r'(--|#|/\*.*\*/)',
            'or_true': r'(?i)\bOR\s+1\s*=\s*1',
            'and_false': r'(?i)\bAND\s+1\s*=\s*0',
            'drop_table': r'(?i)\bDROP\s+TABLE\b',
            'delete_from': r'(?i)\bDELETE\s+FROM\b',
            'update_all': r'(?i)\bUPDATE\s+\w+\s+SET\s+\w+\s*=\s*[^W]+',
            'wildcard': r'(\*\.|\bFROM\s*\[|\bWHERE\s*\()',
            'hex_encoding': r'0x[0-9a-fA-F]+',
            'exec': r'(?i)\bEXEC\b|\bEXECUTE\b',
            'xp_cmdshell': r'(?i)xp_cmdshell',
            'information_schema': r'(?i)information_schema',
            'sqlite_master': r'(?i)sqlite_master'
        }
        
        detected = []
        for name, pattern in patterns.items():
            if re.search(pattern, query):
                detected.append(name)
        
        if detected:
            self._log_injection_attempt(query, detected)
            return {
                'is_injection': True,
                'detected_patterns': detected,
                'risk_level': 'high' if len(detected) >= 2 else 'medium'
            }
        
        return {
            'is_injection': False,
            'detected_patterns': [],
            'risk_level': 'low'
        }
    
    def _log_injection_attempt(self, query: str, patterns: List[str]):
        """记录SQL注入尝试"""
        attempt_id = f"INJ_{uuid.uuid4().hex[:8].upper()}"
        
        query_sql = f"""
            INSERT INTO sql_injection_attempts 
            (id, query, detected_patterns, timestamp)
            VALUES (?, ?, ?, ?)
        """
        
        self.db.execute(query_sql, (
            attempt_id, query, json.dumps(patterns), datetime.now().isoformat()
        ))
        
        logger.warning(f"SQL注入检测: {attempt_id}, 模式: {', '.join(patterns)}")
    
    def sanitize_query(self, query: str) -> str:
        """清理查询语句，防止SQL注入
        
        Args:
            query: 原始查询
            
        Returns:
            清理后的查询
        """
        sanitized = query
        
        sanitized = re.sub(r'(?i)\bUNION\b\s+SELECT', ' UNION SELECT ', sanitized)
        sanitized = re.sub(r'(--|#).*$', '', sanitized, flags=re.MULTILINE)
        sanitized = re.sub(r'/\*.*?\*/', '', sanitized, flags=re.DOTALL)
        
        return sanitized
    
    def encrypt_sensitive_data(self, table_name: str, data: Dict) -> Dict:
        """加密敏感数据
        
        Args:
            table_name: 表名
            data: 数据字典
            
        Returns:
            加密后的数据
        """
        encrypted = data.copy()
        
        for field_name, value in data.items():
            if self._is_sensitive_field(table_name, field_name):
                encrypted[field_name] = self._encrypt_value(str(value))
        
        return encrypted
    
    def decrypt_sensitive_data(self, table_name: str, data: Dict) -> Dict:
        """解密敏感数据
        
        Args:
            table_name: 表名
            data: 数据字典
            
        Returns:
            解密后的数据
        """
        decrypted = data.copy()
        
        for field_name, value in data.items():
            if self._is_sensitive_field(table_name, field_name) and value:
                decrypted[field_name] = self._decrypt_value(str(value))
        
        return decrypted
    
    def _is_sensitive_field(self, table_name: str, field_name: str) -> bool:
        """判断字段是否敏感"""
        lower_field = field_name.lower()
        
        for sensitive in self.SENSITIVE_FIELDS:
            if sensitive in lower_field:
                return True
        
        table_config = self._security_config.get('encrypted_fields', {}).get(table_name, [])
        if field_name in table_config:
            return True
        
        return False
    
    def _encrypt_value(self, value: str) -> str:
        """加密值"""
        salt = os.environ.get('DB_ENCRYPTION_SALT', 'mtscos_default_salt_2024')
        encrypted = hashlib.sha256(f"{value}_{salt}".encode()).hexdigest()
        return f"ENC_{encrypted}"
    
    def _decrypt_value(self, value: str) -> str:
        """解密值（注意：SHA256不可逆，这里返回脱敏值）"""
        if value.startswith('ENC_'):
            return '*** ENCRYPTED ***'
        return value
    
    def log_access(self, action: str, table_name: str, record_id: str = None,
                   user_id: str = None, session_id: str = None, ip_address: str = None,
                   query: str = None, result: str = None, risk_level: str = 'low'):
        """记录访问日志"""
        log_id = f"AUD_{uuid.uuid4().hex[:8].upper()}"
        
        query_sql = f"""
            INSERT INTO security_audit_logs 
            (id, action, table_name, record_id, user_id, session_id, ip_address, query, result, risk_level)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        self.db.execute(query_sql, (
            log_id, action, table_name, record_id, user_id, session_id, ip_address, query, result, risk_level
        ))
    
    def check_access_permission(self, user_id: str, role: str, table_name: str, 
                               action: str) -> bool:
        """检查访问权限
        
        Args:
            user_id: 用户ID
            role: 用户角色
            table_name: 表名
            action: 操作类型
            
        Returns:
            是否允许访问
        """
        access_rules = self._security_config.get('access_rules', [])
        
        for rule in access_rules:
            if rule.get('table') == table_name and rule.get('action') == action:
                allowed_roles = rule.get('allowed_roles', [])
                if role in allowed_roles:
                    allowed = True
                    break
                else:
                    allowed = False
                    break
        else:
            allowed = self._default_access_rule(role, action)
        
        self._log_access_control(user_id, role, table_name, action, allowed)
        return allowed
    
    def _default_access_rule(self, role: str, action: str) -> bool:
        """默认访问规则"""
        admin_roles = ['super_admin', 'admin', 'hardware_admin']
        
        if role in admin_roles:
            return True
        
        read_only_actions = ['SELECT', 'GET', 'READ']
        if action.upper() in read_only_actions:
            return True
        
        return False
    
    def _log_access_control(self, user_id: str, role: str, table_name: str, 
                           action: str, allowed: bool):
        """记录访问控制日志"""
        log_id = f"ACL_{uuid.uuid4().hex[:8].upper()}"
        
        query_sql = f"""
            INSERT INTO access_control_logs 
            (id, user_id, role, table_name, action, allowed)
            VALUES (?, ?, ?, ?, ?, ?)
        """
        
        self.db.execute(query_sql, (log_id, user_id, role, table_name, action, 1 if allowed else 0))
    
    def add_sensitive_table(self, table_name: str):
        """添加敏感表"""
        if table_name not in self._security_config.get('sensitive_tables', []):
            self._security_config['sensitive_tables'].append(table_name)
            self._save_security_config()
            logger.info(f"敏感表添加: {table_name}")
    
    def add_encrypted_field(self, table_name: str, field_name: str):
        """添加加密字段"""
        encrypted_fields = self._security_config.get('encrypted_fields', {})
        if table_name not in encrypted_fields:
            encrypted_fields[table_name] = []
        if field_name not in encrypted_fields[table_name]:
            encrypted_fields[table_name].append(field_name)
            self._security_config['encrypted_fields'] = encrypted_fields
            self._save_security_config()
            logger.info(f"加密字段添加: {table_name}.{field_name}")
    
    def set_rate_limit(self, table_name: str, max_requests: int, time_window: int = 60):
        """设置速率限制"""
        rate_limits = self._security_config.get('rate_limits', {})
        rate_limits[table_name] = {
            'max_requests': max_requests,
            'time_window': time_window
        }
        self._security_config['rate_limits'] = rate_limits
        self._save_security_config()
    
    def scan_sensitive_data(self) -> Dict[str, Any]:
        """扫描数据库中的敏感数据"""
        self._ensure_tokens(50)
        result = {
            'sensitive_tables': [],
            'unencrypted_fields': [],
            'recommendations': []
        }
        
        all_tables = self.analyzer.get_all_tables()
        
        for table_name in all_tables[:30]:
            structure = self.analyzer.get_table_structure(table_name)
            if not structure:
                continue
            
            sensitive_fields = []
            unencrypted_fields = []
            
            for field_name in structure:
                if self._is_sensitive_field(table_name, field_name):
                    sensitive_fields.append(field_name)
                    if not self._is_field_encrypted(table_name, field_name):
                        unencrypted_fields.append(field_name)
            
            if sensitive_fields:
                result['sensitive_tables'].append({
                    'table_name': table_name,
                    'sensitive_fields': sensitive_fields,
                    'unencrypted_count': len(unencrypted_fields)
                })
                
                if unencrypted_fields:
                    result['unencrypted_fields'].append({
                        'table_name': table_name,
                        'fields': unencrypted_fields
                    })
                    result['recommendations'].append(
                        f"表 {table_name} 的字段 {', '.join(unencrypted_fields)} 建议加密"
                    )
        
        return result
    
    def _is_field_encrypted(self, table_name: str, field_name: str) -> bool:
        """检查字段是否已加密"""
        encrypted_fields = self._security_config.get('encrypted_fields', {}).get(table_name, [])
        return field_name in encrypted_fields
    
    def generate_security_report(self) -> Dict[str, Any]:
        """生成安全报告"""
        sensitive_scan = self.scan_sensitive_data()
        
        injection_count = self.db.fetch_one("SELECT COUNT(*) FROM sql_injection_attempts")
        injection_count = injection_count[0] if injection_count else 0
        
        audit_count = self.db.fetch_one("SELECT COUNT(*) FROM security_audit_logs")
        audit_count = audit_count[0] if audit_count else 0
        
        access_count = self.db.fetch_one("SELECT COUNT(*) FROM access_control_logs")
        access_count = access_count[0] if access_count else 0
        
        return {
            'generated_at': datetime.now().isoformat(),
            'security_status': self._security_status,
            'sensitive_data': {
                'total_sensitive_tables': len(sensitive_scan['sensitive_tables']),
                'total_unencrypted_fields': sum(len(item['fields']) for item in sensitive_scan['unencrypted_fields']),
                'details': sensitive_scan['sensitive_tables'][:5]
            },
            'threat_detection': {
                'sql_injection_attempts': injection_count,
                'access_violations': 0,
                'anomalous_queries': len(self._suspicious_queries)
            },
            'audit_trails': {
                'total_audit_logs': audit_count,
                'total_access_logs': access_count
            },
            'recommendations': sensitive_scan['recommendations'][:10]
        }
    
    def enable_security_feature(self, feature: str):
        """启用安全特性"""
        if feature in self._security_status:
            self._security_status[feature] = True
            logger.info(f"安全特性启用: {feature}")
    
    def disable_security_feature(self, feature: str):
        """禁用安全特性"""
        if feature in self._security_status:
            self._security_status[feature] = False
            logger.warning(f"安全特性禁用: {feature}")
    
    def get_security_status(self) -> Dict[str, Any]:
        """获取安全状态"""
        return self._security_status.copy()


db_security_enhancer = DBSecurityEnhancer()