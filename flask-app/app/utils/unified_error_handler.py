# -*- coding: utf-8 -*-
# Unified Error Handler - 统一错误处理模块
"""
提供统一的错误处理机制,支持错误分类、日志记录和友好的错误响应
"""

import logging
import traceback
import json
from typing import Dict, Any, Optional
from enum import Enum
from datetime import datetime

logger = logging.getLogger(__name__)

class ErrorCode(Enum):
    """错误代码枚举"""
    # 通用错误
    SUCCESS = (0, '成功')
    UNKNOWN_ERROR = (1000, '未知错误')
    INVALID_PARAMETER = (1001, '参数无效')
    MISSING_PARAMETER = (1002, '缺少参数')
    PERMISSION_DENIED = (1003, '权限不足')
    AUTHENTICATION_FAILED = (1004, '认证失败')
    
    # 数据库错误
    DATABASE_ERROR = (2000, '数据库错误')
    DATABASE_CONNECTION_FAILED = (2001, '数据库连接失败')
    DATA_NOT_FOUND = (2002, '数据不存在')
    DATA_CONFLICT = (2003, '数据冲突')
    
    # 服务错误
    SERVICE_UNAVAILABLE = (3000, '服务不可用')
    SERVICE_TIMEOUT = (3001, '服务超时')
    SERVICE_ERROR = (3002, '服务错误')
    
    # 业务错误
    BUSINESS_ERROR = (4000, '业务错误')
    VALIDATION_ERROR = (4001, '验证错误')
    LIMIT_EXCEEDED = (4002, '超出限制')

class ErrorLevel(Enum):
    """错误级别枚举"""
    DEBUG = 'debug'
    INFO = 'info'
    WARNING = 'warning'
    ERROR = 'error'
    CRITICAL = 'critical'

class AppError(Exception):
    """应用错误类"""
    
    def __init__(self, error_code: ErrorCode, message: str = None, details: Dict = None):
        super().__init__(message or error_code.value[1])
        self.error_code = error_code
        self.message = message or error_code.value[1]
        self.details = details or {}
        self.timestamp = datetime.now()
        self.traceback = traceback.format_exc()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'code': self.error_code.value[0],
            'message': self.message,
            'details': self.details,
            'timestamp': self.timestamp.isoformat()
        }
    
    def __str__(self):
        return f"[{self.error_code.value[0]}] {self.message}"

