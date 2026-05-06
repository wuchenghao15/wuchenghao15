#!/usr/bin/env python3
"""
SQL注入防护中间件，用于防止SQL注入攻击

from flask import request, abort
from app.utils.logging import logger
import re

class SQLInjectionProtection:
    """SQL注入防护类"""

    def __init__(self):
        # SQL注入模式
        self.sql_injection_patterns = [
            # 常见SQL注入模式
            r'\b(SELECT|INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|TRUNCATE|EXEC|EXECUTE|UNION|JOIN|WHERE|FROM|GROUP BY|ORDER BY|HAVING|LIKE|IN|OR|AND|NOT|IF|CASE|WHEN|ELSE|END)\b',
            # SQL注释
            r'--|#|/\*.*?\*/',
            # 特殊字符
            r'\b(OR|AND)\s+\d+\s*=\s*\d+',
            r'\b(OR|AND)\s+\d+\s*LIKE\s*\d+',
            # 时间延迟攻击
            r'\b(SLEEP|WAITFOR|DELAY)\b',
            # 布尔盲注
            r'\bIF\s*\(.*?\)',
            # 联合查询
            r'\bUNION\s+SELECT\b',
            # 堆叠查询
            r';\s*[A-Za-z]',
            # 内联注释
            r'/\*[^*]*\*/',
        ]

        # 敏感参数名
        self.sensitive_params = [
            'username', 'email', 'password', 'id', 'user_id', 'admin', 'role',
            'token', 'key', 'secret', 'password_hash', 'auth', 'login'
        ]
    def check_sql_injection(self, data):
        """检查数据是否包含SQL注入尝试

        Args:
            data: 要检查的数据

        Returns:
            bool: 是否包含SQL注入尝试
        if isinstance(data, dict):
            for key, value in data.items():
                # 检查参数名是否敏感
                if key.lower() in self.sensitive_params:
                    if self._check_value(value):
                        return True
                # 递归检查嵌套数据
                elif isinstance(value, (dict, list)):
                    if self.check_sql_injection(value):
                        return True
        elif isinstance(data, list):
            for item in data:
                    return True
        elif isinstance(data, str):
            if self._check_value(data):
        return False

        """检查单个值是否包含SQL注入尝试

        Args:
            value: 要检查的值

            bool: 是否包含SQL注入尝试
        if not isinstance(value, str):
            return False
        # 转换为小写进行检查

        # 检查SQL注入模式
        for pattern in self.sql_injection_patterns:
            if re.search(pattern, value, re.IGNORECASE):
                return True

        suspicious_combos = [
            "' or '1'='1",
            "' or 1=1 --",
            "' union select",
            "' and 1=1 --",
            "\" or \"1\"=\"1",
            "\" or 1=1 --",
            "\" union select",
            "\" and \"1\"=\"1",
            "\" and 1=1 --",
        ]

        for combo in suspicious_combos:
                return True

        return False

    def protect(self, app):
        """注册SQL注入防护中间件

        Args:
        @app.before_request
        def sql_injection_protection():
            # 检查请求参数
                if self.check_sql_injection(request.args):
                    logger.warning(f"SQL注入尝试检测到: {request.remote_addr}, URL: {request.url}")
                    abort(403, description="请求包含可疑的SQL注入尝试")
            # 检查表单数据
            if request.form:
                if self.check_sql_injection(request.form):
                    logger.warning(f"SQL注入尝试检测到: {request.remote_addr}, URL: {request.url}")
                    abort(403, description="请求包含可疑的SQL注入尝试")

            # 检查JSON数据
            if request.is_json:
                try:
                    json_data = request.get_json()
                    if json_data and self.check_sql_injection(json_data):
                        logger.warning(f"SQL注入尝试检测到: {request.remote_addr}, URL: {request.url}")
                        abort(403, description="请求包含可疑的SQL注入尝试")
                except Exception:
                    pass

            # 检查URL路径参数
            if request.view_args:
                if self.check_sql_injection(request.view_args):
                    logger.warning(f"SQL注入尝试检测到: {request.remote_addr}, URL: {request.url}")
                    abort(403, description="请求包含可疑的SQL注入尝试")

        logger.info("SQL注入防护中间件已注册")

# 创建SQL注入防护实例
sql_injection_protection = SQLInjectionProtection()
