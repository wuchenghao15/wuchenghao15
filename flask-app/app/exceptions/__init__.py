# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
自定义业务异常类 - 专门处理非系统级的业务异常
"""

import traceback
import uuid
from datetime import datetime
from enum import Enum


class ErrorCategory(Enum):
    """错误分类枚举"""
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    VALIDATION = "validation"
    BUSINESS = "business"
    RESOURCE = "resource"
    INTEGRATION = "integration"
    CONCURRENCY = "concurrency"
    QUOTA = "quota"
    TIMEOUT = "timeout"
    UNKNOWN = "unknown"


class AppException(Exception):
    """
    自定义业务异常类 - 专门处理非系统级的异常错误
    
    特性：
    - 统一错误格式
    - 支持错误分类
    - 自动生成错误ID
    - 支持建议跳转页面
    - 记录错误发生时间
    """
    
    def __init__(
        self,
        message: str,
        error_code: int = 400,
        category: ErrorCategory = ErrorCategory.BUSINESS,
        error_type: str = None,
        suggestion: str = None,
        redirect_url: str = None,
        details: dict = None,
        log_level: str = "error"
    ):
        super().__init__(message)
        
        self.error_id = str(uuid.uuid4())[:8]
        self.timestamp = datetime.now().isoformat()
        self.message = message
        self.error_code = error_code
        self.category = category.value
        self.error_type = error_type or category.value
        self.suggestion = suggestion
        self.redirect_url = redirect_url
        self.details = details or {}
        self.log_level = log_level
        self.stack_trace = traceback.format_exc()
    
    def to_dict(self) -> dict:
        """转换为字典格式"""
        return {
            'success': False,
            'error_id': self.error_id,
            'timestamp': self.timestamp,
            'error_code': self.error_code,
            'error_type': self.error_type,
            'category': self.category,
            'message': self.message,
            'suggestion': self.suggestion,
            'redirect_url': self.redirect_url,
            'details': self.details
        }
    
    def __repr__(self) -> str:
        return f"<AppException {self.error_id}: {self.message} ({self.category})>"
    
    def __str__(self) -> str:
        return f"[{self.error_id}] {self.message}"


class AuthenticationException(AppException):
    """认证异常 - 登录失败、Token失效等"""
    
    def __init__(self, message: str, redirect_url: str = "/auth/login", **kwargs):
        super().__init__(
            message=message,
            error_code=401,
            category=ErrorCategory.AUTHENTICATION,
            suggestion="请重新登录",
            redirect_url=redirect_url,
            **kwargs
        )


class AuthorizationException(AppException):
    """授权异常 - 权限不足、访问被拒绝等"""
    
    def __init__(self, message: str, redirect_url: str = "/", **kwargs):
        super().__init__(
            message=message,
            error_code=403,
            category=ErrorCategory.AUTHORIZATION,
            suggestion="您没有权限访问此资源",
            redirect_url=redirect_url,
            **kwargs
        )


class ValidationException(AppException):
    """验证异常 - 参数错误、格式不正确等"""
    
    def __init__(self, message: str, field_errors: dict = None, **kwargs):
        super().__init__(
            message=message,
            error_code=400,
            category=ErrorCategory.VALIDATION,
            suggestion="请检查输入参数",
            details={"field_errors": field_errors or {}},
            **kwargs
        )


class ResourceNotFoundException(AppException):
    """资源不存在异常"""
    
    def __init__(self, message: str, resource_type: str = None, redirect_url: str = None, **kwargs):
        super().__init__(
            message=message,
            error_code=404,
            category=ErrorCategory.RESOURCE,
            suggestion="请求的资源不存在",
            redirect_url=redirect_url,
            details={"resource_type": resource_type},
            **kwargs
        )


class BusinessException(AppException):
    """业务异常 - 业务规则校验失败等"""
    
    def __init__(self, message: str, suggestion: str = None, **kwargs):
        super().__init__(
            message=message,
            error_code=400,
            category=ErrorCategory.BUSINESS,
            suggestion=suggestion or "操作失败，请稍后重试",
            **kwargs
        )


class QuotaException(AppException):
    """配额异常 - 超出限制等"""
    
    def __init__(self, message: str, quota_type: str = None, **kwargs):
        super().__init__(
            message=message,
            error_code=429,
            category=ErrorCategory.QUOTA,
            suggestion="超出使用限制，请联系管理员",
            details={"quota_type": quota_type},
            **kwargs
        )


class TimeoutException(AppException):
    """超时异常"""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message=message,
            error_code=504,
            category=ErrorCategory.TIMEOUT,
            suggestion="请求超时，请重试",
            **kwargs
        )


class IntegrationException(AppException):
    """集成异常 - 外部服务调用失败等"""
    
    def __init__(self, message: str, service: str = None, **kwargs):
        super().__init__(
            message=message,
            error_code=502,
            category=ErrorCategory.INTEGRATION,
            suggestion="外部服务暂时不可用",
            details={"service": service},
            **kwargs
        )


class ConcurrencyException(AppException):
    """并发异常 - 资源被锁定、冲突等"""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message=message,
            error_code=409,
            category=ErrorCategory.CONCURRENCY,
            suggestion="资源正在被其他操作占用，请稍后重试",
            **kwargs
        )