class ErrorHandler:
    """统一错误处理器"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._handlers = {}
            cls._instance._log_handlers = {}
        return cls._instance
    
    def register_handler(self, error_type: type, handler):
        """注册错误处理器"""
        self._handlers[error_type] = handler
        logger.info(f"注册错误处理器: {error_type.__name__}")
    
    def register_log_handler(self, level: ErrorLevel, handler):
        """注册日志处理器"""
        self._log_handlers[level] = handler
    
    def handle(self, exception: Exception) -> Dict[str, Any]:
        """处理异常"""
        # 查找特定处理器
        for error_type in type(exception).__mro__:
            if error_type in self._handlers:
                try:
                    return self._handlers[error_type](exception)
                except Exception as e:
                    logger.error(f"错误处理器执行失败: {str(e)}")
                    break
        
        # 默认处理
        return self._default_handler(exception)
    
    def _default_handler(self, exception: Exception) -> Dict[str, Any]:
        """默认错误处理"""
        if isinstance(exception, AppError):
            error_info = exception.to_dict()
            self._log_error(ErrorLevel.ERROR, exception)
            return error_info
        
        # 其他异常
        error_info = {
            'code': ErrorCode.UNKNOWN_ERROR.value[0],
            'message': str(exception),
            'details': {
                'type': type(exception).__name__
            },
            'timestamp': datetime.now().isoformat()
        }
        
        self._log_error(ErrorLevel.ERROR, exception)
        return error_info
    
    def _log_error(self, level: ErrorLevel, exception: Exception):
        """记录错误日志"""
        log_message = f"[{level.value.upper()}] {exception}"
        
        if isinstance(exception, AppError):
            log_message = f"[{level.value.upper()}] [{exception.error_code.value[0]}] {exception.message}"
        
        # 调用注册的日志处理器
        if level in self._log_handlers:
            try:
                self._log_handlers[level](exception)
            except Exception as e:
                logger.error(f"日志处理器执行失败: {str(e)}")
        
        # 使用标准日志记录
        if level == ErrorLevel.CRITICAL:
            logger.critical(log_message)
        elif level == ErrorLevel.ERROR:
            logger.error(log_message)
        elif level == ErrorLevel.WARNING:
            logger.warning(log_message)
        elif level == ErrorLevel.INFO:
            logger.info(log_message)
        else:
            logger.debug(log_message)
    
    def log(self, level: ErrorLevel, message: str, details: Dict = None):
        """记录日志"""
        details = details or {}
        log_message = f"[{level.value.upper()}] {message}"
        
        if details:
            log_message += f" | {json.dumps(details)}"
        
        if level == ErrorLevel.CRITICAL:
            logger.critical(log_message)
        elif level == ErrorLevel.ERROR:
            logger.error(log_message)
        elif level == ErrorLevel.WARNING:
            logger.warning(log_message)
        elif level == ErrorLevel.INFO:
            logger.info(log_message)
        else:
            logger.debug(log_message)
    
    def validate_parameters(self, params: Dict, required: list) -> Optional[AppError]:
        """验证参数"""
        missing = [p for p in required if p not in params or params[p] is None]
        if missing:
            return AppError(
                ErrorCode.MISSING_PARAMETER,
                f"缺少必要参数: {', '.join(missing)}",
                {'missing': missing}
            )
        return None
    
    def wrap_result(self, data: Any = None, error: AppError = None) -> Dict[str, Any]:
        """包装返回结果"""
        if error:
            return {
                'success': False,
                'error': error.to_dict()
            }
        
        return {
            'success': True,
            'data': data,
            'timestamp': datetime.now().isoformat()
        }

# 全局错误处理器实例
error_handler = ErrorHandler()

# 注册默认处理器
def register_default_handlers():
    """注册默认错误处理器"""
    
    # 处理 ValueError
    def handle_value_error(e: ValueError):
        return error_handler.wrap_result(error=AppError(
            ErrorCode.INVALID_PARAMETER,
            str(e)
        ))
    
    error_handler.register_handler(ValueError, handle_value_error)
    
    # 处理 TypeError
    def handle_type_error(e: TypeError):
        return error_handler.wrap_result(error=AppError(
            ErrorCode.INVALID_PARAMETER,
            str(e)
        ))
    
    error_handler.register_handler(TypeError, handle_type_error)
    
    # 处理 RuntimeError
    def handle_runtime_error(e: RuntimeError):
        return error_handler.wrap_result(error=AppError(
            ErrorCode.SERVICE_ERROR,
            str(e)
        ))
    
    error_handler.register_handler(RuntimeError, handle_runtime_error)
    
    logger.info("默认错误处理器注册完成")

# 装饰器:统一错误处理
def handle_errors(func):
    """错误处理装饰器"""
    def wrapper(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
            if isinstance(result, dict) and 'success' in result:
                return result
            return error_handler.wrap_result(data=result)
        except Exception as e:
            return error_handler.wrap_result(error=error_handler.handle(e))
    return wrapper

# 装饰器:参数验证
def validate_params(required: list):
    """参数验证装饰器"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            params = kwargs.copy()
            if args:
                params['args'] = args
            
            error = error_handler.validate_parameters(params, required)
            if error:
                return error_handler.wrap_result(error=error)
            
            return func(*args, **kwargs)
        return wrapper
    return decorator

if __name__ == '__main__':
    # 示例用法
    register_default_handlers()
    
    @handle_errors
    @validate_params(['name', 'age'])
    def test_func(name: str, age: int):
        if age < 0:
            raise ValueError("年龄不能为负数")
        return {'name': name, 'age': age}
    
    # 测试成功
    result = test_func(name='test', age=20)
    print("成功:", result)
    
    # 测试参数缺失
    result = test_func(name='test')
    print("参数缺失:", result)
    
    # 测试参数错误
    result = test_func(name='test', age=-5)
    print("参数错误:", result)