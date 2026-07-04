# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
SQL注入防护中间件,用于防止SQL注入攻击
"""

from flask import request, abort
from app.utils.logging import logger
import re
import logging
import json
import os


class SQLInjectionProtection:
    """SQL注入防护类"""

    def __init__(self):
        self.sql_injection_patterns = [
            r'\b(SELECT|INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|TRUNCATE|EXEC|EXECUTE|UNION|JOIN|WHERE|FROM|GROUP BY|ORDER BY|HAVING|LIKE|IN|OR|AND|NOT|IF|CASE|WHEN|ELSE|END)\b',
            r'--|#|/\*.*?\*/',
            r'\b(OR|AND)\s+\d+\s*=\s*\d+',
            r'\b(OR|AND)\s+\d+\s*LIKE\s*\d+',
            r'\b(SLEEP|WAITFOR|DELAY)\b',
            r'\bIF\s*\(.*?\)',
            r'\bUNION\s+SELECT\b',
            r';\s*[A-Za-z]',
            r'/\*[^*]*\*/',
        ]

        self.sensitive_params = [
            'username', 'email', 'password', 'id', 'user_id', 'admin', 'role',
            'token', 'key', 'secret', 'password_hash', 'auth', 'login'
        ]

    def check_sql_injection(self, data):
        """检查数据是否包含SQL注入尝试"""
        if isinstance(data, dict):
            for key, value in data.items():
                if key.lower() in self.sensitive_params:
                    if self._check_value(value):
                        return True
                elif isinstance(value, (dict, list)):
                    if self.check_sql_injection(value):
                        return True
                elif isinstance(value, str):
                    if self._check_value(value):
                        return True
        elif isinstance(data, list):
            for item in data:
                if self.check_sql_injection(item):
                    return True
        elif isinstance(data, str):
            if self._check_value(data):
                return True
        return False

    def _check_value(self, value):
        """检查单个值是否包含SQL注入尝试"""
        if not isinstance(value, str):
            return False

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

        value_lower = value.lower()
        for combo in suspicious_combos:
            if combo in value_lower:
                return True

        return False

    def protect(self, app):
        """注册SQL注入防护中间件"""
        @app.before_request
        def sql_injection_protection():
            if self.check_sql_injection(request.args):
                logger.warning(f"SQL注入尝试检测到: {request.remote_addr}, URL: {request.url}")
                abort(403, description="请求包含可疑的SQL注入尝试")

            if request.form:
                if self.check_sql_injection(request.form):
                    logger.warning(f"SQL注入尝试检测到: {request.remote_addr}, URL: {request.url}")
                    abort(403, description="请求包含可疑的SQL注入尝试")

            if request.is_json:
                try:
                    json_data = request.get_json()
                    if json_data and self.check_sql_injection(json_data):
                        logger.warning(f"SQL注入尝试检测到: {request.remote_addr}, URL: {request.url}")
                        abort(403, description="请求包含可疑的SQL注入尝试")
                except Exception:
                    pass

            if request.view_args:
                if self.check_sql_injection(request.view_args):
                    logger.warning(f"SQL注入尝试检测到: {request.remote_addr}, URL: {request.url}")
                    abort(403, description="请求包含可疑的SQL注入尝试")

        logger.info("SQL注入防护中间件已注册")


sql_injection_protection = SQLInjectionProtection()

def init_sql_injection_protection(app):
    """初始化SQL注入防护中间件"""
    sql_injection_protection.protect(app)
    return app