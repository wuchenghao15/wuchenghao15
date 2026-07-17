#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS数据验证服务
提供统一的数据验证功能
"""

import os
import sys
import json
import re
import email
import ipaddress
from typing import Dict, Any, Optional, List, Tuple

logger = print

class ValidationResult:
    """验证结果"""
    
    def __init__(self, is_valid: bool, errors: List[str] = None):
        self.is_valid = is_valid
        self.errors = errors or []
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'is_valid': self.is_valid,
            'errors': self.errors
        }

class DataValidator:
    """数据验证器"""
    
    def __init__(self):
        self.validators: Dict[str, callable] = {
            'required': self._validate_required,
            'min_length': self._validate_min_length,
            'max_length': self._validate_max_length,
            'min': self._validate_min,
            'max': self._validate_max,
            'type': self._validate_type,
            'pattern': self._validate_pattern,
            'email': self._validate_email,
            'phone': self._validate_phone,
            'url': self._validate_url,
            'ip': self._validate_ip,
            'ipv4': self._validate_ipv4,
            'ipv6': self._validate_ipv6,
            'uuid': self._validate_uuid,
            'json': self._validate_json,
            'in': self._validate_in,
            'not_in': self._validate_not_in,
            'equals': self._validate_equals,
            'not_equals': self._validate_not_equals,
            'custom': self._validate_custom
        }
        
        self.custom_validators: Dict[str, callable] = {}
    
    def _validate_required(self, value: Any, param: bool = True) -> Tuple[bool, str]:
        """验证必填字段"""
        if param and value is None:
            return False, '字段不能为空'
        if param and value == '':
            return False, '字段不能为空'
        if param and value == []:
            return False, '字段不能为空列表'
        if param and value == {}:
            return False, '字段不能为空对象'
        return True, ''
    
    def _validate_min_length(self, value: Any, param: int) -> Tuple[bool, str]:
        """验证最小长度"""
        if value is None:
            return True, ''
        
        if isinstance(value, str):
            if len(value) < param:
                return False, f'长度不能小于{param}'
        elif isinstance(value, list):
            if len(value) < param:
                return False, f'元素数量不能小于{param}'
        elif isinstance(value, dict):
            if len(value) < param:
                return False, f'键值对数量不能小于{param}'
        
        return True, ''
    
    def _validate_max_length(self, value: Any, param: int) -> Tuple[bool, str]:
        """验证最大长度"""
        if value is None:
            return True, ''
        
        if isinstance(value, str):
            if len(value) > param:
                return False, f'长度不能大于{param}'
        elif isinstance(value, list):
            if len(value) > param:
                return False, f'元素数量不能大于{param}'
        elif isinstance(value, dict):
            if len(value) > param:
                return False, f'键值对数量不能大于{param}'
        
        return True, ''
    
    def _validate_min(self, value: Any, param: float) -> Tuple[bool, str]:
        """验证最小值"""
        if value is None:
            return True, ''
        
        if isinstance(value, (int, float)):
            if value < param:
                return False, f'值不能小于{param}'
        
        return True, ''
    
    def _validate_max(self, value: Any, param: float) -> Tuple[bool, str]:
        """验证最大值"""
        if value is None:
            return True, ''
        
        if isinstance(value, (int, float)):
            if value > param:
                return False, f'值不能大于{param}'
        
        return True, ''
    
    def _validate_type(self, value: Any, param: str) -> Tuple[bool, str]:
        """验证类型"""
        if value is None:
            return True, ''
        
        type_map = {
            'string': str,
            'int': int,
            'float': float,
            'bool': bool,
            'list': list,
            'dict': dict,
            'number': (int, float)
        }
        
        target_type = type_map.get(param)
        
        if not target_type:
            return False, f'未知类型: {param}'
        
        if not isinstance(value, target_type):
            return False, f'类型必须为{param}'
        
        return True, ''
    
    def _validate_pattern(self, value: Any, param: str) -> Tuple[bool, str]:
        """验证正则表达式"""
        if value is None:
            return True, ''
        
        if isinstance(value, str):
            try:
                if not re.match(param, value):
                    return False, f'格式不正确'
            except re.error:
                return False, f'无效的正则表达式'
        
        return True, ''
    
    def _validate_email(self, value: Any, param: bool = True) -> Tuple[bool, str]:
        """验证邮箱"""
        if not param:
            return True, ''
        
        if value is None:
            return True, ''
        
        if isinstance(value, str):
            try:
                email_addr = email.utils.parseaddr(value)[1]
                if not email_addr or '@' not in email_addr:
                    return False, '邮箱格式不正确'
                
                local, domain = email_addr.split('@')
                if not local or not domain:
                    return False, '邮箱格式不正确'
                
                if not re.match(r'^[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', domain):
                    return False, '邮箱域名格式不正确'
            except:
                return False, '邮箱格式不正确'
        
        return True, ''
    
    def _validate_phone(self, value: Any, param: bool = True) -> Tuple[bool, str]:
        """验证手机号"""
        if not param:
            return True, ''
        
        if value is None:
            return True, ''
        
        if isinstance(value, str):
            phone = re.sub(r'\D', '', value)
            
            if not re.match(r'^1[3-9]\d{9}$', phone):
                return False, '手机号格式不正确'
        
        return True, ''
    
    def _validate_url(self, value: Any, param: bool = True) -> Tuple[bool, str]:
        """验证URL"""
        if not param:
            return True, ''
        
        if value is None:
            return True, ''
        
        if isinstance(value, str):
            url_pattern = r'^https?://[^\s/$.?#].[^\s]*$'
            
            if not re.match(url_pattern, value):
                return False, 'URL格式不正确'
        
        return True, ''
    
    def _validate_ip(self, value: Any, param: bool = True) -> Tuple[bool, str]:
        """验证IP地址"""
        if not param:
            return True, ''
        
        if value is None:
            return True, ''
        
        if isinstance(value, str):
            try:
                ipaddress.ip_address(value)
            except ValueError:
                return False, 'IP地址格式不正确'
        
        return True, ''
    
    def _validate_ipv4(self, value: Any, param: bool = True) -> Tuple[bool, str]:
        """验证IPv4地址"""
        if not param:
            return True, ''
        
        if value is None:
            return True, ''
        
        if isinstance(value, str):
            try:
                ip = ipaddress.ip_address(value)
                if not isinstance(ip, ipaddress.IPv4Address):
                    return False, '必须是IPv4地址'
            except ValueError:
                return False, 'IPv4地址格式不正确'
        
        return True, ''
    
    def _validate_ipv6(self, value: Any, param: bool = True) -> Tuple[bool, str]:
        """验证IPv6地址"""
        if not param:
            return True, ''
        
        if value is None:
            return True, ''
        
        if isinstance(value, str):
            try:
                ip = ipaddress.ip_address(value)
                if not isinstance(ip, ipaddress.IPv6Address):
                    return False, '必须是IPv6地址'
            except ValueError:
                return False, 'IPv6地址格式不正确'
        
        return True, ''
    
    def _validate_uuid(self, value: Any, param: bool = True) -> Tuple[bool, str]:
        """验证UUID"""
        if not param:
            return True, ''
        
        if value is None:
            return True, ''
        
        if isinstance(value, str):
            uuid_pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
            
            if not re.match(uuid_pattern, value, re.IGNORECASE):
                return False, 'UUID格式不正确'
        
        return True, ''
    
    def _validate_json(self, value: Any, param: bool = True) -> Tuple[bool, str]:
        """验证JSON"""
        if not param:
            return True, ''
        
        if value is None:
            return True, ''
        
        if isinstance(value, str):
            try:
                json.loads(value)
            except json.JSONDecodeError:
                return False, 'JSON格式不正确'
        
        return True, ''
    
    def _validate_in(self, value: Any, param: List[Any]) -> Tuple[bool, str]:
        """验证值在列表中"""
        if value is None:
            return True, ''
        
        if value not in param:
            return False, f'值必须是{param}中的一个'
        
        return True, ''
    
    def _validate_not_in(self, value: Any, param: List[Any]) -> Tuple[bool, str]:
        """验证值不在列表中"""
        if value is None:
            return True, ''
        
        if value in param:
            return False, f'值不能是{param}中的任何一个'
        
        return True, ''
    
    def _validate_equals(self, value: Any, param: Any) -> Tuple[bool, str]:
        """验证值相等"""
        if value != param:
            return False, f'值必须等于{param}'
        
        return True, ''
    
    def _validate_not_equals(self, value: Any, param: Any) -> Tuple[bool, str]:
        """验证值不相等"""
        if value == param:
            return False, f'值不能等于{param}'
        
        return True, ''
    
    def _validate_custom(self, value: Any, param: str) -> Tuple[bool, str]:
        """验证自定义验证器"""
        if param not in self.custom_validators:
            return False, f'自定义验证器不存在: {param}'
        
        validator = self.custom_validators[param]
        
        try:
            result = validator(value)
            
            if isinstance(result, tuple):
                is_valid, error = result
                return is_valid, error
            elif isinstance(result, bool):
                return result, '' if result else '验证失败'
            else:
                return True, ''
        except Exception as e:
            return False, f'自定义验证器执行失败: {e}'
    
    def add_custom_validator(self, name: str, validator: callable):
        """添加自定义验证器"""
        self.custom_validators[name] = validator
        logger(f"[验证] 添加自定义验证器: {name}")
    
    def remove_custom_validator(self, name: str):
        """移除自定义验证器"""
        if name in self.custom_validators:
            del self.custom_validators[name]
            logger(f"[验证] 移除自定义验证器: {name}")
    
    def validate_field(self, value: Any, rules: Dict[str, Any], 
                      field_name: str = 'field') -> ValidationResult:
        """验证单个字段"""
        errors = []
        
        for rule_name, param in rules.items():
            if rule_name not in self.validators:
                errors.append(f'{field_name}: 未知验证规则: {rule_name}')
                continue
            
            validator = self.validators[rule_name]
            
            try:
                is_valid, error = validator(value, param)
                
                if not is_valid:
                    errors.append(f'{field_name}: {error}')
            except Exception as e:
                errors.append(f'{field_name}: 验证规则执行失败: {e}')
        
        return ValidationResult(len(errors) == 0, errors)
    
    def validate(self, data: Dict[str, Any], schema: Dict[str, Dict[str, Any]]) -> ValidationResult:
        """验证数据"""
        errors = []
        
        for field_name, rules in schema.items():
            value = data.get(field_name)
            
            if 'required' in rules and rules['required']:
                if value is None or value == '' or value == [] or value == {}:
                    errors.append(f'{field_name}: 字段不能为空')
                    continue
            
            field_errors = self.validate_field(value, rules, field_name).errors
            errors.extend(field_errors)
        
        return ValidationResult(len(errors) == 0, errors)
    
    def validate_list(self, data: List[Dict[str, Any]], 
                     schema: Dict[str, Dict[str, Any]]) -> ValidationResult:
        """验证列表数据"""
        errors = []
        
        for i, item in enumerate(data):
            item_errors = self.validate(item, schema).errors
            
            if item_errors:
                errors.extend([f'[{i}].{e}' for e in item_errors])
        
        return ValidationResult(len(errors) == 0, errors)
    
    def sanitize_string(self, value: str, allowed_tags: List[str] = None) -> str:
        """清理字符串（防止XSS）"""
        if not value:
            return value
        
        allowed_tags = allowed_tags or []
        
        clean_value = re.sub(r'<script[^>]*>.*?</script>', '', value, flags=re.IGNORECASE)
        clean_value = re.sub(r'on\w+\s*=\s*"[^"]*"', '', clean_value)
        clean_value = re.sub(r'on\w+\s*=\s*\'[^\']*\'', '', clean_value)
        
        if allowed_tags:
            tag_pattern = '|'.join(allowed_tags)
            clean_value = re.sub(f'</?(?!({tag_pattern}))\w+[^>]*>', '', clean_value)
        
        return clean_value
    
    def sanitize_html(self, value: str) -> str:
        """清理HTML"""
        if not value:
            return value
        
        clean_value = re.sub(r'<[^>]*>', '', value)
        return clean_value
    
    def escape_special_chars(self, value: str) -> str:
        """转义特殊字符"""
        if not value:
            return value
        
        escape_map = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#39;'
        }
        
        for char, escaped in escape_map.items():
            value = value.replace(char, escaped)
        
        return value
    
    def get_status(self) -> Dict[str, Any]:
        """获取服务状态"""
        return {
            'status': 'running',
            'built_in_validators': list(self.validators.keys()),
            'custom_validators': list(self.custom_validators.keys())
        }

data_validator = DataValidator()

def validate(schema: Dict[str, Dict[str, Any]]):
    """装饰器：验证请求参数"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            data = kwargs.get('data', {})
            
            if isinstance(args[0], dict):
                data = args[0]
            
            result = data_validator.validate(data, schema)
            
            if not result.is_valid:
                return {'status': 'error', 'errors': result.errors}
            
            return func(*args, **kwargs)
        return wrapper
    return decorator
